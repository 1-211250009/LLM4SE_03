"""API v1 router aggregation"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth

# Create main API router
api_router = APIRouter()

# Include authentication routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证 Authentication"]
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

