"""
Domain-level string enumerations.

Using str-based Enums lets us store human-readable values in the database
while retaining type safety and IDE autocompletion in application code.
"""

from enum import StrEnum


class Difficulty(StrEnum):
    """Problem difficulty tier."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Verdict(StrEnum):
    """Possible outcomes for a code submission (blueprint short-codes)."""

    ACCEPTED = "AC"
    WRONG_ANSWER = "WA"
    TIME_LIMIT_EXCEEDED = "TLE"
    RUNTIME_ERROR = "RE"
    COMPILATION_ERROR = "CE"
    MEMORY_LIMIT_EXCEEDED = "MLE"
    PENDING = "PENDING"


class FriendRequestStatus(StrEnum):
    """Lifecycle states for a friend request."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class BattleStatus(StrEnum):
    """Lifecycle states for a head-to-head coding battle."""

    PENDING = "pending"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class SupportedLanguage(StrEnum):
    """Programming languages supported by the judge."""

    CPP = "cpp"
    PYTHON = "python"
    JAVA = "java"


DEFAULT_RATING = 1200
DEFAULT_TIME_LIMIT_MS = 2000
DEFAULT_MEMORY_LIMIT_MB = 256
JUDGE_QUEUE_KEY = "judge_queue"
