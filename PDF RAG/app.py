"""AI PDF Assistant (RAG) — Tkinter GUI"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from rag.loader import load_and_chunk
from rag.embeddings import build_vectorstore, get_retriever
from rag.chain import (
    answer_question, summarize, extract_key_points,
    detect_topics, generate_quiz, generate_flashcards,
)

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
BG      = "#1e1e2e"
PANEL   = "#2a2a3e"
ACCENT  = "#10b981"
ACCENT2 = "#34d399"
FG      = "#e2e8f0"
FG2     = "#94a3b8"
WARN    = "#f59e0b"
FONT      = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_H    = ("Segoe UI", 13, "bold")
FONT_SM   = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)

# ---------------------------------------------------------------------------
# App State
# ---------------------------------------------------------------------------
class AppState:
    pdf_path: str = ""
    vectorstore = None
    retriever = None
    full_text: str = ""
    loaded: bool = False

state = AppState()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def styled_btn(parent, text, command, accent=False, width=None):
    kw = {"width": width} if width else {}
    return tk.Button(parent, text=text, command=command,
                     bg=ACCENT if accent else PANEL, fg=FG,
                     activebackground=ACCENT2, activeforeground=FG,
                     font=FONT, relief="flat", bd=0, padx=12, pady=6,
                     cursor="hand2", **kw)

def section_label(parent, text):
    return tk.Label(parent, text=text, font=FONT_H, bg=BG, fg=ACCENT2)

def output_box(parent, height=14):
    f = tk.Frame(parent, bg=PANEL, bd=0)
    sb = tk.Scrollbar(f)
    sb.pack(side="right", fill="y")
    box = tk.Text(f, bg=PANEL, fg=FG, font=FONT_MONO, height=height,
                  relief="flat", insertbackground=FG, wrap="word",
                  yscrollcommand=sb.set, state="disabled")
    box.pack(side="left", fill="both", expand=True)
    sb.config(command=box.yview)
    return f, box

def set_output(box: tk.Text, text: str):
    box.config(state="normal")
    box.delete("1.0", tk.END)
    box.insert("1.0", text)
    box.config(state="disabled")

def run_bg(fn, *args, on_done=None, on_error=None):
    def _worker():
        try:
            result = fn(*args)
            if on_done: on_done(result)
        except Exception as e:
            if on_error: on_error(str(e))
            else: messagebox.showerror("Error", str(e))
    threading.Thread(target=_worker, daemon=True).start()

# ---------------------------------------------------------------------------
# PDF Loader Panel (top bar)
# ---------------------------------------------------------------------------

def build_loader(root, status_var: tk.StringVar, on_loaded):
    bar = tk.Frame(root, bg=PANEL, pady=8, padx=12)
    bar.pack(fill="x", padx=10, pady=(0, 6))

    path_var = tk.StringVar(value="No PDF loaded")
    tk.Label(bar, textvariable=path_var, bg=PANEL, fg=FG2, font=FONT_SM,
             anchor="w").pack(side="left", fill="x", expand=True)

    def load_pdf():
        path = filedialog.askopenfilename(
            title="Select PDF", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        state.pdf_path = path
        path_var.set(f"📄 {os.path.basename(path)}")
        status_var.set("⏳ Processing PDF…")

        def _process():
            chunks = load_and_chunk(path)
            state.full_text = " ".join([c.page_content for c in chunks])
            state.vectorstore = build_vectorstore(chunks)
            state.retriever = get_retriever(state.vectorstore)
            state.loaded = True

        def _done(_):
            status_var.set(f"✅ Ready — {os.path.basename(path)}")
            on_loaded()

        def _err(e):
            status_var.set(f"❌ Error: {e}")
            messagebox.showerror("Error", e)

        run_bg(_process, on_done=_done, on_error=_err)

    styled_btn(bar, "📂 Load PDF", load_pdf, accent=True).pack(side="right")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

def check_loaded():
    if not state.loaded:
        messagebox.showwarning("No PDF", "Please load a PDF first.")
        return False
    return True


def build_chat_tab(frame, status_var):
    section_label(frame, "Chat with PDF").pack(anchor="w", pady=(8, 4))

    history_frame, history_box = output_box(frame, height=12)
    history_frame.pack(fill="both", expand=True, pady=4)

    entry_frame = tk.Frame(frame, bg=BG)
    entry_frame.pack(fill="x", pady=4)
    question_var = tk.StringVar()
    entry = tk.Entry(entry_frame, textvariable=question_var, bg=PANEL, fg=FG,
                     font=FONT, insertbackground=FG, relief="flat")
    entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 6))

    def ask(event=None):
        if not check_loaded(): return
        q = question_var.get().strip()
        if not q: return
        question_var.set("")
        status_var.set("⏳ Thinking…")
        history_box.config(state="normal")
        history_box.insert(tk.END, f"\n🧑 {q}\n")
        history_box.config(state="disabled")

        def _done(ans):
            history_box.config(state="normal")
            history_box.insert(tk.END, f"🤖 {ans}\n")
            history_box.see(tk.END)
            history_box.config(state="disabled")
            status_var.set("✅ Ready")

        run_bg(answer_question, state.retriever, q, on_done=_done,
               on_error=lambda e: status_var.set(f"❌ {e}"))

    entry.bind("<Return>", ask)
    styled_btn(entry_frame, "Send ↵", ask, accent=True).pack(side="right")


def _simple_tab(frame, status_var, title, hint, btn_label, fn, extra_arg=None):
    """Generic tab for single-click features."""
    section_label(frame, title).pack(anchor="w", pady=(8, 4))
    if hint:
        tk.Label(frame, text=hint, bg=BG, fg=FG2, font=FONT_SM,
                 wraplength=580).pack(anchor="w")
    out_frame, out_box = output_box(frame)
    out_frame.pack(fill="both", expand=True, pady=8)

    def run():
        if not check_loaded(): return
        status_var.set("⏳ Working…")
        set_output(out_box, "Please wait…")
        args = [state.retriever, state.full_text]
        if extra_arg is not None:
            args.append(extra_arg)

        def _done(result):
            set_output(out_box, result)
            status_var.set("✅ Done")

        run_bg(fn, *args, on_done=_done,
               on_error=lambda e: (status_var.set(f"❌ {e}"), set_output(out_box, f"Error: {e}")))

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w")
    styled_btn(btn_row, btn_label, run, accent=True).pack(side="left", padx=(0, 8))

    def copy():
        frame.clipboard_clear()
        frame.clipboard_append(out_box.get("1.0", tk.END))
        status_var.set("📋 Copied!")
    styled_btn(btn_row, "📋 Copy", copy).pack(side="left")


def build_quiz_tab(frame, status_var):
    section_label(frame, "Quiz Generation").pack(anchor="w", pady=(8, 4))
    nf = tk.Frame(frame, bg=BG)
    nf.pack(anchor="w", pady=4)
    tk.Label(nf, text="Number of questions:", bg=BG, fg=FG, font=FONT).pack(side="left")
    n_var = tk.IntVar(value=5)
    tk.Spinbox(nf, from_=3, to=15, textvariable=n_var, width=4,
               bg=PANEL, fg=FG, font=FONT, relief="flat",
               buttonbackground=PANEL).pack(side="left", padx=6)

    out_frame, out_box = output_box(frame)
    out_frame.pack(fill="both", expand=True, pady=8)

    def run():
        if not check_loaded(): return
        status_var.set("⏳ Generating quiz…")
        set_output(out_box, "Please wait…")
        def _done(r):
            set_output(out_box, r)
            status_var.set("✅ Done")
        run_bg(generate_quiz, state.retriever, state.full_text, n_var.get(),
               on_done=_done, on_error=lambda e: (status_var.set(f"❌ {e}"), set_output(out_box, f"Error: {e}")))

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w")
    styled_btn(btn_row, "📝 Generate Quiz", run, accent=True).pack(side="left", padx=(0,8))
    def copy():
        frame.clipboard_clear()
        frame.clipboard_append(out_box.get("1.0", tk.END))
        status_var.set("📋 Copied!")
    styled_btn(btn_row, "📋 Copy", copy).pack(side="left")


def build_flashcard_tab(frame, status_var):
    section_label(frame, "Flashcard Generation").pack(anchor="w", pady=(8, 4))
    nf = tk.Frame(frame, bg=BG)
    nf.pack(anchor="w", pady=4)
    tk.Label(nf, text="Number of cards:", bg=BG, fg=FG, font=FONT).pack(side="left")
    n_var = tk.IntVar(value=8)
    tk.Spinbox(nf, from_=3, to=20, textvariable=n_var, width=4,
               bg=PANEL, fg=FG, font=FONT, relief="flat",
               buttonbackground=PANEL).pack(side="left", padx=6)

    out_frame, out_box = output_box(frame)
    out_frame.pack(fill="both", expand=True, pady=8)

    def run():
        if not check_loaded(): return
        status_var.set("⏳ Generating flashcards…")
        set_output(out_box, "Please wait…")
        def _done(r):
            set_output(out_box, r)
            status_var.set("✅ Done")
        run_bg(generate_flashcards, state.retriever, state.full_text, n_var.get(),
               on_done=_done, on_error=lambda e: (status_var.set(f"❌ {e}"), set_output(out_box, f"Error: {e}")))

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w")
    styled_btn(btn_row, "🃏 Generate Flashcards", run, accent=True).pack(side="left", padx=(0,8))
    def copy():
        frame.clipboard_clear()
        frame.clipboard_append(out_box.get("1.0", tk.END))
        status_var.set("📋 Copied!")
    styled_btn(btn_row, "📋 Copy", copy).pack(side="left")


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class RAGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI PDF Assistant")
        self.geometry("760x620")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.status_var = tk.StringVar(value="Load a PDF to get started.")
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=ACCENT, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="  🤖 AI PDF Assistant (RAG)", font=("Segoe UI", 14, "bold"),
                 bg=ACCENT, fg="#fff").pack(side="left", padx=10)

        # Status bar
        tk.Label(self, textvariable=self.status_var, bg=BG, fg=WARN,
                 font=FONT_SM, anchor="w").pack(fill="x", padx=12, pady=(6, 0))

        # PDF loader
        build_loader(self, self.status_var, on_loaded=lambda: None)

        # Notebook
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=FG2,
                        font=FONT, padding=[12, 6], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "#fff")])
        style.configure("TFrame", background=BG)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=6)

        tabs = [
            ("💬 Chat",       lambda f: build_chat_tab(f, self.status_var)),
            ("📋 Summary",    lambda f: _simple_tab(f, self.status_var, "PDF Summarization",
                                                    "Generates a concise summary of the entire document.",
                                                    "✨ Summarize", summarize)),
            ("🔑 Key Points", lambda f: _simple_tab(f, self.status_var, "Key Points Extraction",
                                                    "Extracts the most important facts and conclusions.",
                                                    "🔑 Extract Key Points", extract_key_points)),
            ("🏷 Topics",     lambda f: _simple_tab(f, self.status_var, "Important Topics",
                                                    "Identifies main themes and topics in the document.",
                                                    "🏷 Detect Topics", detect_topics)),
            ("📝 Quiz",       lambda f: build_quiz_tab(f, self.status_var)),
            ("🃏 Flashcards", lambda f: build_flashcard_tab(f, self.status_var)),
        ]

        for name, builder in tabs:
            f = ttk.Frame(nb)
            nb.add(f, text=f"  {name}  ")
            inner = tk.Frame(f, bg=BG)
            inner.pack(fill="both", expand=True, padx=16, pady=8)
            builder(inner)


if __name__ == "__main__":
    app = RAGApp()
    app.mainloop()
