"""
Django management command to delete superuser accounts
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Delete superuser accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            nargs='?',
            type=str,
            help='Username of superuser to delete'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all superusers'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_superusers()
            return

        username = options['username']
        if not username:
            self.stdout.write(
                self.style.ERROR('Please provide a username or use --list to see available superusers')
            )
            return

        try:
            user = User.objects.get(username=username, is_superuser=True)
            
            if not options['confirm']:
                confirm = input(f"Are you sure you want to delete superuser '{username}'? (y/N): ")
                if confirm.lower() != 'y':
                    self.stdout.write(self.style.WARNING('Operation cancelled'))
                    return

            user.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted superuser: {username}')
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Superuser with username "{username}" not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error deleting superuser: {str(e)}')
            )

    def list_superusers(self):
        """List all superuser accounts"""
        superusers = User.objects.filter(is_superuser=True)
        
        if not superusers:
            self.stdout.write(self.style.WARNING('No superusers found'))
            return

        self.stdout.write(self.style.SUCCESS('Current superusers:'))
        for user in superusers:
            status = 'Active' if user.is_active else 'Inactive'
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
            self.stdout.write(
                f'  - {user.username} ({user.email}) - {status} - Last login: {last_login}'
            )