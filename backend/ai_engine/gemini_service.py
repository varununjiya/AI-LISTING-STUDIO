"""Google Gemini & Imagen 3 Image-to-Image (img2img) Generation Service."""
from __future__ import annotations

import os
import io
import base64
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
import httpx
from PIL import Image

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger("gemini_service")


class GeminiService:
    """Google Gemini & Imagen 3 Image-to-Image (img2img) generation service."""

    def __init__(self):
        self.request_count = 0
        self.api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or ""
        ).strip()
        
        self.model = os.getenv(
            "GEMINI_IMAGE_MODEL",
            "imagen-3.0-generate-002",
        )
        
        # Try initializing google-genai SDK if available
        self.genai_client = None
        if self.api_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Google GenAI SDK for Gemini img2img generation with model {self.model}")
            except Exception as e:
                logger.warning(f"Could not initialize google-genai SDK: {e}. Will use REST API fallback.")

    def get_api_key(self) -> str:
        """Retrieve API key dynamically from environment."""
        return (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or self.api_key
            or ""
        ).strip()

    def is_configured(self) -> bool:
        """Check if Gemini API Key is configured."""
        return bool(self.get_api_key())


    def _clean_base64(self, b64_str: str) -> str:
        """Strip data URL scheme prefix if present."""
        if "," in b64_str:
            return b64_str.split(",", 1)[1]
        return b64_str

    async def generate_image(
        self,
        prompt: str,
        input_image_base64: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        timeout: int = 120,
        **kwargs,
    ) -> str:
        """
        Generate an Image-to-Image (img2img) or Text-to-Image scene using Google Gemini / Imagen 3.

        Args:
            prompt: Generation prompt description.
            input_image_base64: Reference product image (base64 string) for img2img.
            width: Output width.
            height: Output height.
            timeout: Timeout in seconds.

        Returns:
            Base64 encoded PNG image string.
        """
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Prompt cannot be empty")

        api_key = self.get_api_key()
        if not api_key:
            logger.warning("GEMINI_API_KEY is not set. Falling back to Pollinations / FLUX service.")
            from .pollinations_service import get_pollinations_service
            pollinations = get_pollinations_service()
            return await pollinations.generate_image(
                prompt=prompt,
                input_image_base64=input_image_base64,
                width=width,
                height=height,
                timeout=timeout,
                **kwargs
            )

        logger.info(f"Generating img2img with Gemini model: {self.model} (input image provided: {bool(input_image_base64)})")

        clean_b64 = self._clean_base64(input_image_base64) if input_image_base64 else None

        # Approach 1: Try google-genai SDK if initialized
        if self.genai_client is None and api_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Could not initialize google-genai SDK at runtime: {e}")

        if self.genai_client is not None:
            try:
                from google.genai import types

                aspect_ratio = "1:1"
                if width > height * 1.2:
                    aspect_ratio = "16:9"
                elif height > width * 1.2:
                    aspect_ratio = "9:16"

                def _sdk_call():
                    if clean_b64:
                        # Convert base64 to PIL Image for GenAI multimodal / img2img call
                        img_bytes = base64.b64decode(clean_b64)
                        pil_img = Image.open(io.BytesIO(img_bytes))

                        # If using Gemini 2.0 / 2.5 Flash multimodal or Imagen 3 editing
                        if "gemini" in self.model.lower():
                            response = self.genai_client.models.generate_content(
                                model=self.model,
                                contents=[pil_img, prompt],
                            )
                            # Extract returned image bytes if returned in candidates
                            if response.candidates and response.candidates[0].content.parts:
                                for part in response.candidates[0].content.parts:
                                    if hasattr(part, "inline_data") and part.inline_data:
                                        return part.inline_data.data

                        # Imagen 3 Image-to-Image / Edit call
                        return self.genai_client.models.generate_images(
                            model=self.model,
                            prompt=prompt,
                            image=types.Image(image_bytes=img_bytes),
                            config=types.GenerateImagesConfig(
                                number_of_images=1,
                                output_mime_type="image/png",
                                aspect_ratio=aspect_ratio,
                            ),
                        )
                    else:
                        # Standard text-to-image call
                        return self.genai_client.models.generate_images(
                            model=self.model,
                            prompt=prompt,
                            config=types.GenerateImagesConfig(
                                number_of_images=1,
                                output_mime_type="image/png",
                                aspect_ratio=aspect_ratio,
                            ),
                        )

                result = await asyncio.wait_for(
                    asyncio.to_thread(_sdk_call),
                    timeout=timeout,
                )

                if isinstance(result, bytes):
                    image_b64 = base64.b64encode(result).decode("utf-8")
                    self.request_count += 1
                    logger.info(f"Successfully generated Gemini img2img #{self.request_count} via SDK content")
                    return image_b64
                elif result and hasattr(result, "generated_images") and result.generated_images:
                    image_bytes = result.generated_images[0].image.image_bytes
                    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                    self.request_count += 1
                    logger.info(f"Successfully generated Gemini img2img #{self.request_count} via SDK")
                    return image_b64

            except Exception as e:
                logger.warning(f"Google GenAI SDK call failed: {e}. Trying REST API fallback...")

        # Approach 2: Direct REST API call to Google Generative Language API (Imagen 3 / Gemini)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:predict?key={api_key}"

        
        instance_data = {"prompt": prompt}
        if clean_b64:
            instance_data["image"] = {"bytesBase64Encoded": clean_b64}

        payload = {
            "instances": [instance_data],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "outputOptions": {"mimeType": "image/png"}
            }
        }

        async with httpx.AsyncClient(timeout=float(timeout)) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                predictions = data.get("predictions") or []
                if predictions and "bytesBase64Encoded" in predictions[0]:
                    self.request_count += 1
                    logger.info(f"Successfully generated Gemini img2img #{self.request_count} via REST API")
                    return predictions[0]["bytesBase64Encoded"]
                elif predictions and "image" in predictions[0]:
                    self.request_count += 1
                    return predictions[0]["image"]["bytesBase64Encoded"]

            # If REST API returns error or non-200
            error_msg = resp.text
            logger.error(f"Gemini REST API Error ({resp.status_code}): {error_msg}")
            
            # Fallback to Pollinations if API fails
            logger.warning("Falling back to backup image service...")
            from .pollinations_service import get_pollinations_service
            pollinations = get_pollinations_service()
            return await pollinations.generate_image(
                prompt=prompt,
                input_image_base64=input_image_base64,
                width=width,
                height=height,
                timeout=timeout,
                **kwargs
            )

    async def generate_with_retry(
        self,
        prompt: str,
        input_image_base64: Optional[str] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        """Generate image with retry mechanism."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.generate_image(
                    prompt=prompt,
                    input_image_base64=input_image_base64,
                    **kwargs
                )
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"Gemini Retry {attempt + 1}/{max_retries} after {wait}s...")
                    await asyncio.sleep(wait)

        raise RuntimeError(f"Gemini img2img generation failed after retries: {last_error}")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "service": "Google Gemini (Imagen 3 img2img)",
            "model": self.model,
            "configured": self.is_configured(),
            "requests": self.request_count,
        }


_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Singleton getter for GeminiService."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
