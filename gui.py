import os
import stat
import sys
import math
import json
import csv
import argparse
import hashlib
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

import magic
from PIL import Image, ExifTags
from PyPDF2 import PdfReader
from docx import Document
from openpyxl import load_workbook
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


def file_hashes(path):
    hashes = {
        "md5": hashlib.md5(),
        "sha1": hashlib.sha1(),
        "sha256": hashlib.sha256()
    }
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
        "size": st.st_size,
        "permissions": stat.filemode(st.st_mode),
        "created": datetime.fromtimestamp(st.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(st.st_atime).isoformat(),
    }


def magic_metadata(path):
    m = magic.Magic(mime=True)
    return {
        "mime_type": m.from_file(path),
        "file_type": magic.from_file(path)
    }


def extract_image_exif(path):
    try:
        img = Image.open(path)
        exif = img._getexif()
        if not exif:
            return {}
        return {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
    except Exception:
        return {}


def extract_pdf_metadata(path):
    try:
        reader = PdfReader(path)
        return {k.strip("/"): v for k, v in reader.metadata.items()}
    except Exception:
        return {}


def extract_docx_metadata(path):
    try:
        doc = Document(path)
        cp = doc.core_properties
        return {
            "author": cp.author,
            "created": str(cp.created),
            "modified": str(cp.modified),
            "title": cp.title,
            "subject": cp.subject,
        }
    except Exception:
        return {}


def extract_xlsx_metadata(path):
    try:
        wb = load_workbook(path)
        props = wb.properties
        return {
            "creator": props.creator,
            "created": str(props.created),
            "modified": str(props.modified),
            "title": props.title,
        }
    except Exception:
        return {}


def extract_media_metadata(path):
    try:
        parser = createParser(path)
        if not parser:
            return {}
        meta = extractMetadata(parser)
        if not meta:
            return {}
        return meta.exportDictionary()
    except Exception:
        return {}


def extract_metadata(path):
    metadata = {
        "file": os.path.basename(path),
        "filesystem": filesystem_metadata(path),
        "hashes": file_hashes(path),
        "entropy": shannon_entropy(path),
        "magic": magic_metadata(path),
    }

    mime = metadata["magic"]["mime_type"]

    if mime.startswith("image"):
        metadata["exif"] = extract_image_exif(path)
    elif mime == "application/pdf":
        metadata["pdf"] = extract_pdf_metadata(path)
    elif mime.endswith("wordprocessingml.document"):
        metadata["docx"] = extract_docx_metadata(path)
    elif mime.endswith("spreadsheetml.sheet"):
        metadata["xlsx"] = extract_xlsx_metadata(path)

    metadata["media"] = extract_media_metadata(path)
    return metadata


def flatten_dict(d, parent_key="", sep="."):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep))
        else:
            items[new_key] = v
    return items


class MetadataGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal Metadata Extractor")
        self.geometry("900x600")

        self.file_path = tk.StringVar()
        self.output_format = tk.StringVar(value="json")

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Target File:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.file_path, width=70).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=self.browse_file).grid(row=0, column=2)

        ttk.Label(frame, text="Output Format:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(
            frame,
            textvariable=self.output_format,
            values=["json", "csv", "txt"],
            state="readonly",
            width=10
        ).grid(row=1, column=1, sticky="w")

        ttk.Button(frame, text="Extract Metadata", command=self.run_extraction)\
            .grid(row=1, column=2, padx=5)

        self.output_box = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.output_box.pack(fill="both", expand=True, padx=10, pady=10)

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_path.set(path)

    def run_extraction(self):
        path = self.file_path.get()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a valid file")
            return

        try:
            metadata = extract_metadata(path)
            self.output_box.delete("1.0", tk.END)

            if self.output_format.get() == "json":
                text = json.dumps(metadata, indent=2, default=str)
            elif self.output_format.get() == "csv":
                flat = flatten_dict(metadata)
                text = ",".join(flat.keys()) + "\n" + ",".join(map(str, flat.values()))
            else:
                lines = []

                def walk(d, indent=0):
                    for k, v in d.items():
                        if isinstance(v, dict):
                            lines.append("  " * indent + f"[{k}]")
                            walk(v, indent + 1)
                        else:
                            lines.append("  " * indent + f"{k}: {v}")

                walk(metadata)
                text = "\n".join(lines)

            self.output_box.insert(tk.END, text)

        except Exception as e:
            messagebox.showerror("Extraction Error", str(e))


if __name__ == "__main__":
    app = MetadataGUI()
    app.mainloop()
