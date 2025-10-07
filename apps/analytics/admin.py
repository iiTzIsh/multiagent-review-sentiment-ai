from django.contrib import admin
from .models import (
    SentimentTrend, 
    AnalyticsReport, 
    KeywordFrequency, 
    CompetitorComparison, 
    UserEngagement, 
    SystemMetrics
)


@admin.register(SentimentTrend)
class SentimentTrendAdmin(admin.ModelAdmin):
    list_display = ['date', 'hotel', 'total_reviews', 'positive_count', 'negative_count', 'average_score']
    list_filter = ['date', 'hotel']
    search_fields = ['hotel__name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'hotel', 'generated_at']
    list_filter = ['report_type', 'hotel']
    search_fields = ['title', 'hotel__name']
    readonly_fields = ['id', 'generated_at']
    date_hierarchy = 'generated_at'


@admin.register(KeywordFrequency)
class KeywordFrequencyAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'hotel', 'frequency', 'sentiment_context', 'date_from', 'date_to']
    list_filter = ['sentiment_context', 'hotel']
    search_fields = ['keyword', 'hotel__name']


@admin.register(CompetitorComparison)
class CompetitorComparisonAdmin(admin.ModelAdmin):
    list_display = ['primary_hotel', 'analysis_date', 'date_from', 'date_to']
    list_filter = ['analysis_date', 'primary_hotel']
    search_fields = ['primary_hotel__name']


@admin.register(UserEngagement)
class UserEngagementAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'login_count', 'searches_performed', 'reports_generated']
    list_filter = ['date', 'user']
    search_fields = ['user__username']
    date_hierarchy = 'date'


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ['date', 'reviews_processed', 'api_calls_made', 'api_failures', 'cpu_usage_avg']
    list_filter = ['date']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']
