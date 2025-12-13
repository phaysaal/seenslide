"""Session privacy and password management for cloud sessions."""

import hashlib
import secrets
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SessionPrivacyManager:
    """Manages session privacy settings and password protection."""

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash a password with salt using PBKDF2-HMAC-SHA256.

        Args:
            password: Plain text password to hash
            salt: Optional salt (hex string). If None, generates new salt.

        Returns:
            Tuple of (password_hash, salt) both as hex strings
        """
        if salt is None:
            # Generate random 16-byte salt
            salt = secrets.token_hex(16)

        # Convert salt from hex to bytes
        salt_bytes = bytes.fromhex(salt)

        # Hash password with PBKDF2-HMAC-SHA256
        password_bytes = password.encode('utf-8')
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password_bytes,
            salt_bytes,
            iterations=100000
        )

        # Convert hash to hex string
        password_hash = hash_bytes.hex()

        return password_hash, salt

    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash.

        Args:
            password: Plain text password to verify
            password_hash: Stored password hash (hex string)
            salt: Salt used when hashing (hex string)

        Returns:
            True if password matches, False otherwise
        """
        try:
            # Hash the provided password with the same salt
            computed_hash, _ = SessionPrivacyManager.hash_password(password, salt)

            # Use constant-time comparison to prevent timing attacks
            return secrets.compare_digest(computed_hash, password_hash)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """Validate password meets minimum security requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"

        if len(password) > 128:
            return False, "Password must be less than 128 characters"

        # Add more requirements as needed
        # For now, keeping it simple for MVP

        return True, None

    @staticmethod
    def determine_access_type(is_private: bool, has_password: bool) -> str:
        """Determine access type based on privacy settings.

        Args:
            is_private: Whether session is marked as private
            has_password: Whether session has a password set

        Returns:
            Access type string: 'public', 'private', or 'password_protected'
        """
        if not is_private:
            return "public"
        elif has_password:
            return "password_protected"
        else:
            return "private"

    @staticmethod
    def can_access_session(
        access_type: str,
        password_provided: Optional[str] = None,
        password_hash: Optional[str] = None,
        password_salt: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Check if access to session is allowed.

        Args:
            access_type: Session access type
            password_provided: Password provided by user (if any)
            password_hash: Stored password hash (if any)
            password_salt: Stored password salt (if any)

        Returns:
            Tuple of (can_access, error_message)
        """
        # Public sessions are always accessible
        if access_type == "public":
            return True, None

        # Private sessions without password protection need authentication
        # (This will be implemented in later phases with user auth)
        if access_type == "private":
            return False, "This session is private and requires authentication"

        # Password-protected sessions require password
        if access_type == "password_protected":
            if not password_provided:
                return False, "Password required for this session"

            if not password_hash or not password_salt:
                logger.error("Password-protected session missing hash/salt")
                return False, "Session configuration error"

            # Verify password
            if SessionPrivacyManager.verify_password(
                password_provided, password_hash, password_salt
            ):
                return True, None
            else:
                return False, "Incorrect password"

        # Unknown access type
        return False, "Invalid session configuration"
