# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
import gc
import threading

from loguru import logger
from PIL import Image, ImageEnhance, ImageFilter, ImageStat


class ImageFilterBase(ABC):
    """Base class for all image processing filters."""

    @abstractmethod
    def apply(self, image: Image.Image, task_id: str | None = None) -> Image.Image:
        """Apply the filter to the image.

        Args:
            image: The image to process.
            task_id: Optional task ID for cooperative cancellation.
        """
        pass

    def _check_cancellation(self, task_id: str | None) -> None:
        """Check if the task has been cancelled and raise an exception if so."""
        if task_id:
            from anura.core.atomic_task_manager import get_atomic_manager

            if get_atomic_manager().is_cancelled(task_id):
                raise InterruptedError(f"Task {task_id} was cancelled")


class GrayscaleFilter(ImageFilterBase):
    """Converts image to grayscale."""

    def apply(self, image: Image.Image, task_id: str | None = None) -> Image.Image:
        self._check_cancellation(task_id)
        if image.mode != "L":
            logger.debug("Filter: Converting to Grayscale")
            return image.convert("L")
        return image


class RescaleFilter(ImageFilterBase):
    """Rescales image if too small for reliable OCR."""

    def apply(self, image: Image.Image, task_id: str | None = None) -> Image.Image:
        self._check_cancellation(task_id)
        width, height = image.size

        # Resource Guard: OOM Prevention for images > 20MP
        if width * height > 20_000_000:
            import psutil

            mem = psutil.virtual_memory()
            available = mem.available
            # Use percent of FREE memory (100 - percent_used)
            free_percent = 100.0 - mem.percent

            # Guard condition: < 15% RAM free OR < 500MB available
            if free_percent < 15 or available < 500 * 1024 * 1024:
                logger.warning(
                    f"Resource Guard: Blocking RescaleFilter for {width}x{height} image. "
                    f"Low memory detected: {free_percent:.1f}% free ({available // 1024 // 1024}MB available)."
                )
                # Return original image to prevent OOM
                return image

        if width < 1000 or height < 1000:
            scale_factor = 2
            logger.debug(f"Filter: Rescaling image by {scale_factor}x")
            return image.resize((width * scale_factor, height * scale_factor), Image.Resampling.LANCZOS)
        return image


class ContrastEnhancementFilter(ImageFilterBase):
    """Applies combined brightness and contrast enhancement."""

    def apply(self, image: Image.Image, task_id: str | None = None) -> Image.Image:
        self._check_cancellation(task_id)
        # Ensure image is grayscale for stats
        if image.mode != "L":
            image = image.convert("L")

        histogram = image.histogram()
        width, height = image.size
        total_pixels = width * height

        dark_pixels = sum(histogram[:128]) / total_pixels
        light_pixels = 1.0 - dark_pixels

        brightness_factor = 1.0
        contrast_factor = 1.2

        if dark_pixels > 0.7:
            brightness_factor = 1.3
        elif light_pixels > 0.8:
            contrast_factor = 1.68

        stat = ImageStat.Stat(image)
        mean = stat.mean[0]

        factor = brightness_factor * contrast_factor
        offset = brightness_factor * mean * (1 - contrast_factor)

        lut = [max(0, min(255, int(i * factor + offset))) for i in range(256)]
        self._check_cancellation(task_id)
        logger.debug(f"Filter: Applying Adaptive Enhancement (b={brightness_factor}, c={contrast_factor})")
        return image.point(lut)


class NoiseReductionFilter(ImageFilterBase):
    """Applies median filter for noise reduction."""

    def apply(self, image: Image.Image, task_id: str | None = None) -> Image.Image:
        self._check_cancellation(task_id)
        logger.debug("Filter: Applying Median Noise Reduction")
        return image.filter(ImageFilter.MedianFilter(size=3))


class AdaptiveThresholdFilter(ImageFilterBase):
    """Applies intelligent thresholding based on histogram cutoff."""

    def apply(self, image: Image.Image, task_id: str | None = None) -> Image.Image:
        try:
            self._check_cancellation(task_id)
            hist = image.histogram()
            width, height = image.size
            total_pixels = width * height
            cutoff = int(total_pixels * 0.02)

            low = 0
            temp_sum = 0
            for i in range(256):
                temp_sum += hist[i]
                if temp_sum > cutoff:
                    low = i
                    break

            high = 255
            temp_sum = 0
            for i in range(255, -1, -1):
                temp_sum += hist[i]
                if temp_sum > cutoff:
                    high = i
                    break

            if high <= low:
                lut = [0 if i < 128 else 255 for i in range(256)]
            else:
                threshold_val = low + (high - low) * 0.5
                lut = [0 if i < threshold_val else 255 for i in range(256)]

            self._check_cancellation(task_id)
            logger.debug("Filter: Applying Thresholding")
            return image.point(lut, "L")
        except InterruptedError:
            logger.debug("Anura Filter: Cancellation intercepted, re-raising InterruptedError")
            raise
        except Exception as e:
            logger.warning(f"Thresholding filter failed: {e}")
            return image


class SharpeningFilter(ImageFilterBase):
    """Applies final sharpening pass."""

    def apply(self, image: Image.Image, task_id: str | None = None) -> Image.Image:
        self._check_cancellation(task_id)
        enhancer = ImageEnhance.Sharpness(image)
        logger.debug("Filter: Applying Sharpening")
        return enhancer.enhance(1.5)


class FilterChain:
    """Orchestrates a list of image filters."""

    def __init__(self, filters: list[ImageFilterBase] | None = None) -> None:
        self._filters = filters or []

    def add_filter(self, img_filter: ImageFilterBase) -> None:
        self._filters.append(img_filter)

    def apply(self, image: Image.Image, task_id: str | None = None) -> Image.Image:
        result = image
        for img_filter in self._filters:
            prev_result = result
            result = img_filter.apply(result, task_id=task_id)

            # Explicitly release the previous image buffer if it's no longer needed
            # and it's not the same object as the new result.
            if prev_result is not image and prev_result is not result:
                prev_result.close()
                del prev_result
                # Occasional GC trigger for large buffers
                if result.size[0] * result.size[1] > 4000000:  # > 4MP
                    gc.collect()

        return result


_default_chain: FilterChain | None = None
_default_chain_lock = threading.Lock()


def get_default_filter_chain() -> FilterChain:
    """Build and cache the default OCR preprocessing filter chain.

    Returns:
        Singleton FilterChain configured for OCR preprocessing.
    """
    global _default_chain
    if _default_chain is None:
        with _default_chain_lock:
            if _default_chain is None:
                _default_chain = FilterChain(
                    [
                        GrayscaleFilter(),
                        RescaleFilter(),
                        ContrastEnhancementFilter(),
                        AdaptiveThresholdFilter(),
                    ]
                )
    return _default_chain
