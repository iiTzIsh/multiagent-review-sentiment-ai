"""
URL configuration for hotel_review_platform project.
Hotel Review Insight Platform - Multi-Agent Feedback Analyzer
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_dashboard(request):
    """Redirect root URL to dashboard"""
    return redirect('dashboard:home')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Main application URLs
    path('', redirect_to_dashboard, name='root'),
    path('dashboard/', include('apps.dashboard.urls')),
    path('api/', include('apps.api.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('analytics/', include('apps.analytics.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
