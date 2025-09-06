'''Summary Agent '''

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