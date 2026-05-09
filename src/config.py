"""Configuration loading and defaults."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Default provider
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openai")

# Output directory
OUTPUT_DIR = _project_root / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Image generation defaults
DEFAULT_IMAGE_SIZE = "1024x1024"

# Post-processing defaults
BG_COLOR_MAGENTA = (255, 0, 255)
BG_DISTANCE_THRESHOLD = 100
EDGE_CLEAN_THRESHOLD = 150
DEFAULT_CELL_SIZE = 128
GIF_FRAME_DURATION_MS = 150

# Asset types
ASSET_TYPES = ["creature", "humanoid", "prop", "tile", "ui_element", "effect"]

# Animation modes
ANIMATION_MODES = ["idle", "walk", "run", "attack", "death", "jump", "cast"]

# Grid presets (rows x cols)
GRID_PRESETS = {
    "1x1": (1, 1),
    "1x4": (1, 4),
    "1x6": (1, 6),
    "1x8": (1, 8),
    "2x4": (2, 4),
    "3x4": (3, 4),
    "4x4": (4, 4),
}
