"""
main.py

Orchastrates unpacking, converting assets, parsing
the project, and copying files based on configuration.

To allow simple configuration from the command line, the
path to a configuration json can be passed as an argument.
"""


import logging
import sys
from multiprocessing import Process, Queue

from . import config, packer, parser, pkg_log, project, unpacker

logger = logging.getLogger(__name__)


def main(args=None):
    """
    Reads configuration from the command line and runs the converter
    """
    # Load configuration from the command line
    config.parse_args(args)

    # Configure the logger from config
    pkg_log.config_logger()

    # Run the gui if it is enabled
    if config.USE_GUI:
        # Lazy import of gui. If tkinter is not installed or the GUI is
        # otherwise broken, the terminal interface should still work.
        from . import gui  # pylint: disable=import-outside-toplevel

        return gui.run_app()

    # Run the conversion
    return run()


def run(run_config=None):
    """
    Converts the project using the settings saved in config
    """
    if run_config is None:
        run_config = config.snapshot_config()

    # Initialize the manifest
    manifest = project.Manifest(run_config.OUTPUT_PATH)

    # Download the project from the internet
    if run_config.PROJECT_URL:
        sb3 = unpacker.download_project(manifest, run_config.PROJECT_URL, run_config)

    # Extract the project from an sb3
    elif run_config.PROJECT_PATH:
        sb3 = unpacker.extract_project(manifest, run_config.PROJECT_PATH, run_config)

    else:
        logger.error("A project url/path was not provided.")
        sb3 = None

    # Verify the project was unpacked
    if sb3 is None or not sb3.is_sb3():
        return False

    # Save a debug json
    if run_config.DEBUG_JSON:
        project.save_json(sb3, manifest, run_config.FORMAT_JSON)

    # Convert project assets
    if run_config.CONVERT_ASSETS:
        unpacker.convert_assets(manifest, run_config)

    # Copy engine files
    if run_config.COPY_ENGINE:
        packer.copy_engine(manifest, run_config)

    if run_config.PARSE_PROJECT:
        # Parse the project
        code = parser.parse_project(sb3, manifest, run_config)

        # Save the project's code
        packer.save_code(manifest, code)

        logger.info("Finished converting project. Saved in '%s'",
                    manifest.output_dir)

    if run_config.AUTORUN:
        if not packer.run_project(manifest.output_dir):
            return False

    logger.info("Done!")

    return True


def _run_worker(queue, run_config):
    """
    Runs and attaches a QueueHandler to the log.
    """
    try:
        # Keep module globals aligned for compatibility-only callers.
        config.set_config(run_config.to_dict(modifiable_only=True))

        # Setup the log to use the queue
        pkg_log.config_logger()
        pkg_log.config_queue(queue)
        logger.info("Using Python interpreter: %s", sys.executable)

        # Run the converter
        run(run_config)

    # Catch any errors so they can be shown in the GUI
    except Exception:
        logger.critical(
            "Unhandled exception during the conversion process:",
            exc_info=True)
        raise

    finally:
        queue.put(None)

    # Process now ends


def run_mp():
    """
    Runs in a new Process. Returns a Process, Queue pair.

    The Queue is tied to a QueueHandler to get log messages.
    """
    run_config = config.snapshot_config()
    queue = Queue(-1)
    process = Process(target=_run_worker, args=(
        queue, run_config), daemon=True)
    process.start()

    return process, queue
