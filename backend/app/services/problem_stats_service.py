"""
Problem statistics service.

Aggregated submission analytics per problem using GROUP BY,
COUNT with FILTER, and percentage calculations — all in SQL.
"""

from __future__ import annotations

from sqlalchemy import case, cast, Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Verdict
from app.core.exceptions import NotFoundException
from app.models.problem import Problem
from app.models.submission import Submission


async def get_problem_statistics(db: AsyncSession, slug: str) -> dict:
    """Return aggregated statistics for a problem.

    Uses a single query with conditional aggregation (FILTER/CASE)
    to compute verdict breakdown and solve rate in one table scan.
    """
    # Get problem
    problem_stmt = select(Problem.id, Problem.title).where(Problem.slug == slug)
    problem_res = (await db.execute(problem_stmt)).first()
    if not problem_res:
        raise NotFoundException("Problem not found")
    problem_id = problem_res.id

    # Verdict breakdown using conditional COUNT
    verdict_stmt = (
        select(
            func.count(Submission.id).label("total_submissions"),
            func.count(Submission.id).filter(
                Submission.verdict == Verdict.ACCEPTED
            ).label("accepted"),
            func.count(Submission.id).filter(
                Submission.verdict == "WRONG_ANSWER"
            ).label("wrong_answer"),
            func.count(Submission.id).filter(
                Submission.verdict == "TIME_LIMIT_EXCEEDED"
            ).label("tle"),
            func.count(Submission.id).filter(
                Submission.verdict == "RUNTIME_ERROR"
            ).label("runtime_error"),
            func.count(Submission.id).filter(
                Submission.verdict == "COMPILE_ERROR"
            ).label("compile_error"),
            # Unique users who solved
            func.count(func.distinct(
                case(
                    (Submission.verdict == Verdict.ACCEPTED, Submission.user_id),
                    else_=None,
                )
            )).label("unique_solvers"),
            # Unique users who attempted
            func.count(func.distinct(Submission.user_id)).label("unique_attempted"),
        )
        .where(Submission.problem_id == problem_id)
    )
    row = (await db.execute(verdict_stmt)).first()

    total = row.total_submissions if row else 0
    accepted = row.accepted if row else 0
    solve_rate = round((accepted / total * 100), 1) if total > 0 else 0.0

    # Language usage breakdown
    lang_stmt = (
        select(
            Submission.language,
            func.count(Submission.id).label("count"),
        )
        .where(Submission.problem_id == problem_id)
        .group_by(Submission.language)
        .order_by(func.count(Submission.id).desc())
    )
    lang_rows = (await db.execute(lang_stmt)).all()
    language_breakdown = [
        {"language": r.language, "count": r.count, "percentage": round(r.count / total * 100, 1) if total > 0 else 0}
        for r in lang_rows
    ]

    return {
        "problem_title": problem_res.title,
        "total_submissions": total,
        "accepted": accepted,
        "wrong_answer": row.wrong_answer if row else 0,
        "tle": row.tle if row else 0,
        "runtime_error": row.runtime_error if row else 0,
        "compile_error": row.compile_error if row else 0,
        "solve_rate": solve_rate,
        "unique_solvers": row.unique_solvers if row else 0,
        "unique_attempted": row.unique_attempted if row else 0,
        "language_breakdown": language_breakdown,
    }
