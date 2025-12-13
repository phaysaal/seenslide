"""Cloud slide storage manager."""

import logging
import time
import uuid
import os
import json
import asyncio
from pathlib import Path
from typing import Optional, List
from PIL import Image
import io

from modules.cloud.models import CloudSlide
from modules.cloud.database import get_db

logger = logging.getLogger(__name__)


class CloudSlideStorage:
    """Manages slide file storage and database persistence."""

    def __init__(
        self,
        storage_path: str = "/tmp/seenslide_slides"
    ):
        """Initialize slide storage.

        Args:
            storage_path: Base path for slide file storage
        """
        self.storage_path = Path(storage_path)
        self.lock = asyncio.Lock()

        # Create storage directories
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "slides").mkdir(exist_ok=True)
        (self.storage_path / "thumbnails").mkdir(exist_ok=True)

        logger.info(f"Slide storage initialized at {self.storage_path}")

    async def save_slide(
        self,
        session_id: str,
        slide_number: int,
        image_data: bytes,
        generate_thumbnail: bool = True
    ) -> CloudSlide:
        """Save a slide image and create database entry.

        Args:
            session_id: Session ID this slide belongs to
            slide_number: Slide sequence number
            image_data: Raw image bytes
            generate_thumbnail: Whether to generate thumbnail

        Returns:
            CloudSlide instance

        Raises:
            ValueError: If image is invalid or save fails
        """
        async with self.lock:
            try:
                # Generate unique slide ID
                slide_id = str(uuid.uuid4())

                # Open image to get dimensions
                img = Image.open(io.BytesIO(image_data))
                width, height = img.size
                file_size = len(image_data)

                # Create session directory
                session_dir = self.storage_path / "slides" / session_id
                session_dir.mkdir(parents=True, exist_ok=True)

                # Save full-size image
                file_path = session_dir / f"slide_{slide_number}.png"
                img.save(file_path, "PNG")

                # Generate thumbnail
                thumbnail_path = None
                if generate_thumbnail:
                    thumbnail_path = self._generate_thumbnail(
                        img, session_id, slide_number
                    )

                # Create CloudSlide instance
                slide = CloudSlide(
                    slide_id=slide_id,
                    session_id=session_id,
                    slide_number=slide_number,
                    timestamp=time.time(),
                    file_path=str(file_path),
                    thumbnail_path=thumbnail_path,
                    width=width,
                    height=height,
                    file_size_bytes=file_size,
                )

                # Save to database
                await self._save_slide_to_db(slide)

                logger.info(
                    f"Saved slide {slide_number} for session {session_id} "
                    f"({width}x{height}, {file_size} bytes)"
                )

                return slide

            except Exception as e:
                logger.error(f"Failed to save slide: {e}")
                raise ValueError(f"Failed to save slide: {e}")

    def _generate_thumbnail(
        self, img: Image.Image, session_id: str, slide_number: int
    ) -> str:
        """Generate thumbnail for slide.

        Args:
            img: PIL Image object
            session_id: Session ID
            slide_number: Slide number

        Returns:
            Path to thumbnail file
        """
        try:
            # Create thumbnail directory
            thumb_dir = self.storage_path / "thumbnails" / session_id
            thumb_dir.mkdir(parents=True, exist_ok=True)

            # Create thumbnail (320px width, maintain aspect ratio)
            thumb = img.copy()
            thumb.thumbnail((320, 320), Image.Resampling.LANCZOS)

            # Save thumbnail
            thumb_path = thumb_dir / f"thumb_{slide_number}.jpg"
            thumb.save(thumb_path, "JPEG", quality=85)

            return str(thumb_path)
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}")
            return None

    async def _save_slide_to_db(self, slide: CloudSlide):
        """Save slide metadata to database.

        Args:
            slide: CloudSlide to save
        """
        try:
            db = get_db()
            await db.execute("""
                INSERT INTO cloud_slides
                (slide_id, session_id, slide_number, timestamp,
                 file_path, thumbnail_path, width, height,
                 file_size_bytes, uploaded_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (session_id, slide_number) DO UPDATE SET
                    slide_id = EXCLUDED.slide_id,
                    timestamp = EXCLUDED.timestamp,
                    file_path = EXCLUDED.file_path,
                    thumbnail_path = EXCLUDED.thumbnail_path,
                    width = EXCLUDED.width,
                    height = EXCLUDED.height,
                    file_size_bytes = EXCLUDED.file_size_bytes,
                    uploaded_at = EXCLUDED.uploaded_at,
                    metadata = EXCLUDED.metadata
            """,
                slide.slide_id,
                slide.session_id,
                slide.slide_number,
                slide.timestamp,
                slide.file_path,
                slide.thumbnail_path,
                slide.width,
                slide.height,
                slide.file_size_bytes,
                slide.uploaded_at,
                json.dumps(slide.metadata),
            )
        except Exception as e:
            logger.error(f"Failed to save slide to database: {e}")
            raise

    async def get_slide(self, session_id: str, slide_number: int) -> Optional[CloudSlide]:
        """Get slide metadata from database.

        Args:
            session_id: Session ID
            slide_number: Slide number

        Returns:
            CloudSlide if found, None otherwise
        """
        try:
            db = get_db()
            row = await db.fetchrow("""
                SELECT slide_id, session_id, slide_number, timestamp,
                       file_path, thumbnail_path, width, height,
                       file_size_bytes, uploaded_at, metadata
                FROM cloud_slides
                WHERE session_id = $1 AND slide_number = $2
            """, session_id, slide_number)

            if not row:
                return None

            return CloudSlide(
                slide_id=row['slide_id'],
                session_id=row['session_id'],
                slide_number=row['slide_number'],
                timestamp=row['timestamp'],
                file_path=row['file_path'],
                thumbnail_path=row['thumbnail_path'],
                width=row['width'],
                height=row['height'],
                file_size_bytes=row['file_size_bytes'],
                uploaded_at=row['uploaded_at'],
                metadata=row['metadata'] or {},
            )
        except Exception as e:
            logger.error(f"Failed to get slide: {e}")
            return None

    async def list_slides(self, session_id: str) -> List[CloudSlide]:
        """List all slides for a session.

        Args:
            session_id: Session ID

        Returns:
            List of CloudSlide instances, ordered by slide_number
        """
        try:
            db = get_db()
            rows = await db.fetch("""
                SELECT slide_id, session_id, slide_number, timestamp,
                       file_path, thumbnail_path, width, height,
                       file_size_bytes, uploaded_at, metadata
                FROM cloud_slides
                WHERE session_id = $1
                ORDER BY slide_number ASC
            """, session_id)

            slides = []
            for row in rows:
                slides.append(CloudSlide(
                    slide_id=row['slide_id'],
                    session_id=row['session_id'],
                    slide_number=row['slide_number'],
                    timestamp=row['timestamp'],
                    file_path=row['file_path'],
                    thumbnail_path=row['thumbnail_path'],
                    width=row['width'],
                    height=row['height'],
                    file_size_bytes=row['file_size_bytes'],
                    uploaded_at=row['uploaded_at'],
                    metadata=row['metadata'] or {},
                ))

            return slides
        except Exception as e:
            logger.error(f"Failed to list slides: {e}")
            return []

    def get_slide_file(self, session_id: str, slide_number: int) -> Optional[bytes]:
        """Get slide image file data.

        Args:
            session_id: Session ID
            slide_number: Slide number

        Returns:
            Image bytes if found, None otherwise
        """
        file_path = self.storage_path / "slides" / session_id / f"slide_{slide_number}.png"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read slide file: {e}")
            return None

    def get_thumbnail_file(
        self, session_id: str, slide_number: int
    ) -> Optional[bytes]:
        """Get thumbnail image file data.

        Args:
            session_id: Session ID
            slide_number: Slide number

        Returns:
            Thumbnail bytes if found, None otherwise
        """
        thumb_path = self.storage_path / "thumbnails" / session_id / f"thumb_{slide_number}.jpg"

        if not thumb_path.exists():
            return None

        try:
            with open(thumb_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read thumbnail file: {e}")
            return None

    async def delete_slide(self, session_id: str, slide_number: int) -> bool:
        """Delete a slide and its files.

        Args:
            session_id: Session ID
            slide_number: Slide number

        Returns:
            True if deleted, False if not found
        """
        async with self.lock:
            slide = await self.get_slide(session_id, slide_number)
            if not slide:
                return False

            try:
                # Delete files
                if slide.file_path and os.path.exists(slide.file_path):
                    os.remove(slide.file_path)
                if slide.thumbnail_path and os.path.exists(slide.thumbnail_path):
                    os.remove(slide.thumbnail_path)

                # Delete from database
                db = get_db()
                await db.execute("""
                    DELETE FROM cloud_slides
                    WHERE session_id = $1 AND slide_number = $2
                """, session_id, slide_number)

                logger.info(f"Deleted slide {slide_number} from session {session_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete slide: {e}")
                return False
