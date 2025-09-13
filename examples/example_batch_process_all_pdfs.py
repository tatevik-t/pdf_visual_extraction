#!/usr/bin/env python3
"""
Batch Process All PDFs with CSV Export
Processes all PDF files in the data/ directory with the enhanced PDF visual extraction pipeline
including CSV export functionality.
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Thread-safe print function
print_lock = threading.Lock()

def thread_safe_print(*args, **kwargs):
    """Thread-safe print function"""
    with print_lock:
        print(*args, **kwargs)

def get_pdf_files(data_dir: str) -> list:
    """Get all PDF files from the data directory"""
    pdf_files = []
    for file in os.listdir(data_dir):
        if file.endswith('.pdf'):
            pdf_files.append(os.path.join(data_dir, file))
    return sorted(pdf_files)

def run_pdf_processing(pdf_path: str, output_dir: str, max_pages: int = None, 
                      export_md: bool = True, export_csv: bool = True, 
                      max_workers: int = 3) -> dict:
    """Run PDF visual extraction pipeline for a single PDF"""
    
    pdf_name = Path(pdf_path).stem
    start_time = time.time()
    
    thread_safe_print(f"\n{'='*80}")
    thread_safe_print(f"PROCESSING: {pdf_name}")
    thread_safe_print(f"File: {pdf_path}")
    thread_safe_print(f"{'='*80}")
    
    try:
        # Run the PDF visual extraction pipeline
        cmd = [
            sys.executable, 
            "pdf_visual_extraction/pdf_visual_extract.py",
            "--pdf_path", pdf_path,
            "--output_dir", output_dir,
            "--max_workers", str(max_workers)
        ]
        
        # Only add max_pages if specified
        if max_pages is not None:
            cmd.extend(["--max_pages", str(max_pages)])
        
        if export_md:
            cmd.append("--export_md")
        if export_csv:
            cmd.append("--export_csv")
        
        # Add force flag to reprocess
        cmd.append("--force")
        
        thread_safe_print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 60 min timeout
        
        processing_time = time.time() - start_time
        
        if result.returncode == 0:
            thread_safe_print(f"✅ SUCCESS: {pdf_name} processed in {processing_time:.1f}s")
            
            # Count results
            pdf_output_dir = os.path.join(output_dir, pdf_name)
            results = count_processing_results(pdf_output_dir, pdf_name)
            results.update({
                'status': 'success',
                'processing_time': processing_time,
                'error': None
            })
            
            return results
        else:
            thread_safe_print(f"❌ FAILED: {pdf_name}")
            thread_safe_print(f"Error: {result.stderr}")
            
            return {
                'pdf_name': pdf_name,
                'pdf_path': pdf_path,
                'status': 'failed',
                'processing_time': processing_time,
                'error': result.stderr,
                'total_pages': 0,
                'total_tables': 0,
                'csv_files': 0
            }
            
    except subprocess.TimeoutExpired:
        thread_safe_print(f"⏰ TIMEOUT: {pdf_name} (60 minutes)")
        return {
            'pdf_name': pdf_name,
            'pdf_path': pdf_path,
            'status': 'timeout',
            'processing_time': 3600,
            'error': 'Processing timeout (60 minutes)',
            'total_pages': 0,
            'total_tables': 0,
            'csv_files': 0
        }
    except Exception as e:
        thread_safe_print(f"💥 EXCEPTION: {pdf_name} - {str(e)}")
        return {
            'pdf_name': pdf_name,
            'pdf_path': pdf_path,
            'status': 'exception',
            'processing_time': time.time() - start_time,
            'error': str(e),
            'total_pages': 0,
            'total_tables': 0,
            'csv_files': 0
        }

def count_processing_results(pdf_output_dir: str, pdf_name: str) -> dict:
    """Count the results from processing a PDF"""
    results = {
        'pdf_name': pdf_name,
        'total_pages': 0,
        'total_tables': 0,
        'csv_files': 0,
        'markdown_file': False
    }
    
    try:
        # Count pages from images directory
        images_dir = os.path.join(pdf_output_dir, 'images')
        if os.path.exists(images_dir):
            image_files = [f for f in os.listdir(images_dir) if f.endswith('.png')]
            results['total_pages'] = len(image_files)
        
        # Count tables from final JSON
        final_json = os.path.join(pdf_output_dir, 'text_extraction', f"{pdf_name}_with_tables.json")
        if os.path.exists(final_json):
            with open(final_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_tables = 0
            for page in data.get('pages', []):
                total_tables += len(page.get('tables', []))
            results['total_tables'] = total_tables
        
        # Count CSV files
        csv_dir = os.path.join(pdf_output_dir, 'exports', 'csv_exports')
        if os.path.exists(csv_dir):
            csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            results['csv_files'] = len(csv_files)
        
        # Check for markdown file
        markdown_file = os.path.join(pdf_output_dir, 'exports', f"{pdf_name}_report.md")
        results['markdown_file'] = os.path.exists(markdown_file)
        
    except Exception as e:
        print(f"Warning: Could not count results for {pdf_name}: {e}")
    
    return results

def generate_batch_summary(results: list, output_dir: str) -> None:
    """Generate a comprehensive summary of the batch processing"""
    
    summary_file = os.path.join(output_dir, "batch_processing_summary.md")
    
    # Calculate statistics
    total_files = len(results)
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'failed'])
    timeouts = len([r for r in results if r['status'] == 'timeout'])
    exceptions = len([r for r in results if r['status'] == 'exception'])
    
    total_pages = sum(r.get('total_pages', 0) for r in results)
    total_tables = sum(r.get('total_tables', 0) for r in results)
    total_csv_files = sum(r.get('csv_files', 0) for r in results)
    total_processing_time = sum(r.get('processing_time', 0) for r in results)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# Batch PDF Processing Summary\n\n")
        f.write(f"**Processing Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Files Processed**: {total_files}\n")
        f.write(f"**Output Directory**: {output_dir}\n\n")
        
        f.write("## Processing Results\n\n")
        f.write(f"- ✅ **Successful**: {successful} files\n")
        f.write(f"- ❌ **Failed**: {failed} files\n")
        f.write(f"- ⏰ **Timeouts**: {timeouts} files\n")
        f.write(f"- 💥 **Exceptions**: {exceptions} files\n")
        f.write(f"- 📊 **Success Rate**: {(successful/total_files*100):.1f}%\n\n")
        
        f.write("## Content Statistics\n\n")
        f.write(f"- 📄 **Total Pages Processed**: {total_pages}\n")
        f.write(f"- 📊 **Total Tables Extracted**: {total_tables}\n")
        f.write(f"- 📈 **Total CSV Files Generated**: {total_csv_files}\n")
        f.write(f"- ⏱️ **Total Processing Time**: {total_processing_time/60:.1f} minutes\n")
        f.write(f"- ⚡ **Average Time per File**: {total_processing_time/total_files:.1f} seconds\n\n")
        
        f.write("## Detailed Results\n\n")
        f.write("| File | Status | Pages | Tables | CSV Files | Time (s) | Error |\n")
        f.write("|------|--------|-------|--------|-----------|----------|-------|\n")
        
        for result in results:
            status_emoji = {
                'success': '✅',
                'failed': '❌',
                'timeout': '⏰',
                'exception': '💥'
            }.get(result['status'], '❓')
            
            error_msg = result.get('error', '')[:50] + '...' if result.get('error') else ''
            
            f.write(f"| {result['pdf_name']} | {status_emoji} {result['status']} | "
                   f"{result.get('total_pages', 0)} | {result.get('total_tables', 0)} | "
                   f"{result.get('csv_files', 0)} | {result.get('processing_time', 0):.1f} | "
                   f"{error_msg} |\n")
        
        f.write("\n## Files with Most Tables\n\n")
        sorted_by_tables = sorted([r for r in results if r['status'] == 'success'], 
                                key=lambda x: x.get('total_tables', 0), reverse=True)
        
        for i, result in enumerate(sorted_by_tables[:10]):
            f.write(f"{i+1}. **{result['pdf_name']}**: {result.get('total_tables', 0)} tables\n")
        
        f.write("\n## Files with Most CSV Files\n\n")
        sorted_by_csv = sorted([r for r in results if r['status'] == 'success'], 
                             key=lambda x: x.get('csv_files', 0), reverse=True)
        
        for i, result in enumerate(sorted_by_csv[:10]):
            f.write(f"{i+1}. **{result['pdf_name']}**: {result.get('csv_files', 0)} CSV files\n")
    
    print(f"\n📋 Batch processing summary saved to: {summary_file}")

def main():
    parser = argparse.ArgumentParser(description='Batch process all PDFs with CSV export')
    parser.add_argument('--data_dir', default='data', help='Directory containing PDF files')
    parser.add_argument('--output_dir', default='batch_output', help='Output directory for all results')
    parser.add_argument('--max_pages', type=int, default=None, help='Maximum pages to process per PDF (default: all pages)')
    parser.add_argument('--max_workers', type=int, default=3, help='Maximum concurrent workers for VLM processing')
    parser.add_argument('--parallel_jobs', type=int, default=2, help='Number of PDFs to process in parallel')
    parser.add_argument('--export_md', action='store_true', default=True, help='Export to Markdown format')
    parser.add_argument('--export_csv', action='store_true', default=True, help='Export tables to CSV format')
    parser.add_argument('--skip_existing', action='store_true', help='Skip PDFs that already have output directories')
    
    args = parser.parse_args()
    
    # Check if data directory exists
    if not os.path.exists(args.data_dir):
        print(f"❌ Error: Data directory '{args.data_dir}' not found")
        sys.exit(1)
    
    # Get all PDF files
    pdf_files = get_pdf_files(args.data_dir)
    
    if not pdf_files:
        print(f"❌ No PDF files found in '{args.data_dir}'")
        sys.exit(1)
    
    print(f"🚀 Starting batch processing of {len(pdf_files)} PDF files")
    print(f"📁 Data directory: {args.data_dir}")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"📊 Max pages per PDF: {args.max_pages or 'All pages'}")
    print(f"👥 Max workers per PDF: {args.max_workers}")
    print(f"🔄 Parallel PDF jobs: {args.parallel_jobs}")
    print(f"📝 Export Markdown: {args.export_md}")
    print(f"📈 Export CSV: {args.export_csv}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Filter out existing files if requested
    files_to_process = []
    for pdf_path in pdf_files:
        pdf_name = Path(pdf_path).stem
        
        if args.skip_existing:
            pdf_output_dir = os.path.join(args.output_dir, pdf_name)
            if os.path.exists(pdf_output_dir):
                print(f"⏭️  Skipping {pdf_name} (output already exists)")
                continue
        
        files_to_process.append(pdf_path)
    
    print(f"📄 Processing {len(files_to_process)} PDF files in parallel...")
    
    # Process PDFs in parallel
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=args.parallel_jobs) as executor:
        # Submit all jobs
        future_to_pdf = {}
        for pdf_path in files_to_process:
            future = executor.submit(
                run_pdf_processing,
                pdf_path,
                args.output_dir,
                args.max_pages,
                args.export_md,
                args.export_csv,
                args.max_workers
            )
            future_to_pdf[future] = pdf_path
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_pdf):
            pdf_path = future_to_pdf[future]
            pdf_name = Path(pdf_path).stem
            completed += 1
            
            try:
                result = future.result()
                results.append(result)
                thread_safe_print(f"📊 Completed {completed}/{len(files_to_process)}: {pdf_name}")
            except Exception as e:
                thread_safe_print(f"💥 Error processing {pdf_name}: {e}")
                results.append({
                    'pdf_name': pdf_name,
                    'pdf_path': pdf_path,
                    'status': 'exception',
                    'processing_time': 0,
                    'error': str(e),
                    'total_pages': 0,
                    'total_tables': 0,
                    'csv_files': 0
                })
    
    # Generate summary
    total_time = time.time() - start_time
    print(f"\n🎉 Batch processing completed in {total_time/60:.1f} minutes!")
    
    generate_batch_summary(results, args.output_dir)
    
    # Print quick summary
    successful = len([r for r in results if r['status'] == 'success'])
    total_tables = sum(r.get('total_tables', 0) for r in results)
    total_csv_files = sum(r.get('csv_files', 0) for r in results)
    
    print(f"\n📊 Quick Summary:")
    print(f"   ✅ Successful: {successful}/{len(results)} files")
    print(f"   📊 Total tables extracted: {total_tables}")
    print(f"   📈 Total CSV files generated: {total_csv_files}")
    print(f"   📁 All results saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
