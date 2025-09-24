"""
Management command: process_reviews
Alias for process_with_crewai for backward compatibility
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Process reviews using CrewAI agents (alias for process_with_crewai)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size', 
            type=int, 
            default=10, 
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
        """Forward all arguments to the actual CrewAI command"""
        self.stdout.write(
            self.style.SUCCESS(
                '🔗 Forwarding to process_with_crewai command...'
            )
        )
        
        # Forward all options to the actual command
        call_command('process_with_crewai', **options)