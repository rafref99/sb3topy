import os
import asyncio
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame as pg

from types import SimpleNamespace

from engine.render import Render
from engine.events import on_greater
from engine.util import Events
from engine.types.target import Target
from engine.types import costumes as costume_module
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

    def make_gradient_costumes(self):
        image = pg.Surface((32, 32), pg.SRCALPHA)
        for x in range(32):
            for y in range(32):
                image.set_at((x, y), (x * 7 % 256, y * 5 % 256, (x + y) * 4 % 256, 255))

        asset = {
            "name": "gradient",
            "image": image,
            "center": (16, 16),
            "scale": 1,
            "number": 1,
        }
        return Costumes(
            0,
            100,
            "don't rotate",
            [asset],
            ({"gradient": asset}, {}),
        )

    def test_render_uses_stage_sprite_rect(self):
        stage_sprite = pg.sprite.DirtySprite()
        stage_sprite.image = pg.Surface((6, 6), pg.SRCALPHA)
        stage_sprite.image.fill((200, 10, 20, 255))
        stage_sprite.rect = pg.Rect(10, 12, 6, 6)
        stage_sprite.dirty = 1

        sprites = SimpleNamespace(
            group=pg.sprite.LayeredDirty(),
            stage=SimpleNamespace(sprite=stage_sprite),
            monitors=[],
        )
        display = SimpleNamespace(
            screen=pg.Surface((24, 24), pg.SRCALPHA),
            rect=pg.Rect(0, 0, 24, 24),
        )

        Render(sprites).draw(display)

        self.assertEqual(display.screen.get_at((0, 0)), pg.Color(255, 255, 255, 255))
        self.assertEqual(display.screen.get_at((10, 12)), pg.Color(200, 10, 20, 255))

    def test_render_uses_transparent_stage_rgb_as_base_color(self):
        stage_sprite = pg.sprite.DirtySprite()
        stage_sprite.image = pg.Surface((6, 6), pg.SRCALPHA)
        stage_sprite.image.fill((52, 52, 52, 0))
        stage_sprite.rect = pg.Rect(0, 0, 6, 6)
        stage_sprite.dirty = 1

        sprites = SimpleNamespace(
            group=pg.sprite.LayeredDirty(),
            stage=SimpleNamespace(sprite=stage_sprite),
            monitors=[],
        )
        display = SimpleNamespace(
            screen=pg.Surface((12, 12), pg.SRCALPHA),
            rect=pg.Rect(0, 0, 12, 12),
        )

        Render(sprites).draw(display)

        self.assertEqual(display.screen.get_at((0, 0)), pg.Color(52, 52, 52, 255))

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

    def test_target_size_uses_costume_property_setter(self):
        image = pg.Surface((100, 100), pg.SRCALPHA)
        image.fill((100, 120, 140, 255))
        asset = {
            "name": "costume1",
            "image": image,
            "center": (50, 50),
            "scale": 1,
            "number": 1,
        }
        target = Target.__new__(Target)
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.visible = True
        target.costume = Costumes(0, 100, "don't rotate", [asset], ({"costume1": asset}, {}))

        target.size = 50

        self.assertEqual(target.costume.size, 50)
        self.assertTrue(target.costume.dirty)

    def test_zero_duration_glide_moves_without_dividing(self):
        target = Target.__new__(Target)
        target._xpos = 0
        target._ypos = 0
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.visible = True
        target.pen = mock.Mock()

        asyncio.run(target.glide(0, 12, -8))

        self.assertEqual((target.xpos, target.ypos), (12, -8))
        target.pen.move.assert_called_with(12, -8)

    def test_costume_transform_cache_reuses_scaled_surface(self):
        costumes = self.make_costumes()
        display = SimpleNamespace(scale=1)
        Costumes._transform_cache.clear()

        with mock.patch.object(pg.transform, "smoothscale", wraps=pg.transform.smoothscale) as smoothscale:
            first = costumes.get_image(display, 90)
            second = costumes.get_image(display, 90)

        self.assertIs(first, second)
        smoothscale.assert_called_once()

    def test_costume_transform_cache_includes_effects(self):
        costumes = self.make_costumes()
        display = SimpleNamespace(scale=1)
        Costumes._transform_cache.clear()

        plain = costumes.get_image(display, 90)
        costumes.set_effect("ghost", 50)
        ghosted = costumes.get_image(display, 90)

        self.assertIsNot(plain, ghosted)
        self.assertLess(ghosted.get_at((0, 0)).a, plain.get_at((0, 0)).a)

    @unittest.skipIf(costume_module.np is None, "numpy is required for fisheye")
    def test_fisheye_effect_remaps_pixels_and_preserves_alpha(self):
        costumes = self.make_gradient_costumes()
        display = SimpleNamespace(scale=1)
        Costumes._transform_cache.clear()

        plain = costumes.get_image(display, 90)
        costumes.set_effect("fisheye", 80)
        fisheye = costumes.get_image(display, 90)

        self.assertEqual(fisheye.get_size(), plain.get_size())
        self.assertNotEqual(pg.image.tostring(fisheye, "RGBA"),
                            pg.image.tostring(plain, "RGBA"))
        self.assertEqual(fisheye.get_at((16, 16)).a, 255)

    @unittest.skipIf(costume_module.np is None, "numpy is required for whirl")
    def test_whirl_effect_remaps_pixels_and_preserves_alpha(self):
        costumes = self.make_gradient_costumes()
        display = SimpleNamespace(scale=1)
        Costumes._transform_cache.clear()

        plain = costumes.get_image(display, 90)
        costumes.set_effect("whirl", 120)
        whirl = costumes.get_image(display, 90)

        self.assertEqual(whirl.get_size(), plain.get_size())
        self.assertNotEqual(pg.image.tostring(whirl, "RGBA"),
                            pg.image.tostring(plain, "RGBA"))
        self.assertEqual(whirl.get_at((16, 16)).a, 255)

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

    def test_render_flip_updates_dirty_rects(self):
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

        flip.assert_not_called()
        update.assert_called_once_with([pg.Rect(0, 0, 1, 1)])
        self.assertEqual(render.rects, [])
        self.assertEqual(Pen.dirty, [])

    def test_render_flip_skips_display_update_without_dirty_rects(self):
        render = Render(SimpleNamespace(
            group=pg.sprite.LayeredDirty(),
            stage=SimpleNamespace(sprite=pg.sprite.DirtySprite()),
            monitors=[],
        ))

        with (
            mock.patch.object(pg.display, "flip") as flip,
            mock.patch.object(pg.display, "update") as update,
        ):
            render.flip()

        flip.assert_not_called()
        update.assert_not_called()

    def test_dirty_render_redraws_previous_and_current_sprite_rects(self):
        stage_sprite = pg.sprite.DirtySprite()
        stage_sprite.image = pg.Surface((40, 40)).convert()
        stage_sprite.image.fill((10, 20, 30))
        stage_sprite.rect = pg.Rect(0, 0, 40, 40)
        stage_sprite.dirty = 1

        sprite = pg.sprite.DirtySprite()
        sprite.image = pg.Surface((10, 10), pg.SRCALPHA)
        sprite.image.fill((255, 0, 0, 255))
        sprite.rect = pg.Rect(0, 0, 10, 10)
        sprite.visible = True
        sprite.source_rect = None
        sprite.blendmode = 0
        group = pg.sprite.LayeredDirty(sprite)

        screen = pg.display.set_mode((40, 40))
        display = SimpleNamespace(
            screen=screen,
            rect=pg.Rect(0, 0, 40, 40),
        )
        render = Render(SimpleNamespace(
            group=group,
            stage=SimpleNamespace(sprite=stage_sprite),
            monitors=[],
        ))

        render.draw(display)
        render.flip()

        sprite.rect = pg.Rect(20, 0, 10, 10)
        sprite.dirty = 1
        render.draw(display)

        self.assertEqual(screen.get_at((1, 1)), pg.Color(10, 20, 30, 255))
        self.assertEqual(screen.get_at((21, 1)), pg.Color(255, 0, 0, 255))
        self.assertEqual(render.rects, [pg.Rect(0, 0, 30, 10)])

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

    def test_touching_ignores_hidden_targets_but_keeps_ghosted_targets(self):
        target = Target.__new__(Target)
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.rect = pg.Rect(0, 0, 10, 10)
        target.sprite.mask = pg.mask.Mask((10, 10), True)
        target.sprite.visible = False
        target._shown = True
        target.update = lambda _display, _create_mask=False: None

        other = Target.__new__(Target)
        other.sprite = pg.sprite.DirtySprite()
        other.sprite.rect = pg.Rect(0, 0, 10, 10)
        other.sprite.mask = pg.mask.Mask((10, 10), True)
        other.sprite.visible = False
        other._shown = False
        other.clones = []
        other.update = lambda _display, _create_mask=False: None

        util = SimpleNamespace(
            display=SimpleNamespace(),
            sprites=SimpleNamespace(targets={"Other": other}),
        )

        self.assertFalse(target.get_touching(util, "Other"))

        other._shown = True
        self.assertTrue(target.get_touching(util, "Other"))

    def test_color_touching_color_detects_overlapping_sprite_pixels(self):
        target = Target.__new__(Target)
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.image = pg.Surface((4, 4), pg.SRCALPHA)
        target.sprite.image.fill((255, 0, 0, 255))
        target.sprite.rect = pg.Rect(4, 4, 4, 4)
        target.sprite.visible = True
        target._shown = True
        target.update = lambda _display, _create_mask=False: None

        other_sprite = pg.sprite.DirtySprite()
        other_sprite.image = pg.Surface((4, 4), pg.SRCALPHA)
        other_sprite.image.fill((0, 255, 0, 255))
        other_sprite.rect = pg.Rect(4, 4, 4, 4)
        other_sprite.visible = True
        other_sprite.source_rect = None

        stage_sprite = pg.sprite.DirtySprite()
        stage_sprite.image = pg.Surface((12, 12), pg.SRCALPHA)
        stage_sprite.image.fill((255, 255, 255, 255))
        stage_sprite.rect = pg.Rect(0, 0, 12, 12)

        util = SimpleNamespace(
            display=SimpleNamespace(rect=pg.Rect(0, 0, 12, 12)),
            sprites=SimpleNamespace(
                group=pg.sprite.LayeredDirty(target.sprite, other_sprite),
                stage=SimpleNamespace(sprite=stage_sprite),
            ),
        )

        self.assertTrue(target.get_color_touching_color(util, "#ff0000", "#00ff00"))
        self.assertFalse(target.get_color_touching_color(util, "#0000ff", "#00ff00"))

    def test_touching_color_detects_stage_pixel_under_sprite(self):
        target = Target.__new__(Target)
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.image = pg.Surface((2, 2), pg.SRCALPHA)
        target.sprite.image.fill((255, 0, 0, 255))
        target.sprite.rect = pg.Rect(1, 1, 2, 2)
        target.sprite.visible = True
        target._shown = True
        target.update = lambda _display, _create_mask=False: None

        stage_sprite = pg.sprite.DirtySprite()
        stage_sprite.image = pg.Surface((4, 4), pg.SRCALPHA)
        stage_sprite.image.fill((0, 0, 255, 255))
        stage_sprite.rect = pg.Rect(0, 0, 4, 4)

        util = SimpleNamespace(
            display=SimpleNamespace(rect=pg.Rect(0, 0, 4, 4)),
            sprites=SimpleNamespace(
                group=pg.sprite.LayeredDirty(target.sprite),
                stage=SimpleNamespace(sprite=stage_sprite),
            ),
        )

        self.assertTrue(target.get_touching_color(util, "#0000ff"))
        self.assertFalse(target.get_touching_color(util, "#00ff00"))

    def test_on_greater_awaits_async_handler_once_per_threshold_crossing(self):
        calls = []

        class TimerUtil:
            def __init__(self):
                self.values = [0, 2, 3, 0, 4]
                self.index = 0

            def timer(self):
                value = self.values[self.index]
                self.index = min(self.index + 1, len(self.values) - 1)
                return value

        class ScriptTarget:
            @staticmethod
            async def yield_():
                await asyncio.sleep(0)

            @on_greater("timer", 1)
            async def script(self, util):
                calls.append(util.timer())

        async def run_script():
            task = asyncio.create_task(ScriptTarget().script(TimerUtil()))
            for _ in range(6):
                await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        asyncio.run(run_script())

        self.assertEqual(calls, [3, 4])

    def test_bounce_on_edge_reflects_and_repositions(self):
        image = pg.Surface((20, 20), pg.SRCALPHA)
        image.fill((255, 0, 0, 255))
        asset = {
            "name": "costume1",
            "image": image,
            "center": (10, 10),
            "scale": 1,
            "offset": pg.math.Vector2(0, 0),
            "number": 1,
        }
        target = Target.__new__(Target)
        target._xpos = 238
        target._ypos = 0
        target._direction = 90
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.visible = True
        target.pen = mock.Mock()
        target.costume = Costumes(0, 100, "don't rotate", [asset], ({"costume1": asset}, {}))

        target.bounce_on_edge()

        self.assertEqual(round(target.direction), -90)
        self.assertEqual(target.xpos, 230)
        target.pen.move.assert_called_with(230, 0)

    def test_bounce_on_edge_does_nothing_inside_stage(self):
        image = pg.Surface((20, 20), pg.SRCALPHA)
        asset = {
            "name": "costume1",
            "image": image,
            "center": (10, 10),
            "scale": 1,
            "offset": pg.math.Vector2(0, 0),
            "number": 1,
        }
        target = Target.__new__(Target)
        target._xpos = 0
        target._ypos = 0
        target._direction = 45
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.visible = True
        target.pen = mock.Mock()
        target.costume = Costumes(0, 100, "don't rotate", [asset], ({"costume1": asset}, {}))

        target.bounce_on_edge()

        self.assertEqual(target.direction, 45)
        target.pen.move.assert_not_called()

    def test_point_towards_wraps_direction_through_setter(self):
        image = pg.Surface((20, 20), pg.SRCALPHA)
        asset = {
            "name": "costume1",
            "image": image,
            "center": (10, 10),
            "scale": 1,
            "offset": pg.math.Vector2(0, 0),
            "number": 1,
        }
        target = Target.__new__(Target)
        target._xpos = 0
        target._ypos = 0
        target._direction = 90
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.visible = True
        target.pen = mock.Mock()
        target.costume = Costumes(0, 100, "don't rotate", [asset], ({"costume1": asset}, {}))
        other = SimpleNamespace(xpos=-10, ypos=-10)
        util = SimpleNamespace(sprites=SimpleNamespace(targets={"Other": other}))

        target.point_towards(util, "Other")

        self.assertEqual(round(target.direction), -135)

    def test_distance_and_point_towards_use_case_insensitive_sprite_lookup(self):
        target = Target.__new__(Target)
        target._xpos = 0
        target._ypos = 0
        target._direction = 90
        target.sprite = pg.sprite.DirtySprite()
        target.sprite.visible = True
        target.pen = mock.Mock()
        target.costume = mock.Mock()
        other = SimpleNamespace(xpos=30, ypos=40)
        sprites = SimpleNamespace(
            targets={"Crosshair_locked": other},
            get_target=lambda name, default=None: (
                other if str(name).casefold() == "crosshair_locked" else default
            ),
        )
        util = SimpleNamespace(sprites=sprites)

        self.assertEqual(target.distance_to(util, "crosshair_locked"), 50)
        target.point_towards(util, "crosshair_locked")
        self.assertNotEqual(target.direction, 90)

    def test_target_compatibility_properties_default_and_clamp(self):
        target = _StageCloneSource.__new__(_StageCloneSource)
        _StageCloneSource.__init__(target)

        self.assertFalse(target.draggable)
        self.assertEqual(target.tempo, 60)
        self.assertEqual(target.videoState, "off")
        self.assertEqual(target.videoTransparency, 50)
        self.assertIsNone(target.textToSpeechLanguage)

        target.videoState = "on-flipped"
        target.videoTransparency = 150
        target.textToSpeechLanguage = "de"

        self.assertEqual(target.videoState, "on-flipped")
        self.assertEqual(target.videoTransparency, 100)
        self.assertEqual(target.textToSpeechLanguage, "de")

        target.videoTransparency = -20
        target.videoState = "invalid"
        target.textToSpeechLanguage = ""

        self.assertEqual(target.videoTransparency, 0)
        self.assertEqual(target.videoState, "on-flipped")
        self.assertIsNone(target.textToSpeechLanguage)

    def test_clone_copies_target_compatibility_properties(self):
        parent = Target.__new__(Target)
        parent._xpos = 1
        parent._ypos = 2
        parent._direction = 90
        parent._shown = True
        parent.sprite = pg.sprite.DirtySprite()
        parent.sprite.visible = True
        parent.pen = _Copyable()
        parent.costume = _Copyable()
        parent.sounds = _Copyable()
        parent.draggable = True
        parent.tempo = 120
        parent.video_state = "on"
        parent.video_transparency = 35
        parent.text_to_speech_language = "fr"

        clone = _StageCloneSource(parent)

        self.assertTrue(clone.draggable)
        self.assertEqual(clone.tempo, 120)
        self.assertEqual(clone.videoState, "on")
        self.assertEqual(clone.videoTransparency, 35)
        self.assertEqual(clone.textToSpeechLanguage, "fr")

    def test_events_parent_task_is_removed_after_completion(self):
        events = Events()
        util = SimpleNamespace()

        async def script(_util):
            await asyncio.sleep(0)

        target = SimpleNamespace(
            start_event=lambda _util, _event, _restart: [asyncio.create_task(script(_util))])
        sprites = SimpleNamespace(
            sprites=lambda: [],
            stage=target,
        )

        async def run_event():
            await events.send_wait(util, sprites, "green_flag", True)

        asyncio.run(run_event())

        self.assertEqual(events.events, {})

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
