"""
Professional Hotel Review Management Models
Streamlined for production use with optimal database design
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Index
import uuid


class Hotel(models.Model):
    """Core hotel entity"""
    name = models.CharField(max_length=200, db_index=True)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    website_url = models.URLField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'location'], 
                name='unique_hotel_location'
            )
        ]
        indexes = [
            Index(fields=['name']),
            Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.location})"


class ReviewSource(models.Model):
    """Review platform sources"""
    name = models.CharField(max_length=100, unique=True)
    website_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Review(models.Model):
    """Core review entity with AI analysis"""
    
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(
        Hotel, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        db_index=True
    )
    source = models.ForeignKey(
        ReviewSource, 
        on_delete=models.PROTECT,
        db_index=True
    )
    
    # Review content
    text = models.TextField()
    title = models.CharField(max_length=200, blank=True)
    original_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        null=True, 
        blank=True,
        help_text="Original rating from review platform (0-5 scale)"
    )
    
    # Reviewer information
    reviewer_name = models.CharField(max_length=100, blank=True)
    reviewer_location = models.CharField(max_length=100, blank=True)
    
    # Date information
    date_posted = models.DateTimeField(null=True, blank=True, db_index=True)
    date_stayed = models.DateField(null=True, blank=True)
    
    # AI Analysis Results
    sentiment = models.CharField(
        max_length=10, 
        choices=SENTIMENT_CHOICES,
        default='neutral',
        db_index=True
    )
    ai_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        default=3.0,
        help_text="AI-generated sentiment score (0-5 scale)"
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.5,
        help_text="AI confidence in analysis (0-1 scale)"
    )
    
    # AI-generated insights (JSON fields for flexibility)
    ai_keywords = models.JSONField(
        default=list,
        blank=True,
        help_text="AI-extracted keywords from review text"
    )
    ai_topics = models.JSONField(
        default=dict,
        blank=True,
        help_text="AI-identified topics and their relevance scores"
    )
    ai_summary = models.TextField(
        blank=True,
        help_text="AI-generated summary of the review"
    )
    
    # Processing status
    processed = models.BooleanField(default=False, db_index=True)
    processing_error = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['sentiment', 'ai_score']),
            Index(fields=['hotel', 'sentiment']),
            Index(fields=['date_posted', 'sentiment']),
            Index(fields=['processed', 'created_at']),
            Index(fields=['hotel', 'date_posted']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(ai_score__gte=0.0) & models.Q(ai_score__lte=5.0),
                name='valid_ai_score_range'
            ),
            models.CheckConstraint(
                check=models.Q(confidence_score__gte=0.0) & models.Q(confidence_score__lte=1.0),
                name='valid_confidence_range'
            ),
        ]
    
    def __str__(self):
        return f"Review for {self.hotel.name} - {self.sentiment} ({self.ai_score:.1f}/5)"
    
    @property
    def sentiment_emoji(self):
        """User-friendly sentiment representation"""
        return {
            'positive': '😊',
            'neutral': '😐', 
            'negative': '😞'
        }.get(self.sentiment, '❓')


class ReviewBatch(models.Model):
    """Track batch upload operations"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # File information
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0, help_text="File size in bytes")
    
    # Processing statistics
    total_reviews = models.PositiveIntegerField(default=0)
    processed_reviews = models.PositiveIntegerField(default=0)
    failed_reviews = models.PositiveIntegerField(default=0)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Timestamps
    upload_date = models.DateTimeField(auto_now_add=True)
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-upload_date']
        indexes = [
            Index(fields=['status', 'upload_date']),
            Index(fields=['uploaded_by', 'upload_date']),
        ]
    
    def __str__(self):
        return f"Batch {self.file_name} ({self.status})"
    
    @property
    def processing_progress(self):
        """Calculate processing progress percentage"""
        if self.total_reviews == 0:
            return 0
        return round((self.processed_reviews / self.total_reviews) * 100, 1)
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.processed_reviews == 0:
            return 0
        successful = self.processed_reviews - self.failed_reviews
        return round((successful / self.processed_reviews) * 100, 1)


class AgentTask(models.Model):
    """Simple agent task tracking for processing operations"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_name = models.CharField(max_length=100)
    task_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Task data (simplified)
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True) 
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['status', 'created_at']),
            Index(fields=['agent_name', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.agent_name} - {self.task_type} ({self.status})"


class AIAnalysisResult(models.Model):
    """Store AI analysis results for persistence across sessions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Analysis metadata
    analysis_type = models.CharField(
        max_length=50,
        choices=[
            ('combined', 'Combined Analysis'),
            ('summary', 'Summary Only'),
            ('sentiment', 'Sentiment Analysis'),
            ('tags', 'Tags Analysis'),
        ],
        default='combined',
        db_index=True,
        help_text="Type of AI analysis performed"
    )
    
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Specific hotel analyzed (null for all hotels)"
    )
    
    # Analysis parameters
    days_analyzed = models.PositiveIntegerField(
        default=30,
        help_text="Number of days of data analyzed"
    )
    date_range_start = models.DateField(help_text="Start date of analysis period")
    date_range_end = models.DateField(help_text="End date of analysis period")
    total_reviews_analyzed = models.PositiveIntegerField(help_text="Number of reviews analyzed")
    
    # AI Results (JSON fields)
    summary_data = models.JSONField(
        default=dict,
        help_text="AI-generated summary and insights"
    )
    sentiment_analysis = models.JSONField(
        default=dict,
        help_text="Sentiment analysis results and distribution"
    )
    tags_analysis = models.JSONField(
        default=dict,
        help_text="Tags, keywords, and topic analysis"
    )
    recommendations = models.JSONField(
        default=list,
        help_text="AI-generated recommendations"
    )
    
    # System metadata
    agents_used = models.JSONField(
        default=dict,
        help_text="Information about AI agents used in analysis"
    )
    workflow_info = models.JSONField(
        default=dict,
        help_text="Workflow and processing information"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this analysis is the current active one"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis_type', 'created_at']),
            models.Index(fields=['hotel', 'created_at']),
            models.Index(fields=['is_active', 'analysis_type']),
            models.Index(fields=['date_range_start', 'date_range_end']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(days_analyzed__gte=1, days_analyzed__lte=365),
                name='valid_days_analyzed_range'
            ),
            models.CheckConstraint(
                check=models.Q(total_reviews_analyzed__gte=0),
                name='valid_reviews_count'
            ),
        ]
        verbose_name = "AI Analysis Result"
        verbose_name_plural = "AI Analysis Results"
    
    def __str__(self):
        hotel_name = self.hotel.name if self.hotel else "All Hotels"
        return f"{self.get_analysis_type_display()} - {hotel_name} ({self.created_at.date()})"
    
    @property
    def analysis_summary(self):
        """Get a brief summary of the analysis"""
        return self.summary_data.get('text', '')[:100] + '...' if self.summary_data.get('text') else 'No summary available'
    
    @property
    def sentiment_distribution(self):
        """Get sentiment distribution in a readable format"""
        return self.sentiment_analysis.get('sentiment_distribution', {})
    
    @property
    def key_insights(self):
        """Get key insights from the analysis"""
        return self.summary_data.get('insights', {})