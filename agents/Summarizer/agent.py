import json
import logging
from typing import Dict, List, Any
from collections import Counter
from crewai import Agent, Task
from crewai.tools import BaseTool
from ..base_agent import BaseAgent, HuggingFaceAPITool

logger = logging.getLogger('agents.summarizer')


class TextSummarizationTool(HuggingFaceAPITool):
    """Tool for text summarization using HuggingFace API"""
    
    name: str = "text_summarizer"
    description: str = "Generate concise summaries of hotel reviews"
    
    def __init__(self):
        super().__init__("facebook/bart-large-cnn")
    
    def _run(self, text: str, max_length: int = 150) -> str:
        """Generate summary of the given text"""
        try:
            payload = {
                "inputs": text,
                "parameters": {
                    "max_length": max_length,
                    "min_length": 50,
                    "do_sample": False
                }
            }
            result = self._make_api_request(payload)
            
            if isinstance(result, list) and len(result) > 0:
                summary = result[0].get('summary_text', text[:200])
                return f"Summary: {summary}"
            
            return f"Summary: {text[:200]}..."
            
        except Exception as e:
            logger.error(f"Text summarization failed: {str(e)}")
            return f"Summary: {text[:200]}..."


class KeywordExtractionTool(BaseTool):
    """Tool for extracting key themes and topics from reviews"""
    
    name: str = "keyword_extractor"
    description: str = "Extract key themes and topics from hotel reviews"
    
    def _run(self, reviews: List[str]) -> str:
        """Extract common keywords and themes"""
        try:
            # Simple keyword extraction based on frequency
            all_text = ' '.join(reviews).lower()
            
            # Hotel-specific keywords to look for
            hotel_keywords = [
                'room', 'service', 'staff', 'location', 'breakfast', 'wifi',
                'clean', 'dirty', 'comfortable', 'noisy', 'quiet', 'helpful',
                'rude', 'friendly', 'price', 'value', 'amenities', 'pool',
                'gym', 'restaurant', 'bar', 'view', 'bathroom', 'bed',
                'reception', 'check-in', 'check-out', 'parking'
            ]
            
            # Count keyword occurrences
            keyword_counts = {}
            for keyword in hotel_keywords:
                count = all_text.count(keyword)
                if count > 0:
                    keyword_counts[keyword] = count
            
            # Get top keywords
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            keywords_str = ', '.join([f"{word} ({count})" for word, count in top_keywords])
            return f"Key themes: {keywords_str}"
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {str(e)}")
            return "Key themes: service, room, staff, location"