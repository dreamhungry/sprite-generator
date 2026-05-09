"""Generation controller: orchestrates the full pipeline."""

import time
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from .config import DEFAULT_CELL_SIZE, GRID_PRESETS, OUTPUT_DIR
from .processing import remove_background, split_grid, align_frames, compose_sheet, save_gif, save_frames
from .prompt_builder import build_prompt
from .providers import get_provider
from .providers.base import GenerationRequest, GenerationResult


@dataclass
class PipelineResult:
    """Result of the full generation + post-processing pipeline."""

    raw_image: Image.Image
    processed_image: Image.Image  # Background removed
    sheet: Image.Image | None = None
    frames: list[Image.Image] = field(default_factory=list)
    gif_path: Path | None = None
    frame_paths: list[Path] = field(default_factory=list)
    output_dir: Path | None = None
    prompt_used: str = ""
    provider_name: str = ""
    model_name: str = ""
    generation_time: float = 0.0
    processing_time: float = 0.0


def run_pipeline(
    subject: str,
    provider_name: str = "openai",
    asset_type: str = "creature",
    mode: str = "idle",
    grid: str = "1x4",
    style: str = "pixel_art",
    cell_size: int = DEFAULT_CELL_SIZE,
    align: str = "center",
    shared_scale: bool = True,
    component_mode: str = "all",
    reference_image: Image.Image | None = None,
    extra_instructions: str = "",
    image_size: str = "1024x1024",
) -> PipelineResult:
    """
    Run the full sprite generation pipeline.

    1. Build optimized prompt
    2. Call image generation provider
    3. Remove background
    4. Split grid into frames
    5. Align and scale frames
    6. Compose sheet and export GIF

    Args:
        subject: Description of what to generate.
        provider_name: Which provider to use ('openai', 'gemini').
        asset_type: Type of game asset.
        mode: Animation mode.
        grid: Grid layout (e.g. "1x4", "2x2").
        style: Visual style preset.
        cell_size: Output cell size in pixels.
        align: Frame alignment ('center', 'bottom', 'feet').
        shared_scale: Whether to use uniform scaling across frames.
        component_mode: 'all' or 'largest' for component isolation.
        reference_image: Optional reference image for guided generation.
        extra_instructions: Additional prompt instructions.
        image_size: Generation image size.

    Returns:
        PipelineResult with all generated assets.
    """
    # 1. Build prompt
    prompt = build_prompt(
        subject=subject,
        asset_type=asset_type,
        mode=mode,
        grid=grid,
        style=style,
        extra_instructions=extra_instructions,
    )

    # 2. Generate image
    provider = get_provider(provider_name)
    request = GenerationRequest(
        prompt=prompt,
        reference_image=reference_image,
        size=image_size,
        style=style,
    )

    t0 = time.time()
    gen_result: GenerationResult = provider.generate(request)
    generation_time = time.time() - t0

    raw_image = gen_result.image

    # 3. Post-processing
    t1 = time.time()

    # Parse grid
    if grid in GRID_PRESETS:
        rows, cols = GRID_PRESETS[grid]
    else:
        parts = grid.lower().split("x")
        rows, cols = int(parts[0]), int(parts[1])

    total = rows * cols

    # Remove background
    processed = remove_background(raw_image.copy())

    # Setup output directory
    timestamp = int(time.time())
    out_dir = OUTPUT_DIR / f"{subject[:20].replace(' ', '_')}_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    sheet = None
    frames: list[Image.Image] = []
    gif_path = None
    frame_paths: list[Path] = []

    if total == 1:
        # Single sprite - just crop to content
        bbox = processed.getbbox()
        if bbox:
            single = processed.crop(bbox)
            # Center on canvas
            canvas = Image.new("RGBA", (cell_size, cell_size), (0, 0, 0, 0))
            scale = min(cell_size / single.width, cell_size / single.height) * 0.85
            new_w = max(1, int(single.width * scale))
            new_h = max(1, int(single.height * scale))
            resized = single.resize((new_w, new_h), Image.Resampling.LANCZOS)
            px = (cell_size - new_w) // 2
            py = (cell_size - new_h) // 2
            canvas.paste(resized, (px, py), resized)
            frames = [canvas]
        else:
            frames = [processed]
        frame_paths = save_frames(frames, out_dir, prefix="sprite")
    else:
        # Multi-frame sprite sheet
        raw_frames = split_grid(
            processed,
            rows=rows,
            cols=cols,
            cell_size=cell_size,
            component_mode=component_mode,
        )

        # Align frames
        frames = align_frames(
            raw_frames,
            cell_size=cell_size,
            align=align,
            use_shared_scale=shared_scale,
        )

        # Compose sheet
        sheet = compose_sheet(frames, rows, cols, cell_size)

        # Save outputs
        frame_paths = save_frames(frames, out_dir / "frames", prefix="frame")
        gif_path = save_gif(frames, out_dir / "animation.gif")
        sheet.save(out_dir / "sheet.png", format="PNG")

    # Save raw and processed
    raw_image.save(out_dir / "raw.png", format="PNG")
    processed.save(out_dir / "processed.png", format="PNG")

    processing_time = time.time() - t1

    return PipelineResult(
        raw_image=raw_image,
        processed_image=processed,
        sheet=sheet,
        frames=frames,
        gif_path=gif_path,
        frame_paths=frame_paths,
        output_dir=out_dir,
        prompt_used=prompt,
        provider_name=gen_result.provider,
        model_name=gen_result.model,
        generation_time=generation_time,
        processing_time=processing_time,
    )
