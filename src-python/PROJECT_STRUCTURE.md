# Arrow Backend - Project Structure

## Overview

The Arrow backend has been refactored into a clean, modular architecture following FastAPI best practices.

# Arrow Backend - Project Structure

## 📁 Directory Organization

```
src-python/
├── main.py                 # FastAPI application entry point (222 lines)
├── agent.py                # Root AI agent configuration
│
├── routes/                 # API endpoints (organized by feature)
│   ├── __init__.py
│   ├── health.py          # Health check & status endpoints
│   ├── agent.py           # AI agent processing endpoints
│   ├── settings.py        # Settings management endpoints
│   ├── hotkey.py          # Hotkey configuration endpoints
│   └── rag.py             # RAG/Knowledge base endpoints
│
├── agents/                 # AI sub-agents
│   ├── __init__.py
│   ├── coordinator.py     # Main routing agent (formerly router.py)
│   ├── summarize.py       # Summarization agent
│   └── terminal_cmd.py    # Terminal command generation agent
│
├── tools/                  # Agent tools
│   ├── __init__.py
│   ├── calendar.py        # Google Calendar integration
│   ├── emailer.py         # Email sending tool
│   ├── rag.py             # RAG/Vector store tool
│   └── vision.py          # Screenshot/image analysis tool
│
├── utils/                  # Core utilities
│   ├── __init__.py
│   ├── accessibility.py   # macOS accessibility permissions
│   ├── clipboard_manager.py
│   ├── cursor_manager.py  # Custom cursor (deprecated)
│   ├── keyboard_monitor.py # Global hotkey monitoring
│   ├── screenshot_handler.py
│   └── settings_manager.py # Encrypted settings database
│
├── scripts/                # Development & build scripts
│   ├── build.py           # PyInstaller build script
│   └── populate_settings.py # Settings migration helper
│
├── tests/                  # Test files
│   └── test_email_flow.py
│
├── deprecated/             # Deprecated code (kept for reference)
│   └── plugin_selector.py # Old plugin system (replaced by ADK agents)
│
├── hooks/                  # PyInstaller hooks
│   └── runtime-quartz.py  # Quartz/PyObjC runtime hook
│
├── dist/                   # Build output directory
├── build/                  # Build artifacts
│
└── Configuration Files:
    ├── requirements.txt
    ├── pointer-backend.spec
    ├── credentials.json
    ├── knowledge_base.db
    └── .env.example
```

## 🚀 Key Components

### Main Application (`main.py`)

- **Purpose**: FastAPI server initialization
- **Size**: 222 lines (reduced from 784!)
- **Responsibilities**:
  - Load environment from encrypted settings
  - Initialize ADK agent runner
  - Set up CORS middleware
  - Include route modules
  - Manage WebSocket connections
  - Initialize keyboard monitor with hotkey config

### Routes (`routes/`)

Each route file handles a specific domain:

- **`health.py`**: Health checks, backend availability status
- **`agent.py`**: Process user queries through AI agent
- **`settings.py`**: CRUD operations for encrypted settings
- **`hotkey.py`**: Hotkey configuration management
- **`rag.py`**: Knowledge base operations (add, query, list, delete documents)

### Agents (`agents/`)

AI agents using Google ADK:

- **`coordinator.py`**: Routes commands to appropriate tools/sub-agents
  - Email → send_email
  - Schedule → calendar
  - Summary → SummarizerAgent
  - Terminal → TerminalCmdAgent
  - Knowledge → RAG tools
- **`summarize.py`**: Text summarization agent
- **`terminal_cmd.py`**: Shell command generation agent

### Tools (`tools/`)

Function tools available to agents:

- **`calendar.py`**: Google Calendar integration
- **`emailer.py`**: SMTP email sending
- **`rag.py`**: Vector database with SQLite persistence
- **`vision.py`**: Screenshot analysis using Gemini Vision

### Utils (`utils/`)

Core system utilities:

- **`settings_manager.py`**: Encrypted SQLite settings storage with AES-256
- **`keyboard_monitor.py`**: Global hotkey monitoring using pynput
- **`accessibility.py`**: macOS accessibility permission checks
- **`clipboard_manager.py`**: Clipboard operations
- **`screenshot_handler.py`**: Screen capture functionality

## 📊 Data Flow

```
User Input (Hotkey)
    ↓
keyboard_monitor.py (utils/)
    ↓
WebSocket → Frontend Overlay
    ↓
POST /api/agent (routes/agent.py)
    ↓
root_agent (agent.py)
    ↓
Coordinator (agents/coordinator.py)
    ↓
Tools (tools/) or Sub-Agents (agents/)
    ↓
Response → Frontend
```

## 🔧 Development Scripts

### Build Script (`scripts/build.py`)

- Creates PyInstaller binary for Tauri sidecar
- Platform-specific naming (e.g., `pointer-backend-aarch64-apple-darwin`)
- Automatically copies to `src-tauri/binaries/`

### Populate Settings (`scripts/populate_settings.py`)

- Migrates environment variables from `.env` to encrypted database
- Supports categories: api_keys, email, calendar, pointer
- Encrypts sensitive values (API keys, passwords)

## 🗄️ Database Schema

### Settings Database (`settings_manager.py`)

```sql
CREATE TABLE settings (
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    is_encrypted BOOLEAN DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (category, key)
)
```

### Knowledge Base (`tools/rag.py`)

```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    vec BLOB NOT NULL,
    source TEXT NOT NULL,
    filename TEXT,
    created_at TEXT NOT NULL,
    metadata TEXT
)
```

## 🔐 Security

- **Encrypted Settings**: AES-256-GCM encryption for sensitive data
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **Salt Storage**: Unique salt per installation
- **No Plaintext**: API keys, passwords never stored in plaintext

## 🧪 Testing

Run tests from project root:

```bash
cd src-python
python tests/test_email_flow.py
```

## 🏗️ Building

Build the binary:

```bash
cd src-python
python scripts/build.py
```

Output: `dist/pointer-backend-{platform}`

## 📦 Dependencies

See `requirements.txt` for full list. Key dependencies:

- **FastAPI**: Web framework
- **uvicorn**: ASGI server
- **google-adk**: AI agent framework
- **pynput**: Keyboard/mouse monitoring
- **PyObjC**: macOS system integration
- **cryptography**: Settings encryption

## 🔄 Migration Notes

### From Old Structure

- ✅ `router.py` → `agents/coordinator.py`
- ✅ `plugin_selector.py` → `deprecated/` (replaced by ADK)
- ✅ Utility files → `utils/` package
- ✅ Route handlers → `routes/` package
- ✅ Scripts → `scripts/` directory
- ✅ Tests → `tests/` directory

### Import Changes

```python
# Old
from settings_manager import get_settings_manager
from keyboard_monitor import KeyboardMonitor

# New
from utils.settings_manager import get_settings_manager
from utils.keyboard_monitor import KeyboardMonitor
```

## 📝 Notes

- Main application reduced from 784 → 222 lines
- Better separation of concerns
- Easier to test and maintain
- Clear module boundaries
- Deprecated code preserved for reference

````

## API Routes

### Health (`/`)
- `GET /` - Root endpoint
- `GET /health` - Health check

### Agent (`/api`)
- `POST /api/process-query` - Legacy query endpoint
- `POST /api/agent` - Main AI agent endpoint

### Settings (`/api/settings`)
- `GET /api/settings/categories` - List all categories
- `GET /api/settings/{category}` - Get category settings
- `GET /api/settings/{category}/{key}` - Get specific setting
- `POST /api/settings` - Set a setting
- `DELETE /api/settings/{category}/{key}` - Delete a setting
- `POST /api/settings/import` - Import from .env format
- `GET /api/settings/export/{category}` - Export to .env format

### Hotkey (`/api/hotkey`)
- `GET /api/hotkey/current` - Get current hotkey
- `POST /api/hotkey/set` - Set custom hotkey
- `POST /api/hotkey/reset` - Reset to default

### RAG/Knowledge Base (`/api/rag`)
- `POST /api/rag/add` - Add document to knowledge base
- `POST /api/rag/query` - Search knowledge base
- `GET /api/rag/documents` - List all documents
- `DELETE /api/rag/documents/{id}` - Delete document
- `POST /api/rag/upload` - Upload file to knowledge base

## Key Features

### 1. Modular Route Structure
Each functional area has its own route file with clear separation of concerns:
- **Agent routes**: AI processing and query handling
- **Settings routes**: Configuration management
- **Hotkey routes**: Keyboard shortcut configuration
- **RAG routes**: Knowledge base operations

### 2. Centralized Utilities
All core utilities are in the `utils/` package:
- Accessibility management
- Clipboard operations
- Keyboard monitoring
- Screenshot handling
- Settings persistence (SQLite)

### 3. Agent System
- **Root Agent**: Main entry point for AI operations
- **Coordinator**: Routes tasks to appropriate sub-agents/tools
- **Sub-agents**: Specialized agents for specific tasks
- **Tools**: Reusable functions for agents

### 4. Clean Imports
```python
# main.py
from utils import (
    AccessibilityManager,
    ClipboardManager,
    KeyboardMonitor,
    ScreenshotHandler,
    get_settings_manager
)

# routes
from utils.settings_manager import get_settings_manager
````

## Configuration

### Environment Variables

Loaded from SQLite database (encrypted) or `.env` file:

- `GEMINI_API_KEY`
- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`

### Hotkey Configuration

- Stored in SQLite database
- Default: Cmd+Shift+K
- Configurable via API

### Knowledge Base

- SQLite storage (`knowledge_base.db`)
- Vector embeddings for semantic search
- Supports text and file uploads

## Workflow

1. **Startup** (`main.py`):

   - Load environment variables from database
   - Initialize agent system
   - Set up routes
   - Start keyboard monitor
   - Run FastAPI server

2. **Hotkey Trigger**:

   - Keyboard monitor detects hotkey
   - Captures selected text/screenshot
   - Sends context via WebSocket
   - Shows overlay UI

3. **Query Processing**:

   - Frontend sends query to `/api/agent`
   - Agent processes with context
   - Returns AI response
   - Frontend displays result

4. **Knowledge Base** (Automatic):
   - Agent detects "remember this" intent
   - Uses RAG tool to store information
   - Retrieves on future queries
   - No manual buttons needed

## Benefits of New Structure

1. **Maintainability**: Each module has a single responsibility
2. **Scalability**: Easy to add new routes/features
3. **Testability**: Modules can be tested independently
4. **Readability**: Clear organization, easy to navigate
5. **Performance**: Lazy imports, efficient routing

## Migration Notes

### Breaking Changes

- Import paths changed: `from accessibility import` → `from utils import`
- Route endpoints remain the same (backward compatible)

### Files Moved

- `accessibility.py` → `utils/accessibility.py`
- `clipboard_manager.py` → `utils/clipboard_manager.py`
- `keyboard_monitor.py` → `utils/keyboard_monitor.py`
- `screenshot_handler.py` → `utils/screenshot_handler.py`
- `settings_manager.py` → `utils/settings_manager.py`

### Old Files (Can be deleted)

- `main_old.py` - Old main.py backup
- `main.py.backup` - Another backup
- `cursor_manager.py` - Deprecated feature
