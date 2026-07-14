---
trigger: always_on
---

# Anura OCR Architecture Guide

## Development Philosophy

- **First Principles**: Embrace SOLID principles, KISS (Keep It Simple, Stupid), and DRY (Don't Repeat Yourself)
- **Functional Over Object-Oriented**: Favor functional and declarative programming patterns over imperative and OOP
- **Component-Driven Development**: Build applications as compositions of well-defined, reusable widgets and services
- **Type Safety**: Leverage Python type hints to their fullest potential for enhanced developer experience and code quality
- **Think Then Code**: Begin with step-by-step planning and detailed pseudocode before implementation

## Code Architecture & Structure

### Project Organization
- Use lowercase with underscores for directories (`services/`, `widgets/`, `utils/`)
- Structure files consistently:
  1. Exported classes/functions
  2. Subcomponents/helpers 
  3. Constants/configuration
  4. Type definitions

### Naming Conventions

- **PascalCase** for:
  - Classes (`ClipboardService`, `LanguageManager`)
  - GTK4 widgets (`ExtractedPage`, `WelcomePage`)
  
- **snake_case** for:
  - Directory names (`services/`, `widgets/`, `utils/`)
  - File names (`clipboard_service.py`, `language_manager.py`)
  
- **snake_case** for:
  - Variables, functions, methods
  - Properties, constants
  
- **Descriptive Prefixes**:
  - Prefix event handlers with 'on_': `on_extract_clicked`, `on_language_changed`
  - Prefix boolean variables with verbs: `is_loading`, `has_error`, `can_extract`
  - Prefix private methods with '_': `_validate_language`, `_cleanup_resources`

## Python Type Implementation

- Enable strict type checking with mypy or ruff
- Prefer dataclasses over TypedDict for internal data structures
- Use type guards for None/Optional values
- Apply generics for type flexibility when needed
- Leverage typing utility types (`Optional[]`, `Union[]`, `Literal[]`)
- Use Enum for state management instead of string constants
- Use Union types for complex state management

## GTK4 & Libadwaita Best Practices

### Widget Patterns

- Use functional widget definitions with explicit type hints
- Use the `class` keyword for widget definitions, not functional composition
- Extract reusable logic into utility functions and services
- Place static content in class attributes or module constants
- Implement proper cleanup in GObject signal handlers

### Blueprint First

- Default to Blueprint (.blp) files for UI layout
- Use Python widget creation sparingly, only when necessary:
  - Dynamic widget creation based on data
  - Complex conditional layouts
  - Runtime widget manipulation
- Use Gio.Settings for configuration persistence
- Implement proper data fetching using background threads

### Performance Optimizations

- Use GLib.idle_add() strategically for UI updates from background threads
- Implement GObject signals for event handling passed to child widgets
- Use functools.lru_cache for expensive computations
- Avoid inline widget creation in loops
- Implement lazy loading for language models and resources
- Use proper parent-child relationships in widget hierarchies
- Wrap long-running operations in background threads with proper cancellation

## UI and Styling

- Use CSS for utility-first, maintainable styling
- Leverage Libadwaita components for accessible, composable UI
- Design with mobile-first, responsive principles (where applicable)
- Implement dark mode using CSS variables or Adw.StyleManager
- Maintain consistent spacing values and design tokens
- Use GTK4 CSS transitions for smooth animations

## Error Handling - The Art of Graceful Failures

### The Early Return Pattern

- Handle errors and edge cases at the beginning of functions
- Use early returns for error conditions
- Place the happy path last in the function
- Avoid unnecessary else statements; use if-return pattern instead
- Implement guard clauses to handle preconditions

### Structured Error Handling

- Use custom exception classes for consistent error handling
- For service operations, model expected errors as return values
- Implement error boundaries using try-except blocks in critical sections
- Provide user-friendly error messages via notifications
- Log errors appropriately for debugging with proper levels

## Form Validation

- Use regex patterns for schema validation
- Implement proper error messages
- Use Gio.Settings for form state persistence
- Combine with validation functions for user input

## State Management

- Use GObject properties for simple widget-level state
- Implement Gio.SimpleAction for complex local state
- Use Gio.Settings for shared configuration state
- For application state, choose appropriate patterns:
  - Service singletons for complex operations
  - Language manager for language-specific state
  - Settings service for user preferences

## Accessibility (a11y)

- Use semantic GTK4 widgets and containers
- Apply appropriate ARIA attributes only when necessary
- Ensure keyboard navigation support
- Maintain accessible color contrast ratios
- Follow a logical widget hierarchy
- Provide clear and accessible error feedback
- Test with screen readers

## Thread Safety Patterns

### GLib Main Context Integration

- Never emit GObject signals from secondary threads
- Always use GLib.idle_add() for UI updates from background threads
- Implement proper cancellation patterns with Gio.Cancellable
- Use atomic operations for shared state

### Service Architecture

- Implement __slots__ for memory efficiency in service classes
- Use atomic cancellation patterns for long-running operations
- Proper cleanup of resources in service destructors

## Build System Integration

### Meson Best Practices

- Use Meson for all build operations
- Implement proper dependency management
- Use build options for configurable features
- Generate release notes from CHANGELOG.md

### Flatpak Integration

- Use Flatpak manifest as source of truth for dependencies
- Implement proper sandbox permissions
- Test with different desktop environments
- Use appropriate runtime versions

## Testing Architecture

### Test Organization

- Use pytest for all testing
- Separate GTK tests from pure Python tests using markers
- Implement proper fixtures for test setup
- Use mocking for external dependencies

### Test Patterns

- Test service methods independently
- Test GTK widgets with proper GTK initialization
- Use property-based testing for validation functions
- Implement integration tests for critical user flows

---
Generated for Anura OCR — GTK4/Libadwaita + Python + Meson + Flatpak
