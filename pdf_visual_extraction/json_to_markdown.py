#!/usr/bin/env python3
"""
Convert JSON with tables to Markdown format
"""

import json
import argparse
import os
from typing import Dict, Any


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_table_data(table: Dict[str, Any]) -> str:
    """Format table data as markdown"""
    markdown = []

    try:
        # Add table title
        if table.get("description"):
            description = table["description"]
            if isinstance(description, str):
                markdown.append(f"### {description}")
                markdown.append("")
            else:
                markdown.append(f"### {str(description)}")
                markdown.append("")

        # Add structured data
        if table.get("structured_data"):
            structured_data = table["structured_data"]
            if isinstance(structured_data, str):
                markdown.append(structured_data)
                markdown.append("")
            elif isinstance(structured_data, dict):
                # If it's a dict, try to convert to string
                markdown.append(str(structured_data))
                markdown.append("")
            else:
                markdown.append(str(structured_data))
                markdown.append("")

    except Exception as e:
        # If there's any error, add a fallback
        markdown.append(f"**Error formatting table data: {str(e)}**")
        markdown.append("")
        markdown.append(f"**Raw table data:** {str(table)}")
        markdown.append("")

    return "\n".join(markdown)


def convert_json_to_markdown(json_data: Dict[str, Any]) -> str:
    """Convert JSON data to markdown format"""
    markdown = []

    try:
        # Add document header
        pdf_name = json_data.get("pdf_name", "Unknown Document")
        total_pages = json_data.get("total_pages", 0)

        # Ensure pdf_name is a string
        if not isinstance(pdf_name, str):
            pdf_name = str(pdf_name)

        markdown.append(f"# {pdf_name.replace('_', ' ').replace('-', ' ').title()}")
        markdown.append("")
        markdown.append(f"**Total Pages:** {total_pages}")
        markdown.append("")
        markdown.append("---")
        markdown.append("")

        # Process each page
        pages = json_data.get("pages", [])
        if not isinstance(pages, list):
            markdown.append("**Error: Pages data is not a list**")
            return "\n".join(markdown)

        for page in pages:
            try:
                if not isinstance(page, dict):
                    markdown.append("**Error: Page data is not a dictionary**")
                    continue

                page_number = page.get("page_number", 0)
                text = page.get("text", "")
                tables = page.get("tables", [])

                # Ensure text is a string
                if not isinstance(text, str):
                    text = str(text)

                # Ensure tables is a list
                if not isinstance(tables, list):
                    tables = []

                # Add page header
                markdown.append(f"## Page {page_number}")
                markdown.append("")

                # Add text content
                if text.strip():
                    markdown.append("### Text Content")
                    markdown.append("")
                    markdown.append(text.strip())
                    markdown.append("")

                # Add tables
                if tables:
                    markdown.append("### Tables and Figures")
                    markdown.append("")
                    for i, table in enumerate(tables, 1):
                        try:
                            markdown.append(f"#### Table {i}")
                            markdown.append("")
                            table_markdown = format_table_data(table)
                            markdown.append(table_markdown)
                        except Exception as e:
                            markdown.append(f"**Error formatting table {i}: {str(e)}**")
                            markdown.append("")

                markdown.append("---")
                markdown.append("")

            except Exception as e:
                markdown.append(f"**Error processing page: {str(e)}**")
                markdown.append("---")
                markdown.append("")

    except Exception as e:
        markdown.append(f"**Error converting JSON to markdown: {str(e)}**")
        markdown.append("")
        markdown.append(f"**Raw data:** {str(json_data)}")

    return "\n".join(markdown)


def main():
    parser = argparse.ArgumentParser(description="Convert JSON with tables to Markdown")
    parser.add_argument(
        "--input_file", required=True, help="Input JSON file with tables"
    )
    parser.add_argument("--output_file", required=True, help="Output Markdown file")

    args = parser.parse_args()

    print("Converting JSON to Markdown...")
    print(f"Input: {args.input_file}")
    print(f"Output: {args.output_file}")

    try:
        # Load JSON data
        json_data = load_json_file(args.input_file)

        # Convert to markdown
        markdown_content = convert_json_to_markdown(json_data)

        # Save markdown
        os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print("✅ Markdown conversion completed successfully!")
        print(f"💾 Saved to: {args.output_file}")

        # Show statistics
        total_pages = json_data.get("total_pages", 0)
        total_tables = sum(
            len(page.get("tables", [])) for page in json_data.get("pages", [])
        )
        print(f"📊 Converted {total_pages} pages with {total_tables} tables")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
