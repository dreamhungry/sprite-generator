from .base import ImageProvider, GenerationRequest, GenerationResult
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider

PROVIDERS = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}


def get_provider(name: str) -> ImageProvider:
    """Factory function to create a provider instance by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[name]()
