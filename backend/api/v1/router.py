"""
API V1 Central Router
=====================

Aggregates and registers all V1 resource routers under the /api/v1 prefix.
"""

from fastapi import APIRouter

from backend.api.v1.endpoints import auth, health, sessions, therapist, chat, checkins, events
from backend.api.v1.endpoints import therapist_results

api_v1_router = APIRouter()

# Register endpoint sub-routers
api_v1_router.include_router(health.router, tags=["Health & Status"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(therapist.router, prefix="/therapist", tags=["Therapist"])
api_v1_router.include_router(
    therapist_results.router,
    prefix="/therapist",
    tags=["Therapist Results"],
)
api_v1_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_v1_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_v1_router.include_router(checkins.router, prefix="/checkins", tags=["Check-ins"])
api_v1_router.include_router(events.router, prefix="/events", tags=["Events"])

