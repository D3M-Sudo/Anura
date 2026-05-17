# tests/test_performance_benchmarks.py
import pytest
import time
import os
from PIL import Image
from anura.utils.text_preprocessor import TextPreprocessor

class TestPerformanceBenchmarks:
    def setup_method(self):
        self.preprocessor = TextPreprocessor()

    def test_image_enhancement_latency(self):
        # Benchmark image enhancement for a 4K-ish image
        img = Image.new("RGB", (3840, 2160), color="white")

        start = time.perf_counter()
        enhanced = self.preprocessor.enhance_image(img)
        end = time.perf_counter()

        duration = end - start
        print(f"4K Image Enhancement Latency: {duration:.4f}s")
        # Ensure it's reasonably fast (< 2s on modern hardware, but be generous for CI)
        assert duration < 5.0

    def test_text_cleaning_latency(self):
        # Benchmark cleaning of a large text block
        large_text = "This is a TEST... " * 1000

        start = time.perf_counter()
        cleaned = self.preprocessor.clean_extracted_text(large_text)
        end = time.perf_counter()

        duration = end - start
        print(f"Large Text Cleaning Latency: {duration:.4f}s")
        assert duration < 1.0

    def test_memory_leak_check_repeated_enhancement(self):
        # Basic check for memory growth by running 50 iterations
        import gc
        try:
            import psutil
            process = psutil.Process(os.getpid())
            initial_mem = process.memory_info().rss

            img = Image.new("RGB", (1000, 1000), color="gray")
            for _ in range(50):
                enhanced = self.preprocessor.enhance_image(img)

            gc.collect()
            final_mem = process.memory_info().rss
            growth = final_mem - initial_mem
            print(f"Memory Growth after 50 iterations: {growth / 1024 / 1024:.2f} MB")

            # Allow some growth for fragmentation/caching but flag if excessive (> 100MB)
            assert growth < 100 * 1024 * 1024
        except ImportError:
            pytest.skip("psutil not installed, skipping memory leak check")
