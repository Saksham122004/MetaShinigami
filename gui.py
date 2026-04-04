import os
import stat
import sys
import math
import json
import csv
import hashlib
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

# ─── Try importing required packages ───────────────────────────────────────────
try:
    import customtkinter as ctk
except ImportError:
    os.system(f"{sys.executable} -m pip install customtkinter -q")
    import customtkinter as ctk

try:
    import magic
except ImportError:
    os.system(f"{sys.executable} -m pip install python-magic-bin -q" if sys.platform == "win32"
              else f"{sys.executable} -m pip install python-magic -q")
    import magic

try:
    from PIL import Image, ExifTags, ImageTk
except ImportError:
    os.system(f"{sys.executable} -m pip install Pillow -q")
    from PIL import Image, ExifTags, ImageTk

try:
    from PyPDF2 import PdfReader
except ImportError:
    os.system(f"{sys.executable} -m pip install PyPDF2 -q")
    from PyPDF2 import PdfReader

try:
    from docx import Document
except ImportError:
    os.system(f"{sys.executable} -m pip install python-docx -q")
    from docx import Document

try:
    from openpyxl import load_workbook
except ImportError:
    os.system(f"{sys.executable} -m pip install openpyxl -q")
    from openpyxl import load_workbook

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_AVAILABLE = True
except ImportError:
    HACHOIR_AVAILABLE = False


# ─── THEME & PALETTE ───────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Cyberpunk / forensics dark theme
C_BG        = "#0A0E1A"
C_PANEL     = "#0F1628"
C_CARD      = "#131B30"
C_BORDER    = "#1E2D50"
C_ACCENT    = "#00D4FF"     # electric cyan
C_ACCENT2   = "#7B2FFF"     # deep violet
C_ACCENT3   = "#00FF9D"     # neon green
C_WARN      = "#FFB800"
C_TEXT      = "#C8D8F0"
C_SUBTEXT   = "#5A7A9A"
C_SUCCESS   = "#00FF9D"
C_ERROR     = "#FF4B6E"


# ─── BACKEND LOGIC ─────────────────────────────────────────────────────────────

def file_hashes(path):
    hashes = {"MD5": hashlib.md5(), "SHA-1": hashlib.sha1(), "SHA-256": hashlib.sha256()}
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            for h in hashes.values():
                h.update(chunk)
    return {k: v.hexdigest() for k, v in hashes.items()}


def shannon_entropy(path):
    with open(path, "rb") as f:
        data = f.read()
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    for x in range(256):
        p_x = data.count(bytes([x])) / length
        if p_x > 0:
            entropy -= p_x * math.log2(p_x)
    return round(entropy, 4)


def filesystem_metadata(path):
    st = os.stat(path)
    return {
        "Size": f"{st.st_size:,} bytes  ({_human_size(st.st_size)})",
        "Permissions": stat.filemode(st.st_mode),
        "Created": datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d  %H:%M:%S"),
        "Modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d  %H:%M:%S"),
        "Accessed": datetime.fromtimestamp(st.st_atime).strftime("%Y-%m-%d  %H:%M:%S"),
    }


def _human_size(b):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def magic_metadata(path):
    try:
        m = magic.Magic(mime=True)
        return {"MIME Type": m.from_file(path), "File Type": magic.from_file(path)}
    except Exception:
        return {"MIME Type": "Unknown", "File Type": "Unknown"}


def extract_image_exif(path):
    try:
        img = Image.open(path)
        exif = img._getexif()
        if not exif:
            return {}
        result = {}
        for k, v in exif.items():
            tag = ExifTags.TAGS.get(k, str(k))
            if isinstance(v, bytes):
                v = v.hex()
            result[tag] = str(v)
        return result
    except Exception:
        return {}


def extract_pdf_metadata(path):
    try:
        reader = PdfReader(path)
        return {k.strip("/"): str(v) for k, v in reader.metadata.items()}
    except Exception:
        return {}


def extract_docx_metadata(path):
    try:
        doc = Document(path)
        cp = doc.core_properties
        return {
            "Author": str(cp.author),
            "Created": str(cp.created),
            "Modified": str(cp.modified),
            "Title": str(cp.title),
            "Subject": str(cp.subject),
        }
    except Exception:
        return {}


def extract_xlsx_metadata(path):
    try:
        wb = load_workbook(path)
        props = wb.properties
        return {
            "Creator": str(props.creator),
            "Created": str(props.created),
            "Modified": str(props.modified),
            "Title": str(props.title),
        }
    except Exception:
        return {}


def extract_media_metadata(path):
    if not HACHOIR_AVAILABLE:
        return {}
    try:
        parser = createParser(path)
        if not parser:
            return {}
        meta = extractMetadata(parser)
        if not meta:
            return {}
        raw = meta.exportDictionary()
        flat = {}
        if isinstance(raw, dict):
            for section, items in raw.items():
                if isinstance(items, dict):
                    for k, v in items.items():
                        flat[f"{section} — {k}"] = str(v)
                else:
                    flat[str(section)] = str(items)
        return flat
    except Exception:
        return {}


def extract_all(path):
    result = {
        "📁 Filesystem": filesystem_metadata(path),
        "🔐 Cryptographic Hashes": file_hashes(path),
        "⚡ Entropy": {"Shannon Entropy": f"{shannon_entropy(path)} / 8.0  (higher = more random/encrypted)"},
        "🔮 File Type": magic_metadata(path),
    }
    mime = result["🔮 File Type"].get("MIME Type", "")
    if mime.startswith("image"):
        exif = extract_image_exif(path)
        if exif:
            result["📷 EXIF Data"] = exif
    elif mime == "application/pdf":
        pdf = extract_pdf_metadata(path)
        if pdf:
            result["📄 PDF Metadata"] = pdf
    elif "wordprocessingml" in mime:
        docx = extract_docx_metadata(path)
        if docx:
            result["📝 DOCX Metadata"] = docx
    elif "spreadsheetml" in mime:
        xlsx = extract_xlsx_metadata(path)
        if xlsx:
            result["📊 XLSX Metadata"] = xlsx
    media = extract_media_metadata(path)
    if media:
        result["🎬 Media Metadata"] = media
    return result


# ─── MAIN APPLICATION ──────────────────────────────────────────────────────────

class TechniSAMApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("MetaShinigami •  Metadata Forensics Suite")
        self.geometry("1200x800")
        self.minsize(960, 640)
        self.configure(fg_color=C_BG)
        self._current_file = None
        self._result_data  = {}
        self._build_ui()

    # ── BUILD UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header bar ──────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=C_PANEL, height=70, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        logo_lbl = ctk.CTkLabel(
            header,
            text="⬡  MetaShinigami",
            font=ctk.CTkFont(family="Courier New", size=22, weight="bold"),
            text_color=C_ACCENT,
        )
        logo_lbl.pack(side="left", padx=28, pady=16)

        sub_lbl = ctk.CTkLabel(
            header,
            text="METADATA FORENSICS SUITE  •  FILE INTELLIGENCE",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color=C_SUBTEXT,
        )
        sub_lbl.pack(side="left", padx=0, pady=26)

        # version badge
        ver = ctk.CTkLabel(
            header,
            text="v2.0",
            font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
            text_color=C_ACCENT3,
            fg_color=C_BORDER,
            corner_radius=4,
            width=40, height=22,
        )
        ver.pack(side="right", padx=24, pady=22)

        # ── Body (3-panel layout) ────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color=C_BG)
        body.pack(fill="both", expand=True, padx=16, pady=(10, 0))

        # Left sidebar
        self._build_sidebar(body)

        # Right main area
        self._build_main(body)

        # ── Status bar ──────────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Ready  •  Drag & drop a file or use Open File")
        status_bar = ctk.CTkFrame(self, fg_color=C_PANEL, height=30, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self._status_dot = ctk.CTkLabel(status_bar, text="●", font=ctk.CTkFont(size=11),
                                         text_color=C_SUBTEXT, width=20)
        self._status_dot.pack(side="left", padx=(14, 2), pady=6)

        ctk.CTkLabel(status_bar, textvariable=self._status_var,
                     font=ctk.CTkFont(family="Courier New", size=11),
                     text_color=C_SUBTEXT).pack(side="left", pady=6)

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color=C_PANEL, width=240, corner_radius=12)
        sidebar.pack(side="left", fill="y", padx=(0, 12), pady=(0, 12))
        sidebar.pack_propagate(False)

        # Drop zone
        drop_frame = ctk.CTkFrame(sidebar, fg_color=C_CARD, corner_radius=10,
                                   border_width=2, border_color=C_BORDER, height=160)
        drop_frame.pack(fill="x", padx=14, pady=(18, 10))
        drop_frame.pack_propagate(False)

        ctk.CTkLabel(drop_frame, text="⬇", font=ctk.CTkFont(size=36),
                     text_color=C_ACCENT2).pack(pady=(22, 4))
        ctk.CTkLabel(drop_frame, text="Drop file here\nor click Open",
                     font=ctk.CTkFont(family="Courier New", size=11),
                     text_color=C_SUBTEXT, justify="center").pack()

        # Open button
        self._open_btn = ctk.CTkButton(
            sidebar,
            text="⊕  Open File",
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
            fg_color=C_ACCENT2, hover_color="#5A20CC",
            text_color="white", corner_radius=8, height=42,
            command=self._open_file,
        )
        self._open_btn.pack(fill="x", padx=14, pady=(0, 6))

        # Scan button
        self._scan_btn = ctk.CTkButton(
            sidebar,
            text="⚡  Scan Metadata",
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
            fg_color=C_ACCENT, hover_color="#009BBF",
            text_color=C_BG, corner_radius=8, height=42,
            command=self._start_scan,
            state="disabled",
        )
        self._scan_btn.pack(fill="x", padx=14, pady=(0, 14))

        # Divider
        ctk.CTkFrame(sidebar, fg_color=C_BORDER, height=1).pack(fill="x", padx=14, pady=4)

        # File info card
        ctk.CTkLabel(sidebar, text="FILE INFO",
                     font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
                     text_color=C_SUBTEXT).pack(anchor="w", padx=18, pady=(12, 4))

        info_card = ctk.CTkFrame(sidebar, fg_color=C_CARD, corner_radius=8)
        info_card.pack(fill="x", padx=14, pady=(0, 10))

        self._fname_lbl = ctk.CTkLabel(info_card, text="—",
                                        font=ctk.CTkFont(family="Courier New", size=11, weight="bold"),
                                        text_color=C_TEXT, wraplength=190, justify="left")
        self._fname_lbl.pack(anchor="w", padx=12, pady=(10, 2))

        self._fsize_lbl = ctk.CTkLabel(info_card, text="",
                                        font=ctk.CTkFont(family="Courier New", size=10),
                                        text_color=C_SUBTEXT)
        self._fsize_lbl.pack(anchor="w", padx=12, pady=(0, 4))

        self._ftype_lbl = ctk.CTkLabel(info_card, text="",
                                        font=ctk.CTkFont(family="Courier New", size=10),
                                        text_color=C_ACCENT3, wraplength=190, justify="left")
        self._ftype_lbl.pack(anchor="w", padx=12, pady=(0, 10))

        # Divider
        ctk.CTkFrame(sidebar, fg_color=C_BORDER, height=1).pack(fill="x", padx=14, pady=4)

        # Export buttons
        ctk.CTkLabel(sidebar, text="EXPORT",
                     font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
                     text_color=C_SUBTEXT).pack(anchor="w", padx=18, pady=(12, 4))

        for label, cmd in [("Export JSON", self._export_json),
                            ("Export CSV",  self._export_csv),
                            ("Export TXT",  self._export_txt)]:
            btn = ctk.CTkButton(
                sidebar, text=label,
                font=ctk.CTkFont(family="Courier New", size=12),
                fg_color=C_CARD, hover_color=C_BORDER,
                text_color=C_TEXT, corner_radius=6, height=34,
                border_width=1, border_color=C_BORDER,
                command=cmd,
            )
            btn.pack(fill="x", padx=14, pady=3)

        # Progress bar
        ctk.CTkFrame(sidebar, fg_color=C_BORDER, height=1).pack(fill="x", padx=14, pady=(16, 4))
        self._progress = ctk.CTkProgressBar(sidebar, fg_color=C_CARD, progress_color=C_ACCENT,
                                             corner_radius=4, height=6)
        self._progress.pack(fill="x", padx=14, pady=(4, 6))
        self._progress.set(0)

        self._progress_lbl = ctk.CTkLabel(sidebar, text="",
                                           font=ctk.CTkFont(family="Courier New", size=10),
                                           text_color=C_SUBTEXT)
        self._progress_lbl.pack(anchor="w", padx=18)

    def _build_main(self, parent):
        main = ctk.CTkFrame(parent, fg_color=C_BG)
        main.pack(side="left", fill="both", expand=True)

        # Tab bar
        self._tabview = ctk.CTkTabview(
            main,
            fg_color=C_PANEL,
            segmented_button_fg_color=C_CARD,
            segmented_button_selected_color=C_ACCENT2,
            segmented_button_selected_hover_color="#5A20CC",
            segmented_button_unselected_color=C_CARD,
            segmented_button_unselected_hover_color=C_BORDER,
            text_color=C_TEXT,
            text_color_disabled=C_SUBTEXT,
            corner_radius=12,
        )
        self._tabview.pack(fill="both", expand=True, pady=(0, 12))

        self._tabview.add("Overview")
        self._tabview.add("Raw JSON")
        self._tabview.add("Hashes")
        self._tabview.add("Entropy")

        self._build_overview_tab()
        self._build_json_tab()
        self._build_hash_tab()
        self._build_entropy_tab()

    # ── TAB: OVERVIEW ──────────────────────────────────────────────────────────

    def _build_overview_tab(self):
        tab = self._tabview.tab("Overview")

        # scrollable container
        self._overview_scroll = ctk.CTkScrollableFrame(
            tab, fg_color=C_BG, scrollbar_button_color=C_BORDER,
            scrollbar_button_hover_color=C_ACCENT,
        )
        self._overview_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self._overview_inner = self._overview_scroll

        # placeholder
        self._overview_placeholder = ctk.CTkLabel(
            self._overview_inner,
            text="⬡\n\nOpen a file and click  ⚡ Scan Metadata\nto reveal forensic intelligence",
            font=ctk.CTkFont(family="Courier New", size=14),
            text_color=C_SUBTEXT, justify="center",
        )
        self._overview_placeholder.pack(expand=True, pady=120)

    def _render_overview(self, data: dict):
        # Clear
        for w in self._overview_inner.winfo_children():
            w.destroy()

        cols = 2
        col_frames = []
        row_frame = None

        all_sections = list(data.items())
        for idx, (section, items) in enumerate(all_sections):
            if idx % cols == 0:
                row_frame = ctk.CTkFrame(self._overview_inner, fg_color=C_BG)
                row_frame.pack(fill="x", padx=4, pady=4)
                col_frames = []
                for _ in range(cols):
                    cf = ctk.CTkFrame(row_frame, fg_color=C_BG)
                    cf.pack(side="left", fill="both", expand=True, padx=4)
                    col_frames.append(cf)

            col = col_frames[idx % cols]
            self._make_section_card(col, section, items)

    def _make_section_card(self, parent, title, items: dict):
        card = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=10,
                             border_width=1, border_color=C_BORDER)
        card.pack(fill="both", expand=True, pady=2)

        # Section header
        hdr = ctk.CTkFrame(card, fg_color=C_BORDER, corner_radius=0, height=34)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=title,
                     font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
                     text_color=C_ACCENT).pack(side="left", padx=14, pady=6)

        # Rows
        for i, (k, v) in enumerate(items.items()):
            row = ctk.CTkFrame(card,
                               fg_color=C_CARD if i % 2 == 0 else "#0D1424",
                               corner_radius=0, height=28)
            row.pack(fill="x")
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=str(k),
                         font=ctk.CTkFont(family="Courier New", size=11),
                         text_color=C_SUBTEXT, width=160, anchor="w").pack(side="left", padx=(12, 4), pady=4)

            ctk.CTkLabel(row, text=str(v),
                         font=ctk.CTkFont(family="Courier New", size=11),
                         text_color=C_TEXT, anchor="w", wraplength=380, justify="left").pack(
                             side="left", padx=(0, 8), pady=4, fill="x", expand=True)

    # ── TAB: RAW JSON ──────────────────────────────────────────────────────────

    def _build_json_tab(self):
        tab = self._tabview.tab("Raw JSON")
        self._json_text = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Courier New", size=12),
            fg_color=C_CARD,
            text_color=C_ACCENT3,
            scrollbar_button_color=C_BORDER,
            scrollbar_button_hover_color=C_ACCENT,
            corner_radius=8,
        )
        self._json_text.pack(fill="both", expand=True, padx=4, pady=4)
        self._json_text.insert("1.0", "// Run a scan to see raw JSON output\n")
        self._json_text.configure(state="disabled")

    # ── TAB: HASHES ────────────────────────────────────────────────────────────

    def _build_hash_tab(self):
        tab = self._tabview.tab("Hashes")
        self._hash_frame = ctk.CTkScrollableFrame(tab, fg_color=C_BG,
                                                   scrollbar_button_color=C_BORDER,
                                                   scrollbar_button_hover_color=C_ACCENT)
        self._hash_frame.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(self._hash_frame, text="Run a scan to generate cryptographic hashes",
                     font=ctk.CTkFont(family="Courier New", size=13),
                     text_color=C_SUBTEXT).pack(pady=80)

    def _render_hashes(self, hashes: dict):
        for w in self._hash_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(self._hash_frame, text="CRYPTOGRAPHIC HASH VERIFICATION",
                     font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
                     text_color=C_ACCENT).pack(anchor="w", padx=10, pady=(16, 8))

        for algo, val in hashes.items():
            card = ctk.CTkFrame(self._hash_frame, fg_color=C_CARD, corner_radius=8,
                                border_width=1, border_color=C_BORDER)
            card.pack(fill="x", padx=8, pady=6)

            ctk.CTkLabel(card, text=algo,
                         font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
                         text_color=C_ACCENT2, width=80).pack(side="left", padx=14, pady=14)

            # Hash in monospace blocks
            hash_box = ctk.CTkFrame(card, fg_color=C_BG, corner_radius=6)
            hash_box.pack(side="left", fill="x", expand=True, padx=(0, 14), pady=10)

            ctk.CTkLabel(hash_box, text=val,
                         font=ctk.CTkFont(family="Courier New", size=11),
                         text_color=C_ACCENT3).pack(padx=12, pady=8)

            # Copy button
            def _copy(v=val):
                self.clipboard_clear(); self.clipboard_append(v)
                self._set_status(f"Copied {v[:16]}… to clipboard", C_SUCCESS)

            ctk.CTkButton(card, text="Copy", font=ctk.CTkFont(family="Courier New", size=11),
                          fg_color=C_BORDER, hover_color=C_ACCENT2,
                          text_color=C_TEXT, corner_radius=6, width=60, height=30,
                          command=_copy).pack(side="right", padx=14, pady=12)

    # ── TAB: ENTROPY ───────────────────────────────────────────────────────────

    def _build_entropy_tab(self):
        tab = self._tabview.tab("Entropy")
        self._entropy_frame = ctk.CTkFrame(tab, fg_color=C_BG)
        self._entropy_frame.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(self._entropy_frame, text="Run a scan to calculate Shannon entropy",
                     font=ctk.CTkFont(family="Courier New", size=13),
                     text_color=C_SUBTEXT).pack(pady=80)

    def _render_entropy(self, value: float):
        for w in self._entropy_frame.winfo_children():
            w.destroy()

        pct = value / 8.0
        if pct < 0.4:
            color, label, desc = C_SUCCESS, "LOW", "Likely plain text or structured data"
        elif pct < 0.7:
            color, label, desc = C_WARN, "MEDIUM", "Mixed content, partial compression"
        else:
            color, label, desc = C_ERROR, "HIGH", "Encrypted, compressed, or obfuscated data"

        ctk.CTkLabel(self._entropy_frame, text="SHANNON ENTROPY ANALYSIS",
                     font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
                     text_color=C_ACCENT).pack(pady=(24, 4))

        # Big number display
        big = ctk.CTkFrame(self._entropy_frame, fg_color=C_CARD, corner_radius=16,
                            border_width=2, border_color=color, width=340, height=180)
        big.pack(pady=20)
        big.pack_propagate(False)

        ctk.CTkLabel(big, text=f"{value:.4f}",
                     font=ctk.CTkFont(family="Courier New", size=56, weight="bold"),
                     text_color=color).pack(pady=(22, 0))
        ctk.CTkLabel(big, text="bits per byte",
                     font=ctk.CTkFont(family="Courier New", size=12),
                     text_color=C_SUBTEXT).pack()

        # Level badge
        ctk.CTkLabel(self._entropy_frame, text=f"[ {label} ENTROPY ]",
                     font=ctk.CTkFont(family="Courier New", size=16, weight="bold"),
                     text_color=color).pack(pady=6)

        # Progress bar gauge
        gauge_frame = ctk.CTkFrame(self._entropy_frame, fg_color=C_BG)
        gauge_frame.pack(pady=8, padx=60, fill="x")

        ctk.CTkLabel(gauge_frame, text="0.0", font=ctk.CTkFont(size=10), text_color=C_SUBTEXT).pack(side="left")

        bar = ctk.CTkProgressBar(gauge_frame, fg_color=C_CARD, progress_color=color,
                                  corner_radius=4, height=14)
        bar.pack(side="left", fill="x", expand=True, padx=8)
        bar.set(pct)

        ctk.CTkLabel(gauge_frame, text="8.0", font=ctk.CTkFont(size=10), text_color=C_SUBTEXT).pack(side="left")

        ctk.CTkLabel(self._entropy_frame, text=desc,
                     font=ctk.CTkFont(family="Courier New", size=12),
                     text_color=C_SUBTEXT).pack(pady=8)

        # Interpretation guide
        guide = ctk.CTkFrame(self._entropy_frame, fg_color=C_CARD, corner_radius=8)
        guide.pack(padx=40, pady=12, fill="x")

        for lvl, col, info in [
            ("0.0 – 3.2", C_SUCCESS, "Plain text, source code, XML/JSON"),
            ("3.2 – 5.6", C_WARN,    "Structured binary, partially compressed"),
            ("5.6 – 8.0", C_ERROR,   "Encrypted, compressed, or random data"),
        ]:
            row = ctk.CTkFrame(guide, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(row, text="●", text_color=col, width=16).pack(side="left")
            ctk.CTkLabel(row, text=lvl, font=ctk.CTkFont(family="Courier New", size=11),
                         text_color=C_TEXT, width=110).pack(side="left", padx=6)
            ctk.CTkLabel(row, text=info, font=ctk.CTkFont(family="Courier New", size=11),
                         text_color=C_SUBTEXT).pack(side="left")

    # ── ACTIONS ────────────────────────────────────────────────────────────────

    def _open_file(self):
        path = filedialog.askopenfilename(title="Select a file to analyze")
        if path:
            self._load_file(path)

    def _load_file(self, path):
        self._current_file = path
        name = os.path.basename(path)
        size = _human_size(os.path.getsize(path))
        self._fname_lbl.configure(text=name)
        self._fsize_lbl.configure(text=size)
        try:
            m = magic.Magic(mime=True)
            mime = m.from_file(path)
        except Exception:
            mime = "unknown"
        self._ftype_lbl.configure(text=mime)
        self._scan_btn.configure(state="normal")
        self._set_status(f"Loaded: {name}", C_ACCENT)

    def _start_scan(self):
        if not self._current_file:
            return
        self._scan_btn.configure(state="disabled")
        self._progress.set(0)
        self._progress_lbl.configure(text="Scanning…")
        self._set_status("Scanning…", C_WARN)
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        steps = [0.1, 0.3, 0.55, 0.75, 0.9, 1.0]
        labels = ["Reading filesystem…", "Computing hashes…", "Detecting type…",
                  "Extracting metadata…", "Calculating entropy…", "Done!"]

        def _prog(i):
            self._progress.set(steps[i])
            self._progress_lbl.configure(text=labels[i])

        try:
            self.after(0, _prog, 0); time.sleep(0.1)
            data = extract_all(self._current_file)
            self.after(0, _prog, 1); time.sleep(0.05)
            self.after(0, _prog, 2); time.sleep(0.05)
            self.after(0, _prog, 3); time.sleep(0.05)
            self.after(0, _prog, 4); time.sleep(0.05)
            self._result_data = data
            self.after(0, self._display_results, data)
            self.after(0, _prog, 5)
        except Exception as e:
            self.after(0, self._set_status, f"Error: {e}", C_ERROR)
        finally:
            self.after(0, lambda: self._scan_btn.configure(state="normal"))

    def _display_results(self, data: dict):
        self._render_overview(data)

        hashes = data.get("🔐 Cryptographic Hashes", {})
        self._render_hashes(hashes)

        entropy_str = data.get("⚡ Entropy", {}).get("Shannon Entropy", "0 /")
        try:
            entropy_val = float(entropy_str.split("/")[0].strip())
        except Exception:
            entropy_val = 0.0
        self._render_entropy(entropy_val)

        # JSON tab
        self._json_text.configure(state="normal")
        self._json_text.delete("1.0", "end")
        self._json_text.insert("1.0", json.dumps(data, indent=2, default=str))
        self._json_text.configure(state="disabled")

        self._set_status(f"Scan complete  •  {len(data)} sections extracted", C_SUCCESS)

    # ── EXPORT ─────────────────────────────────────────────────────────────────

    def _export_json(self):
        if not self._result_data:
            messagebox.showwarning("No data", "Run a scan first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json")])
        if path:
            with open(path, "w") as f:
                json.dump(self._result_data, f, indent=2, default=str)
            self._set_status(f"Exported JSON → {os.path.basename(path)}", C_SUCCESS)

    def _export_csv(self):
        if not self._result_data:
            messagebox.showwarning("No data", "Run a scan first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if path:
            def flatten(d, parent="", sep="."):
                items = {}
                for k, v in d.items():
                    key = f"{parent}{sep}{k}" if parent else k
                    if isinstance(v, dict):
                        items.update(flatten(v, key, sep))
                    else:
                        items[key] = v
                return items
            flat = flatten(self._result_data)
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(flat.keys())
                w.writerow(flat.values())
            self._set_status(f"Exported CSV → {os.path.basename(path)}", C_SUCCESS)

    def _export_txt(self):
        if not self._result_data:
            messagebox.showwarning("No data", "Run a scan first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text", "*.txt")])
        if path:
            lines = []
            def walk(d, indent=0):
                for k, v in d.items():
                    if isinstance(v, dict):
                        lines.append("  " * indent + f"[{k}]")
                        walk(v, indent + 1)
                    else:
                        lines.append("  " * indent + f"{k}: {v}")
            walk(self._result_data)
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self._set_status(f"Exported TXT → {os.path.basename(path)}", C_SUCCESS)

    # ── HELPERS ────────────────────────────────────────────────────────────────

    def _set_status(self, msg, color=None):
        self._status_var.set(f"  {msg}")
        if color:
            self._status_dot.configure(text_color=color)


# ─── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = TechniSAMApp()
    app.mainloop()
