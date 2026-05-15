## 2025-05-15 - PIL Point Operation Optimization
**Learning:** Using a Look-Up Table (LUT) with `Image.point()` in Pillow is significantly faster than using a lambda function. For a 16MP image, this resulted in a ~1.2x speedup by avoiding the overhead of Python callbacks for every pixel.

**Action:** Prefer LUTs for point operations in Pillow, especially when dealing with high-resolution images or repetitive operations.

## 2025-05-15 - Quality vs. Performance Trade-off in OCR
**Learning:** Optimizing image preprocessing for speed (e.g., changing resampling from `LANCZOS` to `BILINEAR`) can be risky. While faster, lower-quality filters may degrade OCR accuracy by introducing blur or artifacts.

**Action:** In accuracy-critical paths like OCR preprocessing, prioritize high-quality filters unless benchmarks prove that faster alternatives maintain acceptable accuracy.

## 2026-05-15 - Optimization of Sequential Image Enhancements
**Learning:** Pillow's `ImageEnhance` operations return new image instances, making an explicit `image.copy()` before enhancement redundant. Furthermore, multiple sequential enhancements of the same type (like Contrast) can be combined by multiplying their factors, reducing the number of full-image pixel processing passes.
**Action:** Always check if a copy is truly needed before an enhancement and combine successive enhancement factors of the same type where mathematically appropriate.
