#!/usr/bin/env python3
"""
JSONL to Markdown Converter: Convert blended JSONL output to readable markdown
"""

import json
import argparse
import os
from typing import Dict, List, Any
from datetime import datetime

def load_jsonl_file(file_path: str) -> List[Dict[str, Any]]:
    """Load JSONL data from file"""
    elements = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                elements.append(json.loads(line))
    return elements

def format_table_data(structured_data: str) -> str:
    """Format structured table data as markdown table"""
    if not structured_data:
        return ""
    
    lines = structured_data.split('\n')
    markdown_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Handle headers
        if line.startswith('### Table:'):
            title = line.replace('### Table:', '').strip()
            markdown_lines.append(f"\n## {title}\n")
            continue
            
        # Handle bullet points with data
        if line.startswith('- **') and '**:' in line:
            # Extract key and value
            key = line.split('**:')[0].replace('- **', '').strip()
            value = line.split('**:')[1].strip()
            
            if value:
                markdown_lines.append(f"**{key}**: {value}")
            else:
                markdown_lines.append(f"### {key}")
        elif line.startswith('- '):
            # Regular bullet point
            content = line.replace('- ', '').strip()
            if content:
                markdown_lines.append(f"- {content}")
        elif line.startswith('  - '):
            # Nested bullet point
            content = line.replace('  - ', '').strip()
            if content:
                markdown_lines.append(f"  - {content}")
    
    return '\n'.join(markdown_lines)

def create_markdown_document(elements: List[Dict[str, Any]], pdf_name: str) -> str:
    """Create markdown document from JSONL elements"""
    
    # Extract summary from first element
    summary = elements[0] if elements and 'summary' in elements[0] else {}
    
    # Start building markdown
    markdown_lines = []
    
    # Document header
    markdown_lines.append(f"# {pdf_name.replace('_', ' ').title()}")
    markdown_lines.append("")
    markdown_lines.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    markdown_lines.append("")
    
    # Document summary
    if summary:
        doc_summary = summary.get('document_summary', {})
        markdown_lines.append("## Document Summary")
        markdown_lines.append("")
        markdown_lines.append(f"- **Total Elements**: {summary.get('total_elements', 'N/A')}")
        markdown_lines.append(f"- **Document Type**: {doc_summary.get('document_type', 'N/A')}")
        
        key_metrics = doc_summary.get('key_metrics', [])
        if key_metrics:
            markdown_lines.append("- **Key Metrics**:")
            for metric in key_metrics:
                markdown_lines.append(f"  - {metric}")
        
        markdown_lines.append("")
    
    # Process elements by type
    text_elements = [e for e in elements[1:] if e.get('type') == 'text']
    table_elements = [e for e in elements[1:] if e.get('type') == 'table']
    figure_elements = [e for e in elements[1:] if e.get('type') == 'figure']
    
    # Text content
    if text_elements:
        markdown_lines.append("## Text Content")
        markdown_lines.append("")
        
        for i, element in enumerate(text_elements, 1):
            page = element.get('page', 'Unknown')
            content = element.get('content', {})
            text = content.get('text', '')
            
            if text:
                markdown_lines.append(f"### Page {page}")
                markdown_lines.append("")
                markdown_lines.append(text)
                markdown_lines.append("")
    
    # Tables
    if table_elements:
        markdown_lines.append("## Tables")
        markdown_lines.append("")
        
        for i, element in enumerate(table_elements, 1):
            page = element.get('page', 'Unknown')
            content = element.get('content', {})
            
            # Table description
            description = content.get('text', '')
            if description:
                markdown_lines.append(f"### Table {i} (Page {page})")
                markdown_lines.append(f"*{description}*")
                markdown_lines.append("")
            
            # Structured data
            structured_data = content.get('structured_data', '')
            if structured_data:
                formatted_table = format_table_data(structured_data)
                if formatted_table:
                    markdown_lines.append(formatted_table)
                    markdown_lines.append("")
            
            # Raw text if available
            raw_text = content.get('raw_text', '')
            if raw_text and raw_text != structured_data:
                markdown_lines.append("**Raw Table Data:**")
                markdown_lines.append("```")
                markdown_lines.append(raw_text)
                markdown_lines.append("```")
                markdown_lines.append("")
    
    # Figures
    if figure_elements:
        markdown_lines.append("## Figures")
        markdown_lines.append("")
        
        for i, element in enumerate(figure_elements, 1):
            page = element.get('page', 'Unknown')
            content = element.get('content', {})
            
            description = content.get('text', '')
            if description:
                markdown_lines.append(f"### Figure {i} (Page {page})")
                markdown_lines.append(f"*{description}*")
                markdown_lines.append("")
            
            structured_data = content.get('structured_data', '')
            if structured_data:
                formatted_figure = format_table_data(structured_data)
                if formatted_figure:
                    markdown_lines.append(formatted_figure)
                    markdown_lines.append("")
    
    # Metadata section
    markdown_lines.append("## Processing Metadata")
    markdown_lines.append("")
    
    if summary:
        element_types = summary.get('element_types', {})
        categories = summary.get('categories', {})
        importance_levels = summary.get('importance_levels', {})
        
        markdown_lines.append("### Element Distribution")
        markdown_lines.append("")
        for element_type, count in element_types.items():
            markdown_lines.append(f"- **{element_type.title()}**: {count}")
        markdown_lines.append("")
        
        markdown_lines.append("### Categories")
        markdown_lines.append("")
        for category, count in categories.items():
            markdown_lines.append(f"- **{category.replace('_', ' ').title()}**: {count}")
        markdown_lines.append("")
        
        markdown_lines.append("### Importance Levels")
        markdown_lines.append("")
        for importance, count in importance_levels.items():
            markdown_lines.append(f"- **{importance.title()}**: {count}")
        markdown_lines.append("")
    
    return '\n'.join(markdown_lines)

def convert_jsonl_to_markdown(jsonl_file: str, output_file: str) -> bool:
    """Convert JSONL file to markdown"""
    try:
        # Load JSONL data
        elements = load_jsonl_file(jsonl_file)
        
        if not elements:
            print("Error: No elements found in JSONL file")
            return False
        
        # Extract PDF name from first element or filename
        pdf_name = "Unknown Document"
        if elements and 'summary' in elements[0]:
            pdf_name = elements[0]['summary'].get('pdf_name', 'Unknown Document')
        else:
            # Extract from filename
            base_name = os.path.basename(jsonl_file)
            pdf_name = base_name.replace('_blended_elements.jsonl', '').replace('_text_preserving_blend.jsonl', '').replace('.jsonl', '')
        
        # Clean up PDF name for display
        pdf_name = pdf_name.replace('_', ' ').replace('-', ' ').title()
        
        # Create markdown
        markdown_content = create_markdown_document(elements, pdf_name)
        
        # Write to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return True
        
    except Exception as e:
        print(f"Error converting JSONL to markdown: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Convert JSONL blended output to markdown')
    parser.add_argument('--jsonl_file', required=True, help='Path to input JSONL file')
    parser.add_argument('--output_file', required=True, help='Path to output markdown file')
    
    args = parser.parse_args()
    
    print(f"Converting JSONL to markdown...")
    print(f"Input: {args.jsonl_file}")
    print(f"Output: {args.output_file}")
    
    if convert_jsonl_to_markdown(args.jsonl_file, args.output_file):
        print("✅ Markdown conversion completed successfully!")
    else:
        print("❌ Markdown conversion failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
