"""
Camera — Sovereign, lerp-interpolated 2D camera system for V3X ZULFIQAR-GIDEON.

Features:
- Deadzone tracking: allows free player movement within center bounding box.
- Lookahead lerp interpolation: leads camera smoothly in facing direction.
- Trauma-based screen shake ($T^2$ quadratic decay model by Squirrel Eiserloh).
- Focus zoom interpolation.
- World boundary constraints & coordinate translation.
- EventBus integration: automatically triggers impact shake on DamageDealt events.
"""

from __future__ import annotations

import math
import random
from typing import Optional, Tuple
import pygame as pg

from .event_bus import EventBus, DamageDealt


class Camera:
    """Unified 2D camera with lerp follow, deadzone, focus zoom, and screen shake."""

    def __init__(
        self,
        width: int,
        height: int,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.width = width
        self.height = height

        # Offset & target coordinates
        self.x: float = 0.0
        self.y: float = 0.0
        self.target_x: float = 0.0
        self.target_y: float = 0.0
        self.lerp_speed: float = 8.0

        # Deadzone bounding box
        deadzone_w = int(width * 0.25)
        deadzone_h = int(height * 0.35)
        self.deadzone = pg.Rect(
            (width - deadzone_w) // 2,
            (height - deadzone_h) // 2,
            deadzone_w,
            deadzone_h,
        )

        # World boundary constraints
        self.world_width: Optional[float] = None
        self.world_height: Optional[float] = None

        # Trauma-based Screen Shake ($T^2$ decay model)
        self._trauma: float = 0.0
        self._max_shake_offset: float = 14.0
        self._shake_decay_rate: float = 2.5
        self.shake_offset_x: float = 0.0
        self.shake_offset_y: float = 0.0

        # Zoom interpolation
        self.zoom_level: float = 1.0
        self.target_zoom: float = 1.0
        self.zoom_speed: float = 6.0
        self.focus_x: float = float(width // 2)
        self.focus_y: float = float(height // 2)

        # Render buffer
        self.buffer = pg.Surface((width, height))

        if event_bus is not None:
            self.register_events(event_bus)

    def set_bounds(self, world_width: Optional[float], world_height: Optional[float]) -> None:
        """Set world boundary dimensions to clamp camera panning."""
        self.world_width = world_width
        self.world_height = world_height

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Translate world position to screen viewport coordinates."""
        return (world_x - self.x + self.shake_offset_x, world_y - self.y + self.shake_offset_y)

    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Translate screen viewport coordinates to world position."""
        return (screen_x + self.x - self.shake_offset_x, screen_y + self.y - self.shake_offset_y)

    def register_events(self, event_bus: EventBus) -> None:
        """Subscribe camera to DamageDealt events for automatic impact shake."""
        event_bus.subscribe(DamageDealt, self._on_damage_dealt)

    def _on_damage_dealt(self, event: DamageDealt) -> None:
        """Event handler triggering screen shake on damage impact."""
        intensity = 0.8 if getattr(event, "target_tier", "") in ("boss", "elite") else 0.35
        self.shake(intensity=intensity)

    def shake(self, intensity: float = 0.5) -> None:
        """Add trauma (0.0 to 1.0) to camera shake."""
        self._trauma = min(1.0, self._trauma + intensity)

    def set_zoom(self, target_zoom: float, focus_x: float, focus_y: float) -> None:
        """Set target zoom factor and focal point."""
        self.target_zoom = max(0.5, min(2.5, target_zoom))
        self.focus_x = focus_x
        self.focus_y = focus_y

    def follow(self, target_rect: pg.Rect, dt_seconds: float) -> None:
        """Update camera target relative to player target_rect using deadzone."""
        # Deadzone shift check
        if target_rect.left < self.deadzone.left:
            self.target_x -= (self.deadzone.left - target_rect.left)
        elif target_rect.right > self.deadzone.right:
            self.target_x += (target_rect.right - self.deadzone.right)

        if target_rect.top < self.deadzone.top:
            self.target_y -= (self.deadzone.top - target_rect.top)
        elif target_rect.bottom > self.deadzone.bottom:
            self.target_y += (target_rect.bottom - self.deadzone.bottom)

        # Bounds clamping on target
        if self.world_width is not None:
            max_target_x = max(0.0, self.world_width - self.width)
            self.target_x = max(0.0, min(self.target_x, max_target_x))
        if self.world_height is not None:
            max_target_y = max(0.0, self.world_height - self.height)
            self.target_y = max(0.0, min(self.target_y, max_target_y))

        # Lerp camera position
        diff_x = self.target_x - self.x
        diff_y = self.target_y - self.y
        lerp_factor = min(1.0, dt_seconds * self.lerp_speed)
        self.x += diff_x * lerp_factor
        self.y += diff_y * lerp_factor

    def update(self, dt_seconds: float) -> None:
        """Update trauma decay and zoom interpolation."""
        # 1. Update Trauma & Screen Shake Offset
        if self._trauma > 0.001:
            self._trauma = max(0.0, self._trauma - self._shake_decay_rate * dt_seconds)
            shake_amount = self._trauma * self._trauma  # quadratic T^2
            self.shake_offset_x = (random.uniform(-1, 1)) * self._max_shake_offset * shake_amount
            self.shake_offset_y = (random.uniform(-1, 1)) * self._max_shake_offset * shake_amount
        else:
            self._trauma = 0.0
            self.shake_offset_x = 0.0
            self.shake_offset_y = 0.0

        # 2. Update Zoom Lerp
        if abs(self.target_zoom - self.zoom_level) > 0.001:
            self.zoom_level += (self.target_zoom - self.zoom_level) * min(1.0, dt_seconds * self.zoom_speed)
        else:
            self.zoom_level = self.target_zoom

    @property
    def offset(self) -> Tuple[float, float]:
        """Total world rendering offset (x + shake_x, y + shake_y)."""
        return (self.x + self.shake_offset_x, self.y + self.shake_offset_y)

    def apply(self, source_surface: pg.Surface) -> pg.Surface:
        """Apply camera shake offset and zoom onto source_surface."""
        if self.shake_offset_x == 0.0 and self.shake_offset_y == 0.0 and self.zoom_level == 1.0:
            return source_surface

        self.buffer.blit(source_surface, (int(self.shake_offset_x), int(self.shake_offset_y)))

        if abs(self.zoom_level - 1.0) > 0.001:
            crop_w = int(self.width / self.zoom_level)
            crop_h = int(self.height / self.zoom_level)
            crop_x = int(max(0, min(self.focus_x - crop_w // 2, self.width - crop_w)))
            crop_y = int(max(0, min(self.focus_y - crop_h // 2, self.height - crop_h)))

            crop_rect = pg.Rect(crop_x, crop_y, crop_w, crop_h)
            sub_surf = self.buffer.subsurface(crop_rect)
            return pg.transform.smoothscale(sub_surf, (self.width, self.height))

        return self.buffer
