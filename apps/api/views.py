"""
API Views for Hotel Review Insight Platform
RESTful API endpoints for external integrations and AJAX calls
"""

from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
import json
import logging

from apps.reviews.models import Review, Hotel, ReviewBatch, AgentTask
from apps.analytics.models import AnalyticsReport, SentimentTrend
from .serializers import ReviewSerializer, HotelSerializer, AnalyticsReportSerializer
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
    
    def get(self, request):
        try:
            stats = {
                'total_reviews': Review.objects.count(),
                'total_hotels': Hotel.objects.count(),
                'processed_reviews': Review.objects.filter(processed=True).count(),
                'pending_reviews': Review.objects.filter(processed=False).count(),
                'sentiment_distribution': list(Review.objects.values('sentiment').annotate(count=Count('sentiment'))),
                'avg_score': Review.objects.aggregate(avg_score=Avg('ai_score'))['avg_score'] or 0,
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
            
            # Recent trends
            from datetime import datetime, timedelta
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            trends = SentimentTrend.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
            
            analytics_data = {
                'overview': {
                    'total_reviews': total_reviews,
                    'average_score': round(avg_score, 2),
                    'sentiment_distribution': list(sentiment_data),
                    'processed_reviews': Review.objects.filter(processed=True).count()
                },
                'trends': [
                    {
                        'date': trend.date,
                        'total_reviews': trend.total_reviews,
                        'average_score': trend.average_score,
                        'positive_percentage': trend.positive_percentage,
                        'negative_percentage': trend.negative_percentage
                    }
                    for trend in trends
                ]
            }
            
            return Response(analytics_data)
            
        except Exception as e:
            logger.error(f"Analytics retrieval failed: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class ProcessReviewsAPIView(APIView):
    """API endpoint for processing reviews with AI agents"""
    
    def post(self, request):
        """Process reviews using the multi-agent pipeline"""
        try:
            data = json.loads(request.body)
            
            # Get reviews to process
            if data.get('process_all'):
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
                agent_name='Multi-Agent Pipeline',
                task_type='batch_processing',
                status='pending',
                input_data={
                    'review_count': reviews.count(),
                    'process_all': data.get('process_all', False)
                }
            )
            
            # In production, this would trigger Celery task
            # For now, simulate processing
            task.status = 'running'
            task.save()
            
            # Simulate some processing
            processed_count = 0
            for review in reviews[:10]:  # Process first 10 for demo
                # Simulate AI processing
                if not review.sentiment or review.sentiment == 'neutral':
                    # Simple rule-based classification for demo
                    text_lower = review.text.lower()
                    if any(word in text_lower for word in ['great', 'excellent', 'amazing', 'perfect', 'love']):
                        review.sentiment = 'positive'
                        review.ai_score = 4.2
                    elif any(word in text_lower for word in ['terrible', 'awful', 'horrible', 'worst', 'hate']):
                        review.sentiment = 'negative'
                        review.ai_score = 1.8
                    else:
                        review.sentiment = 'neutral'
                        review.ai_score = 3.0
                    
                    review.processed = True
                    review.confidence_score = 0.85
                    review.save()
                    processed_count += 1
            
            # Complete task
            task.status = 'completed'
            task.output_data = {
                'processed_count': processed_count,
                'success': True
            }
            task.save()
            
            return JsonResponse({
                'success': True,
                'task_id': str(task.id),
                'processed_count': processed_count,
                'message': f'Successfully processed {processed_count} reviews'
            })
            
        except Exception as e:
            logger.error(f"Review processing failed: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
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
    """API endpoint for generating summaries"""
    
    def get(self, request):
        """Get summary for specified criteria"""
        try:
            hotel_id = request.GET.get('hotel')
            days = int(request.GET.get('days', 30))
            
            # Get reviews
            reviews = Review.objects.all()
            if hotel_id:
                reviews = reviews.filter(hotel_id=hotel_id)
            
            # Date filter
            from datetime import datetime, timedelta
            start_date = datetime.now() - timedelta(days=days)
            reviews = reviews.filter(created_at__gte=start_date)
            
            # Calculate summary statistics
            total_reviews = reviews.count()
            avg_score = reviews.aggregate(avg=Avg('ai_score'))['avg'] or 0
            
            sentiment_dist = reviews.values('sentiment').annotate(
                count=Count('sentiment')
            )
            
            # Generate summary (simplified)
            summary_text = f"Analysis of {total_reviews} reviews over the last {days} days. "
            
            if avg_score >= 4.0:
                summary_text += "Overall customer satisfaction is high. "
            elif avg_score <= 2.0:
                summary_text += "Customer satisfaction needs improvement. "
            else:
                summary_text += "Customer satisfaction is moderate. "
            
            # Top positive and negative themes (simplified)
            positive_reviews = reviews.filter(sentiment='positive')[:5]
            negative_reviews = reviews.filter(sentiment='negative')[:5]
            
            return Response({
                'summary': {
                    'text': summary_text,
                    'total_reviews': total_reviews,
                    'average_score': round(avg_score, 2),
                    'sentiment_distribution': list(sentiment_dist),
                    'date_range': {
                        'start': start_date.date(),
                        'end': datetime.now().date()
                    }
                },
                'insights': {
                    'positive_themes': [r.text[:100] + '...' for r in positive_reviews],
                    'negative_themes': [r.text[:100] + '...' for r in negative_reviews],
                }
            })
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
