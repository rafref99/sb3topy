"""
sounds.py

Contains the Sounds class.

TODO Consider using properties for the Sounds class.
"""

__all__ = ['Sounds']


import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Union

import pygame as pg

try:
    import numpy as np
except ImportError:
    np = None

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from asyncio import Task


class Sounds:
    """
    Handles sounds for a target

    Attributes:
        sounds: A dict referencing sounds (pg.mixer.Sound) by name

        sounds_list: Used to reference sounds by number

        volume: The current volume. If set directly, currently playing
            channels will not update. Use set_volume to update them.

        effects: A dict containing current sound effects

        _channels: A dict with sound channels as keys and waiting tasks
            as values. The channels are kept so the volume can be
            adjusted and the tasks are there to be cancelled.

    Class Attributes
        _cache: A shared dict containing md5ext / Sound pairs

        _all_sounds: Contains all sound tasks ready for cancellation
    """

    _cache: Dict[str, pg.mixer.Sound] = {}
    _pitch_cache: Dict[Tuple[pg.mixer.Sound, float], pg.mixer.Sound] = {}
    _all_sounds: Dict[pg.mixer.Channel, 'Task'] = {}
    _pitch_effect_scale = 0.65

    def __init__(self, volume: float, sounds: List[Dict[str, Any]], copy_dict: Optional[Dict[str, pg.mixer.Sound]] = None):
        if copy_dict is None:
            self.sounds: Dict[str, pg.mixer.Sound] = {}
            self.sounds_list: List[pg.mixer.Sound] = []

            for asset in sounds:
                sound = self._load_sound(asset['path'])
                self.sounds[asset['name']] = sound
                self.sounds_list.append(sound)
        else:
            self.sounds = copy_dict
            # sounds is actually the list here when copying
            self.sounds_list = sounds # type: ignore

        self.volume: float = volume
        self.effects: Dict[str, float] = {}
        self._channels: Dict[pg.mixer.Channel, 'Task'] = {}

    def _load_sound(self, path: str) -> pg.mixer.Sound:
        """Load a sound or retrieve it from cache"""
        sound = self._cache.get(path)
        if not sound:
            sound = pg.mixer.Sound("assets/" + path)
            self._cache[path] = sound
        return sound

    def set_volume(self, volume: float):
        """Sets the volume and updates it for playing sounds"""
        self.volume = max(0.0, min(100.0, volume))
        self._update_volume()

    def change_volume(self, volume: float):
        """Changes and updates the volume by an amount"""
        self.set_volume(self.volume + volume)

    def _update_volume(self):
        """Updates the volume for every channel"""
        lvol, rvol = self._get_volume()
        for channel in self._channels:
            channel.set_volume(lvol, rvol)

    def _get_volume(self) -> Tuple[float, float]:
        """Gets the left and right volume levels"""
        pan = self.effects.get("pan", 0.0)
        return (max(0.0, min(100.0, self.volume - pan)) / 100.0,
                max(0.0, min(100.0, self.volume + pan)) / 100.0)

    def play(self, name: Union[str, float]) -> 'Task':
        """Plays the sound and returns an awaitable."""
        # Get the sound from name or number
        sound: Optional[pg.mixer.Sound] = self.sounds.get(str(name))
        if not sound:
            try:
                index = round(float(name)) - 1
                if 0 <= index < len(self.sounds_list):
                    sound = self.sounds_list[index]
                elif self.sounds_list:
                    sound = self.sounds_list[0]
            except (ValueError, TypeError, OverflowError):
                pass

        # Play the sound
        if sound:
            # Apply pitch effect if necessary
            pitch = self.effects.get('pitch', 0.0)
            if pitch != 0.0:
                sound = self._apply_pitch(
                    sound, pitch * self._pitch_effect_scale)

            # Stop the sound if it is already playing
            for channel, task in list(self._channels.items()):
                if channel.get_sound() == sound:
                    channel.stop()
                    task.cancel()

            # Try to play it on an open channel
            channel = pg.mixer.find_channel()
            if channel:
                return asyncio.create_task(
                    self._handle_channel(sound, channel))
        
        # Return a dummy task
        return asyncio.create_task(asyncio.sleep(0))

    def _apply_pitch(self, sound: pg.mixer.Sound, pitch: float) -> pg.mixer.Sound:
        """Applies a pitch effect to a sound by resampling"""
        # Check cache
        cached_sound = self._pitch_cache.get((sound, pitch))
        if cached_sound:
            return cached_sound

        if np is None:
            logger.warning("Sound pitch effect requires numpy; playing original sound.")
            return sound

        # Scratch pitch is in tenths of a semitone, so 120 units is one octave.
        multiplier = 2 ** (pitch / 120)

        # Get sound as array
        try:
            array = pg.sndarray.array(sound)
            if len(array) == 0:
                return sound

            new_len = max(1, int(round(len(array) / multiplier)))
            source_positions = np.arange(new_len, dtype=np.float64) * multiplier
            source_positions = np.clip(source_positions, 0, len(array) - 1)
            indices_low = np.floor(source_positions).astype(np.int64)
            indices_high = np.minimum(indices_low + 1, len(array) - 1)
            weights = source_positions - indices_low

            if array.ndim == 1:
                new_array = (
                    array[indices_low] * (1.0 - weights) +
                    array[indices_high] * weights
                )
            else:
                new_array = (
                    array[indices_low] * (1.0 - weights)[:, None] +
                    array[indices_high] * weights[:, None]
                )
            if np.issubdtype(array.dtype, np.integer):
                type_info = np.iinfo(array.dtype)
                new_array = np.rint(new_array).clip(
                    type_info.min,
                    type_info.max
                )
            new_array = new_array.astype(array.dtype)

            new_sound = pg.sndarray.make_sound(new_array)
            self._pitch_cache[(sound, pitch)] = new_sound
            return new_sound
        except Exception:
            logger.exception("Failed to apply pitch effect")
            return sound

    async def _handle_channel(self, sound: pg.mixer.Sound, channel: pg.mixer.Channel):
        """Saves the channel and waits for it to finish"""
        # Start the sound
        delay = sound.get_length()
        channel.set_volume(*self._get_volume())
        channel.play(sound)

        # Create a cancelable waiting task
        task = asyncio.create_task(asyncio.sleep(delay))
        self._channels[channel] = task
        self._all_sounds[channel] = task

        # Pop the channel once it is done or cancelled
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self._channels.pop(channel, None)
            self._all_sounds.pop(channel, None)

    @classmethod
    def stop_all(cls):
        """Stops all sounds for all sprites"""
        for channel, task in list(cls._all_sounds.items()):
            task.cancel()
            channel.stop()

    def stop(self):
        """Stop all sounds for this sprite"""
        for channel, task in list(self._channels.items()):
            task.cancel()
            channel.stop()

    def copy(self) -> 'Sounds':
        """Returns a copy of this Sounds"""
        return Sounds(self.volume, self.sounds_list, self.sounds) # type: ignore

    def set_effect(self, effect: str, value: float):
        """Set a sound effect"""
        if effect == 'pan':
            self.effects['pan'] = max(-100.0, min(100.0, value))
            self._update_volume()
        elif effect == 'pitch':
            self.effects['pitch'] = value

    def change_effect(self, effect: str, value: float):
        """Change a sound effect"""
        current_value = self.effects.get(effect, 0.0)
        self.set_effect(effect, current_value + value)

    def clear_effects(self):
        """Clear sound effects"""
        self.effects = {}
        self._update_volume()
