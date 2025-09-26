"""
Review Search Agent - CrewAI Implementation
Search and filter hotel reviews based on various criteria

AGENT ROLE: Review Search Expert
- Well-defined role: Search and retrieve hotel reviews based on multiple criteria
- Clear responsibility: Filter reviews by sentiment, score range, keywords, and date
- Communication: Uses CrewAI framework for task execution and tool integration
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from crewai import Agent, Task
from crewai.tools import BaseTool

logger = logging.getLogger('agents.searcher')


class ReviewFilterTool(BaseTool):
    """
    Review Filtering Tool for CrewAI
    
    PURPOSE: Filter reviews based on sentiment, score, keywords, and other criteria
    INPUTS: Review collection and search criteria
    OUTPUT: Filtered reviews matching the specified criteria
    """
    
    name: str = "review_filter"
    description: str = "Filter hotel reviews based on sentiment, score range, keywords, and date criteria"
    
    def _run(self, reviews_json: str, criteria: str) -> str:
        """
        CORE FILTERING FUNCTION
        
        Filter reviews based on provided criteria
        
        Filtering Logic:
        - Sentiment filtering (positive, negative, neutral)
        - Score range filtering (min/max scores)
        - Keyword search in review text
        - Date range filtering if dates are available
        """
        try:
            # Parse inputs
            reviews = json.loads(reviews_json) if isinstance(reviews_json, str) else reviews_json
            search_criteria = json.loads(criteria) if isinstance(criteria, str) else criteria
            
            filtered_reviews = []
            
            for review in reviews:
                if self._matches_criteria(review, search_criteria):
                    filtered_reviews.append(review)
            
            return json.dumps({
                'filtered_reviews': filtered_reviews,
                'total_found': len(filtered_reviews),
                'total_searched': len(reviews)
            })
            
        except Exception as e:
            logger.error(f"Review filtering failed: {str(e)}")
            return json.dumps({
                'filtered_reviews': [],
                'total_found': 0,
                'total_searched': 0,
                'error': str(e)
            })
    
    def _matches_criteria(self, review: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if a review matches the search criteria"""
        
        # Sentiment filtering
        if 'sentiment' in criteria and criteria['sentiment']:
            review_sentiment = review.get('sentiment', '').lower()
            target_sentiment = criteria['sentiment'].lower()
            if review_sentiment != target_sentiment:
                return False
        
        # Score range filtering
        if 'min_score' in criteria and criteria['min_score'] is not None:
            review_score = review.get('score', 0)
            if review_score < criteria['min_score']:
                return False
        
        if 'max_score' in criteria and criteria['max_score'] is not None:
            review_score = review.get('score', 5)
            if review_score > criteria['max_score']:
                return False
        
        # Keyword search
        if 'keywords' in criteria and criteria['keywords']:
            review_text = review.get('text', '').lower()
            keywords = criteria['keywords'] if isinstance(criteria['keywords'], list) else [criteria['keywords']]
            
            # Check if any keyword is found
            keyword_found = False
            for keyword in keywords:
                if keyword.lower() in review_text:
                    keyword_found = True
                    break
            
            if not keyword_found:
                return False
        
        # Exclude keywords
        if 'exclude_keywords' in criteria and criteria['exclude_keywords']:
            review_text = review.get('text', '').lower()
            exclude_keywords = criteria['exclude_keywords'] if isinstance(criteria['exclude_keywords'], list) else [criteria['exclude_keywords']]
            
            for keyword in exclude_keywords:
                if keyword.lower() in review_text:
                    return False
        
        return True