"""Tests for storage plugin registration."""

import pytest
import importlib

from core.registry.plugin_registry import PluginRegistry
from modules.storage.providers.filesystem_provider import FilesystemStorageProvider
from modules.storage.providers.sqlite_provider import SQLiteStorageProvider


class TestStoragePlugin:
    """Test cases for storage plugin registration."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Set up the plugin registry before each test."""
        # Get singleton instance
        registry = PluginRegistry()

        # Clear storage providers
        registry._storage_providers = {}

        # Re-import and reload module to trigger registration
        import modules.storage.plugin
        importlib.reload(modules.storage.plugin)

        yield

    def test_filesystem_provider_registered(self):
        """Test that filesystem provider is registered."""
        registry = PluginRegistry()
        provider = registry.get_storage_provider("filesystem")

        assert provider is not None
        assert provider == FilesystemStorageProvider

    def test_sqlite_provider_registered(self):
        """Test that sqlite provider is registered."""
        registry = PluginRegistry()
        provider = registry.get_storage_provider("sqlite")

        assert provider is not None
        assert provider == SQLiteStorageProvider

    def test_can_instantiate_filesystem_provider(self):
        """Test that registered filesystem provider can be instantiated."""
        registry = PluginRegistry()
        provider_class = registry.get_storage_provider("filesystem")

        provider = provider_class()
        assert provider is not None
        assert provider.name == "filesystem"

    def test_can_instantiate_sqlite_provider(self):
        """Test that registered sqlite provider can be instantiated."""
        registry = PluginRegistry()
        provider_class = registry.get_storage_provider("sqlite")

        provider = provider_class()
        assert provider is not None
        assert provider.name == "sqlite"
