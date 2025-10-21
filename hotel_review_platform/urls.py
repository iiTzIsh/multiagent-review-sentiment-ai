"""
URL configuration for hotel_review_platform project.
Hotel Review Insight Platform - Multi-Agent Feedback Analyzer
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Marketing landing page (root)
    path('', include('apps.marketing.urls')),
    
    # Authentication
    path('auth/', include('apps.authentication.urls')),
    
    # Main application URLs (moved to /app/)
    path('app/', include('apps.dashboard.urls')),
    path('api/', include('apps.api.urls')),
    path('reviews/', include('apps.reviews.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
