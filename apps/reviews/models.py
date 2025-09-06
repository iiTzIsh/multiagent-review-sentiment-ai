"""
Models for Hotel Review Management
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Hotel(models.Model):
    """Hotel information model"""
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ReviewSource(models.Model):
    """Source platforms for reviews (TripAdvisor, Booking.com, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField(blank=True)
    api_endpoint = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class Review(models.Model):
    """Individual hotel review model"""
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]
    
    # Basic review information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews')
    source = models.ForeignKey(ReviewSource, on_delete=models.CASCADE)
    
    # Review content
    text = models.TextField()
    title = models.CharField(max_length=200, blank=True)
    original_rating = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Review metadata
    reviewer_name = models.CharField(max_length=100, blank=True)
    reviewer_location = models.CharField(max_length=100, blank=True)
    date_posted = models.DateTimeField(null=True, blank=True)
    date_stayed = models.DateField(null=True, blank=True)
    
    # AI Analysis results
    sentiment = models.CharField(
        max_length=10, 
        choices=SENTIMENT_CHOICES,
        default='neutral'
    )
    ai_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        default=3.0
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        default=0.5
    )
    
    # Processing status
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sentiment']),
            models.Index(fields=['ai_score']),
            models.Index(fields=['date_posted']),
            models.Index(fields=['hotel']),
        ]
    
    def __str__(self):
        return f"Review for {self.hotel.name} - {self.sentiment}"


class ReviewBatch(models.Model):
    """Batch upload tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    total_reviews = models.PositiveIntegerField(default=0)
    processed_reviews = models.PositiveIntegerField(default=0)
    failed_reviews = models.PositiveIntegerField(default=0)
    
    # Processing status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    
    upload_date = models.DateTimeField(auto_now_add=True)
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"Batch {self.file_name} - {self.status}"
    
    @property
    def processing_progress(self):
        if self.total_reviews == 0:
            return 0
        return (self.processed_reviews / self.total_reviews) * 100


class ReviewSummary(models.Model):
    """AI-generated summaries of review collections"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='summaries')
    
    # Summary content
    summary_text = models.TextField()
    key_positives = models.JSONField(default=list)
    key_negatives = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    
    # Statistics
    total_reviews = models.PositiveIntegerField()
    average_score = models.FloatField()
    sentiment_distribution = models.JSONField(default=dict)
    
    # Date range for summary
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    
    # Meta information
    created_by_agent = models.CharField(max_length=100, default='Summary Agent')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Summary for {self.hotel.name} ({self.total_reviews} reviews)"


class SearchQuery(models.Model):
    """Track search queries for analytics"""
    query_text = models.CharField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    results_count = models.PositiveIntegerField()
    search_type = models.CharField(max_length=20, choices=[
        ('semantic', 'Semantic Search'),
        ('keyword', 'Keyword Search'),
        ('filter', 'Filter')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']


class AgentTask(models.Model):
    """Track agent processing tasks"""
    TASK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_name = models.CharField(max_length=100)
    task_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending')
    
    # Task data
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.agent_name} - {self.task_type} ({self.status})"
