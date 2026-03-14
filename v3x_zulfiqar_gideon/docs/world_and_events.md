# 🌍 V3X ZULFIQAR-GIDEON: World & Events

The World Event System manages the progression of your level. It allows you to trigger logic based on how far the player has traveled.

## Core Concepts

### 1. WorldEventManager
A central hub that tracks distance and fires events. It is high-performance and supports automated event sorting.

### 2. Event Handlers
Before triggering an event, you must register a "Handler" — a function that knows what to do for that event type.

## Using the System

### Step 1: Register Handlers
```python
def spawn_entity(params):
    print(f"Spawning a {params['type']}!")

manager = WorldEventManager()
manager.register_handler("spawn", spawn_entity)
```

### Step 2: Add Events
Often loaded via JSON, but can be added manually:
```python
# id, distance, type, **params
manager.add_event(1, 1000, "spawn", type="Elite")
```

### Step 3: Update in Loop
```python
# Pass the current world scroll distance every frame
manager.update(player_total_distance)
```

## Referencing Other Parts
- **Entities**: Handlers usually call `group.add(MyEntity(...))` to place objects.
- **UI**: Use events to trigger cutscenes or notification banners.
