"""
convert_svg.py

Handles svg conversion.
"""

import logging
import os
import shlex
import shutil
import subprocess
from os import path

from .. import config

logger = logging.getLogger(__name__)


def get_svg_function(svg_config=None):
    """
    Attempts find a way to convert SVG files. If USE_SVG_CMD is
    enabled, either the command will be used or nothing.

    Returns `None` if no conversion method could be found.
    """
    if svg_config is None:
        svg_config = config.snapshot_config()

    # If the command is enabled, try to use it
    if svg_config.USE_SVG_CMD:
        func = _convert_svg_cmd(svg_config)
        if func is not None:
            return func
        logger.warning(
            "Attempting to import cairosvg for SVG support.")

    # Try to use pyvips
    # func = _convert_svg_pyvips()
    # if func is not None:
    #     return func

    # Try to use cairosvg
    func = _convert_svg_cairo(svg_config)
    if func is not None:
        return func

    logger.error((
        "SVG conversion is enabled but cairosvg does not "
        "appear to be installed. Consider configuring "
        "Inkscape under Asset settings in the GUI."
    ))

    # Failed
    return None


def uses_workers(use_workers):
    """
    Decorator used to mark whether a function is thread safe.
    """
    def decorator(func):
        func.use_workers = use_workers
        return func
    return decorator


def _convert_svg_cairo(svg_config):
    """
    Attempts to import cairosvg and return a function
    which uses cairosvg to convert an SVG to a PNG.
    """
    homebrew_lib = "/opt/homebrew/lib"
    if path.isdir(homebrew_lib):
        fallback_path = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        fallback_dirs = fallback_path.split(os.pathsep) if fallback_path else []
        if homebrew_lib not in fallback_dirs:
            fallback_dirs.insert(0, homebrew_lib)
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = os.pathsep.join(
                fallback_dirs)

    try:
        import cairosvg
    except ImportError:
        return None
    except OSError:
        logger.warning("Package cairosvg is not installed correctly.")
        return None

    @uses_workers(False)
    def convert_svg(svg_path, output_dir, md5ext):
        # Get the output path
        filename = f"{md5ext.rpartition('.')[0]}-svg-{svg_config.SVG_SCALE}x.png"
        png_path = path.join(output_dir, filename)

        # Verify the file hasn't already been converted
        if not svg_config.RECONVERT_IMAGES and path.isfile(png_path):
            logger.debug(
                "Skipping conversion of %s, already converted.", md5ext)
            return filename

        logger.debug("Converting %s to PNG using a cariosvg.", md5ext)

        # Convert the svg
        try:
            cairosvg.svg2png(url=svg_path, write_to=png_path,
                             scale=svg_config.SVG_SCALE)
            normalize_png_alpha(png_path)

        # Handle an unexpected error
        except ValueError:
            logger.exception(
                "Failed to convert SVG %s with cairosvg:", md5ext)

            return None
        return filename

    return convert_svg


def _convert_svg_pyvips():
    """
    Attempts to import cairosvg and return a function
    which uses cairosvg to convert an SVG to a PNG.
    """
    try:
        import pyvips
    except ImportError:
        return None
    except OSError:
        logger.warning("Package pyvips is not installed correctly.")
        return None

    @uses_workers(True)
    def convert_svg(svg_path, output_dir, md5ext):
        # Get the output path
        filename = f"{md5ext.rpartition('.')[0]}-svg-{config.SVG_SCALE}x.png"
        png_path = path.join(output_dir, filename)

        # Verify the file hasn't already been converted
        if not config.RECONVERT_IMAGES and path.isfile(png_path):
            logger.debug(
                "Skipping conversion of %s, already converted.", md5ext)
            return filename

        logger.debug("Converting %s to PNG using a pyvips.", md5ext)

        # Convert the SVG
        pyvips.Image.svgload(
            svg_path, memory=True, scale=config.SVG_SCALE
        ).pngsave(png_path)
        normalize_png_alpha(png_path)

        return filename
    return convert_svg


def _convert_svg_cmd(svg_config):
    """
    Attempts to verify that the SVG_COMMAND is valid and returns the
    function which uses the command to convert an SVG to a PNG.
    """
    # Verify the command exists
    prog = shlex.split(svg_config.SVG_COMMAND)[0]
    if shutil.which(prog) is None:
        logger.error((
            "SVG conversion with a command is enabled "
            "but '%s' does not appear to be installed."),
            prog
        )
        return None
    return lambda svg_path, output_dir, md5ext: convert_svg_cmd(
        svg_path, output_dir, md5ext, svg_config)


@uses_workers(True)
def convert_svg_cmd(svg_path, output_dir, md5ext, svg_config=None):
    """
    Converts the svg using the configured command. The md5ext is
    used for logging purposes.
    """
    if svg_config is None:
        svg_config = config.snapshot_config()

    # Get the output path
    filename = f"{md5ext.rpartition('.')[0]}-svg-{svg_config.SVG_SCALE}x.png"
    png_path = path.join(output_dir, filename)

    # Verify the file hasn't already been converted
    if not svg_config.RECONVERT_IMAGES and path.isfile(png_path):
        logger.debug(
            "Skipping conversion of %s, already converted.", md5ext)
        return filename

    logger.debug("Converting %s to PNG using a command.", md5ext)

    # Get the conversion command
    cmd_str = svg_config.SVG_COMMAND.format(
        INPUT=shlex.quote(svg_path),
        OUTPUT=shlex.quote(png_path),
        DPI=svg_config.BASE_DPI*svg_config.SVG_SCALE,
        SCALE=svg_config.SVG_SCALE
    )

    # Attempt to run the command
    try:
        result = subprocess.run(shlex.split(cmd_str), check=True, capture_output=True,
                                text=True, timeout=svg_config.CONVERT_TIMEOUT)

    # Command gave an error
    except subprocess.CalledProcessError as error:
        logger.error("Failed to convert svg '%s':\n%s\n%s\n",
                     md5ext, cmd_str, error.stderr.rstrip())
        return None

    # Command timed out
    except subprocess.TimeoutExpired:
        logger.error(
            "Failed to convert svg %s: Timeout expired.", md5ext)
        return None

    # Verify the command created a file
    if not path.isfile(png_path):
        logger.error("Failed to save svg %s:\n%s\n%s\n",
                     md5ext, cmd_str, result.stderr.rstrip())
        return None
    normalize_png_alpha(png_path)
    return filename


@uses_workers(True)
def fallback_image(_svg_path, output_dir, md5ext, svg_config=None):
    """Save a blank PNG image instead of converting."""
    if svg_config is None:
        svg_config = config.snapshot_config()

    logger.debug("Saving fallback PNG for %s.", md5ext)

    # Get the output filename
    filename = f"{md5ext.rpartition('.')[0]}-fallback.png"
    png_path = path.join(output_dir, filename)

    # Save the fallback image
    with open(png_path, 'wb') as image_file:
        image_file.write(svg_config.FALLBACK_IMAGE)

    return filename


def normalize_png_alpha(png_path):
    """
    Ensure converted SVG PNGs keep alpha and do not carry a black matte.

    Some converters and image pipelines leave fully transparent pixels with
    black RGB values. Those pixels are invisible until a later scale/rotate
    operation samples across the edge. Only pixels touching visible artwork
    are bled; the empty background stays fully transparent black.
    """
    try:
        from PIL import Image
    except ImportError:
        return

    try:
        source_image = Image.open(png_path)
        original_mode = source_image.mode
        image = source_image.convert("RGBA")
    except OSError:
        logger.exception("Failed to normalize alpha for '%s':", png_path)
        return

    alpha = image.getchannel("A")
    if "A" not in original_mode or alpha.getextrema() == (255, 255):
        _clear_uniform_edge_background(image)

    pixels = image.load()
    width, height = image.size
    edge_updates = {}

    for y in range(height):
        for x in range(width):
            if pixels[x, y][3] != 0:
                continue

            neighbors = []
            for nx in range(max(0, x - 1), min(width, x + 2)):
                for ny in range(max(0, y - 1), min(height, y + 2)):
                    if nx == x and ny == y:
                        continue
                    red, green, blue, pixel_alpha = pixels[nx, ny]
                    if pixel_alpha:
                        neighbors.append((red, green, blue))

            if neighbors:
                edge_updates[(x, y)] = tuple(
                    round(sum(color[index] for color in neighbors) / len(neighbors))
                    for index in range(3)
                )

    for (x, y), color in edge_updates.items():
        pixels[x, y] = (*color, 0)

    if edge_updates or original_mode != "RGBA":
        image.save(png_path)


def _clear_uniform_edge_background(image):
    """Make a solid converter-added edge background transparent."""
    pixels = image.load()
    width, height = image.size
    corner_colors = [
        pixels[0, 0][:3],
        pixels[width - 1, 0][:3],
        pixels[0, height - 1][:3],
        pixels[width - 1, height - 1][:3],
    ]

    background = max(set(corner_colors), key=corner_colors.count)
    if corner_colors.count(background) < 3:
        return

    stack = []
    seen = set()
    for x in range(width):
        stack.append((x, 0))
        stack.append((x, height - 1))
    for y in range(height):
        stack.append((0, y))
        stack.append((width - 1, y))

    clear_pixels = []
    while stack:
        x, y = stack.pop()
        if (x, y) in seen:
            continue
        seen.add((x, y))

        if pixels[x, y][:3] != background:
            continue

        clear_pixels.append((x, y))
        if x > 0:
            stack.append((x - 1, y))
        if x < width - 1:
            stack.append((x + 1, y))
        if y > 0:
            stack.append((x, y - 1))
        if y < height - 1:
            stack.append((x, y + 1))

    if len(clear_pixels) == width * height:
        return

    for x, y in clear_pixels:
        pixels[x, y] = (*background, 0)
