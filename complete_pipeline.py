#!/usr/bin/env python3
"""
Complete PDF Visual Extraction Pipeline with Markdown Generation
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
    parser = argparse.ArgumentParser(description='Complete PDF Visual Extraction Pipeline')
    parser.add_argument('--pdf_path', required=True, help='Path to input PDF file')
    parser.add_argument('--output_dir', required=True, help='Output directory for all results')
    parser.add_argument('--max_pages', type=int, default=10, help='Maximum pages to process')
    parser.add_argument('--use_text_preserving', action='store_true', help='Use text-preserving blender instead of smart blender')
    
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
        'blended': str(base_dir / 'blended_output'),
        'markdown': str(base_dir / 'markdown_reports')
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    print(f"🚀 Starting Complete PDF Visual Extraction Pipeline")
    print(f"📄 PDF: {args.pdf_path}")
    print(f"📁 Output: {dirs['base']}")
    print(f"🔧 Text-preserving mode: {'Yes' if args.use_text_preserving else 'No'}")
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
    
    # Step 4: Blending (choose method)
    print("\n" + "="*60)
    print("STEP: Content Blending")
    print("="*60)
    
    if args.use_text_preserving:
        # Use text-preserving blender
        blended_output = os.path.join(dirs['blended'], f"{pdf_name}_text_preserving_blend.jsonl")
        blend_cmd = f"python text_preserving_blender.py --text_file '{text_output}' --visual_file '{visual_output}' --output_file '{blended_output}'"
        blend_type = "Text-Preserving Blending"
    else:
        # Use smart blender
        blended_output = os.path.join(dirs['blended'], f"{pdf_name}_blended_elements.jsonl")
        blend_cmd = f"python openai_smart_blender.py --text_file '{text_output}' --visual_file '{visual_output}' --output_file '{blended_output}'"
        blend_type = "OpenAI Smart Blending"
    
    if not run_command(blend_cmd, blend_type):
        return False
    
    # Step 5: Generate Markdown Report
    print("\n" + "="*60)
    print("STEP: Markdown Report Generation")
    print("="*60)
    markdown_output = os.path.join(dirs['markdown'], f"{pdf_name}_report.md")
    markdown_cmd = f"python jsonl_to_markdown.py --jsonl_file '{blended_output}' --output_file '{markdown_output}'"
    if not run_command(markdown_cmd, "Markdown Report Generation"):
        return False
    
    # Generate summary report
    print("\n" + "="*60)
    print("STEP: Summary Report Generation")
    print("="*60)
    
    summary_report = os.path.join(dirs['base'], f"{pdf_name}_pipeline_summary.md")
    with open(summary_report, 'w') as f:
        f.write(f"# Complete PDF Visual Extraction Pipeline Summary\n\n")
        f.write(f"**Document**: {pdf_name}\n")
        f.write(f"**Processing Date**: {subprocess.run('date', shell=True, capture_output=True, text=True).stdout.strip()}\n")
        f.write(f"**Pipeline Type**: {'Text-Preserving' if args.use_text_preserving else 'Smart Blending'}\n")
        f.write(f"**Max Pages Processed**: {args.max_pages}\n\n")
        
        f.write("## Generated Files\n\n")
        f.write("### Text Extraction\n")
        f.write(f"- `{text_output}`\n\n")
        
        f.write("### Images\n")
        f.write(f"- `{dirs['images']}/` (PNG files)\n\n")
        
        f.write("### Visual Detection\n")
        f.write(f"- `{visual_output}`\n\n")
        
        f.write("### Blended Output\n")
        f.write(f"- `{blended_output}`\n\n")
        
        f.write("### Markdown Report\n")
        f.write(f"- `{markdown_output}`\n\n")
        
        f.write("## Usage\n\n")
        f.write("### For RAG Systems\n")
        f.write(f"Use the JSONL file: `{blended_output}`\n\n")
        f.write("### For Human Reading\n")
        f.write(f"View the markdown report: `{markdown_output}`\n\n")
        
        f.write("## Pipeline Steps Completed\n\n")
        f.write("1. ✅ PDF Text Extraction\n")
        f.write("2. ✅ PDF to Images Conversion\n")
        f.write("3. ✅ OpenAI VLM Table/Figure Detection\n")
        f.write(f"4. ✅ {blend_type}\n")
        f.write("5. ✅ Markdown Report Generation\n")
        f.write("6. ✅ Summary Report Generation\n")
    
    print(f"📋 Summary report generated: {summary_report}")
    
    print("\n" + "="*60)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"📁 All outputs saved to: {dirs['base']}")
    print(f"📊 Blended elements: {blended_output}")
    print(f"📄 Markdown report: {markdown_output}")
    print(f"📋 Summary report: {summary_report}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
