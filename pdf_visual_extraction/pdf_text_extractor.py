#!/usr/bin/env python3
"""
PDF Text Extraction Module
Extracts textual information from PDF files using PyPDF2
"""

import PyPDF2
import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any

def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract text content from PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing extracted text and metadata
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            pages_text = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    pages_text.append({
                        'page_number': page_num + 1,
                        'text': page_text
                    })
                except Exception as e:
                    print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
                    pages_text.append({
                        'page_number': page_num + 1,
                        'text': '',
                        'error': str(e)
                    })
            
            # Combine all text
            full_text = '\n\n'.join([page['text'] for page in pages_text])
            
            return {
                'pdf_path': pdf_path,
                'pdf_name': Path(pdf_path).stem,
                'total_pages': len(pdf_reader.pages),
                'pages': pages_text,
                'full_text': full_text
            }
            
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return {
            'pdf_path': pdf_path,
            'pdf_name': Path(pdf_path).stem,
            'error': str(e),
            'total_pages': 0,
            'pages': [],
            'full_text': ''
        }

def save_text_extraction(extraction_result: Dict[str, Any], output_path: str) -> None:
    """
    Save text extraction result to JSON file
    
    Args:
        extraction_result: Result from extract_text_from_pdf
        output_path: Path to save the JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(extraction_result, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF files")
    parser.add_argument("--pdf_path", type=str, required=True, help="Path to PDF file")
    parser.add_argument("--output_path", type=str, help="Output JSON file path (default: pdf_name_text.json)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF file not found: {args.pdf_path}")
        return
    
    # Extract text
    print(f"Extracting text from: {args.pdf_path}")
    result = extract_text_from_pdf(args.pdf_path)
    
    # Determine output path
    if args.output_path:
        output_path = args.output_path
    else:
        pdf_name = Path(args.pdf_path).stem
        output_path = f"{pdf_name}_text.json"
    
    # Save result
    save_text_extraction(result, output_path)
    
    print(f"Text extraction completed!")
    print(f"Total pages: {result['total_pages']}")
    print(f"Result saved to: {output_path}")

if __name__ == "__main__":
    main()
