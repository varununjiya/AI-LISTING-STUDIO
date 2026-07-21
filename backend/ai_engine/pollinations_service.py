"""Hugging Face FLUX Image Generation Service."""
from __future__ import annotations

import os
import io
import base64
import logging
import asyncio
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger("huggingface_service")


class HuggingFaceService:
    """Hugging Face FLUX image generation service."""

    def __init__(self):
        self.request_count = 0

        self.client = InferenceClient(
            provider="hf-inference",
            api_key=os.getenv("HF_TOKEN"),
        )

        self.model = os.getenv(
            "HF_MODEL",
            "black-forest-labs/FLUX.1-schnell",
        )

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        timeout: int = 120,
        **kwargs,
    ) -> str:
        """
        Generate an image using Hugging Face FLUX.

        Returns:
            Base64 encoded PNG image.
        """

        prompt = prompt.strip()

        if not prompt:
            raise ValueError("Prompt cannot be empty")

        logger.info(f"Generating image with {self.model}")

        try:

            image = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.text_to_image,
                    prompt=prompt,
                    model=self.model,
                ),
                timeout=timeout,
            )

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")

            image_base64 = base64.b64encode(
                buffer.getvalue()
            ).decode("utf-8")

            self.request_count += 1

            logger.info(
                f"Successfully generated image #{self.request_count}"
            )

            return image_base64

        except asyncio.TimeoutError:
            logger.error("Image generation timed out.")
            raise RuntimeError("Image generation timed out.")

        except Exception as e:
            logger.exception(e)
            raise RuntimeError(f"Hugging Face API Error: {str(e)}")

    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs,
    ) -> str:

        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.generate_image(
                    prompt=prompt,
                    **kwargs,
                )

            except Exception as e:
                last_error = e

                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} after {wait}s..."
                    )
                    await asyncio.sleep(wait)

        raise RuntimeError(last_error)

    def get_stats(self):

        return {
            "service": "Hugging Face",
            "model": self.model,
            "requests": self.request_count,
        }


_huggingface_service: Optional[HuggingFaceService] = None


def get_pollinations_service():
    """
    Keeping the same function name so
    the rest of your project doesn't need changes.
    """

    global _huggingface_service

    if _huggingface_service is None:
        _huggingface_service = HuggingFaceService()

    return _huggingface_service
