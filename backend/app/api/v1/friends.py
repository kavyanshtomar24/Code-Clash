"""
Friends system API endpoints.
"""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.friend import FriendRequestCreate, FriendRequestResponse, FriendResponse
from app.services import friend_service

router = APIRouter()


@router.post("/request", response_model=FriendRequestResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    payload: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a friend request to another user by their username."""
    req = await friend_service.send_friend_request(
        db=db, sender_id=current_user.id, receiver_username=payload.receiver_username
    )
    return req


@router.post("/accept/{request_id}", response_model=dict)
async def accept_friend_request(
    request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept an incoming pending friend request."""
    await friend_service.accept_friend_request(
        db=db, receiver_id=current_user.id, request_id=request_id
    )
    return {"status": "success", "message": "Friend request accepted"}


@router.post("/reject/{request_id}", response_model=dict)
async def reject_friend_request(
    request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject an incoming pending friend request."""
    await friend_service.reject_friend_request(
        db=db, receiver_id=current_user.id, request_id=request_id
    )
    return {"status": "success", "message": "Friend request rejected"}


@router.delete("/{friend_id}", response_model=dict)
async def remove_friend(
    friend_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a friendship."""
    await friend_service.remove_friend(db=db, user_id=current_user.id, friend_id=friend_id)
    return {"status": "success", "message": "Friend removed"}


@router.get("/", response_model=list[FriendResponse])
async def list_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active friends."""
    friends = await friend_service.list_friends(db=db, user_id=current_user.id)
    return friends


@router.get("/requests", response_model=list[FriendRequestResponse])
async def list_pending_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pending incoming friend requests."""
    reqs = await friend_service.list_pending_requests(db=db, user_id=current_user.id)
    return reqs


@router.get("/compare/{friend_id}", response_model=dict)
async def compare_stats(
    friend_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve side-by-side stats comparison with a friend."""
    comparison = await friend_service.compare_friend_stats(
        db=db, user_id=current_user.id, friend_id=friend_id
    )
    return comparison
