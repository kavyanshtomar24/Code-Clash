"""
Analytics service.

Computes tag performance, activity heatmaps, difficulty breakdowns,
and diagnoses weak areas with personalized recommendations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Difficulty, Verdict
from app.models.problem import Problem, Tag, ProblemTag
from app.models.submission import Submission, UserProblemStats


async def get_dashboard_analytics(
    db: AsyncSession, user_id: uuid.UUID
) -> dict:
    """Collect all analytics dashboards data for the user."""
    # 1. Difficulty Breakdown (solved counts + total counts)
    # Total problems available per difficulty
    total_problems_stmt = (
        select(Problem.difficulty, func.count(Problem.id))
        .group_by(Problem.difficulty)
    )
    total_problems_res = await db.execute(total_problems_stmt)
    total_problems_map = {row[0]: row[1] for row in total_problems_res.all()}

    # Solved problems per difficulty
    solved_problems_stmt = (
        select(Problem.difficulty, func.count(UserProblemStats.id))
        .join(Problem, UserProblemStats.problem_id == Problem.id)
        .where(
            UserProblemStats.user_id == user_id,
            UserProblemStats.solved.is_(True),
        )
        .group_by(Problem.difficulty)
    )
    solved_problems_res = await db.execute(solved_problems_stmt)
    solved_problems_map = {row[0]: row[1] for row in solved_problems_res.all()}

    difficulty_breakdown = {
        "easy_solved": solved_problems_map.get(Difficulty.EASY, 0),
        "medium_solved": solved_problems_map.get(Difficulty.MEDIUM, 0),
        "hard_solved": solved_problems_map.get(Difficulty.HARD, 0),
        "easy_total": total_problems_map.get(Difficulty.EASY, 0),
        "medium_total": total_problems_map.get(Difficulty.MEDIUM, 0),
        "hard_total": total_problems_map.get(Difficulty.HARD, 0),
    }

    # 2. Topic Performance
    # For each tag: number of attempts (submissions) and number of unique solves
    # Unique solves per tag
    solves_by_tag_stmt = (
        select(Tag.name, func.count(UserProblemStats.id))
        .join(ProblemTag, ProblemTag.tag_id == Tag.id)
        .join(UserProblemStats, UserProblemStats.problem_id == ProblemTag.problem_id)
        .where(
            UserProblemStats.user_id == user_id,
            UserProblemStats.solved.is_(True),
        )
        .group_by(Tag.name)
    )
    solves_by_tag_res = await db.execute(solves_by_tag_stmt)
    solves_by_tag_map = {row[0]: row[1] for row in solves_by_tag_res.all()}

    # Total submissions per tag
    subs_by_tag_stmt = (
        select(Tag.name, func.count(Submission.id))
        .join(ProblemTag, ProblemTag.tag_id == Tag.id)
        .join(Submission, Submission.problem_id == ProblemTag.problem_id)
        .where(Submission.user_id == user_id)
        .group_by(Tag.name)
    )
    subs_by_tag_res = await db.execute(subs_by_tag_stmt)
    subs_by_tag_map = {row[0]: row[1] for row in subs_by_tag_res.all()}

    # AC submissions per tag (for accuracy calculation)
    ac_subs_by_tag_stmt = (
        select(Tag.name, func.count(Submission.id))
        .join(ProblemTag, ProblemTag.tag_id == Tag.id)
        .join(Submission, Submission.problem_id == ProblemTag.problem_id)
        .where(Submission.user_id == user_id, Submission.verdict == Verdict.ACCEPTED)
        .group_by(Tag.name)
    )
    ac_subs_by_tag_res = await db.execute(ac_subs_by_tag_stmt)
    ac_subs_by_tag_map = {row[0]: row[1] for row in ac_subs_by_tag_res.all()}

    # Fetch all tags to build the lists
    tags_stmt = select(Tag.name)
    tags_res = await db.execute(tags_stmt)
    all_tags = [t for t in tags_res.scalars().all()]

    topic_performance = []
    weak_areas = []

    for tag in all_tags:
        solved = solves_by_tag_map.get(tag, 0)
        attempts = subs_by_tag_map.get(tag, 0)
        ac_subs = ac_subs_by_tag_map.get(tag, 0)

        # Accuracy is computed as (AC submissions / total submissions for this tag)
        accuracy = (ac_subs / attempts * 100) if attempts > 0 else 0.0

        # Only add to performance if user has interacted (either attempts or solved > 0)
        if attempts > 0 or solved > 0:
            perf_item = {
                "tag_name": tag,
                "solved_count": solved,
                "attempt_count": attempts,
                "accuracy": round(accuracy, 2),
            }
            topic_performance.append(perf_item)

            # Diagnose as weak area if accuracy < 60% and has attempts
            if accuracy < 60.0 and attempts > 0:
                # Provide recommendation based on difficulty solved
                suggestion = f"Your accuracy in {tag} is low ({accuracy:.1f}%). "
                if solved == 0:
                    suggestion += f"Start by practicing Easy problems tagged with {tag}."
                else:
                    suggestion += f"Review your incorrect submissions on {tag} and focus on edge cases."

                weak_areas.append({
                    "tag_name": tag,
                    "accuracy": round(accuracy, 2),
                    "solved_count": solved,
                    "attempt_count": attempts,
                    "suggestion": suggestion,
                })

    # Sort weak areas by lowest accuracy
    weak_areas = sorted(weak_areas, key=lambda x: x["accuracy"])[:5]

    # 3. Submission Heatmap (last 365 days)
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    heatmap_stmt = (
        select(
            func.to_char(Submission.submitted_at, "YYYY-MM-DD").label("sub_date"),
            func.count(Submission.id).label("sub_count"),
        )
        .where(Submission.user_id == user_id, Submission.submitted_at >= one_year_ago)
        .group_by("sub_date")
        .order_by("sub_date")
    )
    heatmap_res = await db.execute(heatmap_stmt)
    heatmap_list = [
        {"date": row[0], "count": row[1]} for row in heatmap_res.all()
    ]

    return {
        "topic_performance": topic_performance,
        "submission_heatmap": heatmap_list,
        "difficulty_breakdown": difficulty_breakdown,
        "weak_areas": weak_areas,
    }
