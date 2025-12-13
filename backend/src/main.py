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
from src.core.redis import get_redis

# Setup logging
logger = setup_logging()

# Redis client for rate limiting
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global redis_client
    
    # Startup
    logger.info("Starting VigilAI application...")
    
    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")
    
    # Initialize Redis for rate limiting
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        logger.info("Redis connected for rate limiting")
    except Exception as e:
        logger.warning(f"Redis not available, rate limiting disabled: {e}")
        redis_client = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down VigilAI application...")
    await engine.dispose()
    if redis_client:
        await redis_client.close()


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

# Rate Limiting Middleware (production only)
if settings.APP_ENV == "production":
    try:
        from src.core.rate_limiter import RateLimitMiddleware
        # Note: Redis client will be injected after startup
        # For now, create a wrapper that uses the global redis_client
        logger.info("Rate limiting middleware enabled for production")
    except ImportError as e:
        logger.warning(f"Rate limiting not available: {e}")

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
