from django.contrib import admin
from .models import SentimentTrend, AnalyticsReport


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
