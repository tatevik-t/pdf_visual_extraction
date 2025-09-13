# API Reference

## Core Functions

### `extract_text_from_pdf(pdf_path, output_path)`

Extract text content from a PDF document.

**Parameters:**
- `pdf_path` (str): Path to the input PDF file
- `output_path` (str): Path where the extracted text JSON will be saved

**Returns:**
- `dict`: JSON data containing extracted text with page information

**Example:**
```python
from pdf_visual_extraction import extract_text_from_pdf

text_data = extract_text_from_pdf("document.pdf", "output/text.json")
```

### `convert_pdf_to_images(pdf_path, output_dir)`

Convert PDF pages to high-quality PNG images.

**Parameters:**
- `pdf_path` (str): Path to the input PDF file
- `output_dir` (str): Directory where images will be saved

**Returns:**
- `list`: List of generated image file paths

**Example:**
```python
from pdf_visual_extraction import convert_pdf_to_images

images = convert_pdf_to_images("document.pdf", "output/images/")
```

### `process_images_openai(images_dir, pdf_name, output_file, max_pages=10)`

Process images using OpenAI's vision model to detect tables and figures.

**Parameters:**
- `images_dir` (str): Directory containing page images
- `pdf_name` (str): Name of the PDF document
- `output_file` (str): Path where detection results will be saved
- `max_pages` (int): Maximum number of pages to process (default: 10)

**Returns:**
- `dict`: JSON data containing detection results

**Example:**
```python
from pdf_visual_extraction import process_images_openai

visual_data = process_images_openai(
    "output/images/", 
    "document", 
    "output/visual.json",
    max_pages=5
)
```

### `extract_tables_from_visual(visual_data)`

Extract table information from visual detection results.

**Parameters:**
- `visual_data` (dict): Visual detection results from OpenAI

**Returns:**
- `dict`: Dictionary mapping page numbers to lists of table data

**Example:**
```python
from pdf_visual_extraction import extract_tables_from_visual

tables_by_page = extract_tables_from_visual(visual_data)
```

### `inject_tables_into_text(text_data, tables_by_page)`

Inject table data into text extraction results.

**Parameters:**
- `text_data` (dict): Text extraction results
- `tables_by_page` (dict): Table data organized by page number

**Returns:**
- `dict`: Enhanced text data with injected table information

**Example:**
```python
from pdf_visual_extraction import inject_tables_into_text

final_data = inject_tables_into_text(text_data, tables_by_page)
```

### `convert_json_to_markdown(json_data)`

Convert JSON data to Markdown format.

**Parameters:**
- `json_data` (dict): JSON data with text and table information

**Returns:**
- `str`: Markdown formatted content

**Example:**
```python
from pdf_visual_extraction import convert_json_to_markdown

markdown_content = convert_json_to_markdown(final_data)
```

### `convert_markdown_to_pdf(markdown_file, pdf_file)`

Convert Markdown file to PDF.

**Parameters:**
- `markdown_file` (str): Path to input Markdown file
- `pdf_file` (str): Path where PDF will be saved

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
from pdf_visual_extraction import convert_markdown_to_pdf

success = convert_markdown_to_pdf("report.md", "report.pdf")
```

## Data Structures

### Text Data Format

```json
{
  "pdf_path": "path/to/document.pdf",
  "pdf_name": "document-name",
  "total_pages": 10,
  "pages": [
    {
      "page_number": 0,
      "text": "Page text content...",
      "tables": [
        {
          "description": "Table description",
          "structured_data": "### Table: Title\n- **Category**:\n  - Item: value",
          "raw_text": "Raw table text",
          "confidence": 0.95,
          "bbox": [x1, y1, x2, y2]
        }
      ]
    }
  ]
}
```

### Visual Detection Format

```json
{
  "pdf_name": "document-name",
  "images_dir": "path/to/images",
  "total_pages": 10,
  "total_elements": 5,
  "errors": 0,
  "pages": [
    {
      "page_number": 0,
      "image_path": "path/to/page_000.png",
      "image_filename": "page_000.png",
      "detection_result": {
        "page_analysis": {
          "has_tables": true,
          "has_figures": false,
          "total_elements": 1,
          "page_summary": "Page contains financial table"
        },
        "elements": [
          {
            "type": "table",
            "bbox": [0, 0, 100, 100],
            "confidence": 0.95,
            "description": "Financial data table",
            "content": {
              "structured_data": "### Table: Financial Data\n- **Revenue**: $1000",
              "raw_text": "Revenue $1000",
              "summary": "Financial summary"
            }
          }
        ]
      },
      "raw_response": "",
      "processing_timestamp": "1234567890.123"
    }
  ]
}
```

## Error Handling

All functions raise appropriate exceptions for common error conditions:

- `FileNotFoundError`: When input files don't exist
- `ValueError`: When required parameters are missing or invalid
- `RuntimeError`: When external processes fail
- `json.JSONDecodeError`: When JSON parsing fails

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required for visual element detection
- `PDF2IMAGE_DPI`: Optional, defaults to 300 for image quality

### Optional Dependencies

- `weasyprint`: For PDF export functionality
- `pytest`: For running tests
- `black`: For code formatting
- `flake8`: For linting
- `mypy`: For type checking
