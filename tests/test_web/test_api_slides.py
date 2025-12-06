"""Tests for slides API endpoints."""

import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient
import time

from modules.web.app import create_app
from modules.web.state import AppState
from core.models.session import Session
from core.models.slide import ProcessedSlide


class TestSlidesAPI:
    """Test cases for slides API."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def app_state(self, temp_dir):
        """Create application state for testing."""
        config = {
            "base_path": temp_dir,
            "database_subdir": "db",
            "database_filename": "test.db",
            "images_subdir": "images",
            "thumbnails_subdir": "thumbnails",
            "create_thumbnails": True
        }
        state = AppState(config=config)
        # Also initialize filesystem provider
        state.get_fs_provider().initialize(config)
        return state

    @pytest.fixture
    def client(self, app_state):
        """Create test client."""
        app = create_app(app_state)
        return TestClient(app)

    @pytest.fixture
    def sample_session(self, app_state):
        """Create a sample session."""
        session = Session(name="Test Session")
        app_state.get_db_provider().create_session(session)
        app_state.get_fs_provider().create_session(session)
        return session

    @pytest.fixture
    def sample_slide(self, app_state, sample_session, temp_dir):
        """Create a sample slide."""
        # Create an image file
        image = Image.new("RGB", (100, 100), color="blue")
        temp_image_path = Path(temp_dir) / "test_image.png"
        image.save(temp_image_path, "PNG")

        # Create slide object
        slide = ProcessedSlide(
            session_id=sample_session.session_id,
            timestamp=time.time(),
            sequence_number=1,
            width=100,
            height=100,
            image_path=str(temp_image_path)
        )

        # Save slide
        app_state.get_fs_provider().save_slide(slide)
        app_state.get_db_provider().save_slide(slide)

        return slide

    def test_list_slides(self, client, sample_session, sample_slide):
        """Test listing slides."""
        response = client.get(f"/api/slides/{sample_session.session_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["slide_id"] == sample_slide.slide_id

    def test_list_slides_empty(self, client, sample_session):
        """Test listing slides for empty session."""
        response = client.get(f"/api/slides/{sample_session.session_id}")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_slides_with_limit(self, client, app_state, sample_session, temp_dir):
        """Test listing slides with limit."""
        # Create multiple slides
        for i in range(5):
            image = Image.new("RGB", (100, 100), color="blue")
            temp_image_path = Path(temp_dir) / f"test_image_{i}.png"
            image.save(temp_image_path, "PNG")

            slide = ProcessedSlide(
                session_id=sample_session.session_id,
                timestamp=time.time(),
                sequence_number=i + 1,
                width=100,
                height=100,
                image_path=str(temp_image_path)
            )
            app_state.get_fs_provider().save_slide(slide)
            app_state.get_db_provider().save_slide(slide)

        # List with limit
        response = client.get(f"/api/slides/{sample_session.session_id}?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_slide_count(self, client, sample_session, sample_slide):
        """Test getting slide count."""
        response = client.get(f"/api/slides/{sample_session.session_id}/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["session_id"] == sample_session.session_id

    def test_get_slide(self, client, sample_slide):
        """Test getting a specific slide."""
        response = client.get(f"/api/slides/slide/{sample_slide.slide_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["slide_id"] == sample_slide.slide_id

    def test_get_nonexistent_slide(self, client):
        """Test getting a nonexistent slide."""
        response = client.get("/api/slides/slide/nonexistent-id")
        assert response.status_code == 404

    def test_get_slide_image(self, client, sample_slide):
        """Test getting slide image."""
        response = client.get(f"/api/slides/image/{sample_slide.slide_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_get_slide_thumbnail(self, client, sample_slide):
        """Test getting slide thumbnail."""
        response = client.get(f"/api/slides/thumbnail/{sample_slide.slide_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"

    def test_get_nonexistent_image(self, client):
        """Test getting image for nonexistent slide."""
        response = client.get("/api/slides/image/nonexistent-id")
        assert response.status_code == 404

    def test_get_nonexistent_thumbnail(self, client):
        """Test getting thumbnail for nonexistent slide."""
        response = client.get("/api/slides/thumbnail/nonexistent-id")
        assert response.status_code == 404
