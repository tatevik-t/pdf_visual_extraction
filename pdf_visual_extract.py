#!/usr/bin/env python3
"""
Command Line Interface for PDF Visual Extraction
Enhanced version that uses the library functions directly instead of subprocess calls
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Optional

# Add the current directory to Python path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_text_extractor import extract_text_from_pdf, save_text_extraction
from pdf_to_images import convert_pdf_to_images
from openai_vlm_detector import process_images_openai
from simple_table_injector import inject_tables_into_text, extract_tables_from_visual
from json_to_markdown import convert_json_to_markdown

def check_existing_files(dirs: dict, pdf_name: str, export_md: bool, force: bool) -> dict:
    """Check which processing steps can be skipped based on existing files"""
    skip_steps = {
        'text_extraction': False,
        'images': False,
        'visual_detection': False,
        'table_injection': False,
        'markdown_export': False
    }
    
    if force:
        return skip_steps
    
    # Check text extraction
    text_file = os.path.join(dirs['text'], f"{pdf_name}_text.json")
    if os.path.exists(text_file):
        skip_steps['text_extraction'] = True
        print("📄 Text extraction files found, skipping...")
    
    # Check images
    if os.path.exists(dirs['images']) and len(os.listdir(dirs['images'])) > 0:
        skip_steps['images'] = True
        print("🖼️  Image files found, skipping...")
    
    # Check visual detection
    visual_file = os.path.join(dirs['visual'], f"{pdf_name}_tables_figures.json")
    if os.path.exists(visual_file):
        skip_steps['visual_detection'] = True
        print("🔍 Visual detection files found, skipping...")
    
    # Check table injection
    final_file = os.path.join(dirs['text'], f"{pdf_name}_with_tables.json")
    if os.path.exists(final_file):
        skip_steps['table_injection'] = True
        print("📊 Table injection files found, skipping...")
    
    # Check markdown export
    if export_md:
        markdown_file = os.path.join(dirs['exports'], f"{pdf_name}_report.md")
        if os.path.exists(markdown_file):
            skip_steps['markdown_export'] = True
            print("📝 Markdown export files found, skipping...")
    
    return skip_steps

def run_pdf_visual_extraction(pdf_path: str, output_dir: str, max_pages: int = 10, 
                             export_md: bool = False, force: bool = False) -> bool:
    """
    Run the complete PDF visual extraction pipeline
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Output directory for all results
        max_pages: Maximum number of pages to process
        export_md: Whether to export to Markdown
        force: Whether to force reprocessing even if files exist
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract PDF name from path
        pdf_name = Path(pdf_path).stem
        
        # Create output directories
        base_dir = Path(output_dir) / pdf_name
        dirs = {
            'base': str(base_dir),
            'text': str(base_dir / 'text_extraction'),
            'images': str(base_dir / 'images'),
            'visual': str(base_dir / 'visual_detection'),
            'exports': str(base_dir / 'exports')
        }
        
        for dir_path in dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Check for existing files
        skip_steps = check_existing_files(dirs, pdf_name, export_md, force)
        
        print(f"🚀 Starting PDF Visual Extraction Pipeline")
        print(f"📄 PDF: {pdf_path}")
        print(f"📁 Output: {dirs['base']}")
        print(f"📊 Max pages: {max_pages}")
        if force:
            print(f"🔄 Force mode: Reprocessing all steps")
        
        # Step 1: Extract text from PDF
        print("\n" + "="*60)
        print("STEP: PDF Text Extraction")
        print("="*60)
        
        if skip_steps['text_extraction']:
            print("⏭️  Skipping text extraction (files exist)")
            text_output = os.path.join(dirs['text'], f"{pdf_name}_text.json")
            with open(text_output, 'r', encoding='utf-8') as f:
                text_data = json.load(f)
        else:
            print(f"Extracting text from: {pdf_path}")
            text_data = extract_text_from_pdf(pdf_path)
            text_output = os.path.join(dirs['text'], f"{pdf_name}_text.json")
            save_text_extraction(text_data, text_output)
            
            print(f"✅ Text extraction completed!")
            print(f"   Total pages: {text_data['total_pages']}")
            print(f"   Saved to: {text_output}")
        
        # Step 2: Convert PDF to images
        print("\n" + "="*60)
        print("STEP: PDF to Images Conversion")
        print("="*60)
        
        if skip_steps['images']:
            print("⏭️  Skipping image conversion (files exist)")
            image_files = [f for f in os.listdir(dirs['images']) if f.endswith('.png')]
        else:
            print(f"Converting PDF to images...")
            convert_pdf_to_images(pdf_path, dirs['images'], dpi=300, max_pages=max_pages)
            
            # Count generated images
            image_files = [f for f in os.listdir(dirs['images']) if f.endswith('.png')]
            
            print(f"✅ PDF to images conversion completed!")
            print(f"   Generated {len(image_files)} images")
            print(f"   Saved to: {dirs['images']}")
        
        # Step 3: OpenAI VLM Table/Figure Detection
        print("\n" + "="*60)
        print("STEP: OpenAI VLM Table/Figure Detection")
        print("="*60)
        
        visual_output = os.path.join(dirs['visual'], f"{pdf_name}_tables_figures.json")
        
        if skip_steps['visual_detection']:
            print("⏭️  Skipping visual detection (files exist)")
            with open(visual_output, 'r', encoding='utf-8') as f:
                visual_data = json.load(f)
        elif not os.getenv('OPENAI_API_KEY'):
            print("⚠️  Skipping VLM detection (no OpenAI API key)")
            print("   Set OPENAI_API_KEY to enable table/figure detection")
            
            # Create empty visual data structure
            visual_data = {
                'pdf_name': pdf_name,
                'total_pages': min(max_pages, text_data['total_pages']),
                'total_elements': 0,
                'pages': []
            }
            
            # Save empty visual data
            with open(visual_output, 'w', encoding='utf-8') as f:
                json.dump(visual_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ VLM detection skipped (no API key)")
            print(f"   Created empty visual data: {visual_output}")
        else:
            print(f"Detecting tables and figures...")
            visual_data = process_images_openai(dirs['images'], pdf_name, visual_output, max_pages)
            
            # Save the visual detection results
            with open(visual_output, 'w', encoding='utf-8') as f:
                json.dump(visual_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ VLM detection completed!")
            print(f"   Processed {visual_data.get('total_pages', 0)} pages")
            print(f"   Found {visual_data.get('total_elements', 0)} elements")
            print(f"   Saved to: {visual_output}")
        
        # Step 4: Inject tables into text
        print("\n" + "="*60)
        print("STEP: Table Injection")
        print("="*60)
        
        final_output = os.path.join(dirs['text'], f"{pdf_name}_with_tables.json")
        
        if skip_steps['table_injection']:
            print("⏭️  Skipping table injection (files exist)")
            with open(final_output, 'r', encoding='utf-8') as f:
                final_data = json.load(f)
        else:
            print(f"Injecting tables into text...")
            
            # Extract tables from visual data
            tables_by_page = extract_tables_from_visual(visual_data)
            final_data = inject_tables_into_text(text_data, tables_by_page)
            
            # Save the final result
            with open(final_output, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Table injection completed!")
            print(f"   Final result saved to: {final_output}")
        
        # Step 5: Export to Markdown (if requested)
        if export_md:
            print("\n" + "="*60)
            print("STEP: Markdown Export")
            print("="*60)
            
            markdown_output = os.path.join(dirs['exports'], f"{pdf_name}_report.md")
            
            if skip_steps['markdown_export']:
                print("⏭️  Skipping markdown export (files exist)")
            else:
                print(f"Converting to Markdown...")
                
                markdown_content = convert_json_to_markdown(final_data)
                
                # Save markdown content to file
                with open(markdown_output, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                print(f"✅ Markdown export completed!")
                print(f"   Saved to: {markdown_output}")
        
        
        # Generate summary report
        print("\n" + "="*60)
        print("STEP: Summary Report Generation")
        print("="*60)
        
        summary_report = os.path.join(dirs['base'], f"{pdf_name}_pipeline_summary.md")
        create_summary_report(pdf_name, text_data, visual_data, final_data, 
                            dirs, export_md, summary_report)
        
        print(f"✅ Summary report generated!")
        print(f"   Saved to: {summary_report}")
        
        print("\n" + "="*60)
        print("🎉 PDF VISUAL EXTRACTION PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"📁 All outputs saved to: {dirs['base']}")
        print(f"📊 Final result: {final_output}")
        print(f"📋 Summary report: {summary_report}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_summary_report(pdf_name: str, text_data: dict, visual_data: dict, 
                         final_data: dict, dirs: dict, export_md: bool, 
                         summary_file: str) -> None:
    """Create a comprehensive summary report"""
    
    # Count elements by type
    element_counts = {}
    total_elements = 0
    
    for page_data in final_data.get('pages', []):
        for table in page_data.get('tables', []):
            element_type = 'table'
            element_counts[element_type] = element_counts.get(element_type, 0) + 1
            total_elements += 1
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# PDF Visual Extraction Pipeline Summary\n\n")
        f.write(f"**Document**: {pdf_name}\n")
        f.write(f"**Processing Date**: {Path().cwd()}\n")
        f.write(f"**Pipeline Type**: Enhanced (Text + Tables + Visual Detection)\n\n")
        
        f.write("## Processing Results\n\n")
        f.write(f"- **Total Pages**: {text_data.get('total_pages', 0)}\n")
        f.write(f"- **Total Characters**: {len(text_data.get('full_text', ''))}\n")
        f.write(f"- **Visual Elements Found**: {total_elements}\n")
        f.write(f"- **Element Types**: {element_counts}\n\n")
        
        f.write("## Generated Files\n\n")
        f.write("### Text Extraction\n")
        f.write(f"- `{dirs['text']}/{pdf_name}_text.json` (Original text)\n")
        f.write(f"- `{dirs['text']}/{pdf_name}_with_tables.json` (Text with tables injected)\n\n")
        
        f.write("### Images\n")
        f.write(f"- `{dirs['images']}/` (PNG files)\n\n")
        
        f.write("### Visual Detection\n")
        f.write(f"- `{dirs['visual']}/{pdf_name}_tables_figures.json`\n\n")
        
        if export_md:
            f.write("### Exports\n")
            f.write(f"- `{dirs['exports']}/{pdf_name}_report.md` (Markdown report)\n")
            f.write("\n")
        
        f.write("## Usage for RAG Systems\n\n")
        f.write(f"Use the final JSON file: `{dirs['text']}/{pdf_name}_with_tables.json`\n\n")
        f.write("This file contains:\n")
        f.write("- `text`: Original text content for each page\n")
        f.write("- `tables`: Array of table data for each page\n")
        f.write("- Each table has: `description`, `structured_data`, `raw_text`, `confidence`, `bbox`\n\n")
        
        f.write("## Pipeline Steps Completed\n\n")
        f.write("1. ✅ PDF Text Extraction\n")
        f.write("2. ✅ PDF to Images Conversion\n")
        f.write("3. ✅ OpenAI VLM Table/Figure Detection\n")
        f.write("4. ✅ Table Injection\n")
        step_num = 5
        if export_md:
            f.write(f"{step_num}. ✅ Markdown Export\n")
            step_num += 1
        f.write(f"{step_num}. ✅ Summary Report Generation\n")

def main():
    parser = argparse.ArgumentParser(description='Enhanced PDF Visual Extraction Pipeline')
    parser.add_argument('--pdf_path', required=True, help='Path to input PDF file')
    parser.add_argument('--output_dir', required=True, help='Output directory for all results')
    parser.add_argument('--max_pages', type=int, default=10, help='Maximum pages to process')
    parser.add_argument('--export_md', action='store_true', help='Export to Markdown format')
    parser.add_argument('--force', action='store_true', help='Force reprocessing even if output files exist')
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Check if OpenAI API key is set (for VLM detection)
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not set. VLM detection may fail.")
        print("   Set it with: export OPENAI_API_KEY='your-api-key-here'")
    
    # Run the pipeline
    success = run_pdf_visual_extraction(
        args.pdf_path, 
        args.output_dir, 
        args.max_pages,
        args.export_md,
        args.force
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
