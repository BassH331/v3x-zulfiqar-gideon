"""
V3X ZULFIQAR-GIDEON — A sovereign, high-octane game framework for forging legends.

All public symbols are exported here so game projects can import from
the top-level package without depending on internal file layout:

    from v3x_zulfiqar_gideon import State, Actor, AttackConfig, AudioManager, ...

This decouples the game code from the engine's internal module structure,
making the engine safe to refactor and reorganize without breaking consumers.
"""

# ── Core engine ──────────────────────────────────────────────────────────────
from .core import V3XCore
from .settings import SettingsManager

# ── State management ─────────────────────────────────────────────────────────
from .state_machine import State, StateManager

# ── Routing & manifest ───────────────────────────────────────────────────────
from .router import V3XManifest, Router

# ── Asset management ─────────────────────────────────────────────────────────
from .asset_manager import AssetManager

# ── Audio ────────────────────────────────────────────────────────────────────
from .audio_manager import AudioManager, FootstepController, SoundPriority, SpotlightSFXManager, SFXTracker

# ── Entity-Component System ─────────────────────────────────────────────────
from .ecs import Entity, Component, Actor

# ── Combat system ────────────────────────────────────────────────────────────
from .combat import (
    AttackConfig,
    AttackState,
    AttackPhase,
    HitboxData,
    HitResult,
    CombatProcessor,
)

# ── Animation ────────────────────────────────────────────────────────────────
from .animation import Animation, Animator

# ── UI components ────────────────────────────────────────────────────────────
from .ui import (
    UITheme,
    Button,
    LabelButton,
    UIButton,
    FloatingNotification,
    NotificationBanner,
    ParchmentDisplay,
)

# ── Visual effects ───────────────────────────────────────────────────────────
from .effects import SceneHighlighter

# ── World systems ────────────────────────────────────────────────────────────
from .world import WorldEvent, WorldEventManager
from .sky import Sky
from .interaction import InteractionPoint
from .loader import WorldLoader

# ── Game systems ─────────────────────────────────────────────────────────────
from .systems import (
    ObjectiveTrigger,
    ObjectiveTriggerManager,
    SpawnConfig,
    EntityManager,
)

# ── Text-to-Speech ───────────────────────────────────────────────────────────
from .tts_manager import TTSManager


__all__ = [
    # Core
    "V3XCore",
    "SettingsManager",
    # State
    "State", "StateManager",
    # Router
    "V3XManifest", "Router",
    # Assets
    "AssetManager",
    # Audio
    "AudioManager", "FootstepController", "SoundPriority", "SpotlightSFXManager", "SFXTracker",
    # ECS
    "Entity", "Component", "Actor",
    # Combat
    "AttackConfig", "AttackState", "AttackPhase",
    "HitboxData", "HitResult", "CombatProcessor",
    # Animation
    "Animation", "Animator",
    # UI
    "UITheme", "Button", "LabelButton", "UIButton",
    "FloatingNotification", "NotificationBanner", "ParchmentDisplay",
    # Effects
    "SceneHighlighter",
    # World
    "WorldEvent", "WorldEventManager", "InteractionPoint", "Sky", "WorldLoader",
    # Systems
    "ObjectiveTrigger", "ObjectiveTriggerManager", "SpawnConfig", "EntityManager",
    # TTS
    "TTSManager",
]
