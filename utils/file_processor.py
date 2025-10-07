"""
File Processing Utilities
Handles CSV, Excel, and other file uploads for review data
"""

import pandas as pd
import logging
from typing import Dict, List, Any
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from apps.reviews.models import Review, Hotel, ReviewSource, ReviewBatch
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ReviewFileProcessor:
    """Processes uploaded review files"""
    
    SUPPORTED_FORMATS = ['.csv', '.xlsx', '.xls']
    
    def __init__(self):
        self.required_columns = ['text']
        self.optional_columns = [
            'title', 'rating', 'reviewer_name', 'reviewer_location',
            'date_posted', 'hotel_name', 'source'
        ]
    
    def process_file(self, uploaded_file: UploadedFile, batch: ReviewBatch) -> Dict[str, Any]:
        """Process uploaded review file"""
        try:
            # Update batch status
            batch.status = 'processing'
            batch.processing_started = timezone.now()
            batch.save()
            
            # Read file based on extension
            file_extension = uploaded_file.name.lower().split('.')[-1]
            
            if file_extension == 'csv':
                df = pd.read_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Validate columns
            validation_result = self._validate_columns(df)
            if not validation_result['valid']:
                batch.status = 'failed'
                batch.error_message = validation_result['error']
                batch.save()
                return {
                    'success': False,
                    'error': validation_result['error']
                }
            
            # Process rows
            processed_count = 0
            failed_count = 0
            
            batch.total_reviews = len(df)
            batch.save()
            
            for index, row in df.iterrows():
                try:
                    review_data = self._extract_review_data(row)
                    self._create_review(review_data, batch)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process row {index}: {str(e)}")
                    failed_count += 1
                
                # Update progress
                batch.processed_reviews = processed_count
                batch.failed_reviews = failed_count
                batch.save()
            
            # Complete batch processing
            batch.status = 'completed'
            batch.processing_completed = timezone.now()
            batch.save()
            
            return {
                'success': True,
                'processed': processed_count,
                'failed': failed_count,
                'batch_id': batch.id
            }
            
        except Exception as e:
            logger.error(f"File processing failed: {str(e)}")
            batch.status = 'failed'
            batch.error_message = str(e)
            batch.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate that required columns are present"""
        missing_columns = []
        
        for col in self.required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            return {
                'valid': False,
                'error': f"Missing required columns: {', '.join(missing_columns)}"
            }
        
        return {'valid': True}
    
    def _extract_review_data(self, row: pd.Series) -> Dict[str, Any]:
        """Extract review data from DataFrame row"""
        data = {
            'text': str(row.get('text', '')),
            'title': str(row.get('title', '')) if pd.notna(row.get('title')) else '',
            'original_rating': self._safe_float(row.get('rating')),
            'reviewer_name': str(row.get('reviewer_name', '')) if pd.notna(row.get('reviewer_name')) else '',
            'reviewer_location': str(row.get('reviewer_location', '')) if pd.notna(row.get('reviewer_location')) else '',
            'hotel_name': str(row.get('hotel_name', 'Unknown Hotel')) if pd.notna(row.get('hotel_name')) else 'Unknown Hotel',
            'source_name': str(row.get('source', 'Manual Upload')) if pd.notna(row.get('source')) else 'Manual Upload',
        }
        
        # Handle date parsing
        date_posted = row.get('date_posted')
        if pd.notna(date_posted):
            try:
                parsed_date = pd.to_datetime(date_posted)
                # Convert pandas Timestamp to Python datetime
                if hasattr(parsed_date, 'to_pydatetime'):
                    parsed_date = parsed_date.to_pydatetime()
                # Make timezone-aware if naive
                if parsed_date.tzinfo is None:
                    data['date_posted'] = timezone.make_aware(parsed_date)
                else:
                    data['date_posted'] = parsed_date
            except:
                data['date_posted'] = None
        else:
            data['date_posted'] = None
        
        return data
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _create_review(self, data: Dict[str, Any], batch: ReviewBatch):
        """Create a review object from processed data"""
        # Get or create hotel
        hotel, created = Hotel.objects.get_or_create(
            name=data['hotel_name'],
            defaults={'location': 'Unknown'}
        )
        
        # Get or create review source
        source, created = ReviewSource.objects.get_or_create(
            name=data['source_name'],
            defaults={'is_active': True}
        )
        
        # Create review with AI fields initialized
        review = Review.objects.create(
            hotel=hotel,
            source=source,
            text=data['text'],
            title=data['title'],
            original_rating=data['original_rating'],
            reviewer_name=data['reviewer_name'],
            reviewer_location=data['reviewer_location'],
            date_posted=data['date_posted'],
            ai_keywords='',  # Initialize empty, will be populated by AI agents
            ai_summary='',   # Initialize empty, will be populated by AI agents
            processed=False  # Will be processed by agents
        )
        
        return review
    
    def generate_sample_csv(self) -> str:
        """Generate a sample CSV file for users"""
        sample_data = {
            'text': [
                'Great hotel with excellent service and clean rooms.',
                'Poor experience, room was dirty and staff was rude.',
                'Average hotel, nothing special but adequate for the price.'
            ],
            'title': [
                'Excellent Stay',
                'Disappointing Experience',
                'Average Hotel'
            ],
            'rating': [5, 2, 3],
            'reviewer_name': ['John Doe', 'Jane Smith', 'Mike Johnson'],
            'reviewer_location': ['New York, USA', 'London, UK', 'Toronto, Canada'],
            'hotel_name': ['Grand Plaza Hotel', 'Grand Plaza Hotel', 'Grand Plaza Hotel'],
            'source': ['TripAdvisor', 'Booking.com', 'Hotels.com'],
            'date_posted': ['2024-01-15', '2024-01-16', '2024-01-17']
        }
        
        df = pd.DataFrame(sample_data)
        return df.to_csv(index=False)


class DataValidator:
    """Validates review data quality"""
    
    @staticmethod
    def validate_review_text(text: str) -> Dict[str, Any]:
        """Validate review text quality"""
        issues = []
        
        if not text or len(text.strip()) < 10:
            issues.append("Review text too short")
        
        if len(text) > 5000:
            issues.append("Review text too long")
        
        # Check for spam patterns (simple)
        spam_indicators = ['click here', 'visit our website', 'free money']
        if any(indicator in text.lower() for indicator in spam_indicators):
            issues.append("Potential spam content detected")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'text_length': len(text),
            'word_count': len(text.split())
        }
    
    @staticmethod
    def validate_rating(rating: float) -> Dict[str, Any]:
        """Validate rating value"""
        if rating is None:
            return {'valid': True, 'normalized_rating': None}
        
        if not isinstance(rating, (int, float)):
            return {'valid': False, 'error': 'Rating must be a number'}
        
        if rating < 0 or rating > 5:
            return {'valid': False, 'error': 'Rating must be between 0 and 5'}
        
        return {'valid': True, 'normalized_rating': rating}


class FileExporter:
    """Export review data to various formats"""
    
    @staticmethod
    def export_reviews_to_csv(reviews, filename: str = None) -> str:
        """Export reviews to CSV format"""
        data = []
        for review in reviews:
            data.append({
                'id': str(review.id),
                'hotel_name': review.hotel.name,
                'text': review.text,
                'title': review.title,
                'sentiment': review.sentiment,
                'ai_score': review.ai_score,
                'original_rating': review.original_rating,
                'reviewer_name': review.reviewer_name,
                'reviewer_location': review.reviewer_location,
                'date_posted': review.date_posted,
                'created_at': review.created_at,
                'processed': review.processed
            })
        
        df = pd.DataFrame(data)
        
        if filename:
            df.to_csv(filename, index=False)
            return filename
        else:
            return df.to_csv(index=False)
    
    @staticmethod
    def export_analytics_to_excel(analytics_data: Dict, filename: str) -> str:
        """Export analytics data to Excel format"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = pd.DataFrame([analytics_data.get('summary', {})])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sentiment trends sheet
            if 'sentiment_trends' in analytics_data:
                trends_df = pd.DataFrame(analytics_data['sentiment_trends'])
                trends_df.to_excel(writer, sheet_name='Sentiment Trends', index=False)
            
            # Hotel performance sheet
            if 'hotel_performance' in analytics_data:
                performance_df = pd.DataFrame(analytics_data['hotel_performance'])
                performance_df.to_excel(writer, sheet_name='Hotel Performance', index=False)
        
        return filename
