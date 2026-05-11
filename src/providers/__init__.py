"""Unified image generation client using OpenAI-compatible API."""

import base64
from dataclasses import dataclass, field
from io import BytesIO

from openai import OpenAI
from PIL import Image

from ..config import API_KEY, BASE_URL, MODEL


@dataclass
class GenerationRequest:
    """Request parameters for image generation."""

    prompt: str
    reference_image: Image.Image | None = None
    size: str = "1024x1024"
    style: str = "pixel_art"
    extra: dict = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result from image generation."""

    image: Image.Image
    model: str
    revised_prompt: str | None = None


def _get_client() -> OpenAI:
    """Create an OpenAI-compatible client with current config."""
    if not API_KEY:
        raise RuntimeError(
            "API_KEY not configured. Set API_KEY, BASE_URL, and MODEL in .env"
        )
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def generate_image(request: GenerationRequest) -> GenerationResult:
    """Generate an image using the configured API endpoint.

    Works with any OpenAI-compatible API: OpenAI, Gemini, Claude,
    third-party aggregators (OpenRouter, one-api, etc.).
    """
    client = _get_client()

    if request.reference_image is not None:
        # Image editing mode
        buf = BytesIO()
        request.reference_image.save(buf, format="PNG")
        buf.seek(0)

        response = client.images.edit(
            model=MODEL,
            image=buf,
            prompt=request.prompt,
            size=request.size,
        )
    else:
        # Text-to-image mode
        response = client.images.generate(
            model=MODEL,
            prompt=request.prompt,
            size=request.size,
            n=1,
        )

    # Decode response (supports both b64_json and url formats)
    image_data = response.data[0]
    if hasattr(image_data, "b64_json") and image_data.b64_json:
        img_bytes = base64.b64decode(image_data.b64_json)
        image = Image.open(BytesIO(img_bytes)).convert("RGBA")
    elif hasattr(image_data, "url") and image_data.url:
        import httpx
        resp = httpx.get(image_data.url)
        image = Image.open(BytesIO(resp.content)).convert("RGBA")
    else:
        raise RuntimeError("No image data in API response")

    revised = getattr(image_data, "revised_prompt", None)

    return GenerationResult(
        image=image,
        model=MODEL,
        revised_prompt=revised,
    )
