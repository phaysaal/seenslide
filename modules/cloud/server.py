"""Cloud server FastAPI application."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request, Header, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os

from modules.cloud.session_manager import CloudSessionManager, SessionIDGenerator
from modules.cloud.slide_storage import CloudSlideStorage
from modules.cloud.database import init_db, close_db
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
    is_private: bool = Field(False, description="Whether session is private")
    password: Optional[str] = Field(None, min_length=6, max_length=128, description="Password for session protection")


class SessionResponse(BaseModel):
    """Response model for session info."""
    session_id: str
    presenter_name: str
    created_at: float
    status: str
    total_slides: int
    max_slides: int
    viewer_count: int
    is_private: bool
    access_type: str


class VerifyPasswordRequest(BaseModel):
    """Request model for verifying session password."""
    password: str = Field(..., min_length=1, max_length=128)


class VerifyPasswordResponse(BaseModel):
    """Response model for password verification."""
    valid: bool
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    details: Optional[str] = None


class SlideResponse(BaseModel):
    """Response model for slide info."""
    slide_id: str
    session_id: str
    slide_number: int
    timestamp: float
    width: int
    height: int
    file_size_bytes: int
    uploaded_at: float


class SlideListResponse(BaseModel):
    """Response model for list of slides."""
    session_id: str
    total_slides: int
    slides: list[SlideResponse]


# Global instances
session_manager: CloudSessionManager = None
slide_storage: CloudSlideStorage = None
rate_limiter: RateLimiter = None
token_manager: SessionTokenManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global session_manager, slide_storage, rate_limiter, token_manager

    # Startup
    logger.info("Starting SeenSlide Cloud Server")

    # Initialize database connection
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        logger.info("Initializing PostgreSQL database...")
        await init_db(database_url, run_migrations=True)
    else:
        logger.warning("DATABASE_URL not set, database will not be initialized")

    # Initialize managers
    storage_path = os.getenv("SEENSLIDE_STORAGE_PATH", "/tmp/seenslide_slides")

    session_manager = CloudSessionManager()
    slide_storage = CloudSlideStorage(storage_path=storage_path)

    # Load active sessions from database
    if database_url:
        await session_manager.load_active_sessions()

    # Rate limiter: 100 requests per minute per IP
    rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

    # Token manager for admin auth
    token_manager = SessionTokenManager(token_lifetime_hours=24)

    logger.info("Cloud server initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down SeenSlide Cloud Server")
    await close_db()


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
        stats = await session_manager.get_stats() if session_manager else {}
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
            session = await session_manager.create_session(
                presenter_name=body.presenter_name,
                presenter_email=body.presenter_email or "",
                max_slides=body.max_slides,
                settings=body.settings,
                is_private=body.is_private,
                password=body.password
            )

            # Save session to database
            await session_manager.save_session(session)

            logger.info(
                f"Session created: {session.session_id} "
                f"by {body.presenter_name} from {client_ip} "
                f"(access_type: {session.access_type})"
            )

            return SessionResponse(
                session_id=session.session_id,
                presenter_name=session.presenter_name,
                created_at=session.created_at,
                status=session.status,
                total_slides=session.total_slides,
                max_slides=session.max_slides,
                viewer_count=session.viewer_count,
                is_private=session.is_private,
                access_type=session.access_type
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
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            session_id=session.session_id,
            presenter_name=session.presenter_name,
            created_at=session.created_at,
            status=session.status,
            total_slides=session.total_slides,
            max_slides=session.max_slides,
            viewer_count=session.viewer_count,
            is_private=session.is_private,
            access_type=session.access_type
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
        if not await session_manager.end_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"Session ended: {session_id}")
        return {"message": "Session ended successfully", "session_id": session_id}

    @app.post(
        "/api/cloud/session/{session_id}/verify-password",
        response_model=VerifyPasswordResponse,
        responses={
            404: {"model": ErrorResponse, "description": "Session not found"},
            400: {"model": ErrorResponse, "description": "Invalid session ID"}
        }
    )
    @limiter.limit("30/minute")
    async def verify_session_password(
        request: Request,
        session_id: str,
        body: VerifyPasswordRequest
    ):
        """Verify password for a session.

        Args:
            session_id: The session ID
            body: Password verification request

        Returns:
            Verification result

        Rate limit: 30 requests per minute per IP.
        """
        # Validate session ID format
        if not SessionIDGenerator.is_valid(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Validate password
        is_valid, error_message = await session_manager.validate_session_password(
            session_id, body.password
        )

        if not is_valid and error_message == "Session not found":
            raise HTTPException(status_code=404, detail=error_message)

        return VerifyPasswordResponse(
            valid=is_valid,
            message=error_message if not is_valid else "Password verified"
        )

    @app.post(
        "/api/cloud/session/{session_id}/upload-slide",
        response_model=SlideResponse,
        responses={
            404: {"model": ErrorResponse, "description": "Session not found"},
            400: {"model": ErrorResponse, "description": "Invalid request"},
            413: {"model": ErrorResponse, "description": "File too large"}
        }
    )
    @limiter.limit("30/minute")
    async def upload_slide(
        request: Request,
        session_id: str,
        slide_number: int,
        file: UploadFile = File(...)
    ):
        """Upload a slide image to a session.

        Args:
            session_id: The session ID
            slide_number: Slide sequence number
            file: Image file (PNG, JPG, etc.)

        Returns:
            Uploaded slide information

        Rate limit: 30 requests per minute per IP.
        """
        # Validate session ID format
        if not SessionIDGenerator.is_valid(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check session capacity
        if not session.has_capacity():
            raise HTTPException(
                status_code=400,
                detail=f"Session has reached maximum slides ({session.max_slides})"
            )

        # Check file size (max 10MB)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")

        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        try:
            # Save slide
            slide = await slide_storage.save_slide(
                session_id=session_id,
                slide_number=slide_number,
                image_data=contents,
                generate_thumbnail=True
            )

            # Increment session slide count
            await session_manager.increment_slide_count(session_id)

            logger.info(f"Slide uploaded: {session_id}/slide_{slide_number}")

            return SlideResponse(
                slide_id=slide.slide_id,
                session_id=slide.session_id,
                slide_number=slide.slide_number,
                timestamp=slide.timestamp,
                width=slide.width,
                height=slide.height,
                file_size_bytes=slide.file_size_bytes,
                uploaded_at=slide.uploaded_at
            )

        except ValueError as e:
            logger.error(f"Failed to upload slide: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error uploading slide: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get(
        "/api/cloud/session/{session_id}/slides",
        response_model=SlideListResponse,
        responses={
            404: {"model": ErrorResponse, "description": "Session not found"},
            400: {"model": ErrorResponse, "description": "Invalid session ID"}
        }
    )
    @limiter.limit("60/minute")
    async def list_session_slides(request: Request, session_id: str):
        """List all slides for a session.

        Args:
            session_id: The session ID

        Returns:
            List of slides

        Rate limit: 60 requests per minute per IP.
        """
        # Validate session ID format
        if not SessionIDGenerator.is_valid(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Get session
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get slides
        slides = await slide_storage.list_slides(session_id)

        return SlideListResponse(
            session_id=session_id,
            total_slides=len(slides),
            slides=[
                SlideResponse(
                    slide_id=s.slide_id,
                    session_id=s.session_id,
                    slide_number=s.slide_number,
                    timestamp=s.timestamp,
                    width=s.width,
                    height=s.height,
                    file_size_bytes=s.file_size_bytes,
                    uploaded_at=s.uploaded_at
                )
                for s in slides
            ]
        )

    @app.get("/api/cloud/slides/{session_id}/{slide_number}")
    @limiter.limit("100/minute")
    async def get_slide_image(request: Request, session_id: str, slide_number: int):
        """Get slide image file.

        Args:
            session_id: The session ID
            slide_number: Slide number

        Returns:
            Slide image file

        Rate limit: 100 requests per minute per IP.
        """
        # Validate session ID format
        if not SessionIDGenerator.is_valid(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Get slide file
        image_data = slide_storage.get_slide_file(session_id, slide_number)
        if not image_data:
            raise HTTPException(status_code=404, detail="Slide not found")

        return Response(content=image_data, media_type="image/png")

    @app.get("/api/cloud/slides/{session_id}/{slide_number}/thumbnail")
    @limiter.limit("100/minute")
    async def get_slide_thumbnail(request: Request, session_id: str, slide_number: int):
        """Get slide thumbnail image.

        Args:
            session_id: The session ID
            slide_number: Slide number

        Returns:
            Thumbnail image file

        Rate limit: 100 requests per minute per IP.
        """
        # Validate session ID format
        if not SessionIDGenerator.is_valid(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Get thumbnail file
        image_data = slide_storage.get_thumbnail_file(session_id, slide_number)
        if not image_data:
            raise HTTPException(status_code=404, detail="Thumbnail not found")

        return Response(content=image_data, media_type="image/jpeg")

    @app.get("/api/cloud/sessions")
    @limiter.limit("20/minute")
    async def list_sessions(request: Request):
        """List all active sessions (admin only).

        This endpoint should be protected with authentication in production.

        Rate limit: 20 requests per minute per IP.
        """
        sessions = await session_manager.list_active_sessions()
        return {
            "sessions": [
                SessionResponse(
                    session_id=s.session_id,
                    presenter_name=s.presenter_name,
                    created_at=s.created_at,
                    status=s.status,
                    total_slides=s.total_slides,
                    max_slides=s.max_slides,
                    viewer_count=s.viewer_count,
                    is_private=s.is_private,
                    access_type=s.access_type
                )
                for s in sessions
            ]
        }

    @app.get("/api/cloud/stats")
    async def get_stats():
        """Get server statistics."""
        return session_manager.get_stats()

    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Viewer route (catch-all for session IDs)
    @app.get("/{session_id}", response_class=HTMLResponse)
    async def serve_viewer(session_id: str):
        """Serve the viewer page for a session.

        Args:
            session_id: Session ID in format XXX-NNNN

        Returns:
            Viewer HTML page
        """
        # Validate session ID format
        if not SessionIDGenerator.is_valid(session_id):
            raise HTTPException(status_code=404, detail="Invalid session ID format")

        # Serve viewer HTML
        viewer_path = static_dir / "viewer.html"
        if not viewer_path.exists():
            raise HTTPException(status_code=500, detail="Viewer not found")

        return FileResponse(viewer_path)

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
