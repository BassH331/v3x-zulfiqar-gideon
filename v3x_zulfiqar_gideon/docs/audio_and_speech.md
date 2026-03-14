# 🔊 V3X ZULFIQAR-GIDEON: Audio & Speech

High-level control over sound effects, music, and AI-generated voiceovers.

## 1. AudioManager
The `AudioManager` handles multi-channel sound playback with priority and spatial audio support.

### Basic Playback
```python
# Play a sound effect
channel_id = audio_manager.play_sound("slash", priority=SoundPriority.NORMAL)

# Play music in a loop
music_channel = audio_manager.play_sound("bg_music", loop=True, volume=0.5)
```

### Spatial Audio
Sounds can be placed in the world. Their volume will automatically attenuate based on the distance from the listener.
```python
# location=(x, y), player_pos=(x, y)
audio_manager.play_sound("fireball", location=(1500, 300), player_pos=(200, 300))
```

## 2. TTS Manager (Sovereign Voice)
The `TTSManager` uses Edge TTS to generate high-quality voiceover files from text.

### Generation
```python
from src.my_engine.tts_manager import TTSManager

tts = TTSManager()
tts.configure(voice='en-GB-RyanNeural', rate='+20%')
# Saves to an MP3 file if it doesn't already exist
tts.generate_audio("The legends are true.", "assets/audio/voice/line1.mp3")
```

## Referencing Other Parts
- **Asset Manager**: The library is often populated by loading files cached by `AssetManager`.
- **States**: Audio is typically started in `State.on_enter`.
