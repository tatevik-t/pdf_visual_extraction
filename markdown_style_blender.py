#!/usr/bin/env python3
"""
Markdown Style Blending Module
Creates output in the style of combined_descriptions files
"""

import json
import argparse
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

def extract_clean_structured_data(visual_element: Dict[str, Any]) -> str:
    """
    Extract clean structured data from visual elements
    
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

def create_markdown_style_blend(text_data: Dict[str, Any], visual_data: Dict[str, Any]) -> str:
    """
    Create a markdown-style blended output similar to combined_descriptions files
    
    Args:
        text_data: Text extraction results
        visual_data: Visual element detection results
        
    Returns:
        Markdown-formatted blended content
    """
    pdf_name = text_data.get('pdf_name', 'unknown')
    
    # Start with header
    markdown_content = f"# {pdf_name.replace('_', ' ').title()} - Structured Data Extraction\n\n"
    markdown_content += "This document contains structured data extracted from tables and figures in the PDF.\n\n"
    markdown_content += "---\n\n"
    
    # Get text pages and visual elements
    text_pages = text_data.get('pages', [])
    visual_pages = visual_data.get('pages', [])
    
    # Organize visual elements by page
    visual_elements_by_page = {}
    for page_data in visual_pages:
        page_num = page_data.get('page_number', 0)
        elements = page_data.get('detection_result', {}).get('elements', [])
        visual_elements_by_page[page_num] = elements
    
    # Process each page
    for page_data in text_pages:
        page_num = page_data.get('page_number', 0)
        page_text = page_data.get('text', '')
        
        # Add page header
        markdown_content += f"## Page {page_num + 1}\n\n"
        
        # Get visual elements for this page
        page_visual_elements = visual_elements_by_page.get(page_num, [])
        
        if page_visual_elements:
            # Process visual elements first (tables/figures)
            for i, visual_element in enumerate(page_visual_elements):
                element_type = visual_element.get('type', 'unknown')
                confidence = visual_element.get('confidence', 0.0)
                
                # Only process high-confidence elements
                if confidence < 0.3:
                    continue
                
                # Add element header
                element_title = visual_element.get('description', f'{element_type.title()} {i+1}')
                markdown_content += f"### {element_title}\n\n"
                
                # Add structured data
                structured_data = extract_clean_structured_data(visual_element)
                if structured_data:
                    markdown_content += structured_data + "\n\n"
                
                # Add summary if available
                summary = visual_element.get('content', {}).get('summary', '')
                if summary:
                    markdown_content += f"**Summary**: {summary}\n\n"
                
                markdown_content += "---\n\n"
        
        # Add relevant text content (excluding what was already used as context)
        if page_text.strip():
            # Extract key text sections that aren't just table headers
            text_sections = extract_relevant_text_sections(page_text, page_visual_elements)
            if text_sections:
                markdown_content += "### Text Content\n\n"
                for section in text_sections:
                    if section.strip():
                        markdown_content += section + "\n\n"
                markdown_content += "---\n\n"
    
    return markdown_content

def extract_relevant_text_sections(page_text: str, visual_elements: List[Dict[str, Any]]) -> List[str]:
    """
    Extract relevant text sections that aren't just table headers or captions
    
    Args:
        page_text: Full page text
        visual_elements: Visual elements on this page
        
    Returns:
        List of relevant text sections
    """
    # Split text into lines
    lines = page_text.split('\n')
    relevant_sections = []
    
    # Skip lines that are likely table headers or captions
    skip_patterns = [
        r'quarter ended',
        r'year ended',
        r'in millions',
        r'unaudited',
        r'^\s*\|\s*',  # Markdown table lines
        r'^\s*$',      # Empty lines
        r'^\s*\d+\s*$' # Just numbers
    ]
    
    current_section = []
    for line in lines:
        line = line.strip()
        if not line:
            if current_section:
                section_text = ' '.join(current_section)
                if len(section_text) > 50:  # Only keep substantial sections
                    relevant_sections.append(section_text)
                current_section = []
            continue
        
        # Check if line should be skipped
        should_skip = any(re.search(pattern, line.lower()) for pattern in skip_patterns)
        
        if not should_skip:
            current_section.append(line)
        else:
            # End current section if we hit a skip pattern
            if current_section:
                section_text = ' '.join(current_section)
                if len(section_text) > 50:
                    relevant_sections.append(section_text)
                current_section = []
    
    # Add final section if exists
    if current_section:
        section_text = ' '.join(current_section)
        if len(section_text) > 50:
            relevant_sections.append(section_text)
    
    return relevant_sections

def save_markdown_blend(markdown_content: str, output_file: str, pdf_name: str) -> None:
    """
    Save markdown blended content to file
    
    Args:
        markdown_content: Markdown formatted content
        output_file: Path to save the file
        pdf_name: Name of the PDF
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"Markdown blended content saved to: {output_file}")
    print(f"Content length: {len(markdown_content)} characters")

def main():
    parser = argparse.ArgumentParser(description="Markdown style text and visual element blending")
    parser.add_argument("--text_file", type=str, required=True, help="Path to text extraction JSON file")
    parser.add_argument("--visual_file", type=str, required=True, help="Path to visual detection JSON file")
    parser.add_argument("--output_file", type=str, help="Output markdown file path")
    
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
        output_file = f"{pdf_name}_markdown_blend.md"
    
    # Create markdown blend
    print("Creating markdown style blend...")
    markdown_content = create_markdown_style_blend(text_data, visual_data)
    
    if markdown_content:
        # Save results
        save_markdown_blend(markdown_content, output_file, text_data.get('pdf_name', 'unknown'))
        print("Markdown blending completed successfully!")
    else:
        print("No content to blend")

if __name__ == "__main__":
    main()
