"""
Base Agent Module for Hotel Review Insight Platform
Provides common functionality and interfaces for all agents
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
import requests
from django.conf import settings

logger = logging.getLogger('agents')

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the platform
    """
    
    def __init__(self, name: str, role: str, goal: str, backstory: str):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.agent = None
        self.tools = []
        
    @abstractmethod
    def setup_tools(self) -> List[BaseTool]:
        """Setup and return tools for this agent"""
        pass
    
    @abstractmethod
    def create_agent(self) -> Agent:
        """Create and return the CrewAI agent"""
        pass
    
    @abstractmethod
    def create_task(self, description: str, context: Dict[str, Any]) -> Task:
        """Create a task for this agent"""
        pass
    
    def execute_task(self, task_description: str, context: Dict[str, Any]) -> str:
        """Execute a task and return the result"""
        try:
            if not self.agent:
                self.agent = self.create_agent()
            
            task = self.create_task(task_description, context)
            crew = Crew(agents=[self.agent], tasks=[task], verbose=True)
            result = crew.kickoff()
            
            logger.info(f"Agent {self.name} completed task successfully")
            return str(result)
        except Exception as e:
            logger.error(f"Agent {self.name} failed to execute task: {str(e)}")
            raise


class HuggingFaceAPITool(BaseTool):
    """
    Base tool for HuggingFace API interactions
    """
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.api_url = f"{settings.HUGGINGFACE_API_URL}/{model_name}"
        
    def _make_api_request(self, payload: Dict) -> Dict:
        """Make API request to HuggingFace"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HuggingFace API request failed: {str(e)}")
            raise


class AgentOrchestrator:
    """
    Orchestrates multiple agents to work together
    """
    
    def __init__(self):
        self.agents = {}
        self.results = {}
        
    def register_agent(self, agent_name: str, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent_name] = agent
        
    def execute_pipeline(self, reviews: List[Dict], pipeline_config: Dict) -> Dict:
        """Execute the complete multi-agent pipeline"""
        try:
            results = {
                'processed_reviews': [],
                'summary': {},
                'analytics': {},
                'search_index': []
            }
            
            for review in reviews:
                processed_review = self._process_single_review(review)
                results['processed_reviews'].append(processed_review)
            
            # Generate summary and analytics
            if 'summary_agent' in self.agents:
                summary_result = self.agents['summary_agent'].execute_task(
                    "Generate summary of all reviews",
                    {'reviews': results['processed_reviews']}
                )
                results['summary'] = {'text': summary_result}
            
            logger.info(f"Pipeline processed {len(reviews)} reviews successfully")
            return results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            raise
    
    def _process_single_review(self, review: Dict) -> Dict:
        """Process a single review through all agents"""
        result = review.copy()
        
        # Sentiment classification
        if 'classifier_agent' in self.agents:
            sentiment = self.agents['classifier_agent'].execute_task(
                f"Classify sentiment of: {review.get('text', '')}",
                {'review': review}
            )
            result['sentiment'] = sentiment
        
        # Sentiment scoring
        if 'scorer_agent' in self.agents:
            score = self.agents['scorer_agent'].execute_task(
                f"Score review: {review.get('text', '')}",
                {'review': review, 'sentiment': result.get('sentiment', '')}
            )
            result['score'] = score
        
        return result


# Utility functions for agent communication
def format_review_for_agent(review: Dict) -> str:
    """Format review data for agent consumption"""
    text = review.get('text', '')
    rating = review.get('rating', 'N/A')
    date = review.get('date', 'N/A')
    
    return f"""
    Review Text: {text}
    Original Rating: {rating}
    Date: {date}
    """

def parse_agent_response(response: str, response_type: str) -> Any:
    """Parse agent response based on expected type"""
    try:
        if response_type == 'sentiment':
            # Extract sentiment from response
            response_lower = response.lower()
            if 'positive' in response_lower:
                return 'positive'
            elif 'negative' in response_lower:
                return 'negative'
            else:
                return 'neutral'
        
        elif response_type == 'score':
            # Extract numerical score
            import re
            numbers = re.findall(r'\d+\.?\d*', response)
            if numbers:
                score = float(numbers[0])
                return min(max(score, 0), 5)  # Clamp between 0-5
            return 3.0  # Default neutral score
        
        elif response_type == 'summary':
            return response.strip()
        
        else:
            return response
            
    except Exception as e:
        logger.warning(f"Failed to parse agent response: {str(e)}")
        return response
