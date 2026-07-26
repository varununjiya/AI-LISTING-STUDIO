"""Modular Image Generation Abstraction Layer.

Defines the `ImageGenerationProvider` interface and concrete implementations for:
1. Google Gemini (Imagen 3 / Gemini Vision)
2. HuggingFace (FLUX / Stable Diffusion Inference API)
3. Pollinations AI (Fast, fallback)

Switched via `IMAGE_GENERATION_PROVIDER` environment variable or user settings.
"""
from __future__ import annotations

import os
import io
import base64
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import httpx

logger = logging.getLogger("image_providers")


class ImageGenerationProvider(ABC):
    """Abstract base class for all image generation providers."""

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        input_image_base64: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
    ) -> str:
        """Generate scene/product image and return base64 string without data URL prefix."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials/keys are configured."""
        pass


class GeminiImageProvider(ImageGenerationProvider):
    """Google Gemini / Imagen 3 Image Generation Provider."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_IMAGE_MODEL", "imagen-3.0-generate-002")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate_image(
        self,
        prompt: str,
        input_image_base64: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
    ) -> str:
        if not self.is_configured():
            logger.warning("Gemini API key not configured, falling back to Pollinations")
            return await PollinationsImageProvider().generate_image(prompt, input_image_base64, width, height)

        # Call Google GenAI / REST API for Imagen 3
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:predict?key={self.api_key}"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": "1:1"},
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                predictions = data.get("predictions", [])
                if predictions and "bytesBase64Encoded" in predictions[0]:
                    return predictions[0]["bytesBase64Encoded"]
            
            logger.warning("Gemini Imagen call failed (%s: %s). Falling back to Pollinations.", resp.status_code, resp.text[:100])
            return await PollinationsImageProvider().generate_image(prompt, input_image_base64, width, height)


class HuggingFaceImageProvider(ImageGenerationProvider):
    """HuggingFace Inference API Provider (FLUX.1-schnell / Stable Diffusion)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY", os.getenv("HF_TOKEN", ""))
        self.model = os.getenv("HUGGINGFACE_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate_image(
        self,
        prompt: str,
        input_image_base64: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
    ) -> str:
        if not self.is_configured():
            logger.warning("HuggingFace API key not configured, falling back to Pollinations")
            return await PollinationsImageProvider().generate_image(prompt, input_image_base64, width, height)

        url = f"https://api-inference.huggingface.co/models/{self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": prompt, "parameters": {"width": width, "height": height}}
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=30.0)
            if resp.status_code == 200:
                return base64.b64encode(resp.content).decode("utf-8")
            
            logger.warning("HuggingFace call failed (%s: %s). Falling back to Pollinations.", resp.status_code, resp.text[:100])
            return await PollinationsImageProvider().generate_image(prompt, input_image_base64, width, height)


class PollinationsImageProvider(ImageGenerationProvider):
    """Pollinations AI Provider (Fast & reliable fallback)."""

    def __init__(self):
        self.base_url = os.getenv("POLLINATIONS_API_URL", "https://image.pollinations.ai/prompt/")

    def is_configured(self) -> bool:
        return True  # Public endpoint

    async def generate_image(
        self,
        prompt: str,
        input_image_base64: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
    ) -> str:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"{self.base_url}{encoded_prompt}?width={width}&height={height}&nologo=true&seed=42"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=25.0)
            if resp.status_code == 200:
                return base64.b64encode(resp.content).decode("utf-8")
            raise RuntimeError(f"Pollinations image generation failed: HTTP {resp.status_code}")


def get_image_provider(provider_name: Optional[str] = None) -> ImageGenerationProvider:
    """Factory function to get configured ImageGenerationProvider."""
    name = (provider_name or os.getenv("IMAGE_GENERATION_PROVIDER", os.getenv("IMAGE_GENERATION_SERVICE", "gemini"))).lower()
    
    if name in ("gemini", "google"):
        return GeminiImageProvider()
    elif name in ("huggingface", "hf", "flux"):
        return HuggingFaceImageProvider()
    elif name in ("pollinations", "pollination"):
        return PollinationsImageProvider()
    
    logger.info("Defaulting to Gemini image generation provider")
    return GeminiImageProvider()
