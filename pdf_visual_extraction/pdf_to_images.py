#!/usr/bin/env python3
"""
PDF to Images Conversion Module
Converts PDF pages to images using pdf2image
"""

import pdf2image
import argparse
import os
from pathlib import Path
from typing import List

def convert_pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 300, max_pages: int = None) -> List[str]:
    """
    Convert PDF pages to images
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save images
        dpi: DPI for image conversion
        max_pages: Maximum number of pages to convert (None for all pages)
        
    Returns:
        List of generated image file paths
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF to images without output_folder to avoid temp files
        print(f"Converting PDF to images with DPI: {dpi}")
        if max_pages:
            print(f"Limiting to first {max_pages} pages")
        
        images = pdf2image.convert_from_path(
            pdf_path,
            dpi=dpi,
            fmt='png',
            thread_count=4,
            first_page=1,
            last_page=max_pages
        )
        
        # Generate image file paths
        pdf_name = Path(pdf_path).stem
        image_paths = []
        
        for i, image in enumerate(images):
            image_filename = f"page_{i:03d}.png"
            image_path = os.path.join(output_dir, image_filename)
            image.save(image_path, "PNG")
            image_paths.append(image_path)
            print(f"Saved page {i+1}: {image_path}")
        
        print(f"Successfully converted {len(images)} pages to images")
        return image_paths
        
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Convert PDF pages to images")
    parser.add_argument("--pdf_path", type=str, required=True, help="Path to PDF file")
    parser.add_argument("--output_dir", type=str, help="Output directory for images (default: pdf_name_images)")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for image conversion (default: 300)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF file not found: {args.pdf_path}")
        return
    
    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        pdf_name = Path(args.pdf_path).stem
        output_dir = f"{pdf_name}_images"
    
    # Convert PDF to images
    image_paths = convert_pdf_to_images(args.pdf_path, output_dir, args.dpi)
    
    if image_paths:
        print(f"Conversion completed! Generated {len(image_paths)} images in: {output_dir}")
    else:
        print("Conversion failed!")

if __name__ == "__main__":
    main()
