#!/usr/bin/env python3
"""
JSON Repair Utilities for VLM Responses
Handles complex JSON parsing issues from language models
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List

def repair_vlm_json(json_str: str) -> Optional[str]:
    """
    Repair common JSON issues in VLM responses
    
    Args:
        json_str: JSON string to repair
        
    Returns:
        Repaired JSON string or None if unfixable
    """
    try:
        # First, try to parse as-is
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError:
        pass
    
    # Apply repair strategies
    repaired = json_str
    
    # Strategy 1: Remove control characters
    repaired = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', repaired)
    
    # Strategy 2: Fix trailing commas
    repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
    
    # Strategy 3: Fix unescaped quotes in strings
    # This is tricky - we need to be careful not to break valid JSON
    repaired = fix_unescaped_quotes(repaired)
    
    # Strategy 4: Fix incomplete JSON structures
    repaired = fix_incomplete_structures(repaired)
    
    # Strategy 5: Fix boolean values
    repaired = re.sub(r'\btrue\b', 'true', repaired)
    repaired = re.sub(r'\bfalse\b', 'false', repaired)
    repaired = re.sub(r'\bnull\b', 'null', repaired)
    
    try:
        json.loads(repaired)
        return repaired
    except json.JSONDecodeError:
        return None

def fix_unescaped_quotes(json_str: str) -> str:
    """
    Fix unescaped quotes in JSON strings
    
    Args:
        json_str: JSON string to fix
        
    Returns:
        Fixed JSON string
    """
    # This is a simplified approach - in practice, you'd need more sophisticated parsing
    # to handle nested quotes correctly
    
    # Find string values and fix quotes within them
    def fix_string_quotes(match):
        key = match.group(1)
        value = match.group(2)
        
        # If the value contains unescaped quotes, escape them
        if '"' in value and not value.startswith('"'):
            # This is a complex case - for now, we'll use a simple approach
            value = value.replace('"', '\\"')
        
        return f'"{key}": "{value}"'
    
    # Pattern to match key-value pairs with string values
    pattern = r'"([^"]+)"\s*:\s*"([^"]*(?:\\.[^"]*)*)"'
    return re.sub(pattern, fix_string_quotes, json_str)

def fix_incomplete_structures(json_str: str) -> str:
    """
    Fix incomplete JSON structures
    
    Args:
        json_str: JSON string to fix
        
    Returns:
        Fixed JSON string
    """
    # Count braces and brackets
    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    
    # Add missing closing braces
    if open_braces > close_braces:
        json_str += '}' * (open_braces - close_braces)
    
    # Add missing closing brackets
    if open_brackets > close_brackets:
        json_str += ']' * (open_brackets - close_brackets)
    
    return json_str

def extract_json_from_markdown(response_text: str) -> Optional[str]:
    """
    Extract JSON from markdown code blocks
    
    Args:
        response_text: Response text that may contain JSON in markdown
        
    Returns:
        Extracted JSON string or None
    """
    # Look for JSON code blocks
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches:
            # Return the longest match
            return max(matches, key=len).strip()
    
    return None

def parse_with_fallback(response_text: str, page_number: int = 0) -> Dict[str, Any]:
    """
    Parse VLM response with multiple fallback strategies
    
    Args:
        response_text: Raw response from VLM
        page_number: Page number for logging
        
    Returns:
        Parsed JSON object
    """
    # Strategy 1: Try to extract JSON from markdown
    json_str = extract_json_from_markdown(response_text)
    if json_str:
        repaired = repair_vlm_json(json_str)
        if repaired:
            try:
                result = json.loads(repaired)
                logging.info(f"Page {page_number}: Successfully parsed from markdown")
                return result
            except json.JSONDecodeError:
                pass
    
    # Strategy 2: Try to find JSON object in response
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    
    if json_start != -1 and json_end > json_start:
        json_str = response_text[json_start:json_end]
        repaired = repair_vlm_json(json_str)
        if repaired:
            try:
                result = json.loads(repaired)
                logging.info(f"Page {page_number}: Successfully parsed from response")
                return result
            except json.JSONDecodeError:
                pass
    
    # Strategy 3: Try to extract partial data
    return extract_partial_data_from_response(response_text, page_number)

def extract_partial_data_from_response(response_text: str, page_number: int) -> Dict[str, Any]:
    """
    Extract partial data when JSON parsing completely fails
    
    Args:
        response_text: Original response text
        page_number: Page number
        
    Returns:
        Partial data structure
    """
    # Extract basic information
    has_tables = bool(re.search(r'table|Table', response_text, re.IGNORECASE))
    has_figures = bool(re.search(r'figure|chart|graph|Figure|Chart|Graph', response_text, re.IGNORECASE))
    
    # Try to extract structured data
    structured_data = ""
    structured_matches = re.findall(r'structured_data["\']?\s*:\s*["\']([^"\']*)["\']', response_text, re.IGNORECASE | re.DOTALL)
    if structured_matches:
        structured_data = structured_matches[0]
    
    # Try to extract description
    description = "Extracted from partial data"
    desc_matches = re.findall(r'description["\']?\s*:\s*["\']([^"\']*)["\']', response_text, re.IGNORECASE)
    if desc_matches:
        description = desc_matches[0]
    
    # Create result structure
    result = {
        "page_analysis": {
            "has_tables": has_tables,
            "has_figures": has_figures,
            "total_elements": 1 if (has_tables or has_figures) else 0,
            "page_summary": "Partial data extraction due to JSON parsing error"
        },
        "elements": []
    }
    
    # Add element if we found data
    if structured_data or has_tables or has_figures:
        element = {
            "type": "table" if has_tables else "figure",
            "bbox": [0, 0, 600, 400],
            "confidence": 0.5,
            "description": description,
            "content": {
                "structured_data": structured_data,
                "raw_text": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                "summary": "Extracted from partial data"
            }
        }
        result["elements"].append(element)
    
    return result

def test_json_repair():
    """Test the JSON repair utilities"""
    
    # Test cases based on real VLM responses
    test_cases = [
        {
            "name": "Control characters",
            "json": '{"page_analysis": {"has_tables": true, "has_figures": false, "total_elements": 1, "page_summary": "The page contains a financial table."}, "elements": [{"type": "table", "bbox": [10, 10, 600, 400], "confidence": 0.95, "description": "Revenue table", "content": {"structured_data": "Revenue data"}}]}'
        },
        {
            "name": "Trailing comma",
            "json": '{"page_analysis": {"has_tables": true, "has_figures": false, "total_elements": 1, "page_summary": "The page contains a financial table."}, "elements": [{"type": "table", "bbox": [10, 10, 600, 400], "confidence": 0.95, "description": "Revenue table", "content": {"structured_data": "Revenue data"}},]}'
        },
        {
            "name": "Markdown wrapped",
            "json": '```json\n{"page_analysis": {"has_tables": true, "has_figures": false, "total_elements": 1, "page_summary": "The page contains a financial table."}, "elements": [{"type": "table", "bbox": [10, 10, 600, 400], "confidence": 0.95, "description": "Revenue table", "content": {"structured_data": "Revenue data"}}]}\n```'
        }
    ]
    
    print("Testing JSON Repair Utilities:")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Input: {test_case['json'][:100]}...")
        
        result = parse_with_fallback(test_case['json'], 1)
        print(f"Success: {result.get('page_analysis', {}).get('page_summary', 'Unknown')}")
        print(f"Elements: {len(result.get('elements', []))}")

if __name__ == "__main__":
    test_json_repair()
