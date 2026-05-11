"""
costumes.py

Contains the Costumes class and helper functions
"""

import logging
import random

import pygame as pg
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Union

from ..config import STAGE_SIZE

logger = logging.getLogger(__name__)

try:
    import numpy as np
except ImportError:  # pragma: no cover - exercised only without optional dependency
    np = None

if TYPE_CHECKING:
    pass

__all__ = ['Costumes']


class Costumes:
    """
    Handles costumes for a target

    Attributes:
        costumes: A dict referencing costume by name

        costumes_list: Used to reference costumes by number

        name: The name of the current costume, readonly

        number: The number of the current costume, readonly

        size: The current costume size

        rotation_style: The current rotation style

        target: The parent target, used to set dirty TODO Here

        effects: A dict of current effects and values

        dirty: Whether the image needs to be updated

    Class Attributes:
        redraw_requested: Used to indicate a sprite has requested a
            screen redraw

        _cache - A shared cache containing loaded images
    """

    redraw_requested: bool = False
    _cache: Dict[str, pg.Surface] = {}
    _transform_cache: Dict[Tuple[Any, ...], Tuple[pg.Surface, pg.Surface]] = {}

    def __init__(self, costume_number: int, size: float,
                 rotation_style: str, costumes: List[Dict[str, Any]],
                 copy_dicts: Optional[Tuple[Dict[str, Dict[str, Any]], Dict[str, float]]] = None):
        self.number: int = costume_number + 1
        self.costume: Dict[str, Any] = costumes[costume_number]
        self._size: float = size
        self.rotation_style: str = rotation_style

        self.dirty: bool = True

        self.costume_list: List[Dict[str, Any]] = costumes

        # Last gotten image without effects
        # Used to get the sprite mask
        self.last_image: Optional[pg.Surface] = None

        if copy_dicts is None:
            self.effects: Dict[str, float] = {}
            self.costumes: Dict[str, Dict[str, Any]] = {}

            # Initialize the costume lists
            for index, asset in enumerate(costumes):
                # Load the image
                asset['image'] = self._load_image(asset['path'])
                crop_offset = self._trim_transparent_border(asset)

                # Calculate the rotation offset
                center = pg.math.Vector2(asset['image'].get_size()) / 2
                asset['offset'] = pg.math.Vector2(asset['center']) - crop_offset
                asset['offset'] *= -1
                asset['offset'] += center
                asset['offset'] /= asset['scale']

                # Add the costume to the dict
                asset['number'] = index + 1
                self.costumes[asset['name']] = asset
        else:
            self.costumes = copy_dicts[0]
            self.effects = copy_dicts[1]

    def _load_image(self, path: str) -> pg.Surface:
        """Loads an image or retrieves it from cache"""
        image = self._cache.get(path)
        if not image:
            try:
                image = pg.image.load("assets/" + path).convert_alpha()
                self._cache[path] = image
            except (pg.error, FileNotFoundError) as error:
                logger.warning(
                    "Failed to load '%s'. Using a blank image instead.",
                    path,
                    exc_info=True,
                )

                image = pg.Surface((2, 2), pg.SRCALPHA)
                image.fill((0, 0, 0, 0))
                image = image.convert_alpha()

                self._cache[path] = image

        return image

    @staticmethod
    def _trim_transparent_border(asset: Dict[str, Any]) -> pg.math.Vector2:
        """Crop empty transparent borders while preserving costume center."""
        image = asset['image']

        if not image.get_masks()[3]:
            return pg.math.Vector2()

        rect = image.get_bounding_rect(min_alpha=1)
        if rect.size == image.get_size() or rect.width == 0 or rect.height == 0:
            return pg.math.Vector2()

        cropped = pg.Surface(rect.size, pg.SRCALPHA).convert_alpha()
        cropped.fill((0, 0, 0, 0))
        cropped.blit(image, (0, 0), rect)
        asset['image'] = cropped

        return pg.math.Vector2(rect.topleft)

    def switch(self, costume: Union[str, float]):
        """Sets the costume"""
        costume_name = str(costume)
        special_costume = costume_name.lower()

        if special_costume == "next costume":
            self.next()
            return

        if special_costume == "previous costume":
            self.previous()
            return

        if special_costume == "random costume":
            self._switch_number(random.randrange(len(self.costume_list)) + 1)
            return

        asset = self.costumes.get(costume_name)
        if asset:
            self.costume = asset
            self.number = asset['number']
        else:
            try:
                self._switch_number(round(float(costume)))
            except (ValueError, TypeError, OverflowError):
                pass

        # Set dirty
        self.dirty = True
        Costumes.redraw_requested = True

    def _switch_number(self, number: int):
        """Switch to a 1-based costume number with Scratch-style wrapping."""
        self.number = (number - 1) % len(self.costume_list) + 1
        self.costume = self.costume_list[self.number - 1]

    def next(self):
        """Go to the next costume"""
        self._switch_number(self.number + 1)

        # Set dirty
        self.dirty = True
        Costumes.redraw_requested = True

    def previous(self):
        """Go to the previous costume"""
        self._switch_number(self.number - 1)

        # Set dirty
        self.dirty = True
        Costumes.redraw_requested = True

    @property
    def size(self) -> float:
        """The current costume size"""
        return self._size

    @size.setter
    def size(self, value: float):
        image = self.costume['image']

        cost_w = image.get_width() / self.costume['scale']
        cost_h = image.get_height() / self.costume['scale']

        min_scale = min(1.0, max(5.0 / cost_w, 5.0 / cost_h))
        max_scale = min(1.5 * STAGE_SIZE[0] / cost_w,
                        1.5 * STAGE_SIZE[1] / cost_h)

        self._size = max(min_scale, min(max_scale, value / 100.0)) * 100.0

        # Set dirty
        self.dirty = True
        Costumes.redraw_requested = True

    @property
    def name(self) -> str:
        """The name of the current costume"""
        return self.costume['name']

    def set_effect(self, effect: str, value: float):
        """Sets and wraps/clamps a graphics effect"""
        effect = str(effect).lower()
        if effect == 'ghost':
            self.effects[effect] = min(max(value, 0.0), 100.0)
        elif effect == 'brightness':
            self.effects[effect] = min(max(value, -100.0), 100.0)
        elif effect == 'color':
            self.effects[effect] = value % 200.0
        elif effect in ('pixelate', 'mosaic', 'fisheye', 'whirl'):
            self.effects[effect] = value

        # Set dirty
        self.dirty = True
        Costumes.redraw_requested = True

    def change_effect(self, effect: str, value: float):
        """Changes and wraps/clamps a graphics effect"""
        effect = str(effect).lower()
        current_value = self.effects.get(effect, 0.0)
        self.set_effect(effect, current_value + value)

    def clear_effects(self):
        """Clear all graphic effects"""
        self.effects.clear()

        # Set dirty
        self.dirty = True
        Costumes.redraw_requested = True

    def _transform_cache_key(self, display: Any, direction: float) -> Tuple[Any, ...]:
        """Return a stable key for the transformed costume surface."""
        if self.rotation_style == "all around":
            direction_key = round(direction, 3)
        elif self.rotation_style == "left-right":
            direction_key = direction < 0
        else:
            direction_key = None

        return (
            self.costume.get('path', id(self.costume['image'])),
            self.number,
            round(self._size, 3),
            round(float(display.scale), 6),
            self.rotation_style,
            direction_key,
            tuple(sorted((name, round(float(value), 3))
                         for name, value in self.effects.items())),
        )

    def _apply_effects(self, image: pg.Surface) -> pg.Surface:
        """Apply current effects to an image"""
        # Pixelate
        pixelate = self.effects.get('pixelate', 0.0)
        if pixelate != 0:
            # Scratch pixelate: size of pixel is (abs(value) / 10 + 1)
            # We'll use a slightly different formula to match the look
            pixel_size = max(1, int(abs(pixelate) / 10) + 1)
            if pixel_size > 1:
                original_size = image.get_size()
                small_size = (max(1, original_size[0] // pixel_size),
                              max(1, original_size[1] // pixel_size))
                image = pg.transform.scale(image, small_size)
                image = pg.transform.scale(image, original_size)

        # Mosaic
        mosaic = self.effects.get('mosaic', 0.0)
        if mosaic != 0:
            # Scratch mosaic: count is (abs(value) / 10 + 1) rounded up
            count = max(1, int((abs(mosaic) + 10) / 10))
            if count > 1:
                original_size = image.get_size()
                small_size = (max(1, original_size[0] // count),
                              max(1, original_size[1] // count))
                small_image = pg.transform.smoothscale(image, small_size)
                image = pg.Surface(original_size, pg.SRCALPHA)
                for x in range(count):
                    for y in range(count):
                        image.blit(small_image, (x * small_size[0], y * small_size[1]))

        # Brighten/Darken
        brightness = self.effects.get('brightness', 0.0)
        if brightness > 0:
            brightness_val = 255 * brightness / 100
            image.fill(
                (brightness_val, brightness_val, brightness_val),
                special_flags=pg.BLEND_RGB_ADD)
        elif brightness < 0:
            brightness_val = -255 * brightness / 100
            image.fill(
                (brightness_val, brightness_val, brightness_val),
                special_flags=pg.BLEND_RGB_SUB)

        # Transparency
        ghost = self.effects.get('ghost', 0.0)
        if ghost:
            ghost_val = 255 - 255 * ghost / 100
            image = image.copy()
            image.fill(
                (255, 255, 255, ghost_val),
                special_flags=pg.BLEND_RGBA_MULT)

        # Hue change
        color = self.effects.get('color', 0.0)
        if color:
            color_val = 360 * color / 200
            image = hue_effect(image, color_val)

        fisheye = self.effects.get('fisheye', 0.0)
        if fisheye != 0:
            image = self._apply_fisheye(image, fisheye)

        whirl = self.effects.get('whirl', 0.0)
        if whirl != 0:
            image = self._apply_whirl(image, whirl)

        return image

    def _apply_fisheye(self, image: pg.Surface, value: float) -> pg.Surface:
        """Apply a radial fisheye effect."""
        if np is None:
            logger.warning("Fisheye effect requires numpy; leaving image unchanged.")
            return image

        strength = max(-100.0, min(100.0, float(value))) / 100.0
        if strength == 0.0:
            return image

        width, height = image.get_size()
        x_grid, y_grid, radius, theta = _surface_polar_grid(width, height)
        valid = radius <= 1.0

        if strength > 0:
            mapped_radius = radius ** (1.0 + strength * 1.8)
        else:
            mapped_radius = radius ** (1.0 / (1.0 + abs(strength) * 1.8))

        source_x = mapped_radius * np.cos(theta) * max(width - 1, 1) / 2.0 + (width - 1) / 2.0
        source_y = mapped_radius * np.sin(theta) * max(height - 1, 1) / 2.0 + (height - 1) / 2.0
        return _remap_surface(image, source_x, source_y, valid, x_grid, y_grid)

    def _apply_whirl(self, image: pg.Surface, value: float) -> pg.Surface:
        """Apply a radial whirl effect."""
        if np is None:
            logger.warning("Whirl effect requires numpy; leaving image unchanged.")
            return image

        width, height = image.get_size()
        x_grid, y_grid, radius, theta = _surface_polar_grid(width, height)
        valid = radius <= 1.0
        twist = np.radians(float(value)) * (1.0 - np.minimum(radius, 1.0))
        source_theta = theta - twist
        source_x = radius * np.cos(source_theta) * max(width - 1, 1) / 2.0 + (width - 1) / 2.0
        source_y = radius * np.sin(source_theta) * max(height - 1, 1) / 2.0 + (height - 1) / 2.0
        return _remap_surface(image, source_x, source_y, valid, x_grid, y_grid)

    def get_image(self, display: Any, direction: float) -> pg.Surface:
        """Get the current image with a size and direction"""
        cache_key = self._transform_cache_key(display, direction)
        cached = self._transform_cache.get(cache_key)
        if cached is not None:
            self.last_image = cached[0]
            return cached[1]

        # Get the base image
        image = self.costume['image']

        # Scale the image
        scale = self._size / 100.0 / \
            self.costume['scale'] * display.scale
        image = pg.transform.smoothscale(
            image, (min(9000, max(4, int(image.get_width() * scale))),
                    min(9000, max(4, int(image.get_height() * scale))))
        )

        # Rotate the image
        if self.rotation_style == "all around":
            # Segmentation fault here if image size is too small
            image = pg.transform.rotate(image, 90.0 - direction)
        elif self.rotation_style == "left-right":
            if direction < 0:
                image = pg.transform.flip(image, True, False)

        # Save the image without effects
        self.last_image = image

        # Apply effects
        if self.effects:
            image = self._apply_effects(image.copy())

        self._transform_cache[cache_key] = (self.last_image, image)

        return image

    def copy(self) -> 'Costumes':
        """Return a copy of this Costumes object"""
        cost = Costumes(self.number - 1, self._size,
                        self.rotation_style, self.costume_list,
                        (self.costumes, self.effects.copy()))
        return cost

    def get_mask(self) -> pg.mask.Mask:
        """
        Get a sprite mask using the last gotten image without effects
        """
        return pg.mask.from_surface(self.last_image)


def hue_effect(src_image: pg.Surface, value: float) -> pg.Surface:
    """
    Changes the hue of an image for the color effect.

    The value should be between 0 and 360. Coverts the image to an
    8-bit surface and adjusts the color palette. Transparency is
    first copied to preserve it.
    """

    # Get a copy of the alpha channel
    transparency = src_image.convert_alpha()
    transparency.fill((255, 255, 255, 0),
                      special_flags=pg.BLEND_RGBA_MAX)

    # Get an 8-bit surface with a color palette
    # Workaround, see Pygame Issue #2477
    image = pg.Surface(src_image.get_size(), depth=8)
    image.blit(src_image, (0, 0))

    # Change the hue of the palette
    for index in range(256):
        # Get the palette color at index
        color = pg.Color(*image.get_palette_at(index))

        # Get the new hue
        hue = color.hsva[0] + value
        if hue > 360:
            hue -= 360

        # Update the hue
        color.hsva = (hue, *color.hsva[1:3])
        image.set_palette_at(index, color)

    # Return the image transparency
    image.set_alpha()
    image = image.convert_alpha()
    image.blit(transparency, (0, 0), special_flags=pg.BLEND_RGBA_MULT)

    return image


def _surface_polar_grid(width: int, height: int):
    """Return cartesian and polar coordinate grids for a surface."""
    x_grid, y_grid = np.meshgrid(
        np.arange(width, dtype=np.float64),
        np.arange(height, dtype=np.float64),
        indexing='ij',
    )
    center_x = (width - 1) / 2.0
    center_y = (height - 1) / 2.0
    norm_x = (x_grid - center_x) / max(width - 1, 1) * 2.0
    norm_y = (y_grid - center_y) / max(height - 1, 1) * 2.0
    radius = np.sqrt(norm_x * norm_x + norm_y * norm_y)
    theta = np.arctan2(norm_y, norm_x)
    return x_grid, y_grid, radius, theta


def _remap_surface(
        image: pg.Surface,
        source_x,
        source_y,
        valid,
        x_grid,
        y_grid) -> pg.Surface:
    """Remap a surface using nearest-neighbor source coordinates."""
    source = image.convert_alpha()
    rgb = pg.surfarray.array3d(source)
    alpha = pg.surfarray.array_alpha(source)

    src_x = np.rint(source_x).astype(np.int64).clip(0, image.get_width() - 1)
    src_y = np.rint(source_y).astype(np.int64).clip(0, image.get_height() - 1)
    dst_x = x_grid.astype(np.int64)
    dst_y = y_grid.astype(np.int64)

    out_rgb = rgb.copy()
    out_alpha = alpha.copy()
    out_rgb[dst_x[valid], dst_y[valid]] = rgb[src_x[valid], src_y[valid]]
    out_alpha[dst_x[valid], dst_y[valid]] = alpha[src_x[valid], src_y[valid]]

    result = pg.surfarray.make_surface(out_rgb).convert_alpha()
    result_alpha = pg.surfarray.pixels_alpha(result)
    result_alpha[:, :] = out_alpha
    del result_alpha
    return result
