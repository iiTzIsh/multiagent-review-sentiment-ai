from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.reviews.models import Review
import random
from datetime import datetime

class Command(BaseCommand):
    help = 'Process unprocessed reviews with AI sentiment analysis'
    
    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=20, help='Number of reviews to process')
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        
        reviews = Review.objects.filter(
            Q(processed=False) | Q(sentiment__isnull=True) | Q(ai_score__isnull=True)
        )[:batch_size]
        
        self.stdout.write(f'Found {reviews.count()} unprocessed reviews')
        
        if not reviews:
            self.stdout.write(self.style.WARNING('No reviews to process'))
            return
        
        processed_count = 0
        for review in reviews:
            try:
                self.process_single_review(review)
                processed_count += 1
                self.stdout.write(f'✓ Processed review ID: {review.id}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Processed {processed_count} reviews'))
    
    def process_single_review(self, review):
        review_text = review.text
        if not review_text:
            raise ValueError('Review text is empty')
        
        sentiment = self.analyze_sentiment(review_text)
        ai_score = self.generate_ai_score(review_text, review.original_rating, sentiment)
        
        review.sentiment = sentiment
        review.ai_score = ai_score
        review.processed = True
        review.processed_at = datetime.now()
        review.save()
    
    def analyze_sentiment(self, text):
        text_lower = text.lower()
        positive_words = ['excellent', 'amazing', 'great', 'good', 'nice', 'clean', 'friendly']
        negative_words = ['terrible', 'awful', 'bad', 'dirty', 'rude', 'poor', 'worst']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        return 'neutral'
    
    def generate_ai_score(self, text, original_rating, sentiment):
        base_score = original_rating if original_rating else 3.0
        
        if sentiment == 'positive':
            adjustment = random.uniform(0.2, 0.8)
        elif sentiment == 'negative':
            adjustment = random.uniform(-0.8, -0.2)
        else:
            adjustment = random.uniform(-0.3, 0.3)
        
        return round(max(1.0, min(5.0, base_score + adjustment)), 1)
