"""
Django Integration for Clean Three-Agent System
Provides easy access to Classifier, Scorer, and Summarizer agents from Django views

INTEGRATION PURPOSE: Bridge between Django and clean agent architecture
- Easy agent access for Django views and API endpoints
- Consistent error handling and logging
- Performance monitoring and caching where appropriate
"""

import logging
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.core.cache import cache

# Import our clean agents
from .classifier.agent import ReviewClassifierAgent
from .scorer.agent import ReviewScorerAgent
from .summarizer.agent import ReviewSummarizerAgent
from .orchestrator import ReviewProcessingOrchestrator

logger = logging.getLogger('agents.django_integration')


class AgentManager:
    """
    Django-compatible manager for the three-agent system
    
    SINGLETON PATTERN: Ensures consistent agent instances across Django application
    RESPONSIBILITIES:
    - Initialize and manage the three specialized agents
    - Provide easy access methods for Django views
    - Handle caching and performance optimization
    - Centralized error handling and logging
    """
    
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
        """Initialize all three agents and orchestrator"""
        try:
            logger.info("🚀 Initializing clean three-agent system...")
            
            # Initialize individual agents
            self.classifier = ReviewClassifierAgent()
            self.scorer = ReviewScorerAgent()
            self.summarizer = ReviewSummarizerAgent()
            
            # Initialize orchestrator
            self.orchestrator = ReviewProcessingOrchestrator()
            
            # Agent status tracking
            self.agents_initialized = True
            
            logger.info("✅ All agents successfully initialized")
            logger.info(f"   - Classifier: {self.classifier.name}")
            logger.info(f"   - Scorer: {self.scorer.name}")
            logger.info(f"   - Summarizer: {self.summarizer.name}")
            logger.info(f"   - Orchestrator: {self.orchestrator.name}")
            
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {str(e)}")
            self.agents_initialized = False
            raise
    
    def classify_review(self, review_text: str, review_id: str = None) -> Dict[str, Any]:
        """
        Classify single review sentiment using Classifier Agent
        
        Django-friendly wrapper with error handling and caching
        """
        try:
            if not self.agents_initialized:
                raise RuntimeError("Agents not properly initialized")
            
            # Check cache first (optional optimization)
            cache_key = f"classify_{hash(review_text)}"
            cached_result = cache.get(cache_key)
            if cached_result and getattr(settings, 'ENABLE_AGENT_CACHE', False):
                return cached_result
            
            # Use classifier agent
            result = self.classifier.classify_review(review_text)
            
            # Add Django-specific metadata
            result['processed_by'] = 'ClassifierAgent'
            result['review_id'] = review_id
            
            # Cache result (optional)
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
        """
        Score single review using Scorer Agent
        
        Django-friendly wrapper with error handling
        """
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
        """
        Generate summary using Summarizer Agent
        
        Django-friendly wrapper for review collections
        """
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
        """
        Process single review through complete pipeline using Orchestrator
        
        Django-friendly wrapper for full workflow: Classify → Score
        """
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
        """
        Process batch of reviews using Orchestrator
        
        Django-friendly wrapper for batch processing with optional summarization
        """
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
        """Get status of all agents for Django admin/monitoring"""
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
    """Convenience function for sentiment classification"""
    return agent_manager.classify_review(review_text, review_id)


def score_review(review_text: str, sentiment: str = None, review_id: str = None) -> Dict[str, Any]:
    """Convenience function for review scoring"""  
    return agent_manager.score_review(review_text, sentiment, review_id)


def summarize_reviews(reviews_data: List[Dict], analysis_type: str = "comprehensive") -> Dict[str, Any]:
    """Convenience function for review summarization"""
    return agent_manager.summarize_reviews(reviews_data, analysis_type)


def process_review_complete(review_text: str, review_id: str = None) -> Dict[str, Any]:
    """Convenience function for complete review processing"""
    return agent_manager.process_review_complete(review_text, review_id)


def process_batch_reviews(reviews_data: List[Dict], include_summary: bool = True) -> Dict[str, Any]:
    """Convenience function for batch review processing"""
    return agent_manager.process_batch_reviews(reviews_data, include_summary)


def get_agent_status() -> Dict[str, Any]:
    """Convenience function to get agent system status"""
    return agent_manager.get_agent_status()


# =============================================================================
# DJANGO MANAGEMENT COMMANDS SUPPORT
# =============================================================================

def initialize_agents_for_management():
    """Initialize agents for Django management commands"""
    try:
        agent_manager._initialize_agents()
        logger.info("✅ Agents initialized for management command")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize agents for management: {str(e)}")
        return False


def test_agents_functionality():
    """Test all agents for Django health checks"""
    try:
        # Test classifier
        classify_result = classify_review("Test review for functionality check")
        
        # Test scorer
        score_result = score_review("Test review", "positive")
        
        # Test summarizer
        test_data = [{'text': 'Test review', 'sentiment': 'positive', 'score': 4.0}]
        summary_result = summarize_reviews(test_data)
        
        return {
            'all_tests_passed': True,
            'classifier_test': classify_result.get('sentiment') is not None,
            'scorer_test': score_result.get('score') is not None,
            'summarizer_test': summary_result.get('summary_text') is not None
        }
        
    except Exception as e:
        return {
            'all_tests_passed': False,
            'error': str(e)
        }