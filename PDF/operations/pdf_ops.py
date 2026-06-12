"""PDF Operations: Merge, Split, Compress, Password Protect, Remove Password"""
import fitz  # PyMuPDF
import os


def merge_pdfs(input_paths: list[str], output_path: str) -> str:
    """Merge multiple PDFs into one."""
    doc = fitz.open()
    for path in input_paths:
        with fitz.open(path) as src:
            doc.insert_pdf(src)
    doc.save(output_path)
    doc.close()
    return output_path


def split_pdf(input_path: str, output_dir: str, pages_per_split: int = 1) -> list[str]:
    """Split a PDF into chunks of pages_per_split pages each."""
    os.makedirs(output_dir, exist_ok=True)
    results = []
    with fitz.open(input_path) as doc:
        total = len(doc)
        base = os.path.splitext(os.path.basename(input_path))[0]
        for start in range(0, total, pages_per_split):
            end = min(start + pages_per_split, total)
            out = fitz.open()
            out.insert_pdf(doc, from_page=start, to_page=end - 1)
            out_path = os.path.join(output_dir, f"{base}_{start+1}-{end}.pdf")
            out.save(out_path)
            out.close()
            results.append(out_path)
    return results


def compress_pdf(input_path: str, output_path: str) -> str:
    """Compress PDF by reducing image quality and removing redundant data."""
    with fitz.open(input_path) as doc:
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n > 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                compressed = fitz.Pixmap(pix)
                doc.update_stream(xref, compressed.tobytes("jpeg", jpg_quality=60))
        doc.save(output_path, garbage=4, deflate=True, clean=True)
    return output_path


def protect_pdf(input_path: str, output_path: str, user_password: str, owner_password: str = "") -> str:
    """Add password protection to a PDF."""
    if not owner_password:
        owner_password = user_password
    with fitz.open(input_path) as doc:
        doc.save(
            output_path,
            user_pw=user_password,
            owner_pw=owner_password,
            encryption=fitz.PDF_ENCRYPT_AES_256,
        )
    return output_path


def remove_password(input_path: str, output_path: str, password: str) -> str:
    """Remove password from a protected PDF."""
    with fitz.open(input_path) as doc:
        if doc.is_encrypted:
            if not doc.authenticate(password):
                raise ValueError("Incorrect password.")
        doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
    return output_path
