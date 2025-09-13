"""
PDF Visual Extraction Library

A Python library for extracting text and visual elements (tables, figures) 
from PDF documents using OpenAI's vision models.

Main components:
- PDF text extraction
- PDF to image conversion
- Visual element detection using OpenAI VLM
- Table injection and export to multiple formats
"""

__version__ = "1.0.0"
__author__ = "tatevik-t"

from .pdf_text_extractor import extract_text_from_pdf
from .pdf_to_images import convert_pdf_to_images
from .openai_vlm_detector import detect_tables_figures_openai, process_images_openai
from .simple_table_injector import inject_tables_into_text, extract_tables_from_visual
from .json_to_markdown import convert_json_to_markdown
from .markdown_to_pdf import convert_markdown_to_pdf

__all__ = [
    "extract_text_from_pdf",
    "convert_pdf_to_images", 
    "detect_tables_figures_openai",
    "process_images_openai",
    "inject_tables_into_text",
    "extract_tables_from_visual",
    "convert_json_to_markdown",
    "convert_markdown_to_pdf",
]