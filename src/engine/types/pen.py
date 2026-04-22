"""
pen.py

Contains the Pen class and helper functions

TODO Consider using properties for the Pen?
"""

__all__ = ['Pen']


import pygame as pg
from typing import Any, List, Optional, Tuple, TYPE_CHECKING, Union

from ..operators import tonum
from ..config import STAGE_SIZE

if TYPE_CHECKING:
    from .target import Target
    from ..util import Util

__all__ = ['Pen']


class Pen:
    """
    Handles the pen for a sprite

    Attributes:
        target: The sprite of this Pen intance

        isdown: Whether the pen is down

        size: The current pen size

        color: The rgb pygame.Color instance

        hsva: Saved for greater accuracy

        shade: Legacy shade value

        position: Position since last moved

        _alpha_img:  Used internally for transparent blitting

        _scale: The screen scale

        _rect: The stage rect

    Class Attributes:
        image: Shared image of the pen

        dirty: Shared list of dirty rects, screen coords

        util: Shared for internal use, must be set
    """

    image: pg.Surface = None # type: ignore
    dirty: List[pg.Rect] = []

    _scale: float
    _rect: pg.Rect

    _alpha_img: pg.Surface

    def __init__(self, sprite: 'Target'):
        self.target: 'Target' = sprite

        self.isdown: bool = False
        self.size: float = 1.0

        self.color: pg.Color = pg.Color("blue")
        self.alpha: int = 255
        self.hsva: Tuple[float, float, float, float] = self.color.hsva
        self.shade: float = 50.0

        self.position: Tuple[float, float] = (
            self.target.xpos + STAGE_SIZE[0] // 2,
            STAGE_SIZE[1] // 2 - self.target.ypos
        )

    @classmethod
    def clear_all(cls):
        """Clear the pen image"""
        if cls.image is not None:
            cls.image.fill((255, 255, 255, 0))
            cls.dirty = [cls.image.get_rect()]

    def down(self):
        """Puts the pen down"""
        self.isdown = True
        self.move(self.target.xpos, self.target.ypos)

    def up(self):  # pylint: disable=invalid-name
        """Puts the pen up"""
        self.isdown = False

    def stamp(self, util: 'Util'):
        """Stamp the sprite image"""
        self.target.update(util.display)
        if self.image is not None:
            rect = self.image.blit(
                self.target.sprite.image, 
                self.target.sprite.rect.move(-self._rect.x, -self._rect.y)
            )
            Pen.dirty.append(rect.move(self._rect.topleft))

    def move(self, xpos: float, ypos: float):
        """Moves and draws with the pen"""
        if self.isdown:
            # Get the pen offset
            offset = 0.5 if self.size in (1, 3) else 0.0

            # Get new position
            end_pos = (xpos + STAGE_SIZE[0] // 2,
                       STAGE_SIZE[1] // 2 - ypos)

            size = max(1, round(self.size * self._scale))

            # Used to draw transparent lines in pg
            if self.color.a == 255:
                surf = Pen.image
            else:
                surf = Pen._alpha_img

            # Draw the line
            if surf is not None:
                rect = pg.draw.line(
                    surf, self.color,
                    scale_point(self.position, self._scale, offset),
                    scale_point(end_pos, self._scale, offset), size)
                rect.union_ip(pg.draw.circle(
                    surf, self.color,
                    scale_point(self.position, self._scale, offset), size / 2))
                rect.union_ip(pg.draw.circle(
                    surf, self.color,
                    scale_point(end_pos, self._scale, offset), size / 2))
                Pen.dirty.append(rect.move(self._rect.topleft))

                # Blit with blending transparency
                if self.color.a != 255 and Pen.image is not None:
                    Pen.image.blit(surf, rect.topleft, rect)
                    Pen._alpha_img.fill((0, 0, 0, 0), rect)

            self.position = end_pos
        else:
            self.position = (xpos + STAGE_SIZE[0] // 2,
                             STAGE_SIZE[1] // 2 - ypos)

    def set_size(self, value: float):
        """Sets and clamps the pen size"""
        self.size = max(1.0, min(1200.0, value))

    def change_size(self, value: float):
        """Changes and clamps the pen size"""
        self.set_size(self.size + value)

    def exact_color(self, value: Union[str, float]):
        """Sets the exact pen color"""
        # Translate the color
        if isinstance(value, str) and value.startswith("#"):
            try:
                self._hex_color(int(value.lstrip('#'), 16))
            except ValueError:
                self.color = pg.Color("black")
        else:
            self._hex_color(int(tonum(value)))

        self.hsva = self.color.hsva
        self.shade = self.hsva[2] / 2.0

    def _hex_color(self, value: int):
        """Gets alpha from a int color"""
        # Rotate the 8 most significant bits to the end
        # Pygame reads RGBA rather than ARGB
        value = value % 0xFFFFFFFF
        self.color = pg.Color(
            ((value & 0xFFFFFF) << 8) + ((value >> 24) or 255))

    def set_color(self, prop: str, value: float):
        """Sets a certain color property"""
        hue, sat, val, alp = map(round, self.hsva, (9, 9, 9, 9))
        if prop == "color":
            self.hsva = (value * 3.6 % 360, float(sat), float(val), float(alp))
        elif prop == "saturation":
            self.hsva = (float(hue), value % 100, float(val), float(alp))
        elif prop == "brightness":
            self.hsva = (float(hue), float(sat), max(0.0, min(100.0, value)), float(alp))
        elif prop == "transparency":
            self.hsva = (float(hue), float(sat), float(val), max(0.0, min(100.0, 100.0 - value)))
        else:
            print("Invalid color property ", prop)
        self.color.hsva = self.hsva

    def change_color(self, prop: str, value: float):
        """Changes a certain color property"""
        hue, sat, val, alp = map(round, self.hsva, (9, 9, 9, 9))
        if prop == "color":
            self.hsva = ((hue + (value * 3.6)) % 360, float(sat), float(val), float(alp))
        elif prop == "saturation":
            self.hsva = (float(hue), max(0.0, min(100.0, float(sat) + value)), float(val), float(alp))
        elif prop == "brightness":
            self.hsva = (float(hue), float(sat), max(0.0, min(100.0, float(val) + value)), float(alp))
        elif prop == "transparency":
            self.hsva = (float(hue), float(sat), float(val), max(0.0, min(100.0, float(alp) - value)))
        else:
            print("Invalid color property ", prop)
        self.color.hsva = self.hsva

    def set_shade(self, value: float):
        """Legacy set shade"""
        shade = value % 200
        self.shade = shade
        self._legacy_update_color()

    def change_shade(self, value: float):
        """Legacy change shade"""
        self.set_shade(self.shade + value)

    def set_hue(self, hue: float):
        """Legacy set color"""
        self.set_color("color", hue / 2.0)
        self._legacy_update_color()

    def change_hue(self, value: float):
        """Legacy change color"""
        self.change_color("color", value / 2.0)
        self._legacy_update_color()

    def _legacy_update_color(self):
        """Update color using shade"""
        self.color.hsva = (self.hsva[0], 100, 100, self.hsva[3])
        shade = (200.0 - self.shade) if self.shade > 100 else self.shade
        if shade < 50:
            self.color = lerp((0, 0, 0), tuple(self.color), (10.0 + shade) / 60.0)
        else:
            self.color = lerp(tuple(self.color), (255, 255, 255), (shade - 50.0) / 60.0)
        self.hsva = self.color.hsva

    def copy(self, clone: 'Target') -> 'Pen':
        """Create a copy of the pen"""
        pen = Pen(clone)
        pen.isdown = self.isdown
        pen.color = pg.Color(self.color.r, self.color.g,
                             self.color.b, self.color.a)
        pen.size = self.size
        return pen

    @classmethod
    def resize(cls, display: Any):
        """Create/resize the Pen image"""
        if cls.image is None:
            cls.image = pg.Surface(display.rect.size).convert_alpha()
            cls.scale = display.scale
            cls.clear_all()
        else:
            cls.image = pg.transform.smoothscale(cls.image, display.rect.size)
            cls.dirty = []

        # Create the alpha img
        cls._alpha_img = pg.Surface(display.rect.size).convert_alpha()
        cls._alpha_img.fill((0, 0, 0, 0))

        # Save info about the display
        cls._rect = display.rect
        cls._scale = display.scale


def lerp(color0: Tuple[int, int, int], color1: Tuple[int, int, int], fraction1: float) -> pg.Color:
    """Linear interpolation of colors"""
    if fraction1 <= 0:
        return pg.Color(*color0)
    if fraction1 >= 1:
        return pg.Color(*color1)
    fraction0 = 1.0 - fraction1
    return pg.Color(
        round((fraction0 * color0[0]) + (fraction1 * color1[0])),
        round((fraction0 * color0[1]) + (fraction1 * color1[1])),
        round((fraction0 * color0[2]) + (fraction1 * color1[2]))
    )


def scale_point(point: Tuple[float, float], disp_scale: float, offset: float) -> Tuple[int, int]:
    """Scales and rounds point to match the display"""
    return (round((point[0] + offset) * disp_scale),
            round((point[1] + offset) * disp_scale))
