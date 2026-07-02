"""
Regression tests for judge verdict assignment.

The Docker execution boundary is mocked so these tests prove verdict
classification depends on actual stdout/stderr/exit status/timing instead of
defaulting to Accepted.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.core.constants import Verdict
from app.services import judge_service


def case(input_data: str = "1\n", expected: str = "1\n"):
    return SimpleNamespace(
        input=input_data,
        expected_output=expected,
        is_sample=False,
    )


class JudgeVerdictTests(unittest.TestCase):
    def judge_with(self, docker_result, language: str = "python"):
        with (
            patch.object(judge_service, "_docker_available", return_value=True),
            patch.object(judge_service, "_run_docker", return_value=docker_result),
        ):
            return judge_service.judge_against_cases(
                language=language,
                source_code="print('stub')",
                test_cases=[case()],
                time_limit_ms=1000,
                memory_limit_mb=128,
            )

    def test_correct_solution_is_accepted(self):
        result = self.judge_with((0, "1\n", "", 12))

        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertTrue(result.test_results[0]["passed"])

    def test_incorrect_solution_is_wrong_answer(self):
        result = self.judge_with((0, "2\n", "", 12))

        self.assertEqual(result.verdict, Verdict.WRONG_ANSWER)
        self.assertFalse(result.test_results[0]["passed"])
        self.assertEqual(result.test_results[0]["actual_output"], "2\n")

    def test_infinite_loop_is_time_limit_exceeded(self):
        result = self.judge_with((-1, "", "Time limit exceeded", 3000))

        self.assertEqual(result.verdict, Verdict.TIME_LIMIT_EXCEEDED)
        self.assertFalse(result.test_results[0]["passed"])

    def test_runtime_exception_is_runtime_error(self):
        result = self.judge_with((1, "", "Traceback: boom", 12))

        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)
        self.assertFalse(result.test_results[0]["passed"])

    def test_compilation_failure_is_compilation_error(self):
        result = self.judge_with((1, "", "compile.err: syntax error", 12), language="cpp")

        self.assertEqual(result.verdict, Verdict.COMPILATION_ERROR)
        self.assertFalse(result.test_results[0]["passed"])

    def test_docker_unavailable_does_not_default_to_accepted(self):
        with patch.object(judge_service, "_docker_available", return_value=False):
            result = judge_service.judge_against_cases(
                language="python",
                source_code="print('wrong')",
                test_cases=[case()],
                time_limit_ms=1000,
                memory_limit_mb=128,
            )

        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)
        self.assertFalse(result.test_results[0]["passed"])
        self.assertIn("Docker CLI not found", result.test_results[0]["stderr"])

    def test_real_docker_cli_available_in_container(self):
        """Verifies that the Docker CLI is present if running inside a Docker container."""
        import os
        if os.path.exists("/.dockerenv"):
            self.assertTrue(
                judge_service._docker_available(),
                "Docker CLI binary not found in PATH inside the Docker container environment."
            )


if __name__ == "__main__":
    unittest.main()
