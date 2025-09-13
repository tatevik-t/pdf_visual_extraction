#!/usr/bin/env python3
"""
Basic usage example for PDF Visual Extraction Library
"""

import os
import json
from pdf_visual_extraction import (
    extract_text_from_pdf,
    convert_pdf_to_images,
    process_images_openai,
    inject_tables_into_text,
    convert_json_to_markdown,
    convert_tables_to_csv
)

def main():
    """Basic usage example"""
    
    # Set your OpenAI API key
    os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    # Input PDF file
    pdf_path = "sample_document.pdf"
    output_dir = "output"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print("🚀 Starting PDF Visual Extraction...")
    
    # Step 1: Extract text from PDF
    print("📄 Extracting text...")
    text_file = os.path.join(output_dir, "text.json")
    extract_text_from_pdf(pdf_path, text_file)
    
    # Step 2: Convert PDF to images
    print("🖼️ Converting to images...")
    images_dir = os.path.join(output_dir, "images")
    convert_pdf_to_images(pdf_path, images_dir)
    
    # Step 3: Detect visual elements using OpenAI
    print("🔍 Detecting visual elements...")
    visual_file = os.path.join(output_dir, "visual.json")
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    process_images_openai(images_dir, pdf_name, visual_file, max_pages=5)
    
    # Step 4: Load and process data
    print("📊 Processing data...")
    
    # Load text data
    with open(text_file, 'r') as f:
        text_data = json.load(f)
    
    # Load visual data
    with open(visual_file, 'r') as f:
        visual_data = json.load(f)
    
    # Extract tables from visual data
    from pdf_visual_extraction import extract_tables_from_visual
    tables_by_page = extract_tables_from_visual(visual_data)
    
    # Inject tables into text data
    final_data = inject_tables_into_text(text_data, tables_by_page)
    
    # Save final result
    final_file = os.path.join(output_dir, "final_result.json")
    with open(final_file, 'w') as f:
        json.dump(final_data, f, indent=2)
    
    # Step 5: Convert tables to CSV
    print("📈 Converting tables to CSV...")
    csv_results = convert_tables_to_csv(final_data, output_dir, pdf_name)
    print(f"   Converted {csv_results['converted_tables']} out of {csv_results['total_tables']} tables")
    
    # Step 6: Convert to Markdown
    print("📝 Converting to Markdown...")
    markdown_file = os.path.join(output_dir, "report.md")
    markdown_content = convert_json_to_markdown(final_data)
    with open(markdown_file, 'w') as f:
        f.write(markdown_content)
    
    print("✅ Extraction completed!")
    print(f"📁 Results saved to: {output_dir}")
    print(f"📊 Final JSON: {final_file}")
    print(f"📝 Markdown: {markdown_file}")
    print(f"📈 CSV files: {os.path.join(output_dir, 'csv_exports')}")

if __name__ == "__main__":
    main()
