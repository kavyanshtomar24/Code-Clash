"""
Friend request and friendship schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FriendRequestCreate(BaseModel):
    """Payload to send a friend request by username."""
    receiver_username: str


class FriendRequestResponse(BaseModel):
    """Response representing a friend request."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender_id: uuid.UUID
    sender_username: str
    receiver_id: uuid.UUID
    receiver_username: str
    status: str
    created_at: datetime


class FriendResponse(BaseModel):
    """Response representing an active friend."""
    model_config = ConfigDict(from_attributes=True)

    friendship_id: uuid.UUID
    friend_id: uuid.UUID
    friend_username: str
    friend_rating: int
    friend_profile_picture: str | None = None
