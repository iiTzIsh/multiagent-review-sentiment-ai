#!/usr/bin/env python
"""
Sample data population script for testing the dashboard
"""
import os
import django
import sys
from datetime import datetime, timedelta
import random

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_review_platform.settings')
django.setup()

from apps.reviews.models import Hotel, Review, ReviewBatch, ReviewSource
from apps.analytics.models import SentimentTrend, AnalyticsReport
from django.contrib.auth.models import User

def create_sample_data():
    """Create sample data for testing"""
    print("Creating sample data...")
    
    # Create or get a sample user
    user, created = User.objects.get_or_create(
        username='sample_user',
        defaults={
            'email': 'sample@example.com',
            'first_name': 'Sample',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"Created user: {user.username}")
    
    # Create sample hotels
    hotels_data = [
        {"name": "Grand Palace Hotel", "location": "New York"},
        {"name": "Coastal Resort", "location": "Miami"},
        {"name": "City Business Inn", "location": "Chicago"},
        {"name": "Mountain Lodge", "location": "Denver"},
        {"name": "Airport Express", "location": "Los Angeles"},
    ]
    
    hotels = []
    for hotel_data in hotels_data:
        hotel, created = Hotel.objects.get_or_create(
            name=hotel_data["name"],
            defaults=hotel_data
        )
        hotels.append(hotel)
        if created:
            print(f"Created hotel: {hotel.name}")
    
    # Create review source
    source, created = ReviewSource.objects.get_or_create(
        name="Sample Data",
        defaults={"url": "https://example.com", "api_endpoint": "https://example.com/api"}
    )
    
    # Create a sample batch
    batch, created = ReviewBatch.objects.get_or_create(
        file_name="sample_reviews.csv",
        defaults={
            "uploaded_by": user,
            "total_reviews": 100,
            "processed_reviews": 85,
            "failed_reviews": 5,
            "status": "completed"
        }
    )
    
    # Sample review texts
    review_texts = [
        "Excellent service and beautiful rooms. The staff was very friendly and helpful.",
        "Good location but the room was quite small. Overall decent experience.",
        "Outstanding hotel with amazing amenities. Highly recommend!",
        "Poor service and dirty rooms. Would not stay here again.",
        "Average hotel, nothing special but acceptable for the price.",
        "Fantastic breakfast and great view from the room.",
        "Terrible experience. Noisy and uncomfortable.",
        "Perfect for business travel. Clean and efficient.",
        "Beautiful architecture and comfortable beds.",
        "Overpriced for what you get. Expected better.",
    ]
    
    sentiments = ["positive", "negative", "neutral"]
    
    # Create sample reviews
    reviews_created = 0
    for i in range(100):
        review_text = random.choice(review_texts)
        sentiment = random.choice(sentiments)
        score = random.uniform(1, 5)
        
        # Adjust score based on sentiment
        if sentiment == "positive":
            score = random.uniform(3.5, 5)
        elif sentiment == "negative":
            score = random.uniform(1, 2.5)
        else:
            score = random.uniform(2.5, 3.5)
        
        review = Review.objects.create(
            hotel=random.choice(hotels),
            source=source,
            text=review_text,
            sentiment=sentiment,
            ai_score=score,
            processed=True,
            created_at=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        reviews_created += 1
    
    print(f"Created {reviews_created} sample reviews")
    
    # Create sentiment trends
    for hotel in hotels[:2]:  # Just for first 2 hotels
        for i in range(7):  # Last 7 days
            date = datetime.now().date() - timedelta(days=i)
            trend, created = SentimentTrend.objects.get_or_create(
                hotel=hotel,
                date=date,
                defaults={
                    "positive_count": random.randint(10, 30),
                    "negative_count": random.randint(5, 15),
                    "neutral_count": random.randint(8, 20),
                    "total_reviews": random.randint(23, 65),
                    "average_score": random.uniform(3.0, 4.5),
                }
            )
            if created:
                print(f"Created sentiment trend for {hotel.name} on {date}")
    
    # Create analytics report
    report, created = AnalyticsReport.objects.get_or_create(
        title="Weekly Summary",
        defaults={
            "report_type": "weekly",
            "date_from": datetime.now() - timedelta(days=7),
            "date_to": datetime.now(),
            "generated_by": user,
            "data": {
                "summary": "Hotel reviews show positive trend",
                "key_insights": ["Service quality improved", "Location ratings stable"],
                "recommendations": ["Focus on room cleanliness", "Improve check-in process"]
            }
        }
    )
    if created:
        print("Created sample analytics report")
    
    print("Sample data creation completed!")

if __name__ == "__main__":
    create_sample_data()
