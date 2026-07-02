"""
Database seed script.

Populates the platform with 14 curated tags and 13 classic DSA problems
(5 Easy, 5 Medium, 3 Hard) with full descriptions, constraints, and
sample + hidden test cases. Runs on startup only when the problems table
is empty.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.problem import Problem, ProblemTag, Tag, TestCase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tag definitions
# ---------------------------------------------------------------------------
TAG_NAMES = [
    "Arrays", "Strings", "Hash Table", "Two Pointers", "Binary Search",
    "Dynamic Programming", "Graphs", "Trees", "Greedy", "Backtracking",
    "Stack", "Math", "Sorting", "Linked List",
]

# ---------------------------------------------------------------------------
# Problem definitions
# ---------------------------------------------------------------------------
PROBLEMS: list[dict] = [
    # ========================== EASY ==========================
    {
        "title": "Two Sum",
        "difficulty": "easy",
        "tags": ["Arrays", "Hash Table"],
        "description": (
            "Given an array of integers `nums` and an integer `target`, return "
            "the indices of the two numbers such that they add up to `target`.\n\n"
            "You may assume that each input would have **exactly one solution**, "
            "and you may not use the same element twice.\n\n"
            "You can return the answer in any order."
        ),
        "input_format": (
            "The first line contains an integer `n` — the number of elements.\n"
            "The second line contains `n` space-separated integers — the array `nums`.\n"
            "The third line contains a single integer `target`."
        ),
        "output_format": "Print two space-separated integers — the 0-indexed positions of the two numbers.",
        "constraints": (
            "2 <= n <= 10^4\n"
            "-10^9 <= nums[i] <= 10^9\n"
            "-10^9 <= target <= 10^9\n"
            "Only one valid answer exists."
        ),
        "test_cases": [
            {"input": "4\n2 7 11 15\n9", "expected_output": "0 1", "is_sample": True},
            {"input": "3\n3 2 4\n6", "expected_output": "1 2", "is_sample": True},
            {"input": "2\n3 3\n6", "expected_output": "0 1", "is_sample": False},
            {"input": "5\n1 5 3 7 2\n9", "expected_output": "1 3", "is_sample": False},
        ],
    },
    {
        "title": "Valid Parentheses",
        "difficulty": "easy",
        "tags": ["Strings", "Stack"],
        "description": (
            "Given a string `s` containing just the characters `'('`, `')'`, `'{'`, "
            "`'}'`, `'['` and `']'`, determine if the input string is valid.\n\n"
            "An input string is valid if:\n"
            "1. Open brackets must be closed by the same type of brackets.\n"
            "2. Open brackets must be closed in the correct order.\n"
            "3. Every close bracket has a corresponding open bracket of the same type."
        ),
        "input_format": "A single line containing the string `s`.",
        "output_format": "Print `true` if the string is valid, `false` otherwise.",
        "constraints": "1 <= |s| <= 10^4\ns consists of parentheses only: '(){}[]'",
        "test_cases": [
            {"input": "()", "expected_output": "true", "is_sample": True},
            {"input": "()[]{}", "expected_output": "true", "is_sample": True},
            {"input": "(]", "expected_output": "false", "is_sample": False},
            {"input": "([)]", "expected_output": "false", "is_sample": False},
            {"input": "{[]}", "expected_output": "true", "is_sample": False},
        ],
    },
    {
        "title": "Reverse String",
        "difficulty": "easy",
        "tags": ["Strings", "Two Pointers"],
        "description": (
            "Write a function that reverses a string. The input string is given "
            "as an array of characters `s`.\n\n"
            "You must do this by modifying the input array in-place with O(1) extra memory.\n\n"
            "Print the reversed string."
        ),
        "input_format": "A single line containing the string `s`.",
        "output_format": "Print the reversed string.",
        "constraints": "1 <= |s| <= 10^5\ns consists of printable ASCII characters.",
        "test_cases": [
            {"input": "hello", "expected_output": "olleh", "is_sample": True},
            {"input": "Hannah", "expected_output": "hannaH", "is_sample": True},
            {"input": "a", "expected_output": "a", "is_sample": False},
            {"input": "abcdef", "expected_output": "fedcba", "is_sample": False},
        ],
    },
    {
        "title": "Binary Search",
        "difficulty": "easy",
        "tags": ["Arrays", "Binary Search"],
        "description": (
            "Given a sorted array of distinct integers `nums` and a target value "
            "`target`, return the index if the target is found. If not, return `-1`.\n\n"
            "You must write an algorithm with O(log n) runtime complexity."
        ),
        "input_format": (
            "The first line contains an integer `n`.\n"
            "The second line contains `n` space-separated sorted integers.\n"
            "The third line contains the integer `target`."
        ),
        "output_format": "Print the 0-based index of `target`, or `-1` if not found.",
        "constraints": (
            "1 <= n <= 10^4\n"
            "-10^4 <= nums[i], target <= 10^4\n"
            "All integers in nums are unique.\n"
            "nums is sorted in ascending order."
        ),
        "test_cases": [
            {"input": "6\n-1 0 3 5 9 12\n9", "expected_output": "4", "is_sample": True},
            {"input": "6\n-1 0 3 5 9 12\n2", "expected_output": "-1", "is_sample": True},
            {"input": "1\n5\n5", "expected_output": "0", "is_sample": False},
            {"input": "3\n1 2 3\n4", "expected_output": "-1", "is_sample": False},
        ],
    },
    {
        "title": "Palindrome Number",
        "difficulty": "easy",
        "tags": ["Math"],
        "description": (
            "Given an integer `x`, return `true` if `x` is a palindrome, and "
            "`false` otherwise.\n\n"
            "An integer is a **palindrome** when it reads the same forward and "
            "backward.\n\n"
            "For example, `121` is a palindrome while `123` is not.\n\n"
            "**Follow-up:** Could you solve it without converting the integer to a string?"
        ),
        "input_format": "A single line containing the integer `x`.",
        "output_format": "Print `true` if `x` is a palindrome, `false` otherwise.",
        "constraints": "-2^31 <= x <= 2^31 - 1",
        "test_cases": [
            {"input": "121", "expected_output": "true", "is_sample": True},
            {"input": "-121", "expected_output": "false", "is_sample": True},
            {"input": "10", "expected_output": "false", "is_sample": False},
            {"input": "0", "expected_output": "true", "is_sample": False},
            {"input": "12321", "expected_output": "true", "is_sample": False},
        ],
    },
    # ========================== MEDIUM ==========================
    {
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "medium",
        "tags": ["Strings", "Hash Table", "Two Pointers"],
        "description": (
            "Given a string `s`, find the length of the **longest substring** "
            "without repeating characters.\n\n"
            "A **substring** is a contiguous non-empty sequence of characters "
            "within a string."
        ),
        "input_format": "A single line containing the string `s`.",
        "output_format": "Print a single integer — the length of the longest substring without repeating characters.",
        "constraints": "0 <= |s| <= 5 * 10^4\ns consists of English letters, digits, symbols, and spaces.",
        "test_cases": [
            {"input": "abcabcbb", "expected_output": "3", "is_sample": True},
            {"input": "bbbbb", "expected_output": "1", "is_sample": True},
            {"input": "pwwkew", "expected_output": "3", "is_sample": False},
            {"input": "", "expected_output": "0", "is_sample": False},
            {"input": "aab", "expected_output": "2", "is_sample": False},
        ],
    },
    {
        "title": "Merge Intervals",
        "difficulty": "medium",
        "tags": ["Arrays", "Sorting"],
        "description": (
            "Given an array of `intervals` where `intervals[i] = [start_i, end_i]`, "
            "merge all overlapping intervals, and return an array of the "
            "non-overlapping intervals that cover all the intervals in the input.\n\n"
            "Two intervals `[a, b]` and `[c, d]` overlap if `a <= d` and `c <= b`."
        ),
        "input_format": (
            "The first line contains `n` — the number of intervals.\n"
            "The next `n` lines each contain two space-separated integers `start` and `end`."
        ),
        "output_format": "Print the merged intervals, one per line, as `start end`.",
        "constraints": "1 <= n <= 10^4\n0 <= start_i <= end_i <= 10^4",
        "test_cases": [
            {"input": "4\n1 3\n2 6\n8 10\n15 18", "expected_output": "1 6\n8 10\n15 18", "is_sample": True},
            {"input": "2\n1 4\n4 5", "expected_output": "1 5", "is_sample": True},
            {"input": "1\n1 1", "expected_output": "1 1", "is_sample": False},
            {"input": "3\n1 4\n0 4\n3 5", "expected_output": "0 5", "is_sample": False},
        ],
    },
    {
        "title": "Coin Change",
        "difficulty": "medium",
        "tags": ["Dynamic Programming"],
        "description": (
            "You are given an integer array `coins` representing coins of different "
            "denominations and an integer `amount` representing a total amount of money.\n\n"
            "Return the **fewest number of coins** that you need to make up that "
            "amount. If that amount of money cannot be made up by any combination "
            "of the coins, return `-1`.\n\n"
            "You may assume that you have an infinite number of each kind of coin."
        ),
        "input_format": (
            "The first line contains an integer `n` — the number of coin denominations.\n"
            "The second line contains `n` space-separated integers — the coin values.\n"
            "The third line contains the integer `amount`."
        ),
        "output_format": "Print a single integer — the minimum number of coins, or `-1`.",
        "constraints": "1 <= n <= 12\n1 <= coins[i] <= 2^31 - 1\n0 <= amount <= 10^4",
        "test_cases": [
            {"input": "3\n1 2 5\n11", "expected_output": "3", "is_sample": True},
            {"input": "1\n2\n3", "expected_output": "-1", "is_sample": True},
            {"input": "1\n1\n0", "expected_output": "0", "is_sample": False},
            {"input": "3\n1 5 10\n18", "expected_output": "5", "is_sample": False},
        ],
    },
    {
        "title": "Number of Islands",
        "difficulty": "medium",
        "tags": ["Graphs", "Trees"],
        "description": (
            "Given an `m x n` 2D binary grid `grid` which represents a map of "
            "'1's (land) and '0's (water), return the **number of islands**.\n\n"
            "An **island** is surrounded by water and is formed by connecting "
            "adjacent lands horizontally or vertically. You may assume all four "
            "edges of the grid are surrounded by water."
        ),
        "input_format": (
            "The first line contains two integers `m` and `n`.\n"
            "The next `m` lines each contain `n` characters ('0' or '1')."
        ),
        "output_format": "Print a single integer — the number of islands.",
        "constraints": "1 <= m, n <= 300\ngrid[i][j] is '0' or '1'.",
        "test_cases": [
            {
                "input": "4 5\n11110\n11010\n11000\n00000",
                "expected_output": "1",
                "is_sample": True,
            },
            {
                "input": "4 5\n11000\n11000\n00100\n00011",
                "expected_output": "3",
                "is_sample": True,
            },
            {"input": "1 1\n0", "expected_output": "0", "is_sample": False},
            {"input": "1 1\n1", "expected_output": "1", "is_sample": False},
        ],
    },
    {
        "title": "Kth Largest Element in an Array",
        "difficulty": "medium",
        "tags": ["Arrays", "Sorting"],
        "description": (
            "Given an integer array `nums` and an integer `k`, return the "
            "`k`th largest element in the array.\n\n"
            "Note that it is the `k`th largest element in the **sorted order**, "
            "not the `k`th distinct element.\n\n"
            "Can you solve it without sorting?"
        ),
        "input_format": (
            "The first line contains two integers `n` and `k`.\n"
            "The second line contains `n` space-separated integers."
        ),
        "output_format": "Print a single integer — the kth largest element.",
        "constraints": "1 <= k <= n <= 10^5\n-10^4 <= nums[i] <= 10^4",
        "test_cases": [
            {"input": "6 2\n3 2 1 5 6 4", "expected_output": "5", "is_sample": True},
            {"input": "9 4\n3 2 3 1 2 4 5 5 6", "expected_output": "4", "is_sample": True},
            {"input": "1 1\n1", "expected_output": "1", "is_sample": False},
            {"input": "5 3\n7 7 7 7 7", "expected_output": "7", "is_sample": False},
        ],
    },
    # ========================== HARD ==========================
    {
        "title": "Median of Two Sorted Arrays",
        "difficulty": "hard",
        "tags": ["Arrays", "Binary Search"],
        "description": (
            "Given two sorted arrays `nums1` and `nums2` of size `m` and `n` "
            "respectively, return **the median** of the two sorted arrays.\n\n"
            "The overall run-time complexity should be O(log(m + n)).\n\n"
            "The median is the middle value in an ordered integer list. If the "
            "size of the list is even, the median is the average of the two "
            "middle values."
        ),
        "input_format": (
            "The first line contains an integer `m`.\n"
            "The second line contains `m` space-separated sorted integers (or is empty if m=0).\n"
            "The third line contains an integer `n`.\n"
            "The fourth line contains `n` space-separated sorted integers (or is empty if n=0)."
        ),
        "output_format": "Print the median as a decimal number with exactly one decimal place (e.g. 2.0 or 2.5).",
        "constraints": (
            "0 <= m, n <= 1000\n"
            "1 <= m + n <= 2000\n"
            "-10^6 <= nums1[i], nums2[i] <= 10^6"
        ),
        "test_cases": [
            {"input": "2\n1 3\n1\n2", "expected_output": "2.0", "is_sample": True},
            {"input": "2\n1 2\n2\n3 4", "expected_output": "2.5", "is_sample": True},
            {"input": "0\n\n1\n1", "expected_output": "1.0", "is_sample": False},
            {"input": "3\n1 2 3\n3\n4 5 6", "expected_output": "3.5", "is_sample": False},
        ],
    },
    {
        "title": "Trapping Rain Water",
        "difficulty": "hard",
        "tags": ["Arrays", "Two Pointers", "Stack"],
        "description": (
            "Given `n` non-negative integers representing an elevation map where "
            "the width of each bar is 1, compute how much water it can trap "
            "after raining.\n\n"
            "The key insight is that for each position, the water level is "
            "determined by the minimum of the maximum heights to its left and "
            "right, minus its own height."
        ),
        "input_format": (
            "The first line contains an integer `n`.\n"
            "The second line contains `n` space-separated non-negative integers."
        ),
        "output_format": "Print a single integer — the total amount of trapped water.",
        "constraints": "1 <= n <= 2 * 10^4\n0 <= height[i] <= 10^5",
        "test_cases": [
            {"input": "12\n0 1 0 2 1 0 1 3 2 1 2 1", "expected_output": "6", "is_sample": True},
            {"input": "6\n4 2 0 3 2 5", "expected_output": "9", "is_sample": True},
            {"input": "3\n1 0 1", "expected_output": "1", "is_sample": False},
            {"input": "5\n5 4 3 2 1", "expected_output": "0", "is_sample": False},
        ],
    },
    {
        "title": "N-Queens",
        "difficulty": "hard",
        "tags": ["Backtracking"],
        "description": (
            "The **n-queens** puzzle is the problem of placing `n` queens on an "
            "`n x n` chessboard such that no two queens attack each other.\n\n"
            "Given an integer `n`, return the **number of distinct solutions** "
            "to the n-queens puzzle.\n\n"
            "A queen attacks along its row, column, and both diagonals."
        ),
        "input_format": "A single line containing the integer `n`.",
        "output_format": "Print a single integer — the number of distinct solutions.",
        "constraints": "1 <= n <= 9",
        "test_cases": [
            {"input": "4", "expected_output": "2", "is_sample": True},
            {"input": "1", "expected_output": "1", "is_sample": True},
            {"input": "8", "expected_output": "92", "is_sample": False},
            {"input": "5", "expected_output": "10", "is_sample": False},
            {"input": "6", "expected_output": "4", "is_sample": False},
        ],
    },
]


def _slugify(text: str) -> str:
    """Convert title to URL-friendly slug."""
    import re

    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-")


async def seed_database(db: AsyncSession) -> None:
    """Populate the database with tags and sample problems.

    Skips seeding entirely if any problems already exist.
    """
    from app.config import settings
    from app.core.security import hash_password
    from app.models.user import User

    # Ensure default admin account exists
    admin_stmt = select(User).where(User.username == "admin")
    admin_res = await db.execute(admin_stmt)
    if admin_res.scalars().first() is None and "admin" in settings.ADMIN_USERNAMES:
        db.add(
            User(
                username="admin",
                email="admin@codeclash.local",
                password_hash=hash_password("admin12345"),
                is_admin=True,
            )
        )
        await db.commit()
        logger.info("Created default admin user (admin / admin12345)")

    count_result = await db.execute(select(func.count(Problem.id)))
    if (count_result.scalar() or 0) > 0:
        logger.info("Database already seeded — skipping")
        return

    logger.info("Seeding database with %d tags and %d problems …", len(TAG_NAMES), len(PROBLEMS))

    # Create tags
    tag_map: dict[str, Tag] = {}
    for name in TAG_NAMES:
        tag = Tag(name=name)
        db.add(tag)
        tag_map[name] = tag
    await db.flush()

    # Create problems with test cases and tag links
    for prob_data in PROBLEMS:
        problem = Problem(
            title=prob_data["title"],
            slug=_slugify(prob_data["title"]),
            description=prob_data["description"],
            input_format=prob_data["input_format"],
            output_format=prob_data["output_format"],
            constraints=prob_data["constraints"],
            difficulty=prob_data["difficulty"],
        )
        db.add(problem)
        await db.flush()

        # Link tags
        for tag_name in prob_data["tags"]:
            tag = tag_map.get(tag_name)
            if tag:
                db.add(ProblemTag(problem_id=problem.id, tag_id=tag.id))

        # Create test cases
        for tc in prob_data["test_cases"]:
            db.add(
                TestCase(
                    problem_id=problem.id,
                    input=tc["input"],
                    expected_output=tc["expected_output"],
                    is_sample=tc["is_sample"],
                )
            )

    await db.commit()
    logger.info("✅  Seed complete: %d problems created", len(PROBLEMS))
