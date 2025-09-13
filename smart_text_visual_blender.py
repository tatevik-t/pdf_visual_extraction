#!/usr/bin/env python3
"""
Smart Text and Visual Blending Module
Intelligently blends text and visual elements with semantic understanding
"""

import json
import argparse
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

def extract_structured_data_from_visual(visual_element: Dict[str, Any]) -> str:
    """
    Extract the structured data from visual elements (tables/figures)
    
    Args:
        visual_element: Visual element from VLM detection
        
    Returns:
        Clean structured data string
    """
    content = visual_element.get('content', {})
    structured_data = content.get('structured_data', '')
    
    if structured_data:
        return structured_data
    
    # Fallback to raw text if structured_data not available
    return content.get('raw_text', '')

def find_table_context_in_text(text: str, table_description: str) -> str:
    """
    Find the most relevant text context for a table
    
    Args:
        text: Full page text
        table_description: Description of the table
        
    Returns:
        Relevant context text
    """
    # Look for section headers or introductory text before tables
    lines = text.split('\n')
    context_lines = []
    
    # Find lines that might be context for tables
    table_keywords = ['table', 'financial', 'revenue', 'income', 'balance', 'cash flow', 'segment']
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in table_keywords):
            # Take a few lines before and after for context
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            context_lines.extend(lines[start:end])
    
    return '\n'.join(context_lines[:5])  # Limit context length

def create_semantic_blended_elements(text_data: Dict[str, Any], visual_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create semantically blended elements with intelligent text-visual integration
    
    Args:
        text_data: Text extraction results
        visual_data: Visual element detection results
        
    Returns:
        List of intelligently blended elements
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
    
    # Process each page with intelligent blending
    for page_data in text_pages:
        page_num = page_data.get('page_number', 0)
        page_text = page_data.get('text', '')
        
        # Get visual elements for this page
        page_visual_elements = visual_elements_by_page.get(page_num, [])
        
        if not page_visual_elements:
            # No visual elements, just add text as paragraphs
            if page_text.strip():
                paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
                for i, paragraph in enumerate(paragraphs):
                    if paragraph:
                        blended_elements.append({
                            "type": "text",
                            "page": page_num,
                            "content": paragraph,
                            "position": f"paragraph_{i+1}",
                            "context": "text_only"
                        })
        else:
            # We have visual elements, need intelligent blending
            blended_elements.extend(create_intelligent_page_blend(
                page_num, page_text, page_visual_elements
            ))
    
    return blended_elements

def create_intelligent_page_blend(page_num: int, page_text: str, visual_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Intelligently blend text and visual elements for a single page
    
    Args:
        page_num: Page number
        page_text: Full page text
        visual_elements: List of visual elements on this page
        
    Returns:
        List of blended elements for this page
    """
    blended_elements = []
    
    # Split text into logical sections
    text_sections = split_text_into_sections(page_text)
    
    # Process each visual element with its context
    for i, visual_element in enumerate(visual_elements):
        element_type = visual_element.get('type', 'unknown')
        confidence = visual_element.get('confidence', 0.0)
        
        # Only process high-confidence elements
        if confidence < 0.3:
            continue
            
        # Find relevant text context for this visual element
        context_text = find_table_context_in_text(page_text, visual_element.get('description', ''))
        
        # Extract structured data
        structured_data = extract_structured_data_from_visual(visual_element)
        
        if structured_data:
            # Create a comprehensive element that combines context and structured data
            blended_elements.append({
                "type": element_type,
                "page": page_num,
                "content": {
                    "context": context_text.strip(),
                    "structured_data": structured_data,
                    "description": visual_element.get('description', ''),
                    "confidence": confidence,
                    "bbox": visual_element.get('bbox', [])
                },
                "position": f"visual_{i+1}",
                "confidence": confidence,
                "context": "text_and_visual"
            })
    
    # Add remaining text sections that weren't used as context
    remaining_text = find_unused_text_sections(text_sections, visual_elements)
    for i, text_section in enumerate(remaining_text):
        if text_section.strip():
            blended_elements.append({
                "type": "text",
                "page": page_num,
                "content": text_section,
                "position": f"text_{i+1}",
                "context": "text_only"
            })
    
    return blended_elements

def split_text_into_sections(text: str) -> List[str]:
    """
    Split text into logical sections for better blending
    
    Args:
        text: Full page text
        
    Returns:
        List of text sections
    """
    # Split by double newlines first
    sections = [s.strip() for s in text.split('\n\n') if s.strip()]
    
    # Further split long sections
    refined_sections = []
    for section in sections:
        if len(section) > 500:  # Long section, try to split further
            # Split by single newlines for long sections
            sub_sections = [s.strip() for s in section.split('\n') if s.strip()]
            refined_sections.extend(sub_sections)
        else:
            refined_sections.append(section)
    
    return refined_sections

def find_unused_text_sections(text_sections: List[str], visual_elements: List[Dict[str, Any]]) -> List[str]:
    """
    Find text sections that weren't used as context for visual elements
    
    Args:
        text_sections: List of text sections
        visual_elements: List of visual elements
        
    Returns:
        List of unused text sections
    """
    # Simple heuristic: if text section is very short or contains table-like content,
    # it might have been used as context
    unused_sections = []
    
    for section in text_sections:
        # Skip very short sections (likely headers or captions)
        if len(section) < 50:
            continue
            
        # Skip sections that look like table headers or captions
        if any(keyword in section.lower() for keyword in ['quarter ended', 'year ended', 'in millions', 'unaudited']):
            continue
            
        unused_sections.append(section)
    
    return unused_sections

def save_smart_blended_elements(blended_elements: List[Dict[str, Any]], output_file: str, pdf_name: str) -> None:
    """
    Save smart blended elements to JSONL file
    
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
        "context_types": {},
        "pages_covered": set()
    }
    
    # Count element types and pages
    for element in blended_elements:
        element_type = element.get('type', 'unknown')
        page = element.get('page', 0)
        context = element.get('context', 'unknown')
        
        summary["element_types"][element_type] = summary["element_types"].get(element_type, 0) + 1
        summary["context_types"][context] = summary["context_types"].get(context, 0) + 1
        summary["pages_covered"].add(page)
    
    summary["pages_covered"] = sorted(list(summary["pages_covered"]))
    
    # Save JSONL file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write summary as first line
        f.write(json.dumps({"summary": summary}) + '\n')
        
        # Write each element as a separate line
        for element in blended_elements:
            f.write(json.dumps(element, ensure_ascii=False) + '\n')
    
    print(f"Smart blended elements saved to: {output_file}")
    print(f"Total elements: {len(blended_elements)}")
    print(f"Element types: {summary['element_types']}")
    print(f"Context types: {summary['context_types']}")
    print(f"Pages covered: {summary['pages_covered']}")

def main():
    parser = argparse.ArgumentParser(description="Smart text and visual element blending")
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
        output_file = f"{pdf_name}_smart_blended_elements.jsonl"
    
    # Create smart blended elements
    print("Creating smart blended elements...")
    blended_elements = create_semantic_blended_elements(text_data, visual_data)
    
    if blended_elements:
        # Save results
        save_smart_blended_elements(blended_elements, output_file, text_data.get('pdf_name', 'unknown'))
        print("Smart blending completed successfully!")
    else:
        print("No elements to blend")

if __name__ == "__main__":
    main()
