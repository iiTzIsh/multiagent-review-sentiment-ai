"""
Sentiment Scoring Agent for Hotel Review Analysis
Uses HuggingFace BERT model for review scoring.
"""

import json
import logging
import os
import re
from typing import Dict, Any, List
from crewai import Agent, Task
from crewai.tools import BaseTool
import requests

logger = logging.getLogger('agents.scorer')


class SentimentScoringTool(BaseTool):
    name: str = "sentiment_scorer"
    description: str = "Score hotel reviews from 1-5 using sentiment analysis"
    
    def __init__(self):
        super().__init__()
        self._api_url = "https://api-inference.huggingface.co/models/nlptown/bert-base-multilingual-uncased-sentiment"
        self._api_key = os.getenv('HUGGINGFACE_API_KEY', '')

    def _run(self, text: str, sentiment: str = None) -> str:
        """Score review using HuggingFace BERT model"""
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            payload = {"inputs": text}
            
            response = requests.post(self._api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return self._process_result(result)
                
        except Exception as e:
            logger.error(f"Scoring error: {str(e)}")
        
        return self._fallback_scoring(text, sentiment)

    def _process_result(self, result) -> str:
        """Process AI model result"""
        try:
            if result and len(result) > 0:
                scores = result[0] if isinstance(result[0], list) else result
                
                # Calculate weighted score
                total_score = 0.0
                for item in scores:
                    label = item['label']
                    probability = item['score']
                    
                    # Map labels to scores (1-5 scale)
                    if 'LABEL_0' in label:  # 1 star
                        total_score += probability * 1.0
                    elif 'LABEL_1' in label:  # 2 stars
                        total_score += probability * 2.0
                    elif 'LABEL_2' in label:  # 3 stars
                        total_score += probability * 3.0
                    elif 'LABEL_3' in label:  # 4 stars
                        total_score += probability * 4.0
                    elif 'LABEL_4' in label:  # 5 stars
                        total_score += probability * 5.0
                
                final_score = max(1.0, min(5.0, total_score))
                return f"Score: {final_score:.1f}"
        except Exception:
            pass
        
        return "Score: 3.0"

    def _fallback_scoring(self, text: str, sentiment: str = None) -> str:
        """Simple keyword-based scoring fallback"""
        text_lower = text.lower()
        
        # Basic scoring keywords
        excellent_words = ['excellent', 'amazing', 'perfect', 'outstanding']
        good_words = ['good', 'great', 'wonderful', 'nice']
        bad_words = ['bad', 'poor', 'terrible', 'awful']
        horrible_words = ['horrible', 'disgusting', 'worst']
        
        if any(word in text_lower for word in excellent_words):
            score = 5.0
        elif any(word in text_lower for word in good_words):
            score = 4.0
        elif any(word in text_lower for word in horrible_words):
            score = 1.0
        elif any(word in text_lower for word in bad_words):
            score = 2.0
        else:
            score = 3.0
        
        # Apply sentiment adjustment
        if sentiment:
            if sentiment.lower() == 'positive' and score < 3.5:
                score = min(4.0, score + 0.5)
            elif sentiment.lower() == 'negative' and score > 2.5:
                score = max(2.0, score - 0.5)
        
        return f"Score: {score:.1f}"


class ReviewScorerAgent:
    def __init__(self):
        self.name = "ReviewScorer"
        self.role = "Review Scoring Specialist"
        self.goal = "Assign numerical scores (1-5) to hotel reviews"
        self.backstory = "Expert in converting customer feedback into satisfaction scores"
        self.tools = [SentimentScoringTool()]
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            verbose=False,
            allow_delegation=False,
            max_iter=2
        )
    
    def create_task(self, review_text: str, sentiment: str = None) -> Task:
        task_description = f"""
        Score this hotel review from 1-5: "{review_text}"
        Sentiment: {sentiment or 'Not provided'}
        Use the sentiment_scorer tool and provide the score.
        """
        
        return Task(
            description=task_description,
            agent=self.agent,
            expected_output="Numerical score from 1.0 to 5.0"
        )
    
    def score_review(self, review_text: str, sentiment: str = None) -> Dict[str, Any]:
        """Direct scoring without CrewAI workflow"""
        try:
            tool = SentimentScoringTool()
            result = tool._run(review_text, sentiment)
            
            # Parse score
            score_match = re.search(r'Score:\s*(\d+\.?\d*)', result)
            score = float(score_match.group(1)) if score_match else 3.0
            
            return {
                'score': score,
                'sentiment': sentiment or 'neutral',
                'raw_result': result
            }
            
        except Exception as e:
            logger.error(f"Scoring failed: {str(e)}")
            return {
                'score': 3.0,
                'sentiment': sentiment or 'neutral',
                'raw_result': 'Error occurred during scoring'
            }

    def batch_score(self, reviews_with_sentiment: List[Dict]) -> List[Dict[str, Any]]:
        """Score multiple reviews"""
        return [self.score_review(review.get('text', ''), review.get('sentiment', '')) 
                for review in reviews_with_sentiment]