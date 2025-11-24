from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger("arrow.routes.settings")

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingRequest(BaseModel):
    category: str
    key: str
    value: Any
    is_secret: bool = False
    description: Optional[str] = None


@router.get("/categories")
async def get_settings_categories():
    """Get list of all setting categories."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        categories = settings_mgr.get_all_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}")
async def get_category_settings(category: str, include_secrets: bool = False):
    """Get all settings in a category."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        settings = settings_mgr.get_category(category, include_secrets=include_secrets)
        return {"category": category, "settings": settings}
    except Exception as e:
        logger.error(f"Error getting category {category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}/{key}")
async def get_setting(category: str, key: str):
    """Get a specific setting with metadata."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        value = settings_mgr.get(category, key, decrypt=True)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Setting {category}.{key} not found")
        
        # Get metadata
        metadata = settings_mgr.get_setting_info(category, key)
        
        return {
            "category": category,
            "key": key,
            "value": value,
            "metadata": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting setting {category}.{key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def set_setting(request: SettingRequest):
    """Store a setting."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()

        settings_mgr.set(
            request.category,
            request.key,
            request.value,
            is_secret=request.is_secret,
            description=request.description
        )

        # Reload Tadata if TADATA_API_KEY or TADATA_CONNECTORS changed
        if request.key in ["TADATA_API_KEY", "TADATA_CONNECTORS", "TADATA_NOTION_URL", "TADATA_EXA_URL", "TADATA_SUPABASE_URL"]:
            from tools.tadata import reload_tadata_integration
            logger.info(f"🔄 Triggering Tadata reload after {request.key} update")
            reload_tadata_integration()

        return {
            "success": True,
            "category": request.category,
            "key": request.key
        }
    except Exception as e:
        logger.error(f"Error setting {request.category}.{request.key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{category}/{key}")
async def delete_setting(category: str, key: str):
    """Delete a setting."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        settings_mgr.delete(category, key)
        return {
            "success": True,
            "category": category,
            "key": key
        }
    except Exception as e:
        logger.error(f"Error deleting {category}.{key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_settings(request: dict):
    """Import settings from .env format."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        env_text = request.get("env_text", "")
        category = request.get("category", "env")
        
        count = settings_mgr.import_from_env(env_text, category=category)
        
        return {
            "success": True,
            "imported_count": count
        }
    except Exception as e:
        logger.error(f"Error importing settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{category}")
async def export_settings(category: str):
    """Export settings as .env format."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        env_text = settings_mgr.export_to_env(category)
        
        return {
            "category": category,
            "env_text": env_text
        }
    except Exception as e:
        logger.error(f"Error exporting category {category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
