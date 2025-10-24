"""API v1 router aggregation"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, voice, trip, budget

# Create main API router
api_router = APIRouter()

# Include authentication routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证 Authentication"]
)

# Include chat routes
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["聊天对话 Chat"]
)

# Include voice routes
api_router.include_router(
    voice.router,
    prefix="/voice",
    tags=["语音交互 Voice"]
)

# Include trip routes
api_router.include_router(
    trip.router,
    prefix="/trips",
    tags=["行程管理 Trips"]
)

# Include budget routes
api_router.include_router(
    budget.router,
    prefix="/budgets",
    tags=["费用管理 Budget"]
)

# Future: Include other route modules
# api_router.include_router(
#     agent.router,
#     prefix="/agent",
#     tags=["AG-UI Agent"]
# )
# api_router.include_router(
#     trip.router,
#     prefix="/trips",
#     tags=["行程管理 Trips"]
# )
# api_router.include_router(
#     budget.router,
#     prefix="/budget",
#     tags=["费用管理 Budget"]
# )

