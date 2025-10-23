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