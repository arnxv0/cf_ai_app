from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import os
from pathlib import Path

logger = logging.getLogger("pointer.routes.storage")

router = APIRouter(prefix="/api/storage", tags=["storage"])


def _get_data_dir() -> Path:
    """Get the application data directory."""
    if os.name == 'nt':  # Windows
        data_dir = Path(os.environ.get('APPDATA', Path.home())) / 'Pointer'
    elif os.name == 'posix':  # macOS/Linux
        if 'darwin' in os.sys.platform:  # macOS
            data_dir = Path.home() / 'Library' / 'Application Support' / 'Pointer'
        else:  # Linux
            data_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share')) / 'Pointer'
    else:
        data_dir = Path.home() / '.pointer'
    
    return data_dir


def _get_file_size(file_path: Path) -> str:
    """Get human-readable file size."""
    try:
        if file_path.exists():
            size_bytes = file_path.stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        return "0 B"
    except Exception:
        return "Unknown"


def _get_dir_size(dir_path: Path) -> str:
    """Get human-readable directory size."""
    try:
        if dir_path.exists() and dir_path.is_dir():
            total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
            size_bytes = total_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        return "0 B"
    except Exception:
        return "Unknown"


@router.get("/paths")
async def get_storage_paths():
    """Get all storage locations used by the application."""
    try:
        data_dir = _get_data_dir()
        
        # Get settings database path
        try:
            from utils.settings_manager import get_settings_manager
            settings_mgr = get_settings_manager()
            settings_db_path = Path(settings_mgr.db_path)
        except Exception:
            settings_db_path = data_dir / "settings.db"
        
        # Get knowledge base path
        try:
            from tools.rag import get_store
            store = get_store()
            kb_db_path = Path(store.db_path)
        except Exception:
            kb_db_path = data_dir / "knowledge_base.db"
        
        locations = [
            {
                "id": "knowledge_base",
                "title": "Knowledge Base Database",
                "path": str(kb_db_path),
                "description": "SQLite database containing RAG documents and embeddings",
                "icon": "storage",
                "exists": kb_db_path.exists(),
                "size": _get_file_size(kb_db_path) if kb_db_path.exists() else "0 B"
            },
            {
                "id": "settings",
                "title": "Settings Database",
                "path": str(settings_db_path),
                "description": "Encrypted settings and environment variables",
                "icon": "settings",
                "exists": settings_db_path.exists(),
                "size": _get_file_size(settings_db_path) if settings_db_path.exists() else "0 B"
            },
            {
                "id": "data_dir",
                "title": "Application Data Directory",
                "path": str(data_dir),
                "description": "Main directory containing all Pointer data",
                "icon": "folder",
                "exists": data_dir.exists(),
                "size": _get_dir_size(data_dir) if data_dir.exists() else "0 B"
            },
        ]
        
        # Add logs directory if it exists
        logs_dir = data_dir / "logs"
        if logs_dir.exists():
            locations.append({
                "id": "logs",
                "title": "Application Logs",
                "path": str(logs_dir),
                "description": "Backend and application log files",
                "icon": "description",
                "exists": True,
                "size": _get_dir_size(logs_dir)
            })
        
        return {
            "success": True,
            "locations": locations,
            "data_directory": str(data_dir)
        }
    except Exception as e:
        logger.error(f"Error getting storage paths: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_storage_stats():
    """Get overall storage statistics."""
    try:
        data_dir = _get_data_dir()
        
        total_size = _get_dir_size(data_dir)
        
        # Count files
        file_count = 0
        if data_dir.exists():
            file_count = sum(1 for _ in data_dir.rglob('*') if _.is_file())
        
        return {
            "success": True,
            "total_size": total_size,
            "total_files": file_count,
            "data_directory": str(data_dir)
        }
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
