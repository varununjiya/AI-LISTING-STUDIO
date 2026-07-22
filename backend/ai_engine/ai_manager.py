"""AI Manager - Central orchestrator for all AI operations."""
from __future__ import annotations

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from dotenv import load_dotenv

from .openrouter_service import OpenRouterService, NoAPIKeyError as ORNoAPIKeyError
from .model_router import ModelRouter
from .prompt_manager import PromptManager
from .response_formatter import ResponseFormatter
from .pollinations_service import get_pollinations_service
from .gemini_service import get_gemini_service

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger("ai_manager")

IMAGE_GENERATION_SERVICE = os.getenv("IMAGE_GENERATION_SERVICE", "gemini").lower()


class NoAPIKeyError(Exception):
    """Raised when no API key is configured."""


class AIManager:
    """Central AI orchestrator using OpenRouter for text/vision and Gemini/Pollinations for images."""

    def __init__(self):
        self.openrouter = OpenRouterService()
        self.model_router = ModelRouter()
        self.prompt_manager = PromptManager()
        self.formatter = ResponseFormatter()
        self.pollinations = get_pollinations_service()
        self.gemini = get_gemini_service()
        self.image_service = IMAGE_GENERATION_SERVICE
    
    def has_openrouter_configured(self) -> bool:
        """Check if OpenRouter is configured."""
        try:
            self.openrouter.get_active_key()
            return True
        except ORNoAPIKeyError:
            return False
    
    def has_image_generation_configured(self) -> bool:
        return True

    
    async def generate_listing(
        self, product: Dict[str, Any], settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate complete multi-marketplace listing.
        
        Returns a flat dict with all marketplace listings + SEO.
        """
        if not self.has_openrouter_configured():
            raise NoAPIKeyError(
                "OpenRouter not configured. Please add OPENROUTER_API_KEY_1 to backend/.env"
            )
        
        # Get task configuration
        config = self.model_router.get_task_config("listing_generation")
        
        # Build prompt with product data
        tone = settings.get("brand_tone", "professional")
        language = settings.get("language", "English")
        
        product_data = {
            k: v for k, v in product.items() 
            if k not in ("images", "generated_images", "user_id", "id", "_id")
        }
        
        prompt = self.prompt_manager.get_prompt(
            "listing.full_marketplace",
            {
                "tone": tone,
                "language": language,
                "product_data": product_data,
            }
        )
        
        # System message
        system = """You are a senior e-commerce copywriter and marketplace SEO specialist.
Write natural, professional, human marketing copy for Indian marketplaces (Amazon, Flipkart, Meesho).

RULES:
- NEVER repeat keywords, sentences, or phrases
- Use correct grammar and natural language
- Stay within character limits for each marketplace
- Each bullet point and highlight must be UNIQUE
- Avoid keyword stuffing - integrate keywords naturally
- Return STRICT JSON only, no commentary"""
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        
        # Call OpenRouter
        response_text, metadata = await self.openrouter.chat_completion(
            model=config["model"],
            messages=messages,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            response_format={"type": "json_object"},
        )
        
        # Parse and validate response
        raw_data = self.formatter.extract_json(response_text)
        validated_listing = self.formatter.validate_listing_response(raw_data)
        
        # Check quality
        if self.formatter.check_repetition(validated_listing.get("amazon_description", "")):
            logger.warning("Detected repetition in Amazon description")
        
        logger.info(
            f"Generated listing with {metadata['model']} "
            f"(tokens: {metadata['usage'].get('total_tokens', 0)})"
        )
        
        return validated_listing
    
    async def regenerate_section(
        self, section: str, product: Dict[str, Any], settings: Dict[str, Any]
    ) -> Any:
        """Regenerate a single listing section."""
        # For now, regenerate the full listing and extract the section
        # TODO: Optimize to generate only the requested section
        full_listing = await self.generate_listing(product, settings)
        return full_listing.get(section)
    
    async def analyze_image(
        self, image_base64: str, settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze product image and extract attributes."""
        if not self.has_openrouter_configured():
            raise NoAPIKeyError("OpenRouter not configured for vision analysis")
        
        # Strip data URL prefix
        b64 = image_base64.split(",", 1)[1] if image_base64.startswith("data:") else image_base64
        
        config = self.model_router.get_task_config("vision_analysis")
        
        prompt = self.prompt_manager.get_prompt("analysis.vision")
        
        # Call OpenRouter vision model
        response_text, metadata = await self.openrouter.vision_completion(
            model=config["model"],
            prompt=prompt,
            image_base64=b64,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
        )
        
        # Parse and validate
        raw_data = self.formatter.extract_json(response_text)
        validated_attrs = self.formatter.validate_vision_response(raw_data)
        
        logger.info(f"Analyzed image with {metadata['model']}")
        
        return validated_attrs
    async def generate_scene_image(
        self,
        input_image_base64: str,
        prompt: str,
        settings: Dict[str, Any],
    ) -> str:
        """
        Generate an AI product image using Gemini (Imagen 3) or fallback service.
        """
        service = (settings.get("image_service") or self.image_service or "gemini").lower()

        bg_prompt = f"""
Professional commercial product studio background.

{prompt}

Requirements:
- Clean studio environment background.
- Soft, natural commercial lighting.
- Amazon ecommerce listing style.
- High detail, 8K, realistic depth of field.
- Empty space in center for product placement.
- No text, no watermark.
"""

        try:
            # 1. Generate the studio/lifestyle AI scene background
            if service == "gemini" or self.gemini.is_configured():
                logger.info("Generating AI background scene using Google Gemini...")
                scene_base64 = await self.gemini.generate_with_retry(
                    prompt=bg_prompt,
                    input_image_base64=input_image_base64,
                    max_retries=3,
                )
            else:
                logger.info(f"Generating AI background scene using {service}...")
                scene_base64 = await self.pollinations.generate_with_retry(
                    prompt=bg_prompt,
                    input_image_base64=input_image_base64,
                    width=1024,
                    height=1024,
                    max_retries=3,
                )

            # 2. Extract exact product cutout and composite onto the AI scene
            if input_image_base64:
                try:
                    from .product_compositor import extract_product_cutout, composite_product_on_scene
                    logger.info("Extracting exact product cutout and compositing onto AI scene...")
                    product_cutout = extract_product_cutout(input_image_base64)
                    is_white = "pure white" in prompt.lower() or "#ffffff" in prompt.lower() or "amazon white" in prompt.lower()
                    final_b64 = composite_product_on_scene(
                        product_cutout,
                        scene_base64,
                        is_pure_white_bg=is_white
                    )
                    return final_b64
                except Exception as comp_err:
                    logger.warning(f"Product compositing warning: {comp_err}. Returning AI scene.")


            return scene_base64


        except Exception as e:
            logger.exception(e)
            raise RuntimeError(f"Image generation failed: {e}")

    async def generate_seo(
        self, product: Dict[str, Any], settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive SEO keywords and metadata."""
        if not self.has_openrouter_configured():
            raise NoAPIKeyError("OpenRouter not configured")
        
        config = self.model_router.get_task_config("seo_generation")
        
        product_data = {
            k: v for k, v in product.items()
            if k not in ("images", "generated_images", "user_id", "id", "_id")
        }
        
        prompt = self.prompt_manager.get_prompt(
            "seo.comprehensive",
            {"product_data": product_data}
        )
        
        system = """You are an SEO specialist for e-commerce in India.
Generate comprehensive, high-converting SEO keywords and metadata.
Return STRICT JSON only."""
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        
        response_text, metadata = await self.openrouter.chat_completion(
            model=config["model"],
            messages=messages,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            response_format={"type": "json_object"},
        )
        
        raw_data = self.formatter.extract_json(response_text)
        validated_seo = self.formatter.validate_seo_response(raw_data)
        
        logger.info(f"Generated SEO with {metadata['model']}")
        
        return validated_seo

    def get_stats(self) -> Dict[str, Any]:
        """Get AI service statistics."""
        return {
            "openrouter": self.openrouter.get_stats(),
            "models": self.model_router.list_models(),
            "prompts_loaded": len(self.prompt_manager.list_available_prompts()),
            "image_generation_service": self.image_service,
            "image_generation_available": self.has_image_generation_configured(),
            "gemini_stats": self.gemini.get_stats(),
            "pollinations_stats": self.pollinations.get_stats(),
        }

