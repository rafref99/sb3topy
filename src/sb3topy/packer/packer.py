"""
packer.py

Handles several tasks specific to saving files
"""

import logging
import os
import shutil
import subprocess
import sys
import importlib
from multiprocessing import current_process
from os import path

from .. import config, project

__all__ = ('save_code', 'copy_engine', 'run_project', 'launch_project')

logger = logging.getLogger(__name__)


def save_code(manifest: project.Manifest, code: str):
    """
    Saves the codefile into project's directory
    """
    save_path = path.join(manifest.output_dir, "project.py")

    logger.info("Saving converted project to '%s'", save_path)

    with open(save_path, 'w', encoding="utf-8", errors="ignore") as code_file:
        code_file.write(code)


def copy_engine(manifest: project.Manifest, packer_config=None):
    """
    Copies the engine files into the project's directory

    If the engine files already exist, they will
    """
    if packer_config is None:
        packer_config = config.snapshot_config()

    # Get the path to copy from and to
    read_dir = path.join(path.dirname(__file__), "..", "..", "engine")
    save_dir = path.join(manifest.output_dir, "engine")

    if path.isfile(path.join(save_dir, "DISABLE_OVERWRITE")):
        logger.info(
            "Did not copy engine files; 'DISABLE_OVERWRITE' file exists.")
        return

    # Delete and copy the engine files
    if path.isdir(save_dir):
        if packer_config.OVERWRITE_ENGINE:
            logger.info("Overwriting engine files at '%s'", save_dir)
            shutil.rmtree(save_dir)
            shutil.copytree(read_dir, save_dir, )
            create_config(save_dir, packer_config)
        else:
            logger.info(
                "Did not copy engine files; OVERWRITE_ENGINE disabled.")
    else:
        logger.info("Copying engine files to '%s'", save_dir)
        shutil.copytree(read_dir, save_dir)
        create_config(save_dir, packer_config)

    # Create a warning message
    warn_path = path.join(save_dir, "WARNING.txt")
    with open(warn_path, 'w') as warn_file:
        warn_file.write((
            "The files in this directory will be deleted if the sb3topy "
            "converter is run again. All additional files and changes to "
            "existing files will be lost. If you want to prevent this from "
            "happening, set OVERWRITE_ENGINE to False in the configuration. "
            "Alternatively, you can create a file named 'DISABLE_OVERWRITE'"
            "to disable modifying these files.\n"
        ))


def create_config(engine_dir, packer_config=None):
    """Creates a config.py file for the engine"""
    if packer_config is None:
        packer_config = config.snapshot_config()

    # Read a formatable spec file
    spec_path = path.join(path.dirname(__file__), "config.txt")
    with open(spec_path, 'r') as spec_file:
        spec_data = spec_file.read()

    # Format the spec file into Python code
    config_data = spec_data.format(**packer_config.to_dict())

    # Save the config data
    config_path = path.join(engine_dir, "config.py")
    with open(config_path, 'w') as config_file:
        config_file.write(config_data)


def run_project(output_dir):
    """
    Runs the project.py stored in output_dir.
    """
    # pylint: disable=all
    logger.info("Running project...")

    if current_process().name != "MainProcess":
        return launch_project(output_dir)

    old_cwd = os.getcwd()
    old_path = list(sys.path)

    try:
        os.chdir(output_dir)
        sys.path.insert(0, output_dir)

        # Generated projects and their copied engine are output-specific.
        # Clear stale modules so repeated GUI runs do not reuse an older run.
        for module_name in list(sys.modules):
            if module_name == "project" or module_name == "engine" or module_name.startswith("engine."):
                del sys.modules[module_name]

        project_module = importlib.import_module("project")
        project_module.engine.start_program(
            getattr(project_module, "setup_monitors", None))

    except ModuleNotFoundError as exc:
        if exc.name == "pygame":
            logger.error(
                "Could not run project because pygame is not installed. "
                "Install it for this interpreter with: %s -m pip install pygame",
                sys.executable)
            return False
        raise

    finally:
        sys.path = old_path
        os.chdir(old_cwd)

    return True


def launch_project(output_dir):
    """
    Starts project.py in its own Python process.

    This is used by the GUI worker. On macOS, creating a Pygame/Cocoa
    window from a multiprocessing worker can fail during display setup.
    """
    project_path = path.join(output_dir, "project.py")
    if not path.isfile(project_path):
        logger.error("Could not run project; '%s' does not exist.", project_path)
        return False

    env = os.environ.copy()
    homebrew_lib = "/opt/homebrew/lib"
    if path.isdir(homebrew_lib):
        fallback_path = env.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        fallback_dirs = fallback_path.split(os.pathsep) if fallback_path else []
        if homebrew_lib not in fallback_dirs:
            fallback_dirs.insert(0, homebrew_lib)
            env["DYLD_FALLBACK_LIBRARY_PATH"] = os.pathsep.join(fallback_dirs)

    try:
        subprocess.Popen([sys.executable, project_path], cwd=output_dir, env=env)
    except OSError:
        logger.exception("Failed to launch project using '%s'.", sys.executable)
        return False

    logger.info("Launched project in a separate process.")
    return True
