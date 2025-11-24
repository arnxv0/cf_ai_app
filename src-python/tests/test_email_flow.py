#!/usr/bin/env python3
"""
Test script to verify the email flow works end-to-end.
This simulates the overlay -> backend -> email agent flow.
"""
import asyncio
import json
import sys
from settings_manager import get_settings_manager

async def test_email_flow():
    """Test the complete email sending flow."""
    
    print("=" * 60)
    print("🧪 TESTING EMAIL FLOW")
    print("=" * 60)
    
    # Step 1: Check settings
    print("\n📋 Step 1: Checking email settings...")
    settings_mgr = get_settings_manager()
    email_settings = settings_mgr.get_category('email', include_secrets=True, decrypt_secrets=True)
    
    print(f"   SMTP_HOST: {email_settings.get('SMTP_HOST', 'NOT SET')}")
    print(f"   SMTP_PORT: {email_settings.get('SMTP_PORT', 'NOT SET')}")
    print(f"   SMTP_USERNAME: {'SET' if email_settings.get('SMTP_USERNAME') else 'NOT SET'}")
    print(f"   SMTP_PASSWORD: {'SET' if email_settings.get('SMTP_PASSWORD') else 'NOT SET'}")
    print(f"   SMTP_FROM: {email_settings.get('SMTP_FROM', 'NOT SET')}")
    
    if not all([
        email_settings.get('SMTP_HOST'),
        email_settings.get('SMTP_USERNAME'),
        email_settings.get('SMTP_PASSWORD')
    ]):
        print("\n⚠️  WARNING: Email credentials not configured!")
        print("   The email tool will run in DRY RUN mode.")
        print("\n   To configure email:")
        print("   1. Open Pointer Settings")
        print("   2. Go to Environment Variables tab")
        print("   3. Add these variables in the 'email' category:")
        print("      - SMTP_USERNAME (your Gmail)")
        print("      - SMTP_PASSWORD (your app password)")
        print("      - SMTP_FROM (optional, defaults to SMTP_USERNAME)")
        print("\n   Or run:")
        print("   python -c \"from settings_manager import get_settings_manager; mgr = get_settings_manager(); mgr.set('email', 'SMTP_USERNAME', 'your@gmail.com'); mgr.set('email', 'SMTP_PASSWORD', 'your_app_password', is_secret=True); mgr.set('email', 'SMTP_FROM', 'your@gmail.com')\"")
    
    # Step 2: Load settings into environment
    print("\n🔄 Step 2: Loading settings into environment...")
    import os
    for key, value in email_settings.items():
        if isinstance(value, str):
            os.environ[key] = value
            print(f"   Loaded: {key}")
        elif isinstance(value, int):
            os.environ[key] = str(value)
            print(f"   Loaded: {key}")
    
    # Step 3: Test the agent
    print("\n🤖 Step 3: Testing Pointer agent with email request...")
    
    try:
        from agent import root_agent
        from google.adk.runners import InMemoryRunner
        from google.genai import types
        
        runner = InMemoryRunner(agent=root_agent, app_name="test_pointer")
        
        # Create session
        user_id = "test_user"
        session_id = "test_session_123"
        session = runner.session_service.create_session(
            app_name="test_pointer",
            user_id=user_id,
            session_id=session_id
        )
        
        # Simulate the overlay query
        test_query = "Send an email to arnavdewan.dev@gmail.com with subject 'Test from Pointer' and body 'This is a test email from Pointer AI assistant.'"
        
        print(f"   Query: {test_query}")
        print("\n   Running agent...")
        
        message = types.Content(
            role="user",
            parts=[types.Part(text=test_query)]
        )
        
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
                        print(f"   📝 {part.text}", flush=True)
        
        print(f"\n✅ Final response: {response_text}")
        
    except ImportError as e:
        print(f"\n❌ Could not load Pointer agent: {e}")
        print("   Make sure Google ADK is installed:")
        print("   pip install 'google-adk[database]==0.3.0'")
        return False
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)
    return True


if __name__ == '__main__':
    asyncio.run(test_email_flow())
