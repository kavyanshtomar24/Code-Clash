"""
Problem management service.

Handles problem listing with dynamic filters, detail retrieval,
tag management, and problem creation with test cases.
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import json

from app.core.exceptions import ConflictException, NotFoundException
from app.models.problem import Problem, ProblemTag, Tag, TestCase
from app.models.submission import UserProblemStats
from app.schemas.problem import ProblemCreateRequest, ProblemFilterParams
from app.services.cache_service import cache_service


def _slugify(text: str) -> str:
    """Convert a title into a URL-friendly slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


async def list_problems(
    db: AsyncSession,
    filters: ProblemFilterParams,
    user_id: uuid.UUID | None = None,
) -> tuple[list[dict], int]:
    """Return a filtered, paginated list of problems.

    When *user_id* is provided, each result includes a ``solved_by_user``
    flag indicating whether the authenticated user has solved the problem.
    """
    cache_key = (
        f"problem_list:{filters.difficulty}:{filters.tag}:"
        f"{filters.search}:{filters.status}:{filters.page}:{filters.per_page}"
    )
    if user_id is None and filters.status is None:
        cached = await cache_service.get(cache_key)
        if cached:
            data = json.loads(cached)
            return data["items"], data["total"]

    query = select(Problem).options(selectinload(Problem.tags))

    # Status filter requires LEFT OUTER JOIN on UserProblemStats
    if filters.status and user_id:
        from sqlalchemy import and_
        query = query.outerjoin(
            UserProblemStats,
            and_(
                Problem.id == UserProblemStats.problem_id,
                UserProblemStats.user_id == user_id,
            ),
        )
        if filters.status == "solved":
            query = query.where(UserProblemStats.solved.is_(True))
        elif filters.status == "unsolved":
            query = query.where(
                (UserProblemStats.id.is_(None)) | (UserProblemStats.solved.is_(False))
            )
        elif filters.status == "attempted":
            query = query.where(UserProblemStats.attempts > 0)

    # Apply filters
    if filters.difficulty:
        query = query.where(Problem.difficulty == filters.difficulty.lower())

    if filters.tag:
        query = query.join(Problem.tags).where(Tag.name.ilike(filters.tag))

    if filters.search:
        query = query.where(Problem.title.ilike(f"%{filters.search}%"))

    # Total count (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Pagination
    offset = (filters.page - 1) * filters.per_page
    query = query.order_by(Problem.created_at.desc()).offset(offset).limit(filters.per_page)

    result = await db.execute(query)
    problems = list(result.scalars().unique().all())

    # Build solved map for the current user
    solved_map: dict[uuid.UUID, bool] = {}
    if user_id and problems:
        problem_ids = [p.id for p in problems]
        stats_stmt = (
            select(UserProblemStats.problem_id, UserProblemStats.solved)
            .where(
                UserProblemStats.user_id == user_id,
                UserProblemStats.problem_id.in_(problem_ids),
            )
        )
        stats_result = await db.execute(stats_stmt)
        solved_map = {row[0]: row[1] for row in stats_result.all()}

    items = []
    for p in problems:
        items.append(
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "difficulty": p.difficulty,
                "tags": [{"id": t.id, "name": t.name} for t in p.tags],
                "solved_by_user": solved_map.get(p.id, False) if user_id else None,
            }
        )

    if user_id is None:
        await cache_service.set(
            cache_key,
            json.dumps({"items": items, "total": total}, default=str),
            ttl=300,
        )

    return items, total


async def get_problem_by_slug(db: AsyncSession, slug: str) -> Problem:
    """Fetch a single problem by slug with tags and sample test cases.

    Raises:
        NotFoundException: If no problem matches the slug.
    """
    stmt = (
        select(Problem)
        .options(selectinload(Problem.tags), selectinload(Problem.test_cases))
        .where(Problem.slug == slug)
    )
    result = await db.execute(stmt)
    problem = result.scalars().first()
    if problem is None:
        raise NotFoundException(f"Problem '{slug}' not found")
    return problem


async def get_problem_by_id(db: AsyncSession, problem_id: uuid.UUID) -> Problem:
    """Fetch a single problem by id.

    Raises:
        NotFoundException: If no problem matches.
    """
    stmt = select(Problem).where(Problem.id == problem_id)
    result = await db.execute(stmt)
    problem = result.scalars().first()
    if problem is None:
        raise NotFoundException("Problem not found")
    return problem


async def get_all_tags(db: AsyncSession) -> list[Tag]:
    """Return all tags ordered alphabetically."""
    stmt = select(Tag).order_by(Tag.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_problem(
    db: AsyncSession,
    data: ProblemCreateRequest,
    user_id: uuid.UUID,
) -> Problem:
    """Create a problem with associated tags and test cases.

    Auto-generates a slug from the title. Raises ``ConflictException``
    if the slug already exists.
    """
    slug = _slugify(data.title)

    # Check slug uniqueness
    existing = await db.execute(select(Problem).where(Problem.slug == slug))
    if existing.scalars().first() is not None:
        raise ConflictException(f"A problem with slug '{slug}' already exists")

    problem = Problem(
        title=data.title,
        slug=slug,
        description=data.description,
        input_format=data.input_format,
        output_format=data.output_format,
        constraints=data.constraints,
        difficulty=data.difficulty.lower(),
        time_limit_ms=data.time_limit_ms,
        memory_limit_mb=data.memory_limit_mb,
        created_by=user_id,
    )
    db.add(problem)
    await db.flush()  # get problem.id

    # Link tags
    if data.tag_ids:
        for tag_id in data.tag_ids:
            db.add(ProblemTag(problem_id=problem.id, tag_id=tag_id))

    # Create test cases
    for tc in data.test_cases:
        db.add(
            TestCase(
                problem_id=problem.id,
                input=tc.input,
                expected_output=tc.expected_output,
                is_sample=tc.is_sample,
            )
        )

    await db.commit()
    await db.refresh(problem)
    await cache_service.delete_pattern("problem_list:*")
    return problem
