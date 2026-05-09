"""Frame alignment and scaling utilities."""

from PIL import Image

from ..config import DEFAULT_CELL_SIZE


def shared_scale_frames(
    frames: list[Image.Image],
    cell_size: int = DEFAULT_CELL_SIZE,
    fit_scale: float = 0.85,
) -> float:
    """
    Compute a shared scale factor so all frames fit uniformly into cell_size.

    Returns the common scale factor.
    """
    max_width = max((f.size[0] for f in frames if f.size[0] > 0), default=1)
    max_height = max((f.size[1] for f in frames if f.size[1] > 0), default=1)
    return min(cell_size / max_width, cell_size / max_height) * fit_scale


def align_frames(
    frames: list[Image.Image],
    cell_size: int = DEFAULT_CELL_SIZE,
    align: str = "center",
    use_shared_scale: bool = True,
    fit_scale: float = 0.85,
) -> list[Image.Image]:
    """
    Scale and align frames into uniform cell_size x cell_size canvases.

    Args:
        frames: List of cropped frame images.
        cell_size: Output canvas size (square).
        align: Alignment mode - 'center', 'bottom', or 'feet'.
        use_shared_scale: If True, all frames use the same scale factor.
        fit_scale: Fraction of cell to fill (0.0-1.0).

    Returns:
        List of aligned frame images on transparent canvases.
    """
    if not frames:
        return []

    # Compute scale factor
    if use_shared_scale:
        common_scale = shared_scale_frames(frames, cell_size, fit_scale)
    else:
        common_scale = None

    aligned: list[Image.Image] = []
    for frame in frames:
        canvas = Image.new("RGBA", (cell_size, cell_size), (0, 0, 0, 0))
        fw, fh = frame.size
        if fw == 0 or fh == 0:
            aligned.append(canvas)
            continue

        if common_scale is not None:
            scale = common_scale
        else:
            scale = min(cell_size / fw, cell_size / fh) * fit_scale

        new_w = max(1, int(fw * scale))
        new_h = max(1, int(fh * scale))
        resized = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Horizontal: always centered
        paste_x = (cell_size - new_w) // 2

        # Vertical: depends on align mode
        if align in ("bottom", "feet"):
            pad = max(0, int(cell_size * (1 - fit_scale) * 0.5))
            paste_y = cell_size - new_h - pad
        else:
            paste_y = (cell_size - new_h) // 2

        canvas.paste(resized, (paste_x, paste_y), resized)
        aligned.append(canvas)

    return aligned
