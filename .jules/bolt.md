## 2025-05-15 - PIL Point Operation Optimization
**Learning:** Using a Look-Up Table (LUT) with `Image.point()` in Pillow is significantly faster than using a lambda function. For a 16MP image, this resulted in a ~1.2x speedup by avoiding the overhead of Python callbacks for every pixel.

**Action:** Prefer LUTs for point operations in Pillow, especially when dealing with high-resolution images or repetitive operations.

## 2025-05-15 - Quality vs. Performance Trade-off in OCR
**Learning:** Optimizing image preprocessing for speed (e.g., changing resampling from `LANCZOS` to `BILINEAR`) can be risky. While faster, lower-quality filters may degrade OCR accuracy by introducing blur or artifacts.

**Action:** In accuracy-critical paths like OCR preprocessing, prioritize high-quality filters unless benchmarks prove that faster alternatives maintain acceptable accuracy.

## 2026-05-15 - Optimization of Sequential Image Enhancements
**Learning:** Pillow's `ImageEnhance` operations return new image instances, making an explicit `image.copy()` before enhancement redundant. Furthermore, multiple sequential enhancements of the same type (like Contrast) can be combined by multiplying their factors, reducing the number of full-image pixel processing passes.
**Action:** Always check if a copy is truly needed before an enhancement and combine successive enhancement factors of the same type where mathematically appropriate.

## 2026-05-15 - Regex and str.isascii() Optimization for URI Validation
**Learning:** Manual loops for character detection in Python are significantly slower than pre-compiled regular expressions (13x difference). Additionally, `str.isascii()` is much faster than the `try-except` encoding pattern (up to 20x faster) for ASCII validation.
**Action:** Use `re.search()` with pre-compiled patterns for character-set checks and prefer built-in string methods like `isascii()` over manual validation or exception-based checks.

## 2026-05-16 - Pre-compilation and PIL Mode Optimization
**Learning:** Pre-compiling regular expressions in a class constructor for frequently used utility methods (like text cleaning) avoids redundant parsing overhead. Additionally, PIL's `image.point(lut, "L")` is significantly faster (~1.6x) than `image.point(lut, "1").convert("L")` because it skips an intermediate 1-bit mode conversion.
**Action:** Always pre-compile regex patterns used in hot paths and avoid unnecessary image mode conversions in Pillow pipelines.

## 2026-05-17 - Whitespace and Capitalization Optimization
**Learning:** In Python, `" ".join(text.split())` is approximately 5x faster than using `re.sub(r"\s+", " ", text).strip()` for squashing internal whitespace and stripping leading/trailing ones. Additionally, `word.capitalize()` is more efficient and idiomatic than manual slicing for Title Case conversion.
**Action:** Prefer built-in string methods like `split()`, `join()`, and `capitalize()` over regex or manual slicing for common text normalization tasks.

## 2026-05-18 - QR Code Detection Downscaling Optimization
**Learning:** For high-resolution images (e.g., 4K), pyzbar's decode operation is significantly slower (up to 23x) than on downscaled images (e.g., 1024px). QR codes are designed to be resilient and can usually be detected reliably at lower resolutions.
**Action:** Implement a "fast path" for QR detection by downscaling high-resolution images before attempting decoding, while keeping the full-resolution detection as a fallback for cases where downscaling might lose critical detail.
