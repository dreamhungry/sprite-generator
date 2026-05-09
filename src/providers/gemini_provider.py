"""Google Gemini image generation provider."""

import base64
from io import BytesIO

from PIL import Image

from ..config import GEMINI_API_KEY
from .base import GenerationRequest, GenerationResult, ImageProvider


class GeminiProvider(ImageProvider):
    """Generate images using Google Gemini's image generation API."""

    def __init__(self):
        self._client = None

    @property
    def name(self) -> str:
        return "Gemini"

    def is_available(self) -> bool:
        return bool(GEMINI_API_KEY)

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=GEMINI_API_KEY)
        return self._client

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.is_available():
            raise RuntimeError("Gemini API key not configured. Set GEMINI_API_KEY in .env")

        client = self._get_client()

        # Build content parts
        contents = [request.prompt]

        if request.reference_image is not None:
            # Include reference image in the request
            buf = BytesIO()
            request.reference_image.save(buf, format="PNG")
            buf.seek(0)
            img_bytes = buf.getvalue()

            from google.genai import types
            image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")
            contents = [image_part, request.prompt]

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=contents,
            config={
                "response_modalities": ["Text", "Image"],
            },
        )

        # Extract image from response
        image = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                img_bytes = part.inline_data.data
                image = Image.open(BytesIO(img_bytes)).convert("RGBA")
                break

        if image is None:
            raise RuntimeError("No image generated in Gemini response")

        return GenerationResult(
            image=image,
            provider="gemini",
            model="gemini-2.0-flash-exp-image-generation",
            revised_prompt=None,
        )
