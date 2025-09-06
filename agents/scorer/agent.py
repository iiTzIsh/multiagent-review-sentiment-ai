"""
Sentiment Scorer Agent
Assigns numerical scores (0-5) to hotel reviews based on sentiment analysis
"""

import json
import logging
import re
from typing import Dict, List, Any
from crewai import Agent, Task
from crewai.tools import BaseTool
from ..base_agent import BaseAgent, HuggingFaceAPITool, parse_agent_response

logger = logging.getLogger('agents.scorer')



class SentimentScoringTool(HuggingFaceAPITool):
    """Tool for generating numerical sentiment scores"""
    
    name: str = "sentiment_scorer"
    description: str = "Generate numerical sentiment scores from 0-5 based on text analysis"
    
    def __init__(self):
        super().__init__("nlptown/bert-base-multilingual-uncased-sentiment")
    
    def _run(self, text: str, sentiment: str = None) -> str:
        """Generate sentiment score for the given text"""
        try:
            payload = {"inputs": text}
            result = self._make_api_request(payload)
            
            if isinstance(result, list) and len(result) > 0:
                predictions = result[0]
                
                # Calculate weighted score based on predictions
                total_score = 0
                for pred in predictions:
                    label = pred['label']
                    score = pred['score']
                    
                    
            # Fallback based on sentiment if provided
            if sentiment:
                sentiment_scores = {
                    'positive': 4.0,
                    'neutral': 3.0,
                    'negative': 2.0
                }
                score = sentiment_scores.get(sentiment.lower(), 3.0)
                return f"Score: {score:.1f}"
            
            return "Score: 3.0"
            
        except Exception as e:
            logger.error(f"Sentiment scoring failed: {str(e)}")
            return "Score: 3.0"


