"""
Reviews URL Configuration
"""

from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Review management
    path('', views.review_list, name='list'),
    path('<uuid:review_id>/', views.review_detail, name='detail'),
    path('process/<uuid:review_id>/', views.process_review, name='process'),
    
    # Bulk operations
    path('bulk/process/', views.bulk_process_reviews, name='bulk_process'),
    path('bulk/delete/', views.bulk_delete_reviews, name='bulk_delete'),
    
    # Hotel management
    path('hotels/', views.hotel_list, name='hotel_list'),
    path('hotels/<int:hotel_id>/', views.hotel_detail, name='hotel_detail'),
    path('hotels/create/', views.create_hotel, name='create_hotel'),
]
