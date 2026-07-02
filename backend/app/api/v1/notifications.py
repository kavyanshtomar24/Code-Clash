"""
Notification API endpoints.
"""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification_service import notification_service

router = APIRouter()


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated notifications (newest first)."""
    notifications = await notification_service.get_user_notifications(
        db=db, user_id=current_user.id, page=page, per_page=per_page
    )
    return notifications


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread notifications for badge display."""
    count = await notification_service.get_unread_count(db=db, user_id=current_user.id)
    return {"unread_count": count}


@router.put("/{id}/read", response_model=NotificationResponse)
async def mark_as_read(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a specific notification as read."""
    notification = await notification_service.mark_as_read(
        db=db, user_id=current_user.id, notification_id=id
    )
    return notification


@router.put("/read-all", response_model=dict)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    await notification_service.mark_all_as_read(db=db, user_id=current_user.id)
    return {"status": "success", "message": "All notifications marked as read"}
