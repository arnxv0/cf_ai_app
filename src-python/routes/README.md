# API Routes

This directory contains all FastAPI route definitions organized by functionality.

## Structure

```
routes/
├── __init__.py          # Routes module
├── health.py            # Health check and status endpoints
├── settings.py          # Settings management (CRUD)
├── hotkey.py            # Hotkey configuration
├── rag.py               # RAG/Knowledge base operations
└── agent.py             # AI agent processing
```

## Route Files

### `health.py`

- `GET /` - Root endpoint with API info
- `GET /health` - Health check endpoint

### `settings.py`

- `GET /api/settings/categories` - List all setting categories
- `GET /api/settings/{category}` - Get all settings in a category
- `GET /api/settings/{category}/{key}` - Get specific setting
- `POST /api/settings` - Create/update a setting
- `DELETE /api/settings/{category}/{key}` - Delete a setting
- `POST /api/settings/import` - Import settings from .env format
- `GET /api/settings/export/{category}` - Export settings as .env

### `hotkey.py`

- `GET /api/hotkey/current` - Get current hotkey configuration
- `POST /api/hotkey/set` - Set new hotkey and update keyboard monitor
- `POST /api/hotkey/reset` - Reset to default hotkey (Cmd+Shift+K)

### `rag.py`

- `GET /api/rag/stats` - Get knowledge base statistics
- `POST /api/rag/add` - Add document to knowledge base
- `POST /api/rag/upload` - Upload file to knowledge base
- `POST /api/rag/query` - Search the knowledge base
- `GET /api/rag/documents` - List all documents
- `DELETE /api/rag/documents/{doc_id}` - Delete a document
- `DELETE /api/rag/clear` - Clear entire knowledge base

### `agent.py`

- `POST /api/agent` - Process message through AI agent
- `POST /api/process-query` - Legacy endpoint (converts to /api/agent format)

## Usage

All routes are automatically included in `main.py`:

```python
from routes import health, settings, hotkey, rag, agent

app.include_router(health.router)
app.include_router(settings.router)
app.include_router(hotkey.router)
app.include_router(rag.router)
app.include_router(agent.router)
```

## Adding New Routes

1. Create a new file in `routes/` (e.g., `calendar.py`)
2. Define your router with prefix and tags:

   ```python
   from fastapi import APIRouter

   router = APIRouter(prefix="/api/calendar", tags=["calendar"])

   @router.get("/events")
   async def list_events():
       return {"events": []}
   ```

3. Import and include in `main.py`:
   ```python
   from routes import calendar
   app.include_router(calendar.router)
   ```

## Benefits of This Structure

- ✅ **Separation of Concerns**: Each route file handles one domain
- ✅ **Maintainability**: Easy to find and update specific functionality
- ✅ **Scalability**: Add new features without cluttering main.py
- ✅ **Testing**: Routes can be tested independently
- ✅ **Documentation**: Auto-generated OpenAPI docs grouped by tags
