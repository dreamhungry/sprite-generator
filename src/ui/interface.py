"""Gradio interface for the sprite generator."""

import traceback

import gradio as gr
from PIL import Image

from ..config import (
    ANIMATION_MODES,
    ASSET_TYPES,
    DEFAULT_CELL_SIZE,
    DEFAULT_PROVIDER,
    GRID_PRESETS,
)
from ..controller import run_pipeline
from ..prompt_builder import get_style_options
from ..providers import PROVIDERS


def _get_available_providers() -> list[str]:
    """Return list of providers that have API keys configured."""
    available = []
    for name, cls in PROVIDERS.items():
        instance = cls()
        if instance.is_available():
            available.append(name)
    # Always show all providers (user can configure later)
    return list(PROVIDERS.keys())


def _generate(
    subject: str,
    provider_name: str,
    asset_type: str,
    mode: str,
    grid: str,
    style: str,
    cell_size: int,
    align: str,
    shared_scale: bool,
    component_mode: str,
    reference_image: Image.Image | None,
    extra_instructions: str,
    image_size: str,
    progress=gr.Progress(),
):
    """Main generation callback for Gradio."""
    if not subject.strip():
        raise gr.Error("Please enter a subject description.")

    progress(0.1, desc="Building prompt...")

    try:
        progress(0.2, desc=f"Generating with {provider_name}...")
        result = run_pipeline(
            subject=subject,
            provider_name=provider_name,
            asset_type=asset_type,
            mode=mode,
            grid=grid,
            style=style,
            cell_size=cell_size,
            align=align,
            shared_scale=shared_scale,
            component_mode=component_mode,
            reference_image=reference_image,
            extra_instructions=extra_instructions,
            image_size=image_size,
        )
        progress(0.9, desc="Done!")

        # Build info text
        info = (
            f"Provider: {result.provider_name} ({result.model_name})\n"
            f"Generation: {result.generation_time:.1f}s | Processing: {result.processing_time:.1f}s\n"
            f"Output: {result.output_dir}"
        )

        # Return results
        gif_output = str(result.gif_path) if result.gif_path else None

        return (
            result.raw_image,
            result.processed_image,
            result.sheet,
            result.frames if result.frames else [],
            gif_output,
            result.prompt_used,
            info,
        )

    except Exception as e:
        traceback.print_exc()
        raise gr.Error(f"Generation failed: {str(e)}")


def create_ui() -> gr.Blocks:
    """Create and return the Gradio application."""

    with gr.Blocks(title="Sprite Generator") as app:
        gr.Markdown("# 🎮 Sprite Generator\nGenerate 2D game sprites from text prompts or reference images.")

        with gr.Row():
            # Left panel: Input
            with gr.Column(scale=1):
                gr.Markdown("### Input")

                subject = gr.Textbox(
                    label="Subject",
                    placeholder="e.g. fire dragon, knight warrior, magic crystal...",
                    lines=2,
                )

                reference_image = gr.Image(
                    label="Reference Image (optional)",
                    type="pil",
                    height=150,
                )

                extra_instructions = gr.Textbox(
                    label="Extra Instructions (optional)",
                    placeholder="Additional style or content instructions...",
                    lines=2,
                )

                with gr.Row():
                    provider = gr.Dropdown(
                        choices=_get_available_providers(),
                        value=DEFAULT_PROVIDER,
                        label="Provider",
                    )
                    image_size = gr.Dropdown(
                        choices=["1024x1024", "1024x1536", "1536x1024"],
                        value="1024x1024",
                        label="Image Size",
                    )

                with gr.Row():
                    asset_type = gr.Dropdown(
                        choices=ASSET_TYPES,
                        value="creature",
                        label="Asset Type",
                    )
                    mode = gr.Dropdown(
                        choices=ANIMATION_MODES,
                        value="idle",
                        label="Animation Mode",
                    )

                with gr.Row():
                    grid = gr.Dropdown(
                        choices=list(GRID_PRESETS.keys()),
                        value="1x4",
                        label="Grid Layout",
                    )
                    style = gr.Dropdown(
                        choices=get_style_options(),
                        value="pixel_art",
                        label="Style",
                    )

                with gr.Accordion("Advanced Settings", open=False):
                    cell_size = gr.Slider(
                        minimum=64, maximum=512, value=DEFAULT_CELL_SIZE, step=32,
                        label="Cell Size (px)",
                    )
                    align = gr.Dropdown(
                        choices=["center", "bottom", "feet"],
                        value="center",
                        label="Alignment",
                    )
                    shared_scale = gr.Checkbox(value=True, label="Shared Scale")
                    component_mode = gr.Dropdown(
                        choices=["all", "largest"],
                        value="all",
                        label="Component Mode",
                    )

                generate_btn = gr.Button("🚀 Generate", variant="primary", size="lg")

            # Right panel: Output
            with gr.Column(scale=2):
                gr.Markdown("### Output")

                with gr.Tabs():
                    with gr.TabItem("Raw"):
                        raw_output = gr.Image(label="Raw Generated", type="pil")

                    with gr.TabItem("Processed"):
                        processed_output = gr.Image(label="Background Removed", type="pil")

                    with gr.TabItem("Sheet"):
                        sheet_output = gr.Image(label="Sprite Sheet", type="pil")

                    with gr.TabItem("Frames"):
                        frames_output = gr.Gallery(label="Individual Frames", columns=4, height=300)

                    with gr.TabItem("Animation"):
                        gif_output = gr.Image(label="Animation GIF")

                with gr.Accordion("Details", open=False):
                    prompt_output = gr.Textbox(label="Prompt Used", lines=4, interactive=False)
                    info_output = gr.Textbox(label="Generation Info", lines=3, interactive=False)

        # Wire up the generate button
        generate_btn.click(
            fn=_generate,
            inputs=[
                subject, provider, asset_type, mode, grid, style,
                cell_size, align, shared_scale, component_mode,
                reference_image, extra_instructions, image_size,
            ],
            outputs=[
                raw_output, processed_output, sheet_output,
                frames_output, gif_output, prompt_output, info_output,
            ],
        )

    return app
