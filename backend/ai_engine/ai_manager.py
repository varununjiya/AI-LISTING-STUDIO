"""AI Manager - Central orchestrator for all AI operations."""
from __future__ import annotations

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

from .openrouter_service import OpenRouterService, NoAPIKeyError as ORNoAPIKeyError
from .model_router import ModelRouter
from .prompt_manager import PromptManager
from .response_formatter import ResponseFormatter

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger("ai_manager")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
IMAGE_MODEL = os.environ.get("MODEL_IMAGE_GENERATION", "gemini-3.1-flash-image-preview")


class NoAPIKeyError(Exception):
    """Raised when no API key is configured."""


class AIManager:
    """Central AI orchestrator using OpenRouter for text/vision and Gemini for image gen."""

    def __init__(self):
        self.openrouter = OpenRouterService()
        self.model_router = ModelRouter()
        self.prompt_manager = PromptManager()
        self.formatter = ResponseFormatter()
    
    def has_openrouter_configured(self) -> bool:
        """Check if OpenRouter is configured."""
        try:
            self.openrouter.get_active_key()
            return True
        except ORNoAPIKeyError:
            return False
    
    def has_image_generation_configured(self) -> bool:
        """Check if image generation (via Emergent Key) is configured."""
        return bool(EMERGENT_LLM_KEY)
    
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
        self, input_image_base64: str, prompt: str, settings: Dict[str, Any]
    ) -> str:
        """Generate product image with different background/scene (via Emergent Nano Banana).
        
        Returns base64 string (no data URL prefix).
        """
        if not EMERGENT_LLM_KEY:
            raise NoAPIKeyError(
                "Image generation requires EMERGENT_LLM_KEY in backend/.env"
            )
        
        # Strip data URL prefix
        b64 = input_image_base64.split(",", 1)[1] if input_image_base64.startswith("data:") else input_image_base64
        
        # Use emergentintegrations for image generation (Nano Banana)
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id="image-studio",
            system_message="You are an expert product photographer."
        )
        chat.with_model("gemini", IMAGE_MODEL).with_params(modalities=["image", "text"])
        
        # Enhanced prompt
        full_prompt = (
            prompt
            + " CRITICAL: Keep the product COMPLETELY UNCHANGED (same shape, colors, "
            "text, logos, details). Only change the background, environment, and presentation. "
            "Output a photorealistic, high-resolution image."
        )
        
        msg = UserMessage(text=full_prompt, file_contents=[ImageContent(b64)])
        _, images = await chat.send_message_multimodal_response(msg)
        
        if not images:
            raise ValueError("No image returned by Nano Banana")
        
        logger.info(f"Generated scene image with {IMAGE_MODEL}")
        
        return images[0]["data"]  # base64 string
    
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
            "image_generation_available": self.has_image_generation_configured(),
        }
