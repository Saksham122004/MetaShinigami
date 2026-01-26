# MetaShinigami Use Cases

This document demonstrates various use cases for the MetaShinigami metadata extraction tool.

## Basic Usage

Extract metadata from any file:

```bash
python MetaShinigami.py path/to/file.jpg
```

## Output Formats

### JSON (Default)
```bash
python MetaShinigami.py image.jpg
```

Output:
```json
{
  "file": "image.jpg",
  "filesystem": {...},
  "hashes": {...},
  "entropy": 7.1234,
  "magic": {...},
  "exif": {...},
  "media": {...}
}
```

### CSV Format
```bash
python MetaShinigami.py image.jpg --format csv
```

Output: Flattened metadata in CSV format with headers.

### Text Format
```bash
python MetaShinigami.py image.jpg --format txt
```

Output: Hierarchical text representation.

### Save to File
```bash
python MetaShinigami.py image.jpg --out metadata.json
python MetaShinigami.py image.jpg --format csv --out metadata.csv
```

## Supported File Types

### Images (JPEG, PNG, TIFF, etc.)
- EXIF metadata (camera settings, GPS, timestamps)
- Image properties (dimensions, DPI, color space)
- File hashes and entropy

Example:
```bash
python MetaShinigami.py photo.jpg
```

### PDFs
- Document properties (title, author, creation date)
- Page count, producer info

Example:
```bash
python MetaShinigami.py document.pdf
```

### Microsoft Office Documents
- Word (.docx): Author, creation/modification dates, title
- Excel (.xlsx): Creator, dates, title

Example:
```bash
python MetaShinigami.py report.docx
python MetaShinigami.py data.xlsx
```

### Media Files (Audio/Video)
- Duration, bitrate, sample rate
- Tags (artist, title, album)
- Codec information

Example:
```bash
python MetaShinigami.py song.mp3
python MetaShinigami.py video.mp4
```

### Archives and Other Files
- MIME type detection
- File size, permissions, timestamps
- Cryptographic hashes
- Shannon entropy analysis

## Automation Examples

### Batch Processing
```bash
for file in *.jpg; do
    python MetaShinigami.py "$file" --out "${file%.jpg}_metadata.json"
done
```

### Forensic Analysis
```bash
# Extract metadata for digital forensics
python MetaShinigami.py suspicious_file.exe --format json --out forensic_report.json
```

### Content Verification
```bash
# Check file integrity
python MetaShinigami.py important_document.pdf | jq '.hashes.sha256'
```

## Integration Examples

### Python Script Integration
```python
import subprocess
import json

def get_metadata(file_path):
    result = subprocess.run(
        ['python', 'MetaShinigami.py', file_path],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

metadata = get_metadata('image.jpg')
print(f"File size: {metadata['filesystem']['size']} bytes")
```

### Shell Script Integration
```bash
#!/bin/bash
FILE="$1"
METADATA=$(python MetaShinigami.py "$FILE")
SIZE=$(echo "$METADATA" | jq '.filesystem.size')
echo "File size: $SIZE bytes"
```

## Use Cases by Domain

### Digital Forensics
- File timeline analysis
- Hash verification
- Entropy analysis for packed/encrypted content
- EXIF data extraction from images

### Content Management
- Automatic metadata extraction for DAM systems
- File organization based on creation dates
- Duplicate detection using hashes

### Security Research
- Malware analysis (file properties, entropy)
- Steganography detection
- File type verification

### Photography
- Camera settings analysis
- GPS location extraction
- Image authenticity verification

### Document Management
- PDF properties extraction
- Office document metadata
- Version tracking

## Error Handling

The tool gracefully handles:
- Missing files (clear error messages)
- Unsupported formats (basic metadata still extracted)
- Corrupted files (partial metadata where possible)
- Permission issues (appropriate error reporting)

## Performance Notes

- Fast extraction for most file types
- Memory efficient for large files (streaming hash calculation)
- Parallel processing possible for batch operations
- Minimal dependencies for broad compatibility