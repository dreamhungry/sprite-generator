"""Export utilities: compose sheet, save GIF, save individual frames."""

from pathlib import Path

import numpy as np
from PIL import Image

from ..config import GIF_FRAME_DURATION_MS


def compose_sheet(frames: list[Image.Image], rows: int, cols: int, cell_size: int) -> Image.Image:
    """
    Compose aligned frames back into a transparent sprite sheet.

    Args:
        frames: List of aligned frame images (cell_size x cell_size).
        rows: Number of rows in the sheet.
        cols: Number of columns in the sheet.
        cell_size: Size of each cell.

    Returns:
        Composed sprite sheet image.
    """
    canvas = Image.new("RGBA", (cols * cell_size, rows * cell_size), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        row, col = divmod(index, cols)
        if row >= rows:
            break
        canvas.paste(frame, (col * cell_size, row * cell_size), frame)
    return canvas


def save_gif(
    frames: list[Image.Image],
    output_path: Path | str,
    duration: int = GIF_FRAME_DURATION_MS,
) -> Path:
    """
    Save frames as a transparent animated GIF.

    Uses palette-based transparency with a chroma key approach.

    Args:
        frames: List of RGBA frame images.
        output_path: Path to save the GIF.
        duration: Frame duration in milliseconds.

    Returns:
        Path to the saved GIF.
    """
    output_path = Path(output_path)

    if not frames:
        raise ValueError("No frames to save as GIF")

    # Transparency key color (near-magenta but distinguishable)
    key = (255, 0, 254)
    width, height = frames[0].size

    # Stack all frames vertically for unified palette quantization
    stacked = Image.new("RGB", (width, height * len(frames)), key)

    for index, frame in enumerate(frames):
        r, g, b, a = frame.split()
        hard_mask = a.point(lambda v: 255 if v >= 128 else 0)
        rgb = Image.merge("RGB", (r, g, b))
        stacked.paste(rgb, (0, index * height), hard_mask)

    # Convert to paletted image
    paletted = stacked.convert("P", palette=Image.Palette.ADAPTIVE, colors=256, dither=Image.Dither.NONE)
    palette = list(paletted.getpalette() or [])
    while len(palette) < 256 * 3:
        palette.append(0)

    # Find the key color index in palette
    key_index = None
    for i in range(256):
        if palette[i * 3: i * 3 + 3] == list(key):
            key_index = i
            break

    if key_index is None:
        # Find closest color to key
        best_dist = None
        best_idx = 0
        for i in range(256):
            r, g, b = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
            dist = (r - key[0]) ** 2 + (g - key[1]) ** 2 + (b - key[2]) ** 2
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_idx = i
        key_index = best_idx

    # Swap key to index 0 for transparency
    if key_index != 0:
        lut = np.arange(256, dtype=np.uint8)
        lut[0], lut[key_index] = key_index, 0
        arr = np.array(paletted)
        arr = lut[arr]
        paletted = Image.fromarray(arr, mode="P")
        for ch in range(3):
            zero_idx = ch
            key_idx = key_index * 3 + ch
            palette[zero_idx], palette[key_idx] = palette[key_idx], palette[zero_idx]
        paletted.putpalette(palette)

    # Split back into individual frames
    out_frames = [
        paletted.crop((0, i * height, width, (i + 1) * height))
        for i in range(len(frames))
    ]

    # Save as animated GIF
    out_frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=out_frames[1:],
        duration=duration,
        loop=0,
        disposal=2,
        transparency=0,
        background=0,
    )

    return output_path


def save_frames(
    frames: list[Image.Image],
    output_dir: Path | str,
    prefix: str = "frame",
) -> list[Path]:
    """
    Save individual frame PNGs to a directory.

    Args:
        frames: List of frame images.
        output_dir: Directory to save frames.
        prefix: Filename prefix.

    Returns:
        List of saved file paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for i, frame in enumerate(frames):
        path = output_dir / f"{prefix}_{i:03d}.png"
        frame.save(path, format="PNG")
        paths.append(path)

    return paths
