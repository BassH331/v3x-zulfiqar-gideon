# ⚔️ V3X ZULFIQAR-GIDEON

**Yoh, stop writing spaghetti code. Start forging legends.**

Welcome to **V3X ZULFIQAR-GIDEON**. Most people build games by tangling their logic into a mess. We don't. This is a high-octane framework built for one thing: extracting the core infrastructure so you can actually scale your vision.

---

## 🗡️ Why the "Whack" Name?

Look, every major engine—from Unity to Godot—started the same way: Someone builds a game, realizes the *infrastructure* is the real gold, and extracts it. That's exactly what we did with *Guardian Runner*. But a powerful engine needs a title that hits the spot.

### ⚡ V3X: Veni, Vidi, Vici
This is the heart of the brand. **V3X** stands for the Roman saying: *I came, I saw, I conquered.* It’s the mission statement of an indie startup with nothing but a dream and the hustle to make it real. We aren't here to just participate; we're here to win.

### ⚔️ ZULFIQAR: The Double-Edged Split
Named after the legendary split blade, this is our architectural philosophy. A real weapon needs balance. **Zulfiqar** is our commitment to a hard split: **Infrastructure** (Engine) on one side, **Content** (Game) on the other. No more tight coupling.

### 🛡️ GIDEON: Small Force, Massive Impact
Gideon led 300 men to victory against thousands through strategy. That’s the indie dream—one dev (or a small crew) crushing massive project complexities through pure superior architecture.

### 👑 The Sovereign Alignment
Sovereignty isn’t just a buzzword—it’s about owning your tools. When you're a startup starting from zero, the only thing you truly own is your work. By using **V3X ZULFIQAR-GIDEON**, you’re taking back control. You own the code, you own the infrastructure, you own the path. Pure game dev sovereignty.

---

## �📚 Technical Manuals

We've documented every corner of the engine to help you build faster.

- [🧠 State Management](docs/state_management.md) — Mastering the stack-based flow.
- [👻 Entities & Components](docs/entities_and_components.md) — Building characters and logic.
- [🌍 World & Events](docs/world_and_events.md) — Distance-based triggering and level control.
- [🎨 Assets & Animation](docs/assets_and_animation.md) — Optimized loading and smooth sprites.
- [🔊 Audio & Speech](docs/audio_and_speech.md) — Spatial sound and AI-powered voiceovers.
- [🖱️ UI & Interaction](docs/ui_and_interaction.md) — Dynamic buttons and menus.

---

## 🧠 Core Architecture

### 1. State Machine (The Brain)
Forget `if game_state == "menu":`. Our **Stack-Based State Machine** lets you layer your game like a delicious cake. [Learn more.](docs/state_management.md)

### 2. World Event System (The Director)
Tired of timing enemy spawns manually? Schedule them at specific distances!
```python
world_manager.add_event(id=1, distance=1500, event_type="npc", npc_name="Wizard")
```

### 3. Asset Manager (The Vault)
Loading images inside your game loop? **Illegal.** 🚫
The **AssetManager** handles lazy-loading, caching, and placeholder fallback.

---

## 🛠️ Quick Start

1. **Initialize the Engine**:
   ```python
   from src.my_engine import StateManager
   state_manager = StateManager()
   state_manager.push(IntroState(state_manager))
   ```

2. **Run the Loop**:
   ```python
   while True:
       state_manager.update(dt)
       state_manager.draw(screen)
   ```

---

*Built by the V3X.*
