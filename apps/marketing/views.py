"""
Marketing Views for Landing Page
Professional marketing site for ReviNet AI platform
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)


def landing_page(request):
    """Professional landing page for ReviNet AI"""
    
    # Features data for the landing page
    features = [
        {
            'icon': '🎯',
            'title': 'AI Sentiment Analysis',
            'description': 'Advanced RoBERTa model provides 95% accurate sentiment detection with confidence scoring.',
            'benefit': '40% better accuracy than basic tools'
        },
        {
            'icon': '⭐',
            'title': 'Smart Scoring System',
            'description': 'BERT-powered quality assessment correlates review content with actual business metrics.',
            'benefit': 'Predict revenue impact from reviews'
        },
        {
            'icon': '✨',
            'title': 'Auto Title Generation',
            'description': 'BART model creates engaging, SEO-optimized titles that capture review essence.',
            'benefit': 'Save 85% of manual title creation time'
        },
        {
            'icon': '📊',
            'title': 'Intelligent Summarization',
            'description': 'Gemini AI transforms review volumes into actionable business intelligence insights.',
            'benefit': 'Turn data into strategic decisions'
        },
        {
            'icon': '🏷️',
            'title': 'Context-Aware Tagging',
            'description': 'Automatically categorize reviews by topics: service, cleanliness, location, amenities.',
            'benefit': 'Identify improvement priorities instantly'
        },
        {
            'icon': '💡',
            'title': 'Strategic Recommendations',
            'description': 'AI provides specific, actionable advice based on review patterns and industry best practices.',
            'benefit': 'Get expert consultation from AI'
        }
    ]
    
    # Pricing tiers
    pricing_tiers = [
        {
            'name': 'Starter',
            'description': 'Perfect for independent hotels',
            'price': '500',
            'period': 'month',
            'popular': False,
            'features': [
                'Up to 1,000 reviews/month',
                'Basic sentiment analysis',
                'Standard dashboard',
                'Email support',
                'Single property focus'
            ],
            'cta': 'Start Free Trial'
        },
        {
            'name': 'Professional',
            'description': 'Perfect for hotel groups',
            'price': '2,500',
            'period': 'month',
            'popular': True,
            'features': [
                'Up to 10,000 reviews/month',
                'Full 6-agent AI analysis',
                'Advanced analytics dashboard',
                'API access (1,000 calls/month)',
                'Priority support',
                'Multi-property management'
            ],
            'cta': 'Schedule Demo'
        },
        {
            'name': 'Enterprise',
            'description': 'Perfect for hotel chains',
            'price': 'Custom',
            'period': None,
            'popular': False,
            'features': [
                'Unlimited reviews',
                'Custom AI model training',
                'White-label solutions',
                'Unlimited API access',
                'Dedicated account manager',
                'Custom integrations',
                'On-premise deployment'
            ],
            'cta': 'Contact Sales'
        }
    ]
    
    # Customer testimonials
    testimonials = [
        {
            'name': 'Sarah Mitchell',
            'position': 'Revenue Manager',
            'company': 'Luxury Resort Chain',
            'avatar': '👩',
            'content': 'ReviNet AI helped us identify service gaps we never knew existed. Our guest satisfaction improved by 40% in just 3 months.',
            'metric': '40% improvement in guest satisfaction'
        },
        {
            'name': 'David Chen',
            'position': 'General Manager',
            'company': 'Boutique Hotel Group',
            'avatar': '👨',
            'content': 'The AI recommendations are incredibly accurate. We implemented their suggestions and saw immediate revenue impact.',
            'metric': '95% reduction in analysis time'
        },
        {
            'name': 'Maria Rodriguez',
            'position': 'Operations Director',
            'company': 'Independent Hotel',
            'avatar': '👩',
            'content': 'ROI was achieved in the first month. The insights help us make data-driven decisions that actually work.',
            'metric': 'ROI achieved in first month'
        }
    ]
    
    context = {
        'features': features,
        'pricing_tiers': pricing_tiers,
        'testimonials': testimonials,
        'page_title': 'ReviNet AI - Transform Hotel Reviews into Revenue Growth'
    }
    
    return render(request, 'marketing/landing.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def contact_form(request):
    """Handle contact form submissions"""
    try:
        data = json.loads(request.body)
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        company = data.get('company', '').strip()
        message = data.get('message', '').strip()
        form_type = data.get('type', 'contact')  # 'trial' or 'demo' or 'contact'
        
        # Basic validation
        if not all([name, email, company]):
            return JsonResponse({
                'success': False,
                'error': 'Please fill in all required fields.'
            }, status=400)
        
        # Log the contact request
        logger.info(f"Contact form submission: {name} ({email}) from {company} - Type: {form_type}")
        
        # In a real implementation, you would:
        # 1. Save to database
        # 2. Send email notifications
        # 3. Integrate with CRM
        # 4. Set up follow-up tasks
        
        # For now, just log and return success
        contact_data = {
            'name': name,
            'email': email,
            'company': company,
            'message': message,
            'type': form_type,
            'timestamp': str(timezone.now())
        }
        
        # You can save this to a model later:
        # ContactLead.objects.create(**contact_data)
        
        return JsonResponse({
            'success': True,
            'message': f'Thank you {name}! We\'ll be in touch within 24 hours.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format.'
        }, status=400)
    except Exception as e:
        logger.error(f"Contact form error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


def pricing_calculator(request):
    """Calculate custom pricing based on properties and review volume"""
    try:
        properties = int(request.GET.get('properties', 1))
        reviews = int(request.GET.get('reviews', 1000))
        
        # Pricing logic based on your business model
        if properties == 1 and reviews <= 1000:
            recommended_tier = 'Starter'
            price = 500
        elif properties <= 10 and reviews <= 10000:
            recommended_tier = 'Professional'
            price = 2500
        elif properties <= 50:
            recommended_tier = 'Professional+'
            price = min(5000, 2500 + (properties - 10) * 200)
        else:
            recommended_tier = 'Enterprise'
            price = 'Custom'
        
        return JsonResponse({
            'success': True,
            'price': price,
            'recommended_tier': recommended_tier,
            'properties': properties,
            'reviews': reviews
        })
        
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'Invalid input values'
        }, status=400)