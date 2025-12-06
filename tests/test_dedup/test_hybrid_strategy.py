"""Tests for hybrid deduplication strategy."""

import pytest
from PIL import Image

from modules.dedup.strategies.hybrid_strategy import HybridDeduplicationStrategy
from core.models.slide import RawCapture
from core.interfaces.dedup import DeduplicationError
import time


class TestHybridStrategy:
    """Test cases for HybridDeduplicationStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a strategy instance for testing."""
        strategy = HybridDeduplicationStrategy()
        return strategy

    @pytest.fixture
    def identical_captures(self):
        """Create two identical captures."""
        image = Image.new("RGB", (100, 100), color="red")
        capture1 = RawCapture(
            image=image,
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )
        capture2 = RawCapture(
            image=image.copy(),
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )
        return capture1, capture2

    @pytest.fixture
    def different_captures(self):
        """Create two different captures."""
        # Create images with different patterns
        from PIL import ImageDraw
        image1 = Image.new("RGB", (100, 100), color="white")
        draw1 = ImageDraw.Draw(image1)
        draw1.rectangle([10, 10, 90, 90], fill="red")

        image2 = Image.new("RGB", (100, 100), color="white")
        draw2 = ImageDraw.Draw(image2)
        draw2.ellipse([10, 10, 90, 90], fill="blue")

        capture1 = RawCapture(
            image=image1,
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )
        capture2 = RawCapture(
            image=image2,
            timestamp=time.time(),
            monitor_id=1,
            width=100,
            height=100
        )
        return capture1, capture2

    def test_initialization(self, strategy):
        """Test that strategy initializes correctly."""
        config = {
            "hash_algorithm": "md5",
            "perceptual_threshold": 0.95,
            "stages": ["hash", "perceptual"]
        }
        result = strategy.initialize(config)
        assert result is True
        assert strategy.name == "hybrid"

    def test_initialization_with_invalid_stages(self, strategy):
        """Test that invalid stages fail."""
        config = {"stages": ["invalid_stage"]}
        result = strategy.initialize(config)
        assert result is False

    def test_name_property(self, strategy):
        """Test that name property returns correct value."""
        assert strategy.name == "hybrid"

    def test_identical_images_detected_by_hash(self, strategy, identical_captures):
        """Test that identical images are caught by hash stage."""
        strategy.initialize({
            "hash_algorithm": "md5",
            "stages": ["hash", "perceptual"]
        })
        capture1, capture2 = identical_captures

        is_dup = strategy.is_duplicate(capture2, capture1)
        assert is_dup is True
        assert strategy.get_similarity_score() == 1.0

        # Check that hash stage caught it
        stats = strategy.get_statistics()
        assert stats["hash_matches"] >= 1

    def test_different_images_not_duplicate(self, strategy, different_captures):
        """Test that different images are not duplicates."""
        strategy.initialize({
            "hash_algorithm": "md5",
            "perceptual_threshold": 0.95,
            "stages": ["hash", "perceptual"]
        })
        capture1, capture2 = different_captures

        is_dup = strategy.is_duplicate(capture2, capture1)
        assert is_dup is False

    def test_is_duplicate_without_init(self, strategy, identical_captures):
        """Test that comparison without init raises error."""
        capture1, capture2 = identical_captures
        with pytest.raises(DeduplicationError):
            strategy.is_duplicate(capture2, capture1)

    def test_hash_only_stages(self, strategy, identical_captures):
        """Test with hash stage only."""
        strategy.initialize({
            "hash_algorithm": "md5",
            "stages": ["hash"]
        })
        capture1, capture2 = identical_captures

        is_dup = strategy.is_duplicate(capture2, capture1)
        assert is_dup is True

    def test_perceptual_only_stages(self, strategy, identical_captures):
        """Test with perceptual stage only."""
        strategy.initialize({
            "perceptual_threshold": 0.95,
            "stages": ["perceptual"]
        })
        capture1, capture2 = identical_captures

        is_dup = strategy.is_duplicate(capture2, capture1)
        assert is_dup is True

    def test_avg_processing_time(self, strategy, identical_captures):
        """Test that processing time is tracked."""
        strategy.initialize({
            "stages": ["hash", "perceptual"]
        })
        capture1, capture2 = identical_captures

        # Initially no comparisons
        assert strategy.avg_processing_time_ms == 0.0

        # After comparison
        strategy.is_duplicate(capture2, capture1)
        assert strategy.avg_processing_time_ms > 0.0

    def test_get_statistics(self, strategy, identical_captures):
        """Test that statistics are returned."""
        strategy.initialize({
            "hash_algorithm": "md5",
            "perceptual_threshold": 0.95,
            "stages": ["hash", "perceptual"]
        })
        capture1, capture2 = identical_captures

        # Do some comparisons
        strategy.is_duplicate(capture2, capture1)
        strategy.is_duplicate(capture1, capture2)

        stats = strategy.get_statistics()

        assert stats["name"] == "hybrid"
        assert stats["stages"] == ["hash", "perceptual"]
        assert stats["comparisons_count"] == 2
        assert stats["hash_matches"] >= 1
        assert "hash_match_rate" in stats
        assert stats["avg_processing_time_ms"] > 0.0

    def test_match_statistics(self, strategy, identical_captures, different_captures):
        """Test that match statistics are tracked correctly."""
        strategy.initialize({
            "hash_algorithm": "md5",
            "perceptual_threshold": 0.95,
            "stages": ["hash", "perceptual"]
        })

        # Test with identical captures (should match via hash)
        cap1, cap2 = identical_captures
        is_dup1 = strategy.is_duplicate(cap2, cap1)
        assert is_dup1 is True

        # Test with different captures (should not match)
        cap3, cap4 = different_captures
        is_dup2 = strategy.is_duplicate(cap4, cap3)
        assert is_dup2 is False

        stats = strategy.get_statistics()
        assert stats["hash_matches"] + stats["perceptual_matches"] + stats["no_matches"] == 2
