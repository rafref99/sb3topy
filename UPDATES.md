# sb3topy Rework Updates

This file documents the changes and improvements made during the project rework.

## [2026-04-22] - Initial Rework Phase

### Documentation & Project Info
- Updated `README.md` to reflect the project's rework status and highlight key improvements (Modernized Architecture, Performance, Compatibility, Testing).
- Updated `LICENSE` to include 2026 copyright for IguanaLover, reflecting the project rework.
- Updated `README.md` to include information about the AI-assisted rework using Junie (gemini-3-flash-preview, 2026).
- Updated `README.md` requirements section to specify Python 3.12+ and mandatory vs optional packages.
- Created `UPDATES.md` (renamed from `updates.txt`) to track ongoing changes.
- Proposed a modernization plan for the GUI using `CustomTkinter`.
### GUI Modernization & Bug Fixes
- Successfully modernized the GUI using `CustomTkinter`, transitioning from a dated `tkinter/ttk` look to a modern, themeable interface.
- Increased the default application window height by 20% (from 520px to 624px) for better visibility.
- Fixed `ModuleNotFoundError` by ensuring `customtkinter` is correctly installed.
- Resolved multiple `AttributeError`s and `NameError`s in the GUI modules caused by incompatible `tk/ttk` method calls on `CustomTkinter` widgets.
- Improved thumbnail loading logic in the Examples tab with `PIL` support and better fallback mechanisms.
- Replaced the example projects in the "Examples" tab with top projects from the user's Scratch profile (IguanaLover).
- Updated `requirements.txt` to include `customtkinter`.

### Engine Modernization
- Added comprehensive Python type hints to the following engine modules for better maintainability and IDE support:
  - `src/engine/operators.py`
  - `src/engine/util.py`
  - `src/engine/types/target.py`
  - `src/engine/types/lists.py`
  - `src/engine/types/sounds.py`
  - `src/engine/types/costumes.py`
  - `src/engine/types/pen.py`

### Parser Enhancements
- Added type hints to core parser components:
  - `src/sb3topy/parser/targets.py`
  - `src/sb3topy/parser/specmap/codemap.py`
  - `src/sb3topy/parser/sanitizer.py`
- Fixed a bug in `src/sb3topy/parser/specmap/codemap.py` where a missing `Any` import caused runtime errors.

### Tooling & Performance
- Created `profile_converter.py`: A performance profiling tool using `cProfile` to identify bottlenecks in the Scratch-to-Python conversion process.

### Testing
- Implemented `tests/test_integration.py`: Established a framework for end-to-end conversion testing.
- Verified all changes against the existing test suite (`tests/test_sanitization.py`).

## [2026-04-22] - Variable and List Visualization

### New Features
- **Implemented Variable and List Monitors:** Added support for real-time visualization of Scratch variables and lists in the Pygame engine.
  - Monitors now respect position, visibility, and mode (normal, large, list) from the original `.sb3` project.
  - Implemented `Monitor` and `ListMonitor` classes in the engine with high-performance dirty-rect rendering.
  - Added support for `show variable`, `hide variable`, `show list`, and `hide list` blocks.
- **Parser Enhancements:** Updated the parser to extract and transpile monitor data from `project.json` into initialization code.
- **Engine Integration:** Integrated monitors into the core `Runtime` and `Render` loops for seamless updates and display.

### Performance Improvements
- **Optimized `operators.py`:** Reduced overhead in type conversion (`tonum`, `toint`) and comparisons (`gt`, `lt`, `eq`) by adding fast-path checks for common types, avoiding expensive `try-except` blocks for already numeric values.
- **Enhanced Warp Mode:** Re-implemented the warp timer (500ms limit) in the `Warp` context manager, ensuring that "No Screen Refresh" blocks behave more like the original Scratch engine by yielding if they run too long.
- **Efficient Sprite Updates:** Optimized `Target._update_rect` by reducing redundant property lookups and using local variables for frequently accessed configuration values.
- **Scheduler Optimization:** Refined `Runtime.step_threads` to minimize function calls and property accesses within the core execution loop.
- **Type Hint Refinement:** Improved type annotations in core engine files to assist with static analysis and potential future optimizations.

## [2026-04-22] - GUI Conversion and Test Reliability Fixes

### GUI Fixes
- Fixed the Output tab so queued `LogRecord` messages are rendered with `record.getMessage()`, restoring visible logs during conversion, download, and run tasks.
- Added traceback rendering for worker exceptions in the Output tab.
- Added a worker completion sentinel and post-exit polling so the GUI drains final log messages before stopping its watcher loop.
- Added an immediate "Starting task..." message and switched Output textbox state updates to the `CustomTkinter` widget API.
- Ensured Convert, Download, and Download & Run actions explicitly enable `PARSE_PROJECT` and `COPY_ENGINE`, preventing saved config state from producing only `assets/` and `engine/` without `project.py`.
- Added GUI config variables for `PARSE_PROJECT` and `COPY_ENGINE` so those settings round-trip correctly through GUI state.
- Made example downloads choose a persistent `~/sb3topy_examples/<project>/` output folder when no output path is configured, instead of writing to a temporary directory that disappears after conversion.
- Fixed generated project autorun so the output directory is first on `sys.path`, ensuring the copied `engine/` folder is imported instead of the source-tree engine during development runs.
- Added a clear log error when `pygame` is missing during autorun.
- Changed GUI worker autorun to launch generated projects in a separate Python process, avoiding macOS Pygame/Cocoa crashes when `pygame.display.set_mode()` runs inside a multiprocessing worker.
- Rebuilt the project `.venv` with Python 3.12 because the previous Python 3.14 venv could not install `pygame` wheels and failed compiling against missing SDL headers. The old environment was kept as `.venv-py314-backup`.
- Fixed a runtime type-annotation crash where the Scratch `List` class shadowed `typing.List` in `engine.types.target`.
- Moved generated monitor initialization into a `setup_monitors()` hook that runs after runtime sprites are created.
- Added explicit generated imports for `Monitor` and `ListMonitor`.
- Fixed an infinite iteration hang in list monitors by making Scratch lists explicitly iterable and by reading monitor snapshots from the internal list data.
- Hidden monitors no longer update every frame, and zero-sized list monitors are clamped to valid render dimensions.
- Added automatic Homebrew Cairo library discovery for CairoSVG on macOS.
- Example downloads force image reconversion so existing SVG-only outputs are refreshed into PNG-backed assets.
- Fixed generated project shutdown by explicitly cancelling Scratch tasks, stopping sounds, and managing the asyncio event loop directly instead of relying on `asyncio.run()` cleanup.
- Fixed Scratch graphic effects with uppercase field names, including the `GHOST` opacity effect, by normalizing costume effect names in the engine.
- Added `tests/test_engine_effects.py` to verify ghost opacity alpha, clamping, and clearing behavior.
- Examples now detect an existing converted output folder and replace Download/Download & Run with Run/Redownload actions.
- Added `tests/test_examples_gui.py` for example-output detection.

### Conversion Fixes
- Made `main.main()` return the conversion result for non-GUI runs.
- Allowed `config.parse_args()` to accept CLI-style argument lists that include the program name, improving integration-test and tooling compatibility.
- Updated `Manifest` to create missing output directories recursively before writing assets.
- Added `Project.get()` to keep the project wrapper compatible with parser code that reads it like a dictionary.
- Made monitor code generation skip unsupported or non-variable monitor entries with warnings instead of aborting conversion.
- Normalized `requirements.txt` from UTF-16 to UTF-8/LF so `python3 -m pip install -r requirements.txt` works reliably.
- Updated the README quickstart to recommend Python 3.12 for dependency compatibility.

### Testing
- Verified the full pytest suite with `PYTHONPATH=src python3 -m pytest -q`.
- Confirmed `python3 -m compileall -q src/sb3topy` and `git diff --check` pass for the touched files.
- Added `tests/test_strict_integration.py`, a stricter end-to-end test that verifies generated output structure, copied engine fixes, converted SVG PNG assets, monitor setup code, and clean headless QUIT shutdown.
