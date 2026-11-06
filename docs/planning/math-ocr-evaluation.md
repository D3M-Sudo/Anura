# Mathematical OCR evaluation and integration plan

**Status:** research documented; an isolated mathematical OCR proof of concept is planned as a future phase; no engine selected  
**Scope:** issue [#570](https://github.com/D3M-Sudo/Anura/issues/570)  
**Research snapshot:** 2026-11-06  
**Target baseline:** `feature`

## 1. Executive summary

Anura currently uses Tesseract through `pytesseract` for OCR. That remains the general-purpose text-recognition path; it does not provide a dedicated image-to-mathematical-LaTeX recognition stage. Improving page segmentation or OCR configuration may help preserve surrounding text and identify candidate regions, but it does not by itself turn a raster equation into structured LaTeX.

The most promising candidate for a controlled proof of concept is **Pix2Text**, because it exposes both mathematical formula detection (MFD) and mathematical formula recognition (MFR), and documents a mixed text/formula recognition path. It is **not approved for integration** yet. Its published MFD 1.5 and MFR 1.5 ONNX files total approximately 199.8 MB before runtime libraries, caches, tokenizer/configuration files, or any optional layout/text models. More importantly, the MFR model's MIT metadata does not settle the provenance and licensing of its training data: that question is explicitly raised in upstream issue [breezedeus/Pix2Text#209](https://github.com/breezedeus/Pix2Text/issues/209), which was open at the time of this review.

The recommended direction is therefore to preserve LaTeX as the canonical machine-readable result, prototype formula-region detection and recognition behind an optional feature boundary, and defer any dependency, model, or runtime commitment until licensing, CPU performance, memory use, package closure, and Flatpak integration have been measured.

No application dependency, model download, manifest change, or code integration is proposed by this document.

## 2. Current Anura constraints

The current project metadata declares `pytesseract` as the OCR binding and does not declare PyTorch, Transformers, ONNX Runtime, Pix2Text, or pix2tex. The project targets Python 3.12 or newer.

The existing dependency workflow is intentionally explicit:

- `pyproject.toml` and `uv.lock` define the Python dependency graph.
- `flatpak/io.github.d3m_sudo.anura.local.json` is the editable Flatpak source of truth.
- Runtime dependency coverage and the installed license inventory are enforced by CI.
- The release Flatpak manifest is generated; it must not be edited by hand.
- Model assets and native/runtime dependencies need explicit license attribution and reproducible handling.

Any future implementation must preserve these boundaries. In particular, a package's small wheel size is not a useful estimate of the installed footprint when it downloads model weights or pulls large inference frameworks at runtime.

## 3. Pipeline distinction: text OCR versus mathematical OCR

A mathematical OCR workflow needs more than a general OCR text pass:

1. **Region detection:** identify equation regions and their bounding boxes in the source image.
2. **Formula recognition:** convert each cropped equation image into a LaTeX sequence.
3. **Layout reconstruction:** retain reading order and distinguish inline equations from display/block equations.
4. **Mixed-content reconstruction:** combine ordinary text and formula nodes without silently flattening their boundaries.
5. **Review and export:** let the user inspect/correct the recognized result and copy/export the chosen representation.

Tesseract can remain responsible for ordinary text. A specialist math stage should be additive and must not replace or regress the existing text OCR path. Formula recognition output must be treated as a prediction, not as guaranteed valid mathematics.

The first implementation should prefer a structured intermediate representation, for example an ordered sequence of text and formula nodes with source bounding boxes and a formula display/inline hint. The LaTeX string is the canonical payload for formula nodes. Rendering a formula preview is a separate concern from recognizing it.

## 4. Candidate comparison

### 4.1 Pix2Text — preferred proof-of-concept candidate, not yet approved

Pix2Text is an open-source Python toolkit that combines layout/text processing with dedicated mathematical formula detection and recognition. Its published documentation describes:

- MFD (Mathematical Formula Detection), based on CnSTD;
- MFR (Mathematical Formula Recognition), based on a TrOCR-derived architecture;
- recognition of pure formula images and mixed images containing ordinary text and formulas;
- LaTeX as the formula representation and Markdown as an integrated document output.

The current upstream package release observed for this review is 1.1.7 (2026-08-23). PyPI marks the package MIT-licensed. The model cards for MFD 1.5 and MFR 1.5 also declare MIT.

**Published model footprint (ONNX artifacts only):**

| Model | Published artifact | Size |
| --- | --- | ---: |
| MFD 1.5 | `pix2text-mfd-1.5.onnx` | 80.3 MB |
| MFR 1.5 | `encoder_model.onnx` + `decoder_model.onnx` | 87.5 MB + 32 MB |
| **Total** | | **199.8 MB** |

The rounded total is approximately 200 MB (not including tokenizer/configuration files, the Python dependency closure, ONNX Runtime, temporary tensors, model caches, or any layout/table/text-recognition models). The full Pix2Text workflow may involve additional models beyond the two formula-specific artifacts; the footprint of a formula-only integration must be measured separately rather than inferred from the package wheel.

**Important unresolved risks:**

- Upstream issue [#209](https://github.com/breezedeus/Pix2Text/issues/209) asks which training datasets and TrOCR checkpoint were used for MFR 1.5, and whether their terms affect redistribution/commercial use. The model card's MIT label alone is insufficient to close this provenance review. Treat the question as unresolved until the upstream maintainer provides a defensible answer or the project completes an independent legal review.
- Upstream issue [#202](https://github.com/breezedeus/Pix2Text/issues/202) reports that the published ONNX decoder uses `use_cache=False` and requests PyTorch weights or a cache-enabled ONNX export. The report describes slow recognition in one RTX 4060 test; this is a reporter's observation, not a benchmark that can be generalized to Anura or CPU-only hardware. It is nevertheless a concrete performance risk to investigate.
- The MFR model card's direct ONNX example uses Transformers, Optimum ONNX Runtime, Pillow, and PyTorch tensors. The complete dependency closure, CPU behavior, peak RAM, cold-start cost, and aarch64 availability have not been validated for Anura.
- Pix2Text also includes layout, table, and text-recognition components. A minimal integration must prove that it can load only the necessary formula components, or explicitly account for every additional model and dependency.

**Assessment:** best candidate for a bounded technical spike because its documented mixed-content path addresses the central use case. Do not add it to `pyproject.toml`, `uv.lock`, or either Flatpak manifest until the risks above are resolved and measurements pass the acceptance gates below.

### 4.2 pix2tex / LaTeX-OCR — formula-only alternative

pix2tex is a specialized image-to-LaTeX recognizer. Its project documentation says that PyTorch is required and that model checkpoints are downloaded automatically when the model is first run. The package is published under MIT.

Its narrow formula-image input is useful for a comparison benchmark, but it does not, by itself, solve mixed-page layout reconstruction. Anura would still need formula-region detection, ordinary text OCR, reading-order reconstruction, and inline/display classification. The PyTorch runtime and checkpoint footprint also need measurement; no reliable Anura-specific CPU/RAM figures have been established in this research.

**Assessment:** include as a comparator in a prototype only if it can be tested without adding it to the application dependency graph. It is not the preferred integration path at this stage.

### 4.3 Mathpix — hosted service, not a default path

Mathpix provides hosted OCR for text and mathematical content through an authenticated API. This introduces network availability, service credentials, pricing, and external processing of user screenshots/documents.

That conflicts with Anura's local-first/offline expectations for core OCR. It could only be considered as a separately disclosed, explicitly opt-in external service, with privacy and cost controls. It must not become the default or silently receive captured screenshots.

**Assessment:** exclude from the default implementation and from the initial local/offline proof of concept.

### 4.4 Tesseract-only improvements

Tesseract remains appropriate for ordinary text recognition and may help identify text lines or preserve nearby prose. It does not produce a dedicated mathematical formula-to-LaTeX representation. Therefore, configuration changes or page segmentation improvements alone cannot satisfy the minimum requirement in #570.

**Assessment:** retain as the baseline text engine; do not represent a Tesseract-only change as mathematical OCR support.

## 5. LaTeX and Typst are separate output targets

LaTeX should be the initial canonical formula output because the minimum requirement in #570 explicitly asks for LaTeX and the evaluated recognizers emit LaTeX.

Typst has its own markup and math syntax. Its official guide for LaTeX users explicitly describes differences between the systems; the Typst language is not a LaTeX-compatible dialect. Consequently:

- do not relabel LaTeX strings as Typst;
- do not promise lossless conversion;
- do not make Typst a prerequisite for recognizing formulas;
- consider a separate, optional LaTeX-to-Typst conversion/export step only after choosing a converter and validating representative formula constructs.

The first delivery should expose LaTeX output and preserve the distinction between inline and display formulas. Typst conversion is a follow-up scope decision.

## 6. Proposed integration shape (not an implementation commitment)

A future design should keep the existing OCR path intact and introduce a separately testable math-recognition service:

```text
Captured image
    |
    +--> existing Tesseract text OCR
    |
    +--> optional math-region detection
              |
              +--> formula crop(s)
                       |
                       +--> math recognizer --> LaTeX formula node(s)
    |
    v
ordered text/formula representation
    |
    +--> editable/reviewable result
    +--> copy plain text / LaTeX
    +--> optional later Typst conversion
```

The math stage should be optional, lazily initialized, cancellable, and isolated from the GTK main thread. Model acquisition must be explicit and integrity-checked; no large model should be downloaded silently during application startup or an ordinary OCR operation. Offline behavior must remain predictable when the optional model is absent.

This is a proposed boundary only. The actual service interfaces, task-manager integration, settings, UI, and model lifecycle must be designed against the current code before implementation.

## 7. Required proof-of-concept gates

Before selecting an engine, run the same controlled fixture set against Pix2Text and at least one comparator where practical.

### Functional corpus

Include clear printed equations first, then mixed screenshots and harder cases:

- inline equations surrounded by prose;
- display equations and multi-line/aligned equations;
- fractions, nested fractions, roots, superscripts, and subscripts;
- Greek letters, common operators, limits, and summations;
- matrices, brackets, and piecewise/cases expressions;
- mixed text/equation regions with columns or nearby labels;
- low-resolution, anti-aliased, skewed, compressed, and noisy screenshots.

Handwritten mathematics should be reported as a separate capability tier, not assumed from printed-formula results.

### Quality and correctness

- Record exact-match rate and a normalized LaTeX edit-distance metric on a fixed, versioned corpus.
- Review semantic equivalence separately; syntactically different LaTeX may render identically.
- Measure false-positive formula detection on ordinary prose and symbols.
- Verify that source order, bounding boxes, and inline/display classification survive reconstruction.
- Include malformed/partial predictions and a user correction path; never silently claim mathematical correctness.

### Runtime and packaging

Measure on CPU-only systems, with no CUDA assumption:

- cold model load and first-inference latency;
- steady-state latency per formula and per screenshot;
- peak resident memory and temporary disk/cache footprint;
- model download size and installed size;
- x86_64 and aarch64 availability;
- Python dependency closure and native library requirements;
- Flatpak buildability, runtime compatibility, and license-inventory completeness.

The project's low-resource Linux systems make CPU latency and peak memory release-blocking measurements, not optional optimizations. Do not extrapolate from GPU benchmarks.

### Licensing and provenance

For every package, model, tokenizer, and redistributed asset:

- capture the exact upstream version/revision and SHA-256;
- inspect the package license and each model/repository license separately;
- establish training-data and base-checkpoint provenance for MFR 1.5;
- identify licenses/notices for transitive Python and native dependencies;
- verify that all required notices can be included in Anura's installed license inventory.

A model-card SPDX-like label is useful evidence, but it does not answer unresolved dataset provenance questions.

## 8. Suggested phases

1. **Research closure:** resolve MFR 1.5 provenance, review upstream performance reports, and enumerate the exact minimal Pix2Text dependency/model set.
2. **Isolated prototype:** run formula-only and mixed-content fixtures outside Anura's production dependency graph; compare Pix2Text with pix2tex where useful.
3. **Resource and packaging validation:** measure CPU/RAM/latency on representative low-resource x86_64 and aarch64 environments; validate Flatpak and license inventory in CI.
4. **Architecture decision:** select an engine only if all gates pass; otherwise document why the candidate is rejected and evaluate a smaller ONNX-specific implementation.
5. **Incremental integration:** add an opt-in math stage, structured output, user review, tests, translations, docs, and changelog. Preserve ordinary OCR behavior and offline operation.

## 9. Current decision

| Question | Current conclusion |
| --- | --- |
| Can Tesseract alone satisfy image-to-LaTeX recognition? | No; it remains the ordinary text OCR baseline. |
| Best candidate for a first mixed-content prototype? | Pix2Text, conditional on provenance and resource validation. |
| Is Pix2Text approved as an Anura dependency? | No. |
| Is pix2tex suitable as the mixed-page solution by itself? | No; it is a formula-only comparator and needs separate detection/layout handling. |
| Should Mathpix be the default? | No; it is hosted and sends user content to an external service. |
| Canonical first output? | LaTeX. |
| Typst in the first implementation? | No; evaluate later as a distinct conversion/export feature. |
| Code or runtime changes included in this plan? | None. |

## 10. Sources

All sources below were consulted on 2026-11-06. Upstream status and model artifacts can change; re-check them before implementation.

- [Pix2Text on PyPI](https://pypi.org/project/pix2text/) — package description, components, release and package license.
- [Pix2Text repository](https://github.com/breezedeus/Pix2Text) — architecture and mixed-content API.
- [Pix2Text MFD 1.5 model card](https://huggingface.co/breezedeus/pix2text-mfd-1.5) and [ONNX artifact](https://huggingface.co/breezedeus/pix2text-mfd-1.5/tree/main) — MIT metadata and 80.3 MB detector artifact.
- [Pix2Text MFR 1.5 model card](https://huggingface.co/breezedeus/pix2text-mfr-1.5) and [model files](https://huggingface.co/breezedeus/pix2text-mfr-1.5/tree/main) — MIT metadata, TrOCR-derived architecture, ONNX files and usage requirements.
- [Pix2Text #209 — MFR 1.5 training-data and license provenance](https://github.com/breezedeus/Pix2Text/issues/209) — open provenance question.
- [Pix2Text #202 — request for PyTorch MFR weights](https://github.com/breezedeus/Pix2Text/issues/202) — reported ONNX decoder performance concern.
- [pix2tex on PyPI](https://pypi.org/project/pix2tex/) and [installation documentation](https://pix2tex.readthedocs.io/en/latest/installation.html) — formula-only behavior, PyTorch requirement, automatic checkpoint download, package license.
- [Typst guide for LaTeX users](https://typst.app/docs/guides/for-latex-users/) and [Typst math reference](https://typst.app/docs/reference/math/) — distinct syntax and math model.
- [Anura dependency and Flatpak workflow](dependencies.md) — repository-local packaging, dependency, and license constraints.

---

**Implementation status:** no PoC or application integration has started. The isolated mathematical OCR PoC is an explicitly planned future phase, following research closure and review of model/data provenance, licensing, and feasibility. Pix2Text remains a candidate rather than an approved engine; the PoC must not modify Anura's production OCR pipeline or dependency graph. Any subsequent integration requires a separate decision based on the PoC results.
