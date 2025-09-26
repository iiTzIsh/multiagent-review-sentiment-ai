
import logging
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.core.cache import cache

from .classifier.agent import ReviewClassifierAgent
from .scorer.agent import ReviewScorerAgent
from .summarizer.agent import ReviewSummarizerAgent
from .orchestrator import ReviewProcessingOrchestrator

logger = logging.getLogger('agents.django_integration')


class AgentManager:

    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_agents()
            AgentManager._initialized = True
    
    def _initialize_agents(self):
        try:
            logger.info("🚀 Initializing clean three-agent system...")

            self.classifier = ReviewClassifierAgent()
            self.scorer = ReviewScorerAgent()
            self.summarizer = ReviewSummarizerAgent()
            
            # Initialize orchestrator
            self.orchestrator = ReviewProcessingOrchestrator()
            
            # Agent status tracking
            self.agents_initialized = True
            
            logger.info("All agents successfully initialized")
            logger.info(f"   - Classifier: {self.classifier.name}")
            logger.info(f"   - Scorer: {self.scorer.name}")
            logger.info(f"   - Summarizer: {self.summarizer.name}")
            logger.info(f"   - Orchestrator: {self.orchestrator.name}")
            
        except Exception as e:
            logger.error(f" Agent initialization failed: {str(e)}")
            self.agents_initialized = False
            raise
    

    def classify_review(self, review_text: str, review_id: str = None) -> Dict[str, Any]:

        try:
            if not self.agents_initialized:
                raise RuntimeError("Agents not properly initialized")
            
            # Check cache first
            cache_key = f"classify_{hash(review_text)}"
            cached_result = cache.get(cache_key)
            if cached_result and getattr(settings, 'ENABLE_AGENT_CACHE', False):
                return cached_result
            
            # Use classifier agent
            result = self.classifier.classify_review(review_text)
            
            # Add Django-specific metadata
            result['processed_by'] = 'ClassifierAgent'
            result['review_id'] = review_id
            
            # Cache result 
            if getattr(settings, 'ENABLE_AGENT_CACHE', False):
                cache.set(cache_key, result, timeout=3600)  # 1 hour
            
            return result
            
        except Exception as e:
            logger.error(f"Classification failed for review {review_id}: {str(e)}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'error': str(e),
                'processed_by': 'ClassifierAgent',
                'review_id': review_id
            }
    

    def score_review(self, review_text: str, sentiment: str = None, 
                    review_id: str = None) -> Dict[str, Any]:
        try:
            if not self.agents_initialized:
                raise RuntimeError("Agents not properly initialized")
            
            # Use scorer agent
            result = self.scorer.score_review(review_text, sentiment)
            
            # Add Django-specific metadata
            result['processed_by'] = 'ScorerAgent'
            result['review_id'] = review_id
            result['input_sentiment'] = sentiment
            
            return result
            
        except Exception as e:
            logger.error(f"Scoring failed for review {review_id}: {str(e)}")
            return {
                'score': 3.0,
                'confidence': 0.0,
                'error': str(e),
                'processed_by': 'ScorerAgent',
                'review_id': review_id
            }
    

    def summarize_reviews(self, reviews_data: List[Dict], 
                         analysis_type: str = "comprehensive") -> Dict[str, Any]:
        try:
            if not self.agents_initialized:
                raise RuntimeError("Agents not properly initialized")
            
            # Use summarizer agent
            result = self.summarizer.summarize_reviews(reviews_data, include_insights=True)
            
            # Add Django-specific metadata
            result['processed_by'] = 'SummarizerAgent'
            result['analysis_type'] = analysis_type
            result['django_integration'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Summarization failed for {len(reviews_data)} reviews: {str(e)}")
            return {
                'summary_text': f"Error generating summary for {len(reviews_data)} reviews",
                'total_reviews': len(reviews_data),
                'summary_data': {},
                'error': str(e),
                'processed_by': 'SummarizerAgent'
            }
    

    def process_review_complete(self, review_text: str, review_id: str = None) -> Dict[str, Any]:
        try:
            if not self.agents_initialized:
                raise RuntimeError("Agents not properly initialized")
            
            # Use orchestrator for complete pipeline
            result = self.orchestrator.process_single_review(review_text, review_id)
            
            # Add Django-specific metadata
            result['django_integration'] = True
            result['pipeline_used'] = 'Classifier → Scorer'
            
            return result
            
        except Exception as e:
            logger.error(f"Complete processing failed for review {review_id}: {str(e)}")
            return {
                'review_id': review_id,
                'review_text': review_text,
                'analysis': {
                    'sentiment': 'neutral',
                    'sentiment_confidence': 0.0,
                    'score': 3.0,
                    'score_confidence': 0.0,
                    'overall_confidence': 0.0
                },
                'error': str(e),
                'django_integration': True
            }
    

    def process_batch_reviews(self, reviews_data: List[Dict], 
                            include_summary: bool = True) -> Dict[str, Any]:
        try:
            if not self.agents_initialized:
                raise RuntimeError("Agents not properly initialized")
            
            # Use orchestrator for batch processing
            result = self.orchestrator.process_batch_reviews(reviews_data, include_summary)
            
            # Add Django-specific metadata
            result['django_integration'] = True
            result['batch_processing'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Batch processing failed for {len(reviews_data)} reviews: {str(e)}")
            return {
                'batch_info': {
                    'total_reviews': len(reviews_data),
                    'processed_successfully': 0,
                    'error': str(e)
                },
                'django_integration': True
            }
    

    def get_agent_status(self) -> Dict[str, Any]:
        if not self.agents_initialized:
            return {
                'status': 'not_initialized',
                'error': 'Agents not properly initialized'
            }
        
        try:
            orchestrator_status = self.orchestrator.get_orchestrator_status()
            
            return {
                'status': 'operational',
                'agents': {
                    'classifier': {
                        'name': self.classifier.name,
                        'role': self.classifier.role,
                        'status': 'initialized'
                    },
                    'scorer': {
                        'name': self.scorer.name,
                        'role': self.scorer.role,
                        'status': 'initialized'
                    },
                    'summarizer': {
                        'name': self.summarizer.name,
                        'role': self.summarizer.role,
                        'status': 'initialized'
                    }
                },
                'orchestrator': orchestrator_status,
                'django_integration': {
                    'version': '1.0',
                    'cache_enabled': getattr(settings, 'ENABLE_AGENT_CACHE', False),
                    'initialized': self.agents_initialized
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'agents_initialized': self.agents_initialized
            }


# Global agent manager instance for Django
agent_manager = AgentManager()


# Convenience functions for Django views
def classify_review(review_text: str, review_id: str = None) -> Dict[str, Any]:
    return agent_manager.classify_review(review_text, review_id)


def score_review(review_text: str, sentiment: str = None, review_id: str = None) -> Dict[str, Any]:
    return agent_manager.score_review(review_text, sentiment, review_id)


def summarize_reviews(reviews_data: List[Dict], analysis_type: str = "comprehensive") -> Dict[str, Any]:
    return agent_manager.summarize_reviews(reviews_data, analysis_type)


def process_review_complete(review_text: str, review_id: str = None) -> Dict[str, Any]:
    return agent_manager.process_review_complete(review_text, review_id)


def process_batch_reviews(reviews_data: List[Dict], include_summary: bool = True) -> Dict[str, Any]:
    return agent_manager.process_batch_reviews(reviews_data, include_summary)


def get_agent_status() -> Dict[str, Any]:
    return agent_manager.get_agent_status()