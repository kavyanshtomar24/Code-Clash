"""
Submission API endpoints.
"""

import json
import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.submission import (
    SubmissionCreateRequest,
    SubmissionListResponse,
    SubmissionResponse,
    SubmissionRunRequest,
    SubmissionRunResponse,
)
from app.services import submission_service

router = APIRouter()


@router.post(
    "/",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a solution",
)
async def submit_solution(
    data: SubmissionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit code for judging. Returns immediately with status PENDING."""
    submission = await submission_service.create_submission(
        db,
        user_id=current_user.id,
        problem_id=data.problem_id,
        language=data.language,
        source_code=data.source_code,
    )
    return _to_response(submission)


@router.post(
    "/run",
    response_model=SubmissionRunResponse,
    summary="Run code on custom input",
)
async def run_solution(
    data: SubmissionRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute code against custom input without creating a submission record."""
    result = await submission_service.run_submission(
        db,
        problem_id=data.problem_id,
        language=data.language,
        source_code=data.source_code,
        custom_input=data.input,
    )
    return SubmissionRunResponse(**result)


@router.get(
    "/history",
    response_model=SubmissionListResponse,
    summary="Submission history",
)
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    problem_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's submission history (newest first)."""
    import uuid

    pid = uuid.UUID(problem_id) if problem_id else None
    submissions, total = await submission_service.get_submission_history(
        db, current_user.id, page, per_page, problem_id=pid
    )
    return SubmissionListResponse(
        submissions=[_to_response(s) for s in submissions],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get(
    "/problem/{problem_id}",
    response_model=list[SubmissionResponse],
    summary="Submissions for a problem",
)
async def get_problem_submissions(
    problem_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all submissions by the authenticated user for a specific problem."""
    import uuid

    pid = uuid.UUID(problem_id)
    subs = await submission_service.get_problem_submissions(
        db, current_user.id, pid
    )
    return [_to_response(s) for s in subs]


@router.get(
    "/{submission_id}",
    response_model=SubmissionResponse,
    summary="Single submission detail",
)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single submission owned by the authenticated user."""
    import uuid

    sid = uuid.UUID(submission_id)
    submission = await submission_service.get_submission_by_id(
        db, sid, current_user.id
    )
    return _to_response(submission)


def _to_response(submission) -> SubmissionResponse:
    test_results = submission.test_results
    if isinstance(test_results, str) and test_results:
        try:
            test_results = json.loads(test_results)
        except json.JSONDecodeError:
            pass
    return SubmissionResponse(
        id=submission.id,
        user_id=submission.user_id,
        problem_id=submission.problem_id,
        language=submission.language,
        source_code=submission.source_code,
        verdict=submission.verdict,
        execution_time_ms=submission.execution_time_ms,
        memory_used_kb=submission.memory_used_kb,
        test_results=test_results,
        submitted_at=submission.submitted_at,
    )
