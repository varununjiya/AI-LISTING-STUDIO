"""
AI Service Layer for AI Ecommerce Content Studio.

Real AI powered by emergentintegrations (Emergent Universal Key by default, or a
user-supplied OpenAI / Gemini / Anthropic key stored in Settings).

Capabilities:
  - generate_listing()   : multi-marketplace listing JSON (Amazon, Flipkart, Meesho, SEO)
  - analyze_image()      : vision -> structured product attributes
  - generate_scene_image(): image-to-image scene/background generation (Nano Banana)
  - compute_quality_score(): deterministic listing quality scoring (no AI)
  - marketplace validation limits
"""
from __future__ import annotations

import os
import re
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

load_dotenv(Path(__file__).parent / ".env")

logger = logging.getLogger("ai_service")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

# Providers supported through emergentintegrations.
SUPPORTED_TEXT_PROVIDERS = {"gemini", "openai", "anthropic"}
DEFAULT_TEXT_MODEL = {
    "gemini": "gemini-3.1-pro-preview",
    "openai": "gpt-5.4",
    "anthropic": "claude-sonnet-4-6",
}
IMAGE_MODEL = "gemini-3.1-flash-image-preview"  # Nano Banana

# Marketplace character limits used for validation + scoring.
MARKETPLACE_LIMITS = {
    "amazon": {"title": 200, "bullet": 500, "description": 2000, "backend_keywords": 250},
    "flipkart": {"title": 150, "highlight": 120, "description": 2000},
    "meesho": {"title": 120, "description": 1500},
}


class NoAPIKeyError(Exception):
    """Raised when no usable AI key is configured."""


# --------------------------------------------------------------------------- #
# Key / provider resolution
# --------------------------------------------------------------------------- #
def resolve_credentials(settings: Dict[str, Any]) -> Tuple[str, str, str]:
    """Return (api_key, provider, text_model).

    If the user opted for their own key and provided one, use it with their chosen
    provider. Otherwise fall back to the Emergent Universal Key.
    """
    provider = (settings.get("ai_provider") or "gemini").lower()
    if provider not in SUPPORTED_TEXT_PROVIDERS:
        provider = "gemini"

    text_model = settings.get("text_model") or DEFAULT_TEXT_MODEL[provider]

    use_own = bool(settings.get("use_own_key"))
    own_key = (settings.get("api_key") or "").strip()
    if use_own and own_key:
        return own_key, provider, text_model

    if EMERGENT_LLM_KEY:
        return EMERGENT_LLM_KEY, provider, text_model

    raise NoAPIKeyError(
        "No AI key configured. Add your own key in Settings or enable the Emergent Universal Key."
    )


def has_ai_configured(settings: Dict[str, Any]) -> bool:
    try:
        resolve_credentials(settings)
        return True
    except NoAPIKeyError:
        return False


def _new_chat(settings: Dict[str, Any], session_id: str, system_message: str) -> LlmChat:
    api_key, provider, model = resolve_credentials(settings)
    chat = LlmChat(api_key=api_key, session_id=session_id, system_message=system_message)
    chat.with_model(provider, model)
    return chat


def _extract_json(text: str) -> Dict[str, Any]:
    """Robustly parse a JSON object out of an LLM response."""
    if not text:
        raise ValueError("Empty AI response")
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in AI response")
    return json.loads(cleaned[start : end + 1])


# --------------------------------------------------------------------------- #
# Listing generation (multi-marketplace)
# --------------------------------------------------------------------------- #
LISTING_SYSTEM = (
    "You are a senior e-commerce copywriter and marketplace SEO specialist for Amazon, "
    "Flipkart and Meesho in India. You write natural, professional, human marketing copy. "
    "Never stuff keywords, never repeat sentences or phrases, use correct grammar, and keep "
    "each marketplace within its character limits. Return STRICT JSON only, no commentary."
)


def _listing_prompt(product: Dict[str, Any], settings: Dict[str, Any]) -> str:
    tone = settings.get("brand_tone", "professional")
    language = settings.get("language", "English")
    fields = {k: v for k, v in product.items() if k not in ("images", "user_id", "id")}
    return f"""Write complete, high-converting marketplace listings in {language} with a {tone} tone.

PRODUCT DATA (JSON):
{json.dumps(fields, ensure_ascii=False, indent=2)}

Return STRICT JSON with EXACTLY this shape (fill every field with real, unique, non-repetitive content):
{{
  "amazon": {{
    "title": "string, <=200 chars, includes brand + key attributes",
    "bullets": ["5 distinct benefit-led bullet points, each <=500 chars"],
    "description": "string, 3-5 short paragraphs, <=2000 chars",
    "backend_keywords": "space-separated search terms, no commas, <=250 chars, no repeats",
    "search_terms": ["8-12 buyer search phrases"],
    "generic_keywords": ["6-10 broad category keywords"],
    "subject_matter": ["3-5 subject matter keywords"],
    "aplus_content_suggestions": ["3-5 A+ content module ideas"]
  }},
  "flipkart": {{
    "title": "string, <=150 chars",
    "highlights": ["5-6 short highlight lines, each <=120 chars"],
    "description": "string <=2000 chars",
    "specifications": {{"key": "value pairs of important specs"}},
    "search_keywords": ["8-12 keywords"]
  }},
  "meesho": {{
    "title": "string, <=120 chars",
    "description": "string <=1500 chars",
    "highlights": ["4-6 highlights"],
    "tags": ["8-12 discovery tags"]
  }},
  "seo": {{
    "primary_keywords": ["3-5"],
    "secondary_keywords": ["5-8"],
    "long_tail_keywords": ["5-8"],
    "trending_keywords": ["4-6"],
    "competitor_keywords": ["4-6"],
    "meta_description": "string <=160 chars"
  }}
}}"""


async def generate_listing(product: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a full multi-marketplace listing. Raises NoAPIKeyError if unconfigured."""
    resolve_credentials(settings)  # raises if no key
    chat = _new_chat(settings, f"listing-{product.get('id','x')}", LISTING_SYSTEM)
    msg = UserMessage(text=_listing_prompt(product, settings))
    response = await chat.send_message(msg)
    data = _extract_json(response)

    # Flatten to the storage schema used across the app (backward compatible).
    az = data.get("amazon", {})
    fk = data.get("flipkart", {})
    me = data.get("meesho", {})
    seo = data.get("seo", {})

    listing = {
        # Amazon
        "amazon_title": az.get("title", ""),
        "amazon_bullets": az.get("bullets", []),
        "amazon_description": az.get("description", ""),
        "amazon_backend_keywords": az.get("backend_keywords", ""),
        "amazon_search_terms": az.get("search_terms", []),
        "amazon_generic_keywords": az.get("generic_keywords", []),
        "amazon_subject_matter": az.get("subject_matter", []),
        "amazon_aplus_suggestions": az.get("aplus_content_suggestions", []),
        # Flipkart
        "flipkart_title": fk.get("title", ""),
        "flipkart_highlights": fk.get("highlights", []),
        "flipkart_description": fk.get("description", ""),
        "flipkart_specifications": fk.get("specifications", {}),
        "flipkart_search_keywords": fk.get("search_keywords", []),
        # Meesho
        "meesho_title": me.get("title", ""),
        "meesho_description": me.get("description", ""),
        "meesho_highlights": me.get("highlights", []),
        "meesho_tags": me.get("tags", []),
        # SEO
        "seo_primary_keywords": seo.get("primary_keywords", []),
        "seo_secondary_keywords": seo.get("secondary_keywords", []),
        "seo_long_tail_keywords": seo.get("long_tail_keywords", []),
        "seo_trending_keywords": seo.get("trending_keywords", []),
        "seo_competitor_keywords": seo.get("competitor_keywords", []),
        "meta_description": seo.get("meta_description", ""),
        # legacy compatibility fields
        "seo_keywords": (seo.get("primary_keywords", []) + seo.get("secondary_keywords", [])),
        "product_specifications": fk.get("specifications", {}),
    }
    return listing


async def regenerate_section(section: str, product: Dict[str, Any], settings: Dict[str, Any]) -> Any:
    """Regenerate a single stored section key by generating fresh and returning that field."""
    full = await generate_listing(product, settings)
    return full.get(section)


# --------------------------------------------------------------------------- #
# Vision: analyze product image -> attributes
# --------------------------------------------------------------------------- #
VISION_SYSTEM = (
    "You are a product cataloguing expert. Look at the product image and infer accurate "
    "attributes. Return STRICT JSON only."
)


async def analyze_image(image_base64: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a product image and return structured attributes to auto-fill fields."""
    resolve_credentials(settings)
    # strip data URL prefix if present
    b64 = image_base64.split(",", 1)[1] if image_base64.startswith("data:") else image_base64
    chat = _new_chat(settings, "vision-analyze", VISION_SYSTEM)
    prompt = """Analyze this product image and return STRICT JSON:
{
  "category": "", "sub_category": "", "material": "", "color": "", "pattern": "",
  "shape": "", "estimated_dimensions": "", "capacity": "", "product_type": "",
  "product_name": "concise descriptive name", "brand": "if visible else empty",
  "features": "comma-separated key visible features"
}"""
    msg = UserMessage(text=prompt, file_contents=[ImageContent(b64)])
    response = await chat.send_message(msg)
    return _extract_json(response)


# --------------------------------------------------------------------------- #
# Image generation (scene / background) — Nano Banana image-to-image
# --------------------------------------------------------------------------- #
IMAGE_PRESETS: List[Dict[str, str]] = [
    {"id": "white_bg", "label": "Amazon White Background", "group": "studio",
     "prompt": "Place the exact same product on a pure white seamless background (#FFFFFF), professional Amazon product photo, soft even studio lighting, subtle shadow, centered, high detail. Keep the product identical."},
    {"id": "front_view", "label": "Front View", "group": "studio",
     "prompt": "Show the exact same product from a straight front view on a clean light gray studio background, professional lighting."},
    {"id": "side_view", "label": "Side View", "group": "studio",
     "prompt": "Show the exact same product from a 90-degree side profile view on a clean light gray studio background."},
    {"id": "back_view", "label": "Back View", "group": "studio",
     "prompt": "Show the exact same product from the back view on a clean light gray studio background."},
    {"id": "top_view", "label": "Top View", "group": "studio",
     "prompt": "Show the exact same product from a top-down flat lay view on a clean light gray background."},
    {"id": "angle_45", "label": "45 Degree View", "group": "studio",
     "prompt": "Show the exact same product from a 45-degree three-quarter angle on a clean light gray studio background, premium lighting."},
    {"id": "premium_studio", "label": "Premium Studio Shot", "group": "studio",
     "prompt": "Dramatic premium studio product shot of the exact same product with a dark gradient background, rim lighting and reflection, luxury advertising style."},
    {"id": "lifestyle", "label": "Lifestyle Image", "group": "lifestyle",
     "prompt": "Place the exact same product in a natural real-life lifestyle setting with soft natural light and tasteful props, editorial photography."},
    {"id": "on_table", "label": "Product on Table", "group": "lifestyle",
     "prompt": "Place the exact same product on a stylish wooden table with a softly blurred home background, warm natural light."},
    {"id": "in_kitchen", "label": "Product in Kitchen", "group": "lifestyle",
     "prompt": "Place the exact same product in a bright modern kitchen setting with realistic context, natural light."},
    {"id": "in_office", "label": "Product in Office", "group": "lifestyle",
     "prompt": "Place the exact same product in a clean modern office desk setting with realistic context."},
    {"id": "in_gym", "label": "Product in Gym", "group": "lifestyle",
     "prompt": "Place the exact same product in a modern gym environment with realistic context and energetic lighting."},
    {"id": "packaging", "label": "Packaging Image", "group": "commerce",
     "prompt": "Show the exact same product next to elegant minimal branded packaging box on a white background."},
    {"id": "whats_in_box", "label": "What's in the Box", "group": "commerce",
     "prompt": "Flat lay 'what's in the box' image showing the exact same product with its accessories neatly arranged on a white background."},
    {"id": "feature_infographic", "label": "Feature Infographic", "group": "commerce",
     "prompt": "Create a clean feature infographic image of the exact same product with 3-4 callout labels pointing to key features, minimal modern design, white background."},
    {"id": "dimension", "label": "Dimension Image", "group": "commerce",
     "prompt": "Create a dimension diagram of the exact same product with measurement lines and labels on a white background, technical e-commerce style."},
    {"id": "comparison", "label": "Comparison Image", "group": "commerce",
     "prompt": "Create a comparison-style product image of the exact same product highlighting its advantages, clean white background with subtle checkmark icons."},
    {"id": "instagram_post", "label": "Instagram Post", "group": "social",
     "prompt": "Create a trendy square Instagram post featuring the exact same product with a bold modern background, vibrant colors and space for a short headline."},
    {"id": "facebook_banner", "label": "Facebook Banner", "group": "social",
     "prompt": "Create a wide Facebook cover banner featuring the exact same product with a modern gradient background and marketing layout."},
    {"id": "whatsapp_status", "label": "WhatsApp Status", "group": "social",
     "prompt": "Create a vertical WhatsApp status image featuring the exact same product with an eye-catching promotional design."},
    {"id": "sale_banner", "label": "Sale Banner", "group": "social",
     "prompt": "Create a high-impact SALE promotional banner featuring the exact same product with bold discount styling and vibrant background."},
    {"id": "festival_banner", "label": "Festival Banner", "group": "social",
     "prompt": "Create a festive Indian festival sale banner featuring the exact same product with celebratory decorations and warm colors."},
]

PRESET_MAP = {p["id"]: p for p in IMAGE_PRESETS}


async def generate_scene_image(
    input_image_base64: str,
    prompt: str,
    settings: Dict[str, Any],
) -> str:
    """Generate a new product image (image-to-image). Returns base64 (no data URL prefix).

    Uses Nano Banana to keep the product identical while changing background/scene.
    """
    api_key, _, _ = resolve_credentials(settings)  # image gen key (universal or own gemini)
    b64 = input_image_base64.split(",", 1)[1] if input_image_base64.startswith("data:") else input_image_base64

    chat = LlmChat(api_key=api_key, session_id="image-studio", system_message="You are an expert product photographer.")
    chat.with_model("gemini", IMAGE_MODEL).with_params(modalities=["image", "text"])

    full_prompt = (
        prompt
        + " CRITICAL: keep the product itself completely unchanged (same shape, colors, "
        "text, logos and details); only change the background, environment and presentation. "
        "Output a photorealistic, high-resolution image."
    )
    msg = UserMessage(text=full_prompt, file_contents=[ImageContent(b64)])
    _, images = await chat.send_message_multimodal_response(msg)
    if not images:
        raise ValueError("No image returned by the model")
    return images[0]["data"]  # base64 string


# --------------------------------------------------------------------------- #
# Listing Quality Score (deterministic, no AI)
# --------------------------------------------------------------------------- #
def _word_repetition_penalty(text: str) -> float:
    words = re.findall(r"[a-zA-Z]{4,}", (text or "").lower())
    if not words:
        return 0.0
    unique_ratio = len(set(words)) / len(words)
    return max(0.0, (1 - unique_ratio) * 100)  # higher = more repetition


def compute_quality_score(product: Dict[str, Any], listing: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return {score, breakdown, suggestions}. Score out of 100."""
    if not listing:
        return {"score": 0, "breakdown": {}, "suggestions": ["Generate a listing to compute a quality score."]}

    suggestions: List[str] = []
    breakdown: Dict[str, int] = {}

    # 1. Completeness (25)
    core = ["amazon_title", "amazon_bullets", "amazon_description", "flipkart_title", "meesho_title"]
    filled = sum(1 for k in core if listing.get(k))
    completeness = round(filled / len(core) * 25)
    breakdown["completeness"] = completeness
    if completeness < 25:
        suggestions.append("Generate listings for all marketplaces (Amazon, Flipkart, Meesho).")

    # 2. Character limits / marketplace compliance (20)
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
        suggestions.append("Add 5 Amazon bullet points for maximum coverage.")
    breakdown["marketplace_compliance"] = max(0, compliance)

    # 3. SEO / keyword optimization (20)
    seo_kw = (listing.get("seo_primary_keywords", []) or []) + (listing.get("seo_secondary_keywords", []) or [])
    seo_score = min(20, len(seo_kw) * 2)
    breakdown["seo"] = seo_score
    if seo_score < 12:
        suggestions.append("Add more primary and secondary SEO keywords.")

    # 4. Readability / no repetition (20)
    rep = _word_repetition_penalty(listing.get("amazon_description", ""))
    readability = max(0, round(20 - rep / 5))
    breakdown["readability"] = readability
    if readability < 14:
        suggestions.append("Reduce repeated words/phrases in the Amazon description.")

    # 5. Image completeness (15)
    imgs = product.get("images", []) or []
    gen_imgs = product.get("generated_images", []) or []
    total_imgs = len(imgs) + len(gen_imgs)
    image_score = min(15, total_imgs * 3)
    breakdown["images"] = image_score
    if image_score < 15:
        suggestions.append("Generate more product images in AI Image Studio (aim for 5+).")

    score = sum(breakdown.values())
    return {"score": min(100, score), "breakdown": breakdown, "suggestions": suggestions}
