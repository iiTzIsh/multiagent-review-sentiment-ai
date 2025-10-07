"""
Django management command to test API configuration
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from utils.api_config import get_gemini_api_key, validate_gemini_api_key, get_huggingface_api_key
import google.generativeai as genai


class Command(BaseCommand):
    help = 'Test API configuration and connectivity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('🔧 Testing API Configuration...'))
        self.stdout.write('')
        
        # Test Gemini API
        self.stdout.write('📡 Testing Gemini API Configuration:')
        gemini_key = get_gemini_api_key()
        
        if gemini_key:
            self.stdout.write(f'  ✅ Gemini API key found: {gemini_key[:10]}...{gemini_key[-4:]}')
            
            if validate_gemini_api_key():
                self.stdout.write('  ✅ Gemini API key format is valid')
                
                # Test actual API connection
                try:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    response = model.generate_content("Hello, test connection")
                    if response and response.text:
                        self.stdout.write('  ✅ Gemini API connection successful')
                    else:
                        self.stdout.write('  ⚠️  Gemini API responded but with empty content')
                except Exception as e:
                    self.stdout.write(f'  ❌ Gemini API connection failed: {str(e)}')
            else:
                self.stdout.write('  ❌ Gemini API key format is invalid')
        else:
            self.stdout.write('  ❌ Gemini API key not found')
            self.stdout.write('  💡 Add GEMINI_API_KEY to your .env file')
        
        self.stdout.write('')
        
        # Test HuggingFace API
        self.stdout.write('🤗 Testing HuggingFace API Configuration:')
        hf_key = get_huggingface_api_key()
        
        if hf_key:
            self.stdout.write(f'  ✅ HuggingFace API key found: {hf_key[:10]}...{hf_key[-4:]}')
        else:
            self.stdout.write('  ⚠️  HuggingFace API key not found (optional)')
        
        self.stdout.write('')
        
        # Test Django settings
        self.stdout.write('⚙️  Testing Django Configuration:')
        
        if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY:
            self.stdout.write('  ✅ Django SECRET_KEY configured')
        else:
            self.stdout.write('  ❌ Django SECRET_KEY not configured')
        
        if hasattr(settings, 'GEMINI_API_KEY'):
            self.stdout.write('  ✅ GEMINI_API_KEY in Django settings')
        else:
            self.stdout.write('  ❌ GEMINI_API_KEY not in Django settings')
        
        self.stdout.write('')
        
        # Summary
        if gemini_key and validate_gemini_api_key():
            self.stdout.write(self.style.SUCCESS('🎉 Configuration looks good! All agents should work properly.'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Configuration issues detected. Some features may not work.'))
            self.stdout.write('')
            self.stdout.write('📚 See ENVIRONMENT_SETUP.md for detailed setup instructions.')