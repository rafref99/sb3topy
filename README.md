# sb3topy (Reworked)

**Note: This is a reworked version of sb3topy featuring significant performance improvements, enhanced compatibility, and modernized code architecture.**

sb3topy is a tool which can convert [Scratch 3.0](https://scratch.mit.edu) projects into Python. The project is converted into a single file which can run using the sb3topy engine and Pygame. The engine files are automatically copied when the converter is run.

## AI-Assisted Rework
This project is being significantly improved and modernized with the assistance of **Junie**, an autonomous programmer powered by the **gemini-3-flash-preview** LLM (2026). The AI has been instrumental in implementing type hints, modernizing the GUI with CustomTkinter, and optimizing the engine's core logic.

## Key Improvements in this Rework
- **Modernized Architecture:** Enhanced with type hints and a cleaner project structure.
- **Improved Performance:** Optimized rendering and execution loop for smoother Scratch project playback.
- **Enhanced Compatibility:** Ongoing work to support more blocks and Scratch extensions.
- **Robust Testing:** Expanded test suite to ensure conversion accuracy.

## Recent Reliability Fixes
- The GUI Output tab now displays conversion logs and exception tracebacks while tasks run.
- Manual conversion and example downloads now force a full conversion path, including engine copy and `project.py` generation.
- Example downloads use a persistent `~/sb3topy_examples/` output folder when no output path is selected.
- Download & Run reports missing `pygame` clearly, and generated projects run against their copied output `engine/` first.
- GUI Download & Run launches generated projects in a separate Python process to avoid macOS Pygame display setup crashes from worker processes.
- Generated projects initialize Scratch monitors after runtime sprite setup, avoiding startup crashes in Download & Run.
- Generated projects cancel Scratch tasks and close the asyncio loop directly so the Pygame window can quit cleanly.
- Homebrew Cairo is detected automatically on macOS so SVG costumes convert to PNGs instead of making Pygame load large SVGs at startup.
- SVG costume conversion now preserves transparent backgrounds and cleans converter-created matte/edge artifacts.
- The engine redraws transparent sprites over the stage correctly, including ghosted sprites and SVG costumes with transparent backgrounds.
- Output folders are created automatically when converting to a new directory.
- CLI-style calls such as `main.main(["sb3topy", "project.sb3", "out"])` are supported for integration tests and tooling.
- Unsupported Scratch monitor types are skipped with warnings instead of stopping project conversion.

Currently, sb3topy is in Beta and may have bugs or missing features which could prevent some project from running correctly. In addition, there may be bugs which allow arbitrary Python code to run, so be cautious when running untrusted projects.

A full list of supported blocks can be found [here](docs/supported_blocks.md).

## Quickstart

1. Using Python 3.12, install the required packages (`pygame`, `requests`, `customtkinter`, and optionally `cairosvg`) with pip.

   ```pip install -r requirements.txt```

2. Run the GUI.

    ```python run_gui.pyw```

3. Pick an example and hit Download & Run.

## Example Downloads

GUI example projects are downloaded and converted into a persistent folder under `~/sb3topy_examples/`, which resolves to the current user's home directory, such as `/Users/your-username/sb3topy_examples/` on macOS. Each example gets its own subfolder named from the example title and Scratch project id.

## Testing

Run the test suite from the repository root. For development, install the package in editable mode with the test, GUI, and SVG extras first.

```bash
python3 -m pip install -e ".[dev,gui,svg]"
python3 -m pytest -q
```

## Requirements

Before using sb3topy, you need to install a few Python packages using [pip](https://pypi.org/project/pip/). You can install all of them at once using [requirements.txt](requirements.txt).

| Package | Description | Mandatory |
| :--- | :--- | :--- |
| `pygame` | Used by the engine to run converted projects. | Yes |
| `requests` | Used to download projects and example thumbnails. | Yes |
| `customtkinter` | Used for the modern graphical user interface. | Yes |
| `cairosvg` | Used to convert SVG files into PNGs. | Optional* |

\* **Note on SVG Conversion:** `cairosvg` is optional but highly recommended if your Scratch project uses SVG costumes. If you don't want to install it, you can configure Inkscape as an alternative in the Assets tab of the GUI.

Note that Pygame 2+ is required to play MP3 files. MP3 files can optionally be converted using VLC player. To enable MP3 conversion or convert using a custom command, see the assets tab of the GUI.

Note that CairoSVG may be difficult to install on some systems. See CairoSVG's instructions [here](https://cairosvg.org/documentation/). Inkscape can be used as an alternative, but it must be configured under the Assets tab of the GUI.

Note that one of the examples, "The Taco Incident," does not contain any SVG costumes. If you want to get started without installing an SVG conversion tool, you should still be able to run this example. You can also manually convert every costume to bitmap to allow a project to run.

Support for alternate SVG conversion tools with an easier installation process is being looked into.

## Command Usage

```
python -m sb3topy --help
usage: __main__.py [-h] [-c [file]] [--gui] [-r] [PROJECT_PATH] [OUTPUT_PATH]

Converts sb3 files to Python.

positional arguments:
  PROJECT_PATH  path to a sb3 project
  OUTPUT_PATH   specifies an output directory

options:
  -h, --help    show this help message and exit
  -c [file]     path to a config json, disables autoload
  --gui         starts the graphical user interface
  -r            automatically runs the project when done
```
