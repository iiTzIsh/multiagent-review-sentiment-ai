"""
Sentiment Classification Agent for Hotel Review Analysis
Uses HuggingFace RoBERTa model for sentiment analysis.
"""

import json
import logging
import os
import re
from typing import Dict, Any, List
from crewai import Agent, Task
from crewai.tools import BaseTool
import requests

logger = logging.getLogger('agents.classifier')


class SentimentClassificationTool(BaseTool):
    name: str = "sentiment_classifier"
    description: str = "Classify text sentiment as positive, negative, or neutral"
    
    def __init__(self):
        super().__init__()
        self._api_url = "https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment-latest"
        self._api_key = os.getenv('HUGGINGFACE_API_KEY', '')

    def _run(self, text: str) -> str:
        """Classify sentiment using HuggingFace RoBERTa model"""
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            payload = {"inputs": text}
            
            response = requests.post(self._api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return self._process_result(result)
            
        except Exception as e:
            logger.error(f"Sentiment classification error: {str(e)}")
        
        return self._fallback_classification(text)

    def _process_result(self, result) -> str:
        """Process AI model result"""
        try:
            if result and len(result) > 0:
                predictions = result[0] if isinstance(result[0], list) else result
                best_prediction = max(predictions, key=lambda x: x.get('score', 0))
                
                # Map RoBERTa labels
                label_mapping = {
                    'LABEL_0': 'negative',
                    'LABEL_1': 'neutral',   
                    'LABEL_2': 'positive'
                }
                
                sentiment = label_mapping.get(best_prediction.get('label', 'neutral'), 'neutral')
                confidence = best_prediction.get('score', 0.5)
                
                return f"Sentiment: {sentiment}, Confidence: {confidence:.3f}"
        except Exception:
            pass
        
        return "Sentiment: neutral, Confidence: 0.5"

    def _fallback_classification(self, text: str) -> str:
        """Simple keyword-based fallback"""
        text_lower = text.lower()
        
        positive_words = ['good', 'great', 'excellent', 'love', 'perfect', 'amazing']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'worst']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "Sentiment: positive, Confidence: 0.6"
        elif negative_count > positive_count:
            return "Sentiment: negative, Confidence: 0.6"
        else:
            return "Sentiment: neutral, Confidence: 0.5"


class ReviewClassifierAgent:
    def __init__(self):
        self.name = "ReviewClassifier"
        self.role = "Sentiment Analysis Expert"
        self.goal = "Classify hotel review sentiments"
        self.backstory = "Expert in sentiment analysis for hospitality industry"
        self.tools = [SentimentClassificationTool()]
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
    
    def create_task(self, review_text: str) -> Task:
        task_description = f"""
        Classify the sentiment of this hotel review: "{review_text}"
        Use the sentiment_classifier tool and provide the result.
        """
        
        return Task(
            description=task_description,
            agent=self.agent,
            expected_output="Sentiment classification with confidence score"
        )
    
    def classify_review(self, review_text: str) -> Dict[str, Any]:
        """Direct classification without CrewAI workflow"""
        try:
            tool = SentimentClassificationTool()
            result = tool._run(review_text)
            
            # Parse result
            sentiment_match = re.search(r'Sentiment:\s*(\w+)', result)
            confidence_match = re.search(r'Confidence:\s*(\d+\.?\d*)', result)
            
            sentiment = sentiment_match.group(1) if sentiment_match else 'neutral'
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'raw_result': result
            }
            
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'raw_result': 'Error occurred during classification'
            }

    def batch_classify(self, reviews: List[str]) -> List[Dict[str, Any]]:
        """Classify multiple reviews"""
        return [self.classify_review(review) for review in reviews]