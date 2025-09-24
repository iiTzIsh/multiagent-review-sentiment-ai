"""
Management command: clean_reviews
Simple command to remove processed reviews from database
"""

from django.core.management.base import BaseCommand
from apps.reviews.models import Review


class Command(BaseCommand):
    help = 'Clean (remove) processed reviews from database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Remove ALL reviews (processed and unprocessed)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true', 
            help='Skip confirmation prompt'
        )
    
    def handle(self, *args, **options):
        if options['all']:
            # Remove all reviews
            reviews = Review.objects.all()
            message = "ALL reviews"
        else:
            # Remove only processed reviews
            reviews = Review.objects.filter(processed=True)
            message = "processed reviews"
        
        count = reviews.count()
        
        self.stdout.write(f"Found {count} {message} to remove.")
        
        if count == 0:
            self.stdout.write("No reviews to clean.")
            return
        
        # Ask for confirmation unless --confirm flag is used
        if not options['confirm']:
            confirm = input(f"Are you sure you want to delete {count} {message}? (yes/no): ")
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write("Operation cancelled.")
                return
        
        # Delete the reviews
        deleted_count, _ = reviews.delete()
        
        # Also clean up hotels with no reviews
        from apps.reviews.models import Hotel, ReviewBatch
        orphaned_hotels = Hotel.objects.filter(reviews__isnull=True)
        hotel_count = orphaned_hotels.count()
        
        if hotel_count > 0:
            orphaned_hotels.delete()
            self.stdout.write(f"🏨 Also removed {hotel_count} hotels with no reviews")
        
        # Clean up review batches when removing all reviews
        if options['all']:
            batch_count = ReviewBatch.objects.count()
            if batch_count > 0:
                ReviewBatch.objects.all().delete()
                self.stdout.write(f"📦 Also removed {batch_count} review batches")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Successfully removed {deleted_count} {message}"
            )
        )