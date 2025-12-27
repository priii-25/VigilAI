"""
Request context management for structured logging and tracing.

Provides request_id, tenant_id, and correlation_id across the application
for distributed tracing and multi-tenancy support.
"""
from contextvars import ContextVar
from typing import Optional, Callable
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


@dataclass
class RequestContext:
    """
    Context data for current request.
    
    Propagated through the entire request lifecycle and
    included in all log messages.
    """
    request_id: str
    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dict for logging context"""
        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id or self.request_id,
            "tenant_id": self.tenant_id or "default",
            "user_id": self.user_id or "anonymous"
        }
    
    def elapsed_ms(self) -> float:
        """Get elapsed time since request start in milliseconds"""
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000


# Context variable for request-scoped data
_request_context: ContextVar[Optional[RequestContext]] = ContextVar(
    'request_context', default=None
)


def get_request_context() -> Optional[RequestContext]:
    """Get current request context"""
    return _request_context.get()


def set_request_context(ctx: RequestContext):
    """Set request context"""
    _request_context.set(ctx)


def get_request_id() -> str:
    """Get current request ID or generate one"""
    ctx = get_request_context()
    return ctx.request_id if ctx else str(uuid.uuid4())


def get_tenant_id() -> Optional[str]:
    """Get current tenant ID"""
    ctx = get_request_context()
    return ctx.tenant_id if ctx else None


def get_correlation_id() -> str:
    """Get current correlation ID"""
    ctx = get_request_context()
    if ctx:
        return ctx.correlation_id or ctx.request_id
    return str(uuid.uuid4())


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to initialize request context with IDs.
    
    Adds the following headers/context:
    - X-Request-ID: Unique per request (generated if not provided)
    - X-Correlation-ID: For tracing across services (uses request_id if not provided)
    - X-Tenant-ID: For multi-tenancy
    
    Also logs request start/end with timing information.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Extract or generate IDs
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id = request.headers.get("X-Correlation-ID", request_id)
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # Get user_id from auth state if available
        user_id = getattr(request.state, "user_id", None)
        
        # Create context
        ctx = RequestContext(
            request_id=request_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            user_id=str(user_id) if user_id else None
        )
        set_request_context(ctx)
        
        # Log request start
        logger.bind(**ctx.to_dict()).info(
            f"Request started: {request.method} {request.url.path}"
        )
        
        # Process request with context in logs
        try:
            response = await call_next(request)
            
            # Log request end
            logger.bind(**ctx.to_dict()).info(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} elapsed={ctx.elapsed_ms():.2f}ms"
            )
            
            # Add IDs to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            logger.bind(**ctx.to_dict()).error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={str(e)} elapsed={ctx.elapsed_ms():.2f}ms"
            )
            raise
        finally:
            # Clear context
            set_request_context(None)


def log_with_context(level: str, message: str, **extra):
    """
    Log with automatic context injection.
    
    Automatically includes request_id, tenant_id, and correlation_id
    from the current request context.
    
    Usage:
        log_with_context("info", "Processing battlecard", battlecard_id=123)
    """
    ctx = get_request_context()
    context_data = ctx.to_dict() if ctx else {
        "request_id": "background",
        "tenant_id": "default",
        "correlation_id": "background",
        "user_id": "system"
    }
    context_data.update(extra)
    
    log_func = getattr(logger.bind(**context_data), level)
    log_func(message)


# Convenience logging functions
def log_info(message: str, **extra):
    """Log info with context"""
    log_with_context("info", message, **extra)


def log_warning(message: str, **extra):
    """Log warning with context"""
    log_with_context("warning", message, **extra)


def log_error(message: str, **extra):
    """Log error with context"""
    log_with_context("error", message, **extra)


def log_debug(message: str, **extra):
    """Log debug with context"""
    log_with_context("debug", message, **extra)


class BackgroundTaskContext:
    """
    Context manager for background tasks that need request context.
    
    Usage:
        async with BackgroundTaskContext(tenant_id="tenant123") as ctx:
            # All logs here will include the context
            await process_background_job()
    """
    
    def __init__(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.correlation_id = correlation_id
        self._previous_context = None
    
    async def __aenter__(self):
        self._previous_context = get_request_context()
        
        ctx = RequestContext(
            request_id=str(uuid.uuid4()),
            correlation_id=self.correlation_id or str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            user_id=self.user_id
        )
        set_request_context(ctx)
        return ctx
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        set_request_context(self._previous_context)
        return False


def with_context(
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None
):
    """
    Decorator to run function with request context.
    
    Useful for background tasks and Celery jobs.
    
    Usage:
        @with_context(tenant_id="default")
        async def background_job():
            log_info("Processing...")  # Will include context
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            async with BackgroundTaskContext(
                tenant_id=tenant_id,
                correlation_id=correlation_id
            ):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, create context directly
            ctx = RequestContext(
                request_id=str(uuid.uuid4()),
                correlation_id=correlation_id or str(uuid.uuid4()),
                tenant_id=tenant_id
            )
            set_request_context(ctx)
            try:
                return func(*args, **kwargs)
            finally:
                set_request_context(None)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
