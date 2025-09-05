"""
Review Classifier Agent
Classifies hotel reviews as positive, negative, or neutral using HuggingFace models
"""

import json
import logging
from typing import Dict, List, Any
from crewai import Agent, Task
from crewai.tools import BaseTool
from ..base_agent import BaseAgent, HuggingFaceAPITool, parse_agent_response

logger = logging.getLogger('agents.classifier')


class SentimentClassificationTool(HuggingFaceAPITool):
    """Tool for sentiment classification using HuggingFace API"""
    
    name: str = "sentiment_classifier"
    description: str = "Classify text sentiment as positive, negative, or neutral"
    
    def __init__(self):
        super().__init__("cardiffnlp/twitter-roberta-base-sentiment-latest")
    
    def _run(self, text: str) -> str:
        """Run sentiment classification on the given text"""
        try:
            payload = {"inputs": text}
            result = self._make_api_request(payload)
            
            if isinstance(result, list) and len(result) > 0:
                # Get the highest confidence prediction
                predictions = result[0]
                best_prediction = max(predictions, key=lambda x: x['score'])
                
                # Map labels to our format
                label_mapping = {
                    'LABEL_0': 'negative',
                    'LABEL_1': 'neutral', 
                    'LABEL_2': 'positive',
                    'NEGATIVE': 'negative',
                    'NEUTRAL': 'neutral',
                    'POSITIVE': 'positive'
                }
                
                sentiment = label_mapping.get(best_prediction['label'].upper(), 'neutral')
                confidence = best_prediction['score']
                
                return f"Sentiment: {sentiment}, Confidence: {confidence:.2f}"
            
            return "Sentiment: neutral, Confidence: 0.50"
            
        except Exception as e:
            logger.error(f"Sentiment classification failed: {str(e)}")
            return "Sentiment: neutral, Confidence: 0.50"


class ReviewClassifierAgent(BaseAgent):
    """
    Agent responsible for classifying review sentiments
    """
    
    def __init__(self):
        super().__init__(
            name="Review Classifier",
            role="Sentiment Analysis Expert",
            goal="Accurately classify hotel review sentiments as positive, negative, or neutral",
            backstory="""You are an expert in natural language processing and sentiment analysis.
            You have years of experience analyzing customer feedback in the hospitality industry.
            Your task is to accurately classify the emotional tone of hotel reviews to help
            hotel managers understand customer satisfaction levels."""
        )
    
    def setup_tools(self) -> List[BaseTool]:
        """Setup tools for sentiment classification"""
        self.tools = [SentimentClassificationTool()]
        return self.tools
    
    def create_agent(self) -> Agent:
        """Create the CrewAI agent for sentiment classification"""
        tools = self.setup_tools()
        
        self.agent = Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=tools,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
        return self.agent
    
    def create_task(self, description: str, context: Dict[str, Any]) -> Task:
        """Create a sentiment classification task"""
        review = context.get('review', {})
        review_text = review.get('text', description)
        
        task_description = f"""
        Analyze the sentiment of the following hotel review and classify it as positive, negative, or neutral.
        
        Review Text: "{review_text}"
        
        Consider:
        - Overall emotional tone
        - Specific complaints or compliments
        - Language intensity
        - Context of hospitality industry
        
        Provide your classification with confidence level.
        """
        
        return Task(
            description=task_description,
            agent=self.agent,
            expected_output="Sentiment classification (positive/negative/neutral) with confidence score"
        )
    
    def classify_review(self, review_text: str) -> Dict[str, Any]:
        """
        Classify a single review and return structured result
        """
        try:
            result = self.execute_task(
                f"Classify sentiment of review: {review_text}",
                {'review': {'text': review_text}}
            )
            
            # Parse the result
            sentiment = parse_agent_response(result, 'sentiment')
            
            # Extract confidence if available
            confidence = 0.5
            if 'confidence' in result.lower():
                import re
                conf_match = re.search(r'confidence:\s*(\d+\.?\d*)', result.lower())
                if conf_match:
                    confidence = float(conf_match.group(1))
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'raw_result': result
            }
            
        except Exception as e:
            logger.error(f"Review classification failed: {str(e)}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'raw_result': str(e)
            }
    
    def batch_classify(self, reviews: List[str]) -> List[Dict[str, Any]]:
        """
        Classify multiple reviews efficiently
        """
        results = []
        for review_text in reviews:
            result = self.classify_review(review_text)
            results.append(result)
        
        return results
