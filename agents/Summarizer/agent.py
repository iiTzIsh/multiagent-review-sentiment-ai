import json
import logging
from typing import Dict, List, Any
from collections import Counter
from crewai import Agent, Task
from crewai.tools import BaseTool
from ..base_agent import BaseAgent, HuggingFaceAPITool

logger = logging.getLogger('agents.summarizer')


class TextSummarizationTool(HuggingFaceAPITool):
    """Tool for text summarization using HuggingFace API"""
    
    name: str = "text_summarizer"
    description: str = "Generate concise summaries of hotel reviews"
    
    def __init__(self):
        super().__init__("facebook/bart-large-cnn")
    
    def _run(self, text: str, max_length: int = 150) -> str:
        """Generate summary of the given text"""
        try:
            payload = {
                "inputs": text,
                "parameters": {
                    "max_length": max_length,
                    "min_length": 50,
                    "do_sample": False
                }
            }
            result = self._make_api_request(payload)
            
            if isinstance(result, list) and len(result) > 0:
                summary = result[0].get('summary_text', text[:200])
                return f"Summary: {summary}"
            
            return f"Summary: {text[:200]}..."
            
        except Exception as e:
            logger.error(f"Text summarization failed: {str(e)}")
            return f"Summary: {text[:200]}..."


class KeywordExtractionTool(BaseTool):
    """Tool for extracting key themes and topics from reviews"""
    
    name: str = "keyword_extractor"
    description: str = "Extract key themes and topics from hotel reviews"
    
    def _run(self, reviews: List[str]) -> str:
        """Extract common keywords and themes"""
        try:
            # Simple keyword extraction based on frequency
            all_text = ' '.join(reviews).lower()
            
            # Hotel-specific keywords to look for
            hotel_keywords = [
                'room', 'service', 'staff', 'location', 'breakfast', 'wifi',
                'clean', 'dirty', 'comfortable', 'noisy', 'quiet', 'helpful',
                'rude', 'friendly', 'price', 'value', 'amenities', 'pool',
                'gym', 'restaurant', 'bar', 'view', 'bathroom', 'bed',
                'reception', 'check-in', 'check-out', 'parking'
            ]
            
            # Count keyword occurrences
            keyword_counts = {}
            for keyword in hotel_keywords:
                count = all_text.count(keyword)
                if count > 0:
                    keyword_counts[keyword] = count
            
            # Get top keywords
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            keywords_str = ', '.join([f"{word} ({count})" for word, count in top_keywords])
            return f"Key themes: {keywords_str}"
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {str(e)}")
            return "Key themes: service, room, staff, location"
        
class SummaryAgent(BaseAgent):
    """
    Agent responsible for generating review summaries
    """
    
    def __init__(self):
        super().__init__(
            name="Summary Agent",
            role="Content Summarization Expert",
            goal="Generate comprehensive yet concise summaries of hotel review collections",
            backstory="""You are an expert content analyst specializing in hospitality industry feedback.
            You excel at identifying patterns in customer reviews and creating actionable summaries
            that highlight the most important pros and cons. Your summaries help hotel managers
            quickly understand overall guest satisfaction and identify areas for improvement."""
        )
    
    def setup_tools(self) -> List[BaseTool]:
        """Setup tools for summarization"""
        self.tools = [TextSummarizationTool(), KeywordExtractionTool()]
        return self.tools
    
    def create_agent(self) -> Agent:
        """Create the CrewAI agent for summarization"""
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
        """Create a summarization task"""
        reviews = context.get('reviews', [])
        
        # Prepare review texts for analysis
        review_texts = []
        positive_reviews = []
        negative_reviews = []
        
        for review in reviews:
            text = review.get('text', '')
            sentiment = review.get('sentiment', 'neutral')
            
            review_texts.append(text)
            
            if sentiment == 'positive':
                positive_reviews.append(text)
            elif sentiment == 'negative':
                negative_reviews.append(text)
        
        task_description = f"""
        Analyze and summarize the following collection of {len(reviews)} hotel reviews.
        
        Create a comprehensive summary that includes:
        1. Overall sentiment trend
        2. Most common positive aspects (pros)
        3. Most common negative aspects (cons)
        4. Key themes and topics mentioned
        5. Actionable recommendations for hotel management
        
        Positive Reviews: {len(positive_reviews)}
        Negative Reviews: {len(negative_reviews)}
        Neutral Reviews: {len(review_texts) - len(positive_reviews) - len(negative_reviews)}
        
        Focus on identifying patterns and providing insights that would be valuable
        for hotel managers to improve their services.
        """
        
        return Task(
            description=task_description,
            agent=self.agent,
            expected_output="Structured summary with pros, cons, themes, and recommendations"
        )
    
    def generate_summary(self, reviews: List[Dict]) -> Dict[str, Any]:
        """
        Generate comprehensive summary of reviews
        """
        try:
            result = self.execute_task(
                "Generate comprehensive review summary",
                {'reviews': reviews}
            )
            
            # Analyze sentiment distribution
            sentiment_counts = Counter(review.get('sentiment', 'neutral') for review in reviews)
            
            # Calculate average score
            scores = [review.get('score', 3.0) for review in reviews if isinstance(review.get('score'), (int, float))]
            avg_score = sum(scores) / len(scores) if scores else 3.0
            
            # Extract common themes
            review_texts = [review.get('text', '') for review in reviews]
            
            return {
                'summary_text': result,
                'total_reviews': len(reviews),
                'sentiment_distribution': dict(sentiment_counts),
                'average_score': round(avg_score, 1),
                'score_range': {
                    'min': min(scores) if scores else 0,
                    'max': max(scores) if scores else 5
                },
                'key_insights': self._extract_insights(reviews),
                'recommendations': self._generate_recommendations(reviews)
            }
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return {
                'summary_text': 'Unable to generate summary',
                'total_reviews': len(reviews),
                'sentiment_distribution': {'neutral': len(reviews)},
                'average_score': 3.0,
                'error': str(e)
            }