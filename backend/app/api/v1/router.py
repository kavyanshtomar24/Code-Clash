"""
V1 API router — aggregates all sub-routers under ``/api/v1``.
"""

from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.battles import router as battles_router
from app.api.v1.codeforces import router as codeforces_router
from app.api.v1.friends import router as friends_router
from app.api.v1.leaderboard import router as leaderboard_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.problems import router as problems_router
from app.api.v1.submissions import router as submissions_router
from app.api.v1.users import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
api_v1_router.include_router(problems_router, prefix="/problems", tags=["Problems"])
api_v1_router.include_router(submissions_router, prefix="/submissions", tags=["Submissions"])
api_v1_router.include_router(friends_router, prefix="/friends", tags=["Friends"])
api_v1_router.include_router(battles_router, prefix="/battles", tags=["Battles"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_v1_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_v1_router.include_router(codeforces_router, prefix="/codeforces", tags=["Codeforces"])
api_v1_router.include_router(leaderboard_router, prefix="/leaderboard", tags=["Leaderboard"])
