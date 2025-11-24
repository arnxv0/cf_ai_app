"""
Script to populate default environment variables in the settings database.
This makes it easy to migrate from .env files to encrypted storage.
"""
import os
import sys

# Add parent directory to path so we can import from utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.settings_manager import get_settings_manager
from dotenv import load_dotenv

# Load existing .env if it exists
load_dotenv()

def populate_default_settings():
    """Populate settings database with defaults from environment or .env file."""
    settings_mgr = get_settings_manager()
    
    # Google API Keys
    google_api_settings = {
        'GOOGLE_GENAI_USE_VERTEXAI': (os.getenv('GOOGLE_GENAI_USE_VERTEXAI', '0'), False),
        'GOOGLE_API_KEY': (os.getenv('GOOGLE_API_KEY', ''), True),
        'GROQ_API_KEY': (os.getenv('GROQ_API_KEY', ''), True),
    }
    
    for key, (value, is_secret) in google_api_settings.items():
        if value:
            settings_mgr.set('api_keys', key, value, is_secret=is_secret)
            print(f"✅ Set {key}")
    
    # Email (SMTP) Settings
    email_settings = {
        'SMTP_HOST': (os.getenv('SMTP_HOST', 'smtp.gmail.com'), False),
        'SMTP_PORT': (os.getenv('SMTP_PORT', '587'), False),
        'SMTP_USERNAME': (os.getenv('SMTP_USERNAME', ''), False),
        'SMTP_PASSWORD': (os.getenv('SMTP_PASSWORD', ''), True),
        'SMTP_FROM': (os.getenv('SMTP_FROM', ''), False),
    }
    
    for key, (value, is_secret) in email_settings.items():
        if value:
            settings_mgr.set('email', key, value, is_secret=is_secret)
            print(f"✅ Set {key}")
    
    # Google Calendar Settings
    calendar_settings = {
        'GOOGLE_CALENDAR_CREDENTIALS_JSON': (os.getenv('GOOGLE_CALENDAR_CREDENTIALS_JSON', './credentials.json'), False),
        'GOOGLE_CALENDAR_TOKEN_JSON': (os.getenv('GOOGLE_CALENDAR_TOKEN_JSON', './token.json'), False),
        'CALENDAR_ID': (os.getenv('CALENDAR_ID', 'primary'), False),
    }
    
    for key, (value, is_secret) in calendar_settings.items():
        if value:
            settings_mgr.set('calendar', key, value, is_secret=is_secret)
            print(f"✅ Set {key}")
    
    # Pointer Configuration
    pointer_settings = {
        'POINTER_APP_NAME': (os.getenv('POINTER_APP_NAME', 'pointer'), False),
        'POINTER_AGENTS_DIR': (os.getenv('POINTER_AGENTS_DIR', './agents'), False),
        'POINTER_ENV_DIR': (os.getenv('POINTER_ENV_DIR', './'), False),
    }
    
    for key, (value, is_secret) in pointer_settings.items():
        if value:
            settings_mgr.set('pointer', key, value, is_secret=is_secret)
            print(f"✅ Set {key}")
    
    print("\n🎉 Default settings populated!")
    print(f"📊 Categories: {', '.join(settings_mgr.get_all_categories())}")


if __name__ == '__main__':
    populate_default_settings()
