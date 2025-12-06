"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config():
    """Provide a sample configuration dictionary."""
    return {
        "capture": {
            "provider": "mss",
            "config": {
                "monitor_id": 1,
                "quality": 90,
                "format": "png",
            }
        },
        "deduplication": {
            "strategy": "hash",
            "config": {
                "hash_algorithm": "md5",
            }
        },
        "storage": {
            "provider": "filesystem",
            "config": {
                "base_path": "/tmp/test_seenslide",
                "database_type": "sqlite",
            }
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8080,
        },
        "logging": {
            "level": "INFO",
        }
    }
