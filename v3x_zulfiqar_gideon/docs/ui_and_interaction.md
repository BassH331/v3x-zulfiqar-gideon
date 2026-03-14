# 🖱️ V3X ZULFIQAR-GIDEON: UI & Interaction

Modular UI system for buttons, menus, and overlays.

## 1. Buttons
The `Button` class handles mouse interaction, hover animations, and scaling automatically.

### Creating a Button
```python
from src.my_engine.ui import Button

def start_game():
    print("Sovereign session started!")

btn = Button(
    x=400, y=300, 
    image=play_image, 
    hover_image=play_hover_image,
    on_click=start_game,
    anchor='center'
)
```

### Key Properties
- **Anchors**: Place buttons using `'topleft'`, `'center'`, `'bottomright'`, etc.
- **Hover Scale**: Buttons automatically "pulse" larger when hovered for a premium feel.

## Best Practices
- **Event Handling**: You MUST call `btn.handle_event(event)` inside your state's loop.
- **Updating**: Call `btn.update(dt)` to process hover animations.

## Referencing Other Parts
- **States**: UI elements are the primary way users interact with the `StateManager`.
- **Assets**: Buttons use `AssetManager` to retrieve their textures.
