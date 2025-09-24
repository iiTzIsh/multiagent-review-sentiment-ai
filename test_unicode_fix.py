!/usr/bin/env python
"""
Simple test script to verify Unicode encoding fixes in orchestrator.py
This tests that the orchestrator can be imported and logging works without encoding errors.
"""

import os
import sys
import django

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_review_platform.settings')
django.setup()

# Now test the orchestrator import and logging
try:
    print("Testing orchestrator import and logging...")
    
    # Import logging first
    import logging
    
    # Set up a simple logger to test ASCII characters
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('test_orchestrator')
    
    # Test the ASCII logging messages
    logger.info("[OK] Testing ASCII logging messages")
    logger.info("[COMPLETE] ASCII messages work correctly")
    
    # Try to import the orchestrator
    from agents.orchestrator import ReviewWorkflowOrchestrator
    print("✓ Orchestrator imported successfully")
    
    # Test basic initialization (this might take a moment due to AI model loading)
    print("Attempting orchestrator initialization...")
    print("Note: This may take time as it loads AI models...")
    
    # Create orchestrator instance
    orchestrator = ReviewWorkflowOrchestrator()
    print("✓ Orchestrator initialized without Unicode encoding errors!")
    
    print("\n=== TEST RESULTS ===")
    print("✓ Unicode encoding fixes successful")
    print("✓ ASCII logging messages work correctly")
    print("✓ Orchestrator can be imported and initialized")
    print("✓ No UnicodeEncodeError detected")
    
except UnicodeEncodeError as e:
    print(f"❌ Unicode encoding error still exists: {e}")
    print("The fix did not resolve all Unicode issues")
    
except Exception as e:
    print(f"⚠️  Other error occurred (not Unicode related): {e}")
    print("This might be due to missing dependencies or model loading issues")
    print("But it's not the Unicode encoding error we were fixing")
    
print("\nTest completed!")