import json
import logging
import re
from typing import Dict, List, Any
from collections import Counter
from crewai import Agent, Task
from crewai.tools import BaseTool

logger = logging.getLogger('agents.summarizer')


class TextSummarizationTool(BaseTool):
    """Tool for text summarization using rule-based approach"""
    
    name: str = "text_summarizer"
    description: str = "Generate concise summaries of hotel reviews"
    
    def _run(self, text: str, max_length: int = 150) -> str:
        """Generate summary of the given text using rule-based approach"""
        try:
            # Simple extractive summarization
            sentences = text.split('. ')
            if len(sentences) <= 3:
                return text
            
            # Score sentences based on keywords
            hotel_keywords = [
                'room', 'service', 'staff', 'location', 'breakfast', 'wifi',
                'clean', 'comfortable', 'friendly', 'helpful', 'excellent',
                'terrible', 'disappointed', 'amazing', 'perfect', 'worst'
            ]
            
            sentence_scores = []
            for sentence in sentences:
                score = 0
                sentence_lower = sentence.lower()
                for keyword in hotel_keywords:
                    if keyword in sentence_lower:
                        score += 1
                sentence_scores.append((sentence, score))
            
            # Get top sentences
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [sent[0] for sent in sentence_scores[:3]]
            
            summary = '. '.join(top_sentences)
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            
            return f"Summary: {summary}"
            
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


class ModelSummarizationTool(BaseTool):
    """Tool for text summarization using Hugging Face models"""
    
    name: str = "hf_text_summarizer"
    description: str = "Generate abstractive summaries using Hugging Face transformer models"
    
    def __init__(self):
        super().__init__()
        # Load Hugging Face summarization pipeline
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    def _run(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        try:
            if not text.strip():
                return "Summary: (no content provided)"
            
            summary = self.summarizer(
                text, 
                max_length=max_length, 
                min_length=min_length, 
                do_sample=False
            )
            return f"Summary: {summary[0]['summary_text']}"
        
        except Exception as e:
            logger.error(f"Hugging Face summarization failed: {str(e)}")
            return "Summary: Unable to generate model-based summary"


class ReviewSummarizerAgent:
    """
    CREWAI REVIEW SUMMARIZER AGENT
    
    WELL-DEFINED ROLE:
    - Primary Role: Review Summary Expert for Hotel Reviews
    - Specific Responsibility: Generate comprehensive summaries from analyzed review collections
    - Domain Expertise: Hospitality feedback analysis and insight generation
    - Communication: Uses CrewAI framework for task execution
    
    AGENT CAPABILITIES:
    - Multi-review summary generation
    - Sentiment distribution analysis
    - Key theme extraction
    - Actionable recommendations
    """
    
    def __init__(self):
        """
        Initialize the Review Summarizer Agent
        """
        # Agent Identity
        self.name = "ReviewSummarizer"
        self.role = "Review Summary Specialist"
        self.goal = "Generate comprehensive summaries and insights from hotel review collections"
        self.backstory = """You are an expert content analyst specializing in hospitality industry feedback.
        You excel at identifying patterns in customer reviews and creating actionable summaries
        that highlight the most important pros and cons. Your summaries help hotel managers
        quickly understand overall guest satisfaction and identify areas for improvement."""
        
        # CrewAI Agent Instance
        self.agent = None
        self.tools = []
        
        # Initialize the agent
        self._create_agent()
    
    def _create_agent(self) -> Agent:
        """
        CREATE CREWAI AGENT
        """
        # Setup tools
        self.tools = [TextSummarizationTool(), KeywordExtractionTool()]
        
        # Create CrewAI Agent
        self.agent = Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
        return self.agent
    
    def generate_summary(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        MAIN SUMMARIZATION FUNCTION
        
        Generate comprehensive summary using rule-based analysis
        """
        try:
            # Analyze sentiment distribution
            sentiment_counts = Counter(review.get('sentiment', 'neutral') for review in reviews)
            
            # Calculate scores
            scores = [review.get('score', 3.0) for review in reviews if isinstance(review.get('score'), (int, float))]
            avg_score = sum(scores) / len(scores) if scores else 3.0
            
            # Extract themes using tools
            review_texts = [review.get('text', '') for review in reviews]
            combined_text = ' '.join(review_texts)
            
            # Use tools for analysis
            summary_tool = TextSummarizationTool()
            keyword_tool = KeywordExtractionTool()
            
            summary_text = summary_tool._run(combined_text)
            key_themes = keyword_tool._run(review_texts)
            
            # Generate insights and recommendations
            insights = self._extract_insights(reviews, sentiment_counts, avg_score)
            recommendations = self._generate_recommendations(reviews, sentiment_counts, avg_score)
            
            return {
                'summary_text': summary_text,
                'total_reviews': len(reviews),
                'sentiment_distribution': dict(sentiment_counts),
                'average_score': round(avg_score, 1),
                'score_range': {
                    'min': min(scores) if scores else 0,
                    'max': max(scores) if scores else 5
                },
                'key_themes': key_themes,
                'key_insights': insights,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return {
                'summary_text': 'Unable to generate summary due to processing error',
                'total_reviews': len(reviews),
                'sentiment_distribution': {'neutral': len(reviews)},
                'average_score': 3.0,
                'error': str(e)
            }
    
    def _extract_insights(self, reviews: List[Dict], sentiment_counts: Counter, avg_score: float) -> List[str]:
        """Extract key insights from reviews"""
        insights = []
        total = len(reviews)
        
        if total > 0:
            # Sentiment insights
            pos_percent = (sentiment_counts.get('positive', 0) / total) * 100
            neg_percent = (sentiment_counts.get('negative', 0) / total) * 100
            
            insights.append(f"{pos_percent:.1f}% of reviews are positive")
            insights.append(f"{neg_percent:.1f}% of reviews are negative")
            
            # Score insights
            if avg_score >= 4.0:
                insights.append("Overall customer satisfaction is high")
            elif avg_score <= 2.0:
                insights.append("Customer satisfaction needs immediate improvement")
            else:
                insights.append("Customer satisfaction is moderate with room for improvement")
        
        return insights
    
    def _generate_recommendations(self, reviews: List[Dict], sentiment_counts: Counter, avg_score: float) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        total = len(reviews)
        
        if total == 0:
            return ["No reviews available for analysis"]
        
        negative_ratio = sentiment_counts.get('negative', 0) / total
        
        # Score-based recommendations
        if avg_score < 2.5:
            recommendations.append("URGENT: Implement immediate service improvement plan")
        elif avg_score < 3.5:
            recommendations.append("Focus on addressing common customer complaints")
        elif avg_score >= 4.5:
            recommendations.append("Maintain excellent service standards")
        
        # Sentiment-based recommendations
        if negative_ratio > 0.3:
            recommendations.append("Prioritize negative review response and resolution")
        
        # General recommendations
        recommendations.extend([
            "Monitor review trends weekly for early issue detection",
            "Respond to all reviews promptly and professionally"
        ])
        
        return recommendations