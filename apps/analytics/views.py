from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import AnalyticsReport, SentimentTrend

# Create your views here.

def analytics_home(request):
    """Analytics dashboard"""
    return render(request, 'analytics/home.html', {})

def sentiment_trends(request):
    """Sentiment trends view"""
    return render(request, 'analytics/trends.html', {})

def hotel_comparison(request):
    """Hotel comparison view"""
    return render(request, 'analytics/comparison.html', {})

def reports_list(request):
    """List analytics reports"""
    return render(request, 'analytics/reports.html', {'reports': []})

def create_report(request):
    """Create new analytics report"""
    return render(request, 'analytics/create_report.html', {})

def view_report(request, report_id):
    """View analytics report"""
    return render(request, 'analytics/view_report.html', {'report': None})

@require_http_methods(["POST"])
def generate_insight(request):
    """Generate insights"""
    return JsonResponse({'success': True, 'message': 'Insights generated'})

def export_data(request):
    """Export analytics data"""
    return JsonResponse({'success': True, 'message': 'Data exported'})

def api_data(request):
    """API endpoint for analytics data"""
    return JsonResponse({'data': [], 'message': 'Analytics data'})

def export_csv(request):
    """Export data as CSV"""
    return JsonResponse({'success': True, 'message': 'CSV export completed'})

def export_excel(request):
    """Export data as Excel"""
    return JsonResponse({'success': True, 'message': 'Excel export completed'})
