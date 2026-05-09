"""Abstract base class for image generation providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from PIL import Image


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
    provider: str
    model: str
    revised_prompt: str | None = None


class ImageProvider(ABC):
    """Abstract base class for image generation providers."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate an image from the given request."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is properly configured (e.g. API key set)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...
