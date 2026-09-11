import pygame
import os
import re

class AssetManager:
    _instance = None
    _textures = {}
    _sounds = {}
    _fonts = {}

    @classmethod
    def get_texture(cls, path):
        if path not in cls._textures:
            try:
                cls._textures[path] = pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"Error loading texture {path}: {e}")
                # Return a placeholder surface
                surf = pygame.Surface((32, 32))
                surf.fill((255, 0, 255)) # Magenta for missing texture
                return surf
        return cls._textures[path]

    @classmethod
    def get_sound(cls, path):
        if path not in cls._sounds:
            try:
                cls._sounds[path] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Error loading sound {path}: {e}")
                return None
        return cls._sounds[path]
    
    @classmethod
    def get_font(cls, path, size):
        key = (path, size)
        if key not in cls._fonts:
            try:
                cls._fonts[key] = pygame.font.Font(path, size)
            except Exception as e:
                print(f"Error loading font {path}: {e}")
                return pygame.font.SysFont("arial", size)
        return cls._fonts[key]

    @classmethod
    def slice_spritesheet(cls, surface, cols=None, rows=None, frame_width=None, frame_height=None):
        """Slice a Pygame surface into a list of frame subsurfaces."""
        frames = []
        w, h = surface.get_size()
        if w <= 0 or h <= 0:
            return frames

        if cols is not None or rows is not None:
            c = max(1, cols if cols is not None else 1)
            r = max(1, rows if rows is not None else 1)
            fw = w // c
            fh = h // r
        elif frame_width is not None or frame_height is not None:
            fw = max(1, frame_width if frame_width is not None else w)
            fh = max(1, frame_height if frame_height is not None else h)
            c = max(1, w // fw)
            r = max(1, h // fh)
        else:
            return [surface]

        for row_idx in range(r):
            for col_idx in range(c):
                rect = pygame.Rect(col_idx * fw, row_idx * fh, fw, fh)
                frames.append(surface.subsurface(rect).copy())
        return frames

    @classmethod
    def get_animation_frames(cls, target_path, cols=None, rows=None, frame_width=None, frame_height=None):
        """Load animation frames from a directory of PNGs or a single sprite sheet image."""
        frames = []
        if not os.path.exists(target_path):
            print(f"Error: Path not found {target_path}")
            return frames

        try:
            # Handle single image file directly
            if os.path.isfile(target_path):
                return cls._load_frames_from_image_file(target_path, cols, rows, frame_width, frame_height)

            # Handle directory
            def _natural_key(name):
                return [int(s) if s.isdigit() else s.lower()
                        for s in re.split(r'(\d+)', name)]
            files = sorted(
                [f for f in os.listdir(target_path)
                 if f.endswith('.png') or f.endswith('.jpg') or f.endswith('.webp')],
                key=_natural_key,
            )

            if not files:
                return frames

            # If directory contains multiple frame files, load them as individual frames
            if len(files) > 1 and not any("_strip" in f.lower() for f in files):
                for f in files:
                    path = os.path.join(target_path, f)
                    frames.append(cls.get_texture(path))
                return frames

            # If directory has 1 file or a strip file, process the primary image file
            primary_file = files[0]
            for f in files:
                if "_strip" in f.lower():
                    primary_file = f
                    break
            full_img_path = os.path.join(target_path, primary_file)
            return cls._load_frames_from_image_file(full_img_path, cols, rows, frame_width, frame_height)

        except Exception as e:
            print(f"Error loading animation frames from {target_path}: {e}")

        return frames

    @classmethod
    def _load_frames_from_image_file(cls, img_path, cols=None, rows=None, frame_width=None, frame_height=None):
        sheet_surf = cls.get_texture(img_path)
        w, h = sheet_surf.get_size()

        # Check for explicit arguments
        if cols is not None or rows is not None or frame_width is not None or frame_height is not None:
            return cls.slice_spritesheet(sheet_surf, cols=cols, rows=rows, frame_width=frame_width, frame_height=frame_height)

        # Check sidecar JSON metadata (e.g., path.json or config.json)
        json_candidates = [img_path + ".json", os.path.splitext(img_path)[0] + ".json", os.path.join(os.path.dirname(img_path), "config.json")]
        import json
        for jpath in json_candidates:
            if os.path.exists(jpath):
                try:
                    with open(jpath, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    c = meta.get("cols")
                    r = meta.get("rows")
                    fw = meta.get("frame_width")
                    fh = meta.get("frame_height")
                    if c is not None or r is not None or fw is not None or fh is not None:
                        return cls.slice_spritesheet(sheet_surf, cols=c, rows=r, frame_width=fw, frame_height=fh)
                except Exception:
                    pass

        # Check filename pattern for strip count (e.g. _strip8.png or _strip50.png)
        base = os.path.basename(img_path)
        strip_match = re.search(r'_strip(\d+)', base, re.IGNORECASE)
        if strip_match:
            c = int(strip_match.group(1))
            return cls.slice_spritesheet(sheet_surf, cols=c, rows=1)

        # Auto-detect square frame strip if width is multiple of height or height multiple of width
        if w > h and h > 0 and w % h == 0:
            return cls.slice_spritesheet(sheet_surf, cols=w // h, rows=1)
        elif h > w and w > 0 and h % w == 0:
            return cls.slice_spritesheet(sheet_surf, cols=1, rows=h // w)

        # Fallback: single frame
        return [sheet_surf]

    @classmethod
    def clear(cls):
        cls._textures.clear()
        cls._sounds.clear()
        cls._fonts.clear()
