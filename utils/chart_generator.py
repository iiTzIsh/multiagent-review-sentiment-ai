"""
Chart Generation Utilities
Creates interactive charts and visualizations for the dashboard
"""

import json
from typing import Dict, List, Any
from django.db.models import Count, Avg
from apps.reviews.models import Review
from apps.analytics.models import SentimentTrend
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates chart data for dashboard visualizations"""
    
    def __init__(self):
        self.colors = {
            'positive': '#28a745',
            'neutral': '#ffc107', 
            'negative': '#dc3545',
            'primary': '#007bff',
            'secondary': '#6c757d'
        }
    
    def generate_sentiment_distribution_chart(self) -> Dict[str, Any]:
        """Generate pie chart data for sentiment distribution"""
        try:
            sentiment_data = Review.objects.values('sentiment').annotate(
                count=Count('sentiment')
            )
            
            labels = []
            data = []
            colors = []
            
            for item in sentiment_data:
                sentiment = item['sentiment']
                count = item['count']
                
                labels.append(sentiment.title())
                data.append(count)
                colors.append(self.colors.get(sentiment, self.colors['secondary']))
            
            return {
                'type': 'pie',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': data,
                        'backgroundColor': colors,
                        'borderColor': colors,
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Sentiment Distribution'
                        },
                        'legend': {
                            'position': 'bottom'
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate sentiment distribution chart: {str(e)}")
            return self._empty_chart('pie')
    
    def generate_score_distribution_chart(self) -> Dict[str, Any]:
        """Generate bar chart for score distribution"""
        try:
            score_ranges = [
                {'label': '0-1', 'min': 0, 'max': 1},
                {'label': '1-2', 'min': 1, 'max': 2},
                {'label': '2-3', 'min': 2, 'max': 3},
                {'label': '3-4', 'min': 3, 'max': 4},
                {'label': '4-5', 'min': 4, 'max': 5},
            ]
            
            labels = []
            data = []
            
            for range_info in score_ranges:
                count = Review.objects.filter(
                    ai_score__gte=range_info['min'],
                    ai_score__lt=range_info['max'] if range_info['max'] < 5 else 6
                ).count()
                
                labels.append(range_info['label'])
                data.append(count)
            
            return {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': 'Number of Reviews',
                        'data': data,
                        'backgroundColor': self.colors['primary'],
                        'borderColor': self.colors['primary'],
                        'borderWidth': 1
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Score Distribution'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Number of Reviews'
                            }
                        },
                        'x': {
                            'title': {
                                'display': True,
                                'text': 'Score Range'
                            }
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate score distribution chart: {str(e)}")
            return self._empty_chart('bar')
    
    def generate_sentiment_trend_chart(self, sentiment_trends) -> Dict[str, Any]:
        """Generate line chart for sentiment trends over time"""
        try:
            dates = []
            positive_data = []
            neutral_data = []
            negative_data = []
            
            for trend in sentiment_trends:
                dates.append(trend.date.strftime('%Y-%m-%d'))
                
                total = trend.total_reviews
                if total > 0:
                    positive_data.append(round(trend.positive_count / total * 100, 1))
                    neutral_data.append(round(trend.neutral_count / total * 100, 1))
                    negative_data.append(round(trend.negative_count / total * 100, 1))
                else:
                    positive_data.append(0)
                    neutral_data.append(0)
                    negative_data.append(0)
            
            return {
                'type': 'line',
                'data': {
                    'labels': dates,
                    'datasets': [
                        {
                            'label': 'Positive (%)',
                            'data': positive_data,
                            'borderColor': self.colors['positive'],
                            'backgroundColor': self.colors['positive'] + '20',
                            'tension': 0.1
                        },
                        {
                            'label': 'Neutral (%)',
                            'data': neutral_data,
                            'borderColor': self.colors['neutral'],
                            'backgroundColor': self.colors['neutral'] + '20',
                            'tension': 0.1
                        },
                        {
                            'label': 'Negative (%)',
                            'data': negative_data,
                            'borderColor': self.colors['negative'],
                            'backgroundColor': self.colors['negative'] + '20',
                            'tension': 0.1
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Sentiment Trends Over Time'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': 100,
                            'title': {
                                'display': True,
                                'text': 'Percentage (%)'
                            }
                        },
                        'x': {
                            'title': {
                                'display': True,
                                'text': 'Date'
                            }
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate sentiment trend chart: {str(e)}")
            return self._empty_chart('line')
    
    def generate_hotel_comparison_chart(self, hotels_data: List[Dict]) -> Dict[str, Any]:
        """Generate comparison chart for multiple hotels"""
        try:
            hotel_names = [hotel['name'] for hotel in hotels_data]
            avg_scores = [hotel['avg_score'] for hotel in hotels_data]
            review_counts = [hotel['review_count'] for hotel in hotels_data]
            
            return {
                'type': 'bar',
                'data': {
                    'labels': hotel_names,
                    'datasets': [
                        {
                            'label': 'Average Score',
                            'data': avg_scores,
                            'backgroundColor': self.colors['primary'],
                            'borderColor': self.colors['primary'],
                            'borderWidth': 1,
                            'yAxisID': 'y'
                        },
                        {
                            'label': 'Review Count',
                            'data': review_counts,
                            'backgroundColor': self.colors['secondary'],
                            'borderColor': self.colors['secondary'],
                            'borderWidth': 1,
                            'yAxisID': 'y1',
                            'type': 'line'
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Hotel Performance Comparison'
                        }
                    },
                    'scales': {
                        'y': {
                            'type': 'linear',
                            'display': True,
                            'position': 'left',
                            'title': {
                                'display': True,
                                'text': 'Average Score'
                            },
                            'min': 0,
                            'max': 5
                        },
                        'y1': {
                            'type': 'linear',
                            'display': True,
                            'position': 'right',
                            'title': {
                                'display': True,
                                'text': 'Review Count'
                            },
                            'grid': {
                                'drawOnChartArea': False,
                            },
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate hotel comparison chart: {str(e)}")
            return self._empty_chart('bar')
    
    def generate_monthly_summary_chart(self) -> Dict[str, Any]:
        """Generate monthly summary chart"""
        try:
            from django.db.models import Q
            from datetime import datetime, timedelta
            import calendar
            
            # Get data for last 12 months
            months = []
            review_counts = []
            avg_scores = []
            
            for i in range(12):
                # Calculate month
                date = datetime.now() - timedelta(days=30*i)
                month_name = calendar.month_abbr[date.month]
                year = date.year
                
                # Get reviews for this month
                month_reviews = Review.objects.filter(
                    created_at__year=year,
                    created_at__month=date.month
                )
                
                count = month_reviews.count()
                avg_score = month_reviews.aggregate(avg=Avg('ai_score'))['avg'] or 0
                
                months.insert(0, f"{month_name} {year}")
                review_counts.insert(0, count)
                avg_scores.insert(0, round(avg_score, 1))
            
            return {
                'type': 'line',
                'data': {
                    'labels': months,
                    'datasets': [
                        {
                            'label': 'Review Count',
                            'data': review_counts,
                            'borderColor': self.colors['primary'],
                            'backgroundColor': self.colors['primary'] + '20',
                            'yAxisID': 'y',
                            'tension': 0.1
                        },
                        {
                            'label': 'Average Score',
                            'data': avg_scores,
                            'borderColor': self.colors['positive'],
                            'backgroundColor': self.colors['positive'] + '20',
                            'yAxisID': 'y1',
                            'tension': 0.1
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Monthly Review Summary'
                        }
                    },
                    'scales': {
                        'y': {
                            'type': 'linear',
                            'display': True,
                            'position': 'left',
                            'title': {
                                'display': True,
                                'text': 'Review Count'
                            }
                        },
                        'y1': {
                            'type': 'linear',
                            'display': True,
                            'position': 'right',
                            'title': {
                                'display': True,
                                'text': 'Average Score'
                            },
                            'min': 0,
                            'max': 5
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate monthly summary chart: {str(e)}")
            return self._empty_chart('line')
    
    def _empty_chart(self, chart_type: str) -> Dict[str, Any]:
        """Return an empty chart structure"""
        return {
            'type': chart_type,
            'data': {
                'labels': [],
                'datasets': []
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'No Data Available'
                    }
                }
            }
        }
    
    def to_json(self, chart_data: Dict[str, Any]) -> str:
        """Convert chart data to JSON string"""
        return json.dumps(chart_data)
