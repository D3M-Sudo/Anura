---
trigger: always_on
---

# How to work in this repo

- Do what was asked; don't refactor adjacent code or add speculative abstractions.
- Before editing, read the file and its direct callers.                                                                                                                             
- Ask one clarifying question when ambiguous rather than guessing.                                                                                                                  
                                                                                                                                                                                      
## Python & GTK4                                                                                                                                                                     
- Use `dataclass` for data structures; `TypedDict` only when interfacing with external APIs.
- Never `Any` — use `Unknown` and narrow, or write a proper type hint.                                                                                                                   
- No `# type: ignore` except in tests or right after a type guard.                                                                                                         
- `from typing import TYPE_CHECKING` for type-only imports to avoid circular imports.
- Prefer `Enum` over string constants for state management.                                                                                                                           
                                                                                                                                                                                      
## GTK4 & Libadwaita                                                                                                                                                                  
- Blueprint (.blp) files for UI layout — never construct widgets programmatically unless absolutely necessary.
- Use Adw.ApplicationWindow and Adw.* widgets for consistent GNOME HIG compliance.
- Server-side patterns: use Gio.SimpleAction for state management, not direct widget manipulation.
- Data fetching lives in background threads with GLib.idle_add() for UI updates — never block main thread.                                                                                                   
- Use Gio.Settings for configuration persistence; validate all inputs before storing.                                                                                                    
- Use `loading.tsx` and `error.tsx` boundaries. Stream with `<Suspense>` where it helps.                                                                                            
- `GdkPixbuf.Pixbuf` for images, `Gtk.Picture` for display. Never manual image scaling.                                                                                          
- Cache with `Gio.File` and `Gio.MemoryOutputStream` — don't reinvent.                                                                                     
- Metadata via `Adw.AboutDialog` export. Not ad-hoc.                                                                                                          
- Never put server-only secrets in client components — they leak into the bundle.                                                                                                   
                                                                                                                                                                                      
## GObject & Signals                                                                                                                                                                 
- Function components only.                                                                                                                                                         
- `GObject.Property` for widget properties, `GObject.Signal` for events.
- Memoize (`functools.lru_cache`, `functools.cached_property`) only when there's measured performance cost.
- Effects are for syncing with external systems; compute derived state in render.                                                                                                   
- Keys on lists are stable IDs, never array indexes.                                                                                                                                
- Buttons are `<button>`, links are `<a>`, inputs have labels.                                                                                                                      
                                                                                                                                                                                      
## Meson & Build System                                                                                                                                                                                    
- Meson build files; extract to sub-meson files only when a build target repeats 3+ times.                                                                                                   
- Use build options in `meson_options.txt` — no magic values in build files.                                                                                                            
- Use `dependency()` and `find_program()` for external dependencies, not hardcoded paths.
                                                                                                                                                                                      
## Flatpak & Dependencies                                                                                                                                                                                          
- Flatpak manifest is source of truth. Dependencies via flatpak-builder; never manual system drift.                                                                                                  
- Select only the modules you need — don't return full runtime to clients.                                                                                                              
- Wrap multi-step operations in `flatpak-builder` transaction.                                                                                                            
- Singleton runtime in Flatpak; don't assume system dependencies per request.                                                                                              
                                                                                                                                                                                      
## Guardrails
- Never commit secrets, API keys, or credentials.                                                                                                                                   
- Don't invent dependencies — if a package isn't in the Flatpak manifest, confirm before adding.                                                                                            
- When a command fails, read the actual error. Don't retry blindly or use `--force`.
- Prefer editing existing files over creating new ones.                                                                                                                             
- If you touch public types or exported APIs, check every caller.  
- Never modify protected files: `po/*.po`, `anura/_release_notes.py`, `data/ui/*.ui`, `CHANGELOG.md`, `release.sh`
- After any new UI string → remind user to run `./generate_pot.sh`
- Use uv for dependency management: `uv sync --dev` for development dependencies
- Run tests with uv: `uv run pytest tests/ -m "not gtk"` for pure Python tests
                                                                                                                                                                                      
---                                                                
Generated for Anura OCR — GTK4/Libadwaita + Python + Meson + Flatpak
