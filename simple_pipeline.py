#!/usr/bin/env python3
"""
Simple PDF Visual Extraction Pipeline: Extract text + inject tables
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command: str, step_name: str) -> bool:
    """Run a command and return success status"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {step_name} - Success!")
            if result.stdout:
                print(f"Output: {result.stdout}")
            return True
        else:
            print(f"❌ {step_name} - Failed!")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {step_name} - Exception: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Simple PDF Visual Extraction Pipeline')
    parser.add_argument('--pdf_path', required=True, help='Path to input PDF file')
    parser.add_argument('--output_dir', required=True, help='Output directory for all results')
    parser.add_argument('--max_pages', type=int, default=10, help='Maximum pages to process')
    parser.add_argument('--export_md', action='store_true', help='Export to Markdown format')
    parser.add_argument('--export_pdf', action='store_true', help='Export to PDF format')
    
    args = parser.parse_args()
    
    # Extract PDF name from path
    pdf_name = Path(args.pdf_path).stem
    
    # Create output directories
    base_dir = Path(args.output_dir) / pdf_name
    dirs = {
        'base': str(base_dir),
        'text': str(base_dir / 'text_extraction'),
        'images': str(base_dir / 'images'),
        'visual': str(base_dir / 'visual_detection'),
        'exports': str(base_dir / 'exports')
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    print(f"🚀 Starting Simple PDF Visual Extraction Pipeline")
    print(f"📄 PDF: {args.pdf_path}")
    print(f"📁 Output: {dirs['base']}")
    print(f"📊 Max pages: {args.max_pages}")
    
    # Step 1: Extract text from PDF
    print("\n" + "="*60)
    print("STEP: PDF Text Extraction")
    print("="*60)
    text_output = os.path.join(dirs['text'], f"{pdf_name}_text.json")
    text_cmd = f"python pdf_text_extractor.py --pdf_path '{args.pdf_path}' --output_path '{text_output}'"
    if not run_command(text_cmd, "PDF Text Extraction"):
        return False
    
    # Step 2: Convert PDF to images
    print("\n" + "="*60)
    print("STEP: PDF to Images Conversion")
    print("="*60)
    images_cmd = f"python pdf_to_images.py --pdf_path '{args.pdf_path}' --output_dir '{dirs['images']}'"
    if not run_command(images_cmd, "PDF to Images Conversion"):
        return False
    
    # Step 3: OpenAI VLM Table/Figure Detection
    print("\n" + "="*60)
    print("STEP: OpenAI VLM Table/Figure Detection")
    print("="*60)
    visual_output = os.path.join(dirs['visual'], f"{pdf_name}_tables_figures.json")
    vlm_cmd = f"python openai_vlm_detector.py --images_dir '{dirs['images']}' --pdf_name '{pdf_name}' --output_file '{visual_output}' --max_pages {args.max_pages}"
    if not run_command(vlm_cmd, "OpenAI VLM Detection"):
        return False
    
    # Step 4: Inject tables into text
    print("\n" + "="*60)
    print("STEP: Table Injection")
    print("="*60)
    final_output = os.path.join(dirs['text'], f"{pdf_name}_with_tables.json")
    inject_cmd = f"python simple_table_injector.py --text_file '{text_output}' --visual_file '{visual_output}' --output_file '{final_output}'"
    if not run_command(inject_cmd, "Table Injection"):
        return False
    
    # Step 5: Export to Markdown (if requested)
    if args.export_md:
        print("\n" + "="*60)
        print("STEP: Markdown Export")
        print("="*60)
        markdown_output = os.path.join(dirs['exports'], f"{pdf_name}_report.md")
        md_cmd = f"python json_to_markdown.py --input_file '{final_output}' --output_file '{markdown_output}'"
        if not run_command(md_cmd, "Markdown Export"):
            return False
    
    # Step 6: Export to PDF (if requested)
    if args.export_pdf:
        print("\n" + "="*60)
        print("STEP: PDF Export")
        print("="*60)
        pdf_output = os.path.join(dirs['exports'], f"{pdf_name}_report.pdf")
        if args.export_md:
            # Use existing markdown file
            markdown_file = os.path.join(dirs['exports'], f"{pdf_name}_report.md")
        else:
            # Create markdown first
            markdown_file = os.path.join(dirs['exports'], f"{pdf_name}_report.md")
            md_cmd = f"python json_to_markdown.py --input_file '{final_output}' --output_file '{markdown_file}'"
            if not run_command(md_cmd, "Markdown Export (for PDF)"):
                return False
        
        pdf_cmd = f"python markdown_to_pdf.py --input_file '{markdown_file}' --output_file '{pdf_output}'"
        if not run_command(pdf_cmd, "PDF Export"):
            return False
    
    # Generate summary report
    print("\n" + "="*60)
    print("STEP: Summary Report Generation")
    print("="*60)
    
    summary_report = os.path.join(dirs['base'], f"{pdf_name}_pipeline_summary.md")
    with open(summary_report, 'w') as f:
        f.write(f"# Simple PDF Visual Extraction Pipeline Summary\n\n")
        f.write(f"**Document**: {pdf_name}\n")
        f.write(f"**Processing Date**: {subprocess.run('date', shell=True, capture_output=True, text=True).stdout.strip()}\n")
        f.write(f"**Pipeline Type**: Simple (Text + Tables)\n")
        f.write(f"**Max Pages Processed**: {args.max_pages}\n\n")
        
        f.write("## Generated Files\n\n")
        f.write("### Text Extraction\n")
        f.write(f"- `{text_output}` (Original text)\n")
        f.write(f"- `{final_output}` (Text with tables injected)\n\n")
        
        f.write("### Images\n")
        f.write(f"- `{dirs['images']}/` (PNG files)\n\n")
        
        f.write("### Visual Detection\n")
        f.write(f"- `{visual_output}`\n\n")
        
        if args.export_md or args.export_pdf:
            f.write("### Exports\n")
            if args.export_md:
                f.write(f"- `{os.path.join(dirs['exports'], f'{pdf_name}_report.md')}` (Markdown report)\n")
            if args.export_pdf:
                f.write(f"- `{os.path.join(dirs['exports'], f'{pdf_name}_report.pdf')}` (PDF report)\n")
            f.write("\n")
        
        f.write("## Usage\n\n")
        f.write("### For RAG Systems\n")
        f.write(f"Use the final JSON file: `{final_output}`\n\n")
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
        if args.export_md:
            f.write(f"{step_num}. ✅ Markdown Export\n")
            step_num += 1
        if args.export_pdf:
            f.write(f"{step_num}. ✅ PDF Export\n")
            step_num += 1
        f.write(f"{step_num}. ✅ Summary Report Generation\n")
    
    print(f"📋 Summary report generated: {summary_report}")
    
    print("\n" + "="*60)
    print("🎉 SIMPLE PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"📁 All outputs saved to: {dirs['base']}")
    print(f"📊 Final result: {final_output}")
    print(f"📋 Summary report: {summary_report}")
    print("\n✨ Simple and clean - perfect for your needs!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
