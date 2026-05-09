"""OpenAI image generation provider."""

import base64
from io import BytesIO

from openai import OpenAI
from PIL import Image

from ..config import OPENAI_API_KEY
from .base import GenerationRequest, GenerationResult, ImageProvider


class OpenAIProvider(ImageProvider):
    """Generate images using OpenAI's image generation API."""

    def __init__(self):
        self._client = None

    @property
    def name(self) -> str:
        return "OpenAI"

    def is_available(self) -> bool:
        return bool(OPENAI_API_KEY)

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=OPENAI_API_KEY)
        return self._client

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.is_available():
            raise RuntimeError("OpenAI API key not configured. Set OPENAI_API_KEY in .env")

        client = self._get_client()

        if request.reference_image is not None:
            # Image editing mode: use reference image
            buf = BytesIO()
            request.reference_image.save(buf, format="PNG")
            buf.seek(0)

            response = client.images.edit(
                model="gpt-image-1",
                image=buf,
                prompt=request.prompt,
                size=request.size,
            )
        else:
            # Text-to-image mode
            response = client.images.generate(
                model="gpt-image-1",
                prompt=request.prompt,
                size=request.size,
                n=1,
            )

        # Decode base64 response
        image_data = response.data[0]
        if hasattr(image_data, "b64_json") and image_data.b64_json:
            img_bytes = base64.b64decode(image_data.b64_json)
            image = Image.open(BytesIO(img_bytes)).convert("RGBA")
        elif hasattr(image_data, "url") and image_data.url:
            import httpx
            resp = httpx.get(image_data.url)
            image = Image.open(BytesIO(resp.content)).convert("RGBA")
        else:
            raise RuntimeError("No image data in OpenAI response")

        revised = getattr(image_data, "revised_prompt", None)

        return GenerationResult(
            image=image,
            provider="openai",
            model="gpt-image-1",
            revised_prompt=revised,
        )
