"""Tests for capture plugin registration."""

import pytest
from core.registry.plugin_registry import PluginRegistry
from modules.capture.providers.mss_provider import MSSCaptureProvider


class TestCapturePlugin:
    """Test cases for capture plugin registration."""

    def test_mss_provider_registered(self):
        """Test that MSS provider is automatically registered."""
        # Import plugin to trigger registration
        import modules.capture.plugin

        registry = PluginRegistry()
        providers = registry.list_capture_providers()

        assert "mss" in providers

    def test_get_mss_provider(self):
        """Test that MSS provider can be retrieved."""
        import modules.capture.plugin

        registry = PluginRegistry()
        provider_class = registry.get_capture_provider("mss")

        assert provider_class is not None
        assert provider_class == MSSCaptureProvider

    def test_instantiate_provider(self):
        """Test that provider can be instantiated."""
        import modules.capture.plugin

        registry = PluginRegistry()
        provider_class = registry.get_capture_provider("mss")

        provider = provider_class()
        assert provider is not None
        assert provider.name == "mss"
