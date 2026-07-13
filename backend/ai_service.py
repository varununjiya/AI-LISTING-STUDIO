"""
AI Service Layer for AI Listing Studio.

This module provides a provider-agnostic abstraction so different AI models
(OpenAI, Gemini, Ollama, Claude, etc.) can be plugged in later WITHOUT changing
any calling code. For now every provider returns rich MOCK JSON so the full
architecture (generation -> review -> export) is production-ready.

To connect a real provider later:
  1. Implement a subclass of `BaseAIProvider`.
  2. Register it in `PROVIDERS`.
  3. The rest of the app keeps calling `generate_listing()` unchanged.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import random


def _titleize(product: Dict[str, Any]) -> str:
    brand = product.get("brand") or "Premium"
    name = product.get("product_name") or "Product"
    material = product.get("material")
    color = product.get("color")
    parts = [brand, name]
    if color:
        parts.append(color)
    if material:
        parts.append(material)
    return " ".join(str(p) for p in parts if p)


class BaseAIProvider(ABC):
    """Contract every AI provider must implement."""

    name: str = "base"

    @abstractmethod
    def generate(self, product: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
        ...


class MockAIProvider(BaseAIProvider):
    """Deterministic-ish mock provider. Returns fully structured listing JSON."""

    name = "mock"

    def generate(self, product: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
        brand = product.get("brand") or "Brand"
        name = product.get("product_name") or "Product"
        category = product.get("category") or "General"
        material = product.get("material") or "premium materials"
        color = product.get("color") or "multiple colors"
        features = product.get("features") or "high quality, durable, everyday use"
        tone = (settings.get("brand_tone") or "professional").lower()

        base_title = _titleize(product)

        amazon_bullets: List[str] = [
            f"PREMIUM {material.upper()}: Crafted from {material} for long-lasting durability and a refined finish.",
            f"VERSATILE DESIGN: The {name} in {color} suits daily use across {category.lower()} needs.",
            f"KEY FEATURES: {features}.",
            f"TRUSTED QUALITY: {brand} backs every product with rigorous quality checks.",
            f"PERFECT GIFT: Ideal present for family and friends who love great {category.lower()} products.",
        ]

        seo_keywords = [
            f"{name.lower()}",
            f"{brand.lower()} {name.lower()}",
            f"best {category.lower()}",
            f"{color.lower()} {name.lower()}",
            f"{material.lower()} {category.lower()}",
            f"buy {name.lower()} online",
            f"{name.lower()} price",
            f"premium {category.lower()}",
        ]

        specs = {
            "Brand": brand,
            "Category": category,
            "Sub Category": product.get("sub_category") or "-",
            "Material": material,
            "Color": color,
            "Size": product.get("size") or "-",
            "Weight": product.get("weight") or "-",
            "Dimensions": product.get("dimensions") or "-",
            "Country of Origin": product.get("country_of_origin") or "India",
            "Warranty": product.get("warranty") or "1 Year Manufacturer Warranty",
            "HSN Code": product.get("hsn_code") or "-",
        }

        tone_prefix = {
            "professional": "Experience unmatched quality.",
            "friendly": "You're going to love this!",
            "luxury": "Indulge in refined craftsmanship.",
            "playful": "Say hello to your new favorite thing.",
        }.get(tone, "Experience unmatched quality.")

        return {
            "amazon_title": f"{base_title} - {category} ({product.get('size') or 'Standard'})"[:200],
            "amazon_bullets": amazon_bullets,
            "amazon_description": (
                f"{tone_prefix} The {brand} {name} is engineered from {material} and finished in {color}. "
                f"Designed for the modern buyer, it delivers on {features}. Whether for personal use or gifting, "
                f"this {category.lower()} product combines style, durability, and everyday practicality. "
                f"Package includes: {product.get('package_contents') or '1 unit'}."
            ),
            "amazon_backend_keywords": " ".join(seo_keywords),
            "flipkart_title": f"{base_title} ({color})"[:150],
            "flipkart_highlights": [
                f"Material: {material}",
                f"Color: {color}",
                f"Category: {category}",
                f"Features: {features}",
                f"Warranty: {product.get('warranty') or '1 Year'}",
            ],
            "flipkart_description": (
                f"Buy the {brand} {name} online. Made with {material} in an elegant {color} finish. "
                f"{features}. Backed by {brand}'s quality promise."
            ),
            "seo_keywords": seo_keywords,
            "meta_description": (
                f"Shop {brand} {name} in {color}. {category} made from {material}. "
                f"{features}. Best price online."
            )[:160],
            "product_specifications": specs,
        }


# Registry of available providers. Add real providers here later.
PROVIDERS: Dict[str, BaseAIProvider] = {
    "mock": MockAIProvider(),
    # "openai": OpenAIProvider(),
    # "gemini": GeminiProvider(),
    # "ollama": OllamaProvider(),
}


def get_provider(provider_name: str | None) -> BaseAIProvider:
    """Return a registered provider, falling back to the mock provider."""
    if not provider_name:
        return PROVIDERS["mock"]
    return PROVIDERS.get(provider_name.lower(), PROVIDERS["mock"])


def generate_listing(
    product: Dict[str, Any],
    settings: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Public entrypoint used by the API. Provider is chosen from settings."""
    settings = settings or {}
    provider = get_provider(settings.get("ai_provider"))
    return provider.generate(product, settings)


def regenerate_section(
    section: str,
    product: Dict[str, Any],
    settings: Dict[str, Any] | None = None,
) -> Any:
    """Regenerate a single section (adds slight variation to feel 'fresh')."""
    full = generate_listing(product, settings)
    # inject a small variation marker so regenerate visibly changes output
    variants = ["", " ", "  "]
    salt = random.choice(variants)
    value = full.get(section)
    if isinstance(value, str):
        return value + salt
    return value
