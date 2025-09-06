"""
Dashboard URL Configuration
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.dashboard_home, name='home'),
    
    # Upload and batch processing
    path('upload/', views.upload_reviews, name='upload_reviews'),
    path('batch/<uuid:batch_id>/', views.batch_detail, name='batch_detail'),
    path('process-reviews/', views.process_reviews_ajax, name='process_reviews'),
    
    # Reviews management
    path('reviews/', views.reviews_list, name='reviews_list'),
    path('reviews/<uuid:review_id>/', views.review_detail, name='review_detail'),
    
    # Analytics
    path('analytics/', views.analytics_overview, name='analytics'),
    
    # Search and filtering
    path('search/', views.search_reviews, name='search_reviews'),
    
    # Export functionality
    path('export/', views.export_data, name='export_data'),
    
    # Reports
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('reports/<uuid:report_id>/', views.report_detail, name='report_detail'),
]
