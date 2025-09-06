"""
API URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'reviews', views.ReviewViewSet)
router.register(r'hotels', views.HotelViewSet)
router.register(r'analytics', views.AnalyticsViewSet, basename='analytics')

app_name = 'api'

urlpatterns = [
    # ViewSet URLs
    path('v1/', include(router.urls)),
    
    # Auth endpoints
    path('auth/profile/', views.AuthProfileView.as_view(), name='auth_profile'),
    
    # Analytics endpoints  
    path('analytics/dashboard-stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
    path('analytics/recent-activity/', views.RecentActivityView.as_view(), name='recent_activity'),
    
    # Custom API endpoints
    path('v1/process/', views.ProcessReviewsAPIView.as_view(), name='process_reviews'),
    path('v1/search/', views.SearchAPIView.as_view(), name='search'),
    path('v1/summary/', views.SummaryAPIView.as_view(), name='summary'),
    path('v1/export/', views.ExportAPIView.as_view(), name='export'),
    
    # Agent status endpoints
    path('v1/agents/status/', views.AgentStatusAPIView.as_view(), name='agent_status'),
    path('v1/agents/tasks/', views.AgentTasksAPIView.as_view(), name='agent_tasks'),
]
