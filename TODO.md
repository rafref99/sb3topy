# TODO

Active improvement backlog. When an item is completed, remove it from this file in the same change.

1. "Turbo Mode" Toggle in GUI
   - Add a checkbox to enable/disable Turbo Mode from the GUI.

2. Benchmark dirty-rect rendering on representative large converted projects.
   - Capture before/after frame timing once a large exported workload is available in the repo or test fixtures.

3. Enhanced Extension Support
   - Modularize support for Pen, Music, and Video Sensing.

4. Headless Testing with Frame Snapshots
   - Use dummy SDL drivers and visual regression snapshots for CI.

5. Continue reducing global mutable configuration risk.
   - Introduce a `Config` dataclass or immutable config object passed into conversion.
   - Keep module globals as a compatibility layer during transition.

6. Standalone Executable Export
    - Integrate `PyInstaller` or `Nuitka` for exporting projects as executables.

7. Tighten event scheduling compatibility.
   - Improve key/event restart behavior, `stop other scripts`, and warp/no-refresh timing.

8. Live Scratch cloud variable synchronization.
   - Detect Stage cloud variables and connect them to Scratch cloud data instead of treating them as local-only variables.
   - Define authentication/session handling for projects that need to write cloud variables.
   - Provide an explicit offline/local fallback when live cloud writes are unavailable.
