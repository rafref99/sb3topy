import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame as pg

from types import SimpleNamespace

from engine.render import Render
from engine.types.target import Target
from engine.types.costumes import Costumes
from engine.types.pen import Pen


class CostumeEffectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init()
        pg.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pg.quit()

    def make_costumes(self):
        image = pg.Surface((4, 4), pg.SRCALPHA)
        image.fill((100, 120, 140, 255))

        asset = {
            "name": "costume1",
            "image": image,
            "center": (2, 2),
            "scale": 1,
            "number": 1,
        }
        return Costumes(
            0,
            100,
            "don't rotate",
            [asset],
            ({"costume1": asset}, {}),
        )

    def test_ghost_effect_uses_scratch_uppercase_name(self):
        costumes = self.make_costumes()

        costumes.set_effect("GHOST", 50)
        image = costumes.get_image(type("Display", (), {"scale": 1})(), 90)

        self.assertEqual(costumes.effects["ghost"], 50)
        self.assertLess(image.get_at((0, 0)).a, 255)
        self.assertGreater(image.get_at((0, 0)).a, 100)

    def test_ghost_effect_clamps_and_clears(self):
        costumes = self.make_costumes()

        costumes.set_effect("GHOST", 250)
        self.assertEqual(costumes.effects["ghost"], 100)

        image = costumes.get_image(type("Display", (), {"scale": 1})(), 90)
        self.assertEqual(image.get_at((0, 0)).a, 0)

        costumes.clear_effects()
        image = costumes.get_image(type("Display", (), {"scale": 1})(), 90)
        self.assertEqual(image.get_at((0, 0)).a, 255)

    def test_render_keeps_stage_visible_through_transparent_sprite_pixels(self):
        sprite = pg.sprite.DirtySprite()
        sprite.image = pg.Surface((20, 20), pg.SRCALPHA)
        sprite.image.fill((0, 0, 0, 0))
        sprite.image.fill((255, 0, 0, 255), pg.Rect(10, 10, 5, 5))
        sprite.rect = pg.Rect(0, 0, 20, 20)
        sprite.visible = True

        group = pg.sprite.LayeredDirty(sprite)
        stage_sprite = pg.sprite.DirtySprite()
        stage_sprite.image = pg.Surface((40, 40)).convert()
        stage_sprite.image.fill((10, 20, 30))
        stage_sprite.rect = pg.Rect(0, 0, 40, 40)
        stage_sprite.dirty = 1

        render = Render(SimpleNamespace(
            group=group,
            stage=SimpleNamespace(sprite=stage_sprite),
            monitors=[],
        ))
        screen = pg.display.set_mode((40, 40))
        display = SimpleNamespace(
            size=(40, 40),
            rect=pg.Rect(0, 0, 40, 40),
            screen=screen,
        )
        Pen.image = pg.Surface(display.rect.size, pg.SRCALPHA)
        Pen.image.fill((0, 0, 0, 0))

        render.draw(display)

        self.assertEqual(screen.get_at((0, 0)), pg.Color(10, 20, 30, 255))
        self.assertEqual(screen.get_at((12, 12)), pg.Color(255, 0, 0, 255))

    def test_ghost_100_is_not_rendered_but_remains_shown(self):
        target = Target.__new__(Target)
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.visible = True
        target._shown = True
        target.costume = SimpleNamespace(effects={"ghost": 100.0})

        Target._update_effective_visibility(target)

        self.assertTrue(target.shown)
        self.assertFalse(target.sprite.visible)
        self.assertEqual(target.sprite.dirty, 1)

        target.costume.effects["ghost"] = 90.0
        Target._update_effective_visibility(target)

        self.assertTrue(target.shown)
        self.assertTrue(target.sprite.visible)

    def test_transparent_border_trim_preserves_center_offset(self):
        image = pg.Surface((10, 10), pg.SRCALPHA)
        image.fill((0, 0, 0, 0))
        image.fill((255, 0, 0, 255), pg.Rect(3, 4, 2, 2))
        asset = {
            "name": "costume1",
            "image": image.convert_alpha(),
            "center": (5, 5),
            "scale": 1,
        }

        crop_offset = Costumes._trim_transparent_border(asset)

        self.assertEqual(asset["image"].get_size(), (2, 2))
        self.assertEqual(crop_offset, pg.math.Vector2(3, 4))

        center = pg.math.Vector2(asset["image"].get_size()) / 2
        offset = (pg.math.Vector2(asset["center"]) - crop_offset) * -1
        offset += center

        self.assertEqual(offset, pg.math.Vector2(-1, 0))


if __name__ == "__main__":
    unittest.main()
