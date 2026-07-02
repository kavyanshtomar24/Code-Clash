"""
Notification service.

Handles notification creation, retrieval, and status updates (read/unread).
"""

from __future__ import annotations

import uuid
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationService:
    """Manages notifications for users."""

    async def create_notification(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: str,
        reference_id: str | None = None,
    ) -> Notification:
        """Create a notification and save it to the database."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            reference_id=reference_id,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # Invalidate unread count cache
        from app.services.cache_service import cache_service
        cache_key = f"notifications:count:{user_id}"
        await cache_service.delete(cache_key)

        return notification

    async def get_user_notifications(
        self, db: AsyncSession, user_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> list[Notification]:
        """Fetch paginated notifications for a user."""
        offset = (page - 1) * per_page
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_unread_count(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        """Get the count of unread notifications for a user."""
        from app.services.cache_service import cache_service
        cache_key = f"notifications:count:{user_id}"

        # Try cache
        cached_val = await cache_service.get(cache_key)
        if cached_val is not None:
            try:
                return int(cached_val)
            except ValueError:
                pass

        query = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
        )
        result = await db.execute(query)
        count = result.scalar() or 0

        # Cache count for 1 minute
        await cache_service.set(cache_key, str(count), ttl=60)
        return count

    async def mark_as_read(
        self, db: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID
    ) -> Notification | None:
        """Mark a specific notification as read."""
        query = select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
        result = await db.execute(query)
        notification = result.scalar_one_or_none()

        if notification and not notification.is_read:
            notification.is_read = True
            await db.commit()
            await db.refresh(notification)

            # Invalidate unread count cache
            from app.services.cache_service import cache_service
            cache_key = f"notifications:count:{user_id}"
            await cache_service.delete(cache_key)

        return notification

    async def mark_all_as_read(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        """Mark all notifications for a user as read."""
        query = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True)
        )
        await db.execute(query)
        await db.commit()

        # Invalidate unread count cache
        from app.services.cache_service import cache_service
        cache_key = f"notifications:count:{user_id}"
        await cache_service.delete(cache_key)


notification_service = NotificationService()
