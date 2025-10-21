"""
AI-Powered Summarizer Agent for Hotel Review Analysis
Uses Google Gemini for intelligent review summarization.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from collections import Counter
from crewai import Agent, Task
from crewai.tools import BaseTool
import google.generativeai as genai
from utils.api_config import get_gemini_api_key

logger = logging.getLogger('agents.summarizer')


class GeminiSummarizerTool(BaseTool):
    """AI-powered text summarization using Google Gemini"""
    
    name: str = "gemini_summarizer"
    description: str = "Generate intelligent summaries of hotel reviews using Google Gemini AI"
    
    def __init__(self):
        super().__init__()
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini model"""
        try:
            api_key = get_gemini_api_key()
            if api_key:
                genai.configure(api_key=api_key)
                object.__setattr__(self, '_gemini_model', genai.GenerativeModel('gemini-2.0-flash-exp'))
                logger.info("Gemini model initialized successfully for summarization")
            else:
                object.__setattr__(self, '_gemini_model', None)
                logger.error("Gemini API key not found")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            object.__setattr__(self, '_gemini_model', None)
    
    def _run(self, text: str, review_count: int = 0) -> str:
        """Generate AI-powered summary using Google Gemini"""
        try:
            if not hasattr(self, '_gemini_model') or not self._gemini_model:
                return self._fallback_summary(text)
            
            if not text or text.strip() == "":
                return "No review content available for summarization"
            
            prompt = f"""
            Analyze these {review_count} hotel reviews and provide a concise business summary:
            
            1. Overall guest satisfaction level
            2. Main positive aspects mentioned
            3. Common complaints or issues
            4. Key actionable insights for management
            
            Keep it professional and concise (2-3 paragraphs).
            
            Reviews: {text[:4000]}
            """
            
            response = self._gemini_model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return self._fallback_summary(text)
                
        except Exception as e:
            logger.error(f"Gemini summarization failed: {str(e)}")
            return self._fallback_summary(text)
    
    def _fallback_summary(self, text: str) -> str:
        """Simple fallback summary"""
        sentences = text.split('. ')[:3]
        fallback = '. '.join(sentences)
        return f"Summary: {fallback[:200]}..." if fallback else "No summary available"
