"""
Dashboard Views for Hotel Review Insight Platform
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import pandas as pd
import io

from apps.reviews.models import Review, Hotel, ReviewBatch, ReviewSummary
from apps.analytics.models import SentimentTrend, AnalyticsReport
from utils.file_processor import ReviewFileProcessor
from utils.chart_generator import ChartGenerator
# from agents.base_agent import AgentOrchestrator  # Commented out until crewai is installed


def dashboard_home(request):
    """Main dashboard view"""
    # Get basic statistics
    total_reviews = Review.objects.count()
    total_hotels = Hotel.objects.count()
    processed_reviews = Review.objects.filter(processed=True).count()
    
    # Get recent activity
    recent_reviews = Review.objects.order_by('-created_at')[:5]
    recent_batches = ReviewBatch.objects.order_by('-upload_date')[:5]
    
    # Sentiment distribution
    sentiment_data = Review.objects.values('sentiment').annotate(
        count=Count('sentiment')
    )
    
    # Score distribution - updated for chart compatibility
    score_data = []
    for i in range(1, 6):  # 1 to 5 stars
        # Try AI score first, then fallback to original rating
        ai_count = Review.objects.filter(ai_score__gte=i-0.5, ai_score__lt=i+0.5).count()
        original_count = Review.objects.filter(original_rating=i, ai_score__isnull=True).count()
        total_count = ai_count + original_count
        score_data.append(total_count)
    
    context = {
        'total_reviews': total_reviews,
        'total_hotels': total_hotels,
        'processed_reviews': processed_reviews,
        'processing_rate': (processed_reviews / total_reviews * 100) if total_reviews > 0 else 0,
        'recent_reviews': recent_reviews,
        'recent_batches': recent_batches,
        'sentiment_data': list(sentiment_data),
        'score_data': score_data,
        'page_title': 'Dashboard',
    }
    
    return render(request, 'dashboard/home.html', context)


def upload_reviews(request):
    """Upload and process review files"""
    if request.method == 'POST':
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if 'file' not in request.FILES:
            error_msg = 'No file selected'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('dashboard:upload_reviews')
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        if not uploaded_file.name.lower().endswith('.csv'):
            error_msg = 'Please upload a CSV file only'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('dashboard:upload_reviews')
        
        # Validate file size (10MB limit)
        if uploaded_file.size > 10 * 1024 * 1024:
            error_msg = 'File size must be less than 10MB'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('dashboard:upload_reviews')
        
        try:
            # Get or create a default user for uploads
            from django.contrib.auth.models import User
            if request.user.is_authenticated:
                upload_user = request.user
            else:
                # Get or create a default user for anonymous uploads
                upload_user, created = User.objects.get_or_create(
                    username='anonymous_uploader',
                    defaults={
                        'email': 'anonymous@example.com',
                        'first_name': 'Anonymous',
                        'last_name': 'User'
                    }
                )
            
            # Create a new batch
            batch = ReviewBatch.objects.create(
                uploaded_by=upload_user,
                file_name=uploaded_file.name
            )
            
            # Process the file
            from utils.file_processor import ReviewFileProcessor
            processor = ReviewFileProcessor()
            result = processor.process_file(uploaded_file, batch)
            
            if result['success']:
                success_msg = f'Successfully uploaded and processed {result["processed"]} reviews'
                if is_ajax:
                    return JsonResponse({
                        'success': True, 
                        'message': success_msg,
                        'processed': result['processed'],
                        'batch_id': batch.id
                    })
                messages.success(request, success_msg)
                return redirect('dashboard:upload_reviews')
            else:
                error_msg = f'Upload failed: {result["error"]}'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                
        except Exception as e:
            error_msg = f'Upload error: {str(e)}'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
    
    # Get recent batches
    recent_batches = ReviewBatch.objects.order_by('-upload_date')[:10]
    
    context = {
        'recent_batches': recent_batches,
        'page_title': 'Upload Reviews',
    }
    
    return render(request, 'dashboard/upload.html', context)


def batch_detail(request, batch_id):
    """View details of a specific batch"""
    batch = get_object_or_404(ReviewBatch, id=batch_id)
    
    # Get reviews from this batch
    reviews = Review.objects.filter(
        created_at__gte=batch.upload_date,
        created_at__lte=batch.upload_date + timedelta(minutes=10)
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Batch statistics
    sentiment_stats = reviews.values('sentiment').annotate(count=Count('sentiment'))
    avg_score = reviews.aggregate(avg_score=Avg('ai_score'))['avg_score'] or 0
    
    context = {
        'batch': batch,
        'page_obj': page_obj,
        'sentiment_stats': list(sentiment_stats),
        'avg_score': round(avg_score, 1),
        'page_title': f'Batch: {batch.file_name}',
    }
    
    return render(request, 'dashboard/batch_detail.html', context)


def reviews_list(request):
    """List and filter reviews"""
    reviews = Review.objects.all()
    
    # Calculate statistics
    total_reviews = reviews.count()
    positive_reviews = reviews.filter(sentiment='positive').count()
    negative_reviews = reviews.filter(sentiment='negative').count()
    neutral_reviews = reviews.filter(sentiment='neutral').count()
    average_score = reviews.aggregate(avg_score=Avg('ai_score'))['avg_score'] or 0
    
    # Apply filters
    hotel_id = request.GET.get('hotel')
    sentiment = request.GET.get('sentiment')
    min_score = request.GET.get('min_score')
    max_score = request.GET.get('max_score')
    search = request.GET.get('search')
    
    if hotel_id:
        reviews = reviews.filter(hotel_id=hotel_id)
    
    if sentiment:
        reviews = reviews.filter(sentiment=sentiment)
    
    if min_score:
        reviews = reviews.filter(ai_score__gte=float(min_score))
    
    if max_score:
        reviews = reviews.filter(ai_score__lte=float(max_score))
    
    if search:
        reviews = reviews.filter(
            Q(text__icontains=search) | Q(title__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(reviews.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get hotels for filter dropdown
    hotels = Hotel.objects.all()
    
    context = {
        'page_obj': page_obj,
        'reviews': page_obj.object_list,  # Add this line
        'total_count': paginator.count,   # Add total count for pagination info
        'hotels': hotels,
        'total_reviews': total_reviews,
        'positive_reviews': positive_reviews,
        'negative_reviews': negative_reviews,
        'neutral_reviews': neutral_reviews,
        'average_score': average_score,
        'sentiment_choices': [
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('neutral', 'Neutral'),
        ],
        'current_hotel': hotel_id,
        'current_sentiment': sentiment,
        'current_filters': {
            'hotel': hotel_id,
            'sentiment': sentiment,
            'min_score': min_score,
            'max_score': max_score,
            'search': search,
        },
        'page_title': 'All Reviews',
    }
    
    return render(request, 'dashboard/reviews.html', context)


def review_detail(request, review_id):
    """View individual review details"""
    review = get_object_or_404(Review, id=review_id)
    
    context = {
        'review': review,
        'page_title': f'Review Detail',
    }
    
    return render(request, 'dashboard/review_detail.html', context)


def analytics_overview(request):
    """Analytics overview page"""
    # Get basic stats
    total_reviews = Review.objects.count()
    total_hotels = Hotel.objects.count()
    processed_reviews = Review.objects.filter(processed=True).count()
    
    # Calculate averages
    avg_score = Review.objects.aggregate(avg_score=Avg('ai_score'))['avg_score'] or 0
    processing_rate = (processed_reviews / total_reviews * 100) if total_reviews > 0 else 0
    
    # Sentiment distribution
    sentiment_data = list(Review.objects.exclude(sentiment__isnull=True).values('sentiment').annotate(count=Count('sentiment')))
    
    # Calculate sentiment percentages
    positive_count = Review.objects.filter(sentiment='positive').count()
    negative_count = Review.objects.filter(sentiment='negative').count()
    neutral_count = Review.objects.filter(sentiment='neutral').count()
    
    positive_percentage = (positive_count / total_reviews * 100) if total_reviews > 0 else 0
    negative_percentage = (negative_count / total_reviews * 100) if total_reviews > 0 else 0
    neutral_percentage = (neutral_count / total_reviews * 100) if total_reviews > 0 else 0
    
    # Top hotels by review count
    top_hotels = Hotel.objects.annotate(
        review_count=Count('reviews'),
        avg_score=Avg('reviews__ai_score')
    ).filter(review_count__gt=0).order_by('-review_count')[:5]
    
    # Sentiment trends (last 7 days) - simplified approach
    sentiment_trends = []
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        # Get reviews created on this date
        daily_reviews = Review.objects.filter(created_at__date=date)
        sentiment_trends.append({
            'date': date.strftime('%Y-%m-%d'),
            'positive_count': daily_reviews.filter(sentiment='positive').count(),
            'neutral_count': daily_reviews.filter(sentiment='neutral').count(),
            'negative_count': daily_reviews.filter(sentiment='negative').count()
        })
    
    # Score distribution
    score_data = []
    for i in range(1, 6):  # 1 to 5 stars
        count = Review.objects.filter(ai_score__gte=i-0.5, ai_score__lt=i+0.5).count()
        score_data.append(count)
    
    # Recent activity
    recent_reviews = Review.objects.select_related('hotel').order_by('-created_at')[:10]
    
    # Group statistics for template
    statistics = {
        'total_reviews': total_reviews,
        'processed_reviews': processed_reviews,
        'processing_rate': round(processing_rate, 1),
        'average_score': round(avg_score, 1),
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
    }
    
    context = {
        'statistics': statistics,
        'total_reviews': total_reviews,
        'total_hotels': total_hotels,
        'processed_reviews': processed_reviews,
        'processing_rate': round(processing_rate, 1),
        'avg_score': round(avg_score, 1),
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'positive_percentage': round(positive_percentage, 1),
        'negative_percentage': round(negative_percentage, 1),
        'neutral_percentage': round(neutral_percentage, 1),
        'sentiment_data': sentiment_data,
        'sentiment_trends': sentiment_trends,
        'score_data': score_data,
        'top_hotels': top_hotels,
        'recent_reviews': recent_reviews,
        'page_title': 'Analytics',
    }
    
    return render(request, 'dashboard/analytics.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def search_reviews(request):
    """AJAX endpoint for searching reviews"""
    try:
        data = json.loads(request.body)
        query = data.get('query', '')
        search_type = data.get('type', 'semantic')
        
        # Initialize search agent (simplified for now)
        from agents.search.agent import InformationRetrievalAgent
        
        search_agent = InformationRetrievalAgent()
        
        # Get all reviews for search
        reviews = Review.objects.all().values(
            'id', 'text', 'sentiment', 'ai_score', 'hotel__name'
        )
        
        # Index reviews
        review_list = [
            {
                'id': str(r['id']),
                'text': r['text'],
                'sentiment': r['sentiment'],
                'score': r['ai_score'],
                'hotel': r['hotel__name']
            }
            for r in reviews
        ]
        
        search_agent.index_reviews(review_list)
        
        # Perform search
        if search_type == 'semantic':
            results = search_agent.semantic_search(query, top_k=20)
        elif search_type == 'keyword':
            results = search_agent.keyword_search(query)
        else:
            results = search_agent.filter_reviews(query)
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def export_data(request):
    """Export reviews data"""
    format_type = request.GET.get('format', 'csv')
    hotel_id = request.GET.get('hotel')
    
    # Get reviews
    reviews = Review.objects.all()
    if hotel_id:
        reviews = reviews.filter(hotel_id=hotel_id)
    
    if format_type == 'csv':
        # Create CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reviews_export.csv"'
        
        # Convert to DataFrame and export
        data = reviews.values(
            'hotel__name', 'text', 'sentiment', 'ai_score',
            'original_rating', 'date_posted', 'reviewer_name'
        )
        
        df = pd.DataFrame(list(data))
        df.to_csv(response, index=False)
        
        return response
    
    elif format_type == 'json':
        # Create JSON export
        data = list(reviews.values(
            'id', 'hotel__name', 'text', 'sentiment', 'ai_score',
            'original_rating', 'date_posted', 'reviewer_name'
        ))
        
        response = JsonResponse({'reviews': data})
        response['Content-Disposition'] = 'attachment; filename="reviews_export.json"'
        return response
    
    else:
        messages.error(request, 'Unsupported export format')
        return redirect('dashboard:reviews_list')


def generate_report(request):
    """Generate analytics report"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'weekly')
        hotel_id = request.POST.get('hotel')
        format_type = request.POST.get('format', 'pdf')
        
        try:
            # Date range based on report type
            end_date = timezone.now()
            if report_type == 'daily':
                start_date = end_date - timedelta(days=1)
            elif report_type == 'weekly':
                start_date = end_date - timedelta(days=7)
            elif report_type == 'monthly':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            # Create report
            report = AnalyticsReport.objects.create(
                title=f'{report_type.title()} Report',
                report_type=report_type,
                hotel_id=hotel_id,
                format=format_type,
                date_from=start_date,
                date_to=end_date,
                generated_by=request.user if request.user.is_authenticated else None
            )
            
            # Generate report data (simplified)
            report_data = {
                'title': report.title,
                'period': f"{start_date.date()} to {end_date.date()}",
                'total_reviews': Review.objects.filter(
                    created_at__gte=start_date,
                    created_at__lte=end_date
                ).count(),
                'avg_score': Review.objects.filter(
                    created_at__gte=start_date,
                    created_at__lte=end_date
                ).aggregate(avg=Avg('ai_score'))['avg'] or 0,
            }
            
            report.data = report_data
            report.save()
            
            messages.success(request, 'Report generated successfully')
            return redirect('dashboard:report_detail', report_id=report.id)
            
        except Exception as e:
            messages.error(request, f'Report generation failed: {str(e)}')
    
    # Get hotels for dropdown
    hotels = Hotel.objects.all()
    
    context = {
        'hotels': hotels,
        'page_title': 'Generate Report',
    }
    
    return render(request, 'dashboard/generate_report.html', context)


def report_detail(request, report_id):
    """View generated report details"""
    report = get_object_or_404(AnalyticsReport, id=report_id)
    
    context = {
        'report': report,
        'page_title': f'Report: {report.title}',
    }
    
    return render(request, 'dashboard/report_detail.html', context)


@require_http_methods(["POST"])
def process_reviews_ajax(request):
    """AJAX endpoint to process unprocessed reviews"""
    try:
        import json
        from django.core.management import call_command
        from io import StringIO
        import sys
        
        # Parse request data
        data = json.loads(request.body)
        batch_size = data.get('batch_size', 50)
        
        # Capture command output
        out = StringIO()
        
        # Get count of unprocessed reviews before processing
        unprocessed_count = Review.objects.filter(
            Q(processed=False) | Q(sentiment__isnull=True) | Q(ai_score__isnull=True)
        ).count()
        
        if unprocessed_count == 0:
            return JsonResponse({
                'success': True,
                'message': 'All reviews are already processed',
                'processed_count': 0,
                'unprocessed_count': 0
            })
        
        # Run the processing command
        try:
            call_command('process_with_crewai', batch_size=batch_size, stdout=out)
            
            # Get count after processing
            unprocessed_after = Review.objects.filter(
                Q(processed=False) | Q(sentiment__isnull=True) | Q(ai_score__isnull=True)
            ).count()
            
            processed_count = unprocessed_count - unprocessed_after
            
            return JsonResponse({
                'success': True,
                'message': 'Reviews processed successfully',
                'processed_count': processed_count,
                'unprocessed_count': unprocessed_after,
                'total_reviews': Review.objects.count()
            })
            
        except Exception as cmd_error:
            return JsonResponse({
                'success': False,
                'error': f'Processing command failed: {str(cmd_error)}'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Request processing failed: {str(e)}'
        })
