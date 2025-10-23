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