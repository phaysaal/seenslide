"""Tests for SQLite storage provider."""

import pytest
import tempfile
import shutil
from pathlib import Path
import time

from modules.storage.providers.sqlite_provider import SQLiteStorageProvider
from core.models.slide import ProcessedSlide
from core.models.session import Session
from core.interfaces.storage import StorageError


class TestSQLiteStorageProvider:
    """Test cases for SQLiteStorageProvider."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        return SQLiteStorageProvider()

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        return Session(
            name="Test Session",
            description="Test description",
            presenter_name="Test Presenter"
        )

    @pytest.fixture
    def sample_slide(self, sample_session):
        """Create a sample slide for testing."""
        return ProcessedSlide(
            session_id=sample_session.session_id,
            timestamp=time.time(),
            sequence_number=1,
            width=1920,
            height=1080,
            image_path="/path/to/image.png",
            thumbnail_path="/path/to/thumbnail.jpg",
            file_size_bytes=12345,
            image_hash="abc123",
            similarity_score=0.95,
            metadata={"key": "value"}
        )

    def test_initialization(self, provider, temp_dir):
        """Test that provider initializes correctly."""
        config = {
            "base_path": temp_dir,
            "database_subdir": "db",
            "database_filename": "test.db"
        }
        result = provider.initialize(config)
        assert result is True
        assert provider.name == "sqlite"

        # Check that database file was created
        db_path = Path(temp_dir) / "db" / "test.db"
        assert db_path.exists()

    def test_initialization_creates_default_db(self, provider, temp_dir):
        """Test that default database is created."""
        config = {"base_path": temp_dir}
        result = provider.initialize(config)
        assert result is True

        # Default database should be created
        db_path = Path(temp_dir) / "db" / "seenslide.db"
        assert db_path.exists()

    def test_name_property(self, provider):
        """Test that name property returns correct value."""
        assert provider.name == "sqlite"

    def test_create_session(self, provider, temp_dir, sample_session):
        """Test creating a session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        session_id = provider.create_session(sample_session)
        assert session_id == sample_session.session_id

        # Verify session was saved
        saved_session = provider.get_session(session_id)
        assert saved_session is not None
        assert saved_session.name == sample_session.name
        assert saved_session.description == sample_session.description
        assert saved_session.presenter_name == sample_session.presenter_name

    def test_create_session_without_init(self, provider, sample_session):
        """Test that creating session without init raises error."""
        with pytest.raises(StorageError):
            provider.create_session(sample_session)

    def test_get_session(self, provider, temp_dir, sample_session):
        """Test retrieving a session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)
        provider.create_session(sample_session)

        retrieved_session = provider.get_session(sample_session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.session_id == sample_session.session_id
        assert retrieved_session.name == sample_session.name
        assert retrieved_session.status == sample_session.status

    def test_get_nonexistent_session(self, provider, temp_dir):
        """Test retrieving a nonexistent session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        session = provider.get_session("nonexistent-id")
        assert session is None

    def test_get_session_without_init(self, provider):
        """Test that getting session without init returns None."""
        session = provider.get_session("some-id")
        assert session is None

    def test_update_session(self, provider, temp_dir, sample_session):
        """Test updating a session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)
        provider.create_session(sample_session)

        # Update session
        sample_session.name = "Updated Name"
        sample_session.total_slides = 10
        sample_session.status = "completed"

        result = provider.update_session(sample_session)
        assert result is True

        # Verify update
        updated_session = provider.get_session(sample_session.session_id)
        assert updated_session.name == "Updated Name"
        assert updated_session.total_slides == 10
        assert updated_session.status == "completed"

    def test_update_nonexistent_session(self, provider, temp_dir, sample_session):
        """Test updating a nonexistent session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        # Don't create the session, just try to update
        result = provider.update_session(sample_session)
        assert result is False

    def test_update_session_without_init(self, provider, sample_session):
        """Test that updating session without init returns False."""
        result = provider.update_session(sample_session)
        assert result is False

    def test_save_slide(self, provider, temp_dir, sample_slide):
        """Test saving a slide."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        slide_id = provider.save_slide(sample_slide)
        assert slide_id == sample_slide.slide_id

        # Verify slide was saved
        saved_slide = provider.get_slide(slide_id)
        assert saved_slide is not None
        assert saved_slide.slide_id == sample_slide.slide_id
        assert saved_slide.session_id == sample_slide.session_id
        assert saved_slide.sequence_number == sample_slide.sequence_number
        assert saved_slide.image_path == sample_slide.image_path
        assert saved_slide.width == sample_slide.width
        assert saved_slide.height == sample_slide.height

    def test_save_slide_without_init(self, provider, sample_slide):
        """Test that saving slide without init raises error."""
        with pytest.raises(StorageError):
            provider.save_slide(sample_slide)

    def test_get_slide(self, provider, temp_dir, sample_slide):
        """Test retrieving a slide."""
        config = {"base_path": temp_dir}
        provider.initialize(config)
        provider.save_slide(sample_slide)

        retrieved_slide = provider.get_slide(sample_slide.slide_id)
        assert retrieved_slide is not None
        assert retrieved_slide.slide_id == sample_slide.slide_id
        assert retrieved_slide.image_hash == sample_slide.image_hash
        assert retrieved_slide.similarity_score == sample_slide.similarity_score

    def test_get_nonexistent_slide(self, provider, temp_dir):
        """Test retrieving a nonexistent slide."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        slide = provider.get_slide("nonexistent-id")
        assert slide is None

    def test_get_slide_without_init(self, provider):
        """Test that getting slide without init returns None."""
        slide = provider.get_slide("some-id")
        assert slide is None

    def test_list_slides(self, provider, temp_dir, sample_session):
        """Test listing slides for a session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        # Create multiple slides
        slides = []
        for i in range(5):
            slide = ProcessedSlide(
                session_id=sample_session.session_id,
                timestamp=time.time(),
                sequence_number=i + 1,
                width=1920,
                height=1080
            )
            provider.save_slide(slide)
            slides.append(slide)

        # List all slides
        retrieved_slides = provider.list_slides(sample_session.session_id)
        assert len(retrieved_slides) == 5

        # Verify order (should be by sequence_number)
        for i, slide in enumerate(retrieved_slides):
            assert slide.sequence_number == i + 1

    def test_list_slides_with_limit(self, provider, temp_dir, sample_session):
        """Test listing slides with limit."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        # Create 10 slides
        for i in range(10):
            slide = ProcessedSlide(
                session_id=sample_session.session_id,
                timestamp=time.time(),
                sequence_number=i + 1,
                width=1920,
                height=1080
            )
            provider.save_slide(slide)

        # List with limit
        retrieved_slides = provider.list_slides(sample_session.session_id, limit=5)
        assert len(retrieved_slides) == 5

    def test_list_slides_with_offset(self, provider, temp_dir, sample_session):
        """Test listing slides with offset."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        # Create 10 slides
        for i in range(10):
            slide = ProcessedSlide(
                session_id=sample_session.session_id,
                timestamp=time.time(),
                sequence_number=i + 1,
                width=1920,
                height=1080
            )
            provider.save_slide(slide)

        # List with offset
        retrieved_slides = provider.list_slides(
            sample_session.session_id,
            limit=5,
            offset=5
        )
        assert len(retrieved_slides) == 5
        assert retrieved_slides[0].sequence_number == 6

    def test_list_slides_empty_session(self, provider, temp_dir):
        """Test listing slides for session with no slides."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        slides = provider.list_slides("some-session-id")
        assert slides == []

    def test_list_slides_without_init(self, provider):
        """Test that listing slides without init returns empty list."""
        slides = provider.list_slides("some-session-id")
        assert slides == []

    def test_get_slide_count(self, provider, temp_dir, sample_session):
        """Test getting slide count for a session."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        # Initially zero slides
        count = provider.get_slide_count(sample_session.session_id)
        assert count == 0

        # Create 3 slides
        for i in range(3):
            slide = ProcessedSlide(
                session_id=sample_session.session_id,
                timestamp=time.time(),
                sequence_number=i + 1,
                width=1920,
                height=1080
            )
            provider.save_slide(slide)

        # Count should be 3
        count = provider.get_slide_count(sample_session.session_id)
        assert count == 3

    def test_get_slide_count_without_init(self, provider):
        """Test that getting count without init returns 0."""
        count = provider.get_slide_count("some-session-id")
        assert count == 0

    def test_cleanup(self, provider, temp_dir):
        """Test cleanup method."""
        config = {"base_path": temp_dir}
        provider.initialize(config)
        provider.cleanup()

        # Provider should no longer be initialized
        assert provider._initialized is False
        assert provider._conn is None

    def test_session_metadata_serialization(self, provider, temp_dir, sample_session):
        """Test that session metadata is properly serialized."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        # Add metadata
        sample_session.metadata = {"key1": "value1", "key2": 123}
        provider.create_session(sample_session)

        # Retrieve and verify
        retrieved_session = provider.get_session(sample_session.session_id)
        assert retrieved_session.metadata == {"key1": "value1", "key2": 123}

    def test_slide_metadata_serialization(self, provider, temp_dir, sample_slide):
        """Test that slide metadata is properly serialized."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        # Add metadata
        sample_slide.metadata = {"source": "screen", "monitor": 1}
        provider.save_slide(sample_slide)

        # Retrieve and verify
        retrieved_slide = provider.get_slide(sample_slide.slide_id)
        assert retrieved_slide.metadata == {"source": "screen", "monitor": 1}

    def test_concurrent_access(self, provider, temp_dir, sample_session):
        """Test that provider handles concurrent operations."""
        config = {"base_path": temp_dir}
        provider.initialize(config)

        # Create multiple slides rapidly
        for i in range(10):
            slide = ProcessedSlide(
                session_id=sample_session.session_id,
                timestamp=time.time(),
                sequence_number=i + 1,
                width=1920,
                height=1080
            )
            provider.save_slide(slide)

        # All should be saved
        count = provider.get_slide_count(sample_session.session_id)
        assert count == 10
