#!/usr/bin/env python3
"""
Text-Preserving Blender: Keeps original text and adds table information as separate elements
"""

import json
import argparse
import os
from typing import Dict, List, Any
from datetime import datetime

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_text_elements(text_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create text elements from extracted text, preserving original content"""
    elements = []
    
    for page in text_data.get('pages', []):
        page_number = page.get('page_number', 0)
        text_content = page.get('text', '').strip()
        
        if not text_content:
            continue
            
        # Split text into paragraphs for better chunking
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            element = {
                "id": f"text_page_{page_number}_para_{i+1}",
                "type": "text",
                "page": page_number + 1,  # Convert to 1-based page numbering
                "content": {
                    "text": paragraph,
                    "structured_data": None,
                    "context": f"Original text content from page {page_number + 1}",
                    "summary": paragraph[:200] + "..." if len(paragraph) > 200 else paragraph,
                    "key_insights": []
                },
                "metadata": {
                    "confidence": 1.0,
                    "source": "text",
                    "importance": "medium",
                    "category": "narrative"
                }
            }
            elements.append(element)
    
    return elements

def create_table_elements(visual_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create table elements from visual detection results"""
    elements = []
    
    for page in visual_data.get('pages', []):
        page_number = page.get('page_number', 0)
        detection_result = page.get('detection_result', {})
        elements_list = detection_result.get('elements', [])
        
        for i, element in enumerate(elements_list):
            if element.get('type') == 'table':
                table_element = {
                    "id": f"table_page_{page_number}_table_{i+1}",
                    "type": "table",
                    "page": page_number + 1,  # Convert to 1-based page numbering
                    "content": {
                        "text": element.get('description', ''),
                        "structured_data": element.get('content', {}).get('structured_data', ''),
                        "raw_text": element.get('content', {}).get('raw_text', ''),
                        "context": f"Table detected on page {page_number + 1}",
                        "summary": element.get('content', {}).get('summary', ''),
                        "key_insights": []
                    },
                    "metadata": {
                        "confidence": element.get('confidence', 0.9),
                        "source": "visual",
                        "importance": "high",
                        "category": "financial_metrics"
                    }
                }
                elements.append(table_element)
    
    return elements

def create_figure_elements(visual_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create figure elements from visual detection results"""
    elements = []
    
    for page in visual_data.get('pages', []):
        page_number = page.get('page_number', 0)
        detection_result = page.get('detection_result', {})
        elements_list = detection_result.get('elements', [])
        
        for i, element in enumerate(elements_list):
            if element.get('type') == 'figure':
                figure_element = {
                    "id": f"figure_page_{page_number}_fig_{i+1}",
                    "type": "figure",
                    "page": page_number + 1,  # Convert to 1-based page numbering
                    "content": {
                        "text": element.get('description', ''),
                        "structured_data": element.get('content', {}).get('structured_data', ''),
                        "raw_text": element.get('content', {}).get('raw_text', ''),
                        "context": f"Figure detected on page {page_number + 1}",
                        "summary": element.get('content', {}).get('summary', ''),
                        "key_insights": []
                    },
                    "metadata": {
                        "confidence": element.get('confidence', 0.9),
                        "source": "visual",
                        "importance": "high",
                        "category": "visual_data"
                    }
                }
                elements.append(figure_element)
    
    return elements

def blend_elements_preserving_text(text_file: str, visual_file: str, output_file: str) -> Dict[str, Any]:
    """Blend text and visual elements while preserving original text content"""
    
    # Load data
    text_data = load_json_file(text_file)
    visual_data = load_json_file(visual_file)
    
    # Create elements
    text_elements = create_text_elements(text_data)
    table_elements = create_table_elements(visual_data)
    figure_elements = create_figure_elements(visual_data)
    
    # Combine all elements
    all_elements = text_elements + table_elements + figure_elements
    
    # Create summary
    element_types = {}
    categories = {}
    importance_levels = {}
    
    for element in all_elements:
        element_type = element.get('type', 'unknown')
        category = element.get('metadata', {}).get('category', 'unknown')
        importance = element.get('metadata', {}).get('importance', 'unknown')
        
        element_types[element_type] = element_types.get(element_type, 0) + 1
        categories[category] = categories.get(category, 0) + 1
        importance_levels[importance] = importance_levels.get(importance, 0) + 1
    
    # Create document summary
    document_summary = {
        "total_elements": len(all_elements),
        "key_metrics": [],
        "main_topics": [],
        "document_type": "earnings_report"
    }
    
    # Extract key metrics from tables
    for element in table_elements:
        if 'revenue' in element.get('content', {}).get('text', '').lower():
            document_summary["key_metrics"].append("Revenue data available")
        if 'income' in element.get('content', {}).get('text', '').lower():
            document_summary["key_metrics"].append("Income data available")
    
    # Create final output
    output_data = {
        "summary": {
            "pdf_name": text_data.get('pdf_name', 'unknown'),
            "total_elements": len(all_elements),
            "document_summary": document_summary,
            "element_types": element_types,
            "categories": categories,
            "importance_levels": importance_levels
        }
    }
    
    # Write elements to JSONL file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write summary first
        f.write(json.dumps(output_data["summary"]) + '\n')
        
        # Write each element
        for element in all_elements:
            f.write(json.dumps(element) + '\n')
    
    return {
        "total_elements": len(all_elements),
        "element_types": element_types,
        "categories": categories,
        "importance_levels": importance_levels
    }

def main():
    parser = argparse.ArgumentParser(description='Text-Preserving Blender: Keep text and add table info')
    parser.add_argument('--text_file', required=True, help='Path to text extraction JSON file')
    parser.add_argument('--visual_file', required=True, help='Path to visual detection JSON file')
    parser.add_argument('--output_file', required=True, help='Path to output JSONL file')
    
    args = parser.parse_args()
    
    print("Creating text-preserving blended elements...")
    
    try:
        result = blend_elements_preserving_text(args.text_file, args.visual_file, args.output_file)
        
        print(f"Text-preserving blended elements saved to: {args.output_file}")
        print(f"Total elements: {result['total_elements']}")
        print(f"Element types: {result['element_types']}")
        print(f"Categories: {result['categories']}")
        print(f"Importance levels: {result['importance_levels']}")
        print("Text-preserving blending completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
