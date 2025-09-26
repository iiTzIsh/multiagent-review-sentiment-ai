
import json
import logging
import re
from typing import Dict, List, Any
from crewai import Agent, Task
from crewai.tools import BaseTool
import requests

logger = logging.getLogger('agents.scorer')



class SentimentScoringTool(BaseTool):
 
    name: str = "sentiment_scorer"
    description: str = "Score hotel reviews from 0-5 using HuggingFace sentiment analysis model"
    
    def __init__(self):
        super().__init__()
        # Initialize HuggingFace model configuration for scoring
        self._model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
        # Note: In production, API key should be in Django settings
        self._api_url = f"https://api-inference.huggingface.co/models/{self._model_name}"
    
    def _run(self, text: str, sentiment: str = None) -> str:
        """
        CORE FUNCTION: Score review using HuggingFace BERT sentiment model
        Uses real AI for accurate 1-5 scoring based on sentiment analysis
        """
        # Step 1: Try real AI first
        api_key = self._get_api_key()
        if api_key:
            try:
                result = self._call_huggingface_api(text, api_key)
                if result:
                    return result
            except Exception as e:
                logger.error(f"HuggingFace sentiment scoring failed: {e}")
        
        # Step 2: Intelligent fallback scoring
        return self._intelligent_fallback_scoring(text, sentiment)
    
    def _get_api_key(self) -> str:
        """Get HuggingFace API key from environment"""
        import os
        return os.getenv('HUGGINGFACE_API_KEY', '')
    
    def _call_huggingface_api(self, text: str, api_key: str) -> str:
        """Call real HuggingFace BERT sentiment scoring model"""
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
            return self._process_scoring_result(result)
        else:
            logger.warning(f"Scoring API returned status {response.status_code}")
            return None
    
    def _process_scoring_result(self, result) -> str:
        """Process HuggingFace BERT model response for scoring"""
        if isinstance(result, list) and len(result) > 0:
            scores = result[0] if isinstance(result[0], list) else result
            
            # Calculate weighted score based on sentiment probabilities
            total_score = 0.0
            for item in scores:
                label = item['label']
                probability = item['score']
                
                # Map sentiment labels to numerical scores
                if 'LABEL_0' in label or '1' in label:  # Very negative
                    total_score += probability * 1.0
                elif 'LABEL_1' in label or '2' in label:  # Negative
                    total_score += probability * 2.0
                elif 'LABEL_2' in label or '3' in label:  # Neutral
                    total_score += probability * 3.0
                elif 'LABEL_3' in label or '4' in label:  # Positive
                    total_score += probability * 4.0
                elif 'LABEL_4' in label or '5' in label:  # Very positive
                    total_score += probability * 5.0
            
            # Ensure score is within valid range
            final_score = max(1.0, min(5.0, total_score))
            return f"Score: {final_score:.1f}"
        
        return None
    
    def _intelligent_fallback_scoring(self, text: str, sentiment: str = None) -> str:
        """Intelligent fallback scoring when API unavailable"""
        text_lower = text.lower()
        
        # Enhanced scoring indicators with HuggingFace-like weights
        positive_indicators = {
            # Very strong positive (5.0 score indicators)
            'excellent': 5.0, 'amazing': 5.0, 'perfect': 5.0, 'outstanding': 5.0,
            'exceptional': 5.0, 'incredible': 5.0, 'phenomenal': 5.0,
            
            # Strong positive (4.0 score indicators)
            'wonderful': 4.0, 'great': 4.0, 'fantastic': 4.0, 'superb': 4.0,
            'brilliant': 4.0, 'awesome': 4.0, 'beautiful': 4.0,
            
            # Moderate positive (3.5 score indicators)
            'good': 3.5, 'nice': 3.5, 'pleasant': 3.5, 'comfortable': 3.5,
            'helpful': 3.5, 'friendly': 3.5, 'recommend': 3.5,
            
            # Light positive (3.0 score indicators)
            'clean': 3.0, 'decent': 3.0, 'satisfactory': 3.0, 'adequate': 3.0
        }
        
        negative_indicators = {
            # Very strong negative (1.0 score indicators)
            'terrible': 1.0, 'horrible': 1.0, 'awful': 1.0, 'disgusting': 1.0,
            'appalling': 1.0, 'unacceptable': 1.0, 'worst': 1.0,
            
            # Strong negative (2.0 score indicators)
            'bad': 2.0, 'poor': 2.0, 'dirty': 2.0, 'rude': 2.0,
            'disappointed': 2.0, 'unsatisfied': 2.0,
            
            # Moderate negative (2.5 score indicators)
            'disappointing': 2.5, 'uncomfortable': 2.5, 'noisy': 2.5,
            'overpriced': 2.5, 'expensive': 2.5
        }
        
        # Find strongest indicators
        max_positive = 0
        max_negative = 5.0
        
        for word, score in positive_indicators.items():
            if word in text_lower:
                max_positive = max(max_positive, score)
        
        for word, score in negative_indicators.items():
            if word in text_lower:
                max_negative = min(max_negative, score)
        
        # Determine final score based on strongest indicators
        if max_positive > 0 and max_negative < 5.0:
            # Both positive and negative found, average with positive bias
            final_score = (max_positive + max_negative) / 2
        elif max_positive > 0:
            # Only positive found
            final_score = max_positive
        elif max_negative < 5.0:
            # Only negative found
            final_score = max_negative
        else:
            # No strong indicators, neutral
            final_score = 3.0
        
        # Apply sentiment boost if provided
        if sentiment:
            if sentiment.lower() == 'positive' and final_score < 3.5:
                final_score = min(4.0, final_score + 0.5)
            elif sentiment.lower() == 'negative' and final_score > 2.5:
                final_score = max(2.0, final_score - 0.5)
        
        # Ensure score is in valid range
        final_score = max(1.0, min(5.0, final_score))
        
        return f"Score: {final_score:.1f}"


class ReviewScorerAgent:
    
    def __init__(self):
        
        # Agent Identity
        self.name = "ReviewScorer"
        self.role = "Review Scoring Specialist"
        self.goal = "Accurately assign numerical scores (0-5) to hotel reviews based on sentiment analysis"
        self.backstory = """You are an expert in converting qualitative customer feedback 
        into quantitative metrics. You have years of experience in the hospitality industry
        understanding how customer emotions translate to satisfaction scores.
        Your task is to provide consistent, fair numerical scores that help
        hotel managers track satisfaction trends and identify areas for improvement."""
        
        # INstialilize agent and  instance
        self.agent = None
        self.tools = []
        self._create_agent()
    
    def _create_agent(self) -> Agent:
        
        # Step 1: Setup tools
        self.tools = [SentimentScoringTool()]
        
        # Step 2: Create CrewAI Agent
        self.agent = Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            verbose=True,              # agent reasoning
            allow_delegation=False,    # agent works independently
            max_iter=3                # Limit iterations for efficiency
        )
        
        return self.agent
    
    def create_task(self, review_text: str, sentiment: str = None) -> Task:
       
        task_description = f"""
        Assign a numerical score from 0.0 to 5.0 for the following hotel review based on its content and sentiment.
        
        Review Text: "{review_text}"
        Detected Sentiment: {sentiment or 'Not provided'}
        
        Scoring Guidelines:
        - 0.0-1.0: Very negative (major problems, angry customers)
        - 1.0-2.0: Negative (disappointed, unsatisfied)
        - 2.0-3.0: Neutral/Mixed (average experience)
        - 3.0-4.0: Positive (satisfied, good experience)
        - 4.0-5.0: Very positive (delighted, exceptional)
        
        Consider:
        - Severity of complaints or praise
        - Specific service mentions (staff, cleanliness, amenities)
        - Overall customer satisfaction level
        - Language intensity and emotional tone
        
        Use the sentiment_scorer tool to get the numerical score.
        Provide your final answer in this format: "Score: [0.0-5.0]"
        """
        
        return Task(
            description=task_description,
            agent=self.agent,
            expected_output="Numerical score from 0.0 to 5.0"
        )
    
    def score_review(self, review_text: str, sentiment: str = None) -> Dict[str, Any]:
        
        try:
            # Step 1: Use scoring tool directly
            tool = SentimentScoringTool()
            result = tool._run(review_text, sentiment)
            
            # Step 2: Parse result from tool output
            result_text = result.lower()
            
            # Extract score
            score = 3.0  # default
            score_match = re.search(r'score:\s*(\d+\.?\d*)', result_text)
            if score_match:
                score = float(score_match.group(1))
            
            return {
                'score': score,
                'sentiment': sentiment or 'neutral',
                'raw_result': result
            }
            
        except Exception as e:
            logger.error(f"Review scoring failed: {str(e)}")
            return {
                'score': 3.0,
                'sentiment': sentiment or 'neutral',
                'raw_result': str(e)
            }
    
    def batch_score(self, reviews_with_sentiment: List[Dict]) -> List[Dict[str, Any]]:
        
        results = []
        for review_data in reviews_with_sentiment:
            review_text = review_data.get('text', '')
            sentiment = review_data.get('sentiment', '')
            
            result = self.score_review(review_text, sentiment)
            results.append(result)
        
        return results

