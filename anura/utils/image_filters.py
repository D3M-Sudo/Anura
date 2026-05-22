# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from loguru import logger
from PIL import Image, ImageEnhance, ImageFilter, ImageStat


class ImageFilterBase(ABC):
    """Base class for all image processing filters."""

    @abstractmethod
    def apply(self, image: Image.Image) -> Image.Image:
        """Apply the filter to the image."""
        pass


class GrayscaleFilter(ImageFilterBase):
    """Converts image to grayscale."""

    def apply(self, image: Image.Image) -> Image.Image:
        if image.mode != "L":
            logger.debug("Filter: Converting to Grayscale")
            return image.convert("L")
        return image


class RescaleFilter(ImageFilterBase):
    """Rescales image if too small for reliable OCR."""

    def apply(self, image: Image.Image) -> Image.Image:
        width, height = image.size
        if width < 1000 or height < 1000:
            scale_factor = 2
            logger.debug(f"Filter: Rescaling image by {scale_factor}x")
            return image.resize((width * scale_factor, height * scale_factor), Image.Resampling.LANCZOS)
        return image


class AdaptiveEnhancementFilter(ImageFilterBase):
    """Applies combined brightness and contrast enhancement."""

    def apply(self, image: Image.Image) -> Image.Image:
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
        logger.debug(f"Filter: Applying Adaptive Enhancement (b={brightness_factor}, c={contrast_factor})")
        return image.point(lut)


class NoiseReductionFilter(ImageFilterBase):
    """Applies median filter for noise reduction."""

    def apply(self, image: Image.Image) -> Image.Image:
        logger.debug("Filter: Applying Median Noise Reduction")
        return image.filter(ImageFilter.MedianFilter(size=3))


class ThresholdingFilter(ImageFilterBase):
    """Applies intelligent thresholding based on histogram cutoff."""

    def apply(self, image: Image.Image) -> Image.Image:
        try:
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

            logger.debug("Filter: Applying Thresholding")
            return image.point(lut, "L")
        except Exception as e:
            logger.warning(f"Thresholding filter failed: {e}")
            return image


class SharpeningFilter(ImageFilterBase):
    """Applies final sharpening pass."""

    def apply(self, image: Image.Image) -> Image.Image:
        enhancer = ImageEnhance.Sharpness(image)
        logger.debug("Filter: Applying Sharpening")
        return enhancer.enhance(1.5)


class FilterChain:
    """Orchestrates a list of image filters."""

    def __init__(self, filters: list[ImageFilterBase] | None = None) -> None:
        self._filters = filters or []

    def add_filter(self, img_filter: ImageFilterBase) -> None:
        self._filters.append(img_filter)

    def apply(self, image: Image.Image) -> Image.Image:
        result = image
        for img_filter in self._filters:
            result = img_filter.apply(result)
        return result
