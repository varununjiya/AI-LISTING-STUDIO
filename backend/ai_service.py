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
from ai_engine.ai_manager import NoAPIKeyError

logger = logging.getLogger("ai_service")

# Initialize AI Manager (singleton pattern)
_ai_manager: Optional[AIManager] = None


def get_ai_manager() -> AIManager:
    """Get or create the AI Manager instance."""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIManager()
    return _ai_manager


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
        "prompt": "Ultra-high-end commercial product photography on a pristine, pure white seamless infinity curve background (#FFFFFF), professional studio softbox lighting, soft ground contact shadow, ultra-sharp 8k resolution, crisp commercial detail.",
    },
    {
        "id": "front_view",
        "label": "Front View",
        "group": "studio",
        "prompt": "Commercial product photography studio background, minimal neutral light gray studio backdrop, soft diffused key lighting, subtle floor shadow, 8k resolution, empty center for product placement.",
    },
    {
        "id": "side_view",
        "label": "Side View",
        "group": "studio",
        "prompt": "Professional commercial studio setup, clean minimal light beige background, soft ambient studio lighting, soft floor shadow, 8k resolution.",
    },
    {
        "id": "back_view",
        "label": "Back View",
        "group": "studio",
        "prompt": "Clean professional studio environment, soft neutral light gray backdrop, balanced studio lighting, subtle shadow, 8k.",
    },
    {
        "id": "top_view",
        "label": "Top View",
        "group": "studio",
        "prompt": "Minimalist top-down flat lay studio backdrop, clean light gray paper surface, soft overhead light, subtle soft drop shadow.",
    },
    {
        "id": "angle_45",
        "label": "45 Degree View",
        "group": "studio",
        "prompt": "Award-winning commercial product photography studio, clean light gray gradient backdrop, directional key light, soft contact shadow, 8k resolution.",
    },
    {
        "id": "premium_studio",
        "label": "Premium Studio Shot",
        "group": "studio",
        "prompt": "Luxury advertising studio product stage, sleek dark charcoal gradient backdrop, dramatic rim lighting, glossy floor reflection, ambient studio occlusion, 8k commercial photography.",
    },
    {
        "id": "lifestyle",
        "label": "Lifestyle Image",
        "group": "lifestyle",
        "prompt": "High-end interior architectural space, warm natural daylight streaming through window, soft blurred bokeh background, luxury aesthetic, editorial magazine photography.",
    },
    {
        "id": "on_table",
        "label": "Product on Table",
        "group": "lifestyle",
        "prompt": "Elegant rustic oak tabletop scene with a softly blurred sunlit living room background, morning sunlight with soft shadow patterns, 8k resolution.",
    },
    {
        "id": "in_kitchen",
        "label": "Product in Kitchen",
        "group": "lifestyle",
        "prompt": "Modern luxury kitchen countertop scene, white marble surface, warm natural sunlight, soft blurred modern kitchen background, 8k editorial photography.",
    },
    {
        "id": "in_office",
        "label": "Product in Office",
        "group": "lifestyle",
        "prompt": "Clean modern executive office desk setting, polished wooden desk surface, soft natural office light, blurred modern office background, 8k.",
    },
    {
        "id": "in_gym",
        "label": "Product in Gym",
        "group": "lifestyle",
        "prompt": "Sleek modern fitness gym environment, dark rubberized workout floor, energetic ambient lighting, blurred gym background, 8k.",
    },
    {
        "id": "packaging",
        "label": "Packaging Image",
        "group": "commerce",
        "prompt": "Minimalist luxury product showcase background, elegant unbranded gift box on a clean light gray surface, studio lighting, 8k.",
    },
    {
        "id": "whats_in_box",
        "label": "What's in the Box",
        "group": "commerce",
        "prompt": "Flat lay commercial product arrangement background, clean white surface, organized minimalist layout space, studio softbox light, 8k.",
    },
    {
        "id": "feature_infographic",
        "label": "Feature Infographic",
        "group": "commerce",
        "prompt": "Clean modern tech infographic background, minimal light gray surface with subtle abstract accent lines and space for callout text, 8k.",
    },
    {
        "id": "dimension",
        "label": "Dimension Image",
        "group": "commerce",
        "prompt": "Technical ecommerce dimension backdrop, clean light gray technical studio background with subtle grid lines, 8k.",
    },
    {
        "id": "comparison",
        "label": "Comparison Image",
        "group": "commerce",
        "prompt": "Split comparison background, minimal light gray studio surface with subtle checkmark accent graphics, high-end commercial layout, 8k.",
    },
    {
        "id": "instagram_post",
        "label": "Instagram Post",
        "group": "social",
        "prompt": "Vibrant modern social media background, stylish pastel gradient backdrop, soft aesthetic lighting, space for promotional text, 8k.",
    },
    {
        "id": "facebook_banner",
        "label": "Facebook Banner",
        "group": "social",
        "prompt": "Wide commercial marketing banner background, modern dark blue gradient with subtle geometric shapes and studio lighting, 8k.",
    },
    {
        "id": "whatsapp_status",
        "label": "WhatsApp Status",
        "group": "social",
        "prompt": "Vertical promotional status background, eye-catching modern gradient, warm lighting, space for headline, 8k.",
    },
    {
        "id": "sale_banner",
        "label": "Sale Banner",
        "group": "social",
        "prompt": "High-impact promotional SALE banner background, dynamic bold red and gold gradient with festive studio lighting effects, 8k.",
    },
    {
        "id": "festival_banner",
        "label": "Festival Banner",
        "group": "social",
        "prompt": "Festive celebration banner background, warm golden marigold and deep orange lighting, celebratory bokeh accents, luxury Indian festival decor space, 8k.",
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
