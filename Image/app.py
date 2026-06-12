"""Image Processing Suite — Tkinter GUI"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from operations.img_ops import (
    resize_image, crop_image, compress_image,
    convert_image, adjust_brightness_contrast, add_watermark,
)
from operations.ai_ops import remove_background, change_background_color, image_to_text

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
BG     = "#1e1e2e"
PANEL  = "#2a2a3e"
ACCENT = "#0ea5e9"
ACCENT2= "#38bdf8"
FG     = "#e2e8f0"
FG2    = "#94a3b8"
FONT      = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_H    = ("Segoe UI", 13, "bold")
FONT_SM   = ("Segoe UI", 9)

IMG_TYPES = [("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff")]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask_open(title="Open Image"):
    return filedialog.askopenfilename(title=title, filetypes=IMG_TYPES)

def ask_save(title="Save As", ext=".png", filetypes=None):
    ft = filetypes or [("PNG", "*.png"), ("JPEG", "*.jpg"), ("WEBP", "*.webp")]
    return filedialog.asksaveasfilename(title=title, defaultextension=ext, filetypes=ft)

def run_task(fn, *args, status_var=None, success_msg="Done!", on_done=None):
    def _worker():
        try:
            if status_var: status_var.set("⏳ Working…")
            result = fn(*args)
            if status_var: status_var.set(f"✅ {success_msg}")
            if on_done: on_done(result)
        except Exception as e:
            if status_var: status_var.set(f"❌ {e}")
            messagebox.showerror("Error", str(e))
    threading.Thread(target=_worker, daemon=True).start()

def styled_btn(parent, text, command, accent=False):
    return tk.Button(parent, text=text, command=command,
                     bg=ACCENT if accent else PANEL, fg=FG,
                     activebackground=ACCENT2, activeforeground=FG,
                     font=FONT, relief="flat", bd=0, padx=12, pady=6, cursor="hand2")

def section_label(parent, text):
    return tk.Label(parent, text=text, font=FONT_H, bg=BG, fg=ACCENT2)

def status_label(parent, var):
    return tk.Label(parent, textvariable=var, font=FONT_SM, bg=BG, fg=FG2, wraplength=540, justify="left")

def entry_row(parent, label, default="", width=8):
    f = tk.Frame(parent, bg=BG)
    tk.Label(f, text=label, bg=BG, fg=FG, font=FONT, width=14, anchor="w").pack(side="left")
    var = tk.StringVar(value=default)
    tk.Entry(f, textvariable=var, width=width, bg=PANEL, fg=FG, font=FONT,
             insertbackground=FG, relief="flat").pack(side="left", padx=4)
    return f, var

def scale_row(parent, label, from_, to, default, resolution=0.1):
    f = tk.Frame(parent, bg=BG)
    tk.Label(f, text=label, bg=BG, fg=FG, font=FONT, width=14, anchor="w").pack(side="left")
    var = tk.DoubleVar(value=default)
    tk.Scale(f, variable=var, from_=from_, to=to, resolution=resolution,
             orient="horizontal", bg=BG, fg=FG, troughcolor=PANEL,
             highlightthickness=0, length=160).pack(side="left")
    return f, var

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

def build_resize_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Resize Image").pack(anchor="w", pady=(10,4))
    r1, w_var = entry_row(frame, "Width (px)", "800")
    r1.pack(anchor="w", pady=2)
    r2, h_var = entry_row(frame, "Height (px)", "600")
    r2.pack(anchor="w", pady=2)
    aspect_var = tk.BooleanVar(value=True)
    tk.Checkbutton(frame, text="Keep aspect ratio", variable=aspect_var,
                   bg=BG, fg=FG, selectcolor=PANEL, activebackground=BG,
                   font=FONT).pack(anchor="w", pady=4)

    def do_resize():
        path = ask_open()
        if not path: return
        out = ask_save("Save Resized Image")
        if not out: return
        try:
            w, h = int(w_var.get()), int(h_var.get())
        except ValueError:
            messagebox.showerror("Error", "Width and height must be integers."); return
        run_task(resize_image, path, out, w, h, aspect_var.get(), status_var=status, success_msg="Resized!")

    styled_btn(frame, "↔ Resize", do_resize, accent=True).pack(anchor="w", pady=6)
    status_label(frame, status).pack(anchor="w")


def build_crop_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Crop Image").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Coordinates in pixels from top-left corner.", bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")
    r1, l_var = entry_row(frame, "Left",   "0")
    r2, t_var = entry_row(frame, "Top",    "0")
    r3, ri_var= entry_row(frame, "Right",  "800")
    r4, b_var = entry_row(frame, "Bottom", "600")
    for r in [r1,r2,r3,r4]: r.pack(anchor="w", pady=2)

    def do_crop():
        path = ask_open()
        if not path: return
        out = ask_save("Save Cropped Image")
        if not out: return
        try:
            coords = int(l_var.get()), int(t_var.get()), int(ri_var.get()), int(b_var.get())
        except ValueError:
            messagebox.showerror("Error", "All values must be integers."); return
        run_task(crop_image, path, out, *coords, status_var=status, success_msg="Cropped!")

    styled_btn(frame, "✂ Crop", do_crop, accent=True).pack(anchor="w", pady=6)
    status_label(frame, status).pack(anchor="w")


def build_compress_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Compress Image").pack(anchor="w", pady=(10,4))
    r, q_var = scale_row(frame, "Quality", 5, 95, 60, resolution=1)
    r.pack(anchor="w", pady=4)

    def do_compress():
        path = ask_open()
        if not path: return
        out = ask_save("Save Compressed Image", ".jpg", [("JPEG", "*.jpg")])
        if not out: return
        run_task(compress_image, path, out, int(q_var.get()), status_var=status, success_msg="Compressed!")

    styled_btn(frame, "🗜 Compress", do_compress, accent=True).pack(anchor="w", pady=6)
    status_label(frame, status).pack(anchor="w")


def build_convert_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Convert Format").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Output format is determined by the extension you choose when saving.",
             bg=BG, fg=FG2, font=FONT_SM, wraplength=500, justify="left").pack(anchor="w")

    def do_convert(ext, label):
        path = ask_open()
        if not path: return
        out = ask_save(f"Save as {label}", f".{ext}", [(label, f"*.{ext}")])
        if not out: return
        run_task(convert_image, path, out, status_var=status, success_msg=f"Converted to {label}!")

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w", pady=10)
    styled_btn(btn_row, "→ JPG",  lambda: do_convert("jpg",  "JPEG"), accent=True).pack(side="left", padx=4)
    styled_btn(btn_row, "→ PNG",  lambda: do_convert("png",  "PNG")).pack(side="left", padx=4)
    styled_btn(btn_row, "→ WEBP", lambda: do_convert("webp", "WEBP")).pack(side="left", padx=4)
    status_label(frame, status).pack(anchor="w")


def build_brightness_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Brightness & Contrast").pack(anchor="w", pady=(10,4))
    r1, b_var = scale_row(frame, "Brightness", 0.1, 3.0, 1.0)
    r2, c_var = scale_row(frame, "Contrast",   0.1, 3.0, 1.0)
    r1.pack(anchor="w", pady=4)
    r2.pack(anchor="w", pady=4)

    def do_adjust():
        path = ask_open()
        if not path: return
        out = ask_save("Save Adjusted Image")
        if not out: return
        run_task(adjust_brightness_contrast, path, out, b_var.get(), c_var.get(),
                 status_var=status, success_msg="Adjusted!")

    styled_btn(frame, "🌟 Apply", do_adjust, accent=True).pack(anchor="w", pady=6)
    status_label(frame, status).pack(anchor="w")


def build_watermark_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Add Watermark").pack(anchor="w", pady=(10,4))
    r1, txt_var  = entry_row(frame, "Text", "© MyBrand", width=20)
    r2, size_var = entry_row(frame, "Font size", "40", width=6)
    r1.pack(anchor="w", pady=2)
    r2.pack(anchor="w", pady=2)

    opacity_var = tk.IntVar(value=128)
    sr, _ = scale_row(frame, "Opacity", 10, 255, 128, resolution=1)
    # reuse scale with intvar
    for widget in sr.winfo_children():
        if isinstance(widget, tk.Scale):
            widget.config(variable=opacity_var)
    sr.pack(anchor="w", pady=4)

    color_var = tk.StringVar(value="#ffffff")
    cf = tk.Frame(frame, bg=BG)
    cf.pack(anchor="w", pady=2)
    tk.Label(cf, text="Color", bg=BG, fg=FG, font=FONT, width=14, anchor="w").pack(side="left")
    color_preview = tk.Label(cf, bg=color_var.get(), width=4, relief="flat")
    color_preview.pack(side="left", padx=4)

    def pick_color():
        c = colorchooser.askcolor(color=color_var.get())[1]
        if c:
            color_var.set(c)
            color_preview.config(bg=c)
    styled_btn(cf, "Pick Color", pick_color).pack(side="left", padx=4)

    def do_watermark():
        path = ask_open()
        if not path: return
        out = ask_save("Save Watermarked Image")
        if not out: return
        try:
            fs = int(size_var.get())
        except ValueError:
            fs = 40
        run_task(add_watermark, path, out, txt_var.get(), opacity_var.get(), fs, color_var.get(),
                 status_var=status, success_msg="Watermark added!")

    styled_btn(frame, "💧 Add Watermark", do_watermark, accent=True).pack(anchor="w", pady=6)
    status_label(frame, status).pack(anchor="w")


def build_bg_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Background Removal & Color Change").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Uses AI (rembg) to detect and remove background.",
             bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")

    color_var = tk.StringVar(value="#ffffff")
    cf = tk.Frame(frame, bg=BG)
    cf.pack(anchor="w", pady=6)
    tk.Label(cf, text="New BG color:", bg=BG, fg=FG, font=FONT).pack(side="left")
    color_preview = tk.Label(cf, bg=color_var.get(), width=4, relief="flat")
    color_preview.pack(side="left", padx=6)

    def pick_color():
        c = colorchooser.askcolor(color=color_var.get())[1]
        if c:
            color_var.set(c)
            color_preview.config(bg=c)
    styled_btn(cf, "Pick Color", pick_color).pack(side="left")

    def do_remove():
        path = ask_open()
        if not path: return
        out = ask_save("Save (PNG with transparency)", ".png", [("PNG", "*.png")])
        if not out: return
        run_task(remove_background, path, out, status_var=status, success_msg="Background removed!")

    def do_change():
        path = ask_open()
        if not path: return
        out = ask_save("Save with New Background")
        if not out: return
        from PIL import ImageColor
        try:
            rgb = ImageColor.getrgb(color_var.get())
        except Exception:
            rgb = (255, 255, 255)
        run_task(change_background_color, path, out, rgb, status_var=status, success_msg="Background changed!")

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w", pady=4)
    styled_btn(btn_row, "🪄 Remove BG",    do_remove, accent=True).pack(side="left", padx=(0,8))
    styled_btn(btn_row, "🎨 Change BG Color", do_change).pack(side="left")
    status_label(frame, status).pack(anchor="w", pady=(8,0))


def build_ocr_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Image to Text (OCR)").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Extracts text from image using EasyOCR. First run downloads models (~100MB).",
             bg=BG, fg=FG2, font=FONT_SM, wraplength=500, justify="left").pack(anchor="w")

    result_box = tk.Text(frame, bg=PANEL, fg=FG, font=FONT, height=10, relief="flat",
                         insertbackground=FG, wrap="word")
    result_box.pack(fill="both", expand=True, pady=8)

    def do_ocr():
        path = ask_open()
        if not path: return
        status.set("⏳ Running OCR… (may take a moment)")
        result_box.delete("1.0", tk.END)
        def _run():
            try:
                text = image_to_text(path)
                result_box.insert("1.0", text)
                status.set("✅ Done!")
            except Exception as e:
                status.set(f"❌ {e}")
                messagebox.showerror("Error", str(e))
        threading.Thread(target=_run, daemon=True).start()

    def copy_text():
        frame.clipboard_clear()
        frame.clipboard_append(result_box.get("1.0", tk.END))
        status.set("📋 Copied to clipboard!")

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w")
    styled_btn(btn_row, "🔍 Run OCR",   do_ocr, accent=True).pack(side="left", padx=(0,8))
    styled_btn(btn_row, "📋 Copy Text", copy_text).pack(side="left")
    status_label(frame, status).pack(anchor="w", pady=(6,0))


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class ImageSuiteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Processing Suite")
        self.geometry("660x520")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=ACCENT, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="  🖼 Image Processing Suite", font=("Segoe UI", 14, "bold"),
                 bg=ACCENT, fg=FG).pack(side="left", padx=10)

        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=FG2,
                        font=FONT, padding=[10, 5], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", FG)])
        style.configure("TFrame", background=BG)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        tabs = [
            ("Resize",       build_resize_tab),
            ("Crop",         build_crop_tab),
            ("Compress",     build_compress_tab),
            ("Convert",      build_convert_tab),
            ("Brightness",   build_brightness_tab),
            ("Watermark",    build_watermark_tab),
            ("Background",   build_bg_tab),
            ("OCR",          build_ocr_tab),
        ]
        for name, builder in tabs:
            f = ttk.Frame(nb)
            nb.add(f, text=f"  {name}  ")
            inner = tk.Frame(f, bg=BG)
            inner.pack(fill="both", expand=True, padx=16, pady=8)
            builder(inner)


if __name__ == "__main__":
    app = ImageSuiteApp()
    app.mainloop()
