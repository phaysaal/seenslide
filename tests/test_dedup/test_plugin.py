"""Tests for deduplication plugin registration."""

import pytest
from core.registry.plugin_registry import PluginRegistry
from modules.dedup.strategies.hash_strategy import HashDeduplicationStrategy
from modules.dedup.strategies.perceptual_strategy import PerceptualDeduplicationStrategy
from modules.dedup.strategies.hybrid_strategy import HybridDeduplicationStrategy


class TestDedupPlugin:
    """Test cases for dedup plugin registration."""

    def test_all_strategies_registered(self):
        """Test that all strategies are automatically registered."""
        # Import plugin to trigger registration
        import modules.dedup.plugin

        registry = PluginRegistry()
        strategies = registry.list_dedup_strategies()

        assert "hash" in strategies
        assert "perceptual" in strategies
        assert "hybrid" in strategies

    def test_get_hash_strategy(self):
        """Test that hash strategy can be retrieved."""
        import modules.dedup.plugin

        registry = PluginRegistry()
        strategy_class = registry.get_dedup_strategy("hash")

        assert strategy_class is not None
        assert strategy_class == HashDeduplicationStrategy

    def test_get_perceptual_strategy(self):
        """Test that perceptual strategy can be retrieved."""
        import modules.dedup.plugin

        registry = PluginRegistry()
        strategy_class = registry.get_dedup_strategy("perceptual")

        assert strategy_class is not None
        assert strategy_class == PerceptualDeduplicationStrategy

    def test_get_hybrid_strategy(self):
        """Test that hybrid strategy can be retrieved."""
        import modules.dedup.plugin

        registry = PluginRegistry()
        strategy_class = registry.get_dedup_strategy("hybrid")

        assert strategy_class is not None
        assert strategy_class == HybridDeduplicationStrategy

    def test_instantiate_hash_strategy(self):
        """Test that hash strategy can be instantiated."""
        import modules.dedup.plugin

        registry = PluginRegistry()
        strategy_class = registry.get_dedup_strategy("hash")

        strategy = strategy_class()
        assert strategy is not None
        assert strategy.name == "hash"

    def test_instantiate_perceptual_strategy(self):
        """Test that perceptual strategy can be instantiated."""
        import modules.dedup.plugin

        registry = PluginRegistry()
        strategy_class = registry.get_dedup_strategy("perceptual")

        strategy = strategy_class()
        assert strategy is not None
        assert strategy.name == "perceptual"

    def test_instantiate_hybrid_strategy(self):
        """Test that hybrid strategy can be instantiated."""
        import modules.dedup.plugin

        registry = PluginRegistry()
        strategy_class = registry.get_dedup_strategy("hybrid")

        strategy = strategy_class()
        assert strategy is not None
        assert strategy.name == "hybrid"
