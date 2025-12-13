"""Data models for cloud sessions."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import time


@dataclass
class CloudSession:
    """Represents a cloud-based presentation session.

    Attributes:
        session_id: Unique 7-character session identifier
        presenter_name: Name of the presenter
        presenter_email: Email of the presenter (optional)
        created_at: Unix timestamp when session was created
        last_active: Unix timestamp of last activity
        status: Session status (active, ended, expired)
        total_slides: Number of slides uploaded
        max_slides: Maximum allowed slides (default 50)
        viewer_count: Current number of connected viewers
        settings: Session settings (capture interval, etc.)
        metadata: Additional metadata
        is_private: Whether session is private (requires password)
        password_hash: Hashed password for private sessions
        password_salt: Salt used for password hashing
        access_type: Type of access control (public, private, password_protected)
    """
    session_id: str
    presenter_name: str = ""
    presenter_email: str = ""
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    status: str = "active"  # active, ended, expired
    total_slides: int = 0
    max_slides: int = 50
    viewer_count: int = 0
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_private: bool = False
    password_hash: Optional[str] = None
    password_salt: Optional[str] = None
    access_type: str = "public"  # public, private, password_protected

    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == "active"

    def has_capacity(self) -> bool:
        """Check if session can accept more slides."""
        return self.total_slides < self.max_slides

    def update_activity(self):
        """Update last active timestamp."""
        self.last_active = time.time()

    def increment_slides(self):
        """Increment slide count."""
        if self.has_capacity():
            self.total_slides += 1
            self.update_activity()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "presenter_name": self.presenter_name,
            "presenter_email": self.presenter_email,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "status": self.status,
            "total_slides": self.total_slides,
            "max_slides": self.max_slides,
            "viewer_count": self.viewer_count,
            "settings": self.settings,
            "metadata": self.metadata,
            "is_private": self.is_private,
            "password_hash": self.password_hash,
            "password_salt": self.password_salt,
            "access_type": self.access_type,
        }

    def to_public_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for public API (excludes sensitive data)."""
        return {
            "session_id": self.session_id,
            "presenter_name": self.presenter_name,
            "created_at": self.created_at,
            "status": self.status,
            "total_slides": self.total_slides,
            "max_slides": self.max_slides,
            "viewer_count": self.viewer_count,
            "is_private": self.is_private,
            "access_type": self.access_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CloudSession":
        """Create instance from dictionary."""
        return cls(
            session_id=data["session_id"],
            presenter_name=data.get("presenter_name", ""),
            presenter_email=data.get("presenter_email", ""),
            created_at=data.get("created_at", time.time()),
            last_active=data.get("last_active", time.time()),
            status=data.get("status", "active"),
            total_slides=data.get("total_slides", 0),
            max_slides=data.get("max_slides", 50),
            viewer_count=data.get("viewer_count", 0),
            settings=data.get("settings", {}),
            metadata=data.get("metadata", {}),
            is_private=data.get("is_private", False),
            password_hash=data.get("password_hash"),
            password_salt=data.get("password_salt"),
            access_type=data.get("access_type", "public"),
        )


@dataclass
class CloudSlide:
    """Represents a slide in a cloud session.

    Attributes:
        slide_id: Unique identifier for the slide
        session_id: ID of the session this slide belongs to
        slide_number: Sequence number (1, 2, 3, ...)
        timestamp: Unix timestamp when uploaded
        file_path: Path to the slide image file
        thumbnail_path: Path to the thumbnail image
        width: Image width in pixels
        height: Image height in pixels
        file_size_bytes: Size in bytes
        uploaded_at: Unix timestamp when uploaded to cloud
        metadata: Additional metadata
    """
    slide_id: str
    session_id: str
    slide_number: int
    timestamp: float
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    width: int = 0
    height: int = 0
    file_size_bytes: int = 0
    uploaded_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "slide_id": self.slide_id,
            "session_id": self.session_id,
            "slide_number": self.slide_number,
            "timestamp": self.timestamp,
            "file_path": self.file_path,
            "thumbnail_path": self.thumbnail_path,
            "width": self.width,
            "height": self.height,
            "file_size_bytes": self.file_size_bytes,
            "uploaded_at": self.uploaded_at,
            "metadata": self.metadata,
        }
