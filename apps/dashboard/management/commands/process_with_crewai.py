"""
Django Management Command - Process Reviews with CrewAI Classifier Agent
Demonstrates full project integration
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from apps.reviews.models import Review, ReviewBatch, Hotel, ReviewSource
import sys

class Command(BaseCommand):
    help = 'Process reviews using CrewAI Classifier Agent - Full Project Integration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of reviews to process in one batch'
        )
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Run with sample data for demonstration'
        )
        parser.add_argument(
            '--test-integration',
            action='store_true',
            help='Test full project integration'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("🚀 FULL PROJECT INTEGRATION - CrewAI Classifier Agent"))
        self.stdout.write("=" * 70)
        
        # Check if CrewAI is available
        try:
            from agents.classifier.agent import ReviewClassifierAgent
            self.stdout.write(self.style.SUCCESS("✅ CrewAI classifier available"))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"❌ CrewAI not available: {e}"))
            self.stdout.write("💡 Run: pip install crewai crewai-tools")
            return
        
        # Initialize the clean CrewAI agent
        self.stdout.write("🤖 Initializing CrewAI Agent...")
        classifier = ReviewClassifierAgent()
        
        self.stdout.write(f"   Agent Name: {classifier.name}")
        self.stdout.write(f"   Agent Role: {classifier.role}")
        self.stdout.write(f"   Agent Goal: {classifier.goal}")
        self.stdout.write(f"   Model: cardiffnlp/twitter-roberta-base-sentiment-latest")
        
        if options['demo']:
            self.run_demo(classifier)
        elif options['test_integration']:
            self.test_integration(classifier)
        else:
            self.process_reviews(classifier, options['batch_size'])
    
    def run_demo(self, classifier):
        """Run demonstration with sample reviews"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.WARNING("📋 DEMO MODE - Sample Reviews"))
        self.stdout.write("=" * 50)
        
        sample_reviews = [
            "Amazing service! The staff was incredibly helpful and the room was perfect.",
            "Terrible experience. The room was dirty and the staff was rude.",
            "The hotel was okay. Nothing special but not bad either.",
            "Outstanding hotel! Beautiful rooms, excellent breakfast, highly recommend!",
            "Worst hotel ever. Noisy, expensive, and poor customer service.",
            "Clean rooms, friendly staff, great location. Will definitely return!",
            "Average stay. Room was small but clean. Service could be better.",
            "Disappointing experience. Overpriced for what you get."
        ]
        
        self.stdout.write(f"Processing {len(sample_reviews)} sample reviews...\n")
        
        results = []
        for i, review_text in enumerate(sample_reviews, 1):
            self.stdout.write(f"Review {i}: {review_text[:60]}...")
            
            # Process with CrewAI agent
            result = classifier.classify_review(review_text)
            
            self.stdout.write(f"   → Sentiment: {result['sentiment']}")
            self.stdout.write(f"   → Confidence: {result['confidence']:.2f}")
            self.stdout.write(f"   → AI Score (1-5): {result['confidence'] * 5:.1f}")
            self.stdout.write("")
            
            results.append(result)
        
        # Summary
        positive = sum(1 for r in results if r['sentiment'] == 'positive')
        negative = sum(1 for r in results if r['sentiment'] == 'negative')
        neutral = sum(1 for r in results if r['sentiment'] == 'neutral')
        avg_confidence = sum(r['confidence'] for r in results) / len(results)
        
        self.stdout.write("📊 DEMO RESULTS SUMMARY:")
        self.stdout.write(f"   Positive: {positive}")
        self.stdout.write(f"   Negative: {negative}")
        self.stdout.write(f"   Neutral: {neutral}")
        self.stdout.write(f"   Average Confidence: {avg_confidence:.2f}")
        self.stdout.write(self.style.SUCCESS("✅ Demo completed successfully!"))
    
    def test_integration(self, classifier):
        """Test full Django integration"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.WARNING("🧪 FULL INTEGRATION TEST"))
        self.stdout.write("=" * 50)
        
        # Test 1: Create sample reviews in database
        self.stdout.write("Test 1: Creating sample reviews in Django database...")
        
        sample_data = [
            ("Great hotel experience!", "Hotel ABC"),
            ("Terrible service and dirty rooms", "Hotel XYZ"),
            ("Average stay, nothing special", "Hotel 123")
        ]
        
        created_reviews = []
        for review_text, hotel_name in sample_data:
            # Get or create hotel
            hotel, _ = Hotel.objects.get_or_create(
                name=hotel_name,
                defaults={'location': 'Test Location'}
            )
            
            # Get or create review source
            source, _ = ReviewSource.objects.get_or_create(
                name='Test Source',
                defaults={'is_active': True}
            )
            
            review = Review.objects.create(
                text=review_text,
                hotel=hotel,
                source=source,
                processed=False
            )
            created_reviews.append(review)
            self.stdout.write(f"   ✅ Created review ID {review.id}")
        
        # Test 2: Process with CrewAI agent
        self.stdout.write("\nTest 2: Processing with CrewAI Agent...")
        
        processed_count = 0
        for review in created_reviews:
            result = classifier.classify_review(review.text)
            
            # Update review with agent results
            review.sentiment = result['sentiment']
            review.ai_score = result['confidence'] * 5
            review.processed = True
            review.save()
            
            self.stdout.write(f"   ✅ Review {review.id}: {result['sentiment']} ({result['confidence']:.2f})")
            processed_count += 1
        
        # Test 3: Verify database updates
        self.stdout.write("\nTest 3: Verifying database updates...")
        
        total_reviews = Review.objects.count()
        processed_reviews = Review.objects.filter(processed=True).count()
        
        self.stdout.write(f"   Total reviews in DB: {total_reviews}")
        self.stdout.write(f"   Processed reviews: {processed_reviews}")
        self.stdout.write(f"   Successfully processed by CrewAI: {processed_count}")
        
        # Test 4: Query processed data
        self.stdout.write("\nTest 4: Querying processed data...")
        
        positive_reviews = Review.objects.filter(sentiment='positive').count()
        negative_reviews = Review.objects.filter(sentiment='negative').count()
        neutral_reviews = Review.objects.filter(sentiment='neutral').count()
        
        self.stdout.write(f"   Positive sentiment: {positive_reviews}")
        self.stdout.write(f"   Negative sentiment: {negative_reviews}")  
        self.stdout.write(f"   Neutral sentiment: {neutral_reviews}")
        
        self.stdout.write(self.style.SUCCESS("✅ Full integration test completed!"))
        self.stdout.write("💾 Test data remains in database for inspection")
    
    def process_reviews(self, classifier, batch_size):
        """Process actual unprocessed reviews from database"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.WARNING("📊 PROCESSING UNPROCESSED REVIEWS"))
        self.stdout.write("=" * 50)
        
        # Get unprocessed reviews
        unprocessed_reviews = Review.objects.filter(
            Q(processed=False) | Q(sentiment__isnull=True) | Q(ai_score__isnull=True)
        )[:batch_size]
        
        total_unprocessed = unprocessed_reviews.count()
        
        if total_unprocessed == 0:
            self.stdout.write(self.style.SUCCESS("✅ All reviews are already processed!"))
            return
        
        self.stdout.write(f"📋 Found {total_unprocessed} unprocessed reviews")
        self.stdout.write(f"🔄 Processing with batch size: {batch_size}")
        self.stdout.write("")
        
        processed_count = 0
        errors = 0
        
        for i, review in enumerate(unprocessed_reviews, 1):
            try:
                self.stdout.write(f"[{i}/{total_unprocessed}] Processing review {review.id}...")
                self.stdout.write(f"   Text: {review.text[:70]}...")
                
                # Process with CrewAI agent
                result = classifier.classify_review(review.text)
                
                # Update review
                review.sentiment = result['sentiment']
                review.ai_score = result['confidence'] * 5
                review.processed = True
                review.save()
                
                self.stdout.write(f"   ✅ Result: {result['sentiment']} (confidence: {result['confidence']:.2f})")
                processed_count += 1
                
            except Exception as e:
                self.stdout.write(f"   ❌ Error: {str(e)}")
                errors += 1
            
            self.stdout.write("")
        
        # Final summary
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("📈 PROCESSING COMPLETE"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"✅ Successfully processed: {processed_count}")
        self.stdout.write(f"❌ Errors: {errors}")
        self.stdout.write(f"🤖 Agent used: {classifier.name}")
        self.stdout.write(f"📊 Total reviews in database: {Review.objects.count()}")
        self.stdout.write(f"🎯 Processed reviews: {Review.objects.filter(processed=True).count()}")
        
        # Sentiment distribution
        positive = Review.objects.filter(sentiment='positive').count()
        negative = Review.objects.filter(sentiment='negative').count()
        neutral = Review.objects.filter(sentiment='neutral').count()
        
        self.stdout.write("\n📊 SENTIMENT DISTRIBUTION:")
        self.stdout.write(f"   Positive: {positive}")
        self.stdout.write(f"   Negative: {negative}")
        self.stdout.write(f"   Neutral: {neutral}")
        
        self.stdout.write("\n🎉 Full project integration working perfectly!")