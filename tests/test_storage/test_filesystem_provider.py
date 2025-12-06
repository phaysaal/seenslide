"""Tests for filesystem storage provider."""

import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import time

from modules.storage.providers.filesystem_provider import FilesystemStorageProvider
from core.models.slide import ProcessedSlide
from core.models.session import Session
from core.interfaces.storage import StorageError


class TestFilesystemStorageProvider:
    """Test cases for FilesystemStorageProvider."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        return FilesystemStorageProvider()

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        return Session(
            name="Test Session",
            description="Test description"
        )

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        return Image.new("RGB", (100, 100), color="blue")

    @pytest.fixture
    def sample_slide(self, sample_session, temp_dir):
        """Create a sample slide for testing."""
        # Create a temporary image file
        image = Image.new("RGB", (100, 100), color="red")
        temp_image_path = Path(temp_dir) / "temp_image.png"
        image.save(temp_image_path, "PNG")

        return ProcessedSlide(
            session_id=sample_session.session_id,
            timestamp=time.time(),
            sequence_number=1,
            width=100,
            height=100,
            image_path=str(temp_image_path)
        )

    def test_initialization(self, provider, temp_dir):
        """Test that provider initializes correctly."""
        config = {
            "base_path": temp_dir,
            "images_subdir": "images",
            "thumbnails_subdir": "thumbnails",
            "create_thumbnails": True,
            "thumbnail_width": 320
        }
        result = provider.initialize(config)
        assert result is True
        assert provider.name == "filesystem"

        # Check that directories were created
        assert (Path(temp_dir) / "images").exists()
        assert (Path(temp_dir) / "thumbnails").exists()

    def test_initialization_creates_default_dirs(self, provider, temp_dir):
        """Test that default directories are created."""
        config = {"base_path": temp_dir}
        result = provider.initialize(config)
        assert result is True

        # Default subdirectories should be created
        assert (Path(temp_dir) / "images").exists()
        assert (Path(temp_dir) / "thumbnails").exists()

    def test_name_property(self, provider):
        """Test that name property returns correct value."""
        assert provider.name == "filesystem"

    def test_create_session(self, provider, temp_dir, sample_session):
        """Test creating a session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        session_id = provider.create_session(sample_session)
        assert session_id == sample_session.session_id

        # Check that session directories were created
        session_images_dir = Path(temp_dir) / "images" / sample_session.session_id
        session_thumbnails_dir = Path(temp_dir) / "thumbnails" / sample_session.session_id
        assert session_images_dir.exists()
        assert session_thumbnails_dir.exists()

    def test_create_session_without_init(self, provider, sample_session):
        """Test that creating session without init raises error."""
        with pytest.raises(StorageError):
            provider.create_session(sample_session)

    def test_save_slide(self, provider, temp_dir, sample_slide):
        """Test saving a slide."""
        config = {
            "base_path": temp_dir,
            "create_thumbnails": True,
            "thumbnail_width": 320
        }
        provider.initialize(config)

        slide_id = provider.save_slide(sample_slide)
        assert slide_id == sample_slide.slide_id

        # Check that image was saved
        image_path = Path(sample_slide.image_path)
        assert image_path.exists()
        assert image_path.suffix == ".png"

        # Check that thumbnail was created
        thumbnail_path = Path(sample_slide.thumbnail_path)
        assert thumbnail_path.exists()
        assert thumbnail_path.suffix == ".jpg"

        # Check that file size was set
        assert sample_slide.file_size_bytes > 0

    def test_save_slide_without_thumbnail(self, provider, temp_dir, sample_slide):
        """Test saving a slide without creating thumbnail."""
        config = {
            "base_path": temp_dir,
            "create_thumbnails": False
        }
        provider.initialize(config)

        slide_id = provider.save_slide(sample_slide)
        assert slide_id == sample_slide.slide_id

        # Image should exist
        assert Path(sample_slide.image_path).exists()

        # Thumbnail should not be created
        assert sample_slide.thumbnail_path == ""

    def test_save_slide_without_init(self, provider, sample_slide):
        """Test that saving slide without init raises error."""
        with pytest.raises(StorageError):
            provider.save_slide(sample_slide)

    def test_save_slide_without_image_path(self, provider, temp_dir, sample_session):
        """Test that saving slide without image path raises error."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        slide = ProcessedSlide(
            session_id=sample_session.session_id,
            timestamp=time.time(),
            sequence_number=1,
            width=100,
            height=100,
            image_path=""  # No image path
        )

        with pytest.raises(StorageError):
            provider.save_slide(slide)

    def test_get_slide_count(self, provider, temp_dir, sample_session, sample_slide):
        """Test getting slide count for a session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)
        provider.create_session(sample_session)

        # Initially zero slides
        count = provider.get_slide_count(sample_session.session_id)
        assert count == 0

        # Save a slide
        provider.save_slide(sample_slide)

        # Count should be 1
        count = provider.get_slide_count(sample_session.session_id)
        assert count == 1

    def test_get_slide_count_nonexistent_session(self, provider, temp_dir):
        """Test getting count for nonexistent session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        count = provider.get_slide_count("nonexistent-session-id")
        assert count == 0

    def test_delete_session(self, provider, temp_dir, sample_session, sample_slide):
        """Test deleting a session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)
        provider.create_session(sample_session)
        provider.save_slide(sample_slide)

        # Session directories should exist
        session_images_dir = Path(temp_dir) / "images" / sample_session.session_id
        session_thumbnails_dir = Path(temp_dir) / "thumbnails" / sample_session.session_id
        assert session_images_dir.exists()
        assert session_thumbnails_dir.exists()

        # Delete session
        result = provider.delete_session(sample_session.session_id)
        assert result is True

        # Directories should be gone
        assert not session_images_dir.exists()
        assert not session_thumbnails_dir.exists()

    def test_delete_session_without_init(self, provider):
        """Test that deleting session without init returns False."""
        result = provider.delete_session("some-session-id")
        assert result is False

    def test_cleanup(self, provider, temp_dir):
        """Test cleanup method."""
        config = {"base_path": temp_dir}
        provider.initialize(config)
        provider.cleanup()

        # Provider should no longer be initialized
        assert provider._initialized is False

    def test_get_session_returns_none(self, provider, temp_dir):
        """Test that get_session returns None (not implemented)."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        session = provider.get_session("some-id")
        assert session is None

    def test_update_session_returns_true(self, provider, temp_dir, sample_session):
        """Test that update_session returns True (no-op)."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        result = provider.update_session(sample_session)
        assert result is True

    def test_list_slides_returns_empty(self, provider, temp_dir):
        """Test that list_slides returns empty list (not implemented)."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        slides = provider.list_slides("some-session-id")
        assert slides == []

    def test_thumbnail_dimensions(self, provider, temp_dir, sample_session):
        """Test that thumbnail has correct dimensions."""
        config = {
            "base_path": temp_dir,
            "create_thumbnails": True,
            "thumbnail_width": 200
        }
        provider.initialize(config)

        # Create a larger image (400x400) for thumbnail test
        image = Image.new("RGB", (400, 400), color="green")
        temp_image_path = Path(temp_dir) / "large_image.png"
        image.save(temp_image_path, "PNG")

        slide = ProcessedSlide(
            session_id=sample_session.session_id,
            timestamp=time.time(),
            sequence_number=1,
            width=400,
            height=400,
            image_path=str(temp_image_path)
        )

        provider.save_slide(slide)

        # Load thumbnail and check dimensions
        thumbnail = Image.open(slide.thumbnail_path)
        assert thumbnail.width == 200
        # Height should maintain aspect ratio (1:1 in this case)
        assert thumbnail.height == 200

    def test_thumbnail_quality(self, provider, temp_dir, sample_slide):
        """Test that thumbnail quality setting is applied."""
        config = {
            "base_path": temp_dir,
            "create_thumbnails": True,
            "thumbnail_quality": 50
        }
        provider.initialize(config)

        provider.save_slide(sample_slide)

        # Thumbnail should exist and be smaller due to lower quality
        thumbnail_path = Path(sample_slide.thumbnail_path)
        assert thumbnail_path.exists()
        assert thumbnail_path.stat().st_size > 0
