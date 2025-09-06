"""
Serializers for Hotel Review Insight Platform API
DRF serializers for converting Django models to JSON and vice versa
"""

from rest_framework import serializers
from apps.reviews.models import Review, Hotel, ReviewBatch, AgentTask
from apps.analytics.models import AnalyticsReport, SentimentTrend


class HotelSerializer(serializers.ModelSerializer):
    """Serializer for Hotel model"""
    
    review_count = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()
    sentiment_distribution = serializers.SerializerMethodField()
    
    class Meta:
        model = Hotel
        fields = [
            'id', 'name', 'address', 'city', 'country',
            'description', 'amenities', 'star_rating',
            'created_at', 'updated_at', 'review_count',
            'average_score', 'sentiment_distribution'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_review_count(self, obj):
        """Get total number of reviews for this hotel"""
        return obj.reviews.count()
    
    def get_average_score(self, obj):
        """Get average AI score for this hotel"""
        from django.db.models import Avg
        avg_score = obj.reviews.aggregate(avg=Avg('ai_score'))['avg']
        return round(avg_score, 2) if avg_score else 0.0
    
    def get_sentiment_distribution(self, obj):
        """Get sentiment distribution for this hotel"""
        from django.db.models import Count
        
        distribution = obj.reviews.values('sentiment').annotate(
            count=Count('sentiment')
        )
        
        # Convert to dictionary
        result = {'positive': 0, 'negative': 0, 'neutral': 0}
        for item in distribution:
            if item['sentiment']:
                result[item['sentiment']] = item['count']
        
        return result


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    hotel_city = serializers.CharField(source='hotel.city', read_only=True)
    processing_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'hotel', 'hotel_name', 'hotel_city', 'title', 'text',
            'reviewer_name', 'reviewer_location', 'date_posted',
            'original_rating', 'source_platform', 'sentiment',
            'ai_score', 'confidence_score', 'keywords',
            'summary', 'processed', 'processing_duration',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sentiment', 'ai_score', 'confidence_score',
            'keywords', 'summary', 'processed', 'created_at', 'updated_at'
        ]
    
    def get_processing_duration(self, obj):
        """Calculate processing duration if available"""
        if obj.processed and obj.updated_at and obj.created_at:
            delta = obj.updated_at - obj.created_at
            return delta.total_seconds()
        return None
    
    def validate_text(self, value):
        """Validate review text"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Review text must be at least 10 characters long."
            )
        return value.strip()
    
    def validate_original_rating(self, value):
        """Validate original rating if provided"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value


class ReviewBatchSerializer(serializers.ModelSerializer):
    """Serializer for ReviewBatch model"""
    
    processing_progress = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewBatch
        fields = [
            'id', 'name', 'description', 'source_file', 'total_reviews',
            'processed_reviews', 'failed_reviews', 'status',
            'processing_progress', 'review_count', 'created_at',
            'started_at', 'completed_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'processed_reviews', 'failed_reviews', 'status',
            'created_at', 'started_at', 'completed_at', 'error_message'
        ]
    
    def get_processing_progress(self, obj):
        """Calculate processing progress percentage"""
        if obj.total_reviews == 0:
            return 0
        
        return round((obj.processed_reviews / obj.total_reviews) * 100, 2)
    
    def get_review_count(self, obj):
        """Get actual count of related reviews"""
        return obj.reviews.count()


class AgentTaskSerializer(serializers.ModelSerializer):
    """Serializer for AgentTask model"""
    
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentTask
        fields = [
            'id', 'agent_name', 'task_type', 'status',
            'input_data', 'output_data', 'error_message',
            'duration', 'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'started_at', 'completed_at'
        ]
    
    def get_duration(self, obj):
        """Calculate task duration if completed"""
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return delta.total_seconds()
        elif obj.started_at:
            from django.utils import timezone
            delta = timezone.now() - obj.started_at
            return delta.total_seconds()
        return None


class AnalyticsReportSerializer(serializers.ModelSerializer):
    """Serializer for AnalyticsReport model"""
    
    class Meta:
        model = AnalyticsReport
        fields = [
            'id', 'report_type', 'hotel', 'date_from', 'date_to',
            'total_reviews', 'average_score', 'sentiment_distribution',
            'top_keywords', 'insights', 'charts_data',
            'generated_at', 'generated_by'
        ]
        read_only_fields = ['id', 'generated_at']


class SentimentTrendSerializer(serializers.ModelSerializer):
    """Serializer for SentimentTrend model"""
    
    class Meta:
        model = SentimentTrend
        fields = [
            'id', 'hotel', 'date', 'total_reviews',
            'positive_count', 'negative_count', 'neutral_count',
            'average_score', 'positive_percentage',
            'negative_percentage', 'neutral_percentage'
        ]
        read_only_fields = ['id']


# Nested serializers for detailed responses
class DetailedHotelSerializer(HotelSerializer):
    """Detailed hotel serializer with recent reviews"""
    
    recent_reviews = serializers.SerializerMethodField()
    monthly_trends = serializers.SerializerMethodField()
    
    class Meta(HotelSerializer.Meta):
        fields = HotelSerializer.Meta.fields + [
            'recent_reviews', 'monthly_trends'
        ]
    
    def get_recent_reviews(self, obj):
        """Get 5 most recent reviews"""
        recent = obj.reviews.order_by('-created_at')[:5]
        return ReviewSerializer(recent, many=True, context=self.context).data
    
    def get_monthly_trends(self, obj):
        """Get monthly sentiment trends for this hotel"""
        from datetime import datetime, timedelta
        from django.db.models import Count, Avg
        
        # Get trends for last 6 months
        trends = []
        for i in range(6):
            end_date = datetime.now().date() - timedelta(days=i*30)
            start_date = end_date - timedelta(days=30)
            
            month_reviews = obj.reviews.filter(
                created_at__date__gte=start_date,
                created_at__date__lt=end_date
            )
            
            if month_reviews.exists():
                sentiment_dist = month_reviews.values('sentiment').annotate(
                    count=Count('sentiment')
                )
                
                avg_score = month_reviews.aggregate(
                    avg=Avg('ai_score')
                )['avg'] or 0
                
                trends.append({
                    'month': start_date.strftime('%Y-%m'),
                    'total_reviews': month_reviews.count(),
                    'average_score': round(avg_score, 2),
                    'sentiment_distribution': list(sentiment_dist)
                })
        
        return trends[::-1]  # Reverse to get chronological order


class ReviewSearchSerializer(serializers.Serializer):
    """Serializer for review search requests"""
    
    query = serializers.CharField(max_length=500)
    search_type = serializers.ChoiceField(
        choices=['semantic', 'keyword', 'filter'],
        default='semantic'
    )
    hotel_id = serializers.UUIDField(required=False)
    sentiment = serializers.ChoiceField(
        choices=[('positive', 'Positive'), ('negative', 'Negative'), ('neutral', 'Neutral')],
        required=False
    )
    min_score = serializers.FloatField(min_value=0, max_value=5, required=False)
    max_score = serializers.FloatField(min_value=0, max_value=5, required=False)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=20)


class BulkProcessSerializer(serializers.Serializer):
    """Serializer for bulk processing requests"""
    
    review_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of review IDs to process. If not provided, all unprocessed reviews will be processed."
    )
    process_all = serializers.BooleanField(
        default=False,
        help_text="Process all unprocessed reviews"
    )
    force_reprocess = serializers.BooleanField(
        default=False,
        help_text="Reprocess already processed reviews"
    )
    
    def validate(self, attrs):
        """Validate the request"""
        review_ids = attrs.get('review_ids', [])
        process_all = attrs.get('process_all', False)
        
        if not review_ids and not process_all:
            raise serializers.ValidationError(
                "Either provide review_ids or set process_all to True"
            )
        
        return attrs


class ExportRequestSerializer(serializers.Serializer):
    """Serializer for data export requests"""
    
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'excel'],
        default='json'
    )
    hotel_id = serializers.UUIDField(required=False)
    sentiment = serializers.ChoiceField(
        choices=[('positive', 'Positive'), ('negative', 'Negative'), ('neutral', 'Neutral')],
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    include_processed_only = serializers.BooleanField(default=True)
    limit = serializers.IntegerField(min_value=1, max_value=10000, default=1000)


class SummaryRequestSerializer(serializers.Serializer):
    """Serializer for summary generation requests"""
    
    hotel_id = serializers.UUIDField(required=False)
    days = serializers.IntegerField(min_value=1, max_value=365, default=30)
    sentiment_filter = serializers.ChoiceField(
        choices=[('positive', 'Positive'), ('negative', 'Negative'), ('neutral', 'Neutral')],
        required=False
    )
    min_reviews = serializers.IntegerField(min_value=1, default=5)
    include_insights = serializers.BooleanField(default=True)
    include_recommendations = serializers.BooleanField(default=True)


# Response serializers for consistent API responses
class APIResponseSerializer(serializers.Serializer):
    """Base serializer for API responses"""
    
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)
    data = serializers.JSONField(required=False)
    errors = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField(read_only=True)


class PaginatedResponseSerializer(APIResponseSerializer):
    """Serializer for paginated responses"""
    
    count = serializers.IntegerField()
    next = serializers.URLField(required=False, allow_null=True)
    previous = serializers.URLField(required=False, allow_null=True)
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()


class SearchResultSerializer(serializers.Serializer):
    """Serializer for search results"""
    
    id = serializers.UUIDField()
    text = serializers.CharField()
    sentiment = serializers.CharField()
    score = serializers.FloatField()
    hotel = serializers.CharField()
    similarity = serializers.FloatField(required=False)
    matched_keywords = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    relevance_score = serializers.FloatField(required=False)


class AgentStatusSerializer(serializers.Serializer):
    """Serializer for agent status information"""
    
    agent_name = serializers.CharField()
    status = serializers.ChoiceField(
        choices=['active', 'inactive', 'error', 'maintenance']
    )
    last_activity = serializers.DateTimeField()
    current_task = serializers.CharField(required=False, allow_null=True)
    health_score = serializers.FloatField(min_value=0, max_value=1, required=False)
    error_message = serializers.CharField(required=False, allow_null=True)
