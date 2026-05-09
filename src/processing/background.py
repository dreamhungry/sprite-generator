"""Background removal using magenta chroma-key with flood-fill edge diffusion."""

import math
from collections import deque

import numpy as np
from PIL import Image

from ..config import BG_COLOR_MAGENTA, BG_DISTANCE_THRESHOLD, EDGE_CLEAN_THRESHOLD


def color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """Euclidean distance between two RGB colors."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def remove_background(
    img: Image.Image,
    bg_color: tuple[int, int, int] = BG_COLOR_MAGENTA,
    threshold: int = BG_DISTANCE_THRESHOLD,
    edge_threshold: int = EDGE_CLEAN_THRESHOLD,
) -> Image.Image:
    """
    Remove background using chroma-key flood-fill from edges.

    Starts from image edges and flood-fills inward, removing pixels
    whose color is within threshold distance of the background color.
    """
    img = img.convert("RGBA")
    pixels = img.load()
    width, height = img.size
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    # Seed from all edge pixels
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        if x < 0 or x >= width or y < 0 or y >= height:
            continue
        visited.add((x, y))

        r, g, b, a = pixels[x, y]
        dist = color_distance((r, g, b), bg_color)

        if dist < threshold:
            pixels[x, y] = (0, 0, 0, 0)
            # Expand to neighbors (8-connected)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in visited:
                        queue.append((nx, ny))

    # Additional pass: remove near-magenta pixels at edges of remaining content
    _clean_edge_residue(img, bg_color, edge_threshold)

    return img


def _clean_edge_residue(
    img: Image.Image,
    bg_color: tuple[int, int, int],
    threshold: int,
    depth: int = 3,
) -> None:
    """Remove residual dark or near-bg pixels at content edges."""
    pixels = img.load()
    width, height = img.size

    for d in range(depth):
        # Top and bottom rows at depth d
        for x in range(width):
            for y in (d, height - 1 - d):
                if y < 0 or y >= height:
                    continue
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                is_dark = r < 40 and g < 40 and b < 40
                is_near_bg = color_distance((r, g, b), bg_color) < threshold
                if is_dark or is_near_bg:
                    pixels[x, y] = (0, 0, 0, 0)
        # Left and right columns at depth d
        for y in range(height):
            for x in (d, width - 1 - d):
                if x < 0 or x >= width:
                    continue
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                is_dark = r < 40 and g < 40 and b < 40
                is_near_bg = color_distance((r, g, b), bg_color) < threshold
                if is_dark or is_near_bg:
                    pixels[x, y] = (0, 0, 0, 0)
