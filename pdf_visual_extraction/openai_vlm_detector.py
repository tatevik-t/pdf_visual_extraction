#!/usr/bin/env python3
"""
OpenAI VLM Table/Figure Detector using GPT-4o-mini
"""

import json
import argparse
import os
import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any
from openai import OpenAI


def encode_image(image_path: str) -> str:
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def create_table_figure_detection_prompt() -> str:
    """Create prompt for table/figure detection"""
    return """You are an expert at analyzing financial documents and extracting structured data from tables and figures.

For each image, identify and extract:
1. Tables with financial data
2. Charts, graphs, or other figures

For each table/figure found, provide:
- Type: "table" or "figure"
- Description: Brief description of what the table/figure shows
- Bounding box: [x1, y1, x2, y2] coordinates
- Confidence: 0.0 to 1.0
- Content: Extract the structured data in this exact format:

For tables, use this structured list format:
### Table: [Table Title]
- **Category Name**:
  - Subcategory: value
  - Subcategory: value
- **Another Category**:
  - Subcategory: value
  - Subcategory: value

For figures, use this format:
### Figure: [Figure Title]
- **Description**: What the figure shows
- **Key Data Points**:
  - Point 1: value
  - Point 2: value

IMPORTANT: Extract ALL numbers and data from tables/figures. Be precise and complete.

Return your analysis as valid JSON in this format:
{
  "page_analysis": {
    "has_tables": true/false,
    "has_figures": true/false,
    "total_elements": number,
    "page_summary": "Brief summary of the page content"
  },
  "elements": [
    {
      "type": "table" or "figure",
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95,
      "description": "Description of the element",
      "content": {
        "structured_data": "The structured list format data",
        "raw_text": "Raw text from the element",
        "summary": "Brief summary of the element"
      }
    }
  ]
}"""


def detect_tables_figures_openai(image_path: str, client: OpenAI) -> Dict[str, Any]:
    """Detect tables and figures in image using OpenAI VLM"""
    try:
        # Encode image
        base64_image = encode_image(image_path)

        # Create prompt
        prompt = create_table_figure_detection_prompt()

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=4000,
            temperature=0.1,
        )

        # Parse response
        response_text = response.choices[0].message.content
        if response_text is None:
            return {"elements": [], "error": "No response content"}

        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            else:
                # Fallback: create basic structure
                return {
                    "page_analysis": {
                        "has_tables": False,
                        "has_figures": False,
                        "total_elements": 0,
                        "page_summary": "No structured data detected",
                    },
                    "elements": [],
                }
        except json.JSONDecodeError:
            # Fallback: create basic structure
            return {
                "page_analysis": {
                    "has_tables": False,
                    "has_figures": False,
                    "total_elements": 0,
                    "page_summary": "JSON parsing failed",
                },
                "elements": [],
            }

    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return {
            "page_analysis": {
                "has_tables": False,
                "has_figures": False,
                "total_elements": 0,
                "page_summary": f"Error: {str(e)}",
            },
            "elements": [],
        }


def process_single_image(args_tuple) -> tuple:
    """Process a single image - designed for concurrent execution"""
    page_num, image_path, client = args_tuple

    try:
        print(f"Processing page {page_num + 1}: {os.path.basename(image_path)}")

        # Detect tables and figures
        detection_result = detect_tables_figures_openai(image_path, client)

        # Count elements
        elements = detection_result.get("elements", [])

        # Create page result
        page_result = {
            "page_number": page_num,
            "image_path": image_path,
            "image_filename": os.path.basename(image_path),
            "detection_result": detection_result,
            "raw_response": "",
            "processing_timestamp": str(time.time()),
        }

        print(f"Found {len(elements)} elements on page {page_num + 1}")

        return page_num, page_result, len(elements), None

    except Exception as e:
        print(f"Error processing page {page_num + 1}: {e}")
        return page_num, None, 0, str(e)


def process_images_openai(
    images_dir: str,
    pdf_name: str,
    output_file: str,
    max_pages: int = 10,
    max_workers: int = 5,
) -> Dict[str, Any]:
    """Process images using OpenAI VLM with concurrent processing"""

    # Initialize OpenAI client
    # client = OpenAI()  # Not used in this function

    # Get list of image files
    image_files = []
    for i in range(max_pages):
        image_path = os.path.join(images_dir, f"page_{i:03d}.png")
        if os.path.exists(image_path):
            image_files.append((i, image_path))

    if not image_files:
        print("No images found!")
        return {}

    print(
        f"Processing {len(image_files)} images with {max_workers} concurrent workers..."
    )

    results: Dict[str, Any] = {
        "pdf_name": pdf_name,
        "images_dir": images_dir,
        "total_pages": len(image_files),
        "total_elements": 0,
        "errors": 0,
        "pages": [],
    }

    # Prepare arguments for concurrent processing
    # Note: We need to create a new client for each thread to avoid issues
    def create_client():
        return OpenAI()

    # Process images concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_page = {}
        for page_num, image_path in image_files:
            # Create a new client for each task
            task_client = create_client()
            future = executor.submit(
                process_single_image, (page_num, image_path, task_client)
            )
            future_to_page[future] = page_num

        # Collect results as they complete
        for future in as_completed(future_to_page):
            page_num, page_result, element_count, error = future.result()

            if error:
                results["errors"] += 1
                print(f"Error processing page {page_num + 1}: {error}")
            else:
                results["pages"].append(page_result)
                results["total_elements"] += element_count

    # Sort pages by page number to maintain order
    results["pages"].sort(key=lambda x: x["page_number"])

    print("Concurrent processing completed!")
    print(f"Total pages: {results['total_pages']}")
    print(f"Total elements: {results['total_elements']}")
    print(f"Errors: {results['errors']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="OpenAI VLM Table/Figure Detection")
    parser.add_argument(
        "--images_dir", required=True, help="Directory containing page images"
    )
    parser.add_argument("--pdf_name", required=True, help="Name of the PDF file")
    parser.add_argument("--output_file", required=True, help="Output JSON file path")
    parser.add_argument(
        "--max_pages", type=int, default=10, help="Maximum pages to process"
    )

    args = parser.parse_args()

    print("OpenAI VLM Table/Figure Detection")
    print(f"Images directory: {args.images_dir}")
    print(f"PDF name: {args.pdf_name}")
    print(f"Output file: {args.output_file}")
    print(f"Max pages: {args.max_pages}")

    # Process images
    results = process_images_openai(
        args.images_dir, args.pdf_name, args.output_file, args.max_pages
    )

    if not results:
        print("No results generated!")
        return 1

    # Save results
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results saved to: {args.output_file}")
    print("Processing completed!")
    print(f"Total pages: {results['total_pages']}")
    print(f"Total elements: {results['total_elements']}")
    print(f"Errors: {results['errors']}")

    return 0


if __name__ == "__main__":
    exit(main())
