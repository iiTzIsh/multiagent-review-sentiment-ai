"""
AI-Powered Summarizer Agent for Hotel Review Analysis
Uses Google Gemini for intelligent review summarization.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from collections import Counter
from crewai import Agent, Task
from crewai.tools import BaseTool
import google.generativeai as genai
from utils.api_config import get_gemini_api_key

logger = logging.getLogger('agents.summarizer')


class GeminiSummarizerTool(BaseTool):
    """AI-powered text summarization using Google Gemini"""
    
    name: str = "gemini_summarizer"
    description: str = "Generate intelligent summaries of hotel reviews using Google Gemini AI"
    
    def __init__(self):
        super().__init__()
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini model"""
        try:
            api_key = get_gemini_api_key()
            if api_key:
                genai.configure(api_key=api_key)
                object.__setattr__(self, '_gemini_model', genai.GenerativeModel('gemini-2.0-flash-exp'))
                logger.info("Gemini model initialized successfully for summarization")
            else:
                object.__setattr__(self, '_gemini_model', None)
                logger.error("Gemini API key not found")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            object.__setattr__(self, '_gemini_model', None)
    
    def _run(self, text: str, review_count: int = 0) -> str:
        """Generate AI-powered summary using Google Gemini"""
        try:
            if not hasattr(self, '_gemini_model') or not self._gemini_model:
                return self._fallback_summary(text)
            
            if not text or text.strip() == "":
                return "No review content available for summarization"
            
            prompt = f"""
            Analyze these {review_count} hotel reviews and provide a concise business summary:
            
            1. Overall guest satisfaction level
            2. Main positive aspects mentioned
            3. Common complaints or issues
            4. Key actionable insights for management
            
            Keep it professional and concise (2-3 paragraphs).
            
            Reviews: {text[:4000]}
            """
            
            response = self._gemini_model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return self._fallback_summary(text)
                
        except Exception as e:
            logger.error(f"Gemini summarization failed: {str(e)}")
            return self._fallback_summary(text)
    
    def _fallback_summary(self, text: str) -> str:
        """Simple fallback summary"""
        sentences = text.split('. ')[:3]
        fallback = '. '.join(sentences)
        return f"Summary: {fallback[:200]}..." if fallback else "No summary available"

class ReviewSummarizerAgent:
    """AI-powered review summarizer using Google Gemini"""
    
    def __init__(self):
        self.name = "ReviewSummarizer"
        self.role = "AI Review Summary Specialist"
        self.goal = "Generate intelligent summaries from hotel review collections"
        self.backstory = "Expert AI analyst specializing in hospitality feedback summarization"
        self.tools = [GeminiSummarizerTool()]
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
    
    def generate_summary(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive summary using AI analysis"""
        try:
            # Basic statistics
            sentiment_counts = Counter(review.get('sentiment', 'neutral') for review in reviews)
            scores = [review.get('score', 3.0) for review in reviews if isinstance(review.get('score'), (int, float))]
            avg_score = sum(scores) / len(scores) if scores else 3.0
            
            # Generate AI summary
            review_texts = [review.get('text', '') for review in reviews]
            combined_text = ' '.join(review_texts)
            
            summary_tool = GeminiSummarizerTool()
            summary_text = summary_tool._run(combined_text, len(reviews))
            
            # Generate insights
            insights = self._extract_insights(sentiment_counts, avg_score, len(reviews))
            recommendations = self._generate_recommendations(sentiment_counts, avg_score, len(reviews))
            
            return {
                'summary_text': summary_text,
                'total_reviews': len(reviews),
                'sentiment_distribution': dict(sentiment_counts),
                'average_score': round(avg_score, 1),
                'key_insights': insights,
                'recommendations': recommendations,
                'generated_by': self.name
            }
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return {
                'summary_text': 'Unable to generate summary due to processing error',
                'total_reviews': len(reviews),
                'sentiment_distribution': {'neutral': len(reviews)},
                'average_score': 3.0,
                'error': str(e),
                'generated_by': self.name
            }