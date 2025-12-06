"""Tests for session API endpoints."""

import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from modules.web.app import create_app
from modules.web.state import AppState
from core.models.session import Session


class TestSessionsAPI:
    """Test cases for sessions API."""

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
            "database_filename": "test.db"
        }
        return AppState(config=config)

    @pytest.fixture
    def client(self, app_state):
        """Create test client."""
        app = create_app(app_state)
        return TestClient(app)

    def test_create_session(self, client):
        """Test creating a session."""
        response = client.post(
            "/api/sessions/",
            json={
                "name": "Test Session",
                "description": "Test description",
                "presenter_name": "Test Presenter"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Session"
        assert data["description"] == "Test description"
        assert data["presenter_name"] == "Test Presenter"
        assert "session_id" in data

    def test_create_session_minimal(self, client):
        """Test creating a session with minimal data."""
        response = client.post(
            "/api/sessions/",
            json={"name": "Minimal Session"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Session"
        assert data["description"] == ""

    def test_get_session(self, client):
        """Test getting a session."""
        # Create a session first
        create_response = client.post(
            "/api/sessions/",
            json={"name": "Test Session"}
        )
        session_id = create_response.json()["session_id"]

        # Get the session
        response = client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["name"] == "Test Session"

    def test_get_nonexistent_session(self, client):
        """Test getting a nonexistent session."""
        response = client.get("/api/sessions/nonexistent-id")
        assert response.status_code == 404

    def test_update_session(self, client):
        """Test updating a session."""
        # Create a session first
        create_response = client.post(
            "/api/sessions/",
            json={"name": "Original Name"}
        )
        session_id = create_response.json()["session_id"]

        # Update the session
        response = client.patch(
            f"/api/sessions/{session_id}",
            json={
                "name": "Updated Name",
                "status": "completed"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["status"] == "completed"

    def test_update_nonexistent_session(self, client):
        """Test updating a nonexistent session."""
        response = client.patch(
            "/api/sessions/nonexistent-id",
            json={"name": "New Name"}
        )
        assert response.status_code == 404

    def test_list_sessions(self, client):
        """Test listing sessions."""
        # Note: list_sessions returns empty list until implemented
        response = client.get("/api/sessions/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
