"""
target.py

Contains the Target class

TODO Position clamping
TODO Random/mouse pos for glide/goto
TODO Warp deorator?
"""


__all__ = ['Target', 'warp']

import asyncio
import logging
import math
import random
import time
import types
from functools import wraps
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, Optional, Tuple, Union
from typing import List as PyList

import pygame as pg
from pygame.sprite import DirtySprite

from .. import config
from .costumes import Costumes
from .lists import List
from .pen import Pen
from .sounds import Sounds

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..util import Util


class Target:
    """Holds common code for targets

    Attributes:
    [should be set by the child class]

        variables: A dict of variables and their default values

        lists: A dict of lists and their default values

        costumes: A list of costume dicts

        sounds: A list of sound dicts

        costume: The intial costume #. Will be changed into a
            dict from costumes by Target.__init__

        hats: A dict of aync functions which should be started upon
            certain events. Must be initialized in __init__

    [managed by this class, Target]
        sprite: A pygame sprite drawn to the screen

        dirty: Indicates the sprite's rect is dirty

        warp: Marks the Target as running "without screen refresh"

        warp_timer: Keeps track of time to ensure the target doesn't
            run longer than WARP_TIME

    Class Attributes:
        need_redraw: Used to determine if any targets need to be
            redrawn

    TODO Missing Target properties:
        draggable = False
        tempo = 60
        videoTransparency = 50
        videoState
        textToSpeechLanguage
    """

    # Clones for all sprites
    _clones: PyList['Target'] = []

    # Type hints
    pen: Pen
    costume: Costumes
    sounds: Sounds
    sprite: DirtySprite
    dirty: bool
    warp: 'Warp'
    is_clone: bool
    _events: Dict[str, PyList[Callable]]
    _tasks: Dict[str, PyList[Any]]
    _xpos: float
    _ypos: float
    _direction: float

    def __init_subclass__(cls):
        # Initialize the _bound_events dict
        cls._bound_events: Dict[str, str] = {}
        for func_name, func in cls.__dict__.items():
            # Check if the function has an event attriute
            event = getattr(func, 'event', None)

            # If it does, save the function name and event name
            if event is not None:
                cls._bound_events[func_name] = event

        # Create the clones list
        cls.clones: PyList['Target'] = []

    def __init__(self, parent: Optional['Target'] = None):
        # Initialize the events dict
        self._events = {}
        for name, event in self._bound_events.items():
            self._events.setdefault(event, []).append(
                getattr(self, name))

        # Create the task dict
        self._tasks = {}

        # Used to determine if this is a clone
        self.is_clone = parent is not None

        # Create the pygame sprite
        self.sprite = DirtySprite()
        setattr(self.sprite, 'target', self)
        self._shown = True

        # Set dirty
        self.dirty = True

        self.warp = Warp(self)

        # Initialize clone data
        if parent is not None:
            # Copy variables from parent
            for name, var in parent.__dict__.items():
                if name.startswith('var'):
                    self.__dict__[name] = var
                elif isinstance(var, List):
                    self.__dict__[name] = var.copy()

            # Copy attributes
            self._xpos = parent._xpos
            self._ypos = parent._ypos
            self._direction = parent._direction
            self._shown = parent._shown
            self.sprite.visible = parent.sprite.visible
            self.pen = parent.pen.copy(self)

            self.costume = parent.costume.copy()
            self.sounds = parent.sounds.copy()

    @property
    def xpos(self) -> float:
        """Current x coordinate on the stage"""
        return self._xpos

    @xpos.setter
    def xpos(self, xpos: float):
        self._xpos = max(-9e4, min(9e4, xpos))

        # Set dirty, move pen
        self.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True
        self.pen.move(self._xpos, self._ypos)

    @property
    def ypos(self) -> float:
        """Current y coordinate on the stage"""
        return self._ypos

    @ypos.setter
    def ypos(self, ypos: float):
        self._ypos = max(-9e4, min(9e4, ypos))

        # Set dirty, move pen
        self.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True
        self.pen.move(self._xpos, self._ypos)

    @property
    def direction(self) -> float:
        """Current angle on the stage"""
        return self._direction

    @direction.setter
    def direction(self, degrees: float):
        """Sets and wraps the direction"""
        # Wrap the new direction
        self._direction = degrees - ((degrees + 179) // 360) * 360

        # Set dirty
        self.costume.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True

    def move(self, steps: float):
        """Moves steps in the current direction"""
        radians = math.radians(90 - self._direction)
        self._xpos += steps * math.cos(radians)
        self._ypos += steps * math.sin(radians)

        # Set dirty and move the pen
        self.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True
        self.pen.move(self._xpos, self._ypos)

    def gotoxy(self, xpos: float, ypos: float):
        """Set xpos and ypos simultaneously"""
        self._xpos = xpos
        self._ypos = ypos

        # Set dirty, move pen
        self.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True
        self.pen.move(self._xpos, self._ypos)

    def goto(self, util: 'Util', other: Any):
        """Goto the position of another sprite"""
        target_xy = self._get_target_xy(util, other)
        if target_xy:
            self._xpos = target_xy[0]
            self._ypos = target_xy[1]

        # Set dirty
        self.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True
        self.pen.move(self._xpos, self._ypos)

    def point_towards(self, util: 'Util', other: Any):
        """Point towards another sprite"""
        # Get the position of other
        if other == "_mouse_":
            xpos = float(util.inputs.mouse_x)
            ypos = float(util.inputs.mouse_y)
        else:
            other_target = util.sprites.targets.get(other, self)
            xpos = float(other_target.xpos)
            ypos = float(other_target.ypos)

        # Calculate the angle to point in
        xpos -= self.xpos
        ypos -= self.ypos
        self._direction = 90 - math.degrees(math.atan2(ypos, xpos))

        # Set dirty
        self.costume.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True

    async def glide(self, duration: float, endx: float, endy: float):
        """Glides to a position"""
        start_time = time.monotonic()
        elapsed = 0.0
        startx, starty = self.xpos, self.ypos
        while elapsed < duration:
            elapsed = time.monotonic() - start_time
            frac = elapsed / duration
            self.xpos = startx + frac * (endx - startx)
            self.ypos = starty + frac * (endy - starty)

            # Set dirty, move pen
            self.dirty = True
            if self.sprite.visible:
                Costumes.redraw_requested = True
            self.pen.move(self._xpos, self._ypos)

            await self.yield_()
        self.xpos = endx
        self.ypos = endy

    async def glideto(self, util: 'Util', duration: float, other: Any):
        """Glides to the position of another sprite"""
        target_xy = self._get_target_xy(util, other)
        if target_xy:
            await self.glide(duration, target_xy[0], target_xy[1])

    def _get_target_xy(self, util: 'Util', other: Any) -> Optional[Tuple[float, float]]:
        """Gets the xy coordinates of another sprite."""
        if other == "_mouse_":
            return (float(util.inputs.mouse_x), float(util.inputs.mouse_y))

        if other == "_random_":
            return (
                config.STAGE_SIZE[0] * (random.random() - 0.5),
                config.STAGE_SIZE[1] * (random.random() - 0.5),
            )

        target = util.sprites.targets.get(other)
        if target:
            return (target._xpos, target._ypos)

        return None

    def bounce_on_edge(self):
        """If on edge, bounce. Not implemented."""
        # TODO Bounce on edge

    @property
    def rotation_style(self) -> str:
        """The rotation style of the sprite"""
        return self.costume.rotation_style

    @rotation_style.setter
    def rotation_style(self, style: str):
        if style in ('all around', 'left-right', "don't rotate"):
            self.costume.rotation_style = style

        # Set dirty
        self.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True

    @property
    def size(self) -> float:
        """Current sprite size"""
        return self.costume.size

    @size.setter
    def size(self, value: float):
        self.costume._set_size(value)

        # Set dirty
        self.costume.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True

    def distance_to(self, util: 'Util', other: Any) -> float:
        """Calculate the distance to another target"""
        if other == "_mouse_":
            xpos = float(util.inputs.mouse_x)
            ypos = float(util.inputs.mouse_y)
        else:
            other_target = util.sprites.targets.get(other, self)
            xpos = float(other_target.xpos)
            ypos = float(other_target.ypos)
        return math.sqrt((self.xpos - xpos)**2 + (self.ypos - ypos)**2)

    def distance_to_point(self, point: Tuple[float, float]) -> float:
        """"Calculate the distance to a point (x, y)"""
        return math.sqrt((self.xpos - point[0])**2 + (self.ypos - point[1])**2)

    @property
    def shown(self) -> bool:
        """Whether the sprite is currently visible"""
        return self._shown

    @shown.setter
    def shown(self, value: bool):
        self._shown = bool(value)
        self._update_effective_visibility()

        # Update dirty
        # sprite.dirty is set by the visible property
        Costumes.redraw_requested = True

    def start_event(self, util: 'Util', name: str, restart: bool = True) -> PyList[asyncio.Task]:
        """Starts and returns a list of tasks"""
        tasks: PyList[asyncio.Task] = []
        for cor, task in zip_longest(self._events.get(name, []),
                                     self._tasks.get(name, [])):
            # Either restart the task or skip it
            if task is not None and not task.done():
                if not restart:
                    continue
                task.cancel()

            # TODO Better task restart behavior
            # Threads which are restarted are not rescheduled to be
            # run later. Instead, they are restarted with the same
            # place in line. Implementing this behavior with asyncio
            # may require a custom event loop.

            # Start the task
            if cor is not None:
                tasks.append(asyncio.create_task(cor(util)))

        self._tasks[name] = tasks
        return tasks

    def stop_other(self):
        """Stop scripts other than the current"""
        this_task = asyncio.current_task()
        this_name: Optional[str] = None

        for name in self._tasks:
            for task in self._tasks[name]:
                if task is this_task:
                    this_name = name
                else:
                    task.cancel()
            self._tasks[name] = []
        if this_name is None:
            logger.warning("Failed to find running task for stop other.")
        else:
            self._tasks[this_name] = [this_task] if this_task else []

    def update(self, display: Any, create_mask: bool = False):
        """Clears dirty flags by updating the rect and image"""
        # Update the image and rect, if necessary
        if self.costume.dirty:
            self._update_image(display)
            # Rect updated by _update_image

            self.costume.dirty = False
            self.dirty = False

        # Update the rect, if necessary
        elif self.dirty:
            self._update_rect(display)
            self.dirty = False

        self._update_effective_visibility()

        # Update the sprite mask, if requested
        if create_mask and not self.sprite.mask:
            self.sprite.mask = self.costume.get_mask()

    def _update_effective_visibility(self):
        """Sync render visibility with Scratch's shown state and ghost effect."""
        costume = getattr(self, 'costume', None)
        ghost = costume.effects.get('ghost', 0.0) if costume is not None else 0.0
        visible = self._shown and ghost < 100.0
        if self.sprite.visible != visible:
            self.sprite.visible = visible
            self.sprite.dirty = 1

    def _update_image(self, display: Any):
        """Updates and transforms the sprites image"""
        # Update the image
        image = self.costume.get_image(display, self.direction)
        self.sprite.image = image
        self.sprite.mask = None

        # The rect now needs updating
        self._update_rect(display)

    def _update_rect(self, display: Any):
        """Updates the rect to match the sprite's position and orientation"""
        # Rotate the rect properly
        costume = self.costume
        offset = costume.costume['offset'] * (costume.size / 100)
        offset = offset.rotate(self._direction - 90)

        sw, sh = config.STAGE_SIZE
        self.sprite.rect = self.sprite.image.get_rect(
            center=display.scale * (offset + pg.math.Vector2(
                self._xpos + sw // 2,
                sh // 2 - self._ypos)))

        # Move the rect by the stage offset
        self.sprite.rect.move_ip(*display.rect.topleft)

        self.sprite.dirty = 1

    @staticmethod
    @types.coroutine
    def yield_():
        """Yields for a tick"""
        # Note, this will be overriden by Warp
        yield

    async def sleep(self, delay: float):
        """Yields for at least 1 tick and delay"""
        # Force screen refresh before running again
        Costumes.redraw_requested = True

        # Sleep the correct amount of time
        await asyncio.sleep(delay)

    def get_touching(self, util: 'Util', other: Any) -> bool:
        """Check if this sprite is touching another or its clones"""
        if other == "_mouse_":
            self.update(util.display, True)
            if not self.shown:
                return False

            xpos, ypos = pg.mouse.get_pos()

            offset = self.sprite.rect.topleft
            offset = (xpos - offset[0], ypos - offset[1])
            try:
                return bool(self.sprite.mask.get_at(offset))
            except (IndexError, AttributeError):
                return False

        other_target = util.sprites.targets.get(other)
        if not other_target:
            return False

        # Must update this sprite and the other before testing
        self.update(util.display, True)
        other_target.update(util.display, True)
        if not self.shown:
            return False

        # Check if touching the original
        if (other_target.shown and
                pg.sprite.collide_mask(other_target.sprite, self.sprite)):
            return True

        # Check if touching a clone
        for clone in other_target.clones:
            # Update the clones image too
            clone.update(util.display, True)

            # Check if touching a clone
            if clone.shown and pg.sprite.collide_mask(self.sprite, clone.sprite):
                return True
        return False

    def change_layer(self, util: 'Util', value: int):
        """Moves number layers fowards"""
        group = util.sprites.group
        start = group.get_layer_of_sprite(self.sprite)
        top = group.get_top_layer()
        value = max(0, min(top, start + value)) - start
        self._move_layers(group, start, value)

        # Set dirty
        self.sprite.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True

    def front_layer(self, util: 'Util'):
        """Moves the sprite to the front layer"""
        group = util.sprites.group
        start = group.get_layer_of_sprite(self.sprite)
        top = group.get_top_layer()
        self._move_layers(group, start, top - start)

        # Set dirty
        self.sprite.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True

    def back_layer(self, util: 'Util'):
        """Moves the sprite to the back layer"""
        group = util.sprites.group
        start = group.get_layer_of_sprite(self.sprite)
        self._move_layers(group, start, -start)

        self.sprite.dirty = True
        if self.sprite.visible:
            Costumes.redraw_requested = True

    @staticmethod
    def _move_layers(group: Any, start: int, value: int):
        """Used to switch sprite layers around"""
        sign = int(math.copysign(1, value))
        for i in range(int(abs(value))):
            group.switch_layer(
                start + i * sign,
                start + i * sign + sign
            )

    def create_clone_of(self, util: 'Util', name: str):
        """Create a clone of this target"""
        if len(self._clones) < config.MAX_CLONES:
            # Get the target to clone
            if name == "_myself_":
                target = self
            else:
                target = util.sprites.targets.get(name)
                if target is None:
                    return

            # Get a layer for the clone
            # Move the top sprite where the clone will go,
            # Then move it back to the top leaving an empty space
            group = util.sprites.group
            top = group.get_top_layer()
            bottom = group.get_layer_of_sprite(self.sprite)
            top_sprite = group.get_top_sprite()
            self._move_layers(group, top, bottom - top)
            group.change_layer(top_sprite, top + 1)

            # __class__ is the Sprite's subclass
            clone = target.__class__(target)
            self._clones.append(clone)  # Shared between targets
            target.clones.append(clone)
            group.add(clone.sprite, layer=bottom)
            util.events.send_to(util, clone, "clone_start")
        else:
            logger.warning("Clone limit reached; max clones is %s.", config.MAX_CLONES)

    def delete_clone(self, util: 'Util'):
        """Delete this clone, will not delete original"""
        if self.is_clone:
            self._clones.remove(self)
            self.clones.remove(self)

            # Get rid of this sprite layer
            self.front_layer(util)
            self.sprite.kill()

            # Stop all running scripts
            for tasks in self._tasks.values():
                for task in tasks:
                    task.cancel()

            # Stop all playing sounds
            self.sounds.stop()

            # Stop this task now
            raise asyncio.CancelledError()


def warp(func):
    """Makes a function run with "no screen refresh" enabled"""

    @wraps(func)
    async def wrapper(self: Target, *args):
        with self.warp:
            return await func(self, *args)
    return wrapper


@types.coroutine
def _do_yield():
    """Yields for a tick"""
    yield


async def _no_yield():
    """Does nothing"""


class Warp:
    """Context manager to handle warp for a Target"""

    __slots__ = ('_target', '_warp', 'timer')

    def __init__(self, target):
        self._target = target
        self._warp = 0
        self.timer = time.monotonic()

    def __bool__(self):
        return bool(self._warp)

    def __enter__(self):
        if not self._warp:
            self.timer = time.monotonic()
            self._target.yield_ = self._warp_yield
        self._warp += 1

    def __exit__(self, _, _1, _2):
        self._warp -= 1
        if not self._warp:
            self._target.yield_ = _do_yield

    async def _warp_yield(self):
        """Checks the warp timer before yielding"""
        if time.monotonic() - self.timer > config.WARP_TIME:
            await _do_yield()
            self.timer = time.monotonic()
