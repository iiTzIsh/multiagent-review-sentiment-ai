import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_review_platform.settings')
django.setup()

from apps.reviews.models import Review

print("=== REVIEW PROCESSING STATUS ===")
print(f"Total Reviews: {Review.objects.count()}")
print(f"Processed Reviews: {Review.objects.filter(processed=True).count()}")
print(f"Positive Reviews: {Review.objects.filter(sentiment='positive').count()}")
print(f"Negative Reviews: {Review.objects.filter(sentiment='negative').count()}")
print(f"Neutral Reviews: {Review.objects.filter(sentiment='neutral').count()}")

print("\n=== RECENT AI ANALYSIS ===")
for review in Review.objects.filter(processed=True).order_by('-updated_at')[:5]:
    print(f"Hotel: {review.hotel.name}")
    print(f"Sentiment: {review.sentiment} | AI Score: {review.ai_score}")
    print(f"Text: {review.text[:100]}...")
    print("---")
