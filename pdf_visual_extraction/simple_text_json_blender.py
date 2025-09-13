#!/usr/bin/env python3
"""
Simple Text and JSON Blending Module
Creates a basic blended output without requiring complex LLM models
"""

import json
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any

def create_simple_blended_elements(text_data: Dict[str, Any], visual_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create simple blended elements without LLM processing
    
    Args:
        text_data: Text extraction results
        visual_data: Visual element detection results
        
    Returns:
        List of blended elements in document order
    """
    blended_elements = []
    
    # Get text pages
    text_pages = text_data.get('pages', [])
    
    # Get visual elements by page
    visual_pages = visual_data.get('pages', [])
    visual_elements_by_page = {}
    
    for page_data in visual_pages:
        page_num = page_data.get('page_number', 0)
        elements = page_data.get('detection_result', {}).get('elements', [])
        visual_elements_by_page[page_num] = elements
    
    # Process each page
    for page_data in text_pages:
        page_num = page_data.get('page_number', 0)
        page_text = page_data.get('text', '')
        
        # Add text element if there's content
        if page_text.strip():
            # Split text into paragraphs for better structure
            paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
            
            for i, paragraph in enumerate(paragraphs):
                if paragraph:
                    blended_elements.append({
                        "type": "text",
                        "page": page_num,
                        "content": paragraph,
                        "position": f"paragraph_{i+1}"
                    })
        
        # Add visual elements for this page
        page_visual_elements = visual_elements_by_page.get(page_num, [])
        for i, element in enumerate(page_visual_elements):
            element_type = element.get('type', 'unknown')
            confidence = element.get('confidence', 0.0)
            description = element.get('description', '')
            bbox = element.get('bbox', [])
            content = element.get('content', {})
            
            # Only include elements with reasonable confidence
            if confidence > 0.3:
                blended_elements.append({
                    "type": element_type,
                    "page": page_num,
                    "content": {
                        "type": element_type,
                        "bbox": bbox,
                        "confidence": confidence,
                        "description": description,
                        "structure": content.get('structure', ''),
                        "text_content": content.get('text_content', ''),
                        "purpose": content.get('purpose', ''),
                        "data_type": content.get('data_type', '')
                    },
                    "position": f"visual_{i+1}",
                    "confidence": confidence
                })
    
    return blended_elements

def save_blended_elements(blended_elements: List[Dict[str, Any]], output_file: str, pdf_name: str) -> None:
    """
    Save blended elements to JSONL file
    
    Args:
        blended_elements: List of blended elements
        output_file: Path to save the JSONL file
        pdf_name: Name of the PDF
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Create summary
    summary = {
        "pdf_name": pdf_name,
        "total_elements": len(blended_elements),
        "element_types": {},
        "pages_covered": set()
    }
    
    # Count element types and pages
    for element in blended_elements:
        element_type = element.get('type', 'unknown')
        page = element.get('page', 0)
        
        summary["element_types"][element_type] = summary["element_types"].get(element_type, 0) + 1
        summary["pages_covered"].add(page)
    
    summary["pages_covered"] = sorted(list(summary["pages_covered"]))
    
    # Save JSONL file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write summary as first line
        f.write(json.dumps({"summary": summary}) + '\n')
        
        # Write each element as a separate line
        for element in blended_elements:
            f.write(json.dumps(element, ensure_ascii=False) + '\n')
    
    print(f"Blended elements saved to: {output_file}")
    print(f"Total elements: {len(blended_elements)}")
    print(f"Element types: {summary['element_types']}")
    print(f"Pages covered: {summary['pages_covered']}")

def main():
    parser = argparse.ArgumentParser(description="Simple text and visual element blending")
    parser.add_argument("--text_file", type=str, required=True, help="Path to text extraction JSON file")
    parser.add_argument("--visual_file", type=str, required=True, help="Path to visual detection JSON file")
    parser.add_argument("--output_file", type=str, help="Output JSONL file path")
    
    args = parser.parse_args()
    
    # Load input files
    if not os.path.exists(args.text_file):
        print(f"Error: Text file not found: {args.text_file}")
        return
    
    if not os.path.exists(args.visual_file):
        print(f"Error: Visual file not found: {args.visual_file}")
        return
    
    with open(args.text_file, 'r', encoding='utf-8') as f:
        text_data = json.load(f)
    
    with open(args.visual_file, 'r', encoding='utf-8') as f:
        visual_data = json.load(f)
    
    # Determine output file
    if args.output_file:
        output_file = args.output_file
    else:
        pdf_name = text_data.get('pdf_name', 'unknown')
        output_file = f"{pdf_name}_blended_elements.jsonl"
    
    # Create blended elements
    print("Creating blended elements...")
    blended_elements = create_simple_blended_elements(text_data, visual_data)
    
    if blended_elements:
        # Save results
        save_blended_elements(blended_elements, output_file, text_data.get('pdf_name', 'unknown'))
        print("Blending completed successfully!")
    else:
        print("No elements to blend")

if __name__ == "__main__":
    main()
