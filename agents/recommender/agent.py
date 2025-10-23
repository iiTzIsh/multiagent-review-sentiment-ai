"""
AI-Powered Recommendations Agent for Hotel Review Analysis
Uses Google Gemini LLM to generate business recommendations.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import Counter
import google.generativeai as genai
from utils.api_config import get_gemini_api_key

logger = logging.getLogger(__name__)


class ReviewRecommendationsAgent:
    """AI-powered agent for generating business recommendations using Google Gemini"""
    
    def __init__(self):
        self.agent_name = "ReviewRecommendationsAgent"
        self.model = None
        self.initialized = False
        
        try:
            self._initialize_gemini_model()
            self.initialized = True
            logger.info("[OK] Recommendations Agent initialized")
        except Exception as e:
            logger.error(f"[FAILED] Recommendations Agent initialization failed: {str(e)}")
            self.initialized = False

    def _initialize_gemini_model(self):
        """Initialize Google Gemini AI model"""
        try:
            api_key = get_gemini_api_key()
            
            if not api_key:
                raise ValueError("Gemini API key not found")
            
            genai.configure(api_key=api_key)
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1000,
            }
            
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config=generation_config
            )
            
            logger.info("Gemini model initialized successfully for recommendations generation")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise       