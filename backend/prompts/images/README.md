# Image Generation Prompts

These prompts are used by the AI Image Studio to generate different product images.

Presets are defined in ai_service.py IMAGE_PRESETS.

Each preset includes:
- id: Unique identifier
- label: Display name
- group: Category (studio/lifestyle/commerce/social)
- prompt: Base prompt for image generation

The AI Engine will append critical instructions to maintain product consistency.