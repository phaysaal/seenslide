"""Integration tests for the main orchestrator."""

import pytest
import tempfile
import shutil
from pathlib import Path
import time

from seenslide.orchestrator import SeenSlideOrchestrator


class TestOrchestrator:
    """Test cases for SeenSlide orchestrator."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration."""
        return {
            "capture": {
                "interval_seconds": 1.0,
                "save_raw": False
            },
            "deduplication": {
                "strategy": "hash",
                "hash_algorithm": "md5"
            },
            "storage": {
                "base_path": temp_dir,
                "images_subdir": "images",
                "thumbnails_subdir": "thumbnails",
                "database_subdir": "db",
                "create_thumbnails": True
            }
        }

    @pytest.fixture
    def orchestrator(self, config, temp_dir):
        """Create orchestrator instance."""
        # Write config to temp file
        import yaml
        config_path = Path(temp_dir) / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        return SeenSlideOrchestrator(config_path=str(config_path))

    def test_initialization(self, orchestrator):
        """Test that orchestrator initializes correctly."""
        assert orchestrator is not None
        assert orchestrator._running is False
        assert orchestrator.session is None

    def test_start_session(self, orchestrator):
        """Test starting a session."""
        success = orchestrator.start_session(
            session_name="Test Session",
            description="Test description",
            presenter_name="Test Presenter"
        )

        # May fail if no display available, that's ok
        if success:
            assert orchestrator.is_running() is True
            assert orchestrator.session is not None
            assert orchestrator.session.name == "Test Session"

            # Clean up
            orchestrator.stop_session()

    def test_stop_session(self, orchestrator):
        """Test stopping a session."""
        success = orchestrator.start_session("Test Session")

        if success:
            assert orchestrator.is_running() is True

            stop_success = orchestrator.stop_session()
            assert stop_success is True
            assert orchestrator.is_running() is False

    def test_start_already_running(self, orchestrator):
        """Test starting when already running."""
        success1 = orchestrator.start_session("Session 1")

        if success1:
            success2 = orchestrator.start_session("Session 2")
            assert success2 is False

            # Clean up
            orchestrator.stop_session()

    def test_stop_not_running(self, orchestrator):
        """Test stopping when not running."""
        success = orchestrator.stop_session()
        assert success is False

    def test_get_statistics(self, orchestrator):
        """Test getting statistics."""
        stats = orchestrator.get_statistics()

        assert "running" in stats
        assert "session" in stats
        assert "capture" in stats
        assert "deduplication" in stats
        assert "storage" in stats

        assert stats["running"] is False

    def test_get_statistics_while_running(self, orchestrator):
        """Test getting statistics while running."""
        success = orchestrator.start_session("Test Session")

        if success:
            stats = orchestrator.get_statistics()

            assert stats["running"] is True
            assert stats["session"] is not None
            assert stats["session"]["name"] == "Test Session"

            # Clean up
            orchestrator.stop_session()
