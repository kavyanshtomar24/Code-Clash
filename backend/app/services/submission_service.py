"""
Submission service — records submissions and enqueues judge evaluation.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import Verdict
from app.core.exceptions import NotFoundException
from app.models.submission import Submission, UserProblemStats
from app.services import problem_service
from app.services.judge_service import enqueue_submission, process_submission_task, run_code_on_input


async def create_submission(
    db: AsyncSession,
    user_id: uuid.UUID,
    problem_id: uuid.UUID,
    language: str,
    source_code: str,
    *,
    enqueue: bool = True,
) -> Submission:
    """Record a new submission and enqueue for judging."""
    await problem_service.get_problem_by_id(db, problem_id)

    submission = Submission(
        user_id=user_id,
        problem_id=problem_id,
        language=language,
        source_code=source_code,
        verdict=Verdict.PENDING,
    )
    db.add(submission)

    stats_stmt = select(UserProblemStats).where(
        UserProblemStats.user_id == user_id,
        UserProblemStats.problem_id == problem_id,
    )
    stats_result = await db.execute(stats_stmt)
    stats = stats_result.scalars().first()

    if stats is None:
        stats = UserProblemStats(
            user_id=user_id,
            problem_id=problem_id,
            attempts=1,
        )
        db.add(stats)
    else:
        stats.attempts += 1

    await db.commit()
    await db.refresh(submission)

    if settings.JUDGE_ENABLED:
        if enqueue:
            await enqueue_submission(submission.id)
        else:
            await process_submission_task(submission.id)

    return submission


async def run_submission(
    db: AsyncSession,
    problem_id: uuid.UUID,
    language: str,
    source_code: str,
    custom_input: str,
) -> dict:
    """Run code on custom input without persisting a submission."""
    return await run_code_on_input(
        db, problem_id, language, source_code, custom_input
    )


async def get_submission_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    problem_id: uuid.UUID | None = None,
    verdict: str | None = None,
    language: str | None = None,
) -> tuple[list[Submission], int]:
    """Return paginated submission history for a user, newest first."""
    base = select(Submission).where(Submission.user_id == user_id)
    if problem_id:
        base = base.where(Submission.problem_id == problem_id)
    if verdict:
        base = base.where(Submission.verdict == verdict)
    if language:
        base = base.where(Submission.language == language)

    count_stmt = select(func.count()).select_from(base.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    offset = (page - 1) * per_page
    stmt = (
        base.order_by(Submission.submitted_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    submissions = list(result.scalars().all())

    return submissions, total


async def get_submission_by_id(
    db: AsyncSession,
    submission_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Submission:
    """Fetch a single submission owned by the given user."""
    stmt = select(Submission).where(
        Submission.id == submission_id,
        Submission.user_id == user_id,
    )
    result = await db.execute(stmt)
    submission = result.scalars().first()
    if submission is None:
        raise NotFoundException("Submission not found")
    return submission


async def get_problem_submissions(
    db: AsyncSession,
    user_id: uuid.UUID,
    problem_id: uuid.UUID,
) -> list[Submission]:
    """Return all submissions by a user for a specific problem."""
    stmt = (
        select(Submission)
        .where(
            Submission.user_id == user_id,
            Submission.problem_id == problem_id,
        )
        .order_by(Submission.submitted_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
