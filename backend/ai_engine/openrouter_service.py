"""OpenRouter API Service with retry logic and key rotation."""
from __future__ import annotations

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger("openrouter_service")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterError(Exception):
    """OpenRouter API error."""


class NoAPIKeyError(Exception):
    """No valid API key available."""


class OpenRouterService:
    """OpenRouter API client with automatic key rotation and retry logic."""

    def __init__(self):
        # Load all configured OpenRouter keys
        self.api_keys: List[str] = []
        for i in range(1, 10):  # Support up to 9 keys
            key = os.environ.get(f"OPENROUTER_API_KEY_{i}", "").strip()
            if key:
                self.api_keys.append(key)
        
        self.current_key_index = 0
        self.failed_keys: set = set()
        self.request_count = 0
        
        if not self.api_keys:
            logger.warning("No OpenRouter API keys configured")
    
    def get_active_key(self) -> str:
        """Get the current active API key."""
        if not self.api_keys:
            raise NoAPIKeyError("No OpenRouter API keys configured. Please add OPENROUTER_API_KEY_1 to .env")
        
        # Try to find a non-failed key
        for _ in range(len(self.api_keys)):
            key = self.api_keys[self.current_key_index]
            if key not in self.failed_keys:
                return key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        # All keys failed, reset and try again
        logger.warning("All API keys failed, resetting failure tracking")
        self.failed_keys.clear()
        return self.api_keys[self.current_key_index]
    
    def rotate_key(self):
        """Rotate to the next API key."""
        if len(self.api_keys) > 1:
            old_key = self.api_keys[self.current_key_index]
            self.failed_keys.add(old_key)
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f"Rotated API key (now using key #{self.current_key_index + 1})")
    
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
    ) -> Tuple[str, Dict[str, Any]]:
        """Send a chat completion request to OpenRouter.
        
        Returns:
            Tuple of (response_text, metadata)
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                api_key = self.get_active_key()
                
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{OPENROUTER_BASE_URL}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://ai-listing-studio.emergentagent.com",
                            "X-Title": "AI Listing Studio",
                        },
                        json=payload,
                    )
                    
                    self.request_count += 1
                    
                    if response.status_code == 429:
                        # Rate limit hit, rotate key and retry
                        logger.warning(f"Rate limit hit on key #{self.current_key_index + 1}, rotating...")
                        self.rotate_key()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    
                    if response.status_code == 401:
                        # Invalid key, rotate and retry
                        logger.error(f"Invalid API key #{self.current_key_index + 1}, rotating...")
                        self.rotate_key()
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if "error" in data:
                        raise OpenRouterError(f"OpenRouter error: {data['error']}")
                    
                    content = data["choices"][0]["message"]["content"]
                    
                    metadata = {
                        "model": data.get("model", model),
                        "usage": data.get("usage", {}),
                        "key_index": self.current_key_index + 1,
                        "attempt": attempt + 1,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    
                    return content, metadata
                    
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error(f"HTTP error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                last_error = e
                logger.error(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        raise OpenRouterError(f"Failed after {max_retries} attempts: {last_error}")
    
    async def vision_completion(
        self,
        model: str,
        prompt: str,
        image_base64: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Tuple[str, Dict[str, Any]]:
        """Send a vision completion request with an image."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        },
                    },
                ],
            }
        ]
        
        return await self.chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "total_requests": self.request_count,
            "active_keys": len(self.api_keys),
            "current_key_index": self.current_key_index + 1,
            "failed_keys_count": len(self.failed_keys),
        }
