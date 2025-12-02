"""
VigilAI Backend API
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from src.api.v1.router import api_router
from src.core.database import engine
from src.models.base import Base
from src.core.logging import setup_logging

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting VigilAI application...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down VigilAI application...")
    await engine.dispose()


app = FastAPI(
    title="VigilAI API",
    description="Competitive Intelligence & AIOps Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "vigilai-api"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VigilAI API",
        "docs": "/docs",
        "health": "/health"
    }
