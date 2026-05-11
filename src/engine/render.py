"""
render.py

Contains the Display class for managing the screen.

Contains the Render class which handles drawing everything.
"""
import pygame as pg

from . import config
from .types import Pen


class Display:
    """
    Handles the display

    Attributes:
        size: The current screen size (w, h)

        scale: The current scale of a sigle pixel of the Stage

        fullscreen: Whether the screen is in fullscreen

        rect: Represents the stage position and size on the screen

        screen: The screen surface from pygame.display.set_mode
    """

    def __init__(self):
        self.size = config.DISPLAY_SIZE
        self.scale = 1
        self.fullscreen = False

        self.rect: pg.Rect
        self.screen: pg.Surface

        self.setup_display(config.DISPLAY_SIZE)

    def setup_display(self, size):
        """Setup the display mode"""
        # Get a centered rectangle to draw in
        if size[0] / config.STAGE_SIZE[0] < size[1] / config.STAGE_SIZE[1]:
            # Width is the limiting factor
            # height = scale * stage height
            scale = size[0] / config.STAGE_SIZE[0]
            rect = pg.Rect(
                0, (size[1] - scale * config.STAGE_SIZE[1]) // 2,
                size[0], scale * config.STAGE_SIZE[1])
        else:
            # Height is the limiting factor
            scale = size[1] / config.STAGE_SIZE[1]
            rect = pg.Rect(
                (size[0] - scale * config.STAGE_SIZE[0]) // 2,
                0, scale * config.STAGE_SIZE[0], size[1])

        # Save the calculated info
        self.size = size
        self.scale = scale
        self.rect = rect

        # Get flags
        if self.fullscreen:
            flags = config.DISPLAY_FLAGS | pg.FULLSCREEN
        else:
            flags = config.DISPLAY_FLAGS | pg.RESIZABLE

        # Mouse should be visible
        pg.mouse.set_visible(True)

        # Setup and redraw screen
        self.screen = pg.display.set_mode(self.size, flags)
        self.screen.fill((250, 250, 250))
        pg.display.flip()
        Pen.resize(self)

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        # Restart the display
        pg.display.quit()
        pg.display.init()

        self.fullscreen = not self.fullscreen

        # Get the display size
        if self.fullscreen:
            info = pg.display.Info()
            size = (info.current_w // config.FS_SCALE,
                    info.current_h // config.FS_SCALE)
        else:
            size = config.DISPLAY_SIZE

        # Setup the screen again
        self.setup_display(size)

    def video_resize(self, event):
        """Recalculates the rect and scale"""
        # Resize the display
        self.setup_display((event.w, event.h))


class Render:
    """
    Handles drawing the screen

    Attributes:
        group: pygame LayeredDirty sprite group

        stage: The stage Sprite

        rects: A list of dirty rects to update

        font: Used for debug text
    """

    def __init__(self, sprites):
        self.group = sprites.group
        self.stage = sprites.stage.sprite
        self.monitors = sprites.monitors
        self.rects = []
        self._full_redraw = True
        self._last_sprite_rects = {}
        self._last_monitor_rects = {}
        self._dirty_rect_limit = 24
        self._dirty_area_ratio = 0.55
        self.stats = {
            "frames": 0,
            "dirty_frames": 0,
            "full_redraws": 0,
            "last_dirty_rects": 0,
            "last_dirty_area": 0,
        }

        # Debug font
        self.font = pg.font.Font(None, 28)

    def draw(self, display):
        """Handles drawing everything"""
        dirty_rects = self._dirty_rects(display)
        self.stats["frames"] += 1
        self.stats["last_dirty_rects"] = len(dirty_rects)
        self.stats["last_dirty_area"] = sum(rect.width * rect.height for rect in dirty_rects)
        if not dirty_rects:
            return
        self.stats["dirty_frames"] += 1
        if len(dirty_rects) == 1 and dirty_rects[0] == display.screen.get_rect():
            self.stats["full_redraws"] += 1

        stage_base = self.stage.image.get_at((0, 0))
        for rect in dirty_rects:
            display.screen.set_clip(rect)
            display.screen.fill((255, 255, 255), rect)
            if stage_base.a < 255:
                display.screen.fill(stage_base[:3], rect.clip(display.rect))
            display.screen.blit(self.stage.image, self.stage.rect)

            if Pen.image is not None:
                display.screen.blit(Pen.image, display.rect.topleft)

            for sprite in self.group:
                if sprite.visible and sprite.rect.colliderect(rect):
                    display.screen.blit(
                        sprite.image,
                        sprite.rect,
                        sprite.source_rect,
                        sprite.blendmode,
                    )

            self._draw_monitors_in_rect(display, rect)
            self.rects.append(rect.copy())

        display.screen.set_clip(None)
        self.stage.dirty = 0

        for sprite in self.group:
            if sprite.dirty == 1:
                sprite.dirty = 0
            self._last_sprite_rects[sprite] = sprite.rect.copy()

        for monitor in self.monitors:
            if getattr(monitor, "dirty", 0):
                monitor.dirty = 0
            self._last_monitor_rects[monitor] = monitor.rect.copy()

        Pen.dirty = []
        self._full_redraw = False

    def _dirty_rects(self, display):
        """Collect screen regions that need to be redrawn."""
        if self._full_redraw or self.stage.dirty:
            return [display.screen.get_rect()]

        rects = [rect.copy() for rect in Pen.dirty]

        for sprite in self.group:
            previous = self._last_sprite_rects.get(sprite)
            if sprite.dirty or previous != sprite.rect:
                dirty = sprite.rect.copy()
                if previous is not None:
                    dirty.union_ip(previous)
                rects.append(dirty)

        for monitor in self.monitors:
            previous = self._last_monitor_rects.get(monitor)
            if getattr(monitor, "dirty", 0) or previous != monitor.rect:
                dirty = monitor.rect.copy()
                if previous is not None:
                    dirty.union_ip(previous)
                rects.append(dirty)

        screen_rect = display.screen.get_rect()
        clipped = [rect.clip(screen_rect) for rect in rects if rect.clip(screen_rect)]
        if self._should_promote_to_full_redraw(clipped, screen_rect):
            return [screen_rect]
        return clipped

    def _should_promote_to_full_redraw(self, rects, screen_rect):
        """Use a full redraw when dirty rects are too broad to be useful."""
        if not rects:
            return False
        if len(rects) > self._dirty_rect_limit:
            return True
        dirty_area = sum(rect.width * rect.height for rect in rects)
        screen_area = max(1, screen_rect.width * screen_rect.height)
        return dirty_area / screen_area > self._dirty_area_ratio

    def draw_monitors(self, display):
        """Draws all visible monitors"""
        for monitor in self.monitors:
            if monitor.visible:
                self.rects.append(monitor.rect)
                display.screen.blit(monitor.image, monitor.rect)

    def _draw_monitors_in_rect(self, display, rect):
        """Draw visible monitors that overlap a dirty rect."""
        for monitor in self.monitors:
            if monitor.visible and monitor.rect.colliderect(rect):
                display.screen.blit(monitor.image, monitor.rect)

    def draw_fps(self, display, clock):
        """Draws fps to the screen"""
        text = "%.1f FPS" % clock.get_fps()
        self.draw_text(display, text, (5, 5))

    def draw_sprite_rects(self, display):
        """Draws rects around every sprite"""
        # Draw rects
        for sprite in self.group:
            if sprite.visible:
                pg.draw.rect(
                    display.screen, (0, 0, 255), sprite.rect, 1)

        # Draw the stage center
        pg.draw.circle(display.screen, (0, 0, 255),
                       display.rect.center, 4)

    def draw_redraw_rects(self, display):
        """Draws rects in self.rects"""
        for rect in self.rects:
            pg.draw.rect(display.screen, (255, 100, 0), rect, 1)

    @staticmethod
    def draw_pen_rects(display):
        """Draws rects in Pen.dirty"""
        for rect in Pen.dirty:
            pg.draw.rect(display.screen, (0, 200, 100), rect, 1)

    def draw_text(self, display, text, pos, color=(0, 200, 200)):
        """Draws text for a single frame"""
        # Mark the drawn area as dirty
        rect = pg.Rect(pos, self.font.size(text))
        self.rects.append(rect)

        # Draw a rect for text off the stage
        if not display.rect.contains(rect):
            pg.draw.rect(display.screen, (255, 255, 255), rect)
            surf = self.font.render(text, True, color, (255, 255, 255))
        else:
            surf = self.font.render(text, True, color)
        display.screen.blit(surf, pos)

    def flip(self):
        """Update the display after drawing"""
        if self.rects:
            pg.display.update(self.rects)
        self.rects = []
        Pen.dirty = []

    def dirty_all(self):
        """Marks all sprites as dirty"""
        # Resize sprites, stage, and Pen
        for sprite in self.group.sprites():
            sprite.target.costume.dirty = True
        self.stage.target.costume.dirty = True
        self._full_redraw = True

    def request_full_redraw(self):
        """Request a full redraw without invalidating sprite transforms."""
        self._full_redraw = True
