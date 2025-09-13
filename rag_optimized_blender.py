#!/usr/bin/env python3
"""
RAG-Optimized Blending Module
Creates output optimized for Retrieval-Augmented Generation systems
"""

import json
import argparse
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

def create_rag_optimized_chunks(text_data: Dict[str, Any], visual_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create RAG-optimized chunks with proper metadata and searchable content
    
    Args:
        text_data: Text extraction results
        visual_data: Visual element detection results
        
    Returns:
        List of RAG-optimized chunks
    """
    chunks = []
    
    # Get text pages and visual elements
    text_pages = text_data.get('pages', [])
    visual_pages = visual_data.get('pages', [])
    
    # Organize visual elements by page
    visual_elements_by_page = {}
    for page_data in visual_pages:
        page_num = page_data.get('page_number', 0)
        elements = page_data.get('detection_result', {}).get('elements', [])
        visual_elements_by_page[page_num] = elements
    
    # Process each page
    for page_data in text_pages:
        page_num = page_data.get('page_number', 0)
        page_text = page_data.get('text', '')
        
        # Get visual elements for this page
        page_visual_elements = visual_elements_by_page.get(page_num, [])
        
        # Create text chunks with proper metadata
        text_chunks = create_text_chunks(page_num, page_text, page_visual_elements)
        chunks.extend(text_chunks)
        
        # Create visual element chunks
        visual_chunks = create_visual_chunks(page_num, page_visual_elements)
        chunks.extend(visual_chunks)
    
    return chunks

def create_text_chunks(page_num: int, page_text: str, visual_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create text chunks optimized for RAG retrieval
    
    Args:
        page_num: Page number
        page_text: Full page text
        visual_elements: Visual elements on this page
        
    Returns:
        List of text chunks
    """
    chunks = []
    
    # Split text into semantic chunks (paragraphs, sections)
    text_sections = split_text_into_semantic_chunks(page_text)
    
    for i, section in enumerate(text_sections):
        if not section.strip():
            continue
            
        # Create chunk metadata
        chunk_metadata = {
            "chunk_id": f"page_{page_num}_text_{i+1}",
            "page_number": page_num,
            "chunk_type": "text",
            "chunk_index": i + 1,
            "has_visual_elements": len(visual_elements) > 0,
            "visual_element_count": len(visual_elements),
            "chunk_length": len(section),
            "word_count": len(section.split())
        }
        
        # Add content and searchable text
        chunk_content = {
            "text": section,
            "searchable_text": create_searchable_text(section),
            "keywords": extract_keywords(section),
            "entities": extract_entities(section)
        }
        
        chunks.append({
            "id": chunk_metadata["chunk_id"],
            "content": chunk_content,
            "metadata": chunk_metadata
        })
    
    return chunks

def create_visual_chunks(page_num: int, visual_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create visual element chunks optimized for RAG retrieval
    
    Args:
        page_num: Page number
        visual_elements: List of visual elements
        
    Returns:
        List of visual chunks
    """
    chunks = []
    
    for i, element in enumerate(visual_elements):
        element_type = element.get('type', 'unknown')
        confidence = element.get('confidence', 0.0)
        
        # Only process high-confidence elements
        if confidence < 0.3:
            continue
        
        # Extract structured data
        content = element.get('content', {})
        structured_data = content.get('structured_data', '')
        description = element.get('description', '')
        
        # Create chunk metadata
        chunk_metadata = {
            "chunk_id": f"page_{page_num}_visual_{i+1}",
            "page_number": page_num,
            "chunk_type": element_type,
            "chunk_index": i + 1,
            "confidence": confidence,
            "bbox": element.get('bbox', []),
            "has_structured_data": bool(structured_data)
        }
        
        # Create searchable content
        searchable_text = create_visual_searchable_text(description, structured_data)
        
        # Create chunk content
        chunk_content = {
            "element_type": element_type,
            "description": description,
            "structured_data": structured_data,
            "searchable_text": searchable_text,
            "keywords": extract_keywords(searchable_text),
            "entities": extract_entities(searchable_text),
            "raw_data": content
        }
        
        chunks.append({
            "id": chunk_metadata["chunk_id"],
            "content": chunk_content,
            "metadata": chunk_metadata
        })
    
    return chunks

def split_text_into_semantic_chunks(text: str, max_chunk_size: int = 1000) -> List[str]:
    """
    Split text into semantic chunks optimized for RAG
    
    Args:
        text: Full text to split
        max_chunk_size: Maximum chunk size in characters
        
    Returns:
        List of text chunks
    """
    # First split by double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed max size, save current chunk
        if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def create_searchable_text(text: str) -> str:
    """
    Create searchable text by cleaning and normalizing
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned, searchable text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep important punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\$\%]', ' ', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def create_visual_searchable_text(description: str, structured_data: str) -> str:
    """
    Create searchable text for visual elements
    
    Args:
        description: Element description
        structured_data: Structured data content
        
    Returns:
        Combined searchable text
    """
    searchable_parts = []
    
    if description:
        searchable_parts.append(create_searchable_text(description))
    
    if structured_data:
        # Extract key information from structured data
        structured_text = extract_text_from_structured_data(structured_data)
        searchable_parts.append(create_searchable_text(structured_text))
    
    return ' '.join(searchable_parts)

def extract_text_from_structured_data(structured_data: str) -> str:
    """
    Extract plain text from structured data (markdown, lists, etc.)
    
    Args:
        structured_data: Structured data string
        
    Returns:
        Plain text content
    """
    # Remove markdown formatting
    text = re.sub(r'#+\s*', '', structured_data)  # Headers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Code
    text = re.sub(r'^\s*[-*+]\s*', '', text, flags=re.MULTILINE)  # List markers
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)  # Numbered lists
    
    return text

def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from text for better searchability
    
    Args:
        text: Text to extract keywords from
        
    Returns:
        List of keywords
    """
    # Simple keyword extraction (can be enhanced with NLP libraries)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out common stop words
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'a', 'an', 'as', 'from', 'they', 'we', 'you', 'it', 'he', 'she', 'him', 'her', 'his', 'hers', 'its', 'our', 'your', 'their'}
    
    keywords = [word for word in words if word not in stop_words and len(word) > 3]
    
    # Count frequency and return most common
    from collections import Counter
    keyword_counts = Counter(keywords)
    
    return [word for word, count in keyword_counts.most_common(10)]

def extract_entities(text: str) -> List[str]:
    """
    Extract entities from text (simple implementation)
    
    Args:
        text: Text to extract entities from
        
    Returns:
        List of entities
    """
    # Simple entity extraction (can be enhanced with NER libraries)
    entities = []
    
    # Extract monetary amounts
    money_pattern = r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand))?'
    entities.extend(re.findall(money_pattern, text, re.IGNORECASE))
    
    # Extract percentages
    percent_pattern = r'\d+(?:\.\d+)?%'
    entities.extend(re.findall(percent_pattern, text))
    
    # Extract years
    year_pattern = r'\b(?:19|20)\d{2}\b'
    entities.extend(re.findall(year_pattern, text))
    
    # Extract quarters
    quarter_pattern = r'Q[1-4]\s*\d{4}'
    entities.extend(re.findall(quarter_pattern, text, re.IGNORECASE))
    
    return list(set(entities))

def save_rag_chunks(chunks: List[Dict[str, Any]], output_file: str, pdf_name: str) -> None:
    """
    Save RAG-optimized chunks to JSONL file
    
    Args:
        chunks: List of chunks
        output_file: Path to save the file
        pdf_name: Name of the PDF
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Create summary
    summary = {
        "pdf_name": pdf_name,
        "total_chunks": len(chunks),
        "chunk_types": {},
        "pages_covered": set(),
        "total_text_chunks": 0,
        "total_visual_chunks": 0
    }
    
    # Count chunk types and pages
    for chunk in chunks:
        chunk_type = chunk.get('metadata', {}).get('chunk_type', 'unknown')
        page = chunk.get('metadata', {}).get('page_number', 0)
        
        summary["chunk_types"][chunk_type] = summary["chunk_types"].get(chunk_type, 0) + 1
        summary["pages_covered"].add(page)
        
        if chunk_type == "text":
            summary["total_text_chunks"] += 1
        else:
            summary["total_visual_chunks"] += 1
    
    summary["pages_covered"] = sorted(list(summary["pages_covered"]))
    
    # Save JSONL file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write summary as first line
        f.write(json.dumps({"summary": summary}) + '\n')
        
        # Write each chunk as a separate line
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    print(f"RAG-optimized chunks saved to: {output_file}")
    print(f"Total chunks: {len(chunks)}")
    print(f"Text chunks: {summary['total_text_chunks']}")
    print(f"Visual chunks: {summary['total_visual_chunks']}")
    print(f"Chunk types: {summary['chunk_types']}")
    print(f"Pages covered: {summary['pages_covered']}")

def main():
    parser = argparse.ArgumentParser(description="RAG-optimized text and visual element blending")
    parser.add_argument("--text_file", type=str, required=True, help="Path to text extraction JSON file")
    parser.add_argument("--visual_file", type=str, required=True, help="Path to visual detection JSON file")
    parser.add_argument("--output_file", type=str, help="Output JSONL file path")
    
    args = parser.parse_args()
    
    # Load input files
    if not os.path.exists(args.text_file):
        print(f"Error: Text file not found: {args.text_file}")
        return
    
    if not os.path.exists(args.visual_file):
        print(f"Error: Visual file not found: {args.visual_file}")
        return
    
    with open(args.text_file, 'r', encoding='utf-8') as f:
        text_data = json.load(f)
    
    with open(args.visual_file, 'r', encoding='utf-8') as f:
        visual_data = json.load(f)
    
    # Determine output file
    if args.output_file:
        output_file = args.output_file
    else:
        pdf_name = text_data.get('pdf_name', 'unknown')
        output_file = f"{pdf_name}_rag_chunks.jsonl"
    
    # Create RAG-optimized chunks
    print("Creating RAG-optimized chunks...")
    chunks = create_rag_optimized_chunks(text_data, visual_data)
    
    if chunks:
        # Save results
        save_rag_chunks(chunks, output_file, text_data.get('pdf_name', 'unknown'))
        print("RAG optimization completed successfully!")
    else:
        print("No chunks to create")

if __name__ == "__main__":
    main()
