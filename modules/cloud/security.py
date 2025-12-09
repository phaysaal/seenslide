"""Security utilities for cloud server."""

import time
import hashlib
import secrets
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limit.

        Args:
            client_id: Client identifier (IP address, session ID, etc.)

        Returns:
            True if within limit, False if exceeded
        """
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            # Clean old requests
            if client_id in self.requests:
                self.requests[client_id] = [
                    req_time for req_time in self.requests[client_id]
                    if req_time > cutoff_time
                ]

            # Check limit
            if len(self.requests[client_id]) >= self.max_requests:
                return False

            # Record request
            self.requests[client_id].append(current_time)
            return True

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client.

        Args:
            client_id: Client identifier

        Returns:
            Number of remaining requests
        """
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            if client_id in self.requests:
                self.requests[client_id] = [
                    req_time for req_time in self.requests[client_id]
                    if req_time > cutoff_time
                ]
                return max(0, self.max_requests - len(self.requests[client_id]))

            return self.max_requests


class SessionTokenManager:
    """Manages secure session tokens for admin authentication."""

    def __init__(self, token_lifetime_hours: int = 24):
        """Initialize token manager.

        Args:
            token_lifetime_hours: Token lifetime in hours
        """
        self.token_lifetime_hours = token_lifetime_hours
        self.tokens: Dict[str, Dict] = {}
        self.lock = Lock()

    def create_token(self, username: str, session_id: str) -> str:
        """Create a new session token.

        Args:
            username: Admin username
            session_id: Session ID

        Returns:
            Secure token string
        """
        with self.lock:
            # Generate secure token
            token = secrets.token_urlsafe(32)

            # Store token info
            self.tokens[token] = {
                "username": username,
                "session_id": session_id,
                "created_at": time.time(),
                "expires_at": time.time() + (self.token_lifetime_hours * 3600),
            }

            return token

    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate a session token.

        Args:
            token: Token to validate

        Returns:
            Token info dict if valid, None otherwise
        """
        with self.lock:
            if token not in self.tokens:
                return None

            token_info = self.tokens[token]

            # Check expiration
            if time.time() > token_info["expires_at"]:
                del self.tokens[token]
                return None

            return token_info

    def revoke_token(self, token: str):
        """Revoke a session token.

        Args:
            token: Token to revoke
        """
        with self.lock:
            if token in self.tokens:
                del self.tokens[token]

    def cleanup_expired(self):
        """Clean up expired tokens."""
        with self.lock:
            current_time = time.time()
            expired = [
                token for token, info in self.tokens.items()
                if current_time > info["expires_at"]
            ]

            for token in expired:
                del self.tokens[token]


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash a password with salt.

    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)

    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )

    return hashed.hex(), salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify a password against a hash.

    Args:
        password: Plain text password to verify
        hashed: Hashed password
        salt: Salt used for hashing

    Returns:
        True if password matches, False otherwise
    """
    test_hash, _ = hash_password(password, salt)
    return test_hash == hashed


def get_client_ip(request: Request) -> str:
    """Get client IP address from request.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (for proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct client
    return request.client.host if request.client else "unknown"


# Create rate limiter for FastAPI endpoints
limiter = Limiter(key_func=get_remote_address)
