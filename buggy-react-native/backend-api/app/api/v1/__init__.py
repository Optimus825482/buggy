"""
API v1 Router
"""
from fastapi import APIRouter
from app.api.v1 import auth, locations, shuttles, requests, users, websocket

# Ana v1 router
api_router = APIRouter()

# Auth endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Location endpoints
api_router.include_router(
    locations.router,
    prefix="/locations",
    tags=["Locations"]
)

# Shuttle endpoints
api_router.include_router(
    shuttles.router,
    prefix="/shuttles",
    tags=["Shuttles"]
)

# Request endpoints
api_router.include_router(
    requests.router,
    prefix="/requests",
    tags=["Requests"]
)

# User endpoints
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# WebSocket endpoint
api_router.include_router(
    websocket.router,
    tags=["WebSocket"]
)

__all__ = ["api_router"]
