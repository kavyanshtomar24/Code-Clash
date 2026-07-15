"""
Problem management API endpoints.

Provides problem listing with filters, single problem detail by slug,
tag listing, and authenticated problem creation.
"""

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_current_user_optional, get_db
from app.models.user import User
from app.schemas.problem import (
    ProblemCreateRequest,
    ProblemDetailResponse,
    ProblemFilterParams,
    ProblemListItem,
    TagResponse,
    TestCaseResponse,
)
from app.services import problem_service

router = APIRouter()


@router.get(
    "/",
    summary="List problems",
)
async def list_problems(
    difficulty: str | None = Query(None, description="Filter by difficulty"),
    tag: str | None = Query(None, description="Filter by tag name"),
    search: str | None = Query(None, description="Search in title"),
    status: str | None = Query(None, pattern="^(solved|unsolved|attempted)$", description="Filter by solve status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated, filterable list of problems.

    Authenticated users see a ``solved_by_user`` flag on each problem.
    """
    filters = ProblemFilterParams(
        difficulty=difficulty,
        tag=tag,
        search=search,
        status=status,
        page=page,
        per_page=per_page,
    )
    user_id = current_user.id if current_user else None
    items, total = await problem_service.list_problems(db, filters, user_id)

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page) if total > 0 else 0,
    }


@router.get(
    "/tags",
    response_model=list[TagResponse],
    summary="List all tags",
)
async def list_tags(db: AsyncSession = Depends(get_db)):
    """Return every problem tag ordered alphabetically."""
    return await problem_service.get_all_tags(db)


@router.get(
    "/{slug}",
    response_model=ProblemDetailResponse,
    summary="Problem detail",
)
async def get_problem(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Fetch full problem details including sample test cases."""
    problem = await problem_service.get_problem_by_slug(db, slug)
    # Filter to sample test cases only for the public response
    sample_cases = [tc for tc in problem.test_cases if tc.is_sample]
    return ProblemDetailResponse(
        id=problem.id,
        title=problem.title,
        slug=problem.slug,
        description=problem.description,
        input_format=problem.input_format,
        output_format=problem.output_format,
        constraints=problem.constraints,
        difficulty=problem.difficulty,
        tags=[TagResponse(id=t.id, name=t.name) for t in problem.tags],
        test_cases=[
            TestCaseResponse(
                id=tc.id,
                input=tc.input,
                expected_output=tc.expected_output,
                is_sample=tc.is_sample,
            )
            for tc in sample_cases
        ],
        created_at=problem.created_at,
    )


@router.post(
    "/",
    response_model=ProblemDetailResponse,
    status_code=201,
    summary="Create a problem",
)
async def create_problem(
    data: ProblemCreateRequest,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new problem with tags and test cases (admin only)."""
    problem = await problem_service.create_problem(db, data, admin_user.id)
    sample_cases = [tc for tc in problem.test_cases if tc.is_sample]
    return ProblemDetailResponse(
        id=problem.id,
        title=problem.title,
        slug=problem.slug,
        description=problem.description,
        input_format=problem.input_format,
        output_format=problem.output_format,
        constraints=problem.constraints,
        difficulty=problem.difficulty,
        tags=[TagResponse(id=t.id, name=t.name) for t in problem.tags],
        test_cases=[
            TestCaseResponse(
                id=tc.id,
                input=tc.input,
                expected_output=tc.expected_output,
                is_sample=tc.is_sample,
            )
            for tc in sample_cases
        ],
        created_at=problem.created_at,
    )


@router.get(
    "/{slug}/statistics",
    summary="Problem statistics",
)
async def get_problem_statistics(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated statistics for a problem: solve rate, verdict breakdown, language usage."""
    from app.services.problem_stats_service import get_problem_statistics
    return await get_problem_statistics(db, slug)
