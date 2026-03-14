# 🧠 V3X ZULFIQAR-GIDEON: State Management

The State Management system is the backbone of your game's flow. It allows you to switch between menus, gameplay, and cutscenes seamlessly.

## Core Concepts

### 1. The State
A `State` is a single "screen" or "mode" of your game. 

- **Methods to Override:**
    - `on_enter()`: Called when the state becomes active. Use for initialization/audio start.
    - `on_exit()`: Called when the state is removed or paused. Use for cleanup/audio stop.
    - `handle_event(event)`: Process Pygame events (keyboard, mouse).
    - `update(dt)`: Game logic update. `dt` is delta time in seconds.
    - `draw(surface)`: Rendering logic.

### 2. The StateManager
The `StateManager` maintains a **Stack** of states.

- **`push(state)`**: Adds a new state on top. The previous state is "paused" (`on_exit` is called).
- **`pop()`**: Removes the current state and resumes the one below it.
- **`set(state)`**: Clears everything and starts fresh with one state.

## Example Use Case: Pause Menu

```python
class GameplayState(State):
    def handle_event(self, event):
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            # Pushes PauseState on top. GameplayState waits underneath.
            self.manager.push(PauseState(self.manager))

class PauseState(State):
    def handle_event(self, event):
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            # Resumes GameplayState exactly where it was.
            self.manager.pop()
```

## Referencing Other Parts
- **Assets**: Use `AssetManager` inside `on_enter` to preload textures for the state.
- **Audio**: Use `AudioManager` in `on_enter` to play background music.
