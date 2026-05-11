import os
import unittest
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame as pg

from engine.monitors import ListMonitor, Monitor, ReporterMonitor
from engine.render import Render
from engine.runtime import Sprites


class MonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init()
        pg.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pg.quit()

    def make_display(self, scale=1):
        screen = pg.display.set_mode((240, 180))
        return SimpleNamespace(
            screen=screen,
            rect=pg.Rect(0, 0, 240, 180),
            scale=scale,
        )

    def test_variable_monitor_reuses_scaled_surface_until_value_changes(self):
        display = self.make_display(scale=2)
        target = SimpleNamespace(var_score=10)
        monitor = Monitor("score", target, "var_score", 4, 5, True, "default")

        with mock.patch.object(pg.transform, "smoothscale", wraps=pg.transform.smoothscale) as smoothscale:
            monitor.update(display)
            monitor.dirty = 0
            monitor.update(display)
            target.var_score = 11
            monitor.update(display)

        self.assertEqual(smoothscale.call_count, 2)
        self.assertEqual(monitor.rect.topleft, (8, 10))

    def test_monitor_font_falls_back_when_system_font_is_missing(self):
        with mock.patch.object(pg.font, "SysFont", side_effect=FileNotFoundError):
            monitor = Monitor("score", SimpleNamespace(var_score=1), "var_score",
                              0, 0, True, "default")

        self.assertIsInstance(monitor.font, pg.font.Font)

    def test_slider_monitor_updates_target_value_from_mouse(self):
        display = self.make_display()
        target = SimpleNamespace(var_volume=0)
        monitor = Monitor("volume", target, "var_volume", 10, 10, True,
                          "slider", 0, 100)
        monitor.update(display)

        self.assertTrue(monitor.handle_mouse_down(display, (118, 35)))
        self.assertGreater(target.var_volume, 90)
        self.assertTrue(monitor.dirty)
        self.assertTrue(monitor.handle_mouse_up())

    def test_list_monitor_scrolls_visible_items(self):
        display = self.make_display()
        target = SimpleNamespace(var_items=SimpleNamespace(list=list(range(8))))
        monitor = ListMonitor("items", target, "var_items", 0, 0, 120, 78, True)
        monitor.update(display)

        self.assertTrue(monitor.handle_scroll(-1, (10, 30)))
        self.assertEqual(monitor.scroll_index, 1)
        monitor.update(display)
        self.assertEqual(monitor.dirty, 1)

    def test_reporter_monitor_reads_sprite_position_and_timer(self):
        display = self.make_display()
        target = SimpleNamespace(xpos=12.4, ypos=-5.6, direction=90)
        xpos = ReporterMonitor("x position", target, "xpos", 0, 0, True)
        timer = ReporterMonitor("timer", target, "timer", 0, 24, True)

        xpos.update(display)
        timer.update(display, SimpleNamespace(timer=lambda: 1.26))

        self.assertEqual(xpos.last_value, 12)
        self.assertEqual(timer.last_value, 1.3)

    def test_sprites_show_hide_matches_var_and_list_monitors(self):
        sprites = Sprites.__new__(Sprites)
        var_monitor = Monitor("score", SimpleNamespace(var_score=1), "var_score",
                              0, 0, False, "default")
        list_monitor = ListMonitor("items", SimpleNamespace(var_items=[]),
                                   "var_items", 0, 0, 100, 80, False)
        sprites.monitors = [var_monitor, list_monitor]

        Sprites.monitors_show(sprites, "var", "var_score")
        Sprites.monitors_show(sprites, "list", "var_items")

        self.assertTrue(var_monitor.visible)
        self.assertTrue(list_monitor.visible)

        Sprites.monitors_hide(sprites, "list", "var_items")

        self.assertTrue(var_monitor.visible)
        self.assertFalse(list_monitor.visible)

    def test_renderer_promotes_fragmented_dirty_rects_to_full_redraw(self):
        stage_sprite = pg.sprite.DirtySprite()
        stage_sprite.image = pg.Surface((240, 180)).convert()
        stage_sprite.image.fill((10, 20, 30))
        stage_sprite.rect = pg.Rect(0, 0, 240, 180)
        stage_sprite.dirty = 0

        group = pg.sprite.LayeredDirty()
        for index in range(25):
            sprite = pg.sprite.DirtySprite()
            sprite.image = pg.Surface((2, 2), pg.SRCALPHA)
            sprite.rect = pg.Rect(index * 2, 0, 2, 2)
            sprite.visible = True
            sprite.source_rect = None
            sprite.blendmode = 0
            sprite.dirty = 1
            group.add(sprite)

        render = Render(SimpleNamespace(
            group=group,
            stage=SimpleNamespace(sprite=stage_sprite),
            monitors=[],
        ))
        render._full_redraw = False
        display = self.make_display()

        render.draw(display)

        self.assertEqual(render.rects, [display.screen.get_rect()])
        self.assertEqual(render.stats["full_redraws"], 1)


if __name__ == "__main__":
    unittest.main()
