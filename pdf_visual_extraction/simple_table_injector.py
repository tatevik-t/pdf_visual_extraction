#!/usr/bin/env python3
"""
Simple Table Injector: Add table data to text extraction JSON as "tables" field
"""

import json
import argparse
import os
from typing import Dict, List, Any

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_tables_from_visual(visual_data: Dict[str, Any]) -> Dict[int, List[Dict[str, Any]]]:
    """Extract tables from visual detection results, organized by page"""
    tables_by_page = {}
    
    for page in visual_data.get('pages', []):
        page_number = page.get('page_number', 0)
        detection_result = page.get('detection_result', {})
        elements = detection_result.get('elements', [])
        
        page_tables = []
        for element in elements:
            if element.get('type') == 'table':
                table_data = {
                    "description": element.get('description', ''),
                    "structured_data": element.get('content', {}).get('structured_data', ''),
                    "raw_text": element.get('content', {}).get('raw_text', ''),
                    "confidence": element.get('confidence', 0.9),
                    "bbox": element.get('bbox', [])
                }
                page_tables.append(table_data)
        
        if page_tables:
            tables_by_page[page_number] = page_tables
    
    return tables_by_page

def inject_tables_into_text(text_data: Dict[str, Any], tables_by_page: Dict[int, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Inject table data into text extraction JSON"""
    enhanced_data = text_data.copy()
    
    # Add tables to each page
    for page in enhanced_data.get('pages', []):
        page_number = page.get('page_number', 0)
        if page_number in tables_by_page:
            page['tables'] = tables_by_page[page_number]
        else:
            page['tables'] = []
    
    return enhanced_data

def main():
    parser = argparse.ArgumentParser(description='Inject table data into text extraction JSON')
    parser.add_argument('--text_file', required=True, help='Path to text extraction JSON file')
    parser.add_argument('--visual_file', required=True, help='Path to visual detection JSON file')
    parser.add_argument('--output_file', required=True, help='Path to output enhanced JSON file')
    
    args = parser.parse_args()
    
    print("Injecting table data into text extraction...")
    print(f"Text input: {args.text_file}")
    print(f"Visual input: {args.visual_file}")
    print(f"Output: {args.output_file}")
    
    try:
        # Load data
        text_data = load_json_file(args.text_file)
        visual_data = load_json_file(args.visual_file)
        
        # Extract tables from visual detection
        tables_by_page = extract_tables_from_visual(visual_data)
        
        # Inject tables into text data
        enhanced_data = inject_tables_into_text(text_data, tables_by_page)
        
        # Save enhanced data
        os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Table injection completed successfully!")
        
        # Show statistics
        total_tables = sum(len(tables) for tables in tables_by_page.values())
        pages_with_tables = len(tables_by_page)
        print(f"📊 Injected {total_tables} tables across {pages_with_tables} pages")
        print(f"💾 Saved to: {args.output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
