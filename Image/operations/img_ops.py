"""Core image operations: resize, crop, compress, convert, brightness/contrast, watermark"""
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import os


def _open(path: str) -> Image.Image:
    return Image.open(path).copy()


def resize_image(input_path: str, output_path: str, width: int, height: int, keep_aspect: bool = True) -> str:
    img = _open(input_path)
    if keep_aspect:
        img.thumbnail((width, height), Image.LANCZOS)
    else:
        img = img.resize((width, height), Image.LANCZOS)
    img.save(output_path)
    return output_path


def crop_image(input_path: str, output_path: str, left: int, top: int, right: int, bottom: int) -> str:
    img = _open(input_path)
    img = img.crop((left, top, right, bottom))
    img.save(output_path)
    return output_path


def compress_image(input_path: str, output_path: str, quality: int = 60) -> str:
    """Compress image by reducing JPEG quality (1-95)."""
    img = _open(input_path).convert("RGB")
    img.save(output_path, "JPEG", quality=quality, optimize=True)
    return output_path


def convert_image(input_path: str, output_path: str) -> str:
    """Convert between JPG, PNG, WEBP based on output_path extension."""
    img = _open(input_path)
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        img = img.convert("RGB")
    img.save(output_path)
    return output_path


def adjust_brightness_contrast(input_path: str, output_path: str,
                                brightness: float = 1.0, contrast: float = 1.0) -> str:
    """
    Adjust brightness and contrast.
    1.0 = original, <1.0 = darker/less contrast, >1.0 = brighter/more contrast
    """
    img = _open(input_path)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img.save(output_path)
    return output_path


def add_watermark(input_path: str, output_path: str, text: str,
                  opacity: int = 128, font_size: int = 40, color: str = "white") -> str:
    """Add diagonal text watermark to an image."""
    img = _open(input_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    # Get text size and tile across image
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    r, g, b = (255, 255, 255)
    try:
        from PIL import ImageColor
        r, g, b = ImageColor.getrgb(color)
    except Exception:
        pass

    step_x = tw + 80
    step_y = th + 80
    for x in range(-img.width, img.width * 2, step_x):
        for y in range(-img.height, img.height * 2, step_y):
            draw.text((x, y), text, font=font, fill=(r, g, b, opacity))

    watermarked = Image.alpha_composite(img, overlay)
    if os.path.splitext(output_path)[1].lower() in (".jpg", ".jpeg"):
        watermarked = watermarked.convert("RGB")
    watermarked.save(output_path)
    return output_path


def compress_image_to_size(input_path: str, output_path: str, target_size_kb: float) -> str:
    """
    Compresses an image to a target file size in KBs.
    Iterates over image quality and scales if necessary to get close to the target.
    """
    img = _open(input_path)
    
    ext = os.path.splitext(output_path)[1].lower()
    save_format = "JPEG"
    if ext == ".webp":
        save_format = "WEBP"
    
    if save_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")
        
    target_bytes = target_size_kb * 1024
    
    # Try adjusting quality first (between 5 and 95)
    low_q, high_q = 5, 95
    best_q = 75
    
    for _ in range(8):
        q = (low_q + high_q) // 2
        temp_path = output_path + ".tmp"
        try:
            img.save(temp_path, save_format, quality=q, optimize=True)
            size = os.path.getsize(temp_path)
            os.remove(temp_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            break
            
        if size <= target_bytes:
            best_q = q
            low_q = q + 1
        else:
            high_q = q - 1
            
    # Save with best quality found
    img.save(output_path, save_format, quality=best_q, optimize=True)
    
    # If the file size is still too large at quality=5, we need to downscale
    final_size = os.path.getsize(output_path)
    if final_size > target_bytes:
        width, height = img.size
        # Try downscaling in steps of 10%
        for scale in [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]:
            new_w = max(10, int(width * scale))
            new_h = max(10, int(height * scale))
            resized_img = img.resize((new_w, new_h), Image.LANCZOS)
            
            temp_path = output_path + ".tmp"
            try:
                resized_img.save(temp_path, save_format, quality=10, optimize=True)
                size = os.path.getsize(temp_path)
                os.remove(temp_path)
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                break
                
            if size <= target_bytes:
                resized_img.save(output_path, save_format, quality=10, optimize=True)
                break
        else:
            # Save at minimum dimensions/quality if still too large
            resized_img = img.resize((max(10, int(width * 0.05)), max(10, int(height * 0.05))), Image.LANCZOS)
            resized_img.save(output_path, save_format, quality=5, optimize=True)
            
    return output_path

