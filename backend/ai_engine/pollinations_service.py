"""Pollinations.ai Image Generation Service (FREE Unlimited FLUX)."""
from __future__ import annotations

import io
import base64
import logging
import urllib.parse
import asyncio
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger("pollinations_service")


class PollinationsService:
    """Pollinations.ai FREE FLUX image generation service."""

    def __init__(self):
        self.request_count = 0
        self.api_url = "https://image.pollinations.ai/prompt/"

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
        Generate an image using Pollinations.ai FLUX (Free API).

        Returns:
            Base64 encoded PNG image string.
        """
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Prompt cannot be empty")

        encoded_prompt = urllib.parse.quote(prompt)
        url = f"{self.api_url}{encoded_prompt}?width={width}&height={height}&nologo=true&model=flux"

        logger.info(f"Generating image via Pollinations.ai FLUX: {prompt[:60]}...")

        async with httpx.AsyncClient(timeout=float(timeout), follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and resp.content:
                image_base64 = base64.b64encode(resp.content).decode("utf-8")
                self.request_count += 1
                logger.info(f"Successfully generated Pollinations image #{self.request_count}")
                return image_base64

            raise RuntimeError(f"Pollinations API Error ({resp.status_code}): {resp.text[:200]}")

    async def generate_with_retry(
        self,
        prompt: str,
        input_image_base64: Optional[str] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
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
                    logger.warning(f"Pollinations Retry {attempt + 1}/{max_retries} after {wait}s...")
                    await asyncio.sleep(wait)

        raise RuntimeError(f"Pollinations image generation failed after retries: {last_error}")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "service": "Pollinations.ai (FLUX)",
            "model": "flux",
            "requests": self.request_count,
        }


_pollinations_service: Optional[PollinationsService] = None


def get_pollinations_service() -> PollinationsService:
    global _pollinations_service
    if _pollinations_service is None:
        _pollinations_service = PollinationsService()
    return _pollinations_service
