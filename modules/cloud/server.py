"""Cloud server FastAPI application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os

from modules.cloud.session_manager import CloudSessionManager, SessionIDGenerator
from modules.cloud.security import (
    RateLimiter,
    SessionTokenManager,
    get_client_ip,
    limiter
)
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)


# Pydantic models for API
class CreateSessionRequest(BaseModel):
    """Request model for creating a session."""
    presenter_name: str = Field(..., min_length=1, max_length=100)
    presenter_email: Optional[str] = Field(None, max_length=100)
    max_slides: int = Field(50, ge=1, le=100)
    settings: Dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Response model for session info."""
    session_id: str
    presenter_name: str
    created_at: float
    status: str
    total_slides: int
    max_slides: int
    viewer_count: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    details: Optional[str] = None


# Global instances
session_manager: CloudSessionManager = None
rate_limiter: RateLimiter = None
token_manager: SessionTokenManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global session_manager, rate_limiter, token_manager

    # Startup
    logger.info("Starting SeenSlide Cloud Server")

    # Initialize managers
    db_path = os.getenv("SEENSLIDE_DB_PATH", "/tmp/seenslide_cloud.db")
    session_manager = CloudSessionManager(db_path=db_path)

    # Rate limiter: 100 requests per minute per IP
    rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

    # Token manager for admin auth
    token_manager = SessionTokenManager(token_lifetime_hours=24)

    logger.info("Cloud server initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down SeenSlide Cloud Server")


def create_cloud_app() -> FastAPI:
    """Create and configure the cloud FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="SeenSlide Cloud Server",
        description="Cloud-based presentation slide sharing and synchronization",
        version="1.0.0",
        lifespan=lifespan
    )

    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Routes
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": "SeenSlide Cloud Server",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        stats = session_manager.get_stats() if session_manager else {}
        return {
            "status": "healthy",
            "stats": stats
        }

    @app.post(
        "/api/cloud/session/create",
        response_model=SessionResponse,
        responses={
            429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
            400: {"model": ErrorResponse, "description": "Invalid request"}
        }
    )
    @limiter.limit("10/minute")
    async def create_session(
        request: Request,
        body: CreateSessionRequest
    ):
        """Create a new cloud session.

        This endpoint generates a unique session ID for a presentation.
        The presenter's local app will use this ID to upload slides.

        Rate limit: 10 requests per minute per IP.
        """
        try:
            # Check rate limit
            client_ip = get_client_ip(request)
            if not rate_limiter.check_rate_limit(f"create:{client_ip}"):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later."
                )

            # Create session
            session = session_manager.create_session(
                presenter_name=body.presenter_name,
                presenter_email=body.presenter_email or "",
                max_slides=body.max_slides,
                settings=body.settings
            )

            logger.info(
                f"Session created: {session.session_id} "
                f"by {body.presenter_name} from {client_ip}"
            )

            return SessionResponse(
                session_id=session.session_id,
                presenter_name=session.presenter_name,
                created_at=session.created_at,
                status=session.status,
                total_slides=session.total_slides,
                max_slides=session.max_slides,
                viewer_count=session.viewer_count
            )

        except ValueError as e:
            logger.error(f"Failed to create session: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error creating session: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get(
        "/api/cloud/session/{session_id}",
        response_model=SessionResponse,
        responses={
            404: {"model": ErrorResponse, "description": "Session not found"},
            400: {"model": ErrorResponse, "description": "Invalid session ID"}
        }
    )
    @limiter.limit("60/minute")
    async def get_session_info(request: Request, session_id: str):
        """Get information about a session.

        Args:
            session_id: The session ID (format: XXX-NNNN)

        Returns:
            Session information

        Rate limit: 60 requests per minute per IP.
        """
        # Validate session ID format
        if not SessionIDGenerator.is_valid(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            session_id=session.session_id,
            presenter_name=session.presenter_name,
            created_at=session.created_at,
            status=session.status,
            total_slides=session.total_slides,
            max_slides=session.max_slides,
            viewer_count=session.viewer_count
        )

    @app.delete(
        "/api/cloud/session/{session_id}",
        responses={
            200: {"description": "Session ended successfully"},
            404: {"model": ErrorResponse, "description": "Session not found"},
            400: {"model": ErrorResponse, "description": "Invalid session ID"}
        }
    )
    @limiter.limit("10/minute")
    async def end_session(request: Request, session_id: str):
        """End a session.

        Args:
            session_id: The session ID to end

        Returns:
            Success message

        Rate limit: 10 requests per minute per IP.
        """
        # Validate session ID format
        if not SessionIDGenerator.is_valid(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # End session
        if not session_manager.end_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"Session ended: {session_id}")
        return {"message": "Session ended successfully", "session_id": session_id}

    @app.get("/api/cloud/sessions")
    @limiter.limit("20/minute")
    async def list_sessions(request: Request):
        """List all active sessions (admin only).

        This endpoint should be protected with authentication in production.

        Rate limit: 20 requests per minute per IP.
        """
        sessions = session_manager.list_active_sessions()
        return {
            "sessions": [
                SessionResponse(
                    session_id=s.session_id,
                    presenter_name=s.presenter_name,
                    created_at=s.created_at,
                    status=s.status,
                    total_slides=s.total_slides,
                    max_slides=s.max_slides,
                    viewer_count=s.viewer_count
                )
                for s in sessions
            ]
        }

    @app.get("/api/cloud/stats")
    async def get_stats():
        """Get server statistics."""
        return session_manager.get_stats()

    return app


def run_cloud_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False
):
    """Run the cloud server.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
    """
    import uvicorn

    app = create_cloud_app()

    logger.info(f"Starting cloud server on {host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="SeenSlide Cloud Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Port to bind to (default: PORT env var or 8000)"
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    run_cloud_server(
        host=args.host,
        port=args.port,
        reload=args.reload
    )
