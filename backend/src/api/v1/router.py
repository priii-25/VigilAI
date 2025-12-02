"""
Main API router aggregating all v1 endpoints
"""
from fastapi import APIRouter
from src.api.v1.endpoints import competitors, battlecards, logs, auth, dashboard

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(competitors.router, prefix="/competitors", tags=["Competitors"])
api_router.include_router(battlecards.router, prefix="/battlecards", tags=["Battlecards"])
api_router.include_router(logs.router, prefix="/logs", tags=["Log Analysis"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
