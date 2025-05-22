import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.2f}s"
            )
            
            return response
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise

class RequestValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add request validation logic here
        # For example, check content type, validate headers, etc.
        
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return Response(
                    content='{"error": "Content-Type must be application/json"}',
                    status_code=415,
                    media_type="application/json"
                )
        
        return await call_next(request)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, rate_limit: int = 100, time_window: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.requests = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean up old requests
        self.requests = {
            ip: timestamps 
            for ip, timestamps in self.requests.items()
            if current_time - timestamps[-1] < self.time_window
        }
        
        # Check rate limit
        if client_ip in self.requests:
            timestamps = self.requests[client_ip]
            if len(timestamps) >= self.rate_limit:
                return Response(
                    content='{"error": "Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json"
                )
            timestamps.append(current_time)
        else:
            self.requests[client_ip] = [current_time]
        
        return await call_next(request) 