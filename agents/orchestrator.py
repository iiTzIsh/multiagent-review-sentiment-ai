
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import our agents
from .classifier.agent import ReviewClassifierAgent
from .scorer.agent import ReviewScorerAgent  
from .summarizer.agent import ReviewSummarizerAgent

logger = logging.getLogger('agents.orchestrator')


class ReviewProcessingOrchestrator:
    
    def __init__(self):

        # Orchestrator Identity
        self.name = "ReviewProcessingOrchestrator"
        self.role = "Multi-Agent Workflow Coordinator"
        self.goal = "Execute complete hotel review analysis through specialized agent pipeline"
        
        # Initialize the three specialized agents
        self.classifier_agent = None
        self.scorer_agent = None
        self.summarizer_agent = None
        
        # Workflow tracking
        self.workflow_stats = {
            'total_processed': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'last_run': None
        }
        
        # Initialize agents
        self._initialize_agents()
    

    # Initialize all three specialized agents
    def _initialize_agents(self):
        try:
            self.classifier_agent = ReviewClassifierAgent()
            logger.info("[OK] Classifier Agent initialized")
            
            self.scorer_agent = ReviewScorerAgent()
            logger.info("[OK] Scorer Agent initialized")
            
            self.summarizer_agent = ReviewSummarizerAgent()
            logger.info("[OK] Summarizer Agent initialized")
            
            logger.info("[COMPLETE] All three agents successfully initialized")
            
        except Exception as e:
            logger.error(f"Agent initialization failed: {str(e)}")
            raise
    

    def process_single_review(self, review_text: str, review_id: str = None) -> Dict[str, Any]:

        try:
            workflow_start = datetime.now()
            
            # Sentiment Classification
            logger.info(f"[STEP 1] Classifying sentiment for review {review_id or 'unknown'}")
            classification_result = self.classifier_agent.classify_review(review_text)
            
            sentiment = classification_result.get('sentiment', 'neutral')
            classification_confidence = classification_result.get('confidence', 0.5)
            
            # Score Generation
            logger.info(f"[STEP 2] Generating score for {sentiment} sentiment")
            scoring_result = self.scorer_agent.score_review(review_text, sentiment)
            
            score = scoring_result.get('score', 3.0)
            scoring_confidence = scoring_result.get('confidence', 0.5)
            
            # Compile Final Result
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
                    'overall_confidence': round((classification_confidence + scoring_confidence) / 2, 2)
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
                'raw_results': {}
            }
    
    
    def process_batch_reviews(self, reviews: List[Dict[str, str]], 
                            include_summary: bool = True) -> Dict[str, Any]:

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
    
    # Get current orchestrator status and agent health
    def get_orchestrator_status(self) -> Dict[str, Any]:
        
        return {
            'orchestrator_info': {
                'name': self.name,
                'role': self.role,
                'status': 'operational' if all([
                    self.classifier_agent, 
                    self.scorer_agent, 
                    self.summarizer_agent
                ]) else 'degraded'
            },
            'agents_status': {
                'classifier': 'initialized' if self.classifier_agent else 'not_initialized',
                'scorer': 'initialized' if self.scorer_agent else 'not_initialized', 
                'summarizer': 'initialized' if self.summarizer_agent else 'not_initialized'
            },
            'workflow_statistics': self.workflow_stats,
            'capabilities': {
                'single_review_processing': True,
                'batch_review_processing': True,
                'collection_summarization': True,
                'workflow_monitoring': True
            }
        }