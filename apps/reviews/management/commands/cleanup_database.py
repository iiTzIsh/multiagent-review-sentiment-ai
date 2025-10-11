"""
Management command to clean up unnecessary database tables
Removes analytics tables that are no longer needed after restructuring
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Remove unnecessary database tables left over from analytics app'
    
    # Tables to remove (analytics app leftovers)
    TABLES_TO_REMOVE = [
        'analytics_analyticsreport',
        'analytics_competitorcomparison',
        'analytics_competitorcomparison_competitor_hotels',
        'analytics_keywordfrequency', 
        'analytics_sentimenttrend',
        'analytics_systemmetrics',
        'analytics_userengagement',
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what tables would be removed without actually removing them',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force removal without confirmation prompt',
        )
    
    def handle(self, *args, **options):
        """Execute the table cleanup"""
        
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.WARNING('🗂️  Database Table Cleanup Utility')
        )
        self.stdout.write('')
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                # Get existing tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                
                existing_tables = [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            raise CommandError(f'Failed to connect to database: {e}')
        
        # Find tables that exist and need to be removed
        tables_to_remove = []
        for table in self.TABLES_TO_REMOVE:
            if table in existing_tables:
                tables_to_remove.append(table)
        
        if not tables_to_remove:
            self.stdout.write(
                self.style.SUCCESS('✅ No unnecessary tables found. Database is already clean!')
            )
            return
        
        # Show what will be removed
        self.stdout.write(
            self.style.WARNING(f'📋 Found {len(tables_to_remove)} unnecessary tables:')
        )
        for table in tables_to_remove:
            self.stdout.write(f'   • {table}')
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('🔍 DRY RUN: Above tables would be removed (use --force to actually remove)')
            )
            return
        
        # Confirmation prompt
        if not force:
            confirm = input('⚠️  Are you sure you want to remove these tables? This cannot be undone! (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.ERROR('❌ Operation cancelled'))
                return
        
        # Remove tables
        self.stdout.write('🗑️  Removing unnecessary tables...')
        
        try:
            with connection.cursor() as cursor:
                for table in tables_to_remove:
                    self.stdout.write(f'   Dropping table: {table}')
                    
                    # Drop the table
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Removed: {table}')
                    )
                
        except Exception as e:
            raise CommandError(f'Failed to remove tables: {e}')
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Successfully removed {len(tables_to_remove)} unnecessary tables!')
        )
        self.stdout.write(
            self.style.SUCCESS('💽 Database is now clean and optimized.')
        )
        
        # Show remaining relevant tables
        remaining_review_tables = [
            table for table in existing_tables 
            if table.startswith('reviews_') and table not in tables_to_remove
        ]
        
        if remaining_review_tables:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(f'📊 Active review tables ({len(remaining_review_tables)}):')
            )
            for table in sorted(remaining_review_tables):
                self.stdout.write(f'   • {table}')