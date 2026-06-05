# DESIGN.md - Velis Architecture

## Philosophy
Velis is built with the principle of "Actionable Information". It doesn't just extract text; it helps the user process it through smart workflows.

## Original Features Rationale

### 1. History Archive
**Rationale**: Users often need to refer back to something they scanned a few minutes or hours ago. By preserving a local history (with images), Velis acts as a temporary memory for visual information.

### 2. Side-by-Side Verification View
**Rationale**: OCR is rarely 100% perfect. Allowing users to toggle a view where the source image is right next to the text allows for rapid verification and manual correction without switching windows.

### 3. Custom Regex Workflows
**Rationale**: Many users use OCR for specific data (IBANs, Tracking IDs, Serial Numbers). By allowing users to define these patterns, Velis transforms from a generic tool into a specialized productivity utility.

### 4. Translation Integration (LibreTranslate)
**Rationale**: In an internationalized world, the text we scan is often in a language we don't fully understand. Integrating a privacy-first translation service directly into the workflow saves several manual steps.

## Technical Architecture
- **Mediator Pattern**: `Window` manages the navigation and communication between pages.
- **Controller/Service Decoupling**: Business logic is encapsulated in services, which are coordinated by controllers or directly by the UI for simpler tasks.
- **Atomic Tasks**: Long-running operations (OCR, Translation) are handled by the `AtomicTaskManager` to keep the UI responsive.
