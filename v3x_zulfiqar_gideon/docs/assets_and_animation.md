# 🎨 V3X ZULFIQAR-GIDEON: Assets & Animation

Managing visual assets and frame-based animations at high frequency.

## 1. Asset Manager
The `AssetManager` is a global cache. It ensures you never load the same image or sound twice, preventing memory bloat.

### Quick Usage
```python
from src.my_engine import AssetManager

# Get a Surface
img = AssetManager.get_texture("assets/hero.png")

# Get a Font
font = AssetManager.get_font("assets/myfont.ttf", 24)
```

## 2. Animation System
Animations are handled by two classes: `Animation` (data) and `Animator` (logic).

### Definining an Animation
```python
from src.my_engine.animation import Animation

# frames, frame_duration, loop
walk_anim = Animation([frame1, frame2, frame3], 0.1, True)
```

### The Animator
The `Animator` manages multiple animations and handles the timing for you.

```python
from src.my_engine.animation import Animator

class Player(Entity):
    def __init__(self):
        self.animator = Animator()
        self.animator.add("walk", walk_anim)
        self.animator.set("walk")

    def update(self, dt):
        self.image = self.animator.get_frame() # Automatically advances frame
```

## Referencing Other Parts
- **Entities**: Most entities use an `Animator` as their primary visual controller.
- **Asset Manager**: `Animation` frames are usually retrieved via `AssetManager.get_texture`.
