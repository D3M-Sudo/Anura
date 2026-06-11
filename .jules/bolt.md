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

## 2026-05-19 - Multiline Regex and Lambda Callback Performance
**Learning:** Replacing Python line-by-line loops with `re.sub` using `re.MULTILINE` can yield a ~2.7x speedup for artifact removal on large text blocks. However, when using `re.MULTILINE`, using `[ \t]` instead of `\s` is critical to avoid swallowing newlines. Furthermore, combining multiple simple `re.sub` calls into a single call with a lambda callback might not provide significant gains due to the overhead of Python callbacks, often making multiple C-optimized passes faster.
**Action:** Prefer multiline regex for bulk text processing but avoid `\s` if line structure must be preserved. Use multiple `re.sub` calls for simple string replacements instead of a single call with a Python callback.

## 2026-05-20 - Combined Image Enhancement LUT Optimization
**Learning:** Consolidating multiple sequential image processing steps (Brightness, Contrast, Autocontrast, Thresholding) into single-pass Look-Up Tables (LUTs) significantly reduces total pixel traversals. Combining Brightness and Contrast into one linear formula and simulating Autocontrast via histogram bounds for Thresholding yields a measurable speedup (~28% on 4K-like images).
**Action:** When performing sequential linear or threshold-based image transformations, derive a single mathematical mapping and apply it via `image.point(lut)` to minimize processing overhead.

## 2026-05-28 - Histogram-based Statistics Optimization
**Learning:** Calculating image statistics (like the mean) directly from a pre-computed histogram is significantly faster (~2x on 4K images) than using `ImageStat.Stat(image)`. `ImageStat.Stat` often triggers its own full-image traversal if the internal cache is cold or invalidated, whereas a histogram summation is O(bins) rather than O(pixels).
**Action:** If a histogram is already available or required for other logic (like thresholding or adaptive enhancements), derive dependent statistics (mean, median, dark/light pixel ratios) directly from the histogram to avoid redundant pixel passes.

## 2026-05-29 - Single-Pass Layout Statistics Optimization
**Learning:** Consolidating multiple layout property accesses (num_lines, num_pars, num_blocks) into a single-pass cached property using `@cached_property` significantly reduces redundant O(N) traversals. In Magic processing where multiple transformers score the same OcrResult, this reduces the cost from up to 6*O(N) to 1*O(N) for the initial pass and O(1) thereafter.
**Action:** Use `@cached_property` to store multiple related statistics computed during a single traversal of a collection, especially for immutable data objects used in multi-stage pipelines.
