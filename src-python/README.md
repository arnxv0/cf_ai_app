# Arrow Backend

A structured Python backend for the Pointer AI desktop assistant.

## Project Structure

```
src-python/
├── main.py                 # FastAPI server & initialization
├── agent.py                # Root AI agent configuration
├── router.py               # Coordinator agent & routing logic
│
├── agents/                 # AI Agent modules
│   ├── __init__.py
│   ├── summarize.py        # Text summarization agent
│   └── terminal_cmd.py     # Terminal command generation agent
│
├── tools/                  # AI Tools for agents
│   ├── __init__.py
│   ├── calendar.py         # Google Calendar integration
│   ├── emailer.py          # SMTP email sending
│   ├── rag.py              # RAG (Retrieval-Augmented Generation)
│   └── vision.py           # Context attachment & vision
│
├── Core Modules (flat structure for now)
│   ├── accessibility.py            # macOS accessibility API
│   ├── keyboard_monitor.py         # Hotkey listener & inline mode
│   ├── cursor_manager.py           # Custom cursor management
│   ├── clipboard_manager.py        # Clipboard operations
│   ├── screenshot_handler.py       # Screenshot capture
│   └── settings_manager.py         # Encrypted settings storage
│
├── Build & Deployment
│   ├── build.py                    # PyInstaller build script
│   ├── pointer-backend.spec        # PyInstaller spec file
│   ├── requirements.txt            # Python dependencies
│   ├── hooks/                      # PyInstaller hooks
│   │   └── runtime-quartz.py
│   └── build/                      # Build artifacts
│       └── pointer-backend/
│
└── Configuration & Data
    ├── credentials.json            # Google API credentials
    ├── populate_settings.py        # Settings initialization
    └── test_email_flow.py          # Email testing script
```

## Key Components

### Main Server (`main.py`)

- FastAPI application with CORS
- WebSocket support for real-time events
- Agent API endpoint (`/api/agent`)
- Settings management endpoints
- Health checks and monitoring

### AI Agents

#### Root Agent (`agent.py`)

- Multi-tool AI agent with context awareness
- Uses Gemini 2.5 Flash model
- Delegates to specialized sub-agents

#### Coordinator (`router.py`)

- Routes commands to appropriate tools/agents
- Handles email composition with vague prompts
- Manages context from selected text

#### Specialized Agents (`agents/`)

- **Summarizer**: Text summarization
- **TerminalCmdGen**: Shell command generation (returns raw commands only)

### Tools (`tools/`)

- **Calendar**: Google Calendar event management
- **Emailer**: Professional email composition & sending with SMTP
- **RAG**: Vector storage and retrieval (ChromaDB)
- **Vision**: Screenshot context attachment

### Core Modules

#### Keyboard Monitor (`keyboard_monitor.py`)

- **Dual Mode System**:

  1. **Inline Mode**: Captures keystrokes in text fields
     - First hotkey press activates keystroke capture
     - Second hotkey press processes query
     - Backspaces query, shows "Thinking...", types AI response
  2. **Normal Mode**: Works with selected text
     - Uses clipboard (Cmd+C) to get selected text
     - Shows overlay for user input
     - Sends to AI agent

- **Text Field Detection**: AppleScript checks for terminals (ghostty, iTerm, Terminal, etc.)
- **Keystroke Capture**: Stores chars, space, backspace, enter
- **No Clipboard in Inline Mode**: Pure keystroke capture

#### Settings Manager (`settings_manager.py`)

- Encrypted storage using Fernet encryption
- SQLite database backend
- Environment variable loading
- Import/export .env format

#### Cursor Manager (`cursor_manager.py`)

- Custom cursor support
- macOS CGImage cursor loading

#### Screenshot Handler (`screenshot_handler.py`)

- Screen capture functionality
- Context image support for AI

## API Endpoints

### Agent

- `POST /api/agent` - Process messages through AI agent
  - Request: `{message: str, context_parts: [], session_id: str}`
  - Response: `{response: str, session_id: str, metadata: {}}`

### Settings

- `GET /api/settings/categories` - List all categories
- `GET /api/settings/{category}` - Get category settings
- `GET /api/settings/{category}/{key}` - Get specific setting
- `POST /api/settings` - Create/update setting
- `DELETE /api/settings/{category}/{key}` - Delete setting
- `POST /api/settings/import` - Import from .env format
- `GET /api/settings/export/{category}` - Export as .env

### WebSocket

- `/ws` - Real-time event stream for overlay updates

### System

- `GET /` - API information
- `GET /health` - Health check

## Development

### Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode (instant reload)
npm run backend:dev

# Build for production
npm run backend:build

# Run Tauri without rebuilding backend
npm run tauri:dev:quick
```

### Environment Variables

Settings are stored in encrypted SQLite database (`settings_manager.py`).
On startup, settings are loaded into `os.environ`.

Required settings:

- `GEMINI_API_KEY` - Google Gemini API key
- `SMTP_SERVER` - Email server (e.g., smtp.gmail.com)
- `SMTP_PORT` - SMTP port (e.g., 587)
- `SMTP_USERNAME` - Email username
- `SMTP_PASSWORD` - Email password

### Inline Mode Flow

1. User presses `Cmd+Shift+K` in a text field
2. Backend detects text field (terminal, browser input, etc.)
3. Keystroke capture activates
4. User types query (e.g., "grep command for rust files")
5. User presses `Cmd+Shift+K` again
6. Backend:
   - Joins captured keystrokes
   - Backspaces the query (+ 2 for the 'K' keys)
   - Types "Thinking..." with animated dots
   - Calls AI agent
   - Backspaces "Thinking..."
   - Types AI response

### Normal Mode Flow

1. User selects text
2. User presses `Cmd+Shift+K`
3. Backend copies selection with `Cmd+C`
4. Overlay shows with selected text
5. User types message
6. Backend sends to AI agent
7. AI processes and responds (e.g., sends email)

## AI Model

All agents use `gemini-2.5-flash` for fast, cost-effective responses.

## Build & Deployment

PyInstaller bundles Python backend into standalone binary:

- `build/pointer-backend/` - Build artifacts
- `src-tauri/binaries/` - Final binary for Tauri

## Testing

- `test_email_flow.py` - End-to-end email testing
- Run backend in dev mode for instant testing: `npm run backend:dev`

## Notes

- Clipboard only used in normal mode (selected text)
- Inline mode uses pure keystroke capture
- Terminal apps detected by name (ghostty, iTerm, Terminal, etc.)
- Email prompts intentionally vague for natural AI output
- Settings UI shows only Environment Variables tab
