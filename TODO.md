# TODO

Active improvement backlog. When an item is completed, remove it from this file in the same change.

1. "Turbo Mode" Toggle in GUI
   - Add a checkbox to enable/disable Turbo Mode from the GUI.

2. Optimized Rendering for Static Stages
   - Implement dirty-rect optimization for static backgrounds to boost FPS.

3. Enhanced Extension Support
   - Modularize support for Pen, Music, and Video Sensing.

4. Headless Testing with Frame Snapshots
   - Use dummy SDL drivers and visual regression snapshots for CI.

5. Continue reducing global mutable configuration risk.
   - Introduce a `Config` dataclass or immutable config object passed into conversion.
   - Keep module globals as a compatibility layer during transition.

6. Standalone Executable Export
    - Integrate `PyInstaller` or `Nuitka` for exporting projects as executables.
