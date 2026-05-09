"""Prompt builder for sprite generation with magenta background constraints."""

from .config import ASSET_TYPES, ANIMATION_MODES, GRID_PRESETS


# Base style rules that all prompts must include
_BG_CONSTRAINT = (
    "Background is 100% solid flat magenta (#FF00FF), no gradients, no shadows. "
)

_NO_TEXT_RULE = "NO text, NO labels, NO words, NO letters, NO UI elements anywhere."

_STYLE_TEMPLATES = {
    "pixel_art": (
        "Pixel art style with strong outlines, saturated colors, "
        "clean edges suitable for game sprites. "
    ),
    "hd_clean": (
        "Clean HD 2D art style, smooth lines, vibrant colors, "
        "game-ready quality. "
    ),
    "retro_16bit": (
        "16-bit retro pixel art style, limited palette, chunky pixels, "
        "nostalgic SNES/Genesis era look. "
    ),
}

_GRID_RULES = (
    "ABSOLUTE RULES: "
    "1. EXACTLY {total} equal cells arranged in a {rows}x{cols} grid. "
    "2. NO borders, NO lines, NO frames between cells. "
    "3. Each sprite fills ~70% of its cell with consistent size across all cells. "
    "4. Cells connected only by magenta background. "
)

_ANIMATION_DESCRIPTIONS = {
    "idle": [
        "neutral idle pose, calm but alert",
        "subtle breath or sway animation",
        "idle shift in weight or aura",
        "strongest idle accent before loop",
    ],
    "walk": [
        "walking, right leg forward",
        "walking, legs mid-stride",
        "walking, left leg forward",
        "walking, legs passing pose",
    ],
    "run": [
        "running, full stride forward",
        "running, legs gathered",
        "running, opposite stride",
        "running, mid-air moment",
    ],
    "attack": [
        "attack wind-up, gathering force",
        "attack strike, peak impact",
        "attack follow-through",
        "return to ready stance",
    ],
    "death": [
        "hit reaction, stagger",
        "falling, losing balance",
        "collapsed on ground",
        "fading out or dissolving",
    ],
    "jump": [
        "crouch before jump",
        "ascending, legs tucked",
        "peak of jump, spread",
        "descending, legs ready to land",
    ],
    "cast": [
        "casting preparation, hands raised",
        "energy gathering, glow visible",
        "spell release, maximum effect",
        "cooldown, returning to stance",
    ],
}


def get_style_options() -> list[str]:
    """Return available style preset names."""
    return list(_STYLE_TEMPLATES.keys())


def build_prompt(
    subject: str,
    asset_type: str = "creature",
    mode: str = "idle",
    grid: str = "1x4",
    style: str = "pixel_art",
    extra_instructions: str = "",
) -> str:
    """
    Build an optimized prompt for sprite generation.

    Args:
        subject: What to generate (e.g. "fire dragon", "knight warrior").
        asset_type: Type of asset (creature, humanoid, prop, etc.).
        mode: Animation mode (idle, walk, attack, etc.).
        grid: Grid layout as "RxC" string (e.g. "1x4", "2x2").
        style: Visual style preset name.
        extra_instructions: Additional user instructions.

    Returns:
        Complete prompt string ready for image generation.
    """
    # Parse grid
    if grid in GRID_PRESETS:
        rows, cols = GRID_PRESETS[grid]
    else:
        parts = grid.lower().split("x")
        rows, cols = int(parts[0]), int(parts[1])

    total = rows * cols

    # Build style section
    style_text = _STYLE_TEMPLATES.get(style, _STYLE_TEMPLATES["pixel_art"])

    # Single sprite (no grid)
    if total == 1:
        prompt = (
            f"Single 2D game sprite of {subject}. "
            f"Asset type: {asset_type}. "
            f"Centered in frame, facing right. "
            f"{style_text}"
            f"{_BG_CONSTRAINT}"
            f"{_NO_TEXT_RULE}"
        )
        if extra_instructions:
            prompt += f" {extra_instructions}"
        return prompt

    # Multi-frame sprite sheet
    grid_rules = _GRID_RULES.format(total=total, rows=rows, cols=cols)

    # Build frame descriptions
    frame_descs = ""
    anim_frames = _ANIMATION_DESCRIPTIONS.get(mode)
    if anim_frames:
        # Use as many descriptions as we have cells
        for i in range(min(total, len(anim_frames))):
            frame_descs += f"Cell {i + 1}: {anim_frames[i]}. "
        # If more cells than descriptions, repeat last frames
        for i in range(len(anim_frames), total):
            idx = i % len(anim_frames)
            frame_descs += f"Cell {i + 1}: {anim_frames[idx]}. "
    else:
        frame_descs = f"{total} poses/variations of the same {subject}. "

    prompt = (
        f"A {rows}x{cols} sprite sheet of {subject} ({asset_type}, {mode} animation). "
        f"{frame_descs}"
        f"SAME character, SAME size, SAME facing direction, SAME color palette in all cells. "
        f"{style_text}"
        f"{_BG_CONSTRAINT}"
        f"{grid_rules}"
        f"{_NO_TEXT_RULE}"
    )

    if extra_instructions:
        prompt += f" {extra_instructions}"

    return prompt
