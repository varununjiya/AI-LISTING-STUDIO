"""Pollinations.ai Image Generation Service - Free, No API Key Required."""
from __future__ import annotations

import os
import base64
import logging
import asyncio
from typing import Optional
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger("pollinations_service")

POLLINATIONS_API_URL = os.environ.get(
    "POLLINATIONS_API_URL", 
    "https://image.pollinations.ai/prompt/"
)


class PollinationsService:
    """Pollinations.ai image generation service - completely free!"""
    
    def __init__(self):
        self.base_url = POLLINATIONS_API_URL
        self.request_count = 0
    
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        model: str = "flux",  # Options: flux, flux-realism, flux-anime, turbo
        enhance: bool = True,
        timeout: int = 60,
    ) -> str:
        """Generate an image using Pollinations.ai.
        
        Args:
            prompt: Text description of the image
            width: Image width (default 1024)
            height: Image height (default 1024)
            seed: Random seed for reproducibility (optional)
            model: Model to use (flux, flux-realism, flux-anime, turbo)
            enhance: Whether to enhance the prompt
            timeout: Request timeout in seconds
            
        Returns:
            Base64 encoded image string (no data URL prefix)
        """
        # Clean and encode the prompt
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Prompt cannot be empty")
        
        # Build the URL with parameters
        # Format: https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&seed={s}&model={m}&enhance={e}
        params = {
            "width": width,
            "height": height,
            "model": model,
            "nologo": "true",  # Remove pollinations logo
            "private": "true",  # Don't save to public gallery
        }
        
        if enhance:
            params["enhance"] = "true"
        
        if seed is not None:
            params["seed"] = seed
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Pollinations URL format: base_url + encoded_prompt + params
                url = f"{self.base_url}{clean_prompt}"
                
                logger.info(f"Generating image with Pollinations.ai: {clean_prompt[:50]}...")
                
                response = await client.get(url, params=params, follow_redirects=True)
                response.raise_for_status()
                
                # Get image bytes
                image_bytes = response.content
                
                # Convert to base64
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                self.request_count += 1
                
                logger.info(
                    f"Successfully generated image with Pollinations.ai "
                    f"({len(image_bytes)} bytes, request #{self.request_count})"
                )
                
                return image_base64
                
        except httpx.TimeoutException:
            logger.error(f"Pollinations.ai request timed out after {timeout}s")
            raise TimeoutError(f"Image generation timed out after {timeout} seconds")
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Pollinations.ai HTTP error: {e.response.status_code}")
            raise RuntimeError(f"Pollinations.ai API error: {e.response.status_code}")
        
        except Exception as e:
            logger.error(f"Pollinations.ai error: {e}")
            raise RuntimeError(f"Image generation failed: {str(e)}")
    
    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 2,
        **kwargs
    ) -> str:
        """Generate image with retry logic."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.generate_image(prompt, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Pollinations.ai attempt {attempt + 1} failed, "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
        
        raise RuntimeError(
            f"Failed to generate image after {max_retries} attempts: {last_error}"
        )
    
    def get_stats(self) -> dict:
        """Get service statistics."""
        return {
            "service": "Pollinations.ai",
            "total_requests": self.request_count,
            "cost": "$0.00 (Free Forever)",
            "api_url": self.base_url,
        }


# Singleton instance
_pollinations_service: Optional[PollinationsService] = None


def get_pollinations_service() -> PollinationsService:
    """Get or create the Pollinations service instance."""
    global _pollinations_service
    if _pollinations_service is None:
        _pollinations_service = PollinationsService()
    return _pollinations_service
