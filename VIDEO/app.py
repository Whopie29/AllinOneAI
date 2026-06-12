"""Video & Audio Toolkit — Tkinter GUI"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from operations.transcript import transcribe_to_txt, transcribe_to_srt, transcribe_with_speakers
from operations.video_ops import mute_video, extract_audio, convert_video, compress_video
from operations.audio_ops import audio_to_text, reduce_noise, convert_audio

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
BG      = "#1e1e2e"
PANEL   = "#2a2a3e"
ACCENT  = "#f97316"
ACCENT2 = "#fb923c"
FG      = "#e2e8f0"
FG2     = "#94a3b8"
FONT      = ("Segoe UI", 10)
FONT_H    = ("Segoe UI", 13, "bold")
FONT_SM   = ("Segoe UI", 9)

VIDEO_TYPES = [("Video files", "*.mp4 *.mkv *.avi *.mov *.webm *.flv")]
AUDIO_TYPES = [("Audio files", "*.mp3 *.wav *.aac *.flac *.ogg *.m4a")]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask_open(title="Open", filetypes=None):
    ft = filetypes or VIDEO_TYPES
    return filedialog.askopenfilename(title=title, filetypes=ft)

def ask_save(title="Save As", ext=".mp4", filetypes=None):
    ft = filetypes or [("MP4", "*.mp4")]
    return filedialog.asksaveasfilename(title=title, defaultextension=ext, filetypes=ft)

def run_task(fn, *args, status_var=None, success_msg="Done!", on_done=None):
    def _worker():
        try:
            if status_var: status_var.set("⏳ Working… (this may take a while)")
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
    return tk.Label(parent, textvariable=var, font=FONT_SM, bg=BG, fg=FG2,
                    wraplength=560, justify="left")

def model_selector(parent):
    f = tk.Frame(parent, bg=BG)
    tk.Label(f, text="Whisper model:", bg=BG, fg=FG, font=FONT).pack(side="left")
    var = tk.StringVar(value="base")
    cb = ttk.Combobox(f, textvariable=var, values=["tiny", "base", "small", "medium", "large"],
                      width=8, state="readonly")
    cb.pack(side="left", padx=6)
    tk.Label(f, text="(larger = more accurate, slower)",
             bg=BG, fg=FG2, font=FONT_SM).pack(side="left")
    return f, var

# ---------------------------------------------------------------------------
# Transcript Tabs
# ---------------------------------------------------------------------------

def build_txt_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Video → TXT Transcript").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Transcribes speech to a plain text file using Whisper.",
             bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")
    mf, model_var = model_selector(frame)
    mf.pack(anchor="w", pady=6)

    result_box = tk.Text(frame, bg=PANEL, fg=FG, font=FONT, height=8,
                         relief="flat", insertbackground=FG, wrap="word")
    result_box.pack(fill="both", expand=True, pady=4)

    def do_txt():
        path = ask_open("Select Video or Audio", filetypes=VIDEO_TYPES + AUDIO_TYPES)
        if not path: return
        out = ask_save("Save TXT", ".txt", [("Text", "*.txt")])
        if not out: return
        result_box.delete("1.0", tk.END)
        def on_done(p):
            with open(p, encoding="utf-8") as f:
                result_box.insert("1.0", f.read())
        run_task(transcribe_to_txt, path, out, model_var.get(),
                 status_var=status, success_msg="Transcript saved!", on_done=on_done)

    styled_btn(frame, "🎙 Transcribe → TXT", do_txt, accent=True).pack(anchor="w", pady=4)
    status_label(frame, status).pack(anchor="w")


def build_srt_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Video → SRT Subtitles").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Generates timestamped SRT subtitle file.",
             bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")
    mf, model_var = model_selector(frame)
    mf.pack(anchor="w", pady=6)

    result_box = tk.Text(frame, bg=PANEL, fg=FG, font=FONT, height=8,
                         relief="flat", insertbackground=FG, wrap="word")
    result_box.pack(fill="both", expand=True, pady=4)

    def do_srt():
        path = ask_open("Select Video or Audio", filetypes=VIDEO_TYPES + AUDIO_TYPES)
        if not path: return
        out = ask_save("Save SRT", ".srt", [("SRT", "*.srt")])
        if not out: return
        result_box.delete("1.0", tk.END)
        def on_done(p):
            with open(p, encoding="utf-8") as f:
                result_box.insert("1.0", f.read())
        run_task(transcribe_to_srt, path, out, model_var.get(),
                 status_var=status, success_msg="SRT saved!", on_done=on_done)

    styled_btn(frame, "📝 Generate SRT", do_srt, accent=True).pack(anchor="w", pady=4)
    status_label(frame, status).pack(anchor="w")


def build_speaker_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Speaker Identification").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Detects speaker turns based on pause gaps and labels them.",
             bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")
    mf, model_var = model_selector(frame)
    mf.pack(anchor="w", pady=6)

    result_box = tk.Text(frame, bg=PANEL, fg=FG, font=FONT, height=8,
                         relief="flat", insertbackground=FG, wrap="word")
    result_box.pack(fill="both", expand=True, pady=4)

    def do_speaker():
        path = ask_open("Select Video or Audio", filetypes=VIDEO_TYPES + AUDIO_TYPES)
        if not path: return
        out = ask_save("Save Speaker Transcript", ".txt", [("Text", "*.txt")])
        if not out: return
        result_box.delete("1.0", tk.END)
        def on_done(p):
            with open(p, encoding="utf-8") as f:
                result_box.insert("1.0", f.read())
        run_task(transcribe_with_speakers, path, out, model_var.get(),
                 status_var=status, success_msg="Speaker transcript saved!", on_done=on_done)

    styled_btn(frame, "🗣 Identify Speakers", do_speaker, accent=True).pack(anchor="w", pady=4)
    status_label(frame, status).pack(anchor="w")


# ---------------------------------------------------------------------------
# Video Tabs
# ---------------------------------------------------------------------------

def build_mute_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Mute Video").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Removes the audio track from a video file.",
             bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")

    def do_mute():
        path = ask_open()
        if not path: return
        out = ask_save("Save Muted Video")
        if not out: return
        run_task(mute_video, path, out, status_var=status, success_msg="Video muted!")

    styled_btn(frame, "🔇 Mute Video", do_mute, accent=True).pack(anchor="w", pady=10)
    status_label(frame, status).pack(anchor="w")


def build_extract_audio_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Extract Audio").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Extracts audio from video and saves as MP3.",
             bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")

    def do_extract():
        path = ask_open()
        if not path: return
        out = ask_save("Save Audio", ".mp3", [("MP3", "*.mp3"), ("WAV", "*.wav")])
        if not out: return
        run_task(extract_audio, path, out, status_var=status, success_msg="Audio extracted!")

    styled_btn(frame, "🎵 Extract Audio", do_extract, accent=True).pack(anchor="w", pady=10)
    status_label(frame, status).pack(anchor="w")


def build_convert_video_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Convert Video Format").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Output format is determined by the extension you choose when saving.",
             bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")

    def do_convert(ext, label):
        path = ask_open()
        if not path: return
        out = ask_save(f"Save as {label}", f".{ext}", [(label, f"*.{ext}")])
        if not out: return
        run_task(convert_video, path, out, status_var=status, success_msg=f"Converted to {label}!")

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w", pady=10)
    for i, (ext, lbl) in enumerate([("mp4","MP4"), ("mkv","MKV"), ("avi","AVI"), ("webm","WEBM"), ("mov","MOV")]):
        styled_btn(btn_row, f"→ {lbl}", lambda e=ext, l=lbl: do_convert(e, l),
                   accent=(i == 0)).pack(side="left", padx=3)
    status_label(frame, status).pack(anchor="w")


def build_compress_video_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Compress Video").pack(anchor="w", pady=(10,4))

    crf_var = tk.IntVar(value=28)
    sf = tk.Frame(frame, bg=BG)
    sf.pack(anchor="w", pady=4)
    tk.Label(sf, text="Quality (CRF):", bg=BG, fg=FG, font=FONT).pack(side="left")
    tk.Scale(sf, variable=crf_var, from_=18, to=40, resolution=1, orient="horizontal",
             bg=BG, fg=FG, troughcolor=PANEL, highlightthickness=0, length=180).pack(side="left")
    tk.Label(sf, text="18=best  40=smallest", bg=BG, fg=FG2, font=FONT_SM).pack(side="left", padx=6)

    def do_compress():
        path = ask_open()
        if not path: return
        out = ask_save("Save Compressed Video")
        if not out: return
        run_task(compress_video, path, out, crf_var.get(),
                 status_var=status, success_msg="Video compressed!")

    styled_btn(frame, "🗜 Compress Video", do_compress, accent=True).pack(anchor="w", pady=6)
    status_label(frame, status).pack(anchor="w")


# ---------------------------------------------------------------------------
# Audio Tabs
# ---------------------------------------------------------------------------

def build_audio_to_text_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Audio to Text").pack(anchor="w", pady=(10,4))
    mf, model_var = model_selector(frame)
    mf.pack(anchor="w", pady=4)

    result_box = tk.Text(frame, bg=PANEL, fg=FG, font=FONT, height=8,
                         relief="flat", insertbackground=FG, wrap="word")
    result_box.pack(fill="both", expand=True, pady=4)

    def do_a2t():
        path = ask_open("Select Audio", filetypes=AUDIO_TYPES)
        if not path: return
        out = ask_save("Save Transcript", ".txt", [("Text", "*.txt")])
        if not out: return
        result_box.delete("1.0", tk.END)
        def on_done(p):
            with open(p, encoding="utf-8") as f:
                result_box.insert("1.0", f.read())
        run_task(audio_to_text, path, out, model_var.get(),
                 status_var=status, success_msg="Done!", on_done=on_done)

    styled_btn(frame, "🎤 Transcribe Audio", do_a2t, accent=True).pack(anchor="w", pady=4)
    status_label(frame, status).pack(anchor="w")


def build_noise_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Noise Reduction").pack(anchor="w", pady=(10,4))
    tk.Label(frame, text="Reduces background noise from audio using spectral gating.",
             bg=BG, fg=FG2, font=FONT_SM).pack(anchor="w")

    def do_noise():
        path = ask_open("Select Audio", filetypes=AUDIO_TYPES + [("WAV", "*.wav")])
        if not path: return
        out = ask_save("Save Cleaned Audio", ".wav", [("WAV", "*.wav")])
        if not out: return
        run_task(reduce_noise, path, out, status_var=status, success_msg="Noise reduced!")

    styled_btn(frame, "🔉 Reduce Noise", do_noise, accent=True).pack(anchor="w", pady=10)
    status_label(frame, status).pack(anchor="w")


def build_convert_audio_tab(frame):
    status = tk.StringVar()
    section_label(frame, "Audio Format Conversion").pack(anchor="w", pady=(10,4))

    def do_convert(ext, label):
        path = ask_open("Select Audio", filetypes=AUDIO_TYPES)
        if not path: return
        out = ask_save(f"Save as {label}", f".{ext}", [(label, f"*.{ext}")])
        if not out: return
        run_task(convert_audio, path, out, status_var=status, success_msg=f"Converted to {label}!")

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w", pady=10)
    for i, (ext, lbl) in enumerate([("mp3","MP3"), ("wav","WAV"), ("aac","AAC"), ("flac","FLAC"), ("ogg","OGG")]):
        styled_btn(btn_row, f"→ {lbl}", lambda e=ext, l=lbl: do_convert(e, l),
                   accent=(i == 0)).pack(side="left", padx=3)
    status_label(frame, status).pack(anchor="w")


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class VideoAudioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video & Audio Toolkit")
        self.geometry("700x540")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=ACCENT, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="  🎬 Video & Audio Toolkit", font=("Segoe UI", 14, "bold"),
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

        # Outer notebook: Transcript / Video / Audio
        outer = ttk.Notebook(self)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        groups = [
            ("📝 Transcript", [
                ("TXT",     build_txt_tab),
                ("SRT",     build_srt_tab),
                ("Speakers",build_speaker_tab),
            ]),
            ("🎬 Video", [
                ("Mute",        build_mute_tab),
                ("Extract Audio", build_extract_audio_tab),
                ("Convert",     build_convert_video_tab),
                ("Compress",    build_compress_video_tab),
            ]),
            ("🎵 Audio", [
                ("Audio→Text",  build_audio_to_text_tab),
                ("Noise Reduce",build_noise_tab),
                ("Convert",     build_convert_audio_tab),
            ]),
        ]

        for group_name, tabs in groups:
            group_frame = ttk.Frame(outer)
            outer.add(group_frame, text=f"  {group_name}  ")
            inner_nb = ttk.Notebook(group_frame)
            inner_nb.pack(fill="both", expand=True)
            for tab_name, builder in tabs:
                f = ttk.Frame(inner_nb)
                inner_nb.add(f, text=f"  {tab_name}  ")
                inner = tk.Frame(f, bg=BG)
                inner.pack(fill="both", expand=True, padx=16, pady=8)
                builder(inner)


if __name__ == "__main__":
    app = VideoAudioApp()
    app.mainloop()
