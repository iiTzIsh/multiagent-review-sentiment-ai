"""
Analytics URL Configuration
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Analytics views
    path('', views.analytics_home, name='home'),
    path('trends/', views.sentiment_trends, name='trends'),
    path('comparison/', views.hotel_comparison, name='comparison'),
    
    # Reports
    path('reports/', views.reports_list, name='reports'),
    path('reports/create/', views.create_report, name='create_report'),
    path('reports/<uuid:report_id>/', views.view_report, name='view_report'),
    
    # Data export
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/excel/', views.export_excel, name='export_excel'),
]
