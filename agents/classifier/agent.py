import json
import logging
import re
from typing import Dict, List, Any
from crewai import Agent, Task
from crewai.tools import BaseTool
import requests

logger = logging.getLogger('agents.classifier')


class SentimentClassificationTool(BaseTool):
       
    name: str = "sentiment_classifier"
    description: str = "Classify text sentiment as positive, negative, or neutral using HuggingFace RoBERTa model"
    
    def __init__(self):
        super().__init__()

        # Initialize model configuration
        self._model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self._api_url = f"https://api-inference.huggingface.co/models/{self._model_name}"
    
    def _run(self, text: str) -> str:

        api_key = self._get_api_key()
        if api_key:
            try:
                # Call HuggingFace RoBERTa model
                result = self._call_huggingface_api(text, api_key)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"HuggingFace API failed: {e}")
        
        # Minimal fallback 
        return self._minimal_fallback(text)
    
    def _get_api_key(self) -> str:
        import os
        return os.getenv('HUGGINGFACE_API_KEY', '')
    
    def _call_huggingface_api(self, text: str, api_key: str) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": text,
            "parameters": {"return_all_scores": True}
        }
        
        response = requests.post(self._api_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return self._process_ai_result(result)
        else:
            logger.warning(f"API returned status {response.status_code}")
            return None
    
    def _process_ai_result(self, result) -> str:
        # Process HuggingFace AI model response
        if isinstance(result, list) and len(result) > 0:
            scores = result[0] if isinstance(result[0], list) else result
            
            # Parse AI model labels
            sentiment_scores = {}
            for item in scores:
                label = item['label'].lower()
                score = item['score']
                
                # Handle different label formats
                if 'positive' in label or label == 'label_2':
                    sentiment_scores['positive'] = score
                elif 'negative' in label or label == 'label_0':
                    sentiment_scores['negative'] = score
                elif 'neutral' in label or label == 'label_1':
                    sentiment_scores['neutral'] = score
            
            # Return best sentiment with AI confidence
            if sentiment_scores:
                best_sentiment = max(sentiment_scores.items(), key=lambda x: x[1])
                return f"Sentiment: {best_sentiment[0]}, Confidence: {best_sentiment[1]:.2f}"
        
        return None
    
    def _minimal_fallback(self, text: str) -> str:
        # minimal fallback - only when AI completely fails
        text_lower = text.lower()
        
        # Only 2 strongest indicators each
        if any(word in text_lower for word in ['excellent', 'incredible']):
            return "Sentiment: positive, Confidence: 0.70"
        elif any(word in text_lower for word in ['terrible', 'awful']):
            return "Sentiment: negative, Confidence: 0.70"
        else:
            return "Sentiment: neutral, Confidence: 0.50"


class ReviewClassifierAgent:
    
    def __init__(self):

        # Agent Identity
        self.name = "ReviewClassifier"
        self.role = "Sentiment Analysis Expert"
        self.goal = "Accurately classify hotel review sentiments as positive, negative, or neutral"
        self.backstory = """You are an expert in natural language processing and sentiment analysis.
        You have years of experience analyzing customer feedback in the hospitality industry.
        Your task is to accurately classify the emotional tone of hotel reviews to help
        hotel managers understand customer satisfaction levels."""
        
        # CrewAI Agent Instance
        self.agent = None
        self.tools = []
        
        # Initialize the agent
        self._create_agent()
    

    def _create_agent(self) -> Agent:

        # Setup tools
        self.tools = [SentimentClassificationTool()]
        
        # Step 2: Create CrewAI Agent
        self.agent = Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            verbose=True,              # Show agent reasoning
            allow_delegation=False,    # This agent works independently
            max_iter=3                # Limit iterations for efficiency
        )
        
        return self.agent
    

    def create_task(self, review_text: str) -> Task:

        task_description = f"""
        Analyze the sentiment of the following hotel review and classify it as positive, negative, or neutral.
        
        Review Text: "{review_text}"
        
        Consider:
        - Overall emotional tone (happy, angry, disappointed, satisfied)
        - Specific complaints or compliments
        - Language intensity (very positive, slightly negative, etc.)
        - Context of hospitality industry
        
        Use the sentiment_classifier tool to get the classification.
        Provide your final answer in this format: "Sentiment: [positive/negative/neutral], Confidence: [0.0-1.0]"
        """
        
        return Task(
            description=task_description,
            agent=self.agent,
            expected_output="Sentiment classification (positive/negative/neutral) with confidence score"
        )
    
    def classify_review(self, review_text: str) -> Dict[str, Any]:

        try:
            # created HuggingFace tool
            tool = SentimentClassificationTool()
            result = tool._run(review_text)
            
            # Parse result from tool output
            result_text = result.lower()
            
            # Extract sentiment
            sentiment = 'neutral' 
            if 'positive' in result_text:
                sentiment = 'positive'
            elif 'negative' in result_text:
                sentiment = 'negative'
            
            # Extract confidence
            confidence = 0.5  
            conf_match = re.search(r'confidence:\s*(\d+\.?\d*)', result_text)
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
    
    # BATCH PROCESSING
    def batch_classify(self, reviews: List[str]) -> List[Dict[str, Any]]:

        results = []
        for review_text in reviews:
            result = self.classify_review(review_text)
            results.append(result)
        
        return results
