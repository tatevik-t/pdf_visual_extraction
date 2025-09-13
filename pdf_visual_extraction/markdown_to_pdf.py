#!/usr/bin/env python3
"""
Convert Markdown to PDF using weasyprint
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

def install_weasyprint():
    """Install weasyprint if not available"""
    try:
        import weasyprint
        return True
    except ImportError:
        print("Installing weasyprint...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "weasyprint"], check=True)
            return True
        except subprocess.CalledProcessError:
            print("Failed to install weasyprint. Please install manually: pip install weasyprint")
            return False

def convert_markdown_to_pdf(markdown_file: str, pdf_file: str) -> bool:
    """Convert markdown file to PDF"""
    try:
        import weasyprint
        
        # Read markdown file
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert markdown to HTML (basic conversion)
        html_content = markdown_to_html(markdown_content)
        
        # Convert HTML to PDF
        weasyprint.HTML(string=html_content).write_pdf(pdf_file)
        
        return True
        
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return False

def markdown_to_html(markdown_content: str) -> str:
    """Basic markdown to HTML conversion"""
    html = markdown_content
    
    # Headers
    html = html.replace('# ', '<h1>').replace('\n', '</h1>\n')
    html = html.replace('## ', '<h2>').replace('\n', '</h2>\n')
    html = html.replace('### ', '<h3>').replace('\n', '</h3>\n')
    html = html.replace('#### ', '<h4>').replace('\n', '</h4>\n')
    
    # Bold
    html = html.replace('**', '<strong>').replace('**', '</strong>')
    
    # Italic
    html = html.replace('*', '<em>').replace('*', '</em>')
    
    # Code blocks
    html = html.replace('```', '<pre><code>').replace('```', '</code></pre>')
    
    # Line breaks
    html = html.replace('\n', '<br>\n')
    
    # Horizontal rules
    html = html.replace('---', '<hr>')
    
    # Wrap in HTML document
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>PDF Export</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #333; border-bottom: 2px solid #333; }}
            h2 {{ color: #666; border-bottom: 1px solid #666; }}
            h3 {{ color: #888; }}
            h4 {{ color: #aaa; }}
            pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; }}
            hr {{ border: none; border-top: 1px solid #ccc; margin: 20px 0; }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """
    
    return html

def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to PDF')
    parser.add_argument('--input_file', required=True, help='Input Markdown file')
    parser.add_argument('--output_file', required=True, help='Output PDF file')
    
    args = parser.parse_args()
    
    print("Converting Markdown to PDF...")
    print(f"Input: {args.input_file}")
    print(f"Output: {args.output_file}")
    
    # Check if weasyprint is available
    if not install_weasyprint():
        return 1
    
    # Convert to PDF
    if convert_markdown_to_pdf(args.input_file, args.output_file):
        print("✅ PDF conversion completed successfully!")
        print(f"💾 Saved to: {args.output_file}")
        return 0
    else:
        print("❌ PDF conversion failed!")
        return 1

if __name__ == "__main__":
    exit(main())
