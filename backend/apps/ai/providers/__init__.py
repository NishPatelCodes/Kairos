from django.conf import settings

from .base import AIProvider
from .mistral import MistralProvider


def get_provider(name: str | None = None) -> AIProvider:
    provider = (name or getattr(settings, "AI_PROVIDER", "mistral")).lower()
    if provider == "mistral":
        return MistralProvider()
    raise ValueError(f"Unknown AI provider '{provider}'.")
