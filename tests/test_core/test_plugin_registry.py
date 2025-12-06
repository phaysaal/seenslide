"""Tests for the plugin registry."""

import pytest
from core.registry.plugin_registry import PluginRegistry
from core.interfaces.capture import ICaptureProvider


class MockCaptureProvider(ICaptureProvider):
    """Mock capture provider for testing."""

    def initialize(self, config):
        return True

    def list_monitors(self):
        return []

    def capture(self, monitor_id=None):
        pass

    def cleanup(self):
        pass

    @property
    def name(self):
        return "mock"

    @property
    def supported_platforms(self):
        return ["linux"]


class TestPluginRegistry:
    """Test cases for PluginRegistry."""

    def test_singleton(self):
        """Test that PluginRegistry is a singleton."""
        registry1 = PluginRegistry()
        registry2 = PluginRegistry()
        assert registry1 is registry2

    def test_register_capture_provider(self):
        """Test registering a capture provider."""
        registry = PluginRegistry()
        registry.register_capture_provider("mock", MockCaptureProvider)

        providers = registry.list_capture_providers()
        assert "mock" in providers

    def test_get_capture_provider(self):
        """Test retrieving a capture provider."""
        registry = PluginRegistry()
        registry.register_capture_provider("mock", MockCaptureProvider)

        provider_class = registry.get_capture_provider("mock")
        assert provider_class is MockCaptureProvider

    def test_get_nonexistent_provider(self):
        """Test that getting non-existent provider returns None."""
        registry = PluginRegistry()
        provider_class = registry.get_capture_provider("nonexistent")
        assert provider_class is None
