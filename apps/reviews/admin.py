"""
Professional Django Admin Configuration for Review Management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from apps.reviews.models import Hotel, ReviewSource, Review, ReviewBatch, AgentTask, AIAnalysisResult


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    """Professional hotel management interface"""
    
    list_display = [
        'name', 'location', 'review_count', 'avg_rating', 
        'positive_percentage', 'created_at'
    ]
    list_filter = ['location', 'created_at']
    search_fields = ['name', 'location', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Hotel Information', {
            'fields': ('name', 'location', 'description', 'website_url')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def review_count(self, obj):
        count = obj.reviews.count()
        if count > 0:
            url = reverse('admin:reviews_review_changelist') + f'?hotel__id__exact={obj.id}'
            return format_html('<a href="{}">{} reviews</a>', url, count)
        return '0 reviews'
    review_count.short_description = 'Reviews'
    
    def avg_rating(self, obj):
        from django.db.models import Avg
        avg = obj.reviews.aggregate(avg_score=Avg('ai_score'))['avg_score']
        if avg:
            return f"{avg:.1f}/5.0"
        return "No ratings"
    avg_rating.short_description = 'Avg. Rating'
    
    def positive_percentage(self, obj):
        total = obj.reviews.count()
        if total == 0:
            return "No data"
        positive = obj.reviews.filter(sentiment='positive').count()
        percentage = (positive / total) * 100
        color = 'green' if percentage >= 70 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', 
            color, percentage
        )
    positive_percentage.short_description = 'Positive %'


@admin.register(ReviewSource)
class ReviewSourceAdmin(admin.ModelAdmin):
    """Review platform source management"""
    
    list_display = ['name', 'is_active', 'review_count', 'website_url']
    list_filter = ['is_active']
    search_fields = ['name']
    
    def review_count(self, obj):
        count = obj.review_set.count()
        if count > 0:
            url = reverse('admin:reviews_review_changelist') + f'?source__id__exact={obj.id}'
            return format_html('<a href="{}">{} reviews</a>', url, count)
        return '0 reviews'
    review_count.short_description = 'Reviews'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Professional review management interface"""
    
    list_display = [
        'text_preview', 'hotel_link', 'sentiment_badge', 'ai_score_display', 
        'confidence_display', 'processed_status', 'created_at'
    ]
    list_filter = [
        'sentiment', 'processed', 'source', 'hotel', 
        'created_at', 'ai_score'
    ]
    search_fields = [
        'text', 'title', 'reviewer_name', 'hotel__name', 
        'reviewer_location'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'sentiment_emoji'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Review Content', {
            'fields': ('hotel', 'source', 'title', 'text', 'original_rating')
        }),
        ('Reviewer Information', {
            'fields': ('reviewer_name', 'reviewer_location', 'date_posted', 'date_stayed'),
            'classes': ('collapse',)
        }),
        ('AI Analysis Results', {
            'fields': (
                'sentiment', 'sentiment_emoji', 'ai_score', 'confidence_score',
                'ai_keywords', 'ai_topics', 'ai_summary'
            ),
            'classes': ('wide',)
        }),
        ('Processing Status', {
            'fields': ('processed', 'processing_error'),
        }),
        ('System Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_for_reprocessing', 'mark_as_processed']
    
    def text_preview(self, obj):
        preview = obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
        return format_html('<span title="{}">{}</span>', obj.text, preview)
    text_preview.short_description = 'Review Text'
    
    def hotel_link(self, obj):
        url = reverse('admin:reviews_hotel_change', args=[obj.hotel.pk])
        return format_html('<a href="{}">{}</a>', url, obj.hotel.name)
    hotel_link.short_description = 'Hotel'
    
    def sentiment_badge(self, obj):
        colors = {
            'positive': '#28a745',
            'neutral': '#ffc107', 
            'negative': '#dc3545'
        }
        color = colors.get(obj.sentiment, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{} {}</span>',
            color, obj.sentiment.title(), obj.sentiment_emoji
        )
    sentiment_badge.short_description = 'Sentiment'
    
    def ai_score_display(self, obj):
        color = '#28a745' if obj.ai_score >= 4 else '#ffc107' if obj.ai_score >= 3 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}/5</span>',
            color, obj.ai_score
        )
    ai_score_display.short_description = 'AI Score'
    
    def confidence_display(self, obj):
        percentage = obj.confidence_score * 100
        color = '#28a745' if percentage >= 80 else '#ffc107' if percentage >= 60 else '#dc3545'
        return format_html(
            '<span style="color: {};">{:.0f}%</span>',
            color, percentage
        )
    confidence_display.short_description = 'Confidence'
    
    def processed_status(self, obj):
        if obj.processed:
            return format_html(
                '<span style="color: #28a745;">✓ Processed</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">⏳ Pending</span>'
            )
    processed_status.short_description = 'Status'
    
    def mark_for_reprocessing(self, request, queryset):
        updated = queryset.update(processed=False, processing_error='')
        self.message_user(request, f'{updated} reviews marked for reprocessing.')
    mark_for_reprocessing.short_description = "Mark for reprocessing"
    
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(processed=True)
        self.message_user(request, f'{updated} reviews marked as processed.')
    mark_as_processed.short_description = "Mark as processed"


@admin.register(ReviewBatch)
class ReviewBatchAdmin(admin.ModelAdmin):
    """Batch upload management interface"""
    
    list_display = [
        'file_name', 'uploaded_by', 'status_badge', 'progress_display',
        'success_rate_display', 'upload_date'
    ]
    list_filter = ['status', 'upload_date', 'uploaded_by']
    search_fields = ['file_name', 'uploaded_by__username']
    readonly_fields = [
        'id', 'file_size', 'upload_date', 'processing_started', 
        'processing_completed', 'processing_progress', 'success_rate'
    ]
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('file_name', 'uploaded_by', 'file_size', 'status')
        }),
        ('Processing Statistics', {
            'fields': (
                'total_reviews', 'processed_reviews', 'failed_reviews',
                'processing_progress', 'success_rate'
            )
        }),
        ('Timestamps', {
            'fields': ('upload_date', 'processing_started', 'processing_completed'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('System Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'processing': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.status.title()
        )
    status_badge.short_description = 'Status'
    
    def progress_display(self, obj):
        progress = obj.processing_progress
        color = '#28a745' if progress == 100 else '#007bff'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 10px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 10px; '
            'text-align: center; color: white; font-size: 11px; line-height: 20px;">{:.0f}%</div></div>',
            progress, color, progress
        )
    progress_display.short_description = 'Progress'
    
    def success_rate_display(self, obj):
        rate = obj.success_rate
        if rate >= 95:
            color = '#28a745'
        elif rate >= 80:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    success_rate_display.short_description = 'Success Rate'


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    """Agent task monitoring interface"""
    
    list_display = [
        'agent_name', 'task_type', 'status_badge', 
        'duration_display', 'created_at'
    ]
    list_filter = ['status', 'agent_name', 'task_type', 'created_at']
    search_fields = ['agent_name', 'task_type']
    readonly_fields = [
        'id', 'created_at', 'started_at', 'completed_at'
    ]
    
    fieldsets = (
        ('Task Information', {
            'fields': ('agent_name', 'task_type', 'status')
        }),
        ('Task Data', {
            'fields': ('input_data', 'output_data'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('System Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'running': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.status.title()
        )
    status_badge.short_description = 'Status'
    
    def duration_display(self, obj):
        if obj.completed_at and obj.started_at:
            duration = obj.completed_at - obj.started_at
            return f"{duration.total_seconds():.1f}s"
        elif obj.started_at:
            from django.utils import timezone
            duration = timezone.now() - obj.started_at
            return f"{duration.total_seconds():.1f}s (running)"
        return "Not started"
    duration_display.short_description = 'Duration'


@admin.register(AIAnalysisResult)
class AIAnalysisResultAdmin(admin.ModelAdmin):
    """AI Analysis Results management interface"""
    
    list_display = [
        'analysis_type', 'hotel_display', 'total_reviews_analyzed',
        'days_analyzed', 'is_active', 'created_at'
    ]
    list_filter = ['analysis_type', 'is_active', 'created_at', 'days_analyzed']
    search_fields = ['hotel__name']
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis_type', 'hotel', 'is_active')
        }),
        ('Analysis Parameters', {
            'fields': ('days_analyzed', 'date_range_start', 'date_range_end', 'total_reviews_analyzed')
        }),
        ('AI Results', {
            'fields': ('summary_data', 'sentiment_analysis', 'tags_analysis', 'recommendations'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('agents_used', 'workflow_info'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('System Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def hotel_display(self, obj):
        return obj.hotel.name if obj.hotel else "All Hotels"
    hotel_display.short_description = 'Hotel'


# Admin site customization
admin.site.site_header = "Hotel Review Analytics - Admin"
admin.site.site_title = "Review Analytics Admin"
admin.site.index_title = "Hotel Review Management System"