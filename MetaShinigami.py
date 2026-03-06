import os
import stat
import sys
import math
import json
import csv
import argparse
import hashlib
import time
from datetime import datetime

import magic
from PIL import Image, ExifTags
from PyPDF2 import PdfReader
from docx import Document
from openpyxl import load_workbook
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


# ==============================
# COLOR CONSTANTS
# ==============================

GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"


# ==============================
# BANNER
# ==============================

def banner():
    os.system("cls" if os.name == "nt" else "clear")

    art = r"""
 ████████╗███████╗ ██████╗██╗  ██╗███╗   ██╗██╗ ██████╗ █████╗ ██╗
 ╚══██╔══╝██╔════╝██╔════╝██║  ██║████╗  ██║██║██╔════╝██╔══██╗██║
    ██║   █████╗  ██║     ███████║██╔██╗ ██║██║██║     ███████║██║
    ██║   ██╔══╝  ██║     ██╔══██║██║╚██╗██║██║██║     ██╔══██║██║
    ██║   ███████╗╚██████╗██║  ██║██║ ╚████║██║╚██████╗██║  ██║███████╗
    ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝

                    ███████╗ █████╗ ███╗   ███╗
                    ██╔════╝██╔══██╗████╗ ████║
                    ███████╗███████║██╔████╔██║
                    ╚════██║██╔══██║██║╚██╔╝██║
                    ███████║██║  ██║██║ ╚═╝ ██║
                    ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
    """

    print(GREEN + art + RESET)
    print(CYAN + "Universal Metadata Extractor")
    print(YELLOW + "Digital Forensics • File Intelligence • Hash Analysis")
    print(GREEN + "-" * 65)
    print(YELLOW + "             Developed by TECHNICAL SAM")
    print(GREEN + "-" * 65 + RESET)

    time.sleep(0.5)


# ==============================
# HASHES
# ==============================

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


# ==============================
# ENTROPY
# ==============================

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


# ==============================
# FILESYSTEM METADATA
# ==============================

def filesystem_metadata(path):
    st = os.stat(path)

    return {
        "size": st.st_size,
        "permissions": stat.filemode(st.st_mode),
        "created": datetime.fromtimestamp(st.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(st.st_atime).isoformat(),
    }


# ==============================
# FILE TYPE (MAGIC)
# ==============================

def magic_metadata(path):
    m = magic.Magic(mime=True)

    return {
        "mime_type": m.from_file(path),
        "file_type": magic.from_file(path)
    }


# ==============================
# IMAGE EXIF
# ==============================

def extract_image_exif(path):
    try:
        img = Image.open(path)
        exif = img._getexif()

        if not exif:
            return {}

        return {
            ExifTags.TAGS.get(k, k): v
            for k, v in exif.items()
        }

    except Exception:
        return {}


# ==============================
# PDF METADATA
# ==============================

def extract_pdf_metadata(path):
    try:
        reader = PdfReader(path)
        return {k.strip("/"): v for k, v in reader.metadata.items()}
    except Exception:
        return {}


# ==============================
# DOCX METADATA
# ==============================

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


# ==============================
# XLSX METADATA
# ==============================

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


# ==============================
# MEDIA METADATA
# ==============================

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


# ==============================
# MAIN EXTRACTION
# ==============================

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


# ==============================
# FLATTEN DICT (CSV)
# ==============================

def flatten_dict(d, parent_key="", sep="."):

    items = {}

    for k, v in d.items():

        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep))

        else:
            items[new_key] = v

    return items


# ==============================
# OUTPUT JSON
# ==============================

def output_json(metadata, out):

    data = json.dumps(metadata, indent=2, default=str)

    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(data)

    else:
        print(data)


# ==============================
# OUTPUT CSV
# ==============================

def output_csv(metadata, out):

    flat = flatten_dict(metadata)

    if out:
        f = open(out, "w", newline="", encoding="utf-8")

    else:
        f = None

    writer = csv.writer(f or sys.stdout)

    writer.writerow(flat.keys())
    writer.writerow(flat.values())

    if f:
        f.close()


# ==============================
# OUTPUT TXT
# ==============================

def output_txt(metadata, out):

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

    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)

    else:
        print(text)


# ==============================
# MAIN
# ==============================

def main():

    banner()

    parser = argparse.ArgumentParser(
        description="Universal Metadata Extractor (Pure Python)"
    )

    parser.add_argument("file", help="Target file")

    parser.add_argument(
        "--format",
        choices=["json", "csv", "txt"],
        default="json",
        help="Output format (default: json)"
    )

    parser.add_argument(
        "--out",
        help="Write output to file"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print("Error: file not found")
        sys.exit(1)

    metadata = extract_metadata(args.file)

    if args.format == "json":
        output_json(metadata, args.out)

    elif args.format == "csv":
        output_csv(metadata, args.out)

    elif args.format == "txt":
        output_txt(metadata, args.out)


if __name__ == "__main__":
    main()
