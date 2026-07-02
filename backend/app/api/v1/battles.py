"""
Coding battles API endpoints.
"""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.battle import BattleCreateRequest, BattleListItem, BattleResponse, BattleSubmitRequest
from app.schemas.submission import SubmissionResponse
from app.services import battle_service

router = APIRouter()


@router.post("/", response_model=BattleResponse, status_code=status.HTTP_201_CREATED)
async def create_battle_lobby(
    payload: BattleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new 1v1 battle lobby with a specific problem."""
    battle = await battle_service.create_battle(
        db=db,
        host_id=current_user.id,
        problem_id=payload.problem_id,
        duration_seconds=payload.duration_seconds,
        opponent_username=payload.opponent_username,
    )
    details = await battle_service.get_battle_details(db, battle.id)
    return details


@router.post("/{id}/join", response_model=BattleResponse)
async def join_battle_lobby(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a pending battle lobby as the opponent."""
    battle = await battle_service.join_battle(db=db, battle_id=id, opponent_id=current_user.id)
    details = await battle_service.get_battle_details(db, battle.id)
    return details


@router.post("/{id}/cancel", response_model=BattleResponse)
async def cancel_battle_lobby(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending battle lobby."""
    battle = await battle_service.cancel_battle(db=db, battle_id=id, user_id=current_user.id)
    details = await battle_service.get_battle_details(db, battle.id)
    return details


@router.post("/{id}/end", response_model=BattleResponse)
async def end_battle(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually end a pending lobby or active battle."""
    battle = await battle_service.end_battle(db=db, battle_id=id, user_id=current_user.id)
    details = await battle_service.get_battle_details(db, battle.id)
    return details


@router.post("/{id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_battle_solution(
    id: uuid.UUID,
    payload: BattleSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a solution for the problem associated with the battle."""
    sub = await battle_service.submit_battle_solution(
        db=db,
        battle_id=id,
        user_id=current_user.id,
        language=payload.language,
        source_code=payload.source_code,
    )
    return sub


@router.get("/history", response_model=list[BattleListItem])
async def list_battle_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the authenticated user's battle history."""
    history = await battle_service.get_battle_history(
        db=db, user_id=current_user.id, page=page, per_page=per_page
    )
    return history


@router.get("/{id}", response_model=BattleResponse)
async def get_battle_details(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed information about a battle."""
    details = await battle_service.get_battle_details(db=db, battle_id=id)
    return details
