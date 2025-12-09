"""Cloud session manager with ID generation and persistence."""

import sqlite3
import random
import string
import logging
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from threading import Lock

from modules.cloud.models import CloudSession

logger = logging.getLogger(__name__)


class SessionIDGenerator:
    """Generates unique 7-character session IDs."""

    @staticmethod
    def generate() -> str:
        """Generate a unique 7-character session ID.

        Format: XXX-NNNN (3 uppercase letters + 4 digits)
        Example: ABC-1234

        Returns:
            7-character session ID
        """
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=4))
        return f"{letters}-{numbers}"

    @staticmethod
    def is_valid(session_id: str) -> bool:
        """Validate session ID format.

        Args:
            session_id: Session ID to validate

        Returns:
            True if valid format, False otherwise
        """
        if not session_id or len(session_id) != 8:
            return False

        parts = session_id.split('-')
        if len(parts) != 2:
            return False

        letters, numbers = parts
        if len(letters) != 3 or len(numbers) != 4:
            return False

        if not letters.isupper() or not letters.isalpha():
            return False

        if not numbers.isdigit():
            return False

        return True


class CloudSessionManager:
    """Manages cloud sessions with in-memory registry and SQLite persistence."""

    def __init__(self, db_path: str = "/tmp/seenslide_cloud.db"):
        """Initialize session manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.sessions: Dict[str, CloudSession] = {}
        self.lock = Lock()
        self._init_database()
        self._load_active_sessions()

    def _init_database(self):
        """Initialize SQLite database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cloud_sessions (
                    session_id TEXT PRIMARY KEY,
                    presenter_name TEXT,
                    presenter_email TEXT,
                    created_at REAL,
                    last_active REAL,
                    status TEXT,
                    total_slides INTEGER,
                    max_slides INTEGER,
                    viewer_count INTEGER,
                    settings TEXT,
                    metadata TEXT
                )
            """)

            # Create index on status for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON cloud_sessions(status)
            """)

            # Create index on last_active for cleanup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_active
                ON cloud_sessions(last_active)
            """)

            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _load_active_sessions(self):
        """Load active sessions from database into memory."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT session_id, presenter_name, presenter_email,
                       created_at, last_active, status, total_slides,
                       max_slides, viewer_count, settings, metadata
                FROM cloud_sessions
                WHERE status = 'active'
            """)

            rows = cursor.fetchall()
            for row in rows:
                session = CloudSession(
                    session_id=row[0],
                    presenter_name=row[1] or "",
                    presenter_email=row[2] or "",
                    created_at=row[3],
                    last_active=row[4],
                    status=row[5],
                    total_slides=row[6],
                    max_slides=row[7],
                    viewer_count=row[8],
                    settings=eval(row[9]) if row[9] else {},
                    metadata=eval(row[10]) if row[10] else {},
                )
                self.sessions[session.session_id] = session

            conn.close()
            logger.info(f"Loaded {len(self.sessions)} active sessions from database")
        except Exception as e:
            logger.error(f"Failed to load active sessions: {e}")

    def create_session(
        self,
        presenter_name: str = "",
        presenter_email: str = "",
        max_slides: int = 50,
        settings: Dict[str, Any] = None
    ) -> CloudSession:
        """Create a new cloud session.

        Args:
            presenter_name: Name of the presenter
            presenter_email: Email of the presenter
            max_slides: Maximum allowed slides
            settings: Session settings

        Returns:
            Created CloudSession instance

        Raises:
            ValueError: If failed to generate unique ID after retries
        """
        with self.lock:
            # Generate unique session ID
            max_retries = 10
            session_id = None

            for _ in range(max_retries):
                candidate = SessionIDGenerator.generate()
                if candidate not in self.sessions:
                    session_id = candidate
                    break

            if not session_id:
                raise ValueError("Failed to generate unique session ID")

            # Create session
            session = CloudSession(
                session_id=session_id,
                presenter_name=presenter_name,
                presenter_email=presenter_email,
                max_slides=max_slides,
                settings=settings or {},
            )

            # Store in memory
            self.sessions[session_id] = session

            # Persist to database
            self._save_session(session)

            logger.info(f"Created session: {session_id}")
            return session

    def get_session(self, session_id: str) -> Optional[CloudSession]:
        """Get session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            CloudSession if found, None otherwise
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                session.update_activity()
                self._save_session(session)
            return session

    def end_session(self, session_id: str) -> bool:
        """End a session.

        Args:
            session_id: Session ID to end

        Returns:
            True if session was ended, False if not found
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if not session:
                return False

            session.status = "ended"
            session.update_activity()
            self._save_session(session)

            # Remove from active sessions
            del self.sessions[session_id]

            logger.info(f"Ended session: {session_id}")
            return True

    def update_viewer_count(self, session_id: str, count: int):
        """Update viewer count for a session.

        Args:
            session_id: Session ID
            count: New viewer count
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                session.viewer_count = count
                session.update_activity()
                self._save_session(session)

    def increment_slide_count(self, session_id: str) -> bool:
        """Increment slide count for a session.

        Args:
            session_id: Session ID

        Returns:
            True if incremented, False if session not found or at capacity
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if not session:
                return False

            if session.increment_slides():
                self._save_session(session)
                return True
            return False

    def list_active_sessions(self) -> List[CloudSession]:
        """Get list of all active sessions.

        Returns:
            List of active CloudSession instances
        """
        with self.lock:
            return list(self.sessions.values())

    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up old inactive sessions.

        Args:
            max_age_hours: Maximum age in hours before expiring
        """
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - (max_age_hours * 3600)

            expired = []
            for session_id, session in self.sessions.items():
                if session.last_active < cutoff_time:
                    session.status = "expired"
                    self._save_session(session)
                    expired.append(session_id)

            # Remove expired sessions from memory
            for session_id in expired:
                del self.sessions[session_id]

            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")

    def _save_session(self, session: CloudSession):
        """Save session to database.

        Args:
            session: CloudSession to save
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO cloud_sessions
                (session_id, presenter_name, presenter_email, created_at,
                 last_active, status, total_slides, max_slides, viewer_count,
                 settings, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.presenter_name,
                session.presenter_email,
                session.created_at,
                session.last_active,
                session.status,
                session.total_slides,
                session.max_slides,
                session.viewer_count,
                str(session.settings),
                str(session.metadata),
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics.

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            return {
                "active_sessions": len(self.sessions),
                "total_slides": sum(s.total_slides for s in self.sessions.values()),
                "total_viewers": sum(s.viewer_count for s in self.sessions.values()),
            }
