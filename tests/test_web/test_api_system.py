"""Tests for system API endpoints."""

import pytest
from fastapi.testclient import TestClient

from modules.web.app import create_app
from modules.web.state import AppState


class TestSystemAPI:
    """Test cases for system API."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app_state = AppState()
        app = create_app(app_state)
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_system_status(self, client):
        """Test system status endpoint."""
        response = client.get("/api/system/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "uptime_seconds" in data
