"""
Model registry — import every model so Alembic's ``target_metadata``
can discover them via ``Base.metadata``.
"""

from app.models.user import User  # noqa: F401
from app.models.problem import Problem, Tag, ProblemTag, TestCase  # noqa: F401
from app.models.submission import Submission, UserProblemStats  # noqa: F401
from app.models.friend import FriendRequest, Friendship  # noqa: F401
from app.models.battle import Battle, BattleSubmission  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.codeforces import CodeforcesProfile, CodeforcesContest  # noqa: F401

__all__ = [
    "User",
    "Problem",
    "Tag",
    "ProblemTag",
    "TestCase",
    "Submission",
    "UserProblemStats",
    "FriendRequest",
    "Friendship",
    "Battle",
    "BattleSubmission",
    "Notification",
    "CodeforcesProfile",
    "CodeforcesContest",
]
