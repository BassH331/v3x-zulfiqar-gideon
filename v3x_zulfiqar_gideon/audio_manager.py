import pygame as pg
import os
import math
import random
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass
from enum import IntEnum

class SoundPriority(IntEnum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20

@dataclass
class SoundInstance:
    sound: pg.mixer.Sound
    channel: Optional[pg.mixer.Channel]
    priority: int
    volume: float = 1.0
    loop: bool = False

class AudioManager:
    def __init__(self, max_channels: int = 32):
        """
        Initialize the AudioManager.
        Assumes pg.mixer.pre_init() and pg.init() have been called externally.
        """
        self.max_channels = max_channels
        # Channels are managed by pygame, we just track usage
        self.channels = [pg.mixer.Channel(i) for i in range(max_channels)]
        self.sound_library: Dict[str, pg.mixer.Sound] = {}
        self.master_volume = 1.0
        from .settings import SettingsManager
        settings = SettingsManager()
        self.master_volume = settings.get("master_volume")
        self.music_volume = settings.get("music_volume")
        self.sfx_volume = settings.get("sfx_volume")
        self.current_music_volume_factor = 1.0

        
    def load_sound(self, sound_name: str, file_path: str) -> None:
        """Load a sound file into the sound library."""
        try:
            self.sound_library[sound_name] = pg.mixer.Sound(file_path)
        except Exception as e:
            print(f"Error loading sound {sound_name} from {file_path}: {e}")
    
    def load_sounds_from_directory(self, directory: str) -> None:
        """Load all .wav and .ogg files from a directory."""
        for filename in os.listdir(directory):
            if filename.endswith(('.wav', '.ogg')):
                name = os.path.splitext(filename)[0]
                self.load_sound(name, os.path.join(directory, filename))
    
    def _find_free_channel_id(self) -> Optional[int]:
        """Find the index of a free channel."""
        for i, channel in enumerate(self.channels):
            if not channel.get_busy():
                return i
        return None

    def _steal_channel_id(self, new_priority: int) -> Optional[int]:
        """Find the ID of the least important busy channel to interrupt."""
        # Try to find a free channel first
        free_id = self._find_free_channel_id()
        if free_id is not None:
            return free_id
            
        # If no free channel, and priority is high, steal channel 0 (simplification)
        if new_priority >= SoundPriority.HIGH:
            return 0
            
        return None
    
    def play_sound(self, sound_name: str, 
                  priority: int = SoundPriority.NORMAL,
                  volume: float = 7.0,
                  loop: bool = False,
                  location: Optional[Tuple[float, float]] = None,
                  player_pos: Optional[Tuple[float, float]] = None) -> Optional[int]:
        """
        Play a sound with optional spatial audio.
        """
        if sound_name not in self.sound_library:
            print(f"Sound not found: {sound_name}")
            return None
            
        sound = self.sound_library[sound_name]
        
        # Custom sound volume scaling
        from .settings import SettingsManager
        sound_volumes = SettingsManager().get("sound_volumes") or {}
        custom_vol = sound_volumes.get(sound_name, 1.0)
        
        base_vol = volume
        if base_vol == 7.0:
            base_vol = 1.0
            
        # Spatial Audio Calculation
        final_volume = base_vol * custom_vol * self.sfx_volume * self.master_volume
        if location and player_pos:
            dist = math.hypot(location[0] - player_pos[0], location[1] - player_pos[1])
            max_dist = 500 # pixels
            if dist > max_dist:
                return None # Too far to hear
            # Linear attenuation
            final_volume *= (1.0 - (dist / max_dist))
            
        sound.set_volume(1.0)
        final_volume = max(0.0, min(1.0, final_volume))
        
        # Channel Management
        channel_id = self._find_free_channel_id()
        if channel_id is None:
            channel_id = self._steal_channel_id(priority)
            
        if channel_id is not None:
            channel = self.channels[channel_id]
            channel.set_volume(final_volume)
            if loop:
                channel.play(sound, loops=-1)
            else:
                channel.play(sound)
            return channel_id
            
        return None
    
    def play_music(self, sound_name: str, volume: float = 1.0, loop: bool = True) -> None:
        """
        Play a sound as background music on a dedicated channel (Channel 0).
        Stops any existing music on that channel first to prevent overlap.
        """
        if sound_name not in self.sound_library:
            print(f"Music sound not found: {sound_name}")
            return
            
        music_channel = self.channels[0]
        music_channel.stop() # Ensure no overlap
        
        self.current_music_volume_factor = volume
        sound = self.sound_library[sound_name]
        sound.set_volume(1.0)
        
        music_channel.set_volume(max(0.0, min(1.0, volume * self.music_volume * self.master_volume)))
        
        loops = -1 if loop else 0
        music_channel.play(sound, loops=loops)
        print(f"[AudioManager] Music started: {sound_name}")

    def stop_music(self) -> None:
        """Stop any music playing on the dedicated music channel."""
        self.channels[0].stop()
    
    def stop_sound(self, channel_id: int) -> None:
        """Stop a sound on the specified channel index."""
        if 0 <= channel_id < len(self.channels):
            self.channels[channel_id].stop()
    
    def fadeout_sound(self, channel_id: int, fade_ms: int = 500) -> None:
        """Fade out a sound on the specified channel over the given duration.

        Args:
            channel_id: Index of the channel to fade out.
            fade_ms: Duration of the fade in milliseconds (default 500ms).
        """
        if 0 <= channel_id < len(self.channels):
            self.channels[channel_id].fadeout(fade_ms)
    
    def stop_all_sounds(self) -> None:
        """Stop all currently playing sounds."""
        if not pg.mixer.get_init():
            return
        for channel in self.channels:
            channel.stop()
    
    def set_master_volume(self, volume: float) -> None:
        """Set the master volume (0.0 to 1.0)."""
        self.master_volume = max(0.0, min(1.0, volume))
        from .settings import SettingsManager
        SettingsManager().set("master_volume", self.master_volume)
        # Update current music volume
        self.channels[0].set_volume(max(0.0, min(1.0, self.current_music_volume_factor * self.music_volume * self.master_volume)))

    def set_music_volume(self, volume: float) -> None:
        """Set the music volume (0.0 to 1.0) and update the active music channel."""
        self.music_volume = max(0.0, min(1.0, volume))
        from .settings import SettingsManager
        SettingsManager().set("music_volume", self.music_volume)
        self.channels[0].set_volume(max(0.0, min(1.0, self.current_music_volume_factor * self.music_volume * self.master_volume)))

    def set_sfx_volume(self, volume: float) -> None:
        """Set the SFX volume (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        from .settings import SettingsManager
        SettingsManager().set("sfx_volume", self.sfx_volume)

    def update(self) -> None:
        """Update loop (placeholder for future cross-fading logic)."""
        pass
    
    def __del__(self):
        """Clean up resources."""
        self.stop_all_sounds()
        if pg.mixer.get_init():
            pg.mixer.quit()


class FootstepController:
    """Utility to gate repetitive footstep sounds for characters."""

    def __init__(
        self,
        audio_manager: "AudioManager",
        sound_name: str,
        interval_ms: int = 900,
        volume: float = 0.6,
    ) -> None:
        self.audio_manager = audio_manager
        self.sound_name = sound_name
        self.interval_ms = max(300, interval_ms)
        self._volume = max(0.0, min(1.0, volume))
        self._last_play_time: Optional[int] = None

    def set_volume(self, volume: float) -> None:
        """Set absolute volume (0.0 - 1.0)."""
        self._volume = max(0.0, min(1.0, volume))

    def increase_volume(self, delta: float) -> None:
        """Adjust volume relatively by delta."""
        self.set_volume(self._volume + delta)

    def set_interval(self, interval_ms: int) -> None:
        """Update cadence interval."""
        self.interval_ms = max(30, interval_ms)

    def reset(self) -> None:
        """Reset timer so the next active step plays immediately."""
        self._last_play_time = None

    def try_play(self, *, active: bool, current_time_ms: int) -> None:
        """Attempt to play the sound if active movement warrants it."""
        if not active:
            self.reset()
            return

        if self._last_play_time is None:
            self._emit(current_time_ms)
            return

        if current_time_ms - self._last_play_time >= self.interval_ms:
            self._emit(current_time_ms)

    def _emit(self, timestamp: int) -> None:
        self.audio_manager.play_sound(self.sound_name, volume=self._volume)
        self._last_play_time = timestamp


class SpotlightSFXManager:
    """
    Manages sound effects tied to specific spotlight sections/scenes.
    Supports instant play, fixed delays, random delays, continuous looping, 
    and randomly repeating sounds (like crackling fire).
    """
    def __init__(self, audio_manager: Optional[AudioManager] = None, schedule: Optional[dict] = None):
        self.audio_manager = audio_manager
        self.current_section = -2
        self.sfx_schedule = schedule if schedule is not None else {}
        self.active_channels: List[int] = []  # Track channels to stop them later
        
        self.section_timer = 0.0
        self.active_trackers: List[SFXTracker] = []

    def update(self, dt_sec: float, section_idx: int):
        if section_idx == -1:
            if self.current_section != -1:
                self.stop_all()
                self.current_section = -1
            return

        # Handle section transition
        if section_idx != self.current_section:
            self.stop_all()  # Stop sounds from the previous section
            self.current_section = section_idx
            self.section_timer = 0.0
            self._init_trackers(section_idx)

        # Update all audio trackers for the active section
        for tracker in self.active_trackers:
            tracker.update(self.section_timer, self.audio_manager, self.active_channels)

        self.section_timer += dt_sec

    def _init_trackers(self, section_idx: int):
        self.active_trackers = []
        sfx_list = self.sfx_schedule.get(section_idx, [])
        for item in sfx_list:
            if isinstance(item, str):
                self.active_trackers.append(SFXTracker({"name": item}))
            elif isinstance(item, dict):
                self.active_trackers.append(SFXTracker(item))

    def stop_all(self, fade_ms: int = 500):
        """Fade out all currently playing spotlight SFX before clearing them."""
        if self.audio_manager:
            for channel_id in self.active_channels:
                self.audio_manager.fadeout_sound(channel_id, fade_ms)
        self.active_channels.clear()


class SFXTracker:
    def __init__(self, config: dict):
        self.name = config.get("name")
        self.volume = config.get("volume", 1.0)
        self.loop = config.get("loop", False)
        self.repeat = config.get("repeat", None)
        
        self.next_play_time = self._resolve_time(config.get("delay", 0.0))
        self.played = False

    def _resolve_time(self, val: Any) -> float:
        """Converts floats to floats, and resolves (min, max) tuples to random floats."""
        if isinstance(val, (tuple, list)):
            if len(val) == 2:
                return float(random.uniform(val[0], val[1]))
            return 0.0
        try:
            return float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    def update(self, current_time: float, audio_manager: Optional[AudioManager], active_channels: list):
        if not self.played and current_time >= self.next_play_time:
            # Play the sound!
            if audio_manager and self.name:
                channel_id = audio_manager.play_sound(self.name, volume=self.volume, loop=self.loop)
                if channel_id is not None:
                    active_channels.append(channel_id)
            
            self.played = True
            
            # If the sound is meant to repeat (but not natively via pygame loops)
            if self.repeat is not None and not self.loop:
                self.next_play_time = current_time + self._resolve_time(self.repeat)
                self.played = False

