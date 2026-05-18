import pytest

pytest.importorskip("gi")






# tests/test_performance_enterprise.py
import os
import time

from PIL import Image

from anura.utils.text_preprocessor import TextPreprocessor


class TestPerformanceEnterprise:
    """
    Enterprise-grade performance and load tests.
    """

    @pytest.fixture
    def preprocessor(self):
        return TextPreprocessor()

    @pytest.mark.parametrize(
        "resolution",
        [
            (1920, 1080),  # 1080p
            (3840, 2160),  # 4K
        ],
    )
    def test_image_enhancement_latency(self, preprocessor, resolution):
        """Benchmark image enhancement latency for common resolutions."""
        img = Image.new("RGB", resolution, color="white")
        # Add some "text-like" noise
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        for i in range(100):
            draw.text((i * 10, i * 10), "Sample Text", fill="black")

        latencies = []
        for _ in range(5):  # 5 iterations for averaging
            start = time.perf_counter()
            preprocessor.enhance_image(img)
            latencies.append(time.perf_counter() - start)

        p50 = sorted(latencies)[len(latencies) // 2]
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\nResolution {resolution}: p50={p50:.4f}s, p95={p95:.4f}s")
        # Target: < 0.6s for 4K (allowing for environment noise)
        if resolution == (3840, 2160):
            assert p50 < 0.6

    def test_text_cleaning_load(self, preprocessor):
        """Test text cleaning performance with a large payload."""
        large_text = ("Hello world! " * 10000) + "DONE."  # ~130KB

        start = time.perf_counter()
        cleaned = preprocessor.clean_extracted_text(large_text)
        duration = time.perf_counter() - start

        print(f"\nLarge text cleaning (130KB): {duration:.4f}s")
        assert duration < 0.1  # Should be very fast with split/join optimization
        assert cleaned.endswith("DONE.")

    def test_memory_growth_simulated(self, preprocessor):
        """Check for memory growth over repeated operations."""
        import psutil

        process = psutil.Process(os.getpid())

        img = Image.new("RGB", (1000, 1000), color="white")

        initial_mem = process.memory_info().rss
        for _ in range(50):
            preprocessor.enhance_image(img)

        final_mem = process.memory_info().rss
        growth = (final_mem - initial_mem) / 1024 / 1024  # MB

        print(f"\nMemory growth after 50 iterations: {growth:.2f} MB")
        # Negligible growth allowed (allocator overhead)
        assert growth < 10.0
