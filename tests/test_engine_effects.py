import os
import asyncio
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame as pg

from types import SimpleNamespace

from engine.render import Render
from engine.types.target import Target
from engine.types.costumes import Costumes
from engine.types.pen import Pen
from engine.types.sounds import Sounds


class _Copyable:
    def copy(self, *_):
        return _Copyable()


class _LayerGroup:
    def __init__(self):
        self.added = []

    def get_top_layer(self):
        return 3

    def get_layer_of_sprite(self, _sprite):
        return 1

    def get_top_sprite(self):
        return pg.sprite.DirtySprite()

    def change_layer(self, _sprite, _layer):
        pass

    def switch_layer(self, _layer1, _layer2):
        pass

    def add(self, sprite, layer=0):
        self.added.append((sprite, layer))


class _StageCloneSource(Target):
    pass


class _OtherCloneTarget(Target):
    pass


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

    def test_special_costume_menu_values(self):
        image = pg.Surface((4, 4), pg.SRCALPHA)
        costumes = []
        costume_dict = {}
        for index in range(3):
            asset = {
                "name": f"costume{index + 1}",
                "image": image,
                "center": (2, 2),
                "scale": 1,
                "number": index + 1,
            }
            costumes.append(asset)
            costume_dict[asset["name"]] = asset

        costumes = Costumes(
            0,
            100,
            "don't rotate",
            costumes,
            (costume_dict, {}),
        )

        costumes.switch("previous costume")
        self.assertEqual(costumes.number, 3)

        costumes.switch("next costume")
        self.assertEqual(costumes.number, 1)

        costumes.switch(3)
        self.assertEqual(costumes.number, 3)

        costumes.switch(4)
        self.assertEqual(costumes.number, 1)

        with mock.patch("engine.types.costumes.random.randrange", return_value=1):
            costumes.switch("random costume")
        self.assertEqual(costumes.number, 2)

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

    def test_render_flip_uses_full_frame_flip(self):
        render = Render(SimpleNamespace(
            group=pg.sprite.LayeredDirty(),
            stage=SimpleNamespace(sprite=pg.sprite.DirtySprite()),
            monitors=[],
        ))
        render.rects = [pg.Rect(0, 0, 1, 1)]
        Pen.dirty = [pg.Rect(0, 0, 1, 1)]

        with (
            mock.patch.object(pg.display, "flip") as flip,
            mock.patch.object(pg.display, "update") as update,
        ):
            render.flip()

        flip.assert_called_once_with()
        update.assert_not_called()
        self.assertEqual(render.rects, [])
        self.assertEqual(Pen.dirty, [])

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

    def test_stage_created_clone_is_registered_with_cloned_target(self):
        Target._clones = []
        _StageCloneSource.clones = []
        _OtherCloneTarget.clones = []

        stage = _StageCloneSource.__new__(_StageCloneSource)
        stage.sprite = pg.sprite.DirtySprite()
        stage.sprite.visible = True

        other = _OtherCloneTarget.__new__(_OtherCloneTarget)
        other.sprite = pg.sprite.DirtySprite()
        other.sprite.visible = True
        other._xpos = 1
        other._ypos = 2
        other._direction = 90
        other._shown = True
        other.pen = _Copyable()
        other.costume = _Copyable()
        other.sounds = _Copyable()

        group = _LayerGroup()
        sent_events = []
        util = SimpleNamespace(
            sprites=SimpleNamespace(
                targets={"Other": other},
                group=group,
            ),
            events=SimpleNamespace(
                send_to=lambda _util, target, event: sent_events.append(
                    (target, event)),
            ),
        )

        stage.create_clone_of(util, "Other")

        self.assertEqual(len(_StageCloneSource.clones), 0)
        self.assertEqual(len(_OtherCloneTarget.clones), 1)
        self.assertIs(group.added[0][0].target, _OtherCloneTarget.clones[0])
        self.assertEqual(sent_events, [(_OtherCloneTarget.clones[0], "clone_start")])

    def test_sound_pitch_effect_is_reduced_before_resampling(self):
        sound = mock.Mock()
        sounds = Sounds(100, [sound], {"engine": sound})
        sounds.set_effect("pitch", 100)

        async def play_sound():
            with (
                mock.patch.object(sounds, "_apply_pitch", return_value=sound) as apply_pitch,
                mock.patch.object(pg.mixer, "find_channel", return_value=None),
            ):
                await sounds.play("engine")
            return apply_pitch

        apply_pitch = asyncio.run(play_sound())
        apply_pitch.assert_called_once_with(sound, 65)


if __name__ == "__main__":
    unittest.main()
