"""Response Formatter - Parse and validate AI responses."""
from __future__ import annotations

import re
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("response_formatter")


class ResponseFormatter:
    """Parse, validate and format AI model responses."""

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """Extract JSON object from AI response text."""
        if not text:
            raise ValueError("Empty AI response")
        
        cleaned = text.strip()
        
        # Remove markdown code blocks
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        
        # Find JSON object boundaries
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        
        if start == -1 or end == -1:
            # Try to find JSON array
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start == -1 or end == -1:
                raise ValueError(f"No JSON object or array found in response: {text[:200]}")
        
        json_str = cleaned[start : end + 1]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}\nText: {json_str[:500]}")
            raise ValueError(f"Invalid JSON in AI response: {e}")
    
    @staticmethod
    def validate_listing_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize a listing generation response."""
        validated = {}
        
        # Amazon
        amazon = data.get("amazon", {})
        validated["amazon_title"] = str(amazon.get("title", ""))[:200]
        validated["amazon_bullets"] = [
            str(b)[:500] for b in (amazon.get("bullets", []) or [])[:5]
        ]
        validated["amazon_description"] = str(amazon.get("description", ""))[:2000]
        validated["amazon_backend_keywords"] = str(amazon.get("backend_keywords", ""))[:250]
        validated["amazon_search_terms"] = [
            str(t) for t in (amazon.get("search_terms", []) or [])[:15]
        ]
        validated["amazon_generic_keywords"] = [
            str(k) for k in (amazon.get("generic_keywords", []) or [])[:10]
        ]
        validated["amazon_subject_matter"] = [
            str(s) for s in (amazon.get("subject_matter", []) or [])[:5]
        ]
        validated["amazon_aplus_suggestions"] = [
            str(a) for a in (amazon.get("aplus_content_suggestions", []) or [])[:5]
        ]
        
        # Flipkart
        flipkart = data.get("flipkart", {})
        validated["flipkart_title"] = str(flipkart.get("title", ""))[:150]
        validated["flipkart_highlights"] = [
            str(h)[:120] for h in (flipkart.get("highlights", []) or [])[:6]
        ]
        validated["flipkart_description"] = str(flipkart.get("description", ""))[:2000]
        validated["flipkart_specifications"] = dict(flipkart.get("specifications", {}))
        validated["flipkart_search_keywords"] = [
            str(k) for k in (flipkart.get("search_keywords", []) or [])[:15]
        ]
        
        # Meesho
        meesho = data.get("meesho", {})
        validated["meesho_title"] = str(meesho.get("title", ""))[:120]
        validated["meesho_description"] = str(meesho.get("description", ""))[:1500]
        validated["meesho_highlights"] = [
            str(h) for h in (meesho.get("highlights", []) or [])[:6]
        ]
        validated["meesho_tags"] = [
            str(t) for t in (meesho.get("tags", []) or [])[:15]
        ]
        
        # SEO
        seo = data.get("seo", {})
        validated["seo_primary_keywords"] = [
            str(k) for k in (seo.get("primary_keywords", []) or [])[:5]
        ]
        validated["seo_secondary_keywords"] = [
            str(k) for k in (seo.get("secondary_keywords", []) or [])[:10]
        ]
        validated["seo_long_tail_keywords"] = [
            str(k) for k in (seo.get("long_tail_keywords", []) or [])[:10]
        ]
        validated["seo_trending_keywords"] = [
            str(k) for k in (seo.get("trending_keywords", []) or [])[:10]
        ]
        validated["seo_competitor_keywords"] = [
            str(k) for k in (seo.get("competitor_keywords", []) or [])[:10]
        ]
        validated["meta_description"] = str(seo.get("meta_description", ""))[:160]
        
        # Legacy compatibility
        validated["seo_keywords"] = (
            validated["seo_primary_keywords"] + validated["seo_secondary_keywords"]
        )
        validated["product_specifications"] = validated["flipkart_specifications"]
        
        return validated
    
    @staticmethod
    def validate_vision_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize a vision analysis response."""
        validated = {}
        
        fields = [
            "category", "sub_category", "material", "color", "pattern",
            "shape", "estimated_dimensions", "capacity", "product_type",
            "product_name", "brand", "features"
        ]
        
        for field in fields:
            value = data.get(field, "")
            validated[field] = str(value).strip() if value else ""
        
        return validated
    
    @staticmethod
    def validate_seo_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize an SEO generation response."""
        validated = {}
        
        validated["primary_keywords"] = [
            str(k) for k in (data.get("primary_keywords", []) or [])[:5]
        ]
        validated["secondary_keywords"] = [
            str(k) for k in (data.get("secondary_keywords", []) or [])[:10]
        ]
        validated["long_tail_keywords"] = [
            str(k) for k in (data.get("long_tail_keywords", []) or [])[:10]
        ]
        validated["trending_keywords"] = [
            str(k) for k in (data.get("trending_keywords", []) or [])[:10]
        ]
        validated["competitor_keywords"] = [
            str(k) for k in (data.get("competitor_keywords", []) or [])[:10]
        ]
        validated["meta_description"] = str(data.get("meta_description", ""))[:160]
        validated["seo_score"] = int(data.get("seo_score", 0))
        validated["readability_score"] = int(data.get("readability_score", 0))
        validated["keyword_density"] = float(data.get("keyword_density", 0.0))
        
        return validated
    
    @staticmethod
    def check_repetition(text: str, max_repetition_ratio: float = 0.3) -> bool:
        """Check if text has excessive word repetition."""
        if not text:
            return False
        
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        if not words:
            return False
        
        unique_ratio = len(set(words)) / len(words)
        return unique_ratio < (1 - max_repetition_ratio)
    
    @staticmethod
    def check_keyword_stuffing(text: str, keywords: List[str]) -> bool:
        """Check if text has keyword stuffing."""
        if not text or not keywords:
            return False
        
        text_lower = text.lower()
        total_words = len(text.split())
        
        if total_words == 0:
            return False
        
        keyword_count = sum(
            text_lower.count(kw.lower()) for kw in keywords
        )
        
        # If keywords appear more than 5% of total words, it's stuffing
        density = keyword_count / total_words
        return density > 0.05
