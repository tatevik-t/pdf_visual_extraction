#!/usr/bin/env python3
"""
PDF Visual Extraction Pipeline
Complete pipeline that processes PDFs through text extraction, image conversion, 
VLM table/figure detection, and text-JSON blending
"""

import os
import subprocess
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional
import glob

def run_command(cmd: list, description: str, cwd: Optional[str] = None) -> bool:
    """
    Run a command and return success status
    
    Args:
        cmd: Command to run as list
        description: Description of what the command does
        cwd: Working directory for the command
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            cwd=cwd
        )
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def process_single_pdf(pdf_path: str, output_dir: str = "pdf_visual_output", 
                      vlm_model: str = "mistralai/Pixtral-12B-2409",
                      llm_model: str = "mistralai/Mistral-7B-Instruct-v0.2") -> bool:
    """
    Process a single PDF through the complete visual extraction pipeline
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save all outputs
        vlm_model: VLM model for table/figure detection
        llm_model: LLM model for text blending
        
    Returns:
        True if successful, False otherwise
    """
    pdf_name = Path(pdf_path).stem
    
    print(f"\n{'='*80}")
    print(f"PDF VISUAL EXTRACTION PIPELINE: {pdf_name}")
    print(f"PDF Path: {pdf_path}")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*80}")
    
    # Create output directory structure
    os.makedirs(output_dir, exist_ok=True)
    text_dir = os.path.join(output_dir, "text_extraction")
    images_dir = os.path.join(output_dir, "images")
    visual_dir = os.path.join(output_dir, "visual_detection")
    blended_dir = os.path.join(output_dir, "blended_output")
    
    os.makedirs(text_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(visual_dir, exist_ok=True)
    os.makedirs(blended_dir, exist_ok=True)
    
    # Step 1: Extract text from PDF
    print("\n🔄 Step 1: Extracting text from PDF...")
    text_output = os.path.join(text_dir, f"{pdf_name}_text.json")
    cmd = [
        "python", "pdf_text_extractor.py",
        "--pdf_path", pdf_path,
        "--output_path", text_output
    ]
    if not run_command(cmd, "PDF Text Extraction", cwd=os.path.dirname(os.path.abspath(__file__))):
        return False
    
    # Step 2: Convert PDF to images
    print("\n🔄 Step 2: Converting PDF to images...")
    pdf_images_dir = os.path.join(images_dir, pdf_name)
    cmd = [
        "python", "pdf_to_images.py",
        "--pdf_path", pdf_path,
        "--output_dir", pdf_images_dir,
        "--dpi", "300"
    ]
    if not run_command(cmd, "PDF to Images Conversion", cwd=os.path.dirname(os.path.abspath(__file__))):
        return False
    
    # Step 3: Detect tables and figures using VLM
    print("\n🔄 Step 3: Detecting tables and figures with VLM...")
    visual_output = os.path.join(visual_dir, f"{pdf_name}_tables_figures.json")
    cmd = [
        "python", "vlm_table_figure_detector.py",
        "--images_dir", pdf_images_dir,
        "--pdf_name", pdf_name,
        "--output_file", visual_output,
        "--model_name", vlm_model
    ]
    if not run_command(cmd, "VLM Table/Figure Detection", cwd=os.path.dirname(os.path.abspath(__file__))):
        return False
    
    # Step 4: Blend text and visual elements
    print("\n🔄 Step 4: Blending text and visual elements...")
    blended_output = os.path.join(blended_dir, f"{pdf_name}_blended_elements.jsonl")
    cmd = [
        "python", "text_json_blender.py",
        "--text_file", text_output,
        "--visual_file", visual_output,
        "--output_file", blended_output,
        "--model_name", llm_model
    ]
    if not run_command(cmd, "Text-Visual Blending", cwd=os.path.dirname(os.path.abspath(__file__))):
        return False
    
    # Step 5: Create summary report
    print("\n🔄 Step 5: Creating summary report...")
    create_summary_report(pdf_name, text_output, visual_output, blended_output, output_dir)
    
    print(f"\n✅ PDF VISUAL EXTRACTION PIPELINE COMPLETED for {pdf_name}!")
    print(f"All outputs saved in: {output_dir}")
    return True

def create_summary_report(pdf_name: str, text_file: str, visual_file: str, 
                         blended_file: str, output_dir: str) -> None:
    """
    Create a summary report of the processing results
    
    Args:
        pdf_name: Name of the PDF
        text_file: Path to text extraction results
        visual_file: Path to visual detection results
        blended_file: Path to blended elements
        output_dir: Output directory
    """
    try:
        # Load results
        with open(text_file, 'r', encoding='utf-8') as f:
            text_data = json.load(f)
        
        with open(visual_file, 'r', encoding='utf-8') as f:
            visual_data = json.load(f)
        
        # Count blended elements
        blended_elements = []
        with open(blended_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        element = json.loads(line)
                        if 'summary' not in element:  # Skip summary line
                            blended_elements.append(element)
                    except json.JSONDecodeError:
                        continue
        
        # Create summary
        summary = {
            "pdf_name": pdf_name,
            "processing_timestamp": str(Path(text_file).stat().st_mtime),
            "text_extraction": {
                "total_pages": text_data.get('total_pages', 0),
                "total_characters": text_data.get('total_char_count', 0),
                "total_words": text_data.get('total_word_count', 0),
                "has_metadata": bool(text_data.get('metadata', {}))
            },
            "visual_detection": {
                "total_pages_processed": visual_data.get('total_pages', 0),
                "total_elements_found": visual_data.get('total_elements', 0),
                "processing_errors": visual_data.get('errors', 0),
                "elements_by_type": {}
            },
            "blended_output": {
                "total_elements": len(blended_elements),
                "element_types": {}
            },
            "file_paths": {
                "text_extraction": text_file,
                "visual_detection": visual_file,
                "blended_elements": blended_file
            }
        }
        
        # Count visual elements by type
        for page_data in visual_data.get('pages', []):
            elements = page_data.get('detection_result', {}).get('elements', [])
            for element in elements:
                element_type = element.get('type', 'unknown')
                summary["visual_detection"]["elements_by_type"][element_type] = \
                    summary["visual_detection"]["elements_by_type"].get(element_type, 0) + 1
        
        # Count blended elements by type
        for element in blended_elements:
            element_type = element.get('type', 'unknown')
            summary["blended_output"]["element_types"][element_type] = \
                summary["blended_output"]["element_types"].get(element_type, 0) + 1
        
        # Save summary
        summary_file = os.path.join(output_dir, f"{pdf_name}_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Summary report saved to: {summary_file}")
        
        # Print summary to console
        print(f"\n📊 PROCESSING SUMMARY for {pdf_name}:")
        print(f"  Text: {summary['text_extraction']['total_pages']} pages, "
              f"{summary['text_extraction']['total_characters']} characters")
        print(f"  Visual: {summary['visual_detection']['total_elements_found']} elements found "
              f"({summary['visual_detection']['elements_by_type']})")
        print(f"  Blended: {summary['blended_output']['total_elements']} elements "
              f"({summary['blended_output']['element_types']})")
        
    except Exception as e:
        print(f"Error creating summary report: {e}")

def get_all_pdfs(data_dir: str) -> list:
    """
    Get all PDF files from data directory
    
    Args:
        data_dir: Directory containing PDF files
        
    Returns:
        List of PDF file paths
    """
    pdf_pattern = os.path.join(data_dir, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    return sorted(pdf_files)

def main():
    parser = argparse.ArgumentParser(description="PDF Visual Extraction Pipeline")
    parser.add_argument("--pdf_path", type=str, help="Specific PDF file to process")
    parser.add_argument("--data_dir", type=str, default="data", help="Directory containing PDF files")
    parser.add_argument("--output_dir", type=str, default="pdf_visual_output", help="Output directory for all results")
    parser.add_argument("--vlm_model", type=str, default="mistralai/Pixtral-12B-2409", help="VLM model for table/figure detection")
    parser.add_argument("--llm_model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2", help="LLM model for text blending")
    parser.add_argument("--max_pdfs", type=int, help="Maximum number of PDFs to process")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.pdf_path:
        # Process specific PDF
        if not os.path.exists(args.pdf_path):
            print(f"Error: PDF file not found: {args.pdf_path}")
            return
        
        success = process_single_pdf(
            args.pdf_path, args.output_dir, args.vlm_model, args.llm_model
        )
        
        if success:
            print(f"\n🎉 SUCCESS: Pipeline completed for {args.pdf_path}")
        else:
            print(f"\n💥 FAILED: Pipeline failed for {args.pdf_path}")
    else:
        # Process all PDFs
        pdf_files = get_all_pdfs(args.data_dir)
        
        if not pdf_files:
            print(f"No PDF files found in {args.data_dir}")
            return
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        if args.max_pdfs:
            pdf_files = pdf_files[:args.max_pdfs]
            print(f"Limiting to first {len(pdf_files)} PDFs")
        
        successful = 0
        failed = 0
        
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing: {os.path.basename(pdf_path)}")
            
            success = process_single_pdf(
                pdf_path, args.output_dir, args.vlm_model, args.llm_model
            )
            
            if success:
                successful += 1
            else:
                failed += 1
        
        print(f"\n{'='*80}")
        print(f"PDF VISUAL EXTRACTION PIPELINE BATCH PROCESSING FINISHED!")
        print(f"Successfully processed: {successful} PDFs")
        print(f"Failed: {failed} PDFs")
        print(f"Total: {len(pdf_files)} PDFs")
        print(f"Results saved in: {args.output_dir}")
        print(f"{'='*80}")

if __name__ == "__main__":
    main()
