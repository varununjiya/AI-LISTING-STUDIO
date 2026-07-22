"""Exact Product Background Removal and Studio Scene Compositor."""
from __future__ import annotations

import io
import base64
import logging
from typing import Optional, Tuple
from PIL import Image, ImageFilter, ImageOps, ImageEnhance

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
            return cutout
        except Exception as e:
            logger.warning(f"rembg extraction failed: {e}. Using fallback matting.")

    # 2. Fallback PIL matting: luminance + edge thresholding to remove uniform light/dark backgrounds
    grayscale = src_img.convert("L")
    # Identify background color from corners
    w, h = src_img.size
    corner_pixels = [grayscale.getpixel((0, 0)), grayscale.getpixel((w - 1, 0)), grayscale.getpixel((0, h - 1)), grayscale.getpixel((w - 1, h - 1))]
    avg_bg = sum(corner_pixels) / len(corner_pixels)

    # Create alpha mask based on delta from background luminance
    mask = grayscale.point(lambda p: 255 if abs(p - avg_bg) > 22 else 0)
    mask = mask.filter(ImageFilter.GaussianBlur(1))

    cutout = src_img.copy()
    cutout.putalpha(mask)
    return cutout


def composite_product_on_scene(
    product_rgba: Image.Image,
    background_b64: str,
    target_width: int = 1024,
    target_height: int = 1024,
    product_scale: float = 0.65,
) -> str:
    """
    Composite the exact product cutout onto a generated background scene with realistic drop shadow.

    Returns:
        Base64 string of the final composite image.
    """
    # 1. Load background image
    clean_bg_b64 = background_b64.split(",", 1)[-1] if "," in background_b64 else background_b64
    bg_bytes = base64.b64decode(clean_bg_b64)
    bg_img = Image.open(io.BytesIO(bg_bytes)).convert("RGBA").resize((target_width, target_height), Image.Resampling.LANCZOS)

    # 2. Trim bounding box of product
    bbox = product_rgba.getbbox()
    if bbox:
        product_rgba = product_rgba.crop(bbox)

    pw, ph = product_rgba.size
    if pw == 0 or ph == 0:
        # Fallback if product empty
        buf = io.BytesIO()
        bg_img.convert("RGB").save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # 3. Calculate scaling for product to fit comfortably in the scene
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

    # 5. Create drop shadow under the product base
    shadow = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
    shadow_mask = resized_product.split()[3].point(lambda p: int(p * 0.35) if p > 0 else 0)
    
    # Shadow offset & blur
    shadow_offset_y = int(new_ph * 0.05)
    shadow_img = Image.new("RGBA", resized_product.size, (0, 0, 0, 255))
    shadow_img.putalpha(shadow_mask)
    shadow_img = shadow_img.resize((new_pw, int(new_ph * 0.25)), Image.Resampling.LANCZOS)
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(15))

    shadow_x = pos_x
    shadow_y = pos_y + new_ph - int(new_ph * 0.15)
    shadow.paste(shadow_img, (shadow_x, shadow_y), shadow_img)

    # 6. Composite layers: Background + Drop Shadow + Exact Product Cutout
    composite = Image.alpha_composite(bg_img, shadow)
    composite.paste(resized_product, (pos_x, pos_y), resized_product)

    # 7. Convert to RGB PNG & Return Base64
    final_rgb = composite.convert("RGB")
    buffer = io.BytesIO()
    final_rgb.save(buffer, format="PNG", quality=95)
    
    logger.info("Composited exact product onto AI background scene successfully")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
