
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import our agents
from .classifier.agent import ReviewClassifierAgent
from .scorer.agent import ReviewScorerAgent  
from .summarizer.agent import ReviewSummarizerAgent
from .tagger.agent import TagsGeneratorAgent
from .recommender.agent import ReviewRecommendationsAgent
from .title_generator.agent import ReviewTitleGeneratorAgent

logger = logging.getLogger('agents.orchestrator')


class ReviewProcessingOrchestrator:
    """
    Two-Stage Workflow:
    
    Stage 1: Core Processing (Fast, Essential)
    - Process individual reviews with sentiment, score, topics
    - Store structured data in database
    
    Stage 2: Analytics Generation (On-Demand)
    - Generate dashboard summaries and recommendations
    - Create business intelligence from processed data
    """
    
    def __init__(self):

        # Orchestrator Identity
        self.name = "ReviewProcessingOrchestrator"
        self.role = "Two-Stage Workflow Coordinator"
        self.goal = "Stage 1: Core processing | Stage 2: Analytics generation"
        
        # Initialize the specialized agents
        self.classifier_agent = None
        self.scorer_agent = None
        self.summarizer_agent = None
        self.tags_generator_agent = None
        self.recommendations_agent = None
        self.title_generator_agent = None
        
        # Workflow tracking
        self.workflow_stats = {
            'total_processed': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'last_run': None
        }
        
        # Initialize agents
        self._initialize_agents()
    

    def _initialize_agents(self):
        """Initialize agents for two-stage workflow"""
        try:
            # Stage 1: Core Processing Agents (Always Initialized)
            self.classifier_agent = ReviewClassifierAgent()
            logger.info("[STAGE 1] Classifier Agent initialized")
            
            self.scorer_agent = ReviewScorerAgent()
            logger.info("[STAGE 1] Scorer Agent initialized")
            
            # Title generation (can be Stage 1 for immediate titles)
            self.title_generator_agent = ReviewTitleGeneratorAgent()
            logger.info("[STAGE 1] Title Generator Agent initialized")
            
            # Stage 2: Analytics Agents (Lazy Initialization)
            self.summarizer_agent = None
            self.tags_generator_agent = None
            self.recommendations_agent = None
            
            logger.info("[STAGE 1 COMPLETE] Core processing agents ready")
            logger.info("[STAGE 2] Analytics agents will be initialized on-demand")
            
        except Exception as e:
            logger.error(f"Agent initialization failed: {str(e)}")
            raise
    

    def process_single_review(self, review_text: str, review_id: str = None) -> Dict[str, Any]:
        """
        STAGE 1: Core Processing (Fast, Essential)
        
        Process individual review with core analysis:
        - Sentiment classification
        - Score generation
        - Basic topic extraction
        
        Returns structured data ready for database storage
        """
        try:
            workflow_start = datetime.now()
            logger.info(f"[STAGE 1] Processing review {review_id or 'unknown'}")
            
            # Step 1: Sentiment Classification
            classification_result = self.classifier_agent.classify_review(review_text)
            sentiment = classification_result.get('sentiment', 'neutral')
            classification_confidence = classification_result.get('confidence', 0.5)
            
            # Step 2: Score Generation (uses sentiment context)
            scoring_result = self.scorer_agent.score_review(review_text, sentiment)
            score = scoring_result.get('score', 3.0)
            scoring_confidence = scoring_result.get('confidence', 0.5)
            
            # Step 3: Title Generation (uses sentiment context)
            title_result = self.title_generator_agent.generate_title(review_text, sentiment)
            title = title_result.get('title', 'Untitled Review')
            title_confidence = title_result.get('confidence', 0.5)
            
            # Compile Core Processing Result
            workflow_end = datetime.now()
            processing_time = (workflow_end - workflow_start).total_seconds()
            
            final_result = {
                'review_id': review_id,
                'review_text': review_text,
                'analysis': {
                    'sentiment': sentiment,
                    'sentiment_confidence': classification_confidence,
                    'score': score,
                    'score_confidence': scoring_confidence,
                    'title': title,
                    'title_confidence': title_confidence,
                    'overall_confidence': round((classification_confidence + scoring_confidence + title_confidence) / 3, 2)
                },
                'processing': {
                    'processed_at': workflow_end.isoformat(),
                    'processing_time_seconds': round(processing_time, 2),
                    'orchestrator': self.name
                },
                'raw_results': {
                    'classification': classification_result,
                    'scoring': scoring_result
                }
            }
            
            # Update workflow stats
            self.workflow_stats['total_processed'] += 1
            self.workflow_stats['successful_workflows'] += 1
            self.workflow_stats['last_run'] = workflow_end.isoformat()
            
            logger.info(f"[COMPLETED] Single review workflow completed in {processing_time:.2f}s")
            return final_result
            
        except Exception as e:
            logger.error(f"Single review workflow failed: {str(e)}")
            self.workflow_stats['failed_workflows'] += 1
            
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
                'processing': {
                    'processed_at': datetime.now().isoformat(),
                    'processing_time_seconds': 0,
                    'orchestrator': self.name,
                    'error': str(e)
                },
                'raw_results': {},
                'stage': 'core_processing_complete'
            }
    
    def _ensure_analytics_agents(self):
        """Lazy initialization of Stage 2 analytics agents"""
        if not self.summarizer_agent:
            self.summarizer_agent = ReviewSummarizerAgent()
            logger.info("[STAGE 2] Summarizer Agent initialized")
            
        if not self.tags_generator_agent:
            self.tags_generator_agent = TagsGeneratorAgent()
            logger.info("[STAGE 2] Tags Generator Agent initialized")
            
        if not self.recommendations_agent:
            self.recommendations_agent = ReviewRecommendationsAgent()
            logger.info("[STAGE 2] Recommendations Agent initialized")
            
        logger.info("[STAGE 2] All analytics agents ready")
    
    
    def process_batch_reviews(self, reviews: List[Dict[str, str]], 
                            include_summary: bool = False) -> Dict[str, Any]:
        """
        STAGE 1: Core Processing for Batch Reviews
        
        Processes multiple reviews through core workflow (sentiment + score).
        Note: include_summary should be False for Stage 1, use generate_analytics_summary() for Stage 2.
        """

        try:
            workflow_start = datetime.now()
            
            logger.info(f" Starting batch workflow for {len(reviews)} reviews")
            
            # Process Individual Reviews
            individual_results = []
            
            for i, review_data in enumerate(reviews, 1):
                review_text = review_data.get('text', review_data.get('review_text', ''))
                review_id = review_data.get('id', f"batch_review_{i}")
                
                logger.info(f"Processing review {i}/{len(reviews)}")
                
                result = self.process_single_review(review_text, review_id)
                individual_results.append(result)
            
            #  Generate Collection Summary
            summary_result = None
            if include_summary and individual_results:
                logger.info("📝 Step 2: Generating collection summary")
                
                # Prepare data for summarizer
                summary_input = []
                for result in individual_results:
                    summary_input.append({
                        'text': result['review_text'],
                        'sentiment': result['analysis']['sentiment'],
                        'score': result['analysis']['score']
                    })
                
                summary_result = self.summarizer_agent.summarize_reviews(summary_input)
            
            # Compile Batch Report
            workflow_end = datetime.now()
            total_processing_time = (workflow_end - workflow_start).total_seconds()
            
            # Calculate batch statistics
            sentiments = [r['analysis']['sentiment'] for r in individual_results]
            scores = [r['analysis']['score'] for r in individual_results]
            
            batch_stats = {
                'total_reviews': len(individual_results),
                'sentiment_distribution': {
                    'positive': sentiments.count('positive'),
                    'negative': sentiments.count('negative'),
                    'neutral': sentiments.count('neutral')
                },
                'score_statistics': {
                    'average': round(sum(scores) / len(scores), 2) if scores else 0,
                    'minimum': min(scores) if scores else 0,
                    'maximum': max(scores) if scores else 0
                }
            }
            
            batch_report = {
                'batch_info': {
                    'total_reviews': len(reviews),
                    'processed_successfully': len(individual_results),
                    'processing_time_seconds': round(total_processing_time, 2),
                    'processed_at': workflow_end.isoformat(),
                    'orchestrator': self.name
                },
                'batch_statistics': batch_stats,
                'individual_results': individual_results,
                'collection_summary': summary_result,
                'workflow_performance': {
                    'avg_time_per_review': round(total_processing_time / len(reviews), 2) if reviews else 0,
                    'successful_rate': round(len(individual_results) / len(reviews) * 100, 1) if reviews else 0
                }
            }
            
            # Update workflow stats
            self.workflow_stats['total_processed'] += len(reviews)
            self.workflow_stats['successful_workflows'] += 1
            self.workflow_stats['last_run'] = workflow_end.isoformat()
            
            logger.info(f"[COMPLETE] Batch workflow completed: {len(reviews)} reviews in {total_processing_time:.2f}s")
            return batch_report
            
        except Exception as e:
            logger.error(f"Batch workflow failed: {str(e)}")
            self.workflow_stats['failed_workflows'] += 1
            
            return {
                'batch_info': {
                    'total_reviews': len(reviews),
                    'processed_successfully': 0,
                    'processing_time_seconds': 0,
                    'processed_at': datetime.now().isoformat(),
                    'orchestrator': self.name,
                    'error': str(e)
                },
                'batch_statistics': {},
                'individual_results': [],
                'collection_summary': None,
                'workflow_performance': {}
            }
    
    def generate_tags_analysis(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        STAGE 2: Analytics Generation - Tags Analysis
        
        Generate comprehensive tags and topic analysis for dashboard display.
        Only called when user visits analytics page or requests analysis.
        
        Args:
            reviews: List of processed review dictionaries with sentiment/score data
            
        Returns:
            Dictionary containing AI-generated tags, keywords, topics, and issues
        """
        try:
            logger.info(f"[STAGE 2] Generating tags analysis for {len(reviews)} reviews")
            
            # Ensure analytics agents are initialized
            self._ensure_analytics_agents()
            
            # Generate comprehensive tags analysis
            tags_result = self.tags_generator_agent.generate_tags(reviews)
            
            logger.info("[STAGE 2] Tags analysis completed successfully")
            
            return {
                'status': 'success',
                'tags_analysis': tags_result,
                'processed_reviews': len(reviews),
                'generated_at': datetime.now().isoformat(),
                'agent': 'TagsGeneratorAgent',
                'stage': 'analytics_generation'
            }
            
        except Exception as e:
            logger.error(f"Tags generation failed: {str(e)}")
            return {
                'status': 'error',
                'error_message': str(e),
                'tags_analysis': self._get_default_tags_response(),
                'processed_reviews': 0,
                'generated_at': datetime.now().isoformat()
            }
    
    def _get_default_tags_response(self) -> Dict[str, Any]:
        """Return default tags structure if generation fails"""
        return {
            "positive_keywords": [
                "excellent", "clean", "friendly", "comfortable", "beautiful",
                "perfect", "amazing", "helpful", "spacious", "convenient"
            ],
            "negative_keywords": [
                "dirty", "noise", "rude", "expensive", "old",
                "broken", "slow", "uncomfortable", "smelly", "disappointing"
            ],
            "topic_metrics": {
                "service": {
                    "percentage": 75,
                    "keywords": ["staff", "support", "help"],
                    "description": "Service quality analysis"
                },
                "cleanliness": {
                    "percentage": 70,
                    "keywords": ["clean", "hygiene", "tidy"],
                    "description": "Cleanliness standards analysis"
                },
                "location": {
                    "percentage": 80,
                    "keywords": ["area", "transport", "access"],
                    "description": "Location convenience analysis"
                },
                "value": {
                    "percentage": 65,
                    "keywords": ["price", "cost", "worth"],
                    "description": "Value for money analysis"
                }
            },
            "main_issues": [
                "Service quality concerns",
                "Cleanliness standards",
                "Noise levels",
                "Value for money",
                "Facility maintenance"
            ],
            "emerging_topics": [
                "Health and safety protocols",
                "Digital service integration",
                "Sustainability practices",
                "Contactless services",
                "Flexible booking policies"
            ]
        }
    
    def generate_recommendations(self, reviews_data: List[Dict], analysis_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        STAGE 2: Analytics Generation - Business Recommendations
        
        Generate AI-powered business recommendations for dashboard display.
        Only called when user visits analytics page or requests analysis.
        
        Args:
            reviews_data: List of processed review dictionaries with sentiment/score data
            analysis_context: Optional context from tags analysis
            
        Returns:
            Dictionary containing AI-generated recommendations and metadata
        """
        try:
            logger.info(f"[STAGE 2] Generating business recommendations for {len(reviews_data)} reviews")
            
            # Ensure analytics agents are initialized
            self._ensure_analytics_agents()
            
            # Generate recommendations using the AI agent
            recommendations_result = self.recommendations_agent.generate_recommendations(
                reviews_data, 
                analysis_context
            )
            
            # Add Stage 2 metadata
            recommendations_result.update({
                'orchestrator': self.name,
                'agent_used': 'ReviewRecommendationsAgent',
                'generated_at': datetime.now().isoformat(),
                'stage': 'analytics_generation'
            })
            
            logger.info("[STAGE 2] Business recommendations generated successfully")
            return recommendations_result
            
        except Exception as e:
            logger.error(f"[RECOMMENDATIONS] Failed to generate recommendations: {str(e)}")
            return {
                'recommendations': [],
                'status': 'error',
                'generated_by': 'Orchestrator (Error)',
                'error': str(e),
                'stage': 'analytics_generation_failed'
            }
    
    def generate_analytics_summary(self, reviews_data: List[Dict]) -> Dict[str, Any]:
        """
        STAGE 2: Analytics Generation - Executive Summary
        
        Generate AI-powered executive summary for dashboard display.
        Only called when user visits analytics page or requests analysis.
        
        Args:
            reviews_data: List of processed review dictionaries with sentiment/score data
            
        Returns:
            Dictionary containing AI-generated summary and insights
        """
        try:
            logger.info(f"[STAGE 2] Generating executive summary for {len(reviews_data)} reviews")
            
            # Ensure analytics agents are initialized
            self._ensure_analytics_agents()
            
            # Generate summary using the AI agent
            summary_result = self.summarizer_agent.summarize_reviews(reviews_data, include_insights=True)
            
            # Add Stage 2 metadata
            summary_result.update({
                'orchestrator': self.name,
                'generated_at': datetime.now().isoformat(),
                'stage': 'analytics_generation'
            })
            
            logger.info("[STAGE 2] Executive summary generated successfully")
            return summary_result
            
        except Exception as e:
            logger.error(f"[STAGE 2] Failed to generate summary: {str(e)}")
            return {
                'summary_text': 'Summary generation failed',
                'status': 'error',
                'error': str(e),
                'stage': 'analytics_generation_failed'
            }
    
    # Get current orchestrator status and agent health
    def get_orchestrator_status(self) -> Dict[str, Any]:
        
        return {
            'orchestrator_info': {
                'name': self.name,
                'role': self.role,
                'architecture': 'Two-Stage Workflow',
                'status': 'operational' if all([self.classifier_agent, self.scorer_agent]) else 'degraded'
            },
            'stage_1_agents': {
                'classifier': 'initialized' if self.classifier_agent else 'not_initialized',
                'scorer': 'initialized' if self.scorer_agent else 'not_initialized'
            },
            'stage_2_agents': {
                'summarizer': 'initialized' if self.summarizer_agent else 'lazy_initialization',
                'tags_generator': 'initialized' if self.tags_generator_agent else 'lazy_initialization',
                'recommendations': 'initialized' if self.recommendations_agent else 'lazy_initialization'
            },
            'workflow_statistics': self.workflow_stats,
            'workflow_stages': {
                'stage_1': 'Core Processing (Always Ready)',
                'stage_2': 'Analytics Generation (On-Demand)'
            },
            'capabilities': {
                'core_processing': True,
                'analytics_generation': True,
                'lazy_initialization': True,
                'workflow_monitoring': True
            }
        }