#!/usr/bin/env python3
"""
Batch Processing Example for PDF Visual Extraction Library
Shows how to process multiple PDFs with CSV export in parallel
"""

import os
import sys
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.append('.')

from pdf_visual_extraction import run_pdf_visual_extraction

def process_single_pdf(pdf_path: str, output_dir: str, max_pages: int = None) -> dict:
    """Process a single PDF and return results"""
    
    pdf_name = Path(pdf_path).stem
    start_time = time.time()
    
    print(f"📄 Processing: {pdf_name}")
    
    try:
        success = run_pdf_visual_extraction(
            pdf_path=pdf_path,
            output_dir=output_dir,
            max_pages=max_pages,
            export_md=True,
            export_csv=True,  # Enable CSV export
            force=False,
            max_workers=3
        )
        
        processing_time = time.time() - start_time
        
        if success:
            print(f"✅ {pdf_name} completed in {processing_time:.1f}s")
            return {
                'pdf_name': pdf_name,
                'status': 'success',
                'processing_time': processing_time,
                'error': None
            }
        else:
            print(f"❌ {pdf_name} failed")
            return {
                'pdf_name': pdf_name,
                'status': 'failed',
                'processing_time': processing_time,
                'error': 'Processing failed'
            }
            
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"💥 {pdf_name} error: {str(e)}")
        return {
            'pdf_name': pdf_name,
            'status': 'error',
            'processing_time': processing_time,
            'error': str(e)
        }

def main():
    """Batch processing example"""
    
    # Set your OpenAI API key
    os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    # Configuration
    data_dir = "data"  # Directory containing PDF files
    output_dir = "batch_output"
    max_pages = 5  # Limit pages for demo (set to None for all pages)
    
    print("🚀 Batch PDF Processing with CSV Export")
    print("=" * 50)
    
    # Get all PDF files
    pdf_files = []
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(data_dir, file))
    
    if not pdf_files:
        print(f"❌ No PDF files found in '{data_dir}'")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files")
    print(f"📊 Max pages per PDF: {max_pages or 'All pages'}")
    print(f"📈 CSV export: Enabled")
    print(f"📝 Markdown export: Enabled")
    print()
    
    # Process each PDF
    results = []
    start_time = time.time()
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] ", end="")
        result = process_single_pdf(pdf_path, output_dir, max_pages)
        results.append(result)
        
        # Small delay between files to avoid overwhelming the API
        if i < len(pdf_files):
            time.sleep(2)
    
    # Summary
    total_time = time.time() - start_time
    successful = len([r for r in results if r['status'] == 'success'])
    
    print("\n" + "=" * 50)
    print("📊 BATCH PROCESSING SUMMARY")
    print("=" * 50)
    print(f"✅ Successful: {successful}/{len(results)} files")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"📁 Output directory: {output_dir}")
    
    # Show results by status
    print(f"\n📋 Results by Status:")
    for status in ['success', 'failed', 'error']:
        count = len([r for r in results if r['status'] == status])
        if count > 0:
            print(f"   {status.title()}: {count} files")
    
    # Show successful files
    if successful > 0:
        print(f"\n✅ Successfully processed files:")
        for result in results:
            if result['status'] == 'success':
                print(f"   - {result['pdf_name']} ({result['processing_time']:.1f}s)")
    
    # Show failed files
    failed_files = [r for r in results if r['status'] != 'success']
    if failed_files:
        print(f"\n❌ Failed files:")
        for result in failed_files:
            print(f"   - {result['pdf_name']}: {result['error']}")
    
    print(f"\n🎉 Batch processing completed!")
    print(f"📁 Check '{output_dir}' for all results including CSV files")

if __name__ == "__main__":
    main()
