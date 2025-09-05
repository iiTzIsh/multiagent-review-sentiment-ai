"""
File Processing Utilities for Hotel Review Insight Platform
Handles CSV, Excel, and JSON file uploads and processing
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Any, Tuple
from io import StringIO, BytesIO
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
import re
import uuid

logger = logging.getLogger(__name__)


class FileProcessor:
    """Main class for processing uploaded review files"""
    
    REQUIRED_COLUMNS = ['text', 'hotel_name']
    OPTIONAL_COLUMNS = [
        'title', 'reviewer_name', 'reviewer_location', 'date_posted',
        'original_rating', 'source_platform'
    ]
    
    def __init__(self, file: UploadedFile, batch=None):
        self.file = file
        self.batch = batch
        self.filename = file.name
        self.file_extension = self._get_file_extension()
        self.errors = []
        self.warnings = []
        
    def _get_file_extension(self) -> str:
        """Get file extension from filename"""
        return self.filename.lower().split('.')[-1]
    
    def process_file(self) -> Dict[str, Any]:
        """Main method to process the uploaded file"""
        try:
            # Read file based on extension
            if self.file_extension == 'csv':
                df = self._read_csv()
            elif self.file_extension in ['xlsx', 'xls']:
                df = self._read_excel()
            elif self.file_extension == 'json':
                df = self._read_json()
            else:
                raise ValueError(f"Unsupported file format: {self.file_extension}")
            
            # Validate and clean data
            df = self._validate_dataframe(df)
            df = self._clean_data(df)
            
            # Process reviews
            result = self._process_reviews(df)
            
            return {
                'success': True,
                'total': len(df),
                'processed': result['processed'],
                'failed': result['failed'],
                'errors': self.errors,
                'warnings': self.warnings
            }
            
        except Exception as e:
            logger.error(f"File processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'processed': 0,
                'failed': 0,
                'errors': self.errors + [str(e)],
                'warnings': self.warnings
            }
    
    def _read_csv(self) -> pd.DataFrame:
        """Read CSV file"""
        try:
            # Try different encodings
            content = self.file.read()
            
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text_content = content.decode(encoding)
                    df = pd.read_csv(StringIO(text_content))
                    return df
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("Could not decode CSV file with any supported encoding")
            
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
    
    def _read_excel(self) -> pd.DataFrame:
        """Read Excel file"""
        try:
            df = pd.read_excel(BytesIO(self.file.read()))
            return df
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")
    
    def _read_json(self) -> pd.DataFrame:
        """Read JSON file"""
        try:
            content = json.loads(self.file.read().decode('utf-8'))
            
            # Handle different JSON structures
            if isinstance(content, list):
                df = pd.DataFrame(content)
            elif isinstance(content, dict) and 'reviews' in content:
                df = pd.DataFrame(content['reviews'])
            elif isinstance(content, dict) and 'data' in content:
                df = pd.DataFrame(content['data'])
            else:
                raise ValueError("Unsupported JSON structure")
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error reading JSON file: {str(e)}")
    
    def _validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate dataframe structure and required columns"""
        
        # Check if dataframe is empty
        if df.empty:
            raise ValueError("File contains no data")
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        
        # Map common column variations
        column_mapping = {
            'review_text': 'text',
            'review': 'text',
            'comment': 'text',
            'content': 'text',
            'hotel': 'hotel_name',
            'property_name': 'hotel_name',
            'accommodation': 'hotel_name',
            'reviewer': 'reviewer_name',
            'author': 'reviewer_name',
            'guest_name': 'reviewer_name',
            'rating': 'original_rating',
            'score': 'original_rating',
            'stars': 'original_rating',
            'date': 'date_posted',
            'review_date': 'date_posted',
            'posted_date': 'date_posted',
            'location': 'reviewer_location',
            'guest_location': 'reviewer_location',
            'platform': 'source_platform',
            'site': 'source_platform',
            'source': 'source_platform'
        }
        
        # Apply column mapping
        df = df.rename(columns=column_mapping)
        
        # Check for required columns
        missing_columns = []
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Add warnings for missing optional columns
        for col in self.OPTIONAL_COLUMNS:
            if col not in df.columns:
                self.warnings.append(f"Optional column '{col}' not found")
        
        return df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize data"""
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Clean text columns
        text_columns = ['text', 'title', 'hotel_name', 'reviewer_name', 'reviewer_location']
        
        for col in text_columns:
            if col in df.columns:
                # Remove extra whitespace
                df[col] = df[col].astype(str).str.strip()
                
                # Replace 'nan' string with actual NaN
                df[col] = df[col].replace('nan', pd.NaN)
                
                # Remove empty strings
                df[col] = df[col].replace('', pd.NaN)
        
        # Clean and validate ratings
        if 'original_rating' in df.columns:
            df['original_rating'] = pd.to_numeric(df['original_rating'], errors='coerce')
            
            # Validate rating range (assuming 1-5 scale, but could be 1-10)
            invalid_ratings = df[
                (df['original_rating'] < 1) | (df['original_rating'] > 10)
            ]['original_rating'].count()
            
            if invalid_ratings > 0:
                self.warnings.append(f"{invalid_ratings} reviews have invalid ratings")
                df.loc[
                    (df['original_rating'] < 1) | (df['original_rating'] > 10),
                    'original_rating'
                ] = pd.NaN
        
        # Clean dates
        if 'date_posted' in df.columns:
            df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
        
        # Remove rows with missing required data
        initial_count = len(df)
        df = df.dropna(subset=self.REQUIRED_COLUMNS)
        dropped_count = initial_count - len(df)
        
        if dropped_count > 0:
            self.warnings.append(f"Dropped {dropped_count} rows with missing required data")
        
        return df
    
    def _process_reviews(self, df: pd.DataFrame) -> Dict[str, int]:
        """Process reviews and save to database"""
        from apps.reviews.models import Review, Hotel
        
        processed_count = 0
        failed_count = 0
        
        for index, row in df.iterrows():
            try:
                # Get or create hotel
                hotel, created = Hotel.objects.get_or_create(
                    name=row['hotel_name'],
                    defaults={
                        'city': self._extract_city_from_text(row.get('reviewer_location', '')),
                        'description': f"Hotel: {row['hotel_name']}"
                    }
                )
                
                # Create review
                review_data = {
                    'hotel': hotel,
                    'text': row['text'],
                    'title': row.get('title', ''),
                    'reviewer_name': row.get('reviewer_name', ''),
                    'reviewer_location': row.get('reviewer_location', ''),
                    'original_rating': row.get('original_rating'),
                    'source_platform': row.get('source_platform', 'upload'),
                    'date_posted': row.get('date_posted'),
                }
                
                # Remove None values
                review_data = {k: v for k, v in review_data.items() if v is not None and v != ''}
                
                review = Review.objects.create(**review_data)
                
                # Associate with batch if provided
                if self.batch:
                    review.batch = self.batch
                    review.save()
                
                processed_count += 1
                
            except Exception as e:
                failed_count += 1
                error_msg = f"Row {index + 1}: {str(e)}"
                self.errors.append(error_msg)
                logger.error(f"Failed to process review: {error_msg}")
        
        return {
            'processed': processed_count,
            'failed': failed_count
        }
    
    def _extract_city_from_text(self, location_text: str) -> str:
        """Extract city name from location text"""
        if not location_text or pd.isna(location_text):
            return ''
        
        # Simple extraction - take first part before comma
        parts = str(location_text).split(',')
        return parts[0].strip() if parts else ''


def process_reviews_file(file: UploadedFile, batch=None) -> Dict[str, Any]:
    """
    Main function to process uploaded review files
    
    Args:
        file: Django UploadedFile object
        batch: ReviewBatch instance to associate reviews with
    
    Returns:
        Dictionary with processing results
    """
    processor = FileProcessor(file, batch)
    return processor.process_file()


def validate_file_format(file: UploadedFile) -> Tuple[bool, str]:
    """
    Validate if uploaded file format is supported
    
    Args:
        file: Django UploadedFile object
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    supported_extensions = ['csv', 'xlsx', 'xls', 'json']
    
    if not file.name:
        return False, "File name is missing"
    
    extension = file.name.lower().split('.')[-1]
    
    if extension not in supported_extensions:
        return False, f"Unsupported file format. Supported: {', '.join(supported_extensions)}"
    
    # Check file size (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        return False, f"File too large. Maximum size: {max_size / 1024 / 1024:.1f}MB"
    
    return True, ""


def generate_sample_data() -> pd.DataFrame:
    """
    Generate sample review data for testing
    
    Returns:
        DataFrame with sample review data
    """
    sample_data = [
        {
            'text': 'Amazing hotel with excellent service. The staff was very friendly and helpful.',
            'hotel_name': 'Grand Plaza Hotel',
            'title': 'Excellent Stay',
            'reviewer_name': 'John Smith',
            'reviewer_location': 'New York, USA',
            'original_rating': 5,
            'date_posted': '2024-01-15',
            'source_platform': 'sample'
        },
        {
            'text': 'Room was dirty and service was poor. Would not recommend.',
            'hotel_name': 'Budget Inn',
            'title': 'Disappointing Experience',
            'reviewer_name': 'Jane Doe',
            'reviewer_location': 'Los Angeles, USA',
            'original_rating': 2,
            'date_posted': '2024-01-10',
            'source_platform': 'sample'
        },
        {
            'text': 'Good location and decent amenities. Average stay overall.',
            'hotel_name': 'City Center Hotel',
            'title': 'Average Stay',
            'reviewer_name': 'Mike Johnson',
            'reviewer_location': 'Chicago, USA',
            'original_rating': 3,
            'date_posted': '2024-01-08',
            'source_platform': 'sample'
        }
    ]
    
    return pd.DataFrame(sample_data)


def export_reviews_to_format(reviews, format_type: str = 'csv') -> bytes:
    """
    Export reviews to specified format
    
    Args:
        reviews: QuerySet of Review objects
        format_type: Export format ('csv', 'excel', 'json')
    
    Returns:
        Bytes content of exported file
    """
    
    # Convert reviews to DataFrame
    data = []
    for review in reviews:
        data.append({
            'id': str(review.id),
            'hotel_name': review.hotel.name,
            'hotel_city': getattr(review.hotel, 'city', ''),
            'text': review.text,
            'title': review.title or '',
            'reviewer_name': review.reviewer_name or '',
            'reviewer_location': review.reviewer_location or '',
            'sentiment': review.sentiment or '',
            'ai_score': review.ai_score,
            'confidence_score': review.confidence_score,
            'original_rating': review.original_rating,
            'date_posted': review.date_posted.strftime('%Y-%m-%d') if review.date_posted else '',
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'processed': review.processed,
            'source_platform': review.source_platform or ''
        })
    
    df = pd.DataFrame(data)
    
    if format_type == 'csv':
        return df.to_csv(index=False).encode('utf-8')
    
    elif format_type == 'excel':
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reviews')
        return buffer.getvalue()
    
    elif format_type == 'json':
        return json.dumps(data, indent=2, default=str).encode('utf-8')
    
    else:
        raise ValueError(f"Unsupported export format: {format_type}")


# Data validation functions
def validate_review_text(text: str) -> Tuple[bool, str]:
    """Validate review text content"""
    if not text or not text.strip():
        return False, "Review text cannot be empty"
    
    if len(text.strip()) < 10:
        return False, "Review text must be at least 10 characters long"
    
    if len(text) > 5000:
        return False, "Review text must be less than 5000 characters"
    
    return True, ""


def validate_rating(rating) -> Tuple[bool, str]:
    """Validate rating value"""
    if rating is None:
        return True, ""  # Rating is optional
    
    try:
        rating = float(rating)
        if rating < 1 or rating > 5:
            return False, "Rating must be between 1 and 5"
        return True, ""
    except (ValueError, TypeError):
        return False, "Rating must be a number"


def sanitize_text(text: str) -> str:
    """Sanitize text content"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
    
    return text.strip()


# Utility functions for data analysis
def analyze_upload_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze the quality of uploaded data"""
    
    analysis = {
        'total_rows': len(df),
        'empty_text_count': df['text'].isna().sum(),
        'empty_hotel_count': df['hotel_name'].isna().sum(),
        'duplicate_count': df.duplicated(subset=['text', 'hotel_name']).sum(),
        'missing_ratings': df.get('original_rating', pd.Series()).isna().sum(),
        'missing_dates': df.get('date_posted', pd.Series()).isna().sum(),
        'text_length_stats': {
            'mean': df['text'].str.len().mean(),
            'min': df['text'].str.len().min(),
            'max': df['text'].str.len().max(),
        } if 'text' in df.columns else None
    }
    
    return analysis
