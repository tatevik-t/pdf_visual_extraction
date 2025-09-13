# OpenAI PDF Visual Extraction Pipeline

A complete pipeline for extracting and intelligently blending text and visual elements from PDFs using OpenAI's GPT-4o-mini model.

## 🚀 Features

- **GPT-4o-mini Visual Analysis**: High-quality table and figure detection
- **GPT-4o-mini Intelligent Blending**: Semantic understanding of text-visual relationships
- **RAG Optimized**: Perfect output format for retrieval systems
- **Robust Error Handling**: Fallback strategies for reliable processing
- **Structured Data**: Clean, searchable output with rich metadata

## 📋 Requirements

```bash
pip install -r requirements_openai.txt
```

## 🔑 Setup

1. **Get OpenAI API Key**: Sign up at [OpenAI](https://platform.openai.com/) and get your API key

2. **Set Environment Variable**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## 🏃‍♂️ Quick Start

### Complete Pipeline
```bash
python openai_pipeline.py --pdf_path "path/to/your/document.pdf"
```

### Individual Steps

1. **Extract Text**:
   ```bash
   python pdf_text_extractor.py --pdf_path "document.pdf" --output_file "text.json"
   ```

2. **Convert to Images**:
   ```bash
   python pdf_to_images.py --pdf_path "document.pdf" --output_dir "images/"
   ```

3. **Detect Tables/Figures**:
   ```bash
   python openai_vlm_detector.py --images_dir "images/" --pdf_name "document" --output_file "visual.json"
   ```

4. **Blend Content**:
   ```bash
   python openai_smart_blender.py --text_file "text.json" --visual_file "visual.json" --output_file "blended.jsonl"
   ```

## 📊 Output Format

### Blended Elements (JSONL)
```json
{
  "id": "element_1",
  "type": "integrated",
  "page": 1,
  "content": {
    "text": "Q4 2024 Financial Highlights...",
    "structured_data": "### Q4 2024 Financial Highlights\n- **Revenues**:\n  - 2023: $86,310 million\n  - 2024: $96,469 million",
    "context": "Financial results table with key metrics",
    "summary": "Strong revenue growth across all segments",
    "key_insights": ["12% revenue growth", "Strong Cloud performance", "Improved margins"]
  },
  "metadata": {
    "confidence": 0.95,
    "source": "both",
    "importance": "high",
    "category": "financial_metrics"
  }
}
```

## 🎯 Use Cases

### 1. RAG Systems
Perfect for retrieval-augmented generation systems:
- Rich metadata for filtering
- Structured data for queries
- Semantic understanding of content

### 2. Document Analysis
- Financial report analysis
- Research paper processing
- Legal document review

### 3. Data Extraction
- Table data extraction
- Figure analysis
- Content summarization

## 🔧 Configuration

### API Key Options
```bash
# Environment variable
export OPENAI_API_KEY="your-key"

# Command line
python openai_pipeline.py --pdf_path "doc.pdf" --api_key "your-key"

# .env file
echo "OPENAI_API_KEY=your-key" > .env
```

### Processing Options
```bash
# Limit pages
python openai_pipeline.py --pdf_path "doc.pdf" --max_pages 5

# Custom output directory
python openai_pipeline.py --pdf_path "doc.pdf" --output_dir "./my_output"
```

## 📈 Performance

### Model Capabilities
- **GPT-4o-mini**: Excellent at table/figure detection, data extraction, and content integration
- **JSON Output**: Reliable structured data generation
- **Cost-Effective**: Optimized for performance vs. cost ratio

### Processing Speed
- **Text Extraction**: ~1-2 seconds per page
- **Image Conversion**: ~2-3 seconds per page
- **VLM Detection**: ~10-15 seconds per page
- **Blending**: ~5-10 seconds per document

### Cost Estimation
- **GPT-4o-mini**: ~$0.00015-0.0003 per page
- **Total**: ~$0.00015-0.0003 per page

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```bash
   export OPENAI_API_KEY="your-key"
   ```

2. **Rate Limiting**
   - Add delays between requests
   - Use smaller batch sizes
   - Check your OpenAI usage limits

3. **JSON Parsing Errors**
   - The pipeline includes robust error handling
   - Fallback strategies ensure processing continues
   - Check logs for specific error details

4. **Memory Issues**
   - Process documents in smaller batches
   - Use `--max_pages` to limit processing

### Debug Mode
```bash
# Enable verbose logging
export OPENAI_DEBUG=1
python openai_pipeline.py --pdf_path "doc.pdf"
```

## 📁 Output Structure

```
openai_output/
└── document_name/
    ├── images/                    # PDF page images
    ├── text_extraction/          # Text extraction results
    ├── visual_detection/         # VLM detection results
    ├── blended_output/           # Final blended elements
    └── document_name_pipeline_report.md
```

## 🔄 Migration from vLLM

If migrating from the vLLM version:

1. **Install OpenAI requirements**:
   ```bash
   pip install -r requirements_openai.txt
   ```

2. **Set API key**:
   ```bash
   export OPENAI_API_KEY="your-key"
   ```

3. **Update scripts**:
   - Replace `vlm_table_figure_detector.py` with `openai_vlm_detector.py`
   - Replace `smart_text_visual_blender.py` with `openai_smart_blender.py`
   - Use `openai_pipeline.py` for complete pipeline

## 🚀 Advanced Usage

### Custom Prompts
Modify prompts in the respective modules:
- `openai_vlm_detector.py`: VLM detection prompt
- `openai_smart_blender.py`: Blending prompt

### Batch Processing
```bash
for pdf in *.pdf; do
    python openai_pipeline.py --pdf_path "$pdf" --output_dir "./batch_output"
done
```

### Integration with RAG
```python
import json

# Load blended elements
with open('blended_elements.jsonl', 'r') as f:
    elements = [json.loads(line) for line in f if line.strip()]

# Filter by importance
high_importance = [e for e in elements if e['metadata']['importance'] == 'high']

# Extract structured data
tables = [e for e in elements if e['type'] == 'visual' and 'table' in e['content'].get('structured_data', '')]
```

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review error logs
3. Ensure API key is valid
4. Check OpenAI service status

## 🎉 Benefits

- **Reliability**: OpenAI's robust models with excellent JSON output
- **Quality**: Superior understanding of financial documents
- **Integration**: Perfect for RAG systems and document analysis
- **Scalability**: Easy to process multiple documents
- **Maintenance**: No local model management required
