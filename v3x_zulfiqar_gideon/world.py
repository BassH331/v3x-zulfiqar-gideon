"""
World Event System for distance-triggered game logic.

Provides a standard way to schedule spawns, dialogue, and other events
at specific points in a scrolling game world.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Set


@dataclass
class WorldEvent:
    """A single event triggered at a specific world distance.

    Args:
        id: Unique identifier for the event (prevents double-triggering).
        distance: World X distance when this event fires.
        event_type: String identifier for the type of event (e.g. "npc", "enemy").
        params: Arbitrary data passed to the event handler.
    """
    id: int
    distance: float
    event_type: str
    params: Dict[str, Any] = field(default_factory=dict)
    triggered: bool = False


class WorldEventManager:
    """Manages distance-based triggers and dispatches them to handlers.

    Usage:
        manager = WorldEventManager()
        
        # Register a handler for a specific event type
        manager.register_handler("spawn", lambda params: create_entity(**params))
        
        # Add events
        manager.add_event(id=1, distance=500, event_type="spawn", type="enemy")
        
        # update() in game loop
        manager.update(current_world_distance)
    """

    def __init__(self) -> None:
        self._events: List[WorldEvent] = []
        self._handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._spawned_ids: Set[int] = set()
        self._is_sorted: bool = False

    def register_handler(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback function for an event type."""
        self._handlers[event_type] = callback

    def add_event(self, id: int, distance: float, event_type: str, **params: Any) -> None:
        """Schedule a new world event.
        
        Events are automatically sorted by distance during update() or finalize().
        """
        self._events.append(WorldEvent(id, distance, event_type, params))
        self._is_sorted = False

    def finalize(self) -> None:
        """Manually sort and optimize the event list. 
        
        Call this after adding all events for a level. update() will also call this
        automatically if not already sorted.
        """
        self._events.sort(key=lambda e: e.distance)
        self._is_sorted = True

    def update(self, current_distance: float) -> None:
        """Check for events to fire at the current world distance.

        Optimized to handle distance jumps and sequential triggers efficiently.
        """
        if not self._is_sorted:
            self.finalize()

        for event in self._events:
            # Skip if already triggered globally or in this session
            if event.triggered or event.id in self._spawned_ids:
                continue

            # Since list is sorted, we can stop early if we haven't reached the distance
            if event.distance > current_distance:
                break

            # Trigger the event
            handler = self._handlers.get(event.event_type)
            if handler:
                event.triggered = True
                self._spawned_ids.add(event.id)
                handler(event.params)
            else:
                print(f"[WorldEventManager] Warning: No handler registered for '{event.event_type}'")

    def reset(self) -> None:
        """Reset all events (clears triggered status)."""
        self._spawned_ids.clear()
        for event in self._events:
            event.triggered = False

    def clear(self) -> None:
        """Remove all events and handlers."""
        self._events.clear()
        self._handlers.clear()
        self._spawned_ids.clear()
        self._is_sorted = True


# ── Backward-compatible re-exports ───────────────────────────────────────────
# These classes have been moved to dedicated modules for single-responsibility.
# Re-exported here so existing `from .world import Sky` style imports still work.
from .sky import Sky                        # noqa: E402, F401
from .interaction import InteractionPoint   # noqa: E402, F401
from .loader import WorldLoader             # noqa: E402, F401
