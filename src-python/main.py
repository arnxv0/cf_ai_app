# Disable ADK telemetry FIRST - must be before any Google ADK imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

# Monkey-patch telemetry to completely disable it
import sys
from unittest.mock import MagicMock

# Create a no-op decorator that preserves function signatures
def noop_decorator(*args, **kwargs):
    """A decorator that does nothing - just returns the function unchanged"""
    if len(args) == 1 and callable(args[0]) and not kwargs:
        return args[0]
    else:
        def decorator(func):
            return func
        return decorator

# Create a fake telemetry module
fake_telemetry = MagicMock()
fake_telemetry.trace_call_llm = noop_decorator
sys.modules['google.adk.telemetry'] = fake_telemetry

print("🔇 Disabled Google ADK telemetry (avoids thought_signature bytes serialization issue)")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List
import logging

# Force load Quartz/PyObjC for pynput (required for PyInstaller)
try:
    import Quartz
    _ = Quartz.CGEventGetIntegerValueField
    _ = Quartz.CGEventGetFlags
    _ = Quartz.CGEventGetType
except (ImportError, AttributeError) as e:
    print(f"⚠️  Warning: Could not preload Quartz functions: {e}")

# Set up logging
logger = logging.getLogger("arrow")
logger.setLevel(logging.INFO)

from utils import (
    AccessibilityManager,
    ClipboardManager,
    KeyboardMonitor,
    ScreenshotHandler,
    get_settings_manager
)

# Load environment variables from encrypted settings database
def load_env_from_settings():
    """Load environment variables from settings database into os.environ."""
    try:
        settings_mgr = get_settings_manager()
        all_settings = settings_mgr.get_all_settings(include_secrets=True, decrypt_secrets=True)
        
        for category, settings in all_settings.items():
            for key, value in settings.items():
                if isinstance(value, str):
                    os.environ[key] = value
                    logger.info(f"Loaded {key} from settings database")
    except Exception as e:
        logger.warning(f"Could not load settings from database: {e}")
        from dotenv import load_dotenv
        load_dotenv()

load_env_from_settings()

# Import Arrow backend agent
try:
    from agent import root_agent
    from gradient_agent import InMemoryRunner
    
    arrow_runner = InMemoryRunner(agent=root_agent, app_name="arrow_agent")
    ARROW_BACKEND_AVAILABLE = True
    print("✅ Arrow backend agent loaded successfully")
except ImportError as e:
    ARROW_BACKEND_AVAILABLE = False
    arrow_runner = None
    print(f"⚠️  Arrow backend not available: {e}, running in basic mode")

# Create FastAPI app
app = FastAPI(title="Arrow Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from routes import health, settings, hotkey, rag, agent, storage, calendar_auth, integrations

# Set the ARROW_BACKEND_AVAILABLE flag in health router
health.ARROW_BACKEND_AVAILABLE = ARROW_BACKEND_AVAILABLE

# Set the arrow_runner in agent router
agent.arrow_runner = arrow_runner

# Include all route modules
app.include_router(health.router)
app.include_router(settings.router)
app.include_router(hotkey.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(storage.router)
app.include_router(calendar_auth.router)
app.include_router(integrations.router)


@app.get("/api/settings")
async def get_all_settings_toplevel():
    """Return all settings grouped by category (non-secrets only)."""
    try:
        settings_mgr = get_settings_manager()
        return settings_mgr.get_all_settings(include_secrets=False, decrypt_secrets=False)
    except Exception as e:
        logger.warning(f"Could not load all settings: {e}")
        return {}


# Debug endpoint for checking tools
@app.get("/api/debug/tools")
async def debug_tools():
    """Debug endpoint to see what tools are loaded"""
    try:
        from tools.tadata import get_tadata_integration
        from agents.coordinator import Coordinator

        tadata = get_tadata_integration()

        # Get detailed info about each tool
        tool_details = []
        for idx, tool in enumerate(Coordinator.tools):
            tool_info = {
                "index": idx + 1,
                "type": type(tool).__name__,
                "name": getattr(tool, 'name', 'unknown'),
                "has_name": hasattr(tool, 'name'),
                "has_description": hasattr(tool, 'description'),
                "has_func": hasattr(tool, 'func') or hasattr(tool, '_run'),
                "is_callable": callable(tool),
                "attributes": [attr for attr in dir(tool) if not attr.startswith('_')][:10]
            }

            if hasattr(tool, 'description'):
                tool_info['description'] = getattr(tool, 'description', '')[:100]

            tool_details.append(tool_info)

        return {
            "tadata_configured": tadata.is_configured(),
            "tadata_servers": list(tadata.servers.keys()) if tadata.servers else [],
            "tadata_tools_count": len(tadata.get_tools()),
            "tadata_connected": tadata._connected,
            "coordinator_tools_count": len(Coordinator.tools),
            "coordinator_has_tools_attr": hasattr(Coordinator, 'tools'),
            "coordinator_tools_is_list": isinstance(Coordinator.tools, list),
            "tool_details": tool_details
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/debug/test-tadata")
async def test_tadata_access():
    """Test if Coordinator can access Tadata tools"""
    try:
        from tools.tadata import get_tadata_integration
        from agents.coordinator import Coordinator

        tadata = get_tadata_integration()

        # Ensure Tadata is connected
        if tadata.is_configured() and not tadata._connected:
            await tadata.ensure_connected()

        # Check if tools are in Coordinator
        tadata_tool_names = [getattr(t, 'name', '') for t in tadata.get_tools()]
        coordinator_tool_names = [getattr(t, 'name', 'unknown') for t in Coordinator.tools]

        # Find Tadata tools in Coordinator
        tadata_in_coordinator = [name for name in tadata_tool_names if name in coordinator_tool_names]

        return {
            "tadata_connected": tadata._connected,
            "tadata_tools": tadata_tool_names,
            "coordinator_total_tools": len(Coordinator.tools),
            "coordinator_tool_names": coordinator_tool_names,
            "tadata_tools_in_coordinator": tadata_in_coordinator,
            "tadata_tools_accessible": len(tadata_in_coordinator) > 0,
            "message": f"✅ {len(tadata_in_coordinator)} Tadata tools accessible" if len(tadata_in_coordinator) > 0 else "❌ No Tadata tools found in Coordinator"
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []
    
    def add(self, websocket: WebSocket):
        self.connections.append(websocket)
    
    def remove(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
    
    def get_all(self):
        return self.connections[:]
    
    def count(self):
        return len(self.connections)

connection_manager = ConnectionManager()

# Initialize managers
accessibility_mgr = AccessibilityManager()
clipboard_mgr = ClipboardManager()
screenshot_handler = ScreenshotHandler()

# Global keyboard monitor instance
keyboard_monitor = None


@app.on_event("startup")
async def startup_event():
    """Startup event - keyboard monitor is initialized in main"""
    print("✅ Pointer backend startup event completed!")

    # Load Tadata tools if configured
    try:
        from tools.tadata import get_tadata_integration, reload_tadata_integration_async
        tadata = get_tadata_integration()
        if tadata.is_configured():
            print(f"🔄 Loading Tadata tools from {len(tadata.servers)} server(s)...")
            await reload_tadata_integration_async()
    except Exception as e:
        logger.error(f"Failed to load Tadata tools on startup: {e}")
        import traceback
        traceback.print_exc()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time events"""
    await websocket.accept()
    connection_manager.add(websocket)
    print(f"✅ WebSocket connected! Total connections: {connection_manager.count()}")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📨 Received WebSocket message: {data}")
    except WebSocketDisconnect:
        connection_manager.remove(websocket)
        print(f"❌ WebSocket disconnected. Remaining connections: {connection_manager.count()}")


def get_keyboard_monitor():
    """Get the global keyboard monitor instance"""
    return keyboard_monitor


def initialize_backend():
    """Initialize backend services before starting uvicorn"""
    global keyboard_monitor
    
    try:
        print("🚀 Arrow backend starting...", flush=True)
        
        # Load hotkey configuration from database
        print("⌨️  Loading hotkey configuration...", flush=True)
        hotkey_config = None
        inline_hotkey_config = None
        try:
            settings_mgr = get_settings_manager()
            hotkey_settings = settings_mgr.get_category("hotkey", include_secrets=False)
            
            if hotkey_settings and "modifiers" in hotkey_settings and "key" in hotkey_settings:
                hotkey_config = {
                    "modifiers": hotkey_settings["modifiers"],
                    "key": hotkey_settings["key"]
                }
                print(f"✅ Loaded popup hotkey: {hotkey_settings['modifiers']} + {hotkey_settings['key']}", flush=True)
            else:
                print("ℹ️  Using default popup hotkey: Cmd+Shift+K", flush=True)
            
            # Load inline hotkey (separate setting)
            if hotkey_settings and "inline_modifiers" in hotkey_settings and "inline_key" in hotkey_settings:
                inline_hotkey_config = {
                    "modifiers": hotkey_settings["inline_modifiers"],
                    "key": hotkey_settings["inline_key"]
                }
                print(f"✅ Loaded inline hotkey: {hotkey_settings['inline_modifiers']} + {hotkey_settings['inline_key']}", flush=True)
            else:
                print("ℹ️  Using default inline hotkey: Cmd+Shift+L", flush=True)
                
        except Exception as e:
            print(f"⚠️  Could not load hotkey settings: {e}, using defaults", flush=True)
        
        # Initialize keyboard monitor with both hotkey configs
        print("📡 Creating keyboard monitor...", flush=True)
        keyboard_monitor = KeyboardMonitor(
            connection_manager=connection_manager,
            hotkey_config=hotkey_config,
            inline_hotkey_config=inline_hotkey_config
        )
        
        print("⌨️  Starting keyboard monitor...", flush=True)
        keyboard_monitor.start()
        
        # Make keyboard_monitor available to hotkey router
        hotkey.keyboard_monitor = keyboard_monitor
        
        print("✅ Pointer backend ready!", flush=True)
    except Exception as e:
        print(f"❌ Error initializing backend: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Initialize keyboard monitor before starting server
    initialize_backend()
    
    # Run uvicorn server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765,
        log_level="info"
    )
