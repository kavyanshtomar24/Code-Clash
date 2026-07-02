"""
Friend system service.

Handles sending, accepting, and rejecting friend requests, removing friends,
listing active friends and pending requests, and side-by-side performance comparisons.
"""

from __future__ import annotations

import uuid
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models.friend import FriendRequest, Friendship
from app.models.user import User
from app.services.notification_service import notification_service
from app.services.user_service import get_user_stats


async def _format_friend_request(db: AsyncSession, req: FriendRequest) -> dict:
    """Build FriendRequestResponse-compatible dict with resolved usernames."""
    sender_stmt = select(User.username).where(User.id == req.sender_id)
    sender_res = await db.execute(sender_stmt)
    sender_username = sender_res.scalar() or "unknown"

    receiver_stmt = select(User.username).where(User.id == req.receiver_id)
    receiver_res = await db.execute(receiver_stmt)
    receiver_username = receiver_res.scalar() or "unknown"

    return {
        "id": req.id,
        "sender_id": req.sender_id,
        "sender_username": sender_username,
        "receiver_id": req.receiver_id,
        "receiver_username": receiver_username,
        "status": req.status,
        "created_at": req.created_at,
    }


async def send_friend_request(
    db: AsyncSession, sender_id: uuid.UUID, receiver_username: str
) -> dict:
    """Send a friend request from sender to a user identified by username."""
    # Find receiver
    stmt = select(User).where(User.username == receiver_username)
    result = await db.execute(stmt)
    receiver = result.scalars().first()
    if not receiver:
        raise NotFoundException(f"User '{receiver_username}' not found")

    if sender_id == receiver.id:
        raise BadRequestException("You cannot send a friend request to yourself")

    # Check if they are already friends
    u1, u2 = min(sender_id, receiver.id), max(sender_id, receiver.id)
    stmt = select(Friendship).where(
        and_(Friendship.user1_id == u1, Friendship.user2_id == u2)
    )
    res = await db.execute(stmt)
    if res.scalars().first():
        raise ConflictException("You are already friends with this user")

    # Check if request already exists (either direction)
    stmt = select(FriendRequest).where(
        or_(
            and_(FriendRequest.sender_id == sender_id, FriendRequest.receiver_id == receiver.id),
            and_(FriendRequest.sender_id == receiver.id, FriendRequest.receiver_id == sender_id),
        )
    )
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if existing:
        if existing.status == "pending":
            if existing.sender_id == sender_id:
                raise ConflictException("Friend request already sent and is pending")
            else:
                raise ConflictException("This user has already sent you a friend request")
        # If rejected, we can reactivate it
        existing.status = "pending"
        existing.sender_id = sender_id
        existing.receiver_id = receiver.id
        await db.commit()
        await db.refresh(existing)
        req = existing
    else:
        req = FriendRequest(sender_id=sender_id, receiver_id=receiver.id, status="pending")
        db.add(req)
        await db.commit()
        await db.refresh(req)

    # Get sender info for notification
    stmt = select(User.username).where(User.id == sender_id)
    sender_res = await db.execute(stmt)
    sender_username = sender_res.scalar() or "Someone"

    # Send Notification
    await notification_service.create_notification(
        db=db,
        user_id=receiver.id,
        title="New Friend Request",
        message=f"{sender_username} sent you a friend request.",
        notification_type="friend_request",
        reference_id=str(req.id),
    )

    return await _format_friend_request(db, req)


async def accept_friend_request(
    db: AsyncSession, receiver_id: uuid.UUID, request_id: uuid.UUID
) -> Friendship:
    """Accept a pending friend request."""
    stmt = select(FriendRequest).where(
        and_(FriendRequest.id == request_id, FriendRequest.receiver_id == receiver_id)
    )
    result = await db.execute(stmt)
    req = result.scalars().first()
    if not req:
        raise NotFoundException("Friend request not found or not addressed to you")

    if req.status != "pending":
        raise BadRequestException(f"Cannot accept request with status '{req.status}'")

    req.status = "accepted"

    # Create the Friendship
    u1, u2 = min(req.sender_id, req.receiver_id), max(req.sender_id, req.receiver_id)
    friendship = Friendship(user1_id=u1, user2_id=u2)
    db.add(friendship)
    await db.commit()
    await db.refresh(friendship)

    # Get receiver username
    stmt = select(User.username).where(User.id == receiver_id)
    receiver_res = await db.execute(stmt)
    receiver_username = receiver_res.scalar() or "A user"

    # Send notification to sender
    await notification_service.create_notification(
        db=db,
        user_id=req.sender_id,
        title="Friend Request Accepted",
        message=f"{receiver_username} accepted your friend request.",
        notification_type="friend_accepted",
        reference_id=str(friendship.id),
    )

    return friendship


async def reject_friend_request(
    db: AsyncSession, receiver_id: uuid.UUID, request_id: uuid.UUID
) -> FriendRequest:
    """Reject a pending friend request."""
    stmt = select(FriendRequest).where(
        and_(FriendRequest.id == request_id, FriendRequest.receiver_id == receiver_id)
    )
    result = await db.execute(stmt)
    req = result.scalars().first()
    if not req:
        raise NotFoundException("Friend request not found or not addressed to you")

    if req.status != "pending":
        raise BadRequestException(f"Cannot reject request with status '{req.status}'")

    req.status = "rejected"
    await db.commit()
    await db.refresh(req)
    return req


async def remove_friend(
    db: AsyncSession, user_id: uuid.UUID, friend_id: uuid.UUID
) -> None:
    """Remove a friendship between two users."""
    u1, u2 = min(user_id, friend_id), max(user_id, friend_id)
    stmt = select(Friendship).where(
        and_(Friendship.user1_id == u1, Friendship.user2_id == u2)
    )
    result = await db.execute(stmt)
    friendship = result.scalars().first()
    if not friendship:
        raise NotFoundException("Friendship not found")

    # Delete the friendship
    await db.delete(friendship)

    # Delete any associated friend requests too to clean up
    req_stmt = select(FriendRequest).where(
        or_(
            and_(FriendRequest.sender_id == user_id, FriendRequest.receiver_id == friend_id),
            and_(FriendRequest.sender_id == friend_id, FriendRequest.receiver_id == user_id),
        )
    )
    req_res = await db.execute(req_stmt)
    for req in req_res.scalars().all():
        await db.delete(req)

    await db.commit()


async def list_friends(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    """List all active friends for a user."""
    # Find friendships
    stmt = select(Friendship).where(
        or_(Friendship.user1_id == user_id, Friendship.user2_id == user_id)
    )
    result = await db.execute(stmt)
    friendships = result.scalars().all()

    friends = []
    for fs in friendships:
        friend_id = fs.user2_id if fs.user1_id == user_id else fs.user1_id
        # Get friend details
        friend_stmt = select(User).where(User.id == friend_id)
        friend_res = await db.execute(friend_stmt)
        friend_user = friend_res.scalars().first()
        if friend_user:
            friends.append({
                "friendship_id": fs.id,
                "friend_id": friend_user.id,
                "friend_username": friend_user.username,
                "friend_rating": friend_user.rating,
                "friend_profile_picture": friend_user.profile_picture,
            })
    return friends


async def list_pending_requests(
    db: AsyncSession, user_id: uuid.UUID
) -> list[dict]:
    """List all pending incoming friend requests for a user."""
    stmt = select(FriendRequest).where(
        and_(FriendRequest.receiver_id == user_id, FriendRequest.status == "pending")
    )
    result = await db.execute(stmt)
    requests = result.scalars().all()

    payload = []
    for r in requests:
        # Get sender username
        sender_stmt = select(User.username).where(User.id == r.sender_id)
        sender_res = await db.execute(sender_stmt)
        sender_username = sender_res.scalar() or "unknown"

        stmt_rec = select(User.username).where(User.id == user_id)
        rec_res = await db.execute(stmt_rec)
        receiver_username = rec_res.scalar() or "unknown"

        payload.append({
            "id": r.id,
            "sender_id": r.sender_id,
            "sender_username": sender_username,
            "receiver_id": r.receiver_id,
            "receiver_username": receiver_username,
            "status": r.status,
            "created_at": r.created_at,
        })
    return payload


async def compare_friend_stats(
    db: AsyncSession, user_id: uuid.UUID, friend_id: uuid.UUID
) -> dict:
    """Compare a user's stats side-by-side with a friend."""
    # Verify they are friends
    u1, u2 = min(user_id, friend_id), max(user_id, friend_id)
    stmt = select(Friendship).where(
        and_(Friendship.user1_id == u1, Friendship.user2_id == u2)
    )
    result = await db.execute(stmt)
    if not result.scalars().first():
        raise ForbiddenException("You can only compare stats with active friends")

    user_stats = await get_user_stats(db, user_id)
    friend_stats = await get_user_stats(db, friend_id)

    return {
        "user_stats": user_stats,
        "friend_stats": friend_stats,
    }
