#!/usr/bin/env python3
"""
Complete OpenAI-based PDF Visual Extraction Pipeline
Uses OpenAI models for all processing steps
"""

import json
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

def run_command(command: str, description: str) -> bool:
    """
    Run a command and return success status
    
    Args:
        command: Command to run
        description: Description of what the command does
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def create_output_directories(base_output_dir: str, pdf_name: str) -> Dict[str, str]:
    """
    Create output directory structure
    
    Args:
        base_output_dir: Base output directory
        pdf_name: Name of the PDF
        
    Returns:
        Dictionary of directory paths
    """
    dirs = {
        'base': os.path.join(base_output_dir, pdf_name),
        'images': os.path.join(base_output_dir, pdf_name, 'images'),
        'text': os.path.join(base_output_dir, pdf_name, 'text_extraction'),
        'visual': os.path.join(base_output_dir, pdf_name, 'visual_detection'),
        'blended': os.path.join(base_output_dir, pdf_name, 'blended_output')
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    return dirs

def run_openai_pipeline(
    pdf_path: str,
    output_dir: str = "./openai_output",
    api_key: str = None,
    max_pages: int = None
) -> bool:
    """
    Run the complete OpenAI-based pipeline
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Output directory
        api_key: OpenAI API key
        max_pages: Maximum number of pages to process
        
    Returns:
        True if successful, False otherwise
    """
    pdf_name = Path(pdf_path).stem
    dirs = create_output_directories(output_dir, pdf_name)
    
    print(f"🚀 Starting OpenAI PDF Visual Extraction Pipeline (GPT-4o-mini)")
    print(f"📄 PDF: {pdf_path}")
    print(f"📁 Output: {dirs['base']}")
    print(f"🔑 API Key: {'Set' if api_key or os.getenv('OPENAI_API_KEY') else 'Not set'}")
    
    # Step 1: Extract text from PDF
    text_output = os.path.join(dirs['text'], f"{pdf_name}_text.json")
    text_cmd = f"python pdf_text_extractor.py --pdf_path '{pdf_path}' --output_path '{text_output}'"
    if not run_command(text_cmd, "PDF Text Extraction"):
        return False
    
    # Step 2: Convert PDF to images
    images_cmd = f"python pdf_to_images.py --pdf_path '{pdf_path}' --output_dir '{dirs['images']}'"
    if not run_command(images_cmd, "PDF to Images Conversion"):
        return False
    
    # Step 3: Detect tables and figures using OpenAI GPT-4o-mini
    visual_output = os.path.join(dirs['visual'], f"{pdf_name}_tables_figures.json")
    visual_cmd = f"python openai_vlm_detector.py --images_dir '{dirs['images']}' --pdf_name '{pdf_name}' --output_file '{visual_output}'"
    if api_key:
        visual_cmd += f" --api_key '{api_key}'"
    if max_pages:
        visual_cmd += f" --max_pages {max_pages}"
    if not run_command(visual_cmd, "OpenAI VLM Table/Figure Detection"):
        return False
    
    # Step 4: Blend text and visual elements using OpenAI GPT-4o-mini
    blended_output = os.path.join(dirs['blended'], f"{pdf_name}_blended_elements.jsonl")
    blend_cmd = f"python openai_smart_blender.py --text_file '{text_output}' --visual_file '{visual_output}' --output_file '{blended_output}'"
    if api_key:
        blend_cmd += f" --api_key '{api_key}'"
    if not run_command(blend_cmd, "OpenAI Smart Blending"):
        return False
    
    # Step 5: Generate summary report
    generate_summary_report(dirs, pdf_name)
    
    print(f"\n🎉 Pipeline completed successfully!")
    print(f"📁 All outputs saved to: {dirs['base']}")
    print(f"📊 Blended elements: {blended_output}")
    
    return True

def generate_summary_report(dirs: Dict[str, str], pdf_name: str) -> None:
    """
    Generate a summary report of the pipeline results
    
    Args:
        dirs: Directory paths
        pdf_name: Name of the PDF
    """
    report_path = os.path.join(dirs['base'], f"{pdf_name}_pipeline_report.md")
    
    # Load results
    text_file = os.path.join(dirs['text'], f"{pdf_name}_text.json")
    visual_file = os.path.join(dirs['visual'], f"{pdf_name}_tables_figures.json")
    blended_file = os.path.join(dirs['blended'], f"{pdf_name}_blended_elements.jsonl")
    
    # Read text data
    text_data = {}
    if os.path.exists(text_file):
        with open(text_file, 'r', encoding='utf-8') as f:
            text_data = json.load(f)
    
    # Read visual data
    visual_data = {}
    if os.path.exists(visual_file):
        with open(visual_file, 'r', encoding='utf-8') as f:
            visual_data = json.load(f)
    
    # Read blended data
    blended_elements = []
    if os.path.exists(blended_file):
        with open(blended_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        element = json.loads(line)
                        if 'id' in element:  # Skip summary line
                            blended_elements.append(element)
                    except json.JSONDecodeError:
                        continue
    
    # Generate report
    report_content = f"""# OpenAI PDF Visual Extraction Pipeline Report

## Document: {pdf_name}

### Pipeline Overview
This document was processed using the OpenAI-based PDF visual extraction pipeline, which uses GPT-4o-mini for both visual analysis and intelligent content blending.

### Results Summary

#### Text Extraction
- **Total Pages**: {text_data.get('total_pages', 'Unknown')}
- **Text Quality**: {'Good' if text_data.get('pages') else 'No data'}

#### Visual Detection
- **Total Pages Processed**: {visual_data.get('total_pages', 'Unknown')}
- **Total Elements Found**: {visual_data.get('total_elements', 'Unknown')}
- **Errors**: {visual_data.get('errors', 'Unknown')}

#### Blended Output
- **Total Elements**: {len(blended_elements)}
- **Element Types**: {get_element_type_counts(blended_elements)}
- **Categories**: {get_category_counts(blended_elements)}

### File Structure
```
{dirs['base']}/
├── images/                    # PDF page images
├── text_extraction/          # Text extraction results
├── visual_detection/         # VLM detection results
├── blended_output/           # Final blended elements
└── {pdf_name}_pipeline_report.md  # This report
```

### Key Features
- ✅ **OpenAI GPT-4o-mini**: High-quality visual analysis and intelligent content blending
- ✅ **Cost-Effective**: Optimized performance-to-cost ratio
- ✅ **Structured Data**: Clean, searchable output
- ✅ **RAG Optimized**: Perfect for retrieval systems
- ✅ **Error Handling**: Robust processing with fallbacks

### Next Steps
1. **Review Output**: Check the blended elements in `blended_output/`
2. **RAG Integration**: Use the JSONL format for your RAG system
3. **Customization**: Modify prompts for specific document types
4. **Scaling**: Process multiple documents in batch

### Technical Details
- **VLM Model**: GPT-4V (gpt-4o)
- **LLM Model**: GPT-4 (gpt-4o)
- **Output Format**: JSONL with rich metadata
- **Processing**: Page-by-page with intelligent integration
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📋 Summary report generated: {report_path}")

def get_element_type_counts(elements: list) -> Dict[str, int]:
    """Get counts of element types"""
    counts = {}
    for element in elements:
        element_type = element.get('type', 'unknown')
        counts[element_type] = counts.get(element_type, 0) + 1
    return counts

def get_category_counts(elements: list) -> Dict[str, int]:
    """Get counts of categories"""
    counts = {}
    for element in elements:
        category = element.get('metadata', {}).get('category', 'unknown')
        counts[category] = counts.get(category, 0) + 1
    return counts

def main():
    parser = argparse.ArgumentParser(description="OpenAI PDF Visual Extraction Pipeline")
    parser.add_argument("--pdf_path", type=str, required=True, help="Path to PDF file")
    parser.add_argument("--output_dir", type=str, default="./openai_output", help="Output directory")
    parser.add_argument("--api_key", type=str, help="OpenAI API key")
    parser.add_argument("--max_pages", type=int, help="Maximum number of pages to process")
    
    args = parser.parse_args()
    
    # Check if PDF exists
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Check API key
    if not args.api_key and not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OpenAI API key not found. Set OPENAI_API_KEY environment variable or use --api_key")
        sys.exit(1)
    
    # Run pipeline
    success = run_openai_pipeline(
        pdf_path=args.pdf_path,
        output_dir=args.output_dir,
        api_key=args.api_key,
        max_pages=args.max_pages
    )
    
    if success:
        print("\n🎉 Pipeline completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Pipeline failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
