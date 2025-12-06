"""Tests for hash-based deduplication strategy."""

import pytest
from PIL import Image

from modules.dedup.strategies.hash_strategy import HashDeduplicationStrategy
from core.models.slide import RawCapture
from core.interfaces.dedup import DeduplicationError
import time


class TestHashStrategy:
    """Test cases for HashDeduplicationStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a strategy instance for testing."""
        strategy = HashDeduplicationStrategy()
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
        image1 = Image.new("RGB", (100, 100), color="red")
        image2 = Image.new("RGB", (100, 100), color="blue")
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
        config = {"hash_algorithm": "md5"}
        result = strategy.initialize(config)
        assert result is True
        assert strategy.name == "hash"

    def test_initialization_with_sha256(self, strategy):
        """Test initialization with SHA256."""
        config = {"hash_algorithm": "sha256"}
        result = strategy.initialize(config)
        assert result is True

    def test_initialization_with_invalid_algorithm(self, strategy):
        """Test that invalid algorithm fails."""
        config = {"hash_algorithm": "invalid"}
        result = strategy.initialize(config)
        assert result is False

    def test_name_property(self, strategy):
        """Test that name property returns correct value."""
        assert strategy.name == "hash"

    def test_identical_images_are_duplicate(self, strategy, identical_captures):
        """Test that identical images are detected as duplicates."""
        strategy.initialize({"hash_algorithm": "md5"})
        capture1, capture2 = identical_captures

        is_dup = strategy.is_duplicate(capture2, capture1)
        assert is_dup is True
        assert strategy.get_similarity_score() == 1.0

    def test_different_images_not_duplicate(self, strategy, different_captures):
        """Test that different images are not duplicates."""
        strategy.initialize({"hash_algorithm": "md5"})
        capture1, capture2 = different_captures

        is_dup = strategy.is_duplicate(capture2, capture1)
        assert is_dup is False
        assert strategy.get_similarity_score() == 0.0

    def test_is_duplicate_without_init(self, strategy, identical_captures):
        """Test that comparison without init raises error."""
        capture1, capture2 = identical_captures
        with pytest.raises(DeduplicationError):
            strategy.is_duplicate(capture2, capture1)

    def test_avg_processing_time(self, strategy, identical_captures):
        """Test that processing time is tracked."""
        strategy.initialize({"hash_algorithm": "md5"})
        capture1, capture2 = identical_captures

        # Initially no comparisons
        assert strategy.avg_processing_time_ms == 0.0

        # After comparison
        strategy.is_duplicate(capture2, capture1)
        assert strategy.avg_processing_time_ms > 0.0

    def test_multiple_comparisons(self, strategy, identical_captures):
        """Test multiple comparisons."""
        strategy.initialize({"hash_algorithm": "md5"})
        capture1, capture2 = identical_captures

        # First comparison
        is_dup1 = strategy.is_duplicate(capture2, capture1)
        assert is_dup1 is True

        # Second comparison
        is_dup2 = strategy.is_duplicate(capture1, capture2)
        assert is_dup2 is True

        # Average should be calculated from both
        assert strategy.avg_processing_time_ms > 0.0

    def test_get_statistics(self, strategy, identical_captures):
        """Test that statistics are returned."""
        strategy.initialize({"hash_algorithm": "sha256"})
        capture1, capture2 = identical_captures

        strategy.is_duplicate(capture2, capture1)
        stats = strategy.get_statistics()

        assert stats["name"] == "hash"
        assert stats["algorithm"] == "sha256"
        assert stats["comparisons_count"] == 1
        assert stats["last_similarity_score"] == 1.0
        assert stats["avg_processing_time_ms"] > 0.0

    def test_slightly_different_images_not_duplicate(self, strategy):
        """Test that even slightly different images are not duplicates."""
        strategy.initialize({"hash_algorithm": "md5"})

        # Create two images that differ by one pixel
        image1 = Image.new("RGB", (100, 100), color="red")
        image2 = image1.copy()
        image2.putpixel((50, 50), (0, 0, 255))  # Change one pixel

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

        is_dup = strategy.is_duplicate(capture2, capture1)
        assert is_dup is False
