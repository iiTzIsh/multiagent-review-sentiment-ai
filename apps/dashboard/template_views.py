"""
Template Views for Hotel Review Insight Platform
Django template-based views for web interface
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from datetime import datetime, timedelta

from apps.reviews.models import Review, Hotel, ReviewBatch, AgentTask
from apps.analytics.models import AnalyticsReport, SentimentTrend
from utils.file_processor import ReviewFileProcessor

logger = logging.getLogger(__name__)


def reviews_list(request):
    """Display paginated list of reviews"""
    # Get filter parameters
    hotel_id = request.GET.get('hotel')
    sentiment = request.GET.get('sentiment')
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset
    reviews = Review.objects.select_related('hotel').order_by('-created_at')
    
    # Apply filters
    if hotel_id:
        reviews = reviews.filter(hotel_id=hotel_id)
    
    if sentiment and sentiment != 'all':
        reviews = reviews.filter(sentiment=sentiment)
    
    if search_query:
        reviews = reviews.filter(
            Q(text__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(reviewer_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(reviews, 20)  # 20 reviews per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    hotels = Hotel.objects.all().order_by('name')
    sentiment_choices = Review.SENTIMENT_CHOICES
    
    context = {
        'page_obj': page_obj,
        'reviews': page_obj.object_list,
        'hotels': hotels,
        'sentiment_choices': sentiment_choices,
        'current_hotel': hotel_id,
        'current_sentiment': sentiment,
        'search_query': search_query,
        'total_count': reviews.count()
    }
    
    return render(request, 'dashboard/reviews.html', context)


def review_detail(request, review_id):
    """Display detailed view of a single review"""
    try:
        review = get_object_or_404(Review, id=review_id)
        
        # Get related reviews from same hotel
        related_reviews = Review.objects.filter(
            hotel=review.hotel
        ).exclude(id=review.id).order_by('-created_at')[:5]
        
        context = {
            'review': review,
            'related_reviews': related_reviews,
        }
        
        return render(request, 'dashboard/review_detail.html', context)
        
    except Exception as e:
        logger.error(f"Review detail error: {str(e)}")
        messages.error(request, f"Error loading review details: {str(e)}")
        return redirect('dashboard:reviews')


def batch_list(request):
    """Display list of review batches"""
    batches = ReviewBatch.objects.order_by('-created_at')
    
    # Add progress calculation
    for batch in batches:
        if batch.total_reviews > 0:
            batch.progress = (batch.processed_reviews / batch.total_reviews) * 100
        else:
            batch.progress = 0
    
    context = {
        'batches': batches
    }
    
    return render(request, 'dashboard/batches.html', context)


def batch_detail(request, batch_id):
    """Display detailed view of a review batch"""
    try:
        batch = get_object_or_404(ReviewBatch, id=batch_id)
        
        # Get batch reviews with pagination
        reviews = batch.reviews.select_related('hotel').order_by('-created_at')
        paginator = Paginator(reviews, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Calculate statistics
        total_reviews = batch.reviews.count()
        processed_reviews = batch.reviews.filter(processed=True).count()
        sentiment_dist = batch.reviews.values('sentiment').annotate(
            count=Count('sentiment')
        )
        
        progress = (processed_reviews / total_reviews * 100) if total_reviews > 0 else 0
        
        context = {
            'batch': batch,
            'page_obj': page_obj,
            'total_reviews': total_reviews,
            'processed_reviews': processed_reviews,
            'progress': progress,
            'sentiment_distribution': list(sentiment_dist)
        }
        
        return render(request, 'dashboard/batch_detail.html', context)
        
    except Exception as e:
        logger.error(f"Batch detail error: {str(e)}")
        messages.error(request, f"Error loading batch details: {str(e)}")
        return redirect('dashboard:batches')


def analytics_dashboard(request):
    """Display analytics and insights dashboard"""
    try:
        # Get date range
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Filter reviews by date range
        reviews = Review.objects.filter(created_at__date__gte=start_date)
        
        # Overall statistics
        total_reviews = reviews.count()
        processed_reviews = reviews.filter(processed=True).count()
        avg_score = reviews.aggregate(avg=Avg('ai_score'))['avg'] or 0
        
        # Sentiment distribution
        sentiment_data = reviews.values('sentiment').annotate(
            count=Count('sentiment')
        )
        
        sentiment_labels = []
        sentiment_values = []
        sentiment_colors = []
        
        for item in sentiment_data:
            if item['sentiment']:
                sentiment_labels.append(item['sentiment'].title())
                sentiment_values.append(item['count'])
                
                # Assign colors
                if item['sentiment'] == 'positive':
                    sentiment_colors.append('#28a745')
                elif item['sentiment'] == 'negative':
                    sentiment_colors.append('#dc3545')
                else:
                    sentiment_colors.append('#ffc107')
        
        # Score distribution
        score_ranges = [
            {'label': '1-2', 'min': 1, 'max': 2},
            {'label': '2-3', 'min': 2, 'max': 3},
            {'label': '3-4', 'min': 3, 'max': 4},
            {'label': '4-5', 'min': 4, 'max': 5},
        ]
        
        score_data = []
        for range_item in score_ranges:
            count = reviews.filter(
                ai_score__gte=range_item['min'],
                ai_score__lt=range_item['max']
            ).count()
            score_data.append({
                'label': range_item['label'],
                'count': count
            })
        
        # Top hotels by review count
        top_hotels = Hotel.objects.annotate(
            review_count=Count('reviews')
        ).filter(review_count__gt=0).order_by('-review_count')[:5]
        
        # Daily trends (last 30 days)
        daily_trends = []
        for i in range(min(days, 30)):
            day = end_date - timedelta(days=i)
            day_reviews = Review.objects.filter(created_at__date=day)
            
            daily_trends.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': day_reviews.count(),
                'avg_score': day_reviews.aggregate(avg=Avg('ai_score'))['avg'] or 0
            })
        
        daily_trends.reverse()  # Chronological order
        
        context = {
            'date_range': {
                'start': start_date,
                'end': end_date,
                'days': days
            },
            'statistics': {
                'total_reviews': total_reviews,
                'processed_reviews': processed_reviews,
                'processing_rate': (processed_reviews / total_reviews * 100) if total_reviews > 0 else 0,
                'average_score': round(avg_score, 2)
            },
            'sentiment_chart': {
                'labels': sentiment_labels,
                'data': sentiment_values,
                'colors': sentiment_colors
            },
            'score_distribution': score_data,
            'top_hotels': top_hotels,
            'daily_trends': daily_trends
        }
        
        return render(request, 'dashboard/analytics.html', context)
        
    except Exception as e:
        logger.error(f"Analytics dashboard error: {str(e)}")
        messages.error(request, f"Error loading analytics: {str(e)}")
        return render(request, 'dashboard/analytics.html', {'error': str(e)})


def reports_list(request):
    """Display list of generated reports"""
    reports = AnalyticsReport.objects.order_by('-generated_at')
    
    context = {
        'reports': reports
    }
    
    return render(request, 'dashboard/reports.html', context)


def generate_report(request):
    """Generate a new analytics report"""
    if request.method == 'POST':
        try:
            # Get parameters from form
            report_type = request.POST.get('report_type', 'overview')
            hotel_id = request.POST.get('hotel_id')
            days = int(request.POST.get('days', 30))
            
            # Date range
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Filter reviews
            reviews = Review.objects.filter(created_at__date__gte=start_date)
            if hotel_id:
                reviews = reviews.filter(hotel_id=hotel_id)
                hotel = get_object_or_404(Hotel, id=hotel_id)
            else:
                hotel = None
            
            # Calculate report data
            total_reviews = reviews.count()
            avg_score = reviews.aggregate(avg=Avg('ai_score'))['avg'] or 0
            
            sentiment_dist = {}
            for item in reviews.values('sentiment').annotate(count=Count('sentiment')):
                if item['sentiment']:
                    sentiment_dist[item['sentiment']] = item['count']
            
            # Create report
            report = AnalyticsReport.objects.create(
                report_type=report_type,
                hotel=hotel,
                date_from=start_date,
                date_to=end_date,
                total_reviews=total_reviews,
                average_score=avg_score,
                sentiment_distribution=sentiment_dist,
                generated_by=request.user if request.user.is_authenticated else None
            )
            
            messages.success(request, f'Report "{report.report_type}" generated successfully')
            return redirect('dashboard:reports')
            
        except Exception as e:
            logger.error(f"Report generation error: {str(e)}")
            messages.error(request, f"Error generating report: {str(e)}")
    
    # GET request - show form
    hotels = Hotel.objects.all().order_by('name')
    context = {
        'hotels': hotels,
        'report_types': [
            ('overview', 'Overview Report'),
            ('sentiment', 'Sentiment Analysis'),
            ('trends', 'Trend Analysis'),
            ('hotel', 'Hotel Specific'),
        ]
    }
    
    return render(request, 'dashboard/generate_report.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def upload_reviews(request):
    """Handle file upload for batch processing"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            }, status=400)
        
        file = request.FILES['file']
        batch_name = request.POST.get('batch_name', f'Upload_{timezone.now().strftime("%Y%m%d_%H%M%S")}')
        
        # Validate file type
        allowed_extensions = ['.csv', '.xlsx', '.json']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': f'File type not supported. Allowed: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # Create batch record
        batch = ReviewBatch.objects.create(
            name=batch_name,
            source_file=file.name,
            status='uploaded'
        )
        
        # Process file (this would typically be done asynchronously)
        try:
            # For demo purposes, we'll process synchronously
            # In production, this should be a Celery task
            
            batch.status = 'processing'
            batch.started_at = timezone.now()
            batch.save()
            
            # Use file processing utility
            processor = ReviewFileProcessor()
            result = processor.process_file(file, batch)
            
            # The ReviewFileProcessor updates batch internally, so we don't need to set these
            batch.status = 'completed'
            batch.completed_at = timezone.now()
            batch.save()
            
            return JsonResponse({
                'success': True,
                'batch_id': str(batch.id),
                'message': f'Successfully processed {result["processed"]} reviews',
                'stats': result
            })
            
        except Exception as e:
            batch.status = 'failed'
            batch.error_message = str(e)
            batch.save()
            raise e
            
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def search_reviews(request):
    """AJAX endpoint for searching reviews"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'Search query is required'
            })
        
        # Perform search
        reviews = Review.objects.select_related('hotel').filter(
            Q(text__icontains=query) |
            Q(title__icontains=query) |
            Q(hotel__name__icontains=query) |
            Q(reviewer_name__icontains=query)
        ).order_by('-created_at')[:20]
        
        results = []
        for review in reviews:
            results.append({
                'id': str(review.id),
                'title': review.title or 'Untitled Review',
                'text': review.text[:200] + '...' if len(review.text) > 200 else review.text,
                'hotel_name': review.hotel.name,
                'sentiment': review.sentiment,
                'ai_score': review.ai_score,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def agent_status(request):
    """Display current status of all AI agents"""
    try:
        # Get recent agent tasks
        recent_tasks = AgentTask.objects.order_by('-created_at')[:20]
        
        # Get agent statistics
        agent_stats = {}
        agent_names = [
            'ReviewClassifierAgent',
            'SentimentScorerAgent', 
            'SummaryAgent',
            'InformationRetrievalAgent',
            'SecurityAgent'
        ]
        
        for agent_name in agent_names:
            tasks = AgentTask.objects.filter(agent_name=agent_name)
            
            agent_stats[agent_name] = {
                'total_tasks': tasks.count(),
                'completed_tasks': tasks.filter(status='completed').count(),
                'failed_tasks': tasks.filter(status='failed').count(),
                'running_tasks': tasks.filter(status='running').count(),
                'last_activity': tasks.order_by('-created_at').first()
            }
        
        context = {
            'recent_tasks': recent_tasks,
            'agent_stats': agent_stats,
            'system_status': 'operational'  # This would be determined by actual health checks
        }
        
        return render(request, 'dashboard/agent_status.html', context)
        
    except Exception as e:
        logger.error(f"Agent status error: {str(e)}")
        messages.error(request, f"Error loading agent status: {str(e)}")
        return render(request, 'dashboard/agent_status.html', {'error': str(e)})


def hotels_list(request):
    """Display list of hotels with statistics"""
    # Annotate hotels with statistics
    hotels = Hotel.objects.annotate(
        review_count=Count('reviews'),
        avg_score=Avg('reviews__ai_score'),
        positive_reviews=Count('reviews', filter=Q(reviews__sentiment='positive')),
        negative_reviews=Count('reviews', filter=Q(reviews__sentiment='negative'))
    ).order_by('-review_count')
    
    # Add percentage calculations
    for hotel in hotels:
        if hotel.review_count > 0:
            hotel.positive_percentage = (hotel.positive_reviews / hotel.review_count) * 100
            hotel.negative_percentage = (hotel.negative_reviews / hotel.review_count) * 100
        else:
            hotel.positive_percentage = 0
            hotel.negative_percentage = 0
    
    context = {
        'hotels': hotels
    }
    
    return render(request, 'dashboard/hotels.html', context)


def hotel_detail(request, hotel_id):
    """Display detailed view of a single hotel"""
    try:
        hotel = get_object_or_404(Hotel, id=hotel_id)
        
        # Get hotel reviews with pagination
        reviews = hotel.reviews.order_by('-created_at')
        paginator = Paginator(reviews, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Calculate statistics
        total_reviews = hotel.reviews.count()
        avg_score = hotel.reviews.aggregate(avg=Avg('ai_score'))['avg'] or 0
        
        sentiment_dist = hotel.reviews.values('sentiment').annotate(
            count=Count('sentiment')
        )
        
        # Recent trends (last 30 days)
        from datetime import datetime, timedelta
        trend_data = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).date()
            day_reviews = hotel.reviews.filter(created_at__date=date)
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': day_reviews.count(),
                'avg_score': day_reviews.aggregate(avg=Avg('ai_score'))['avg'] or 0
            })
        
        trend_data.reverse()
        
        context = {
            'hotel': hotel,
            'page_obj': page_obj,
            'total_reviews': total_reviews,
            'average_score': round(avg_score, 2),
            'sentiment_distribution': list(sentiment_dist),
            'trend_data': trend_data
        }
        
        return render(request, 'dashboard/hotel_detail.html', context)
        
    except Exception as e:
        logger.error(f"Hotel detail error: {str(e)}")
        messages.error(request, f"Error loading hotel details: {str(e)}")
        return redirect('dashboard:hotels')
