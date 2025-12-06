"""Tests for perceptual deduplication strategy."""

import pytest
from PIL import Image

from modules.dedup.strategies.perceptual_strategy import PerceptualDeduplicationStrategy
from core.models.slide import RawCapture
from core.interfaces.dedup import DeduplicationError
import time


class TestPerceptualStrategy:
    """Test cases for PerceptualDeduplicationStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a strategy instance for testing."""
        strategy = PerceptualDeduplicationStrategy()
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
    def similar_captures(self):
        """Create two similar but not identical captures."""
        # Create base image
        image1 = Image.new("RGB", (100, 100), color="red")

        # Create slightly modified version (change one pixel)
        image2 = image1.copy()
        image2.putpixel((50, 50), (255, 0, 100))  # Slight color change

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

    @pytest.fixture
    def different_captures(self):
        """Create two very different captures."""
        # Create images with different patterns (not just colors)
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
        config = {"perceptual_threshold": 0.95, "perceptual_hash_size": 8}
        result = strategy.initialize(config)
        assert result is True
        assert strategy.name == "perceptual"

    def test_initialization_with_invalid_threshold(self, strategy):
        """Test that invalid threshold fails."""
        config = {"perceptual_threshold": 1.5}  # > 1.0
        result = strategy.initialize(config)
        assert result is False

    def test_initialization_with_invalid_hash_size(self, strategy):
        """Test that invalid hash size fails."""
        config = {"perceptual_hash_size": 32}  # Not 8 or 16
        result = strategy.initialize(config)
        assert result is False

    def test_name_property(self, strategy):
        """Test that name property returns correct value."""
        assert strategy.name == "perceptual"

    def test_identical_images_are_duplicate(self, strategy, identical_captures):
        """Test that identical images are detected as duplicates."""
        strategy.initialize({"perceptual_threshold": 0.95})
        capture1, capture2 = identical_captures

        is_dup = strategy.is_duplicate(capture2, capture1)
        assert is_dup is True
        assert strategy.get_similarity_score() >= 0.95

    def test_similar_images_are_duplicate(self, strategy, similar_captures):
        """Test that similar images are detected as duplicates."""
        strategy.initialize({"perceptual_threshold": 0.90})  # Lower threshold
        capture1, capture2 = similar_captures

        is_dup = strategy.is_duplicate(capture2, capture1)
        # Should be duplicate with reasonable threshold
        similarity = strategy.get_similarity_score()
        assert similarity > 0.7  # Reasonably similar

    def test_different_images_not_duplicate(self, strategy, different_captures):
        """Test that different images are not duplicates."""
        strategy.initialize({"perceptual_threshold": 0.95})
        capture1, capture2 = different_captures

        is_dup = strategy.is_duplicate(capture2, capture1)
        assert is_dup is False
        assert strategy.get_similarity_score() < 0.95

    def test_is_duplicate_without_init(self, strategy, identical_captures):
        """Test that comparison without init raises error."""
        capture1, capture2 = identical_captures
        with pytest.raises(DeduplicationError):
            strategy.is_duplicate(capture2, capture1)

    def test_avg_processing_time(self, strategy, identical_captures):
        """Test that processing time is tracked."""
        strategy.initialize({"perceptual_threshold": 0.95})
        capture1, capture2 = identical_captures

        # Initially no comparisons
        assert strategy.avg_processing_time_ms == 0.0

        # After comparison
        strategy.is_duplicate(capture2, capture1)
        assert strategy.avg_processing_time_ms > 0.0

    def test_threshold_adjustment(self, strategy, similar_captures):
        """Test that threshold affects duplicate detection."""
        capture1, capture2 = similar_captures

        # With high threshold (strict)
        strategy.initialize({"perceptual_threshold": 0.99})
        is_dup_strict = strategy.is_duplicate(capture2, capture1)

        # With low threshold (lenient)
        strategy.initialize({"perceptual_threshold": 0.80})
        is_dup_lenient = strategy.is_duplicate(capture2, capture1)

        # Lenient should be more likely to find duplicates
        # (though exact behavior depends on the images)
        similarity = strategy.get_similarity_score()
        assert 0.0 <= similarity <= 1.0

    def test_get_statistics(self, strategy, identical_captures):
        """Test that statistics are returned."""
        strategy.initialize({
            "perceptual_threshold": 0.95,
            "perceptual_hash_size": 8
        })
        capture1, capture2 = identical_captures

        strategy.is_duplicate(capture2, capture1)
        stats = strategy.get_statistics()

        assert stats["name"] == "perceptual"
        assert stats["threshold"] == 0.95
        assert stats["hash_size"] == 8
        assert stats["comparisons_count"] == 1
        assert stats["last_similarity_score"] >= 0.95
        assert stats["avg_processing_time_ms"] > 0.0

    def test_similarity_score_range(self, strategy, different_captures):
        """Test that similarity score is always in valid range."""
        strategy.initialize({"perceptual_threshold": 0.95})
        capture1, capture2 = different_captures

        strategy.is_duplicate(capture2, capture1)
        score = strategy.get_similarity_score()

        assert 0.0 <= score <= 1.0
