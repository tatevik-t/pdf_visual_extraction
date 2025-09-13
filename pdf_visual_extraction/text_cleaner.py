#!/usr/bin/env python3
"""
Text Cleaner: Remove table and figure content from extracted text using LLM
This module intelligently removes redundant table/figure content that has already
been parsed by the VLM to avoid duplication in the final output.
"""

import json
import argparse
import os
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_text_cleaning_prompt(text: str, tables_info: List[Dict[str, Any]]) -> str:
    """Create a prompt for cleaning text by removing table/figure content"""

    # Create a summary of tables/figures that were found
    tables_summary = []
    for i, table in enumerate(tables_info, 1):
        page_num = table.get("page_number", "Unknown")
        description = table.get("description", "No description")
        table_type = table.get("type", "table")
        tables_summary.append(
            f"{i}. Page {page_num}: {table_type.title()} - {description}"
        )

    tables_list = (
        "\n".join(tables_summary) if tables_summary else "No tables/figures found"
    )

    prompt = f"""You are an expert at cleaning extracted text from PDFs. Your task is to remove ONLY redundant table and figure content that has already been properly parsed and structured by a Vision Language Model (VLM).

CONTEXT:
The following text was extracted from a PDF using a text extractor. Additionally, a VLM has already identified and parsed the following tables and figures:

TABLES/FIGURES ALREADY PARSED:
{tables_list}

TASK:
Clean the extracted text by removing ONLY:
1. Raw table data that appears as text (rows, columns, numbers in table format)
2. Malformed table data that appears as plain text
3. Content that exactly duplicates the parsed table/figure data

CRITICAL RULES - DO NOT CHANGE ANYTHING ELSE:
- Keep ALL regular paragraph text, headings, and narrative content EXACTLY as written
- Keep table/figure references and mentions (like "see Table 1" or "as shown in Figure 2")
- DO NOT reformat, rewrite, or change ANY remaining text
- DO NOT add any new content, explanations, or formatting
- Keep the original formatting, spacing, punctuation, and structure EXACTLY as it was
- If unsure whether to remove something, KEEP IT
- Only remove raw table data, not descriptive text about tables
- Preserve all line breaks, spacing, and original text structure

TEXT TO CLEAN:
{text}

CLEANED TEXT:"""

    return prompt


def clean_text_with_llm(
    text: str, tables_info: List[Dict[str, Any]], client: OpenAI
) -> Optional[str]:
    """Clean text using LLM to remove redundant table/figure content"""

    prompt = create_text_cleaning_prompt(text, tables_info)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.1,
        )

        cleaned_text = response.choices[0].message.content
        if cleaned_text is None:
            return None
        return cleaned_text.strip()

    except Exception as e:
        print(f"Error cleaning text with LLM: {e}")
        return None


def extract_tables_info_from_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract table/figure information from the structured data"""

    tables_info = []

    for page in data.get("pages", []):
        page_num = page.get("page_number", 0)

        for table in page.get("tables", []):
            table_info = {
                "page_number": page_num,
                "type": table.get("type", "table"),
                "description": table.get("description", ""),
                "confidence": table.get("confidence", 0.0),
                "bbox": table.get("bbox", []),
            }
            tables_info.append(table_info)

    return tables_info


def clean_text_in_data(data: Dict[str, Any], client: OpenAI) -> Dict[str, Any]:
    """Clean text in the data structure by removing redundant table/figure content"""

    # Extract table/figure information
    tables_info = extract_tables_info_from_data(data)

    if not tables_info:
        print("No tables/figures found, skipping text cleaning")
        return data

    print(f"Found {len(tables_info)} tables/figures, cleaning text...")

    # Clean text for each page
    for page in data.get("pages", []):
        page_num = page.get("page_number", 0)
        original_text = page.get("text", "")

        if not original_text.strip():
            continue

        # Get tables for this specific page
        page_tables = [t for t in tables_info if t["page_number"] == page_num]

        if page_tables:
            print(f"Cleaning text for page {page_num}...")
            cleaned_text = clean_text_with_llm(original_text, page_tables, client)

            if cleaned_text:
                # Store both original and cleaned text
                page["original_text"] = original_text
                page["text"] = cleaned_text
                page["text_cleaned"] = True
                print(f"   ✅ Text cleaned for page {page_num}")
            else:
                page["text_cleaned"] = False
                print(f"   ⚠️  Text cleaning failed for page {page_num}")
        else:
            page["text_cleaned"] = False

    return data


def clean_pdf_text(data_file: str, output_file: str, pdf_name: str) -> int:
    """Main function to clean PDF text using LLM"""

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        return 1

    client = OpenAI(api_key=api_key)

    try:
        # Load data
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"📄 Cleaning text for: {pdf_name}")

        # Clean the text
        cleaned_data = clean_text_in_data(data, client)

        # Save cleaned data
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

        print("✅ Text cleaning completed!")
        print(f"   Cleaned data saved to: {output_file}")

        # Count cleaned pages
        cleaned_pages = sum(
            1
            for page in cleaned_data.get("pages", [])
            if page.get("text_cleaned", False)
        )
        total_pages = len(cleaned_data.get("pages", []))

        print(f"   Pages cleaned: {cleaned_pages}/{total_pages}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def main():
    """Command line interface for text cleaning"""
    parser = argparse.ArgumentParser(
        description="Clean PDF text by removing redundant table/figure content"
    )
    parser.add_argument(
        "--data_file", required=True, help="Path to JSON file with extracted data"
    )
    parser.add_argument(
        "--output_file", required=True, help="Path to save cleaned data"
    )
    parser.add_argument("--pdf_name", required=True, help="Name of the PDF file")

    args = parser.parse_args()

    return clean_pdf_text(args.data_file, args.output_file, args.pdf_name)


if __name__ == "__main__":
    exit(main())
