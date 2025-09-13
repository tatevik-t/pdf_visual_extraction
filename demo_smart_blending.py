#!/usr/bin/env python3
"""
Demo script to show smart blending capabilities with sample data
"""

import json
from smart_text_visual_blender import create_semantic_blended_elements, save_smart_blended_elements

def create_demo_data():
    """Create sample data to demonstrate smart blending"""
    
    # Sample text data
    text_data = {
        "pdf_name": "demo-earnings-report",
        "pages": [
            {
                "page_number": 1,
                "text": "Alphabet Inc. Q4 2024 Earnings Report\n\nFinancial Highlights:\nConsolidated Alphabet revenues in Q4 2024 increased 12% year over year to $96.5 billion, reflecting robust momentum across the business. Google Services revenues increased 10% to $84.1 billion, reflecting strong momentum across Google Search and YouTube ads.\n\nKey Financial Metrics:\nThe following table summarizes our consolidated financial results for the quarter and fiscal year ended December 31, 2023 and 2024 (in millions, except for per share information and percentages)."
            },
            {
                "page_number": 2,
                "text": "Segment Operating Results:\nAs announced on October 17, 2024, the Gemini app team joined Google DeepMind. The costs associated with the Gemini app team continue to be reported within our Google Services segment.\n\nRevenue Breakdown:\nGoogle Services includes products and services such as ads, Android, Chrome, devices, Google Maps, Google Play, Search, and YouTube. Google Cloud includes infrastructure and platform services for enterprise customers."
            }
        ]
    }
    
    # Sample visual data with clean structured data
    visual_data = {
        "pages": [
            {
                "page_number": 1,
                "detection_result": {
                    "elements": [
                        {
                            "type": "table",
                            "bbox": [10, 400, 600, 650],
                            "confidence": 0.95,
                            "description": "Financial results table for Alphabet Inc. for Q4 2024",
                            "content": {
                                "structured_data": "### Q4 2024 Financial Highlights\n\n- **Revenues**:\n  - Quarter Ended December 31, 2023: $86,310 million\n  - Quarter Ended December 31, 2024: $96,469 million\n  - Year Ended December 31, 2023: $307,394 million\n  - Year Ended December 31, 2024: $350,018 million\n\n- **Operating Income**:\n  - Quarter Ended December 31, 2023: $23,697 million\n  - Quarter Ended December 31, 2024: $30,972 million\n  - Year Ended December 31, 2023: $84,293 million\n  - Year Ended December 31, 2024: $112,390 million\n\n- **Net Income**:\n  - Quarter Ended December 31, 2023: $20,687 million\n  - Quarter Ended December 31, 2024: $26,536 million\n  - Year Ended December 31, 2023: $73,795 million\n  - Year Ended December 31, 2024: $100,118 million",
                                "summary": "Key financial metrics showing strong growth across all major categories"
                            }
                        }
                    ]
                }
            },
            {
                "page_number": 2,
                "detection_result": {
                    "elements": [
                        {
                            "type": "table",
                            "bbox": [10, 200, 500, 400],
                            "confidence": 0.92,
                            "description": "Segment revenue breakdown for Q4 2024",
                            "content": {
                                "structured_data": "### Segment Revenue Breakdown\n\n- **Google Services**:\n  - 2023: $76,311 million\n  - 2024: $84,094 million\n  - Growth: 10%\n\n- **Google Cloud**:\n  - 2023: $9,192 million\n  - 2024: $11,955 million\n  - Growth: 30%\n\n- **Other Bets**:\n  - 2023: $657 million\n  - 2024: $400 million\n  - Growth: -39%\n\n- **Total Revenues**:\n  - 2023: $86,310 million\n  - 2024: $96,469 million\n  - Growth: 12%",
                                "summary": "Segment performance showing strong growth in Google Services and Cloud"
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    return text_data, visual_data

def main():
    print("Creating demo data for smart blending...")
    
    # Create demo data
    text_data, visual_data = create_demo_data()
    
    # Run smart blending
    print("Running smart blending...")
    blended_elements = create_semantic_blended_elements(text_data, visual_data)
    
    # Save results
    output_file = "./demo_smart_blend.jsonl"
    save_smart_blended_elements(blended_elements, output_file, "demo-earnings-report")
    
    print(f"\nSmart blending completed! Results saved to: {output_file}")
    print(f"Total elements: {len(blended_elements)}")
    
    # Show sample of results
    print("\nSample blended elements:")
    for i, element in enumerate(blended_elements[:3]):
        print(f"\n--- Element {i+1} ---")
        print(f"Type: {element['type']}")
        print(f"Page: {element['page']}")
        print(f"Context: {element['context']}")
        if element['type'] == 'text':
            print(f"Content: {element['content'][:100]}...")
        else:
            print(f"Description: {element['content']['description']}")
            print(f"Has structured data: {bool(element['content']['structured_data'])}")

if __name__ == "__main__":
    main()
