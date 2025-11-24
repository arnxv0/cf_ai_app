"""
Calendar OAuth authentication routes.
"""

from fastapi import APIRouter, HTTPException
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pydantic import BaseModel
import json
import os
from pathlib import Path
from typing import Optional

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

# OAuth 2.0 scopes for Google Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Redirect URI for OAuth flow
REDIRECT_URI = "http://localhost:8765/api/calendar/auth/callback"

# Global variable to store the flow object during OAuth process
_oauth_flow: Optional[Flow] = None


class CredentialsInput(BaseModel):
    credentials: str  # JSON string of OAuth credentials


def _get_data_dir() -> Path:
    """Get the application data directory based on OS."""
    import platform
    system = platform.system()
    
    if system == "Darwin":  # macOS
        data_dir = Path.home() / "Library" / "Application Support" / "Pointer"
    elif system == "Windows":
        data_dir = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "Pointer"
    else:  # Linux
        data_dir = Path.home() / ".local" / "share" / "Pointer"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _get_credentials_path() -> Path:
    """Get the path to the OAuth client credentials file."""
    # First check in the data directory
    data_dir = _get_data_dir()
    creds_path = data_dir / "oauth_client_credentials.json"
    
    if creds_path.exists():
        return creds_path
    
    # Fallback to src-python directory
    src_python_dir = Path(__file__).parent.parent
    creds_path = src_python_dir / "oauth_client_credentials.json"
    
    if not creds_path.exists():
        # Try the test directory as well
        test_dir = src_python_dir.parent / "test"
        creds_path = test_dir / "credentials.json"
    
    return creds_path


def _get_token_path() -> Path:
    """Get the path where OAuth tokens are stored."""
    return _get_data_dir() / "calendar_token.json"


def _load_credentials() -> Optional[Credentials]:
    """Load stored OAuth credentials."""
    token_path = _get_token_path()
    
    if not token_path.exists():
        return None
    
    try:
        with open(token_path, "r") as f:
            token_data = json.load(f)
        
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_credentials(creds)
        
        return creds
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None


def _save_credentials(creds: Credentials):
    """Save OAuth credentials to disk."""
    token_path = _get_token_path()
    
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)


def _get_user_email(creds: Credentials) -> Optional[str]:
    """Get the user's email address from their Google account."""
    try:
        from googleapiclient.discovery import build
        
        service = build("oauth2", "v2", credentials=creds)
        user_info = service.userinfo().get().execute()
        return user_info.get("email")
    except Exception as e:
        print(f"Error getting user email: {e}")
        return None


@router.get("/status")
async def get_calendar_status():
    """Check if the user has connected their calendar."""
    creds = _load_credentials()
    
    if not creds or not creds.valid:
        return {
            "connected": False,
            "email": None,
        }
    
    email = _get_user_email(creds)
    
    return {
        "connected": True,
        "email": email,
    }


@router.post("/credentials")
async def save_oauth_credentials(input_data: CredentialsInput):
    """Save OAuth client credentials from the frontend."""
    try:
        # Parse and validate the credentials JSON
        creds_data = json.loads(input_data.credentials)
        
        # Validate it has the required structure
        if "installed" not in creds_data and "web" not in creds_data:
            raise HTTPException(
                status_code=400,
                detail="Invalid credentials format. Must contain 'installed' or 'web' key.",
            )
        
        # Fix redirect URIs to include our callback endpoint
        # This ensures the OAuth flow works regardless of what was set in Google Cloud Console
        if "installed" in creds_data:
            creds_data["installed"]["redirect_uris"] = [
                "http://localhost:8765/api/calendar/auth/callback",
                "http://localhost",
            ]
        elif "web" in creds_data:
            creds_data["web"]["redirect_uris"] = [
                "http://localhost:8765/api/calendar/auth/callback",
                "http://localhost",
            ]
        
        # Save to the data directory
        data_dir = _get_data_dir()
        creds_path = data_dir / "oauth_client_credentials.json"
        
        with open(creds_path, "w") as f:
            json.dump(creds_data, f, indent=2)
        
        print(f"[Calendar OAuth] Saved credentials to: {creds_path}")
        print(f"[Calendar OAuth] Updated redirect URIs to include our callback endpoint")
        
        return {
            "success": True,
            "message": "OAuth credentials saved successfully",
            "path": str(creds_path),
        }
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON format: {str(e)}",
        )
    except Exception as e:
        print(f"[Calendar OAuth Error] Failed to save credentials: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save credentials: {str(e)}",
        )


@router.post("/auth/start")
async def start_oauth_flow():
    """Start the OAuth flow and return the authorization URL."""
    global _oauth_flow
    
    creds_path = _get_credentials_path()
    data_dir = _get_data_dir()
    
    print(f"[Calendar OAuth] Looking for credentials at: {creds_path}")
    print(f"[Calendar OAuth] Data directory: {data_dir}")
    
    if not creds_path.exists():
        error_msg = (
            f"OAuth client credentials not found. Please download oauth_client_credentials.json "
            f"from Google Cloud Console and place it at: {data_dir}/oauth_client_credentials.json\n\n"
            f"See CALENDAR_OAUTH_SETUP.md for detailed instructions."
        )
        print(f"[Calendar OAuth Error] {error_msg}")
        raise HTTPException(
            status_code=400,
            detail=error_msg,
        )
    
    try:
        print(f"[Calendar OAuth] Creating OAuth flow with credentials from: {creds_path}")
        _oauth_flow = Flow.from_client_secrets_file(
            str(creds_path),
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )
        
        auth_url, _ = _oauth_flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",  # Force consent to get refresh token
        )
        
        print(f"[Calendar OAuth] Generated auth URL successfully")
        return {"auth_url": auth_url}
    
    except Exception as e:
        error_msg = f"Failed to start OAuth flow: {str(e)}"
        print(f"[Calendar OAuth Error] {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/auth/callback")
async def oauth_callback(code: str = None, error: str = None):
    """Handle the OAuth callback from Google."""
    global _oauth_flow
    
    if error:
        return {
            "success": False,
            "error": error,
        }
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    if not _oauth_flow:
        raise HTTPException(status_code=400, detail="No OAuth flow in progress")
    
    try:
        # Exchange the authorization code for credentials
        _oauth_flow.fetch_token(code=code)
        creds = _oauth_flow.credentials
        
        # Save the credentials
        _save_credentials(creds)
        
        # Clear the flow
        _oauth_flow = None
        
        # Return a simple success page
        return """
        <html>
            <head>
                <title>Calendar Connected</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 3rem;
                        border-radius: 12px;
                        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                        text-align: center;
                    }
                    .icon {
                        font-size: 64px;
                        color: #34c759;
                        margin-bottom: 1rem;
                    }
                    h1 {
                        color: #333;
                        margin-bottom: 0.5rem;
                    }
                    p {
                        color: #666;
                        margin-bottom: 2rem;
                    }
                    button {
                        background: #007aff;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                    }
                    button:hover {
                        background: #0051d5;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">✓</div>
                    <h1>Calendar Connected!</h1>
                    <p>You can now close this window and return to Pointer.</p>
                    <button onclick="window.close()">Close Window</button>
                </div>
            </body>
        </html>
        """
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth flow: {str(e)}")


@router.post("/disconnect")
async def disconnect_calendar():
    """Disconnect the calendar by deleting stored credentials."""
    token_path = _get_token_path()
    
    if token_path.exists():
        token_path.unlink()
    
    return {"success": True}


@router.get("/auth/status")
async def get_auth_status():
    """Check if the user is authenticated (alias for /status)."""
    return await get_calendar_status()


def get_calendar_credentials() -> Optional[Credentials]:
    """
    Get valid calendar credentials for use by the calendar tool.
    This function is used by tools/calendar.py.
    """
    return _load_credentials()
