# 👻 V3X ZULFIQAR-GIDEON: Entities & Components

PixelEngine (V3X ZULFIQAR-GIDEON) uses a lightweight "ECS-Lite" approach. It balances the power of composition with the simplicity of class inheritance.

## 1. Entities

The `Entity` class is a specialized Pygame Sprite. It handles its own position (`rect`), image, and components.

### Simple Creation
```python
from src.my_engine import Entity

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/graphics/player.png")
```

### Hitbox Management
Don't use the raw `self.rect` for collisions if your sprite has transparent padding. Use these helpers:
- `reduce_hitbox(w, h, align='center')`: Shrinks the collision box.
- `adjust_hitbox_sides(top, bottom, left, right)`: Precise side-by-side adjustment.

## 2. Components

Components are reusable bits of logic you can "plug in" to any entity.

### Creating a Component
```python
from src.my_engine import Component

class HealthComponent(Component):
    def __init__(self, amount):
        super().__init__()
        self.name = "health" 
        self.hp = amount

    def update(self, dt):
        if self.hp <= 0:
            self.owner.kill() 
```

## Referencing Other Parts
- **Animation**: Use the `Animator` class within an Entity.
- **World Events**: Entity spawning is often handled by `WorldEventManager` handlers.
