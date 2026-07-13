"""Model Router - Routes tasks to optimal OpenRouter models."""
from __future__ import annotations

import os
from typing import Dict, Any, Literal
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

TaskType = Literal[
    "listing_generation",
    "seo_generation",
    "grammar_check",
    "vision_analysis",
    "image_generation",
]


class ModelRouter:
    """Routes different AI tasks to optimal models on OpenRouter."""

    def __init__(self):
        # Load model configuration from environment
        self.model_config = {
            "listing_generation": os.environ.get(
                "MODEL_LISTING_GENERATION", "deepseek/deepseek-chat"
            ),
            "seo_generation": os.environ.get(
                "MODEL_SEO_GENERATION", "qwen/qwen-2.5-72b-instruct"
            ),
            "grammar_check": os.environ.get(
                "MODEL_GRAMMAR_CHECK", "anthropic/claude-3.5-sonnet"
            ),
            "vision_analysis": os.environ.get(
                "MODEL_VISION_ANALYSIS", "qwen/qwen2-vl-72b-instruct"
            ),
            "image_generation": os.environ.get(
                "MODEL_IMAGE_GENERATION", "gemini-3.1-flash-image-preview"
            ),
        }
        
        # Temperature settings per task type
        self.temperature_config = {
            "listing_generation": 0.8,  # Creative but controlled
            "seo_generation": 0.6,  # More focused
            "grammar_check": 0.3,  # Precise
            "vision_analysis": 0.5,  # Balanced
            "image_generation": 0.7,  # Creative
        }
        
        # Max tokens per task
        self.max_tokens_config = {
            "listing_generation": 4000,
            "seo_generation": 2000,
            "grammar_check": 1000,
            "vision_analysis": 2000,
            "image_generation": 1000,
        }
    
    def get_model(self, task_type: TaskType) -> str:
        """Get the optimal model for a task type."""
        return self.model_config.get(task_type, "deepseek/deepseek-chat")
    
    def get_temperature(self, task_type: TaskType) -> float:
        """Get the optimal temperature for a task type."""
        return self.temperature_config.get(task_type, 0.7)
    
    def get_max_tokens(self, task_type: TaskType) -> int:
        """Get the optimal max tokens for a task type."""
        return self.max_tokens_config.get(task_type, 2000)
    
    def get_task_config(self, task_type: TaskType) -> Dict[str, Any]:
        """Get complete configuration for a task."""
        return {
            "model": self.get_model(task_type),
            "temperature": self.get_temperature(task_type),
            "max_tokens": self.get_max_tokens(task_type),
        }
    
    def list_models(self) -> Dict[str, str]:
        """List all configured models."""
        return self.model_config.copy()
