"""
Pagination helpers.

Provides a reusable utility for calculating offsets and building
standardized paginated response envelopes.
"""

import math


def calculate_offset(page: int, per_page: int) -> int:
    """Compute the SQL OFFSET from 1-based page number."""
    return (max(1, page) - 1) * per_page


def paginated_response(
    items: list,
    total: int,
    page: int,
    per_page: int,
) -> dict:
    """Build a standard pagination envelope.

    Returns:
        Dict with ``items``, ``total``, ``page``, ``per_page``,
        and ``total_pages`` keys.
    """
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page) if total > 0 else 0,
    }
