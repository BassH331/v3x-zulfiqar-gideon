"""
Multi-layer parallax sky/background component.

Provides a generic scrolling background system that can be configured
with any number of layers at different scroll speeds.
"""

from typing import List, Optional

import pygame as pg

from .asset_manager import AssetManager


class Sky:
    """Generic multi-layer parallax sky/background component."""
    
    def __init__(self, screen_width: int, screen_height: int, layer_paths: List[str], speeds: List[int] = None):
        """
        Initialize the sky with multiple parallax layers.
        
        Args:
            screen_width: Width of the screen.
            screen_height: Height of the screen.
            layer_paths: List of file paths for the background layers.
            speeds: List of scroll speeds (pixels per second) for each layer.
        """
        self.width = screen_width
        self.height = screen_height
        self.layers = []
        for path in layer_paths:
            img = AssetManager.get_texture(path)
            scaled_img = pg.transform.scale(img, (screen_width, screen_height))
            self.layers.append(scaled_img)
            
        self.speeds = speeds or [0] * len(self.layers)
        self.offsets = [0.0] * len(self.layers)
        
    def update(self, dt_sec: float):
        """Update layer offsets based on elapsed time."""
        for i in range(len(self.offsets)):
            if self.speeds[i] == 0: continue
            self.offsets[i] -= self.speeds[i] * dt_sec
            if self.offsets[i] <= -self.width:
                self.offsets[i] += self.width
                
    def draw(self, surface: pg.Surface):
        """Draw all layers with horizontal wrapping."""
        for i, layer in enumerate(self.layers):
            if self.speeds[i] == 0:
                surface.blit(layer, (0, 0))
            else:
                surface.blit(layer, (self.offsets[i], 0))
                surface.blit(layer, (self.offsets[i] + self.width, 0))
