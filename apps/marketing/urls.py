"""
URL Configuration for Marketing Landing Page
"""

from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing'),
    
    # Contact and lead generation
    path('contact/', views.contact_form, name='contact'),
    path('pricing-calculator/', views.pricing_calculator, name='pricing_calculator'),
]