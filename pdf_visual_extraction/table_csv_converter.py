#!/usr/bin/env python3
"""
Table CSV Converter: Convert extracted table data to CSV format using LLM
"""

import json
import argparse
import os
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_csv_conversion_prompt(table_data: str) -> str:
    """Create prompt for converting table structured data to CSV format"""
    return f"""You are an expert at converting structured table data into CSV format.

Convert the following table data into a clean, properly formatted CSV:

{table_data}

Requirements:
1. Extract all numerical data and text content
2. Identify proper column headers
3. Create rows with consistent data alignment
4. Handle missing values appropriately (use empty cells)
5. Ensure proper CSV formatting with commas as delimiters
6. Quote text fields that contain commas or special characters
7. Preserve the hierarchical structure if applicable

Return ONLY the CSV content, no explanations or additional text.
The first line should be the header row with column names.
Each subsequent line should be a data row.

Example format:
"Category","Subcategory","Value","Notes"
"Revenue","Q1 2024","1000000","Strong growth"
"Revenue","Q2 2024","1200000","Continued growth"
"""


def convert_table_to_csv_llm(table_data: str, client: OpenAI) -> Optional[str]:
    """Convert table structured data to CSV using LLM"""
    try:
        prompt = create_csv_conversion_prompt(table_data)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.1,
        )

        csv_content = response.choices[0].message.content
        if csv_content is None:
            return None
        csv_content = csv_content.strip()

        # Clean up the response - remove any markdown formatting
        if csv_content.startswith("```csv"):
            csv_content = csv_content[6:]
        if csv_content.startswith("```"):
            csv_content = csv_content[3:]
        if csv_content.endswith("```"):
            csv_content = csv_content[:-3]

        return csv_content.strip()

    except Exception as e:
        print(f"Error converting table to CSV: {e}")
        # Return a simple fallback CSV instead of None
        return "Error,Unable to convert,LLM Error\n"


def extract_tables_from_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all tables from the processed data"""
    all_tables = []

    for page in data.get("pages", []):
        page_number = page.get("page_number", 0)
        tables = page.get("tables", [])

        for table_idx, table in enumerate(tables):
            table_info = {
                "page_number": page_number,
                "table_index": table_idx,
                "description": table.get("description", ""),
                "structured_data": table.get("structured_data", ""),
                "raw_text": table.get("raw_text", ""),
                "confidence": table.get("confidence", 0.0),
                "bbox": table.get("bbox", []),
            }
            all_tables.append(table_info)

    return all_tables


def convert_tables_to_csv(
    data: Dict[str, Any], output_dir: str, pdf_name: str
) -> Dict[str, Any]:
    """Convert all extracted tables to CSV format"""

    # Initialize OpenAI client with API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required for CSV conversion"
        )

    client = OpenAI(api_key=api_key)

    # Extract all tables
    tables = extract_tables_from_data(data)

    if not tables:
        print("No tables found to convert")
        return {
            "pdf_name": pdf_name,
            "total_tables": 0,
            "converted_tables": 0,
            "csv_files": [],
            "errors": 0,
        }

    print(f"Found {len(tables)} tables to convert to CSV")

    # Create CSV output directory
    csv_dir = os.path.join(output_dir, "csv_exports")
    os.makedirs(csv_dir, exist_ok=True)

    results: Dict[str, Any] = {
        "pdf_name": pdf_name,
        "total_tables": len(tables),
        "converted_tables": 0,
        "csv_files": [],
        "errors": 0,
    }

    for table in tables:
        page_num = table["page_number"]
        table_idx = table["table_index"]
        description = table["description"]
        structured_data = table["structured_data"]

        # Create filename
        safe_description = "".join(
            c for c in description if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        if not safe_description:
            safe_description = f"table_{page_num}_{table_idx}"
        else:
            safe_description = safe_description.replace(" ", "_")[:50]  # Limit length

        csv_filename = f"{pdf_name}_page_{page_num:03d}_{safe_description}.csv"
        csv_path = os.path.join(csv_dir, csv_filename)

        print(f"Converting table from page {page_num} to CSV...")

        # Convert to CSV using LLM
        try:
            csv_content = convert_table_to_csv_llm(structured_data, client)

            if csv_content:
                try:
                    # Save CSV file
                    with open(csv_path, "w", encoding="utf-8", newline="") as f:
                        f.write(csv_content)

                    results["converted_tables"] += 1
                    results["csv_files"].append(
                        {
                            "page_number": page_num,
                            "table_index": table_idx,
                            "description": description,
                            "filename": csv_filename,
                            "file_path": csv_path,
                            "file_size": os.path.getsize(csv_path),
                        }
                    )

                    print(f"✅ Converted table from page {page_num} -> {csv_filename}")

                except Exception as e:
                    print(f"❌ Error saving CSV for page {page_num}: {e}")
                    results["errors"] += 1
            else:
                print(f"❌ Failed to convert table from page {page_num}")
                results["errors"] += 1
        except Exception as e:
            print(f"❌ Error in CSV conversion for page {page_num}: {e}")
            results["errors"] += 1

    # Save conversion summary
    summary_path = os.path.join(csv_dir, f"{pdf_name}_csv_conversion_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n📊 CSV Conversion Summary:")
    print(f"   Total tables: {results['total_tables']}")
    print(f"   Converted: {results['converted_tables']}")
    print(f"   Errors: {results['errors']}")
    print(f"   CSV files saved to: {csv_dir}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Convert extracted tables to CSV format"
    )
    parser.add_argument(
        "--data_file", required=True, help="Path to JSON file with table data"
    )
    parser.add_argument(
        "--output_dir", required=True, help="Output directory for CSV files"
    )
    parser.add_argument("--pdf_name", required=True, help="Name of the PDF file")

    args = parser.parse_args()

    print("Table CSV Converter")
    print(f"Data file: {args.data_file}")
    print(f"Output directory: {args.output_dir}")
    print(f"PDF name: {args.pdf_name}")

    try:
        # Load data
        with open(args.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert tables to CSV
        convert_tables_to_csv(data, args.output_dir, args.pdf_name)

        print("✅ CSV conversion completed!")
        summary_path = os.path.join(
            args.output_dir,
            "csv_exports",
            f"{args.pdf_name}_csv_conversion_summary.json",
        )
        print(f"   Summary saved to: {summary_path}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
