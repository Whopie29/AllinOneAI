"""AI operations: Background Removal, Background Color Change, OCR"""
from PIL import Image
import os


def remove_background(input_path: str, output_path: str) -> str:
    """Remove background using rembg."""
    from rembg import remove
    with open(input_path, "rb") as f:
        result = remove(f.read())
    # Ensure output is PNG (supports transparency)
    out = output_path if output_path.lower().endswith(".png") else os.path.splitext(output_path)[0] + ".png"
    with open(out, "wb") as f:
        f.write(result)
    return out


def change_background_color(input_path: str, output_path: str, color: tuple = (255, 255, 255)) -> str:
    """
    Remove background then fill with a solid color.
    color: RGB tuple e.g. (255, 255, 255) for white
    """
    from rembg import remove
    from io import BytesIO
    with open(input_path, "rb") as f:
        result = remove(f.read())
    fg = Image.open(BytesIO(result)).convert("RGBA")
    bg = Image.new("RGBA", fg.size, color + (255,))
    bg.paste(fg, mask=fg.split()[3])
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        bg = bg.convert("RGB")
    bg.save(output_path)
    return output_path


def image_to_text(input_path: str) -> str:
    """Extract text from image using EasyOCR."""
    import easyocr
    reader = easyocr.Reader(["en"], gpu=False)
    results = reader.readtext(input_path, detail=0)
    return "\n".join(results)
