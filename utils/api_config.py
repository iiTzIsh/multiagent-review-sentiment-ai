"""
API Configuration utilities for consistent handling of API keys across agents
"""

import os
import logging

logger = logging.getLogger(__name__)


def get_gemini_api_key():
    """
    Get Gemini API key from Django settings or environment variables
    
    Returns:
        str: The Gemini API key if found, None otherwise
    """
    try:
        # Try to get from Django settings first
        from django.conf import settings
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            return settings.GEMINI_API_KEY
    except ImportError:
        # Django might not be configured in some contexts
        pass
    except Exception as e:
        logger.warning(f"Could not access Django settings: {str(e)}")
    
    # Fall back to environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("Gemini API key not found in settings or environment variables")
        logger.info("Please set GEMINI_API_KEY in your .env file or environment variables")
    
    return api_key


def validate_gemini_api_key():
    """
    Validate that Gemini API key is available and properly formatted
    
    Returns:
        bool: True if API key is valid, False otherwise
    """
    api_key = get_gemini_api_key()
    
    if not api_key:
        return False
    
    # Basic validation - Gemini API keys typically start with 'AIza'
    if not api_key.startswith('AIza'):
        logger.warning("Gemini API key format appears invalid (should start with 'AIza')")
        return False
    
    if len(api_key) < 30:  # Basic length check
        logger.warning("Gemini API key appears too short")
        return False
    
    return True


def get_huggingface_api_key():
    """
    Get HuggingFace API key from Django settings or environment variables
    
    Returns:
        str: The HuggingFace API key if found, None otherwise
    """
    try:
        from django.conf import settings
        if hasattr(settings, 'HUGGINGFACE_API_KEY') and settings.HUGGINGFACE_API_KEY:
            return settings.HUGGINGFACE_API_KEY
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Could not access Django settings: {str(e)}")
    
    return os.getenv('HUGGINGFACE_API_KEY')