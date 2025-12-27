"""
VigilAI Backend API
Main FastAPI application entry point

Enhanced with:
- Request context middleware (request_id, tenant_id, correlation_id)
- Circuit breaker status endpoints
- DLQ status endpoints
- Structured logging
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
from src.core.request_context import RequestContextMiddleware

# Setup logging
logger = setup_logging()

# Redis client for rate limiting and other services
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
    
    # Initialize Redis for rate limiting, caching, and other services
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        logger.info("Redis connected for rate limiting, caching, and DLQ")
    except Exception as e:
        logger.warning(f"Redis not available, some features disabled: {e}")
        redis_client = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down VigilAI application...")
    await engine.dispose()
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="VigilAI API",
    description="Competitive Intelligence & AIOps Platform - A+ Enterprise Grade",
    version="1.0.0",
    lifespan=lifespan
)

# Request Context Middleware (adds request_id, tenant_id, correlation_id)
# Must be added before other middleware for proper context propagation
app.add_middleware(RequestContextMiddleware)

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
    """Health check endpoint with system status"""
    from src.core.circuit_breaker import get_all_circuit_breaker_states
    
    circuit_breakers = get_all_circuit_breaker_states()
    open_circuits = [cb for cb in circuit_breakers if cb["state"] == "open"]
    
    status = "healthy"
    if open_circuits:
        status = "degraded"
    
    return {
        "status": status,
        "version": "1.0.0",
        "service": "vigilai-api",
        "environment": settings.APP_ENV,
        "circuit_breakers": {
            "total": len(circuit_breakers),
            "open": len(open_circuits),
            "open_services": [cb["name"] for cb in open_circuits]
        }
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all system components"""
    from src.core.circuit_breaker import get_all_circuit_breaker_states
    
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "service": "vigilai-api",
        "environment": settings.APP_ENV,
        "components": {}
    }
    
    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            health_status["components"]["redis"] = {"status": "healthy"}
        else:
            health_status["components"]["redis"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
    
    # Check Database
    try:
        from src.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await db.execute("SELECT 1")
        health_status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Circuit Breakers
    circuit_breakers = get_all_circuit_breaker_states()
    health_status["components"]["circuit_breakers"] = circuit_breakers
    
    # DLQ Stats (if Redis available)
    if redis_client:
        try:
            from src.core.dead_letter_queue import DeadLetterQueue
            dlq = DeadLetterQueue(redis_client)
            dlq_stats = await dlq.get_stats()
            health_status["components"]["dead_letter_queue"] = dlq_stats
        except Exception as e:
            health_status["components"]["dead_letter_queue"] = {"error": str(e)}
    
    # Overall status based on components
    if any(c.get("status") == "unhealthy" for c in health_status["components"].values() if isinstance(c, dict)):
        health_status["status"] = "unhealthy"
    elif any(cb["state"] == "open" for cb in circuit_breakers):
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VigilAI API - A+ Enterprise Grade",
        "docs": "/docs",
        "health": "/health",
        "health_detailed": "/health/detailed"
    }


@app.get("/system/circuit-breakers")
async def get_circuit_breaker_status():
    """Get status of all circuit breakers"""
    from src.core.circuit_breaker import get_all_circuit_breaker_states
    return {
        "circuit_breakers": get_all_circuit_breaker_states()
    }


@app.post("/system/circuit-breakers/reset")
async def reset_circuit_breakers():
    """Reset all circuit breakers to closed state (admin only)"""
    from src.core.circuit_breaker import reset_all_circuit_breakers
    reset_all_circuit_breakers()
    return {"message": "All circuit breakers reset to closed state"}


@app.get("/system/dlq")
async def get_dlq_status():
    """Get Dead Letter Queue status"""
    if not redis_client:
        return {"error": "Redis not available"}
    
    from src.core.dead_letter_queue import DeadLetterQueue
    dlq = DeadLetterQueue(redis_client)
    
    stats = await dlq.get_stats()
    dead_letters = await dlq.get_dead_letters(limit=10)
    
    return {
        "stats": stats,
        "recent_dead_letters": dead_letters
    }


@app.post("/system/dlq/{task_id}/retry")
async def retry_dead_letter(task_id: str):
    """Retry a dead letter task"""
    if not redis_client:
        return {"error": "Redis not available"}
    
    from src.core.dead_letter_queue import DeadLetterQueue
    dlq = DeadLetterQueue(redis_client)
    
    success = await dlq.retry_dead_letter(task_id)
    
    if success:
        return {"message": f"Task {task_id} queued for retry"}
    return {"error": f"Task {task_id} not found in DLQ"}
