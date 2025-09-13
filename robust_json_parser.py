#!/usr/bin/env python3
"""
Robust JSON Parser for VLM Responses
Handles common JSON parsing issues from language models
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Tuple

def clean_json_string(json_str: str) -> str:
    """
    Clean JSON string by removing common issues that cause parsing errors
    
    Args:
        json_str: Raw JSON string from VLM
        
    Returns:
        Cleaned JSON string
    """
    # Remove control characters except newlines and tabs
    json_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', json_str)
    
    # Fix common JSON issues
    # 1. Remove trailing commas before closing braces/brackets
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # 2. Fix unescaped quotes in strings
    json_str = re.sub(r'(?<!\\)"(?=.*")', '\\"', json_str)
    
    # 3. Fix single quotes to double quotes (but be careful with apostrophes)
    json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
    
    # 4. Fix unescaped newlines in strings
    json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
    
    # 5. Fix unescaped backslashes
    json_str = re.sub(r'\\(?!["\\/bfnrt])', '\\\\', json_str)
    
    # 6. Remove any remaining control characters
    json_str = ''.join(char for char in json_str if ord(char) >= 32 or char in '\n\t')
    
    return json_str

def extract_json_from_response(response_text: str) -> Tuple[Optional[str], str]:
    """
    Extract JSON from VLM response text
    
    Args:
        response_text: Full response from VLM
        
    Returns:
        Tuple of (extracted_json, original_response)
    """
    # Look for JSON code blocks first
    json_patterns = [
        r'```json\s*(.*?)\s*```',  # ```json ... ```
        r'```\s*(.*?)\s*```',      # ``` ... ```
        r'\{.*\}',                  # Any JSON object
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches:
            # Return the longest match (most likely to be complete)
            json_str = max(matches, key=len)
            return json_str.strip(), response_text
    
    # If no code blocks found, try to find JSON object boundaries
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    
    if json_start != -1 and json_end > json_start:
        json_str = response_text[json_start:json_end]
        return json_str, response_text
    
    return None, response_text

def parse_vlm_json_response(response_text: str, page_number: int = 0) -> Dict[str, Any]:
    """
    Parse VLM JSON response with robust error handling
    
    Args:
        response_text: Raw response from VLM
        page_number: Page number for error reporting
        
    Returns:
        Parsed JSON object or error fallback
    """
    # Extract JSON from response
    json_str, original_response = extract_json_from_response(response_text)
    
    if not json_str:
        logging.warning(f"Page {page_number}: No JSON found in response")
        return create_error_fallback("No JSON found in response", page_number)
    
    # Clean the JSON string
    cleaned_json = clean_json_string(json_str)
    
    # Try to parse the cleaned JSON
    try:
        result = json.loads(cleaned_json)
        logging.info(f"Page {page_number}: Successfully parsed JSON")
        return result
    except json.JSONDecodeError as e:
        logging.warning(f"Page {page_number}: JSON parsing failed after cleaning: {e}")
        
        # Try additional cleaning strategies
        result = try_advanced_json_cleaning(cleaned_json, page_number)
        if result:
            return result
        
        # If all else fails, try to extract partial data
        return extract_partial_data(original_response, page_number)

def try_advanced_json_cleaning(json_str: str, page_number: int) -> Optional[Dict[str, Any]]:
    """
    Try advanced JSON cleaning strategies
    
    Args:
        json_str: JSON string to clean
        page_number: Page number for logging
        
    Returns:
        Parsed JSON or None if failed
    """
    # Strategy 1: Fix common VLM JSON issues
    advanced_cleaning = json_str
    
    # Fix incomplete JSON (missing closing braces)
    open_braces = advanced_cleaning.count('{')
    close_braces = advanced_cleaning.count('}')
    if open_braces > close_braces:
        advanced_cleaning += '}' * (open_braces - close_braces)
    
    # Fix incomplete arrays
    open_brackets = advanced_cleaning.count('[')
    close_brackets = advanced_cleaning.count(']')
    if open_brackets > close_brackets:
        advanced_cleaning += ']' * (open_brackets - close_brackets)
    
    try:
        result = json.loads(advanced_cleaning)
        logging.info(f"Page {page_number}: Successfully parsed with advanced cleaning")
        return result
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Try to fix specific common issues
    try:
        # Remove problematic characters
        fixed_json = re.sub(r'[\x00-\x1F\x7F]', '', advanced_cleaning)
        result = json.loads(fixed_json)
        logging.info(f"Page {page_number}: Successfully parsed after character removal")
        return result
    except json.JSONDecodeError:
        pass
    
    return None

def extract_partial_data(response_text: str, page_number: int) -> Dict[str, Any]:
    """
    Extract partial data from response when JSON parsing completely fails
    
    Args:
        response_text: Original response text
        page_number: Page number for logging
        
    Returns:
        Partial data structure
    """
    logging.warning(f"Page {page_number}: Attempting partial data extraction")
    
    # Try to extract basic information using regex
    has_tables = bool(re.search(r'table|Table', response_text, re.IGNORECASE))
    has_figures = bool(re.search(r'figure|chart|graph|Figure|Chart|Graph', response_text, re.IGNORECASE))
    
    # Try to extract structured data using regex
    structured_data_matches = re.findall(r'structured_data["\']?\s*:\s*["\']([^"\']*)["\']', response_text, re.IGNORECASE)
    structured_data = structured_data_matches[0] if structured_data_matches else ""
    
    # Try to extract description
    description_matches = re.findall(r'description["\']?\s*:\s*["\']([^"\']*)["\']', response_text, re.IGNORECASE)
    description = description_matches[0] if description_matches else "Extracted from partial data"
    
    # Create a basic structure
    result = {
        "page_analysis": {
            "has_tables": has_tables,
            "has_figures": has_figures,
            "total_elements": 1 if (has_tables or has_figures) else 0,
            "page_summary": "Partial data extraction due to JSON parsing error"
        },
        "elements": []
    }
    
    # Add elements if we found structured data
    if structured_data or has_tables or has_figures:
        element = {
            "type": "table" if has_tables else "figure",
            "bbox": [0, 0, 600, 400],  # Default bbox
            "confidence": 0.5,  # Lower confidence for partial data
            "description": description,
            "content": {
                "structured_data": structured_data,
                "raw_text": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                "summary": "Extracted from partial data due to JSON parsing issues"
            }
        }
        result["elements"].append(element)
    
    return result

def create_error_fallback(error_message: str, page_number: int) -> Dict[str, Any]:
    """
    Create error fallback structure
    
    Args:
        error_message: Error message
        page_number: Page number
        
    Returns:
        Error fallback structure
    """
    return {
        "page_analysis": {
            "has_tables": False,
            "has_figures": False,
            "total_elements": 0,
            "page_summary": f"Error: {error_message}"
        },
        "elements": []
    }

def test_json_parser():
    """Test the JSON parser with sample problematic responses"""
    
    # Test case 1: Control characters
    test1 = '{"page_analysis": {"has_tables": true, "has_figures": false, "total_elements": 1, "page_summary": "The page contains a financial table with revenue data."}, "elements": [{"type": "table", "bbox": [10, 10, 600, 400], "confidence": 0.95, "description": "Revenue table", "content": {"structured_data": "Revenue data here"}}]}'
    
    # Test case 2: Trailing comma
    test2 = '{"page_analysis": {"has_tables": true, "has_figures": false, "total_elements": 1, "page_summary": "The page contains a financial table."}, "elements": [{"type": "table", "bbox": [10, 10, 600, 400], "confidence": 0.95, "description": "Revenue table", "content": {"structured_data": "Revenue data"}},]}'
    
    # Test case 3: Unescaped quotes
    test3 = '{"page_analysis": {"has_tables": true, "has_figures": false, "total_elements": 1, "page_summary": "The page contains a "financial" table."}, "elements": [{"type": "table", "bbox": [10, 10, 600, 400], "confidence": 0.95, "description": "Revenue table", "content": {"structured_data": "Revenue data"}}]}'
    
    test_cases = [
        ("Control characters", test1),
        ("Trailing comma", test2),
        ("Unescaped quotes", test3)
    ]
    
    print("Testing JSON Parser:")
    print("=" * 50)
    
    for name, test_json in test_cases:
        print(f"\nTest: {name}")
        print(f"Input: {test_json[:100]}...")
        
        result = parse_vlm_json_response(test_json, 1)
        print(f"Success: {result.get('page_analysis', {}).get('page_summary', 'Unknown')}")
        print(f"Elements: {len(result.get('elements', []))}")

if __name__ == "__main__":
    test_json_parser()
