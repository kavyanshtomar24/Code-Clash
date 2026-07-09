"""
Automated judge system — supports both Docker-isolated execution (local)
and OnlineCompiler.io API (cloud) for deployments without Docker.

Compiles and runs user submissions against test cases, returns verdicts,
updates database records, and publishes results via Redis Pub/Sub.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.constants import Verdict
from app.db.session import async_session_maker
from app.models.problem import Problem, TestCase
from app.models.submission import Submission, UserProblemStats
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

# ─── Language mappings ───────────────────────────────────────────────

LANGUAGE_IMAGES = {
    "cpp": "gcc:13",
    "python": "python:3.12-alpine",
    "java": "eclipse-temurin:21-jdk-alpine",
}

LANGUAGE_FILENAMES = {
    "cpp": "solution.cpp",
    "python": "solution.py",
    "java": "Main.java",
}

# OnlineCompiler.io compiler identifiers
ONLINECOMPILER_COMPILERS = {
    "python": "python-3.14",
    "cpp": "g++-15",
    "java": "openjdk-25",
}


@dataclass
class TestCaseResult:
    passed: bool
    verdict: str
    execution_time_ms: int
    memory_used_kb: int
    stdout: str
    stderr: str


@dataclass
class JudgeResult:
    verdict: str
    execution_time_ms: int | None
    memory_used_kb: int | None
    test_results: list[dict]


# ─── Helpers ─────────────────────────────────────────────────────────

def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _onlinecompiler_available() -> bool:
    return hasattr(settings, "ONLINECOMPILER_API_KEY") and bool(settings.ONLINECOMPILER_API_KEY)


def _truncate(value: str, limit: int = 2000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"... <truncated {len(value) - limit} chars>"


def _normalize_output(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


# ═══════════════════════════════════════════════════════════════════
# DOCKER-BASED JUDGE (local / self-hosted)
# ═══════════════════════════════════════════════════════════════════

def _run_docker(
    image: str,
    shell_cmd: str,
    time_limit_ms: int,
    memory_limit_mb: int,
) -> tuple[int, str, str, int]:
    """Run a command inside an isolated Docker container."""
    container_name = f"codeclash-judge-{uuid.uuid4().hex}"
    timeout_sec = (time_limit_ms / 1000.0) + 2.0
    cmd = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--name",
        container_name,
        f"--memory={memory_limit_mb}m",
        "--cpus=1.0",
        "--pids-limit=64",
        image,
        "sh",
        "-c",
        shell_cmd,
    ]

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return proc.returncode, proc.stdout, proc.stderr, elapsed_ms
    except subprocess.TimeoutExpired as exc:
        subprocess.run(["docker", "kill", container_name], capture_output=True)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        stdout = exc.stdout.decode() if exc.stdout else ""
        stderr = exc.stderr.decode() if exc.stderr else "Time limit exceeded"
        return -1, stdout, stderr, elapsed_ms


def _build_compile_run_cmd(language: str, input_data: str) -> str:
    """Return shell command to compile (if needed) and run with stdin."""
    inp_escaped = input_data.replace("'", "'\"'\"'")
    if language == "cpp":
        return (
            "g++ -O2 -std=c++17 -o /tmp/sol solution.cpp 2>/tmp/compile.err "
            "|| (echo '[COMPILATION ERROR]' && cat /tmp/compile.err && exit 1) "
            f"&& printf '%s' '{inp_escaped}' | /tmp/sol"
        )
    if language == "python":
        return f"printf '%s' '{inp_escaped}' | python3 solution.py"
    if language == "java":
        return (
            "javac Main.java 2>/tmp/compile.err "
            "|| (echo '[COMPILATION ERROR]' && cat /tmp/compile.err && exit 1) "
            f"&& printf '%s' '{inp_escaped}' | java -XX:+TieredCompilation -XX:TieredStopAtLevel=1 -cp . Main"
        )
    raise ValueError(f"Unsupported language: {language}")


def _evaluate_test_case_docker(
    language: str,
    source_code: str,
    test_case: TestCase,
    time_limit_ms: int,
    memory_limit_mb: int,
) -> TestCaseResult:
    """Execute source against a single test case inside Docker."""
    image = LANGUAGE_IMAGES.get(language)
    if not image:
        return TestCaseResult(
            passed=False,
            verdict=Verdict.COMPILATION_ERROR,
            execution_time_ms=0,
            memory_used_kb=0,
            stdout="",
            stderr=f"Unsupported language: {language}",
        )

    filename = LANGUAGE_FILENAMES[language]
    import base64
    encoded_source = base64.b64encode(source_code.encode("utf-8")).decode("utf-8")

    run_cmd = _build_compile_run_cmd(language, test_case.input)
    shell_cmd = (
        f"echo '{encoded_source}' | base64 -d > /tmp/{filename} "
        f"&& cd /tmp && {run_cmd}"
    )

    adjusted_limit = time_limit_ms
    if language == "python":
        adjusted_limit += 1500
    elif language == "cpp":
        adjusted_limit += 3000
    elif language == "java":
        adjusted_limit += 5000

    exit_code, stdout, stderr, elapsed_ms = _run_docker(
        image, shell_cmd, adjusted_limit, memory_limit_mb
    )

    if "[COMPILATION ERROR]" in stdout or "[COMPILATION ERROR]" in stderr:
        if elapsed_ms > time_limit_ms:
            return TestCaseResult(
                False, Verdict.TIME_LIMIT_EXCEEDED, elapsed_ms, 0, stdout, stderr
            )
        return TestCaseResult(
            False, Verdict.COMPILATION_ERROR, elapsed_ms, 0, stdout, stderr
        )

    if elapsed_ms > adjusted_limit:
        return TestCaseResult(
            False, Verdict.TIME_LIMIT_EXCEEDED, elapsed_ms, 0, stdout, stderr
        )

    if exit_code != 0:
        return TestCaseResult(
            False, Verdict.RUNTIME_ERROR, elapsed_ms, 0, stdout, stderr
        )

    actual_normalized = _normalize_output(stdout)
    expected_normalized = _normalize_output(test_case.expected_output)
    passed = actual_normalized == expected_normalized

    if passed:
        return TestCaseResult(True, Verdict.ACCEPTED, elapsed_ms, 0, stdout, stderr)
    return TestCaseResult(False, Verdict.WRONG_ANSWER, elapsed_ms, 0, stdout, stderr)


# ═══════════════════════════════════════════════════════════════════
# ONLINECOMPILER.IO API-BASED JUDGE (cloud deployment)
# ═══════════════════════════════════════════════════════════════════

async def _onlinecompiler_submit(
    source_code: str,
    language: str,
    stdin: str,
) -> dict:
    """Submit code to OnlineCompiler.io API synchronously."""
    compiler = ONLINECOMPILER_COMPILERS.get(language)
    if not compiler:
        return {"status": "error", "error": f"Unsupported language: {language}", "output": "", "time": "0"}

    headers = {
        "Authorization": f"Bearer {settings.ONLINECOMPILER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "compiler": compiler,
        "code": source_code,
        "input": stdin,
    }

    url = "https://api.onlinecompiler.io/api/run-code-sync/"

    async with httpx.AsyncClient(timeout=35.0) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            logger.error("OnlineCompiler.io error: %s %s", resp.status_code, resp.text)
            return {"status": "error", "error": f"API error: {resp.status_code}", "output": "", "time": "0"}
        except Exception as exc:
            logger.error("Failed to connect to OnlineCompiler.io: %s", exc)
            return {"status": "error", "error": f"Connection failed: {exc}", "output": "", "time": "0"}


async def _evaluate_test_case_onlinecompiler(
    language: str,
    source_code: str,
    test_case: TestCase,
    time_limit_ms: int,
) -> TestCaseResult:
    """Execute source against a single testcase via OnlineCompiler.io."""
    logger.info(
        "OnlineCompiler.io case start language=%s input=%r expected=%r",
        language,
        _truncate(test_case.input),
        _truncate(test_case.expected_output),
    )

    result = await _onlinecompiler_submit(source_code, language, test_case.input)

    status = result.get("status")  # 'success' or 'error'
    stdout = result.get("output", "")
    stderr = result.get("error", "")
    time_str = result.get("time", "0")
    elapsed_ms = int(float(time_str or "0") * 1000)
    memory_kb = int(float(result.get("memory", "0")))

    logger.info(
        "OnlineCompiler.io case result status=%s elapsed_ms=%s stdout=%r stderr=%r",
        status, elapsed_ms, _truncate(stdout), _truncate(stderr),
    )

    # If status is error, determine the verdict
    if status == "error":
        if "Timeout" in stderr or elapsed_ms > time_limit_ms:
            return TestCaseResult(
                False, Verdict.TIME_LIMIT_EXCEEDED, elapsed_ms, memory_kb, stdout, stderr
            )
        # Compilation errors usually print compilation diagnostics in stderr
        if "compilation" in stderr.lower() or "error" in stderr.lower():
            return TestCaseResult(
                False, Verdict.COMPILATION_ERROR, elapsed_ms, memory_kb, stdout, stderr
            )
        return TestCaseResult(
            False, Verdict.RUNTIME_ERROR, elapsed_ms, memory_kb, stdout, stderr
        )

    # Compare output
    actual_normalized = _normalize_output(stdout)
    expected_normalized = _normalize_output(test_case.expected_output)
    passed = actual_normalized == expected_normalized

    if passed:
        return TestCaseResult(True, Verdict.ACCEPTED, elapsed_ms, memory_kb, stdout, stderr)
    return TestCaseResult(False, Verdict.WRONG_ANSWER, elapsed_ms, memory_kb, stdout, stderr)


# ═══════════════════════════════════════════════════════════════════
# UNIFIED JUDGE INTERFACE
# ═══════════════════════════════════════════════════════════════════

def _evaluate_test_case(
    language: str,
    source_code: str,
    test_case: TestCase,
    time_limit_ms: int,
    memory_limit_mb: int,
) -> TestCaseResult:
    """Execute source against a single test case (Docker mode only — sync)."""
    if not _docker_available():
        logger.error("Docker CLI is unavailable; cannot judge submission safely.")
        return TestCaseResult(
            passed=False,
            verdict=Verdict.RUNTIME_ERROR,
            execution_time_ms=0,
            memory_used_kb=0,
            stdout="",
            stderr="Judge runtime unavailable: Docker CLI not found",
        )
    return _evaluate_test_case_docker(
        language, source_code, test_case, time_limit_ms, memory_limit_mb
    )


async def _evaluate_test_case_auto(
    language: str,
    source_code: str,
    test_case: TestCase,
    time_limit_ms: int,
    memory_limit_mb: int,
) -> TestCaseResult:
    """Evaluate testcase using the best available judge backend."""
    if _docker_available():
        return _evaluate_test_case_docker(
            language, source_code, test_case, time_limit_ms, memory_limit_mb
        )
    if _onlinecompiler_available():
        return await _evaluate_test_case_onlinecompiler(
            language, source_code, test_case, time_limit_ms
        )
    return TestCaseResult(
        passed=False,
        verdict=Verdict.RUNTIME_ERROR,
        execution_time_ms=0,
        memory_used_kb=0,
        stdout="",
        stderr="No judge backend available (neither Docker nor OnlineCompiler.io API configured)",
    )


def judge_against_cases(
    language: str,
    source_code: str,
    test_cases: list[TestCase],
    time_limit_ms: int,
    memory_limit_mb: int,
) -> JudgeResult:
    """Run all test cases and compute final verdict (Docker mode — sync)."""
    results: list[dict] = []
    max_time = 0
    final_verdict = Verdict.ACCEPTED

    for i, tc in enumerate(test_cases):
        tc_result = _evaluate_test_case(
            language, source_code, tc, time_limit_ms, memory_limit_mb
        )
        max_time = max(max_time, tc_result.execution_time_ms)
        results.append({
            "case": i + 1,
            "verdict": tc_result.verdict,
            "is_sample": tc.is_sample,
            "execution_time_ms": tc_result.execution_time_ms,
            "passed": tc_result.passed,
            "input": _truncate(tc.input),
            "expected_output": _truncate(tc.expected_output),
            "actual_output": _truncate(tc_result.stdout),
            "stderr": _truncate(tc_result.stderr),
        })
        if not tc_result.passed:
            final_verdict = tc_result.verdict
            break

    return JudgeResult(
        verdict=final_verdict,
        execution_time_ms=max_time if results else None,
        memory_used_kb=None,
        test_results=results,
    )


async def judge_against_cases_async(
    language: str,
    source_code: str,
    test_cases: list[TestCase],
    time_limit_ms: int,
    memory_limit_mb: int,
) -> JudgeResult:
    """Run all test cases and compute final verdict (supports both Docker and OnlineCompiler.io)."""
    results: list[dict] = []
    max_time = 0
    max_memory = 0
    final_verdict = Verdict.ACCEPTED

    for i, tc in enumerate(test_cases):
        logger.info(
            "Judging test case %s/%s is_sample=%s",
            i + 1, len(test_cases), tc.is_sample,
        )
        tc_result = await _evaluate_test_case_auto(
            language, source_code, tc, time_limit_ms, memory_limit_mb
        )
        max_time = max(max_time, tc_result.execution_time_ms)
        max_memory = max(max_memory, tc_result.memory_used_kb)
        results.append({
            "case": i + 1,
            "verdict": tc_result.verdict,
            "is_sample": tc.is_sample,
            "execution_time_ms": tc_result.execution_time_ms,
            "passed": tc_result.passed,
            "input": _truncate(tc.input),
            "expected_output": _truncate(tc.expected_output),
            "actual_output": _truncate(tc_result.stdout),
            "stderr": _truncate(tc_result.stderr),
        })
        if not tc_result.passed:
            final_verdict = tc_result.verdict
            break

    return JudgeResult(
        verdict=final_verdict,
        execution_time_ms=max_time if results else None,
        memory_used_kb=max_memory if results else None,
        test_results=results,
    )


# ═══════════════════════════════════════════════════════════════════
# SUBMISSION PROCESSING
# ═══════════════════════════════════════════════════════════════════

async def enqueue_submission(submission_id: uuid.UUID) -> None:
    """Push submission id onto the Redis judge queue."""
    await cache_service.lpush(
        settings.JUDGE_QUEUE_KEY,
        json.dumps({"submission_id": str(submission_id)}),
    )


async def process_submission_task(submission_id: uuid.UUID) -> None:
    """Judge worker entry point — evaluate submission and persist verdict."""
    async with async_session_maker() as db:
        stmt = (
            select(Submission)
            .options(selectinload(Submission.problem).selectinload(Problem.test_cases))
            .where(Submission.id == submission_id)
        )
        result = await db.execute(stmt)
        submission = result.scalars().first()
        if not submission:
            logger.warning("Submission %s not found for judging", submission_id)
            return

        problem = submission.problem
        test_cases = list(problem.test_cases) if problem else []
        logger.info(
            "Processing submission=%s user=%s problem=%s language=%s test_cases=%s source=%r",
            submission.id,
            submission.user_id,
            submission.problem_id,
            submission.language,
            len(test_cases),
            _truncate(submission.source_code),
        )
        if not test_cases:
            submission.verdict = Verdict.RUNTIME_ERROR
            await db.commit()
            return

        # Use async judge (supports both Docker and OnlineCompiler.io)
        judge_result = await judge_against_cases_async(
            submission.language,
            submission.source_code,
            test_cases,
            problem.time_limit_ms,
            problem.memory_limit_mb,
        )

        submission.verdict = judge_result.verdict
        submission.execution_time_ms = judge_result.execution_time_ms
        submission.memory_used_kb = judge_result.memory_used_kb
        submission.test_results = json.dumps(judge_result.test_results)

        if judge_result.verdict == Verdict.ACCEPTED:
            stats_stmt = select(UserProblemStats).where(
                UserProblemStats.user_id == submission.user_id,
                UserProblemStats.problem_id == submission.problem_id,
            )
            stats_res = await db.execute(stats_stmt)
            stats = stats_res.scalars().first()
            if stats is None:
                stats = UserProblemStats(
                    user_id=submission.user_id,
                    problem_id=submission.problem_id,
                    solved=True,
                    attempts=1,
                )
                from datetime import datetime, timezone

                stats.first_solved_at = datetime.now(timezone.utc)
                db.add(stats)
            elif not stats.solved:
                stats.solved = True
                from datetime import datetime, timezone

                stats.first_solved_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(submission)

        await cache_service.publish(
            f"submission:{submission.id}",
            json.dumps({
                "submission_id": str(submission.id),
                "verdict": submission.verdict,
                "execution_time_ms": submission.execution_time_ms,
                "memory_used_kb": submission.memory_used_kb,
            }),
        )

        await cache_service.delete(f"user:stats:{submission.user_id}")
        await cache_service.delete_pattern("problem_list:*")

        logger.info(
            "Judged submission %s → %s",
            submission_id,
            submission.verdict,
        )


async def run_code_on_input(
    db: AsyncSession,
    problem_id: uuid.UUID,
    language: str,
    source_code: str,
    custom_input: str,
) -> dict:
    """Run code against custom input (sample run — no DB record)."""
    stmt = (
        select(Problem)
        .options(selectinload(Problem.test_cases))
        .where(Problem.id == problem_id)
    )
    result = await db.execute(stmt)
    problem = result.scalars().first()
    if not problem:
        from app.core.exceptions import NotFoundException

        raise NotFoundException("Problem not found")

    tc = TestCase(
        input=custom_input,
        expected_output="",
        is_sample=True,
        problem_id=problem.id,
    )
    tc_result = await _evaluate_test_case_auto(
        language,
        source_code,
        tc,
        problem.time_limit_ms,
        problem.memory_limit_mb,
    )
    return {
        "stdout": tc_result.stdout,
        "stderr": tc_result.stderr,
        "verdict": tc_result.verdict,
        "execution_time_ms": tc_result.execution_time_ms,
    }
