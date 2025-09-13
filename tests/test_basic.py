"""
Basic tests for PDF Visual Extraction Library
"""

import pytest
import json
import os
import tempfile
from pathlib import Path

# Import the library functions
from pdf_visual_extraction import (
    extract_text_from_pdf,
    convert_pdf_to_images,
    inject_tables_into_text,
    extract_tables_from_visual
)

class TestBasicFunctionality:
    """Test basic functionality without requiring actual PDF files"""
    
    def test_extract_tables_from_visual(self):
        """Test table extraction from visual data"""
        # Mock visual data
        visual_data = {
            "pages": [
                {
                    "page_number": 0,
                    "detection_result": {
                        "elements": [
                            {
                                "type": "table",
                                "description": "Test table",
                                "content": {
                                    "structured_data": "### Table: Test\n- **Item**: value",
                                    "raw_text": "Item value"
                                },
                                "confidence": 0.95,
                                "bbox": [0, 0, 100, 100]
                            }
                        ]
                    }
                }
            ]
        }
        
        tables = extract_tables_from_visual(visual_data)
        
        assert 0 in tables
        assert len(tables[0]) == 1
        assert tables[0][0]["description"] == "Test table"
        assert tables[0][0]["confidence"] == 0.95
    
    def test_inject_tables_into_text(self):
        """Test table injection into text data"""
        # Mock text data
        text_data = {
            "pdf_name": "test",
            "total_pages": 1,
            "pages": [
                {
                    "page_number": 0,
                    "text": "Test page content"
                }
            ]
        }
        
        # Mock tables data
        tables_by_page = {
            0: [
                {
                    "description": "Test table",
                    "structured_data": "### Table: Test",
                    "raw_text": "Test data",
                    "confidence": 0.95,
                    "bbox": [0, 0, 100, 100]
                }
            ]
        }
        
        result = inject_tables_into_text(text_data, tables_by_page)
        
        assert "tables" in result["pages"][0]
        assert len(result["pages"][0]["tables"]) == 1
        assert result["pages"][0]["tables"][0]["description"] == "Test table"
    
    def test_json_serialization(self):
        """Test that data structures are JSON serializable"""
        data = {
            "pdf_name": "test",
            "total_pages": 1,
            "pages": [
                {
                    "page_number": 0,
                    "text": "Test content",
                    "tables": [
                        {
                            "description": "Test table",
                            "structured_data": "### Table: Test",
                            "raw_text": "Test data",
                            "confidence": 0.95,
                            "bbox": [0, 0, 100, 100]
                        }
                    ]
                }
            ]
        }
        
        # Should not raise an exception
        json_str = json.dumps(data, indent=2)
        assert isinstance(json_str, str)
        
        # Should be able to parse back
        parsed_data = json.loads(json_str)
        assert parsed_data["pdf_name"] == "test"
        assert len(parsed_data["pages"]) == 1
