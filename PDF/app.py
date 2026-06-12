"""PDF Utility Suite — Tkinter GUI"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from operations.pdf_ops import merge_pdfs, split_pdf, compress_pdf, protect_pdf, remove_password
from operations.convert import (
    pdf_to_word, pdf_to_excel, pdf_to_ppt, pdf_to_images,
    word_to_pdf, excel_to_pdf, ppt_to_pdf, images_to_pdf,
)

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
BG = "#1e1e2e"
PANEL = "#2a2a3e"
ACCENT = "#7c3aed"
ACCENT2 = "#a78bfa"
FG = "#e2e8f0"
FG2 = "#94a3b8"
SUCCESS = "#22c55e"
ERROR = "#ef4444"
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_H = ("Segoe UI", 13, "bold")
FONT_SM = ("Segoe UI", 9)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask_save(title="Save As", ext=".pdf", filetypes=None):
    if filetypes is None:
        filetypes = [("PDF files", "*.pdf")]
    return filedialog.asksaveasfilename(title=title, defaultextension=ext, filetypes=filetypes)


def ask_open(title="Open File", multi=False, filetypes=None):
    if filetypes is None:
        filetypes = [("PDF files", "*.pdf")]
    if multi:
        return filedialog.askopenfilenames(title=title, filetypes=filetypes)
    return filedialog.askopenfilename(title=title, filetypes=filetypes)


def ask_dir(title="Select Folder"):
    return filedialog.askdirectory(title=title)


def run_task(fn, *args, status_var=None, success_msg="Done!", on_done=None):
    """Run fn(*args) in a background thread, update status_var."""
    def _worker():
        try:
            if status_var:
                status_var.set("⏳ Working…")
            result = fn(*args)
            if status_var:
                status_var.set(f"✅ {success_msg}")
            if on_done:
                on_done(result)
        except Exception as e:
            if status_var:
                status_var.set(f"❌ Error: {e}")
            messagebox.showerror("Error", str(e))
    threading.Thread(target=_worker, daemon=True).start()


# ---------------------------------------------------------------------------
# Styled Widgets
# ---------------------------------------------------------------------------

def styled_btn(parent, text, command, accent=False):
    bg = ACCENT if accent else PANEL
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=FG, activebackground=ACCENT2, activeforeground=FG,
        font=FONT, relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
    )
    return btn


def section_label(parent, text):
    return tk.Label(parent, text=text, font=FONT_H, bg=BG, fg=ACCENT2)


def status_label(parent, var):
    return tk.Label(parent, textvariable=var, font=FONT_SM, bg=BG, fg=FG2, wraplength=520, justify="left")


# ---------------------------------------------------------------------------
# Tab Builders
# ---------------------------------------------------------------------------

def build_merge_tab(frame):
    files = []
    status = tk.StringVar(value="No files selected.")

    def add_files():
        paths = ask_open("Select PDFs to Merge", multi=True)
        if paths:
            files.extend(paths)
            listbox.delete(0, tk.END)
            for p in files:
                listbox.insert(tk.END, os.path.basename(p))
            status.set(f"{len(files)} file(s) loaded.")

    def clear_files():
        files.clear()
        listbox.delete(0, tk.END)
        status.set("Cleared.")

    def do_merge():
        if len(files) < 2:
            messagebox.showwarning("Merge", "Add at least 2 PDFs.")
            return
        out = ask_save("Save Merged PDF")
        if out:
            run_task(merge_pdfs, files, out, status_var=status, success_msg=f"Saved: {os.path.basename(out)}")

    section_label(frame, "Merge PDFs").pack(anchor="w", pady=(10, 4))
    tk.Label(frame, text="Add PDFs in the order you want them merged.", bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")

    listbox = tk.Listbox(frame, bg=PANEL, fg=FG, font=FONT, selectbackground=ACCENT,
                         relief="flat", height=7, bd=0, highlightthickness=1, highlightbackground=ACCENT)
    listbox.pack(fill="x", pady=8)

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w")
    styled_btn(btn_row, "➕ Add PDFs", add_files, accent=True).pack(side="left", padx=(0, 6))
    styled_btn(btn_row, "🗑 Clear", clear_files).pack(side="left")
    styled_btn(btn_row, "🔗 Merge", do_merge, accent=True).pack(side="left", padx=(6, 0))

    status_label(frame, status).pack(anchor="w", pady=(8, 0))


def build_split_tab(frame):
    status = tk.StringVar(value="")
    pages_var = tk.StringVar(value="1")

    def do_split():
        path = ask_open("Select PDF to Split")
        if not path:
            return
        out_dir = ask_dir("Select Output Folder")
        if not out_dir:
            return
        try:
            n = int(pages_var.get())
        except ValueError:
            messagebox.showerror("Error", "Pages per split must be a number.")
            return
        run_task(split_pdf, path, out_dir, n, status_var=status, success_msg="Split complete.")

    section_label(frame, "Split PDF").pack(anchor="w", pady=(10, 4))
    row = tk.Frame(frame, bg=BG)
    row.pack(anchor="w", pady=4)
    tk.Label(row, text="Pages per file:", bg=BG, fg=FG, font=FONT).pack(side="left")
    tk.Entry(row, textvariable=pages_var, width=5, bg=PANEL, fg=FG, font=FONT,
             insertbackground=FG, relief="flat").pack(side="left", padx=6)
    styled_btn(frame, "✂ Split PDF", do_split, accent=True).pack(anchor="w", pady=8)
    status_label(frame, status).pack(anchor="w")


def build_compress_tab(frame):
    status = tk.StringVar(value="")

    def do_compress():
        path = ask_open("Select PDF to Compress")
        if not path:
            return
        out = ask_save("Save Compressed PDF")
        if out:
            run_task(compress_pdf, path, out, status_var=status, success_msg="Compressed!")

    section_label(frame, "Compress PDF").pack(anchor="w", pady=(10, 4))
    tk.Label(frame, text="Reduces file size by optimizing images (JPEG 60%).", bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")
    styled_btn(frame, "🗜 Compress PDF", do_compress, accent=True).pack(anchor="w", pady=10)
    status_label(frame, status).pack(anchor="w")


def build_password_tab(frame):
    status = tk.StringVar(value="")

    def do_protect():
        path = ask_open("Select PDF to Protect")
        if not path:
            return
        pwd = simpledialog.askstring("Password", "Enter user password:", show="*")
        if not pwd:
            return
        out = ask_save("Save Protected PDF")
        if out:
            run_task(protect_pdf, path, out, pwd, status_var=status, success_msg="Password applied!")

    def do_remove():
        path = ask_open("Select Protected PDF")
        if not path:
            return
        pwd = simpledialog.askstring("Password", "Enter current password:", show="*")
        if pwd is None:
            return
        out = ask_save("Save Unlocked PDF")
        if out:
            run_task(remove_password, path, out, pwd, status_var=status, success_msg="Password removed!")

    section_label(frame, "Password Protection").pack(anchor="w", pady=(10, 4))
    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w")
    styled_btn(btn_row, "🔒 Protect PDF", do_protect, accent=True).pack(side="left", padx=(0, 8))
    styled_btn(btn_row, "🔓 Remove Password", do_remove).pack(side="left")
    status_label(frame, status).pack(anchor="w", pady=(10, 0))


def build_pdf_to_x_tab(frame):
    status = tk.StringVar(value="")

    def convert(fn, out_title, ext, filetypes, success):
        path = ask_open()
        if not path:
            return
        out = ask_save(out_title, ext, filetypes)
        if out:
            run_task(fn, path, out, status_var=status, success_msg=success)

    def to_images():
        path = ask_open()
        if not path:
            return
        out_dir = ask_dir("Select Output Folder for Images")
        if out_dir:
            run_task(pdf_to_images, path, out_dir, status_var=status, success_msg="Images saved!")

    section_label(frame, "PDF → Other Formats").pack(anchor="w", pady=(10, 4))
    grid = tk.Frame(frame, bg=BG)
    grid.pack(anchor="w")

    btns = [
        ("📄 → Word",  lambda: convert(pdf_to_word,  "Save DOCX", ".docx", [("Word", "*.docx")], "Word file saved!")),
        ("📊 → Excel", lambda: convert(pdf_to_excel, "Save XLSX", ".xlsx", [("Excel", "*.xlsx")], "Excel file saved!")),
        ("📽 → PPT",   lambda: convert(pdf_to_ppt,   "Save PPTX", ".pptx", [("PowerPoint", "*.pptx")], "PPT saved!")),
        ("🖼 → Images", to_images),
    ]
    for i, (label, cmd) in enumerate(btns):
        styled_btn(grid, label, cmd, accent=(i % 2 == 0)).grid(row=0, column=i, padx=4, pady=4)

    status_label(frame, status).pack(anchor="w", pady=(10, 0))


def build_x_to_pdf_tab(frame):
    status = tk.StringVar(value="")

    def convert(fn, title, filetypes, success):
        path = ask_open(title, filetypes=filetypes)
        if not path:
            return
        out = ask_save("Save as PDF")
        if out:
            run_task(fn, path, out, status_var=status, success_msg=success)

    def from_images():
        paths = ask_open("Select Images", multi=True,
                         filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp")])
        if not paths:
            return
        out = ask_save("Save as PDF")
        if out:
            run_task(images_to_pdf, list(paths), out, status_var=status, success_msg="PDF created!")

    section_label(frame, "Other Formats → PDF").pack(anchor="w", pady=(10, 4))
    grid = tk.Frame(frame, bg=BG)
    grid.pack(anchor="w")

    btns = [
        ("📄 Word → PDF",  lambda: convert(word_to_pdf, "Select DOCX", [("Word", "*.docx *.doc")], "PDF saved!")),
        ("📊 Excel → PDF", lambda: convert(excel_to_pdf, "Select XLSX", [("Excel", "*.xlsx *.xls")], "PDF saved!")),
        ("📽 PPT → PDF",   lambda: convert(ppt_to_pdf, "Select PPTX", [("PowerPoint", "*.pptx *.ppt")], "PDF saved!")),
        ("🖼 Images → PDF", from_images),
    ]
    for i, (label, cmd) in enumerate(btns):
        styled_btn(grid, label, cmd, accent=(i % 2 == 0)).grid(row=0, column=i, padx=4, pady=4)

    status_label(frame, status).pack(anchor="w", pady=(10, 0))


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class PDFSuiteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Utility Suite")
        self.geometry("620x480")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=ACCENT, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="  📄 PDF Utility Suite", font=("Segoe UI", 14, "bold"),
                 bg=ACCENT, fg=FG).pack(side="left", padx=10)

        # Notebook
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=FG2,
                        font=FONT, padding=[12, 6], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", FG)])
        style.configure("TFrame", background=BG)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        tabs = [
            ("Merge",        build_merge_tab),
            ("Split",        build_split_tab),
            ("Compress",     build_compress_tab),
            ("Password",     build_password_tab),
            ("PDF → X",      build_pdf_to_x_tab),
            ("X → PDF",      build_x_to_pdf_tab),
        ]
        for name, builder in tabs:
            f = ttk.Frame(nb)
            nb.add(f, text=f"  {name}  ")
            inner = tk.Frame(f, bg=BG)
            inner.pack(fill="both", expand=True, padx=16, pady=8)
            builder(inner)


if __name__ == "__main__":
    app = PDFSuiteApp()
    app.mainloop()
