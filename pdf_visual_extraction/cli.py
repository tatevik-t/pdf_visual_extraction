#!/usr/bin/env python3
"""
Command Line Interface for PDF Visual Extraction Library
"""

import argparse
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path modification
from simple_pipeline import main as pipeline_main  # noqa: E402


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="PDF Visual Extraction - Extract text and visual elements from PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic extraction
  pdf-visual-extract --pdf_path document.pdf --output_dir ./output

  # With markdown export
  pdf-visual-extract --pdf_path document.pdf --output_dir ./output --export_md

  # With PDF export
  pdf-visual-extract --pdf_path document.pdf --output_dir ./output --export_pdf

  # Full pipeline with all exports
  pdf-visual-extract --pdf_path document.pdf --output_dir ./output --export_md --export_pdf --max_pages 5
        """,
    )

    parser.add_argument("--pdf_path", required=True, help="Path to input PDF file")
    parser.add_argument(
        "--output_dir", required=True, help="Output directory for all results"
    )
    parser.add_argument(
        "--max_pages",
        type=int,
        default=10,
        help="Maximum pages to process (default: 10)",
    )
    parser.add_argument(
        "--export_md", action="store_true", help="Export to Markdown format"
    )
    parser.add_argument(
        "--export_pdf", action="store_true", help="Export to PDF format"
    )

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        return 1

    if not args.pdf_path.lower().endswith(".pdf"):
        print(f"❌ Error: File must be a PDF: {args.pdf_path}")
        return 1

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Run the pipeline
    try:
        return pipeline_main()
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
