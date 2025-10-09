"""
URL Configuration for Authentication
"""

from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    # Authentication pages
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # User management
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('users/', views.user_list_view, name='user_list'),
    path('toggle-user-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Error pages
    path('unauthorized/', views.unauthorized_view, name='unauthorized'),
]