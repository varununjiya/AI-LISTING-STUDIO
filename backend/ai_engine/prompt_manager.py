"""Prompt Manager - Load and manage AI prompts from template files."""
from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("prompt_manager")

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptManager:
    """Manages AI prompts loaded from template files."""

    def __init__(self):
        self.prompts_cache: Dict[str, str] = {}
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompt templates into cache."""
        if not PROMPTS_DIR.exists():
            logger.warning(f"Prompts directory not found: {PROMPTS_DIR}")
            return
        
        # Load all .txt prompt files
        for prompt_file in PROMPTS_DIR.rglob("*.txt"):
            relative_path = prompt_file.relative_to(PROMPTS_DIR)
            key = str(relative_path.with_suffix("")).replace(os.sep, ".")
            
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    self.prompts_cache[key] = f.read().strip()
                logger.info(f"Loaded prompt: {key}")
            except Exception as e:
                logger.error(f"Failed to load prompt {key}: {e}")
    
    def get_prompt(self, key: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """Get a prompt template and optionally fill variables.
        
        Args:
            key: Prompt key (e.g., "amazon.title", "seo.keywords")
            variables: Optional dict of variables to substitute in the template
        
        Returns:
            The prompt text with variables substituted
        """
        template = self.prompts_cache.get(key)
        
        if not template:
            logger.warning(f"Prompt not found: {key}, using fallback")
            return self._get_fallback_prompt(key)
        
        if not variables:
            return template
        
        # Simple variable substitution: {variable_name}
        prompt = template
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if isinstance(var_value, (dict, list)):
                var_value = json.dumps(var_value, ensure_ascii=False, indent=2)
            prompt = prompt.replace(placeholder, str(var_value))
        
        return prompt
    
    def _get_fallback_prompt(self, key: str) -> str:
        """Get a hardcoded fallback prompt if template file is missing."""
        fallbacks = {
            "amazon.full_listing": self._amazon_full_listing_fallback(),
            "flipkart.full_listing": self._flipkart_full_listing_fallback(),
            "meesho.full_listing": self._meesho_full_listing_fallback(),
            "seo.keywords": self._seo_keywords_fallback(),
            "analysis.vision": self._vision_analysis_fallback(),
        }
        return fallbacks.get(key, "Generate high-quality content based on the provided information.")
    
    def _amazon_full_listing_fallback(self) -> str:
        return """You are a senior Amazon copywriter. Write a complete Amazon listing with:
- SEO-optimized title (max 200 characters)
- 5 benefit-focused bullet points (each max 500 characters)
- Engaging description (max 2000 characters)
- Backend keywords (max 250 characters, space-separated)
- 8-12 search terms
- Generic keywords and subject matter

Use natural language, avoid repetition, and include relevant keywords naturally."""
    
    def _flipkart_full_listing_fallback(self) -> str:
        return """You are a Flipkart listing specialist. Write a complete Flipkart listing with:
- Title (max 150 characters)
- 5-6 highlights (each max 120 characters)
- Description (max 2000 characters)
- Product specifications as key-value pairs
- 8-12 search keywords

Focus on features, benefits, and specifications."""
    
    def _meesho_full_listing_fallback(self) -> str:
        return """You are a Meesho marketplace expert. Write a complete Meesho listing with:
- Title (max 120 characters)
- Description (max 1500 characters)
- 4-6 highlights
- 8-12 discovery tags

Use simple, clear language that appeals to value-conscious buyers."""
    
    def _seo_keywords_fallback(self) -> str:
        return """You are an SEO specialist. Generate comprehensive SEO keywords including:
- 3-5 primary keywords
- 5-8 secondary keywords
- 5-8 long-tail keywords
- 4-6 trending keywords
- 4-6 competitor keywords
- Meta description (max 160 characters)
- SEO score (0-100)
- Readability score (0-100)
- Keyword density percentage

Return strict JSON format."""
    
    def _vision_analysis_fallback(self) -> str:
        return """You are a product cataloguing expert. Analyze the product image and extract:
- Category and subcategory
- Material and color
- Pattern and shape
- Estimated dimensions
- Capacity (if applicable)
- Product type
- Product name
- Brand (if visible)
- Key visible features

Return strict JSON format."""
    
    def list_available_prompts(self) -> list[str]:
        """List all available prompt keys."""
        return sorted(self.prompts_cache.keys())
    
    def reload_prompts(self):
        """Reload all prompts from files."""
        self.prompts_cache.clear()
        self._load_all_prompts()
