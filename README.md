# File Metadata Extractor

A comprehensive Python script for extracting metadata from various file types, including images, PDFs, documents, and media files.

## Features

- **File System Metadata**: Size, permissions, creation/modification/access timestamps
- **Cryptographic Hashes**: MD5, SHA1, SHA256 for file integrity verification
- **Shannon Entropy**: Calculate file randomness/entropy
- **MIME Type Detection**: Automatic file type identification
- **Format-Specific Metadata**:
  - **Images**: EXIF data (camera settings, GPS, timestamps)
  - **PDFs**: Document properties (title, author, creation date)
  - **Word Documents**: Core properties (author, created, modified)
  - **Excel Files**: Workbook properties
  - **Media Files**: Audio/video metadata (duration, bitrate, tags)
- **Universal Metadata**: Advanced extraction using hachoir for unsupported formats

## Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone or download the script
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. For Windows users, ensure `python-magic-bin` is used for file type detection

## Usage

Run the script with a file path as argument:

```bash
python MetaShinigami.py /path/to/file.jpg
```

The script outputs metadata in JSON format with the following structure:

```json
{
  "file": "filename.ext",
  "filesystem": {
    "size": 12345,
    "permissions": "-rw-r--r--",
    "created": "2023-01-01T12:00:00",
    "modified": "2023-01-01T12:00:00",
    "accessed": "2023-01-01T12:00:00"
  },
  "hashes": {
    "md5": "hash",
    "sha1": "hash",
    "sha256": "hash"
  },
  "entropy": 7.1234,
  "magic": {
    "mime_type": "image/jpeg",
    "file_type": "JPEG image data..."
  },
  "exif": {...},  // For images
  "pdf": {...},   // For PDFs
  "docx": {...},  // For Word docs
  "xlsx": {...},  // For Excel files
  "media": {...}  // Universal metadata
}
```

## Supported File Types

- Images: JPEG, PNG, TIFF, BMP
- Documents: PDF, DOCX, XLSX
- Media: MP3, MP4, AVI, MKV, FLV, etc.
- Archives: ZIP, RAR, 7Z
- Other: Any file with detectable metadata

## Dependencies

- `pillow`: Image processing and EXIF extraction
- `PyPDF2`: PDF metadata reading
- `mutagen`: Audio/video tag extraction
- `openpyxl`: Excel file handling
- `pytesseract`: OCR capabilities (requires Tesseract)
- `python-docx`: Word document processing
- `python-magic-bin`: File type detection
- `hachoir`: Advanced metadata parsing

## Notes

- For OCR functionality, install Tesseract OCR separately
- Some file types may require additional system libraries
- The script attempts all available extractors and gracefully handles failures
- Output is always valid JSON for easy parsing and integration

## License

This project is open source. Feel free to modify and distribute.