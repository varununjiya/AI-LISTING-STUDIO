"""
AI Service Layer for AI Ecommerce Content Studio - OpenRouter Edition.

This module provides the main interface for all AI operations, now powered by
OpenRouter for text/vision and Emergent Universal Key for image generation.

Capabilities:
  - generate_listing()    : Multi-marketplace listing (Amazon, Flipkart, Meesho, SEO)
  - analyze_image()       : Vision -> structured product attributes
  - generate_scene_image(): Image-to-image scene generation (Nano Banana)
  - compute_quality_score(): Deterministic quality scoring
  - Marketplace validation & limits
"""
from __future__ import annotations

import re
import logging
from typing import Dict, Any, List, Optional

from ai_engine import AIManager

logger = logging.getLogger("ai_service")

# Initialize AI Manager (singleton pattern)
_ai_manager: Optional[AIManager] = None


def get_ai_manager() -> AIManager:
    """Get or create the AI Manager instance."""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIManager()
    return _ai_manager


# Re-export the NoAPIKeyError from AI Manager
NoAPIKeyError = AIManager.__module__ + ".NoAPIKeyError"


# Marketplace character limits (for validation and scoring)
MARKETPLACE_LIMITS = {
    "amazon": {
        "title": 200,
        "bullet": 500,
        "description": 2000,
        "backend_keywords": 250,
    },
    "flipkart": {
        "title": 150,
        "highlight": 120,
        "description": 2000,
    },
    "meesho": {
        "title": 120,
        "description": 1500,
    },
}

# Image generation presets (for AI Image Studio)
IMAGE_PRESETS: List[Dict[str, str]] = [
    {
        "id": "white_bg",
        "label": "Amazon White Background",
        "group": "studio",
        "prompt": "Place the exact same product on a pure white seamless background (#FFFFFF), professional Amazon product photo, soft even studio lighting, subtle shadow, centered, high detail. Keep the product identical.",
    },
    {
        "id": "front_view",
        "label": "Front View",
        "group": "studio",
        "prompt": "Show the exact same product from a straight front view on a clean light gray studio background, professional lighting.",
    },
    {
        "id": "side_view",
        "label": "Side View",
        "group": "studio",
        "prompt": "Show the exact same product from a 90-degree side profile view on a clean light gray studio background.",
    },
    {
        "id": "back_view",
        "label": "Back View",
        "group": "studio",
        "prompt": "Show the exact same product from the back view on a clean light gray studio background.",
    },
    {
        "id": "top_view",
        "label": "Top View",
        "group": "studio",
        "prompt": "Show the exact same product from a top-down flat lay view on a clean light gray background.",
    },
    {
        "id": "angle_45",
        "label": "45 Degree View",
        "group": "studio",
        "prompt": "Show the exact same product from a 45-degree three-quarter angle on a clean light gray studio background, premium lighting.",
    },
    {
        "id": "premium_studio",
        "label": "Premium Studio Shot",
        "group": "studio",
        "prompt": "Dramatic premium studio product shot of the exact same product with a dark gradient background, rim lighting and reflection, luxury advertising style.",
    },
    {
        "id": "lifestyle",
        "label": "Lifestyle Image",
        "group": "lifestyle",
        "prompt": "Place the exact same product in a natural real-life lifestyle setting with soft natural light and tasteful props, editorial photography.",
    },
    {
        "id": "on_table",
        "label": "Product on Table",
        "group": "lifestyle",
        "prompt": "Place the exact same product on a stylish wooden table with a softly blurred home background, warm natural light.",
    },
    {
        "id": "in_kitchen",
        "label": "Product in Kitchen",
        "group": "lifestyle",
        "prompt": "Place the exact same product in a bright modern kitchen setting with realistic context, natural light.",
    },
    {
        "id": "in_office",
        "label": "Product in Office",
        "group": "lifestyle",
        "prompt": "Place the exact same product in a clean modern office desk setting with realistic context.",
    },
    {
        "id": "in_gym",
        "label": "Product in Gym",
        "group": "lifestyle",
        "prompt": "Place the exact same product in a modern gym environment with realistic context and energetic lighting.",
    },
    {
        "id": "packaging",
        "label": "Packaging Image",
        "group": "commerce",
        "prompt": "Show the exact same product next to elegant minimal branded packaging box on a white background.",
    },
    {
        "id": "whats_in_box",
        "label": "What's in the Box",
        "group": "commerce",
        "prompt": "Flat lay 'what's in the box' image showing the exact same product with its accessories neatly arranged on a white background.",
    },
    {
        "id": "feature_infographic",
        "label": "Feature Infographic",
        "group": "commerce",
        "prompt": "Create a clean feature infographic image of the exact same product with 3-4 callout labels pointing to key features, minimal modern design, white background.",
    },
    {
        "id": "dimension",
        "label": "Dimension Image",
        "group": "commerce",
        "prompt": "Create a dimension diagram of the exact same product with measurement lines and labels on a white background, technical e-commerce style.",
    },
    {
        "id": "comparison",
        "label": "Comparison Image",
        "group": "commerce",
        "prompt": "Create a comparison-style product image of the exact same product highlighting its advantages, clean white background with subtle checkmark icons.",
    },
    {
        "id": "instagram_post",
        "label": "Instagram Post",
        "group": "social",
        "prompt": "Create a trendy square Instagram post featuring the exact same product with a bold modern background, vibrant colors and space for a short headline.",
    },
    {
        "id": "facebook_banner",
        "label": "Facebook Banner",
        "group": "social",
        "prompt": "Create a wide Facebook cover banner featuring the exact same product with a modern gradient background and marketing layout.",
    },
    {
        "id": "whatsapp_status",
        "label": "WhatsApp Status",
        "group": "social",
        "prompt": "Create a vertical WhatsApp status image featuring the exact same product with an eye-catching promotional design.",
    },
    {
        "id": "sale_banner",
        "label": "Sale Banner",
        "group": "social",
        "prompt": "Create a high-impact SALE promotional banner featuring the exact same product with bold discount styling and vibrant background.",
    },
    {
        "id": "festival_banner",
        "label": "Festival Banner",
        "group": "social",
        "prompt": "Create a festive Indian festival sale banner featuring the exact same product with celebratory decorations and warm colors.",
    },
]

PRESET_MAP = {p["id"]: p for p in IMAGE_PRESETS}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def has_ai_configured(settings: Dict[str, Any]) -> bool:
    """Check if AI is properly configured (OpenRouter or Emergent key)."""
    manager = get_ai_manager()
    return manager.has_openrouter_configured()


async def generate_listing(
    product: Dict[str, Any], settings: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate complete multi-marketplace listing.
    
    Returns a flat dict with all marketplace-specific fields + SEO.
    """
    manager = get_ai_manager()
    return await manager.generate_listing(product, settings)


async def regenerate_section(
    section: str, product: Dict[str, Any], settings: Dict[str, Any]
) -> Any:
    """Regenerate a single listing section."""
    manager = get_ai_manager()
    return await manager.regenerate_section(section, product, settings)


async def analyze_image(image_base64: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a product image and return structured attributes."""
    manager = get_ai_manager()
    return await manager.analyze_image(image_base64, settings)


async def generate_scene_image(
    input_image_base64: str, prompt: str, settings: Dict[str, Any]
) -> str:
    """Generate a scene image (background change) using Nano Banana.
    
    Returns base64 string (no data URL prefix).
    """
    manager = get_ai_manager()
    return await manager.generate_scene_image(input_image_base64, prompt, settings)


async def generate_seo(
    product: Dict[str, Any], settings: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate comprehensive SEO keywords and metadata."""
    manager = get_ai_manager()
    return await manager.generate_seo(product, settings)


# --------------------------------------------------------------------------- #
# Quality Scoring (deterministic, no AI)
# --------------------------------------------------------------------------- #


def _word_repetition_penalty(text: str) -> float:
    """Calculate word repetition penalty."""
    words = re.findall(r"[a-zA-Z]{4,}", (text or "").lower())
    if not words:
        return 0.0
    unique_ratio = len(set(words)) / len(words)
    return max(0.0, (1 - unique_ratio) * 100)


def compute_quality_score(
    product: Dict[str, Any], listing: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Compute listing quality score (0-100) with breakdown and suggestions."""
    if not listing:
        return {
            "score": 0,
            "breakdown": {},
            "suggestions": ["Generate a listing to compute quality score."],
        }

    suggestions: List[str] = []
    breakdown: Dict[str, int] = {}

    # 1. Completeness (25 points)
    core_fields = [
        "amazon_title",
        "amazon_bullets",
        "amazon_description",
        "flipkart_title",
        "meesho_title",
    ]
    filled = sum(1 for k in core_fields if listing.get(k))
    completeness = round(filled / len(core_fields) * 25)
    breakdown["completeness"] = completeness
    if completeness < 25:
        suggestions.append(
            "Generate listings for all marketplaces (Amazon, Flipkart, Meesho)."
        )

    # 2. Marketplace compliance (20 points)
    compliance = 20
    title = listing.get("amazon_title", "")
    if len(title) > MARKETPLACE_LIMITS["amazon"]["title"]:
        compliance -= 8
        suggestions.append("Amazon title exceeds 200 characters — shorten it.")
    if len(listing.get("flipkart_title", "")) > MARKETPLACE_LIMITS["flipkart"]["title"]:
        compliance -= 6
        suggestions.append("Flipkart title exceeds 150 characters.")
    bullets = listing.get("amazon_bullets", []) or []
    if len(bullets) < 5:
        compliance -= 6
        suggestions.append("Add 5 Amazon bullet points for maximum impact.")
    breakdown["marketplace_compliance"] = max(0, compliance)

    # 3. SEO optimization (20 points)
    seo_primary = listing.get("seo_primary_keywords", []) or []
    seo_secondary = listing.get("seo_secondary_keywords", []) or []
    total_seo_kw = len(seo_primary) + len(seo_secondary)
    seo_score = min(20, total_seo_kw * 2)
    breakdown["seo"] = seo_score
    if seo_score < 12:
        suggestions.append("Add more SEO keywords (primary and secondary).")

    # 4. Readability / no repetition (20 points)
    rep = _word_repetition_penalty(listing.get("amazon_description", ""))
    readability = max(0, round(20 - rep / 5))
    breakdown["readability"] = readability
    if readability < 14:
        suggestions.append(
            "Reduce repeated words/phrases in Amazon description for better readability."
        )

    # 5. Image completeness (15 points)
    imgs = product.get("images", []) or []
    gen_imgs = product.get("generated_images", []) or []
    total_imgs = len(imgs) + len(gen_imgs)
    image_score = min(15, total_imgs * 3)
    breakdown["images"] = image_score
    if image_score < 15:
        suggestions.append(
            "Generate more product images in AI Image Studio (aim for 5+ images)."
        )

    score = sum(breakdown.values())

    return {
        "score": min(100, score),
        "breakdown": breakdown,
        "suggestions": suggestions[:10],  # Limit to top 10
    }


def get_ai_stats() -> Dict[str, Any]:
    """Get AI service statistics."""
    manager = get_ai_manager()
    return manager.get_stats()
