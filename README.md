# PDF Visual Extraction Library

A Python library for extracting text and visual elements (tables, figures) from PDF documents using OpenAI's vision models. Perfect for RAG systems, document analysis, and automated data extraction.

## Features

- **📄 PDF Text Extraction**: Extract clean text content from PDF documents
- **🖼️ PDF to Images**: Convert PDF pages to high-quality images
- **🔍 Visual Element Detection**: Use OpenAI's GPT-4o-mini to detect and extract tables and figures
- **📊 Structured Data Extraction**: Extract tables in structured list format with all numerical data
- **📈 CSV Export**: Convert extracted tables to CSV format using LLM
- **📝 Multiple Export Formats**: Export to JSON, Markdown, and CSV
- **🚀 Simple API**: Easy-to-use command line interface and Python API
- **💰 Cost-Effective**: Uses GPT-4o-mini for optimal performance and cost

## Installation

### From Source

```bash
git clone https://github.com/yourusername/pdf-visual-extraction.git
cd pdf-visual-extraction
pip install -e .
```

### Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

### Command Line Usage

```bash
# Basic extraction
pdf-visual-extract --pdf_path document.pdf --output_dir ./output

# With markdown export
pdf-visual-extract --pdf_path document.pdf --output_dir ./output --export_md

# With CSV export
pdf-visual-extract --pdf_path document.pdf --output_dir ./output --export_csv

# Full pipeline with all exports
pdf-visual-extract --pdf_path document.pdf --output_dir ./output --export_md --export_csv --max_pages 5
```

### Python API Usage

```python
from pdf_visual_extraction import (
    extract_text_from_pdf,
    convert_pdf_to_images,
    process_images_openai,
    inject_tables_into_text,
    convert_tables_to_csv
)

# Extract text
text_data = extract_text_from_pdf("document.pdf", "output/text.json")

# Convert to images
convert_pdf_to_images("document.pdf", "output/images/")

# Detect visual elements
visual_data = process_images_openai("output/images/", "document", "output/visual.json")

# Inject tables into text
final_data = inject_tables_into_text(text_data, visual_data)

# Convert tables to CSV
csv_results = convert_tables_to_csv(final_data, "output", "document")
```

## Configuration

### Environment Variables

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### API Key in Code

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

## Output Format

The library generates structured JSON output with the following format:

```json
{
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

## Examples

### Financial Document Analysis

```bash
pdf-visual-extract \
  --pdf_path "earnings-report.pdf" \
  --output_dir "./analysis" \
  --export_md \
  --export_pdf \
  --max_pages 10
```

### Research Paper Processing

```bash
pdf-visual-extract \
  --pdf_path "research-paper.pdf" \
  --output_dir "./research" \
  --export_md \
  --max_pages 20
```

## File Structure

```
output/
├── document-name/
│   ├── text_extraction/
│   │   ├── document-name_text.json
│   │   └── document-name_with_tables.json
│   ├── images/
│   │   ├── page_000.png
│   │   └── page_001.png
│   ├── visual_detection/
│   │   └── document-name_tables_figures.json
│   ├── exports/
│   │   ├── document-name_report.md
│   │   └── document-name_report.pdf
│   └── document-name_pipeline_summary.md
```

## API Reference

### Core Functions

- `extract_text_from_pdf(pdf_path, output_path)`: Extract text from PDF
- `convert_pdf_to_images(pdf_path, output_dir)`: Convert PDF to images
- `process_images_openai(images_dir, pdf_name, output_file, max_pages)`: Detect visual elements
- `inject_tables_into_text(text_data, visual_data)`: Inject tables into text data
- `convert_json_to_markdown(json_data)`: Convert JSON to Markdown
- `convert_markdown_to_pdf(markdown_file, pdf_file)`: Convert Markdown to PDF

## Requirements

- Python 3.8+
- OpenAI API key
- poppler-utils (for PDF to image conversion)

### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
Download poppler binaries and add to PATH.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for providing the vision language models
- The open-source community for the underlying PDF processing libraries

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation
- Review the examples

---

**Made with ❤️ for the AI and document processing community**