"""
monitors.py

Contains classes for variable and list monitors.
"""

from functools import lru_cache

import pygame as pg


MONITOR_ORANGE = (255, 140, 26)
MONITOR_BORDER = (150, 150, 150)
MONITOR_BG = (238, 238, 238)
MONITOR_TEXT = (45, 45, 45)
LIST_ITEM_BG = (255, 255, 255)
LIST_INDEX = (96, 96, 96)


def _format_value(value):
    """Format monitor values close to Scratch's compact display."""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.6g}"
    return str(value)


def _scaled(surface, scale):
    """Scale a monitor surface for the current display."""
    if scale == 1:
        return surface.copy()
    size = (
        max(1, round(surface.get_width() * scale)),
        max(1, round(surface.get_height() * scale)),
    )
    return pg.transform.smoothscale(surface, size)


@lru_cache(maxsize=16)
def _font(name, size, bold=False):
    """Return a system font, falling back when the platform font is missing."""
    try:
        return pg.font.SysFont(name, size, bold=bold)
    except (FileNotFoundError, OSError):
        return pg.font.Font(None, size)


class Monitor(pg.sprite.DirtySprite):
    """A variable monitor with normal, large, and slider modes."""

    def __init__(self, name, target, varname, x, y, visible, mode,
                 slider_min=0, slider_max=100):
        super().__init__()
        self.name = name
        self.target = target
        self.varname = varname
        self.kind = "var"
        self._visible = bool(visible)
        self.mode = mode
        self.slider_min = float(slider_min)
        self.slider_max = float(slider_max)
        self.dragging = False

        self.font = _font("Arial", 12, bold=True)
        self.value_font = _font("Arial", 13, bold=True)
        self.large_font = _font("Arial", 20, bold=True)

        self.x = x
        self.y = y
        self.rect = pg.Rect(x, y, 0, 0)
        self.image = pg.Surface((1, 1), pg.SRCALPHA)

        self.last_value = None
        self._base_cache_key = None
        self._base_image = None
        self._scale_cache = {}
        self.dirty = 2

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        value = bool(value)
        if getattr(self, "_visible", None) != value:
            self._visible = value
            self.dirty = 2

    @property
    def monitor_name(self):
        return self.varname

    def update(self, display):
        if not self.visible:
            return

        try:
            value = getattr(self.target, self.varname)
        except AttributeError:
            value = ""

        if value != self.last_value or self.dirty or display.scale not in self._scale_cache:
            self.last_value = value
            self.render_monitor(display)
            self.dirty = 1

    def render_monitor(self, display):
        val_str = _format_value(self.last_value)
        cache_key = (self.mode, self.name, val_str, self.slider_min, self.slider_max)
        if cache_key != self._base_cache_key:
            self._base_cache_key = cache_key
            self._scale_cache.clear()
            if self.mode == "large":
                self._base_image = self._render_large(val_str)
            elif self.mode == "slider":
                self._base_image = self._render_slider(val_str)
            else:
                self._base_image = self._render_default(val_str)

        if display.scale not in self._scale_cache:
            self._scale_cache[display.scale] = _scaled(self._base_image, display.scale)
        self.image = self._scale_cache[display.scale]
        self.rect = self.image.get_rect()
        self.rect.topleft = (
            round(display.rect.x + self.x * display.scale),
            round(display.rect.y + self.y * display.scale),
        )

    def _render_default(self, val_str):
        name_surf = self.font.render(self.name, True, MONITOR_TEXT)
        val_surf = self.value_font.render(val_str, True, (255, 255, 255))

        val_width = max(val_surf.get_width() + 12, 34)
        width = name_surf.get_width() + val_width + 17
        height = 22

        image = pg.Surface((width, height), pg.SRCALPHA)
        pg.draw.rect(image, MONITOR_BG, image.get_rect(), border_radius=4)
        pg.draw.rect(image, MONITOR_BORDER, image.get_rect(), 1, border_radius=4)

        image.blit(name_surf, (5, (height - name_surf.get_height()) // 2))

        val_rect = pg.Rect(name_surf.get_width() + 11, 3, val_width, height - 6)
        pg.draw.rect(image, MONITOR_ORANGE, val_rect, border_radius=4)
        image.blit(val_surf, (
            val_rect.centerx - val_surf.get_width() // 2,
            val_rect.centery - val_surf.get_height() // 2,
        ))
        return image

    def _render_large(self, val_str):
        val_surf = self.large_font.render(val_str, True, (255, 255, 255))
        width = max(val_surf.get_width() + 16, 48)
        height = max(val_surf.get_height() + 8, 28)
        image = pg.Surface((width, height), pg.SRCALPHA)
        pg.draw.rect(image, MONITOR_ORANGE, image.get_rect(), border_radius=5)
        image.blit(val_surf, (
            (width - val_surf.get_width()) // 2,
            (height - val_surf.get_height()) // 2,
        ))
        return image

    def _render_slider(self, val_str):
        base = self._render_default(val_str)
        width = max(base.get_width(), 120)
        height = base.get_height() + 18
        image = pg.Surface((width, height), pg.SRCALPHA)
        image.blit(base, ((width - base.get_width()) // 2, 0))

        track = pg.Rect(12, base.get_height() + 6, width - 24, 4)
        pg.draw.rect(image, (204, 204, 204), track, border_radius=2)
        pg.draw.rect(image, (125, 125, 125), track, 1, border_radius=2)

        value = self._numeric_value()
        span = self.slider_max - self.slider_min
        fraction = 0.0 if span == 0 else (value - self.slider_min) / span
        fraction = max(0.0, min(1.0, fraction))
        knob_x = round(track.left + fraction * track.width)
        pg.draw.circle(image, MONITOR_ORANGE, (knob_x, track.centery), 6)
        pg.draw.circle(image, (130, 82, 20), (knob_x, track.centery), 6, 1)
        return image

    def _numeric_value(self):
        try:
            return float(self.last_value)
        except (TypeError, ValueError):
            return self.slider_min

    def handle_mouse_down(self, display, pos):
        if self.mode != "slider" or not self.visible or not self.rect.collidepoint(pos):
            return False
        self.dragging = True
        self._set_slider_from_pos(display, pos[0])
        return True

    def handle_mouse_motion(self, display, pos):
        if not self.dragging:
            return False
        self._set_slider_from_pos(display, pos[0])
        return True

    def handle_mouse_up(self):
        was_dragging = self.dragging
        self.dragging = False
        return was_dragging

    def _set_slider_from_pos(self, display, x_pos):
        local_x = (x_pos - self.rect.x) / display.scale
        width = max(self._base_image.get_width() if self._base_image else 120, 120)
        track_left = 12
        track_width = width - 24
        fraction = max(0.0, min(1.0, (local_x - track_left) / track_width))
        value = self.slider_min + fraction * (self.slider_max - self.slider_min)
        if value.is_integer():
            value = int(value)
        setattr(self.target, self.varname, value)
        self.dirty = 2

    def set_position(self, x, y, scale, display_rect):
        self.rect.x = display_rect.x + x * scale
        self.rect.y = display_rect.y + y * scale


class ListMonitor(pg.sprite.DirtySprite):
    """A Scratch-style list monitor with scrolling and cached scaling."""

    def __init__(self, name, target, listname, x, y, width, height, visible):
        super().__init__()
        self.name = name
        self.target = target
        self.listname = listname
        self.kind = "list"
        self._visible = bool(visible)

        self.font = _font("Arial", 12, bold=True)
        self.item_font = _font("Arial", 12)

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pg.Rect(x, y, width, height)
        self.image = pg.Surface((1, 1), pg.SRCALPHA)
        self.last_value = None
        self.scroll_index = 0
        self._base_cache_key = None
        self._base_image = None
        self._scale_cache = {}
        self.dirty = 2

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        value = bool(value)
        if getattr(self, "_visible", None) != value:
            self._visible = value
            self.dirty = 2

    @property
    def monitor_name(self):
        return self.listname

    def update(self, display):
        if not self.visible:
            return

        try:
            scratch_list = getattr(self.target, self.listname)
            value = list(getattr(scratch_list, "list", scratch_list))
        except AttributeError:
            value = []

        max_scroll = self._max_scroll(len(value))
        if self.scroll_index > max_scroll:
            self.scroll_index = max_scroll
            self.dirty = 2

        if value != self.last_value or self.dirty or display.scale not in self._scale_cache:
            self.last_value = value
            self.render_monitor(display)
            self.dirty = 1

    def render_monitor(self, display):
        width = max(1, self.width)
        height = max(1, self.height)
        cache_key = (
            tuple(_format_value(item) for item in self.last_value),
            self.scroll_index,
            width,
            height,
            self.name,
        )
        if cache_key != self._base_cache_key:
            self._base_cache_key = cache_key
            self._scale_cache.clear()
            self._base_image = self._render_base(width, height)

        if display.scale not in self._scale_cache:
            self._scale_cache[display.scale] = _scaled(self._base_image, display.scale)
        self.image = self._scale_cache[display.scale]
        self.rect = self.image.get_rect()
        self.rect.topleft = (
            round(display.rect.x + self.x * display.scale),
            round(display.rect.y + self.y * display.scale),
        )

    def _render_base(self, width, height):
        image = pg.Surface((width, height), pg.SRCALPHA)
        pg.draw.rect(image, MONITOR_BG, image.get_rect(), border_radius=4)
        pg.draw.rect(image, MONITOR_BORDER, image.get_rect(), 1, border_radius=4)

        name_surf = self.font.render(self.name, True, MONITOR_TEXT)
        image.blit(name_surf, ((width - name_surf.get_width()) // 2, 4))

        footer_height = 18
        items_top = 22
        items_bottom = max(items_top, height - footer_height - 2)
        item_height = 18
        visible_count = max(0, (items_bottom - items_top) // item_height)

        visible_items = self.last_value[self.scroll_index:self.scroll_index + visible_count]
        for row, item in enumerate(visible_items):
            index = self.scroll_index + row + 1
            y_pos = items_top + row * item_height
            item_rect = pg.Rect(5, y_pos, max(1, width - 18), item_height - 2)
            pg.draw.rect(image, LIST_ITEM_BG, item_rect, border_radius=3)
            pg.draw.rect(image, (210, 210, 210), item_rect, 1, border_radius=3)

            index_surf = self.item_font.render(str(index), True, LIST_INDEX)
            item_surf = self.item_font.render(_format_value(item), True, MONITOR_TEXT)
            image.blit(index_surf, (item_rect.x + 4, item_rect.y + 2))
            image.blit(item_surf, (item_rect.x + 28, item_rect.y + 2))

        if len(self.last_value) > visible_count and visible_count > 0:
            track = pg.Rect(width - 10, items_top, 5, max(1, items_bottom - items_top))
            pg.draw.rect(image, (205, 205, 205), track, border_radius=2)
            max_scroll = self._max_scroll(len(self.last_value))
            knob_h = max(12, round(track.height * visible_count / len(self.last_value)))
            knob_y = track.y if max_scroll == 0 else track.y + round(
                (track.height - knob_h) * self.scroll_index / max_scroll)
            pg.draw.rect(image, (145, 145, 145),
                         (track.x, knob_y, track.width, knob_h), border_radius=2)

        len_surf = self.font.render(f"length {len(self.last_value)}", True, MONITOR_TEXT)
        image.blit(len_surf, ((width - len_surf.get_width()) // 2, height - 15))
        return image

    def _visible_count(self):
        return max(0, (max(1, self.height) - 42) // 18)

    def _max_scroll(self, length):
        return max(0, length - self._visible_count())

    def handle_scroll(self, amount, pos=None):
        if not self.visible:
            return False
        if pos is not None and not self.rect.collidepoint(pos):
            return False
        old_index = self.scroll_index
        self.scroll_index = max(
            0,
            min(self._max_scroll(len(self.last_value or [])),
                self.scroll_index - amount),
        )
        if self.scroll_index != old_index:
            self.dirty = 2
            return True
        return False

    def set_position(self, x, y, scale, display_rect):
        self.rect.x = display_rect.x + x * scale
        self.rect.y = display_rect.y + y * scale


class ReporterMonitor(Monitor):
    """A monitor for built-in reporter values such as x, y, and timer."""

    def __init__(self, name, target, reporter, x, y, visible, mode="default"):
        super().__init__(name, target, reporter, x, y, visible, mode)
        self.kind = "reporter"
        self.reporter = reporter

    @property
    def monitor_name(self):
        return self.reporter

    def update(self, display, util=None):
        if not self.visible:
            return

        value = self._reporter_value(util)
        if value != self.last_value or self.dirty or display.scale not in self._scale_cache:
            self.last_value = value
            self.render_monitor(display)
            self.dirty = 1

    def _reporter_value(self, util):
        if self.reporter == "xpos":
            return round(self.target.xpos)
        if self.reporter == "ypos":
            return round(self.target.ypos)
        if self.reporter == "direction":
            return round(self.target.direction)
        if self.reporter == "timer" and util is not None:
            return round(util.timer(), 1)
        return ""
