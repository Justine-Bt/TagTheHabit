# Tag The Habit -- HVPS-4 Data Annotation Tool

Simple image annotation tool for cloud particle classification.

## Quick Start

```bash
python image_annotator.py
```

1. Click **"Select Image Folder"**
2. Annotate using keyboard (1-9) or mouse clicks
3. Navigate with **← →** arrows
4. Annotations auto-save to "annotations.csv"

## Configuration

Edit "config.json" to customize:
- Class names (with a maximum of 9 classes supported)
- Image display sizes
- Output filename

## Output

CSV file with 3 columns:
- `image`: filename
- `class_index`: 0-9
- `class_name`: label

## Requirements

```bash
pip install Pillow
```

Python 3.7+ required.
