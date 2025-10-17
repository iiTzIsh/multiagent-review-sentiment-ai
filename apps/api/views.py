"""
API Views for Hotel Review Insight Platform
RESTful API endpoints for external integrations and AJAX calls
"""

from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json
import logging
from datetime import datetime, timedelta

from apps.reviews.models import Review, Hotel, ReviewBatch, AgentTask, AIAnalysisResult
from .serializers import ReviewSerializer, HotelSerializer
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class AuthProfileView(APIView):
    """API endpoint for user profile information"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_staff': request.user.is_staff,
                'date_joined': request.user.date_joined
            })
        else:
            return Response({
                'username': 'Anonymous',
                'email': '',
                'first_name': '',
                'last_name': '',
                'is_staff': False
            })


class DashboardStatsView(APIView):
    """API endpoint for dashboard statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Filter by accessible hotels
            accessible_hotels = request.user.profile.get_accessible_hotels()
            
            if accessible_hotels:
                total_reviews = Review.objects.filter(hotel__in=accessible_hotels).count()
                processed_reviews = Review.objects.filter(processed=True, hotel__in=accessible_hotels).count()
                pending_reviews = Review.objects.filter(processed=False, hotel__in=accessible_hotels).count()
                sentiment_distribution = list(Review.objects.filter(hotel__in=accessible_hotels).values('sentiment').annotate(count=Count('sentiment')))
                avg_score = Review.objects.filter(hotel__in=accessible_hotels).aggregate(avg_score=Avg('ai_score'))['avg_score'] or 0
            else:
                total_reviews = 0
                processed_reviews = 0
                pending_reviews = 0
                sentiment_distribution = []
                avg_score = 0
            
            stats = {
                'total_reviews': total_reviews,
                'total_hotels': len(accessible_hotels),
                'processed_reviews': processed_reviews,
                'pending_reviews': pending_reviews,
                'sentiment_distribution': sentiment_distribution,
                'avg_score': avg_score,
            }
            return Response(stats)
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
            return Response({'error': 'Failed to fetch stats'}, status=500)


class RecentActivityView(APIView):
    """API endpoint for recent activity"""
    
    def get(self, request):
        try:
            recent_reviews = Review.objects.order_by('-created_at')[:10]
            recent_batches = ReviewBatch.objects.order_by('-upload_date')[:10]
            
            activity = {
                'recent_reviews': ReviewSerializer(recent_reviews, many=True).data,
                'recent_batches': [{
                    'id': str(batch.id),
                    'file_name': batch.file_name,
                    'status': batch.status,
                    'total_reviews': batch.total_reviews,
                    'processed_reviews': batch.processed_reviews,
                    'upload_date': batch.upload_date
                } for batch in recent_batches]
            }
            return Response(activity)
        except Exception as e:
            logger.error(f"Error fetching recent activity: {e}")
            return Response({'error': 'Failed to fetch activity'}, status=500)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Review operations"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    
    def get_queryset(self):
        """Filter reviews based on query parameters"""
        queryset = Review.objects.all()
        
        # Filter by hotel
        hotel_id = self.request.query_params.get('hotel')
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        
        # Filter by sentiment
        sentiment = self.request.query_params.get('sentiment')
        if sentiment:
            queryset = queryset.filter(sentiment=sentiment)
        
        # Filter by score range
        min_score = self.request.query_params.get('min_score')
        max_score = self.request.query_params.get('max_score')
        
        if min_score:
            queryset = queryset.filter(ai_score__gte=float(min_score))
        if max_score:
            queryset = queryset.filter(ai_score__lte=float(max_score))
        
        # Search in text
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(text__icontains=search) | Q(title__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Reprocess a single review"""
        review = self.get_object()
        
        try:
            # In production, this would trigger Celery task
            # For now, we'll simulate processing
            review.processed = False
            review.save()
            
            return Response({
                'success': True,
                'message': 'Review queued for reprocessing'
            })
            
        except Exception as e:
            logger.error(f"Reprocessing failed: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HotelViewSet(viewsets.ModelViewSet):
    """ViewSet for Hotel operations"""
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for a specific hotel"""
        hotel = self.get_object()
        
        # Calculate analytics
        reviews = hotel.reviews.all()
        analytics_data = {
            'total_reviews': reviews.count(),
            'average_score': reviews.aggregate(avg=Avg('ai_score'))['avg'] or 0,
            'sentiment_distribution': dict(
                reviews.values('sentiment').annotate(count=Count('sentiment'))
            ),
            'recent_reviews': ReviewSerializer(
                reviews.order_by('-created_at')[:5], many=True
            ).data
        }
        
        return Response(analytics_data)


class AnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for Analytics operations"""
    
    def list(self, request):
        """Get overall analytics"""
        try:
            # Overall statistics
            total_reviews = Review.objects.count()
            avg_score = Review.objects.aggregate(avg=Avg('ai_score'))['avg'] or 0
            
            # Sentiment distribution
            sentiment_data = Review.objects.values('sentiment').annotate(
                count=Count('sentiment')
            )
            
            # Generate simple trends from actual review data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            trends = []
            current_date = start_date
            while current_date <= end_date:
                daily_reviews = Review.objects.filter(created_at__date=current_date)
                if daily_reviews.exists():
                    trends.append({
                        'date': current_date.isoformat(),
                        'total_reviews': daily_reviews.count(),
                        'average_score': daily_reviews.aggregate(avg=Avg('ai_score'))['avg'] or 0,
                        'positive_percentage': daily_reviews.filter(sentiment='positive').count() / daily_reviews.count() * 100 if daily_reviews.count() > 0 else 0,
                        'negative_percentage': daily_reviews.filter(sentiment='negative').count() / daily_reviews.count() * 100 if daily_reviews.count() > 0 else 0
                    })
                current_date += timedelta(days=1)
            
            analytics_data = {
                'overview': {
                    'total_reviews': total_reviews,
                    'average_score': round(avg_score, 2),
                    'sentiment_distribution': list(sentiment_data),
                    'processed_reviews': Review.objects.filter(processed=True).count()
                },
                'trends': trends
            }
            
            return Response(analytics_data)
            
        except Exception as e:
            logger.error(f"Analytics retrieval failed: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class ProcessReviewsAPIView(APIView):
    """
    API endpoint for processing reviews with proper three-agent pipeline
    
    REPLACED: Rule-based simulation with real agent orchestrator
    NOW USES: ReviewProcessingOrchestrator with Classifier → Scorer workflow
    """
    
    def post(self, request):
        """Process reviews using the proper multi-agent orchestrator"""
        try:
            from agents.orchestrator import ReviewProcessingOrchestrator
            
            # Parse request body, handle empty body case
            try:
                data = json.loads(request.body) if request.body else {}
            except json.JSONDecodeError:
                data = {}
            
            # Get reviews to process (default to processing all unprocessed reviews)
            if data.get('process_all', True):  # Default to True when no data provided
                reviews = Review.objects.filter(processed=False)
            else:
                review_ids = data.get('review_ids', [])
                reviews = Review.objects.filter(id__in=review_ids)
            
            if not reviews.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'No reviews to process'
                })
            
            # Create agent task
            task = AgentTask.objects.create(
                agent_name='ReviewProcessingOrchestrator',
                task_type='batch_processing',
                status='pending',
                input_data={
                    'review_count': reviews.count(),
                    'process_all': data.get('process_all', False)
                }
            )
            
            # Initialize Two-Stage Workflow orchestrator
            orchestrator = ReviewProcessingOrchestrator()
            logger.info(f"[STAGE 1] Using {orchestrator.name} for core processing of {reviews.count()} reviews")
            
            task.status = 'running'
            task.save()
            
            # STAGE 1: Core Processing (Fast, Essential)
            processed_count = 0
            agent_results = []
            
            # Limit batch size for performance (can be adjusted)
            batch_size = min(20, reviews.count())
            reviews_to_process = reviews[:batch_size]
            
            for review in reviews_to_process:
                try:
                    # Stage 1: Core processing only (sentiment + score)
                    result = orchestrator.process_single_review(
                        review_text=review.text,
                        review_id=str(review.id)
                    )
                    
                    # Update review with agent results
                    analysis = result['analysis']
                    
                    review.sentiment = analysis['sentiment']
                    review.ai_score = analysis['score']
                    review.confidence_score = analysis['overall_confidence']
                    
                    # Update title with AI-generated title if not already set
                    if 'title' in analysis and analysis['title']:
                        if not review.title or review.title.strip() == '':
                            review.title = analysis['title']
                    
                    review.processed = True
                    review.save()
                    
                    agent_results.append({
                        'review_id': str(review.id),
                        'sentiment': analysis['sentiment'],
                        'score': analysis['score'],
                        'title': analysis.get('title', ''),
                        'confidence': analysis['overall_confidence']
                    })
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process review {review.id}: {str(e)}")
                    # Continue with other reviews
                    continue
            
            # Get orchestrator performance stats
            orchestrator_status = orchestrator.get_orchestrator_status()
            
            # Complete task with detailed results
            task.status = 'completed'
            task.output_data = {
                'processed_count': processed_count,
                'success': True,
                'orchestrator_stats': orchestrator_status['workflow_statistics'],
                'method': 'AI Agent Pipeline'
            }
            task.save()
            
            return JsonResponse({
                'success': True,
                'task_id': str(task.id),
                'processed_count': processed_count,
                'total_available': reviews.count(),
                'batch_processed': batch_size,
                'agent_used': orchestrator.name,
                'processing_method': 'Three-Agent Pipeline (Classifier → Scorer)',
                'message': f'Successfully processed {processed_count}/{batch_size} reviews using AI agents',
                'orchestrator_performance': {
                    'total_processed': orchestrator_status['workflow_statistics']['total_processed'],
                    'success_rate': orchestrator_status['workflow_statistics']['successful_workflows']
                }
            })
            
        except Exception as e:
            logger.error(f"AI agent processing failed: {str(e)}")
            
            # Update task status
            if 'task' in locals():
                task.status = 'failed'
                task.output_data = {'error': str(e)}
                task.save()
            
            return JsonResponse({
                'success': False,
                'error': f"AI agent processing failed: {str(e)}",
                'fallback': 'Consider using rule-based backup processing'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SearchAPIView(APIView):
    """API endpoint for searching reviews"""
    
    def post(self, request):
        """Search reviews using various methods"""
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            search_type = data.get('type', 'semantic')
            
            if not query:
                return JsonResponse({
                    'success': False,
                    'error': 'Query is required'
                })
            
            # Perform search based on type
            if search_type == 'semantic':
                results = self._semantic_search(query)
            elif search_type == 'keyword':
                results = self._keyword_search(query)
            else:
                results = self._filter_search(query)
            
            return JsonResponse({
                'success': True,
                'results': results,
                'count': len(results),
                'query': query,
                'search_type': search_type
            })
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _semantic_search(self, query):
        """Perform semantic search (simplified implementation)"""
        # In production, this would use the IR agent
        reviews = Review.objects.filter(
            Q(text__icontains=query) | Q(title__icontains=query)
        )[:20]
        
        return [
            {
                'id': str(review.id),
                'text': review.text[:200] + '...' if len(review.text) > 200 else review.text,
                'sentiment': review.sentiment,
                'score': review.ai_score,
                'hotel': review.hotel.name,
                'similarity': 0.85  # Simulated similarity score
            }
            for review in reviews
        ]
    
    def _keyword_search(self, query):
        """Perform keyword search"""
        keywords = [k.strip() for k in query.split(',')]
        
        q_objects = Q()
        for keyword in keywords:
            q_objects |= Q(text__icontains=keyword)
        
        reviews = Review.objects.filter(q_objects)[:20]
        
        return [
            {
                'id': str(review.id),
                'text': review.text[:200] + '...' if len(review.text) > 200 else review.text,
                'sentiment': review.sentiment,
                'score': review.ai_score,
                'hotel': review.hotel.name,
                'matched_keywords': [k for k in keywords if k.lower() in review.text.lower()]
            }
            for review in reviews
        ]
    
    def _filter_search(self, criteria):
        """Perform filtered search"""
        # Parse filter criteria
        filters = {}
        for criterion in criteria.split(','):
            if ':' in criterion:
                key, value = criterion.split(':', 1)
                filters[key.strip()] = value.strip()
        
        reviews = Review.objects.all()
        
        # Apply filters
        if 'sentiment' in filters:
            reviews = reviews.filter(sentiment=filters['sentiment'])
        
        if 'min_score' in filters:
            reviews = reviews.filter(ai_score__gte=float(filters['min_score']))
        
        if 'max_score' in filters:
            reviews = reviews.filter(ai_score__lte=float(filters['max_score']))
        
        reviews = reviews[:20]
        
        return [
            {
                'id': str(review.id),
                'text': review.text[:200] + '...' if len(review.text) > 200 else review.text,
                'sentiment': review.sentiment,
                'score': review.ai_score,
                'hotel': review.hotel.name
            }
            for review in reviews
        ]


class SummaryAPIView(APIView):
    """
    API endpoint for AI-powered summaries using Google Gemini
    
    Uses ReviewSummarizerAgent with Google Gemini integration for intelligent 
    analysis and actionable business insights from hotel reviews.
    """
    
    def get(self, request):
        """Get summary for specified criteria using Summarizer Agent"""
        try:
            from agents.summarizer.agent import ReviewSummarizerAgent
            
            hotel_id = request.GET.get('hotel')
            days = int(request.GET.get('days', 30))
            
            # Get reviews
            reviews = Review.objects.all() 
            if hotel_id:
                reviews = reviews.filter(hotel_id=hotel_id)
            
            # Date filter
            start_date = datetime.now() - timedelta(days=days)
            reviews = reviews.filter(created_at__gte=start_date)
            
            # Convert Django queryset to agent-compatible format
            reviews_data = []
            for review in reviews:
                reviews_data.append({
                    'text': review.text,
                    'sentiment': review.sentiment or 'neutral',
                    'score': review.ai_score or 3.0,
                    'hotel': review.hotel.name if review.hotel else 'Unknown',
                    'date': review.created_at.isoformat()
                })
            
            if not reviews_data:
                return Response({
                    'summary': {
                        'text': f"No reviews found for the specified criteria over the last {days} days.",
                        'total_reviews': 0,
                        'average_score': 0,
                        'sentiment_distribution': [],
                        'date_range': {
                            'start': start_date.date(),
                            'end': datetime.now().date()
                        }
                    },
                    'insights': {},
                    'agent_used': 'None (no data)'
                })
            
            # Use proper Summarizer Agent instead of rule-based logic
            summarizer = ReviewSummarizerAgent()
            logger.info(f"Using {summarizer.name} to analyze {len(reviews_data)} reviews")
            
            summary_result = summarizer.summarize_reviews(reviews_data, include_insights=True)
            
            # Format response in API-compatible structure
            return Response({
                'summary': {
                    'text': summary_result['summary_text'],
                    'total_reviews': summary_result['total_reviews'],
                    'average_score': summary_result['summary_data'].get('average_score', 0),
                    'sentiment_distribution': [
                        {'sentiment': k, 'count': v} 
                        for k, v in summary_result['summary_data'].get('sentiment_distribution', {}).items()
                    ],
                    'date_range': {
                        'start': start_date.date(),
                        'end': datetime.now().date()
                    }
                },
                'insights': {
                    'sentiment_percentages': summary_result['summary_data'].get('sentiment_percentages', {}),
                    'score_range': summary_result['summary_data'].get('score_range', [0, 5]),
                    'generated_by': summary_result.get('generated_by', 'ReviewSummarizer')
                },
                'agent_used': summary_result.get('generated_by', 'ReviewSummarizer'),
                'processing_info': {
                    'method': 'AI Agent Analysis',
                    'replaced': 'Rule-based summarization'
                }
            })
            
        except Exception as e:
            logger.error(f"AI-powered summary generation failed: {str(e)}")
            return Response({
                'error': f"Summary generation failed: {str(e)}",
                'fallback': 'Consider using rule-based backup'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TagsAnalysisAPIView(APIView):
    """
    API endpoint for AI-powered tags and topic analysis using Google Gemini
    
    Uses ReviewTagsGeneratorAgent with Google Gemini integration to generate
    comprehensive topic analysis including keywords, topics, and issues.
    """
    
    def get(self, request):
        """Get AI-generated tags analysis for specified criteria"""
        try:
            from agents.orchestrator import ReviewProcessingOrchestrator
            
            hotel_id = request.GET.get('hotel')
            days = int(request.GET.get('days', 30))
            
            # Get reviews
            reviews = Review.objects.all()
            if hotel_id:
                reviews = reviews.filter(hotel_id=hotel_id)
            
            # Date filter
            start_date = datetime.now() - timedelta(days=days)
            reviews = reviews.filter(created_at__gte=start_date)
            
            # Convert Django queryset to agent-compatible format
            reviews_data = []
            for review in reviews:
                reviews_data.append({
                    'text': review.text,
                    'sentiment': review.sentiment or 'neutral',
                    'original_rating': review.original_rating or 3.0,
                    'hotel': review.hotel.name if review.hotel else 'Unknown',
                    'date': review.created_at.isoformat()
                })
            
            if not reviews_data:
                return Response({
                    'status': 'no_data',
                    'message': f"No reviews found for the specified criteria over the last {days} days.",
                    'tags_analysis': {
                        'positive_keywords': [],
                        'negative_keywords': [],
                        'topic_metrics': {},
                        'main_issues': [],
                        'emerging_topics': []
                    },
                    'processed_reviews': 0,
                    'date_range': {
                        'start': start_date.date(),
                        'end': datetime.now().date()
                    }
                })
            
            # Use the orchestrator's tags generation method
            orchestrator = ReviewProcessingOrchestrator()
            
            logger.info(f"Generating AI-powered tags analysis for {len(reviews_data)} reviews")
            
            tags_result = orchestrator.generate_tags_analysis(reviews_data)
            
            # Format response in API-compatible structure
            return Response({
                'status': tags_result.get('status', 'success'),
                'tags_analysis': tags_result.get('tags_analysis', {}),
                'processed_reviews': tags_result.get('processed_reviews', len(reviews_data)),
                'generated_at': tags_result.get('generated_at'),
                'agent_used': tags_result.get('agent', 'TagsGeneratorAgent'),
                'date_range': {
                    'start': start_date.date(),
                    'end': datetime.now().date()
                },
                'processing_info': {
                    'method': 'AI Agent Analysis',
                    'model': 'Google Gemini 2.0 Flash',
                    'replaced': 'Hard-coded patterns'
                }
            })
            
        except Exception as e:
            logger.error(f"AI-powered tags analysis failed: {str(e)}")
            return Response({
                'status': 'error',
                'error_message': str(e),
                'tags_analysis': {
                    'positive_keywords': ['excellent', 'clean', 'friendly', 'comfortable', 'beautiful'],
                    'negative_keywords': ['dirty', 'noise', 'rude', 'expensive', 'old'],
                    'topic_metrics': {
                        'service': {'percentage': 75, 'keywords': ['staff', 'support'], 'description': 'Service quality'},
                        'cleanliness': {'percentage': 70, 'keywords': ['clean', 'hygiene'], 'description': 'Cleanliness standards'},
                        'location': {'percentage': 80, 'keywords': ['area', 'transport'], 'description': 'Location convenience'},
                        'value': {'percentage': 65, 'keywords': ['price', 'cost'], 'description': 'Value for money'}
                    },
                    'main_issues': ['Service concerns', 'Cleanliness issues'],
                    'emerging_topics': ['Safety protocols', 'Digital services']
                },
                'processed_reviews': 0,
                'generated_at': datetime.now().isoformat(),
                'fallback': 'Default tags structure used'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CombinedAIAnalysisAPIView(APIView):
    """
    Combined API endpoint for generating both summary and tags analysis
    
    This endpoint generates all AI analysis in a single request to avoid
    multiple API calls and page reloading. Optimized for on-demand generation.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Generate complete AI analysis including summary and tags"""
        try:
            from agents.orchestrator import ReviewProcessingOrchestrator
            from agents.summarizer.agent import ReviewSummarizerAgent
            
            # Get parameters
            hotel_id = request.data.get('hotel')
            days = int(request.data.get('days', 30))
            
            # Filter by accessible hotels
            accessible_hotels = request.user.profile.get_accessible_hotels()
            
            # Convert to list if it's a QuerySet to avoid multiple evaluation issues
            if hasattr(accessible_hotels, 'all'):  # It's a QuerySet
                accessible_hotels_list = list(accessible_hotels)
            else:  # It's already a list
                accessible_hotels_list = accessible_hotels
            
            # Get reviews
            if accessible_hotels_list:
                reviews = Review.objects.filter(hotel__in=accessible_hotels_list)
                if hotel_id:
                    # Verify user can access this specific hotel
                    accessible_hotel_ids = [h.id for h in accessible_hotels_list]
                    if int(hotel_id) in accessible_hotel_ids:
                        reviews = reviews.filter(hotel_id=hotel_id)
                    else:
                        return Response({'error': 'You do not have access to this hotel'}, status=403)
            else:
                # No accessible hotels - return empty result
                return Response({
                    'status': 'no_access',
                    'message': 'You do not have access to any hotels.',
                    'summary': None,
                    'tags_analysis': None,
                    'processed_reviews': 0
                }, status=403)
            
            # Date filter
            start_date = datetime.now() - timedelta(days=days)
            reviews = reviews.filter(created_at__gte=start_date)
            
            if not reviews.exists():
                return Response({
                    'status': 'no_data',
                    'message': f"No reviews found for the specified criteria over the last {days} days.",
                    'summary': None,
                    'tags_analysis': None,
                    'processed_reviews': 0
                })
            
            # Convert Django queryset to agent-compatible format
            reviews_data = []
            for review in reviews:
                reviews_data.append({
                    'text': review.text,
                    'sentiment': review.sentiment or 'neutral',
                    'score': review.ai_score or 3.0,
                    'original_rating': review.original_rating or 3.0,
                    'hotel': review.hotel.name if review.hotel else 'Unknown',
                    'date': review.created_at.isoformat()
                })
            
            logger.info(f"[STAGE 2] Generating analytics for {len(reviews_data)} reviews")
            
            # Initialize Two-Stage Workflow orchestrator
            orchestrator = ReviewProcessingOrchestrator()
            
            # STAGE 2: Analytics Generation (On-Demand)
            # Generate tags analysis first (for context)
            tags_result = orchestrator.generate_tags_analysis(reviews_data)
            
            # Generate AI-powered recommendations with context from tags analysis
            recommendations_result = orchestrator.generate_recommendations(
                reviews_data, 
                analysis_context={'tags_analysis': tags_result.get('tags_analysis', {})}
            )
            
            # Generate executive summary using Stage 2 method
            summary_result = orchestrator.generate_analytics_summary(reviews_data)
            
            # Combine Stage 2 Analytics Results
            response_data = {
                'status': 'success',
                'workflow_stage': 'analytics_generation',
                'summary': {
                    'text': summary_result.get('summary_text', ''),
                    'total_reviews': summary_result.get('total_reviews', len(reviews_data)),
                    'average_score': summary_result.get('summary_data', {}).get('average_score', 0),
                    'sentiment_distribution': [
                        {'sentiment': k, 'count': v} 
                        for k, v in summary_result.get('summary_data', {}).get('sentiment_distribution', {}).items()
                    ],
                    'insights': {
                        'sentiment_percentages': summary_result.get('summary_data', {}).get('sentiment_percentages', {}),
                        'score_range': summary_result.get('summary_data', {}).get('score_range', [0, 5]),
                        'generated_by': summary_result.get('generated_by', 'Two-Stage Workflow')
                    },
                    'recommendations': recommendations_result.get('recommendations', [])
                },
                'tags_analysis': tags_result.get('tags_analysis', {}),
                'processed_reviews': len(reviews_data),
                'generated_at': datetime.now().isoformat(),
                'date_range': {
                    'start': start_date.date(),
                    'end': datetime.now().date()
                },
                'workflow_info': {
                    'architecture': 'Two-Stage Workflow',
                    'stage_executed': 'Stage 2: Analytics Generation'
                },
                'agents_used': {
                    'summarizer': summary_result.get('generated_by', 'ReviewSummarizer'),
                    'tags_generator': tags_result.get('agent', 'TagsGeneratorAgent')
                }
            }
            
            # Save analysis results to database for persistence
            try:
                # Mark previous analysis as inactive
                if hotel_id:
                    AIAnalysisResult.objects.filter(
                        hotel_id=hotel_id, 
                        is_active=True
                    ).update(is_active=False)
                else:
                    AIAnalysisResult.objects.filter(
                        hotel__isnull=True, 
                        is_active=True
                    ).update(is_active=False)
                
                # Create new analysis result
                analysis_result = AIAnalysisResult.objects.create(
                    analysis_type='combined',
                    hotel_id=hotel_id,
                    days_analyzed=days,
                    date_range_start=start_date.date(),
                    date_range_end=datetime.now().date(),
                    total_reviews_analyzed=len(reviews_data),
                    summary_data=response_data['summary'],
                    sentiment_analysis={
                        'sentiment_distribution': response_data['summary']['sentiment_distribution'],
                        'sentiment_percentages': response_data['summary']['insights']['sentiment_percentages'],
                        'average_score': response_data['summary']['average_score'],
                        'score_range': response_data['summary']['insights']['score_range']
                    },
                    tags_analysis=response_data['tags_analysis'],
                    recommendations=response_data['summary']['recommendations'],
                    agents_used=response_data['agents_used'],
                    workflow_info=response_data['workflow_info'],
                    is_active=True
                )
                
                logger.info(f"AI analysis saved to database with ID: {analysis_result.id}")
                response_data['analysis_id'] = str(analysis_result.id)
                response_data['persisted'] = True
                
            except Exception as save_error:
                logger.warning(f"Failed to save analysis to database: {save_error}")
                response_data['persisted'] = False
                response_data['save_error'] = str(save_error)
            
            logger.info("Complete AI analysis generated successfully")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Combined AI analysis failed: {str(e)}")
            return Response({
                'status': 'error',
                'error_message': str(e),
                'summary': None,
                'tags_analysis': None,
                'processed_reviews': 0,
                'generated_at': datetime.now().isoformat(),
                'fallback': 'AI analysis generation failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetAIAnalysisAPIView(APIView):
    """API endpoint to retrieve persisted AI analysis results"""
    
    def get(self, request):
        """Get the latest AI analysis from database"""
        try:
            # Get parameters
            hotel_id = request.GET.get('hotel')
            
            # Get the most recent active analysis
            query = AIAnalysisResult.objects.filter(is_active=True)
            if hotel_id:
                query = query.filter(hotel_id=hotel_id)
            else:
                query = query.filter(hotel__isnull=True)
            
            latest_analysis = query.latest('created_at')
            
            # Format response to match frontend expectations
            response_data = {
                'status': 'success',
                'has_existing_analysis': True,
                'persisted': True,
                'analysis': {
                    'id': str(latest_analysis.id),
                    'summary': latest_analysis.summary_data,
                    'tags_analysis': latest_analysis.tags_analysis,
                    'sentiment_analysis': latest_analysis.sentiment_analysis,
                    'recommendations': latest_analysis.recommendations,
                    'processed_reviews': latest_analysis.total_reviews_analyzed,
                    'generated_at': latest_analysis.created_at.isoformat(),
                    'date_range': {
                        'start': latest_analysis.date_range_start,
                        'end': latest_analysis.date_range_end,
                        'days': latest_analysis.days_analyzed
                    },
                    'workflow_info': latest_analysis.workflow_info,
                    'agents_used': latest_analysis.agents_used
                }
            }
            
            logger.info(f"Retrieved persisted AI analysis: {latest_analysis.id}")
            return Response(response_data)
            
        except AIAnalysisResult.DoesNotExist:
            return Response({
                'status': 'no_data',
                'has_existing_analysis': False,
                'persisted': False,
                'message': 'No previous AI analysis found. Generate new analysis.',
                'analysis': None
            })
            
        except Exception as e:
            logger.error(f"Failed to retrieve AI analysis: {str(e)}")
            return Response({
                'status': 'error',
                'has_existing_analysis': False,
                'persisted': False,
                'error_message': str(e),
                'analysis': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _calculate_average_score_for_period(self, date_range):
        """Calculate average score for the analysis period"""
        try:
            from datetime import datetime
            from django.db.models import Avg
            
            if not date_range or 'start' not in date_range or 'end' not in date_range:
                # Fallback to overall average if no date range
                avg_score = Review.objects.aggregate(avg_score=Avg('ai_score'))['avg_score']
                return round(avg_score, 1) if avg_score else 3.0
                
            # Parse date range
            start_date = datetime.fromisoformat(date_range['start'])
            end_date = datetime.fromisoformat(date_range['end'])
            
            # Calculate average for the period
            avg_score = Review.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(avg_score=Avg('ai_score'))['avg_score']
            
            return round(avg_score, 1) if avg_score else 3.0
            
        except Exception as e:
            logger.warning(f"Failed to calculate average score: {e}")
            return 3.0


class ExportAPIView(APIView):
    """API endpoint for data export"""
    
    def get(self, request):
        """Export reviews data in various formats"""
        try:
            format_type = request.GET.get('format', 'json')
            hotel_id = request.GET.get('hotel')
            sentiment = request.GET.get('sentiment')
            
            # Get reviews
            reviews = Review.objects.all()
            
            if hotel_id:
                reviews = reviews.filter(hotel_id=hotel_id)
            
            if sentiment:
                reviews = reviews.filter(sentiment=sentiment)
            
            # Limit for performance
            reviews = reviews[:1000]
            
            if format_type == 'csv':
                return self._export_csv(reviews)
            elif format_type == 'excel':
                return self._export_excel(reviews)
            else:
                return self._export_json(reviews)
                
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    def _export_json(self, reviews):
        """Export as JSON"""
        data = []
        for review in reviews:
            data.append({
                'id': str(review.id),
                'hotel_name': review.hotel.name,
                'text': review.text,
                'sentiment': review.sentiment,
                'ai_score': review.ai_score,
                'original_rating': review.original_rating,
                'reviewer_name': review.reviewer_name,
                'date_posted': review.date_posted.isoformat() if review.date_posted else None,
                'created_at': review.created_at.isoformat()
            })
        
        response = JsonResponse({'reviews': data})
        response['Content-Disposition'] = 'attachment; filename="reviews_export.json"'
        return response
    
    def _export_csv(self, reviews):
        """Export as CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Hotel Name', 'Review Text', 'Sentiment', 'AI Score',
            'Original Rating', 'Reviewer Name', 'Date Posted', 'Created At'
        ])
        
        # Write data
        for review in reviews:
            writer.writerow([
                str(review.id),
                review.hotel.name,
                review.text,
                review.sentiment,
                review.ai_score,
                review.original_rating or '',
                review.reviewer_name or '',
                review.date_posted.strftime('%Y-%m-%d') if review.date_posted else '',
                review.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reviews_export.csv"'
        return response
    
    def _export_excel(self, reviews):
        """Export as Excel (simplified implementation)"""
        # For now, return CSV with Excel MIME type
        return self._export_csv(reviews)


class AgentStatusAPIView(APIView):
    """API endpoint for agent status monitoring"""
    
    def get(self, request):
        """Get current status of all agents"""
        try:
            # In production, this would check actual agent health
            agent_status = {
                'classifier': {'status': 'active', 'last_activity': '2024-01-01T12:00:00Z'},
                'scorer': {'status': 'active', 'last_activity': '2024-01-01T12:00:00Z'},
                'summarizer': {'status': 'active', 'last_activity': '2024-01-01T12:00:00Z'},
                'search': {'status': 'active', 'last_activity': '2024-01-01T12:00:00Z'},
                'security': {'status': 'active', 'last_activity': '2024-01-01T12:00:00Z'},
            }
            
            all_operational = all(
                agent['status'] == 'active' for agent in agent_status.values()
            )
            
            return Response({
                'agents': agent_status,
                'all_operational': all_operational,
                'last_check': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Agent status check failed: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentTasksAPIView(APIView):
    """API endpoint for agent task management"""
    
    def get(self, request):
        """Get agent task status"""
        try:
            tasks = AgentTask.objects.order_by('-created_at')[:20]
            
            task_data = []
            for task in tasks:
                task_data.append({
                    'id': str(task.id),
                    'agent_name': task.agent_name,
                    'task_type': task.task_type,
                    'status': task.status,
                    'created_at': task.created_at.isoformat(),
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'error_message': task.error_message
                })
            
            return Response({
                'tasks': task_data,
                'total_tasks': AgentTask.objects.count(),
                'active_tasks': AgentTask.objects.filter(status='running').count()
            })
            
        except Exception as e:
            logger.error(f"Task retrieval failed: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_object(self, task_id):
        """Get specific task by ID"""
        try:
            task = AgentTask.objects.get(id=task_id)
            return Response({
                'id': str(task.id),
                'agent_name': task.agent_name,
                'task_type': task.task_type,
                'status': task.status,
                'input_data': task.input_data,
                'output_data': task.output_data,
                'error_message': task.error_message,
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            })
            
        except AgentTask.DoesNotExist:
            return Response({
                'error': 'Task not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Task retrieval failed: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
