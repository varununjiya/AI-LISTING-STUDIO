"""Exact Product Background Removal and Ultra-Polished Commercial Studio Scene Compositor."""
from __future__ import annotations

import io
import base64
import logging
from typing import Optional, Tuple
from PIL import Image, ImageFilter, ImageOps, ImageEnhance, ImageStat

logger = logging.getLogger("product_compositor")

# Optional rembg for high-precision AI background removal
try:
    from rembg import remove as rembg_remove
    HAS_REMBG = True
except Exception:
    HAS_REMBG = False
    logger.warning("rembg package not available. Falling back to PIL alpha matting.")


def extract_product_cutout(input_image_b64: str) -> Image.Image:
    """
    Extract the exact foreground product from the uploaded image base64,
    returning a RGBA PIL Image with transparent background.
    """
    clean_b64 = input_image_b64.split(",", 1)[-1] if "," in input_image_b64 else input_image_b64
    img_bytes = base64.b64decode(clean_b64)
    src_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    # 1. Try rembg AI cutout if available
    if HAS_REMBG:
        try:
            output_bytes = rembg_remove(img_bytes)
            cutout = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
            logger.info("Extracted product cutout using rembg AI model")
            return _smooth_alpha_edges(cutout)
        except Exception as e:
            logger.warning(f"rembg extraction failed: {e}. Using fallback matting.")

    # 2. Fallback PIL matting: luminance + edge thresholding to remove uniform light/dark backgrounds
    grayscale = src_img.convert("L")
    w, h = src_img.size
    corner_pixels = [
        grayscale.getpixel((0, 0)),
        grayscale.getpixel((w - 1, 0)),
        grayscale.getpixel((0, h - 1)),
        grayscale.getpixel((w - 1, h - 1))
    ]
    avg_bg = sum(corner_pixels) / len(corner_pixels)

    mask = grayscale.point(lambda p: 255 if abs(p - avg_bg) > 20 else 0)
    mask = mask.filter(ImageFilter.GaussianBlur(1))

    cutout = src_img.copy()
    cutout.putalpha(mask)
    return _smooth_alpha_edges(cutout)


def _smooth_alpha_edges(cutout: Image.Image) -> Image.Image:
    """Apply subtle anti-aliasing to alpha channel for ultra-smooth edge blending."""
    r, g, b, a = cutout.split()
    # Subtle blur to eliminate jagged edges
    a_smooth = a.filter(ImageFilter.GaussianBlur(0.8))
    smoothed = Image.merge("RGBA", (r, g, b, a_smooth))
    return smoothed


def composite_product_on_scene(
    product_rgba: Image.Image,
    background_b64: str,
    target_width: int = 1024,
    target_height: int = 1024,
    product_scale: float = 0.65,
    is_pure_white_bg: bool = False,
) -> str:
    """
    Composite the exact product cutout onto a generated background scene
    with dual-layer commercial studio shadows (Contact + Ambient Diffused).

    Returns:
        Base64 string of the final composite image.
    """
    # 1. Prepare background image
    if is_pure_white_bg:
        bg_img = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
    else:
        clean_bg_b64 = background_b64.split(",", 1)[-1] if "," in background_b64 else background_b64
        bg_bytes = base64.b64decode(clean_bg_b64)
        bg_img = Image.open(io.BytesIO(bg_bytes)).convert("RGBA").resize((target_width, target_height), Image.Resampling.LANCZOS)

    # 2. Trim bounding box of product cutout
    bbox = product_rgba.getbbox()
    if bbox:
        product_rgba = product_rgba.crop(bbox)

    pw, ph = product_rgba.size
    if pw == 0 or ph == 0:
        buf = io.BytesIO()
        bg_img.convert("RGB").save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # 3. Calculate scaling
    max_pw = int(target_width * product_scale)
    max_ph = int(target_height * product_scale)

    aspect = pw / ph
    if pw > max_pw or ph > max_ph:
        if aspect > 1:
            new_pw = max_pw
            new_ph = int(max_pw / aspect)
        else:
            new_ph = max_ph
            new_pw = int(max_ph * aspect)
    else:
        new_pw, new_ph = pw, ph

    resized_product = product_rgba.resize((new_pw, new_ph), Image.Resampling.LANCZOS)

    # 4. Position product in center / slightly lower center (tabletop position)
    pos_x = (target_width - new_pw) // 2
    pos_y = int((target_height - new_ph) * 0.55)

    # 5. Dual-Layer Shadow Synthesis
    shadow_layer = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
    alpha = resized_product.split()[3]

    # A) Layer 1: Tight Contact Shadow (Grounding)
    contact_mask = alpha.point(lambda p: int(p * 0.6) if p > 0 else 0)
    contact_img = Image.new("RGBA", resized_product.size, (15, 15, 20, 255))
    contact_img.putalpha(contact_mask)
    contact_img = contact_img.resize((new_pw, int(new_ph * 0.12)), Image.Resampling.LANCZOS)
    contact_img = contact_img.filter(ImageFilter.GaussianBlur(4))
    shadow_layer.paste(contact_img, (pos_x, pos_y + new_ph - int(new_ph * 0.06)), contact_img)

    # B) Layer 2: Soft Diffused Ambient Shadow
    ambient_mask = alpha.point(lambda p: int(p * 0.25) if p > 0 else 0)
    ambient_img = Image.new("RGBA", resized_product.size, (20, 20, 25, 255))
    ambient_img.putalpha(ambient_mask)
    ambient_img = ambient_img.resize((int(new_pw * 1.05), int(new_ph * 0.28)), Image.Resampling.LANCZOS)
    ambient_img = ambient_img.filter(ImageFilter.GaussianBlur(18))
    shadow_layer.paste(ambient_img, (pos_x - int(new_pw * 0.025), pos_y + new_ph - int(new_ph * 0.15)), ambient_img)

    # 6. Lighting Harmonization (Subtle Ambient Matching)
    harmonized_product = _harmonize_lighting(resized_product, bg_img)

    # 7. Composite layers: Background + Studio Shadow + Harmonized Product Cutout
    composite = Image.alpha_composite(bg_img, shadow_layer)
    composite.paste(harmonized_product, (pos_x, pos_y), harmonized_product)

    # 8. Return Base64 PNG
    final_rgb = composite.convert("RGB")
    buffer = io.BytesIO()
    final_rgb.save(buffer, format="PNG", quality=95)
    
    logger.info("Composited ultra-polished product onto AI background scene successfully")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _harmonize_lighting(product_img: Image.Image, bg_img: Image.Image) -> Image.Image:
    """Gently balance brightness & contrast of product cutout to match environment."""
    try:
        bg_stat = ImageStat.Stat(bg_img.convert("L"))
        bg_mean = bg_stat.mean[0]
        
        # Soft contrast and brightness enhancement
        if bg_mean > 200:
            # Bright environment: brighten product slightly
            enhancer = ImageEnhance.Brightness(product_img)
            return enhancer.enhance(1.04)
        elif bg_mean < 80:
            # Dark environment: subtle contrast boost
            enhancer = ImageEnhance.Contrast(product_img)
            return enhancer.enhance(1.05)
    except Exception:
        pass
    return product_img
