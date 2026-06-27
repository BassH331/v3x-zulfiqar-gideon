import pygame
from .asset_manager import AssetManager

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path=None):
        super().__init__()
        if image_path:
            self.image = AssetManager.get_texture(image_path)
            self.rect = self.image.get_rect(topleft=(x, y))
        else:
            self.image = pygame.Surface((32, 32))
            self.image.fill((255, 255, 255))
            self.rect = self.image.get_rect(topleft=(x, y))
            
        self.image_offset = pygame.math.Vector2(0, 0)
        self.components = {}
        
    def add_component(self, component):
        self.components[component.name] = component
        component.owner = self
        
    def get_component(self, name):
        return self.components.get(name)
        
    def update(self, dt):
        for component in self.components.values():
            component.update(dt)
            
    def draw(self, surface):
        """Draws the entity's image at the rect position minus the offset."""
        draw_pos = self.rect.topleft - self.image_offset
        surface.blit(self.image, draw_pos)

    def set_hitbox_size(self, width, height):
        """
        Sets the absolute size of the collision rect, maintaining center.
        Use this if you know the exact dimensions you want for the hitbox.
        
        Args:
            width (int): The new width of the hitbox.
            height (int): The new height of the hitbox.
        """
        center = self.rect.center
        self.rect.size = (width, height)
        self.rect.center = center

    def reduce_hitbox(self, reduce_w, reduce_h, align='center', offset_y=0):
        """
        Reduces the collision rect by the specified width and height.
        Use this to make the hitbox smaller than the sprite image.
        
        Args:
            reduce_w (int): Amount to reduce the width by (total).
            reduce_h (int): Amount to reduce the height by (total).
            align (str): 'center' or 'bottom'. Defaults to 'center'.
                         'bottom' keeps the bottom edge fixed (good for platformers).
            offset_y (int): Additional vertical offset to raise the bottom (only for align='bottom').
        """
        if align == 'center':
            self.rect.inflate_ip(-reduce_w, -reduce_h)
            self.image_offset = pygame.math.Vector2(reduce_w // 2, reduce_h // 2)
        elif align == 'bottom':
            original_bottom = self.rect.bottom
            self.rect.inflate_ip(-reduce_w, -reduce_h)
            self.rect.bottom = original_bottom - offset_y
            self.image_offset = pygame.math.Vector2(reduce_w // 2, reduce_h - offset_y)

    def adjust_hitbox_sides(self, top=0, bottom=0, left=0, right=0):
        """
        Shrinks the hitbox by the specified amount from each side.
        Positive values shrink the box, negative values expand it.
        
        Args:
            top (int): Amount to shrink from the top.
            bottom (int): Amount to shrink from the bottom.
            left (int): Amount to shrink from the left.
            right (int): Amount to shrink from the right.
        """
        self.rect.x += left
        self.rect.y += top
        self.rect.width -= (left + right)
        self.rect.height -= (top + bottom)
        
        # Update image offset to keep image stationary relative to the new rect
        self.image_offset.x += left
        self.image_offset.y += top

    def set_image_offset(self, x, y):
        """
        Manually sets the image offset relative to the hitbox top-left corner.
        
        Args:
            x (int): Horizontal offset. Positive moves image LEFT relative to hitbox.
            y (int): Vertical offset. Positive moves image UP relative to hitbox.
        """
        self.image_offset = pygame.math.Vector2(x, y)

class Component:
    def __init__(self):
        self.name = "base_component"
        self.owner = None
        
    def update(self, dt):
        pass

from typing import Dict, List, Optional, Any, Set
from enum import Enum

class Actor(Entity):
    """
    An advanced Entity with a priority-based state machine and animation system.
    """
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.state: Optional[Enum] = None
        self.animation_index: float = 0.0
        self.animations: Dict[Any, List[Any]] = {}
        self.state_configs: Dict[Enum, Any] = {} # Mapping of state to behavior config
        
        self.facing_left: bool = False
        self.velocity = pygame.math.Vector2(0, 0)
        self._animations_flipped: Dict[Any, List[Any]] = {}
        
        # Lazy import: combat is only needed by Actor, not Entity/Component
        from .combat import AttackState, AttackConfig
        self.attack_state = AttackState()
        self.current_attack_config: Optional[AttackConfig] = None

    @property
    def hitbox(self) -> pygame.Rect:
        return self.rect

    @property
    def entity_id(self) -> int:
        return id(self)

    @property
    def is_dead(self) -> bool:
        return False

    @property
    def is_invincible(self) -> bool:
        return False

    def should_deal_damage(self) -> bool:
        return self.attack_state.is_hit_frame_active() if self.attack_state else False

    def get_attack_hitbox(self) -> Any:
        if not self.should_deal_damage():
            return None
        return self.attack_state.get_current_hitbox(self.rect, self.facing_left)

    def try_register_hit(self, target_id: int) -> bool:
        return self.attack_state.try_register_hit(target_id) if self.attack_state else False

    def get_current_attack_damage(self) -> float:
        return self.attack_state.get_current_damage() if self.attack_state else 0.0

    def draw_debug_hitboxes(self, surface: pygame.Surface) -> None:
        """Draws the actor's body hitbox and any active attack hitbox for debugging."""
        # Draw body hitbox (blue outline)
        pygame.draw.rect(surface, (0, 0, 255), self.rect, 2)
        
        # Draw active attack hitbox if present (red/orange outline)
        atk_hitbox = self.get_attack_hitbox()
        if atk_hitbox:
            pygame.draw.rect(surface, (255, 100, 0), atk_hitbox, 2)

    def set_state(self, new_state: Enum, force: bool = False):
        """Sets the actor state, respecting priority if defined."""
        if self.state == new_state:
            return

        # Simple priority check: lower enum value = higher priority
        if not force and self.state is not None:
            if hasattr(self.state, 'value') and hasattr(new_state, 'value'):
                if new_state.value > self.state.value:
                    # Check if current state is interruptible
                    cfg = self.state_configs.get(self.state)
                    if cfg and hasattr(cfg, 'interruptible') and not cfg.interruptible:
                        return

        self.state = new_state
        self.animation_index = 0.0
        
        # Clear pre-resolved configuration cache fields
        self._current_frames = None
        self._current_config = None
        self._current_base_speed = None
        self._current_loops = None
        self._current_frame_speeds = None
        self._current_next_state = None
        
        # Sync attack state if entering an attack
        if self.current_attack_config and hasattr(new_state, 'name') and "ATTACK" in new_state.name:
            self.attack_state.begin(self.current_attack_config)

    def update_animation(self, dt: float):
        """Updates the current animation frame with per-frame speed support."""
        if not self.state:
            return

        frames = getattr(self, '_current_frames', None)
        if not frames:
            frames = self.animations.get(self.state)
            self._current_frames = frames
            if not frames:
                return

        cfg = getattr(self, '_current_config', None)
        if cfg is None:
            cfg = self.state_configs.get(self.state)
            self._current_config = cfg if cfg is not None else False
            self._current_base_speed = getattr(cfg, 'animation_speed', 0.2) if cfg else 0.2
            self._current_loops = getattr(cfg, 'loops', True) if cfg else True
            self._current_frame_speeds = getattr(cfg, 'frame_speeds', None) if cfg else None
            self._current_next_state = getattr(cfg, 'next_state', None) if cfg else None

        base_speed = self._current_base_speed
        loops = self._current_loops
        
        # Handle hit-stop during attack
        if self.attack_state.is_in_hit_stop:
            return

        # Per-frame speed curve: use frame-specific speed if available
        current_frame = int(self.animation_index)
        frame_speeds = self._current_frame_speeds
        if frame_speeds and current_frame in frame_speeds:
            speed = frame_speeds[current_frame]
        else:
            speed = base_speed

        self.animation_index += speed
        if self.animation_index >= len(frames):
            if loops:
                self.animation_index = 0.0
            else:
                self.animation_index = len(frames) - 1
                # Transition to next state if defined
                next_state = self._current_next_state
                if next_state:
                    self.set_state(next_state, force=True)
                    frames = getattr(self, '_current_frames', None)
                    if not frames:
                        frames = self.animations.get(self.state)
                        self._current_frames = frames
                        if not frames:
                            return
        
        self.image = frames[int(self.animation_index)]
        if self.facing_left:
            flipped_frames = self._animations_flipped.get(self.state)
            if flipped_frames is None or len(flipped_frames) != len(frames):
                flipped_frames = [pygame.transform.flip(img, True, False) for img in frames]
                self._animations_flipped[self.state] = flipped_frames
            self.image = flipped_frames[int(self.animation_index)]

    def update(self, dt: float):
        super().update(dt)
        if self.attack_state.is_active:
            self.attack_state.update(int(self.animation_index))
        self.update_animation(dt)
