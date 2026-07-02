"""
Notification schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """Response representing a system or social notification."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    message: str
    is_read: bool
    notification_type: str
    reference_id: str | None = None
    created_at: datetime
