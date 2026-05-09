"""Grid splitting, trimming, and connected component analysis."""

from collections import deque

from PIL import Image

from ..config import DEFAULT_CELL_SIZE


def trim_border(img: Image.Image, px: int = 4) -> Image.Image:
    """Trim px pixels from all edges."""
    width, height = img.size
    if width > px * 2 and height > px * 2:
        return img.crop((px, px, width - px, height - px))
    return img


def clean_edges(img: Image.Image, depth: int = 3) -> Image.Image:
    """Remove dark or near-magenta pixels at content edges."""
    import math

    pixels = img.load()
    width, height = img.size

    for d in range(depth):
        for x in range(width):
            for y in (d, height - 1 - d):
                if y < 0 or y >= height:
                    continue
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                is_dark = r < 40 and g < 40 and b < 40
                is_near_magenta = math.sqrt((r - 255) ** 2 + g ** 2 + (b - 255) ** 2) < 150
                if is_dark or is_near_magenta:
                    pixels[x, y] = (0, 0, 0, 0)
        for y in range(height):
            for x in (d, width - 1 - d):
                if x < 0 or x >= width:
                    continue
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                is_dark = r < 40 and g < 40 and b < 40
                is_near_magenta = math.sqrt((r - 255) ** 2 + g ** 2 + (b - 255) ** 2) < 150
                if is_dark or is_near_magenta:
                    pixels[x, y] = (0, 0, 0, 0)
    return img


def connected_components(img: Image.Image, min_area: int = 1) -> list[dict]:
    """
    Find connected components in an RGBA image based on alpha channel.
    Returns list of dicts with 'area', 'bbox', 'touches_edge' sorted by area desc.
    """
    alpha = img.getchannel("A")
    pixels = alpha.load()
    width, height = img.size
    visited = [[False] * width for _ in range(height)]
    components: list[dict] = []

    for y in range(height):
        for x in range(width):
            if pixels[x, y] == 0 or visited[y][x]:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited[y][x] = True
            area = 0
            min_x = max_x = x
            min_y = max_y = y
            touches_edge = x == 0 or y == 0 or x == width - 1 or y == height - 1

            while queue:
                cx, cy = queue.popleft()
                area += 1
                min_x = min(min_x, cx)
                min_y = min(min_y, cy)
                max_x = max(max_x, cx)
                max_y = max(max_y, cy)
                if cx == 0 or cy == 0 or cx == width - 1 or cy == height - 1:
                    touches_edge = True
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height and pixels[nx, ny] > 0 and not visited[ny][nx]:
                        visited[ny][nx] = True
                        queue.append((nx, ny))

            if area >= min_area:
                components.append({
                    "area": area,
                    "bbox": (min_x, min_y, max_x + 1, max_y + 1),
                    "touches_edge": touches_edge,
                })

    components.sort(key=lambda c: c["area"], reverse=True)
    return components


def split_grid(
    img: Image.Image,
    rows: int,
    cols: int,
    cell_size: int = DEFAULT_CELL_SIZE,
    trim_px: int = 4,
    edge_depth: int = 3,
    component_mode: str = "all",
    min_component_area: int = 50,
) -> list[Image.Image]:
    """
    Split an RGBA image into a grid of frames.

    Args:
        img: Source image (should already have background removed).
        rows: Number of rows in the grid.
        cols: Number of columns in the grid.
        cell_size: Output size for each frame (square).
        trim_px: Pixels to trim from each cell border.
        edge_depth: Depth for edge cleaning pass.
        component_mode: 'all' keeps full bbox, 'largest' keeps only largest component.
        min_component_area: Min pixel area for a component to be considered.

    Returns:
        List of cropped frame images (not yet aligned/scaled).
    """
    width, height = img.size
    cell_width = width // cols
    cell_height = height // rows
    frames: list[Image.Image] = []

    for row in range(rows):
        for col in range(cols):
            box = (col * cell_width, row * cell_height,
                   (col + 1) * cell_width, (row + 1) * cell_height)
            frame = img.crop(box)

            if trim_px > 0:
                frame = trim_border(frame, px=trim_px)

            if edge_depth > 0:
                frame = clean_edges(frame, depth=edge_depth)

            # Isolate content via component analysis
            components = connected_components(frame, min_area=min_component_area)
            if component_mode == "largest" and components:
                bbox = components[0]["bbox"]
            else:
                bbox = frame.getbbox()

            if bbox:
                frame = frame.crop(bbox)

            frames.append(frame)

    return frames
