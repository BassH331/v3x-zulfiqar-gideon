"""
Event Bus — A decoupled publish/subscribe messaging system for game events.

Allows game systems (combat, UI, audio, telemetry) to communicate without
direct references to each other.  Publishers emit typed event objects;
subscribers react independently.

Usage::

    from v3x_zulfiqar_gideon import EventBus, EntityDied

    bus = EventBus()
    bus.subscribe(EntityDied, on_entity_died)
    bus.emit(EntityDied(entity=skeleton, killer=player, position=(100, 200)))

Thread-safety:
    subscribe() and emit() are protected by a threading.Lock so that
    background tasks (e.g. async config fetches) can safely publish events
    from non-main threads.

Performance:
    - defaultdict(list) dispatch table → O(1) lookup by event type.
    - WeakMethod references → automatic cleanup when subscriber objects die.
    - __slots__ on all event dataclasses → zero per-instance dict overhead.
"""

from __future__ import annotations

import threading
import weakref
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from types import MethodType
from typing import Any, Callable, Optional, Type, TypeVar

import pygame as pg


# ─────────────────────────────────────────────────────────────────────────────
# Event Type Registry
# ─────────────────────────────────────────────────────────────────────────────

class EventType(Enum):
    """Engine-level event type identifiers."""
    ENTITY_DIED = auto()
    DAMAGE_DEALT = auto()
    DAMAGE_RECEIVED = auto()
    STATE_CHANGED = auto()
    ENTITY_SPAWNED = auto()


# ─────────────────────────────────────────────────────────────────────────────
# Base Event
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(slots=True)
class GameEvent:
    """Base class for all game events.

    Subclass this with ``@dataclass(slots=True)`` and add your fields.
    The ``timestamp`` is auto-filled with the current pygame tick count.
    """
    timestamp: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        try:
            self.timestamp = pg.time.get_ticks()
        except pg.error:
            # Pygame not initialized (e.g. unit tests)
            self.timestamp = 0


# ─────────────────────────────────────────────────────────────────────────────
# Concrete Event Types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(slots=True)
class EntityDied(GameEvent):
    """Fired when any entity's health reaches zero."""
    entity: Any = None
    killer: Any = None
    position: tuple[float, float] = (0.0, 0.0)
    soul_value: int = 0
    is_boss: bool = False
    tier: str = "minion"
    spawn_zone: Any = None


@dataclass(slots=True)
class DamageDealt(GameEvent):
    """Fired when damage is successfully applied to a target."""
    attacker: Any = None
    target: Any = None
    amount: float = 0.0
    knockback: float = 0.0
    target_health_before: float = 0.0
    target_health_after: float = 0.0
    is_boss: bool = False
    target_tier: str = "minion"


@dataclass(slots=True)
class DamageReceived(GameEvent):
    """Fired when the player takes damage."""
    target: Any = None
    attacker: Any = None
    amount: float = 0.0
    health_remaining: float = 0.0
    attacker_type: str = "unknown"


@dataclass(slots=True)
class StateChanged(GameEvent):
    """Fired when an entity's FSM state transitions."""
    entity: Any = None
    old_state: Any = None
    new_state: Any = None


@dataclass(slots=True)
class EntitySpawned(GameEvent):
    """Fired when a new entity enters the game world."""
    entity: Any = None
    position: tuple[float, float] = (0.0, 0.0)
    entity_type: str = "unknown"
    event_id: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────────────
# Weak Reference Wrapper
# ─────────────────────────────────────────────────────────────────────────────

_EventT = TypeVar("_EventT", bound=GameEvent)
_Callback = Callable[[GameEvent], None]


class _WeakCallback:
    """Weak reference wrapper that handles both bound methods and functions.

    Bound methods are stored via ``weakref.WeakMethod`` so that the
    subscriber object can be garbage-collected normally.  Plain functions
    use a standard ``weakref.ref``.
    """
    __slots__ = ("_ref", "_is_method")

    def __init__(self, callback: _Callback) -> None:
        if isinstance(callback, MethodType):
            self._ref = weakref.WeakMethod(callback)
            self._is_method = True
        else:
            # Try a standard weakref; fall back to a strong ref for
            # non-weak-referenceable callables (lambdas, closures, etc.)
            try:
                self._ref = weakref.ref(callback)
                self._is_method = False
            except TypeError:
                # Lambdas / closures / partials can't be weak-ref'd —
                # store them directly wrapped in a lambda that returns them.
                _strong = callback
                self._ref = lambda: _strong  # type: ignore[assignment]
                self._is_method = False

    def __call__(self, event: GameEvent) -> bool:
        """Invoke the callback.  Returns False if the referent is dead."""
        cb = self._ref()
        if cb is None:
            return False
        cb(event)
        return True

    @property
    def alive(self) -> bool:
        return self._ref() is not None


# ─────────────────────────────────────────────────────────────────────────────
# Event Bus
# ─────────────────────────────────────────────────────────────────────────────

class EventBus:
    """Publish/subscribe event dispatcher.

    Example::

        bus = EventBus()

        def on_kill(event: EntityDied):
            print(f"{event.entity} was slain!")

        bus.subscribe(EntityDied, on_kill)
        bus.emit(EntityDied(entity=skeleton, killer=player))

    Subscribers whose owner objects have been garbage-collected are
    automatically pruned on the next ``emit()`` call.
    """

    def __init__(self) -> None:
        self._subscribers: defaultdict[
            Type[GameEvent], list[_WeakCallback]
        ] = defaultdict(list)
        self._lock = threading.Lock()

    # ── Public API ───────────────────────────────────────────────────────

    def subscribe(
        self,
        event_type: Type[_EventT],
        callback: Callable[[_EventT], None],
    ) -> None:
        """Register *callback* to be called whenever *event_type* is emitted.

        Bound methods are stored as weak references; the subscription is
        automatically removed when the owning object is garbage-collected.

        Args:
            event_type: The event class to listen for.
            callback:   A callable accepting a single event argument.
        """
        with self._lock:
            self._subscribers[event_type].append(_WeakCallback(callback))  # type: ignore[arg-type]

    def unsubscribe(
        self,
        event_type: Type[_EventT],
        callback: Callable[[_EventT], None],
    ) -> None:
        """Remove a specific callback from an event type's subscriber list.

        Safe to call even if *callback* was never subscribed.

        Args:
            event_type: The event class the callback was registered for.
            callback:   The exact callable to remove.
        """
        with self._lock:
            subs = self._subscribers.get(event_type)
            if subs is None:
                return
            # Remove entries whose referent matches *callback* or is dead
            self._subscribers[event_type] = [
                s for s in subs
                if s.alive and s._ref() is not callback
            ]

    def emit(self, event: GameEvent) -> None:
        """Dispatch *event* to all subscribers of its type.

        Dead (garbage-collected) subscribers are silently pruned.

        Args:
            event: The event instance to broadcast.
        """
        event_type = type(event)
        with self._lock:
            subs = self._subscribers.get(event_type)
            if subs is None:
                return
            # Dispatch and prune dead refs in one pass
            alive: list[_WeakCallback] = []
            for weak_cb in subs:
                if weak_cb(event):
                    alive.append(weak_cb)
            self._subscribers[event_type] = alive

    def clear(self) -> None:
        """Remove all subscriptions."""
        with self._lock:
            self._subscribers.clear()

    def subscriber_count(self, event_type: Type[GameEvent]) -> int:
        """Return the number of live subscribers for *event_type*."""
        with self._lock:
            subs = self._subscribers.get(event_type)
            if subs is None:
                return 0
            return sum(1 for s in subs if s.alive)
