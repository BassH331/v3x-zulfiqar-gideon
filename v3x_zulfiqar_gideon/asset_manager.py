import pygame
import os
import re
from typing import Optional, List, Dict, Tuple

class AssetManager:
    _instance = None
    _textures = {}
    _sounds = {}
    _fonts = {}
    _animation_frames_cache = {}

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

    KNOWN_SPRITESHEET_GRIDS: Dict[str, Tuple[int, int]] = {
        "large skull.png": (10, 4),
        "memento mori skeleton.png": (4, 4),
        "large statue.png": (1, 1),
        "large statue 2.png": (1, 1),
        "male damned.png": (8, 4),
        "male damned covered.png": (8, 4),
        "female damned.png": (8, 4),
        "female damned covered.png": (8, 4),
        "burning damned.png": (8, 4),
        "burning damned blue.png": (8, 4),
        "twisted damned.png": (8, 4),
        "imp.png": (10, 5),
        "bloated damned.png": (8, 3),
        "tree damned.png": (7, 2),
        "demon eye.png": (7, 2),
        "flying demon head.png": (2, 2),
        "the devil.png": (6, 5),
        "old demon.png": (7, 1),
        "old demon covered.png": (7, 1),
        "demon mine.png": (7, 2),
        "plague flies.png": (5, 2),
        "pot_frames.png": (2, 2),
        "statue_frames.png": (6, 1),
        "totem.png": (6, 1),
        "fire sheet.png": (6, 1),
        "blue fire sheet.png": (6, 1),
        "spr_roninattack_strip33.png": (25, 1),
        "spr_roninattackalt_strip.png": (25, 1),
    }

    COMMON_CELL_SIZES = (32, 16, 24, 48, 64, 128)
    MAX_AUTO_FRAMES = 1024

    @classmethod
    def resolve_path(cls, path: str) -> str:
        """Resolve file path case-insensitively on Linux and other case-sensitive filesystems."""
        if not path or os.path.exists(path):
            return path
        try:
            norm = os.path.normpath(path)
            parts = norm.split(os.sep)
            current = "." if not os.path.isabs(norm) else os.sep
            for part in parts:
                if not part or part == ".":
                    continue
                if not os.path.isdir(current):
                    return path
                candidates = os.listdir(current)
                part_lower = part.lower()
                matched = False
                for c in candidates:
                    if c.lower() == part_lower:
                        current = os.path.join(current, c)
                        matched = True
                        break
                if not matched:
                    return path
            return current if os.path.exists(current) else path
        except Exception:
            return path

    @classmethod
    def get_texture(cls, path, silent=False):
        path = cls.resolve_path(path)
        if not path:
            surf = pygame.Surface((32, 32))
            surf.fill((255, 0, 255))
            return surf

        if path not in cls._textures:
            ext = os.path.splitext(path)[1].lower()
            if ext and ext not in cls.SUPPORTED_EXTENSIONS:
                # Unsupported file formats (.ase, .aseprite, .txt, etc.) return placeholder without error spam
                surf = pygame.Surface((32, 32))
                surf.fill((255, 0, 255))
                cls._textures[path] = surf
                return surf

            try:
                raw_surf = pygame.image.load(path)
                try:
                    cls._textures[path] = raw_surf.convert_alpha()
                except pygame.error:
                    # Headless mode without display surface set; retain unconverted surface safely
                    cls._textures[path] = raw_surf
            except Exception as e:
                if not silent:
                    print(f"Error loading texture {path}: {e}")
                surf = pygame.Surface((32, 32))
                surf.fill((255, 0, 255))
                cls._textures[path] = surf
                return surf
        return cls._textures[path]

    @classmethod
    def get_sound(cls, path):
        path = cls.resolve_path(path)
        if path not in cls._sounds:
            try:
                cls._sounds[path] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Error loading sound {path}: {e}")
                return None
        return cls._sounds[path]

    @classmethod
    def clear(cls):
        """Clear all cached surfaces, sounds, fonts, and animation frame sequences."""
        cls._textures.clear()
        cls._sounds.clear()
        cls._fonts.clear()
        cls._animation_frames_cache.clear()

    @classmethod
    def get_font(cls, path, size):
        if not pygame.font.get_init():
            try:
                pygame.font.init()
            except Exception:
                pass
            cls._fonts.clear()

        path = cls.resolve_path(path)
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
        """Slice a Pygame surface into a list of frame subsurfaces with robust bounds checking."""
        frames = []
        if not isinstance(surface, pygame.Surface):
            return frames
        w, h = surface.get_size()
        if w <= 0 or h <= 0:
            return frames

        try:
            if cols is not None or rows is not None:
                c = max(1, int(cols) if cols is not None else 1)
                r = max(1, int(rows) if rows is not None else 1)
                fw = max(1, int(w // c))
                fh = max(1, int(h // r))
            elif frame_width is not None or frame_height is not None:
                raw_fw = int(frame_width) if frame_width is not None else w
                raw_fh = int(frame_height) if frame_height is not None else h
                if raw_fw <= 0 or raw_fh <= 0:
                    return [surface]
                fw = max(1, min(w, raw_fw))
                fh = max(1, min(h, raw_fh))
                c = max(1, int(w // fw))
                r = max(1, int(h // fh))
            else:
                return [surface]
        except (ValueError, TypeError, ArithmeticError, OverflowError):
            return [surface]

        for row_idx in range(r):
            sy = int(row_idx * fh)
            if sy >= h:
                break
            for col_idx in range(c):
                sx = int(col_idx * fw)
                if sx >= w:
                    break
                sw = min(fw, w - sx)
                sh = min(fh, h - sy)
                if sw <= 0 or sh <= 0:
                    continue
                try:
                    rect = pygame.Rect(sx, sy, sw, sh)
                    frames.append(surface.subsurface(rect).copy())
                except Exception:
                    pass

        return frames if frames else [surface]

    @classmethod
    def is_multi_sheet_directory(cls, dir_path: str) -> bool:
        """
        Determine if dir_path is a multi-sheet container directory (catalog of disparate entity sheets)
        rather than a single animated entity's frames folder.
        """
        resolved = cls.resolve_path(dir_path)
        if not resolved or not os.path.isdir(resolved):
            return False

        base = os.path.basename(resolved.rstrip("/\\")).lower()
        # Direct signals that this is an animation frames folder
        if base.endswith("_frames") or base.endswith("_anim") or base in (
            "frames", "idle", "run", "walk", "jump", "attack", "death", "die", "spawn", "hurt", "gethit", "chase", "anim"
        ):
            return False

        try:
            items = os.listdir(resolved)
        except Exception:
            return False

        subdirs = [d for d in items if os.path.isdir(os.path.join(resolved, d))]
        image_files = [
            f for f in items
            if os.path.isfile(os.path.join(resolved, f)) and f.lower().endswith(('.png', '.jpg', '.webp'))
        ]

        # Signal A: Contains child directories ending in _frames
        if any(d.lower().endswith("_frames") for d in subdirs):
            return True

        # Signal B: Contains images whose companion {stem}_frames directories exist
        subdirs_lower = {d.lower() for d in subdirs}
        if any(f"{os.path.splitext(f)[0]}_frames".lower() in subdirs_lower for f in image_files):
            return True

        if len(image_files) <= 1:
            return False

        # Signal C: Check if images are sequentially numbered frames of a single animation
        seq_matches = [
            re.match(r'^(.*?)[_ \-]?(\d+)\.(png|jpg|webp)$', f, re.IGNORECASE)
            for f in image_files
        ]
        if all(m is not None for m in seq_matches):
            prefixes = {m.group(1).lower() for m in seq_matches if m}
            if len(prefixes) <= 1:
                return False  # All files share a single sequence stem

        return True

    @classmethod
    def list_entities(cls, dir_path: str) -> list[str]:
        """Discover and list all unique entity names available inside a multi-sheet container directory."""
        resolved = cls.resolve_path(dir_path)
        if not resolved or not os.path.isdir(resolved):
            return []

        try:
            items = os.listdir(resolved)
        except Exception:
            return []

        entities = set()
        for item in items:
            full_p = os.path.join(resolved, item)
            if os.path.isdir(full_p) and item.lower().endswith("_frames"):
                entity_name = item[:-7]  # strip _frames suffix
                entities.add(entity_name)
            elif os.path.isfile(full_p):
                stem, ext = os.path.splitext(item)
                if ext.lower() in cls.SUPPORTED_EXTENSIONS:
                    entities.add(stem)

        def _natural_key(name):
            return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', name)]

        return sorted(list(entities), key=_natural_key)

    @classmethod
    def get_entity_animation_frames(cls, container_path: str, entity_name: str, cols=None, rows=None, frame_width=None, frame_height=None):
        """Load animation frames for a specific entity inside a multi-sheet container folder."""
        container_path = cls.resolve_path(container_path)
        if not container_path or not os.path.isdir(container_path) or not entity_name:
            return []

        target_lower = entity_name.strip().lower()
        try:
            items = os.listdir(container_path)
        except Exception:
            return []

        # 1. Prefer dedicated _frames directory if it yields frames
        for item in items:
            if item.lower() == f"{target_lower}_frames" and os.path.isdir(os.path.join(container_path, item)):
                frames = cls.get_animation_frames(
                    os.path.join(container_path, item),
                    cols=cols, rows=rows, frame_width=frame_width, frame_height=frame_height
                )
                if frames:
                    return frames

        # 2. Look for matching image sheet file
        for item in items:
            stem, ext = os.path.splitext(item)
            if stem.lower() == target_lower and ext.lower() in cls.SUPPORTED_EXTENSIONS:
                frames = cls.get_animation_frames(
                    os.path.join(container_path, item),
                    cols=cols, rows=rows, frame_width=frame_width, frame_height=frame_height
                )
                if frames:
                    return frames

        return []

    @classmethod
    def get_animation_frames(cls, target_path, cols=None, rows=None, frame_width=None, frame_height=None, entity_name=None):
        """
        Load animation frames from a directory of PNGs, a multi-sheet container folder, or a single sprite sheet image.
        Supports entity_name parameter to resolve a specific entity within a multi-sheet container folder.
        """
        target_path = cls.resolve_path(target_path)
        if not target_path or not os.path.exists(target_path):
            print(f"Error: Path not found {target_path}")
            return []

        cache_key = (target_path, cols, rows, frame_width, frame_height, entity_name)
        if cache_key in cls._animation_frames_cache:
            return cls._animation_frames_cache[cache_key]

        frames = []
        try:
            # Handle single image file directly
            if os.path.isfile(target_path):
                frames = cls._load_frames_from_image_file(target_path, cols, rows, frame_width, frame_height)
                cls._animation_frames_cache[cache_key] = frames
                return frames

            # Handle directory with specific entity_name
            if entity_name:
                frames = cls.get_entity_animation_frames(
                    target_path, entity_name, cols=cols, rows=rows, frame_width=frame_width, frame_height=frame_height
                )
                cls._animation_frames_cache[cache_key] = frames
                return frames

            # Check if this is a multi-sheet container folder
            if cls.is_multi_sheet_directory(target_path):
                cls._animation_frames_cache[cache_key] = []
                return []

            def _natural_key(name):
                return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', name)]

            files = sorted(
                [f for f in os.listdir(target_path) if f.lower().endswith(('.png', '.jpg', '.webp'))],
                key=_natural_key,
            )

            if not files:
                cls._animation_frames_cache[cache_key] = []
                return []

            is_frame_dir = any(
                "frame_" in f.lower() or "_strip" in f.lower() for f in files
            ) or target_path.rstrip("/\\").endswith("_frames") or not cls.is_multi_sheet_directory(target_path)

            if is_frame_dir and len(files) > 1 and not any("_strip" in f.lower() for f in files):
                for f in files:
                    path = os.path.join(target_path, f)
                    frames.append(cls.get_texture(path))
                cls._animation_frames_cache[cache_key] = frames
                return frames

            primary_file = files[0]
            for f in files:
                if "_strip" in f.lower():
                    primary_file = f
                    break
            full_img_path = os.path.join(target_path, primary_file)
            frames = cls._load_frames_from_image_file(full_img_path, cols, rows, frame_width, frame_height)

        except Exception as e:
            print(f"Error loading animation frames from {target_path}: {e}")

        cls._animation_frames_cache[cache_key] = frames
        return frames

    @classmethod
    def _load_frames_from_image_file(cls, img_path, cols=None, rows=None, frame_width=None, frame_height=None):
        """
        Load and slice frames from an image file using sidecar JSON, companion directories,
        known grid mappings, regex dimensions, and 2D grid auto-slicing heuristics.
        """
        sheet_surf = cls.get_texture(img_path)
        w, h = sheet_surf.get_size()

        if w <= 0 or h <= 0:
            return []

        # Do not slice fallback placeholder magenta surface
        if w == 32 and h == 32:
            try:
                if (sheet_surf.get_at((0, 0))[:3] == (255, 0, 255) and
                    sheet_surf.get_at((w - 1, h - 1))[:3] == (255, 0, 255) and
                    sheet_surf.get_at((w // 2, h // 2))[:3] == (255, 0, 255)):
                    return []
            except Exception:
                pass

        # 1. Explicit arguments
        if cols is not None or rows is not None or frame_width is not None or frame_height is not None:
            return cls.slice_spritesheet(sheet_surf, cols=cols, rows=rows, frame_width=frame_width, frame_height=frame_height)

        raw_name = os.path.splitext(os.path.basename(img_path))[0]
        base_name = os.path.basename(img_path)
        base_lower = base_name.lower()
        dir_name = os.path.dirname(img_path)

        # 2. Known grid mappings
        if base_lower in cls.KNOWN_SPRITESHEET_GRIDS:
            kc, kr = cls.KNOWN_SPRITESHEET_GRIDS[base_lower]
            return cls.slice_spritesheet(sheet_surf, cols=kc, rows=kr)

        # 3. Check sidecar JSON metadata (including companion _frames/config.json)
        json_candidates = [
            img_path + ".json",
            os.path.splitext(img_path)[0] + ".json",
            os.path.join(dir_name, f"{raw_name}_frames", "config.json"),
            os.path.join(dir_name, "config.json")
        ]
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
                    # Use sidecar if it specifies genuine multi-frame slicing
                    try:
                        c_val = int(c) if c is not None else None
                    except (ValueError, TypeError):
                        c_val = None
                    try:
                        r_val = int(r) if r is not None else None
                    except (ValueError, TypeError):
                        r_val = None
                    try:
                        fw_val = int(fw) if fw is not None else None
                    except (ValueError, TypeError):
                        fw_val = None
                    try:
                        fh_val = int(fh) if fh is not None else None
                    except (ValueError, TypeError):
                        fh_val = None

                    is_valid_slice = (
                        (c_val is not None and 1 < c_val <= cls.MAX_AUTO_FRAMES) or
                        (r_val is not None and 1 < r_val <= cls.MAX_AUTO_FRAMES) or
                        (fw_val is not None and 0 < fw_val < w) or
                        (fh_val is not None and 0 < fh_val < h)
                    )
                    calc_c = c_val if c_val is not None else (max(1, w // fw_val) if fw_val and fw_val > 0 else 1)
                    calc_r = r_val if r_val is not None else (max(1, h // fh_val) if fh_val and fh_val > 0 else 1)
                    if is_valid_slice and (calc_c * calc_r <= cls.MAX_AUTO_FRAMES):
                        return cls.slice_spritesheet(sheet_surf, cols=c_val, rows=r_val, frame_width=fw_val, frame_height=fh_val)
                except Exception:
                    pass

        # 4. Check if companion _frames directory contains pre-sliced frames
        companion_frames_dir = os.path.join(dir_name, f"{raw_name}_frames")
        if os.path.isdir(companion_frames_dir):
            try:
                frame_files = [
                    f for f in os.listdir(companion_frames_dir)
                    if f.lower().endswith(('.png', '.jpg', '.webp'))
                ]
                if len(frame_files) > 1:
                    def _nat(n): return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', n)]
                    frame_files.sort(key=_nat)
                    return [cls.get_texture(os.path.join(companion_frames_dir, f)) for f in frame_files]
            except Exception:
                pass

        # 5. Check filename pattern for horizontal strip count (e.g. _strip8.png or _strip50.png)
        strip_match = re.search(r'_strip(\d+)', base_name, re.IGNORECASE)
        if strip_match:
            c = int(strip_match.group(1))
            return cls.slice_spritesheet(sheet_surf, cols=c, rows=1)

        # Check filename pattern for vertical strip count (e.g. _vstrip4.png)
        vstrip_match = re.search(r'_vstrip(\d+)', base_name, re.IGNORECASE)
        if vstrip_match:
            r = int(vstrip_match.group(1))
            return cls.slice_spritesheet(sheet_surf, cols=1, rows=r)

        # 6. Check for explicit grid pattern in filename (e.g. _grid4x4 or grid_10x4)
        grid_match = re.search(r'(?:grid|cells?)_?(\d+)[xX](\d+)', base_name, re.IGNORECASE)
        if grid_match:
            gc, gr = int(grid_match.group(1)), int(grid_match.group(2))
            if gc > 0 and gr > 0 and w % gc == 0 and h % gr == 0 and (gc * gr <= cls.MAX_AUTO_FRAMES):
                return cls.slice_spritesheet(sheet_surf, cols=gc, rows=gr)

        # 7. Check for dimension pattern (\d+)x(\d+) in filename (e.g. "Hell Tiles 32x32.png")
        dim_match = re.search(r'(\d+)\s*[xX]\s*(\d+)', base_name, re.IGNORECASE)
        if dim_match:
            d1, d2 = int(dim_match.group(1)), int(dim_match.group(2))
            if d1 > 0 and d2 > 0 and w % d1 == 0 and h % d2 == 0:
                c_cand = w // d1
                r_cand = h // d2
                if (c_cand > 1 or r_cand > 1) and (c_cand * r_cand <= cls.MAX_AUTO_FRAMES):
                    return cls.slice_spritesheet(sheet_surf, cols=c_cand, rows=r_cand, frame_width=d1, frame_height=d2)

        # 8. Check for dimension pattern in parent directory (leaf to root)
        cur = os.path.dirname(os.path.abspath(img_path))
        while cur and cur != os.path.dirname(cur):
            parent_match = re.search(r'(\d+)\s*[xX]\s*(\d+)', os.path.basename(cur), re.IGNORECASE)
            if parent_match:
                d1, d2 = int(parent_match.group(1)), int(parent_match.group(2))
                if d1 > 0 and d2 > 0 and w % d1 == 0 and h % d2 == 0:
                    c_cand = w // d1
                    r_cand = h // d2
                    if (c_cand > 1 or r_cand > 1) and (c_cand * r_cand <= cls.MAX_AUTO_FRAMES):
                        return cls.slice_spritesheet(sheet_surf, cols=c_cand, rows=r_cand, frame_width=d1, frame_height=d2)
            cur = os.path.dirname(cur)

        # 9. Auto-detect square frame strip if width is multiple of height or height multiple of width
        if w > h and h > 0 and w % h == 0:
            return cls.slice_spritesheet(sheet_surf, cols=w // h, rows=1)
        elif h > w and w > 0 and h % w == 0:
            return cls.slice_spritesheet(sheet_surf, cols=1, rows=h // w)

        # 10. Auto-detect common square cell sizes (32, 16, 24, 48, 64, 128) for square sheets
        if w == h and w >= 64:
            for cs in cls.COMMON_CELL_SIZES:
                if w % cs == 0:
                    c_cand = w // cs
                    r_cand = h // cs
                    if (c_cand > 1 or r_cand > 1) and (c_cand * r_cand <= cls.MAX_AUTO_FRAMES):
                        return cls.slice_spritesheet(sheet_surf, cols=c_cand, rows=r_cand, frame_width=cs, frame_height=cs)

        # 11. Fallback: single frame
        return [sheet_surf]
