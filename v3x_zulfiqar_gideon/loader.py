"""
Generic utility for loading world/level data from JSON files.

Provides a simple static interface for parsing JSON configuration
files used for level layouts, spawn tables, and event schedules.
"""

import json
import os
from typing import Optional


class WorldLoader:
    """Generic utility for loading world/level data from JSON."""
    
    @staticmethod
    def load_json(file_path: str) -> Optional[dict]:
        """Load and parse a JSON file."""
        if not os.path.exists(file_path):
            print(f"[WorldLoader] Error: File not found: {file_path}")
            return None
            
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WorldLoader] Error parsing {file_path}: {e}")
            return None
