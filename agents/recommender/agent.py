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
        
    
    def generate_recommendations(self, reviews_data: List[Dict], analysis_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate AI-powered business recommendations"""
        try:
            if not self.initialized:
                logger.warning("Recommendations Agent not properly initialized, using fallback")
                return self._get_fallback_recommendations(reviews_data)
            
            if not reviews_data:
                return {
                    'recommendations': ["No reviews available for analysis"],
                    'priority_breakdown': {'high': 0, 'medium': 0, 'low': 1},
                    'generated_by': self.agent_name,
                    'status': 'no_data'
                }
            
            logger.info(f"Generating AI recommendations for {len(reviews_data)} reviews")
        
            # Create analysis prompt
            prompt = self._create_prompt(reviews_data)
            
            # Generate recommendations using Gemini AI
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini, using fallback")
                return self._get_fallback_recommendations(reviews_data)
            
            # Parse AI response
            result = self._parse_response(response.text, reviews_data)
            
            logger.info("successfully")
            return result
        
        except Exception as e:
            logger.error(f"Failed to generate AI recommendations: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._get_fallback_recommendations(reviews_data)
        

    def _create_prompt(self, reviews_data: List[Dict]) -> str:
        """Create prompt for AI recommendation generation"""
        total_reviews = len(reviews_data)
        avg_score = sum(float(r.get('score', 3.0)) for r in reviews_data) / total_reviews if total_reviews > 0 else 3.0
        sentiment_counts = Counter(r.get('sentiment', 'neutral') for r in reviews_data)
        
        # Sample reviews for context
        sample_reviews = []
        for sentiment in ['negative', 'positive']:
            sentiment_reviews = [r for r in reviews_data if r.get('sentiment') == sentiment]
            if sentiment_reviews:
                sample_reviews.extend(sentiment_reviews[:2])

        prompt = f"""
You are a hotel business consultant. Analyze {total_reviews} hotel reviews and provide exactly 5 actionable business recommendations.

DATA:
- Average Rating: {avg_score:.1f}/5.0
- Sentiment: {dict(sentiment_counts)}

SAMPLE REVIEWS:
{chr(10).join([f"- [{r.get('sentiment', 'neutral').upper()}] {r.get('text', '')[:100]}..." for r in sample_reviews[:4]])}

IMPORTANT: Respond ONLY in this exact format (no other text):

HIGH PRIORITY:
- Specific actionable recommendation 1
- Specific actionable recommendation 2

MEDIUM PRIORITY:
- Specific actionable recommendation 3
- Specific actionable recommendation 4

LOW PRIORITY:
- Specific actionable recommendation 5
"""
        
        return prompt