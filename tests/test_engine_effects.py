import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame as pg

from engine.types.costumes import Costumes


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


if __name__ == "__main__":
    unittest.main()
