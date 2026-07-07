import json
import os
from typing import Any, Dict

class SettingsManager:
    _instance = None
    _settings_file = "settings.json"
    
    # Default settings configuration
    defaults = {
        "fps_cap": 60,
        "graphics_quality": "high",
        "music_volume": 0.5,
        "sfx_volume": 0.8,
    }
    
    def __new__(cls) -> "SettingsManager":
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance.data = cls.defaults.copy()
            cls._instance.load()
        return cls._instance
        
    def load(self) -> None:
        """Load settings from the JSON file if it exists."""
        if os.path.exists(self._settings_file):
            try:
                with open(self._settings_file, "r") as f:
                    loaded = json.load(f)
                    for k, v in loaded.items():
                        if k in self.defaults:
                            self.data[k] = v
            except Exception as e:
                print(f"[SettingsManager] Error loading settings: {e}")
                
    def save(self) -> None:
        """Save settings to the JSON file."""
        try:
            with open(self._settings_file, "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"[SettingsManager] Error saving settings: {e}")
            
    def get(self, key: str) -> Any:
        """Get the value of a setting."""
        return self.data.get(key, self.defaults.get(key))
        
    def set(self, key: str, value: Any) -> None:
        """Set the value of a setting and save immediately."""
        if key in self.defaults:
            self.data[key] = value
            self.save()
