"""
Core engine wrapper for V3X ZULFIQAR-GIDEON.
Centralizes the game loop, state management, event handling, and resolution independence.
"""

from __future__ import annotations
import sys
from sys import exit
from typing import Type, Optional, Any, Tuple
import pygame as pg

from .state_machine import StateManager, State
from .audio_manager import AudioManager
from .router import V3XManifest, Router
from .ui import UITheme


class V3XCore:
    """The central engine class that manages the application lifecycle and virtual canvas."""

    def __init__(
        self,
        width: int = 0,
        height: int = 0,
        title: str = "V3X Engine",
        base_width: int = 1280,
        base_height: int = 720,
    ) -> None:
        """
        Initialize the engine, display, and sovereign virtual canvas.
        """
        # Enable Per-Monitor DPI awareness on Windows to prevent blurry OS scaling
        if sys.platform == "win32":
            try:
                import ctypes
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                except Exception:
                    ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        # Pre-initialize mixer
        pg.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
        pg.init()
        pg.mixer.set_num_channels(32)

        self.base_width = base_width
        self.base_height = base_height
        self.title = title

        # Determine initial window resolution
        if width == 0 or height == 0:
            info = pg.display.Info()
            screen_w, screen_h = info.current_w, info.current_h
            # Fit inside user monitor maintaining aspect ratio with margin
            scale_factor = min(screen_w / base_width, screen_h / base_height) * 0.95
            self.width = max(base_width, int(base_width * scale_factor))
            self.height = max(base_height, int(base_height * scale_factor))
        else:
            self.width, self.height = width, height

        self.window = pg.display.set_mode((self.width, self.height), pg.RESIZABLE)
        self.screen = self.window  # For backward compatibility
        pg.display.set_caption(title)

        # Sovereign Virtual Canvas (Fixed Internal Resolution)
        self.virtual_surface = pg.Surface((self.base_width, self.base_height))

        # Intercept display.get_surface so all game systems perceive the exact base resolution
        pg.display.get_surface = lambda: self.virtual_surface

        # Viewport metrics for letterbox/pillarbox scaling
        self._viewport_scale = 1.0
        self._viewport_dest_x = 0
        self._viewport_dest_y = 0
        self._viewport_dest_rect = pg.Rect(0, 0, self.width, self.height)
        self._recompute_viewport()

        # Intercept mouse coordinates
        self._orig_mouse_get_pos = pg.mouse.get_pos
        pg.mouse.get_pos = self._get_virtual_mouse_pos

        self.clock = pg.time.Clock()
        from .settings import SettingsManager
        self.settings = SettingsManager()
        self.audio_manager = AudioManager()
        self.state_manager = StateManager(audio_manager=self.audio_manager)
        self.is_running = True
        self.is_fullscreen = False
        self._saved_window_size = (self.width, self.height)

    def _recompute_viewport(self) -> None:
        """Compute the letterbox/pillarbox destination rect for scaling the virtual surface."""
        win_w, win_h = self.window.get_size()
        scale = min(win_w / self.base_width, win_h / self.base_height)
        self._viewport_scale = max(0.001, scale)
        dest_w = max(1, int(self.base_width * self._viewport_scale))
        dest_h = max(1, int(self.base_height * self._viewport_scale))
        self._viewport_dest_x = (win_w - dest_w) // 2
        self._viewport_dest_y = (win_h - dest_h) // 2
        self._viewport_dest_rect = pg.Rect(self._viewport_dest_x, self._viewport_dest_y, dest_w, dest_h)

    def _get_virtual_mouse_pos(self) -> Tuple[int, int]:
        """Convert real window mouse coordinates to virtual canvas coordinates."""
        mx, my = self._orig_mouse_get_pos()
        if self._viewport_scale <= 0:
            return (0, 0)
        vx = int((mx - self._viewport_dest_x) / self._viewport_scale)
        vy = int((my - self._viewport_dest_y) / self._viewport_scale)
        return (max(0, min(self.base_width - 1, vx)), max(0, min(self.base_height - 1, vy)))

    def toggle_fullscreen(self) -> None:
        """Toggles fullscreen mode while preserving aspect ratio."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self._saved_window_size = self.window.get_size()
            self.window = pg.display.set_mode((0, 0), pg.FULLSCREEN)
        else:
            self.window = pg.display.set_mode(self._saved_window_size, pg.RESIZABLE)
        self.screen = self.window
        self._recompute_viewport()

    def launch(self, manifest: V3XManifest) -> None:
        """Launch the engine using a project manifest."""
        # 0. Sync base dimensions from manifest if specified
        if manifest.base_width and manifest.base_height:
            if manifest.base_width != self.base_width or manifest.base_height != self.base_height:
                self.base_width = manifest.base_width
                self.base_height = manifest.base_height
                self.virtual_surface = pg.Surface((self.base_width, self.base_height))
                self._recompute_viewport()
        if manifest.title:
            self.title = manifest.title
            pg.display.set_caption(self.title)

        # 1. Apply UI Theme
        if manifest.theme:
            if "buttons" in manifest.theme: UITheme.configure_buttons(**manifest.theme["buttons"])
            if "notifications" in manifest.theme: UITheme.configure_notifications(**manifest.theme["notifications"])
            if "overlays" in manifest.theme: UITheme.configure_overlays(**manifest.theme["overlays"])

        # 2. Register Audio
        import os
        master_cfg_path = "game_data/master_audio_config.json"
        if os.path.exists(master_cfg_path):
            self.audio_manager.load_audio_config(master_cfg_path)

        for name, path in manifest.audio.items():
            self.audio_manager.load_sound_safe(name, path)

        # 3. Setup Router
        if manifest.routes:
            router = Router(manifest.routes)
            self.state_manager.set_router(router)

        # 4. Start Loop
        if not manifest.initial_state:
            raise ValueError("V3XManifest must specify an initial_state class.")

        self.run(manifest.initial_state)

    def run(self, initial_state_class: Type[State], **kwargs: Any) -> None:
        """Start the main game loop with an initial state."""
        initial_state = initial_state_class(self.state_manager, **kwargs)
        self.state_manager.push(initial_state)

        dt_target = 1000.0 / 60.0  # 60Hz target physics update rate (~16.67 ms)
        accumulator = 0.0

        while self.is_running:
            # Tick the clock to get elapsed time. Cap rendering loop using configured FPS cap.
            fps_cap = self.settings.get("fps_cap") or 60
            elapsed = self.clock.tick(fps_cap)

            # Prevent "spiral of death" during lag spikes or window focus transitions
            if elapsed > 100.0:
                elapsed = 100.0

            accumulator += elapsed

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                elif event.type == pg.VIDEORESIZE:
                    self.window = pg.display.set_mode((event.w, event.h), pg.RESIZABLE)
                    self.screen = self.window
                    self._recompute_viewport()
                    continue
                elif event.type == pg.KEYDOWN:
                    # F11 or Alt+Enter toggles fullscreen
                    if event.key == pg.K_F11 or (event.key == pg.K_RETURN and (pg.key.get_mods() & pg.KMOD_ALT)):
                        self.toggle_fullscreen()
                        continue

                # Remap mouse event coordinates from window space to virtual canvas space
                if hasattr(event, "pos"):
                    mx, my = event.pos
                    if self._viewport_scale > 0:
                        vx = int((mx - self._viewport_dest_x) / self._viewport_scale)
                        vy = int((my - self._viewport_dest_y) / self._viewport_scale)
                        event.pos = (max(0, min(self.base_width - 1, vx)), max(0, min(self.base_height - 1, vy)))
                if hasattr(event, "rel"):
                    rx, ry = event.rel
                    if self._viewport_scale > 0:
                        event.rel = (int(rx / self._viewport_scale), int(ry / self._viewport_scale))

                self.state_manager.handle_event(event)

            # Consume accumulator in fixed physics steps
            while accumulator >= dt_target:
                self.state_manager.update(dt_target)
                accumulator -= dt_target

            self.audio_manager.update()

            # 1. State draws to sovereign virtual surface
            self.state_manager.draw(self.virtual_surface)

            # 2. Presentation: Scale virtual surface to window with letterbox/pillarbox
            dest_rect = self._viewport_dest_rect
            if dest_rect.size == (self.base_width, self.base_height):
                scaled_view = self.virtual_surface
            else:
                scaled_view = pg.transform.smoothscale(self.virtual_surface, dest_rect.size)

            self.window.fill((0, 0, 0))
            self.window.blit(scaled_view, dest_rect.topleft)
            pg.display.flip()

    def quit(self) -> None:
        self.is_running = False
        pg.quit()
        exit()
