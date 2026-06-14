"""
Interaction point system for proximity-triggered dialogue and objectives.

Provides an invisible world marker (pygame sprite) that detects player
proximity and displays a contextual prompt.
"""

from typing import Optional

import pygame as pg

from .asset_manager import AssetManager


class InteractionPoint(pg.sprite.Sprite):
    """An invisible world marker that triggers dialogue on proximity.

    Args:
        x: Initial world X position.
        y: Screen Y position.
        text: Objective/dialogue text shown in the parchment overlay.
        title: Header text for the parchment overlay.
        proximity_radius: Pixel distance to trigger the talk prompt.
        font_path: Path to the font asset.
        font_size: Size of the font.
    """

    def __init__(
        self,
        x: int,
        y: int,
        text: str,
        title: str = "Objective",
        proximity_radius: int = 150,
        font_path: Optional[str] = None,
        font_size: int = 30
    ) -> None:
        super().__init__()

        self.text = text
        self.title = title
        self.proximity_radius = proximity_radius
        self._interacted: bool = False
        
        # UI Settings
        self._font_path = font_path
        self._font_size = font_size
        self._PROMPT_COLOR = (255, 255, 255)
        self._PROMPT_BG_COLOR = (30, 30, 30, 200)
        self._PROMPT_PADDING_X = 16
        self._PROMPT_PADDING_Y = 8
        self._PROMPT_OFFSET_Y = -70
        self._PROMPT_BORDER_RADIUS = 8

        # Invisible sprite
        self.image = pg.Surface((1, 1), pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        self.rect = pg.Rect(x, y, 1, 1)

        self._prompt_surface: Optional[pg.Surface] = None
        self._in_range: bool = False

    def _ensure_prompt(self) -> None:
        """Lazy load font and build prompt surface."""
        if self._prompt_surface is not None:
            return
            
        if self._font_path is None:
            # Fallback to default pygame font if no path provided
            font = pg.font.SysFont(None, self._font_size)
        else:
            font = AssetManager.get_font(self._font_path, self._font_size)
            
        text_surf = font.render("Talk  [ X / ENTER ]", True, self._PROMPT_COLOR)
        w = text_surf.get_width() + self._PROMPT_PADDING_X * 2
        h = text_surf.get_height() + self._PROMPT_PADDING_Y * 2

        bg = pg.Surface((w, h), pg.SRCALPHA)
        pg.draw.rect(
            bg,
            self._PROMPT_BG_COLOR,
            (0, 0, w, h),
            border_radius=self._PROMPT_BORDER_RADIUS,
        )
        pg.draw.rect(
            bg,
            (200, 200, 200, 120),
            (0, 0, w, h),
            width=2,
            border_radius=self._PROMPT_BORDER_RADIUS,
        )
        bg.blit(text_surf, (self._PROMPT_PADDING_X, self._PROMPT_PADDING_Y))
        self._prompt_surface = bg

    @property
    def can_interact(self) -> bool:
        return self._in_range and not self._interacted

    def mark_interacted(self) -> None:
        self._interacted = True

    def reset(self) -> None:
        self._interacted = False

    def check_proximity(self, player_rect: pg.Rect) -> bool:
        dx = abs(self.rect.centerx - player_rect.centerx)
        dy = abs(self.rect.centery - player_rect.centery)
        distance = (dx * dx + dy * dy) ** 0.5
        self._in_range = distance <= self.proximity_radius
        return self._in_range

    def update(self, dt: Optional[float] = None, scroll_speed: int = 0) -> None:
        self.rect.x -= scroll_speed

    def draw(self, surface: pg.Surface) -> None:
        if not self.can_interact:
            return

        self._ensure_prompt()
        if self._prompt_surface:
            # Pulsing alpha
            ticks = pg.time.get_ticks()
            alpha = 180 + int(75 * abs(((ticks // 8) % 200 - 100) / 100))
            self._prompt_surface.set_alpha(alpha)

            px = self.rect.centerx - self._prompt_surface.get_width() // 2
            py = self.rect.centery + self._PROMPT_OFFSET_Y
            surface.blit(self._prompt_surface, (px, py))
