from django.contrib import admin
from .models import Hotel, ReviewSource, Review, ReviewBatch, ReviewSummary, SearchQuery, AgentTask


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'created_at', 'review_count']
    list_filter = ['created_at', 'location']
    search_fields = ['name', 'location']
    readonly_fields = ['created_at', 'updated_at']
    
    def review_count(self, obj):
        return obj.reviews.count()
    review_count.short_description = 'Total Reviews'


@admin.register(ReviewSource)
class ReviewSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'url']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'hotel', 'sentiment', 'ai_score', 'processed', 'created_at']
    list_filter = ['sentiment', 'processed', 'created_at', 'hotel', 'source']
    search_fields = ['text', 'title', 'reviewer_name', 'hotel__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'confidence_score']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Content', {
            'fields': ('hotel', 'source', 'text', 'title', 'original_rating')
        }),
        ('Reviewer Information', {
            'fields': ('reviewer_name', 'reviewer_location', 'date_posted', 'date_stayed')
        }),
        ('AI Analysis', {
            'fields': ('sentiment', 'ai_score', 'confidence_score', 'processed', 'processing_error')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Review Text'
    
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    def mark_as_processed(self, request, queryset):
        queryset.update(processed=True)
        self.message_user(request, f'{queryset.count()} reviews marked as processed.')
    mark_as_processed.short_description = 'Mark selected reviews as processed'
    
    def mark_as_unprocessed(self, request, queryset):
        queryset.update(processed=False)
        self.message_user(request, f'{queryset.count()} reviews marked as unprocessed.')
    mark_as_unprocessed.short_description = 'Mark selected reviews as unprocessed'


@admin.register(ReviewBatch)
class ReviewBatchAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'status', 'total_reviews', 'processed_reviews', 'failed_reviews', 'upload_date', 'uploaded_by']
    list_filter = ['status', 'upload_date', 'uploaded_by']
    search_fields = ['file_name', 'uploaded_by__username']
    readonly_fields = ['id', 'upload_date', 'processing_started', 'processing_completed', 'processing_progress']
    date_hierarchy = 'upload_date'
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('file_name', 'uploaded_by', 'status')
        }),
        ('Processing Stats', {
            'fields': ('total_reviews', 'processed_reviews', 'failed_reviews', 'processing_progress')
        }),
        ('Timestamps', {
            'fields': ('upload_date', 'processing_started', 'processing_completed')
        }),
        ('Errors', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReviewSummary)
class ReviewSummaryAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'total_reviews', 'average_score', 'date_from', 'date_to', 'created_at']
    list_filter = ['created_at', 'hotel', 'created_by_agent']
    search_fields = ['hotel__name', 'summary_text']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Summary Information', {
            'fields': ('hotel', 'total_reviews', 'average_score', 'created_by_agent')
        }),
        ('Date Range', {
            'fields': ('date_from', 'date_to')
        }),
        ('Content', {
            'fields': ('summary_text', 'key_positives', 'key_negatives', 'recommendations')
        }),
        ('Statistics', {
            'fields': ('sentiment_distribution',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['query_text', 'search_type', 'results_count', 'user', 'created_at']
    list_filter = ['search_type', 'created_at', 'user']
    search_fields = ['query_text']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    list_display = ['agent_name', 'task_type', 'status', 'created_at', 'started_at', 'completed_at']
    list_filter = ['agent_name', 'task_type', 'status', 'created_at']
    search_fields = ['agent_name', 'task_type']
    readonly_fields = ['id', 'created_at', 'started_at', 'completed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Task Information', {
            'fields': ('agent_name', 'task_type', 'status')
        }),
        ('Task Data', {
            'fields': ('input_data', 'output_data', 'error_message')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
