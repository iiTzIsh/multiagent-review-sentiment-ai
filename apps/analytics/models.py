"""
Models for Analytics and Reporting
"""

from django.db import models
from django.contrib.auth.models import User
from apps.reviews.models import Hotel, Review
import uuid


class AnalyticsReport(models.Model):
    """Generated analytics reports"""
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('custom', 'Custom Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, null=True, blank=True)
    
    # Report content
    data = models.JSONField(default=dict)
    file_path = models.FileField(upload_to='reports/', null=True, blank=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Date range
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    
    # Generation info
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.report_type}"


class SentimentTrend(models.Model):
    """Track sentiment trends over time"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    date = models.DateField()
    
    # Daily statistics
    total_reviews = models.PositiveIntegerField(default=0)
    positive_count = models.PositiveIntegerField(default=0)
    neutral_count = models.PositiveIntegerField(default=0)
    negative_count = models.PositiveIntegerField(default=0)
    
    average_score = models.FloatField(default=0.0)
    sentiment_score = models.FloatField(default=0.0)  # Overall sentiment score
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['hotel', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.hotel.name} - {self.date}"
    
    @property
    def positive_percentage(self):
        if self.total_reviews == 0:
            return 0
        return (self.positive_count / self.total_reviews) * 100
    
    @property
    def negative_percentage(self):
        if self.total_reviews == 0:
            return 0
        return (self.negative_count / self.total_reviews) * 100


class KeywordFrequency(models.Model):
    """Track keyword frequency in reviews"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=100)
    frequency = models.PositiveIntegerField(default=0)
    sentiment_context = models.CharField(max_length=20, choices=[
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ])
    
    # Time period
    date_from = models.DateField()
    date_to = models.DateField()
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hotel', 'keyword', 'sentiment_context', 'date_from', 'date_to']
        ordering = ['-frequency']
    
    def __str__(self):
        return f"{self.keyword} ({self.frequency})"


class CompetitorComparison(models.Model):
    """Compare hotels against competitors"""
    primary_hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='comparisons')
    competitor_hotels = models.ManyToManyField(Hotel, related_name='competitor_comparisons')
    
    # Comparison metrics
    comparison_data = models.JSONField(default=dict)
    
    # Analysis period
    analysis_date = models.DateField()
    date_from = models.DateField()
    date_to = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comparison for {self.primary_hotel.name}"


class UserEngagement(models.Model):
    """Track user engagement with the platform"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    
    # Activity metrics
    login_count = models.PositiveIntegerField(default=0)
    searches_performed = models.PositiveIntegerField(default=0)
    reports_generated = models.PositiveIntegerField(default=0)
    reviews_processed = models.PositiveIntegerField(default=0)
    
    # Time spent (in minutes)
    total_time_spent = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class SystemMetrics(models.Model):
    """System performance and usage metrics"""
    date = models.DateTimeField()
    
    # Processing metrics
    reviews_processed = models.PositiveIntegerField(default=0)
    processing_time_avg = models.FloatField(default=0.0)  # Average processing time per review
    api_calls_made = models.PositiveIntegerField(default=0)
    api_failures = models.PositiveIntegerField(default=0)
    
    # Agent performance
    classifier_accuracy = models.FloatField(default=0.0)
    scorer_accuracy = models.FloatField(default=0.0)
    
    # Resource usage
    cpu_usage_avg = models.FloatField(default=0.0)
    memory_usage_avg = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"System Metrics - {self.date}"
