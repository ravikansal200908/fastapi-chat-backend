from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from app.core.errors import (
    http_exception_handler,
    validation_exception_handler,
    APIError,
    RequestValidationError
)
from app.core.middleware import (
    RequestLoggingMiddleware,
    RequestValidationMiddleware,
    RateLimitMiddleware
)
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.mongodb import mongodb

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(RateLimitMiddleware)

# Add exception handlers
app.add_exception_handler(APIError, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
async def startup():
    """
    Initialize Redis connection, FastAPI cache, and MongoDB on startup.
    """
    # Initialize Redis
    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
        encoding="utf8",
        decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    
    # Initialize MongoDB
    await mongodb.connect_to_database()

@app.on_event("shutdown")
async def shutdown():
    """
    Close database connections on shutdown.
    """
    await mongodb.close_database_connection()

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
    - dict: Health status
    """
    return {
        "status": "healthy",
        "version": settings.VERSION
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    
    Parameters:
    - request: The request that caused the exception
    - exc: The unhandled exception
    
    Returns:
    - JSONResponse: Error response
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    ) 