from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger("pointer.routes.hotkey")

router = APIRouter(prefix="/api/hotkey", tags=["hotkey"])

# Will be set by main.py
keyboard_monitor = None


class HotkeyConfigFull(BaseModel):
    modifiers: List[str]
    key: str
    inline_modifiers: List[str]
    inline_key: str


class HotkeyConfig(BaseModel):
    keys: List[str]
    description: Optional[str] = None


@router.get("")
async def get_hotkey():
    """Get both popup and inline hotkey configurations."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        hotkey_settings = settings_mgr.get_category("hotkey", include_secrets=False)
        
        # Default values
        popup_modifiers = hotkey_settings.get("modifiers", ["cmd", "shift"]) if hotkey_settings else ["cmd", "shift"]
        popup_key = hotkey_settings.get("key", "k") if hotkey_settings else "k"
        inline_modifiers = hotkey_settings.get("inline_modifiers", ["cmd", "shift"]) if hotkey_settings else ["cmd", "shift"]
        inline_key = hotkey_settings.get("inline_key", "l") if hotkey_settings else "l"
        
        return {
            "modifiers": popup_modifiers,
            "key": popup_key,
            "inline_modifiers": inline_modifiers,
            "inline_key": inline_key
        }
    except Exception as e:
        logger.error(f"Error getting hotkeys: {e}")
        return {
            "modifiers": ["cmd", "shift"],
            "key": "k",
            "inline_modifiers": ["cmd", "shift"],
            "inline_key": "l"
        }

@router.post("")
async def set_hotkeys(config: HotkeyConfigFull):
    """Set both popup and inline hotkey configurations."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        # Validate
        if not config.modifiers or len(config.modifiers) < 1:
            raise HTTPException(status_code=400, detail="At least one modifier is required for popup hotkey")
        if not config.inline_modifiers or len(config.inline_modifiers) < 1:
            raise HTTPException(status_code=400, detail="At least one modifier is required for inline hotkey")
        if not config.key or len(config.key) != 1:
            raise HTTPException(status_code=400, detail="Popup key must be a single character")
        if not config.inline_key or len(config.inline_key) != 1:
            raise HTTPException(status_code=400, detail="Inline key must be a single character")
        
        # Save to database
        settings_mgr.set("hotkey", "modifiers", config.modifiers, is_secret=False, 
                        description="Popup mode hotkey modifiers")
        settings_mgr.set("hotkey", "key", config.key, is_secret=False, 
                        description="Popup mode hotkey key")
        settings_mgr.set("hotkey", "inline_modifiers", config.inline_modifiers, is_secret=False, 
                        description="Inline mode hotkey modifiers")
        settings_mgr.set("hotkey", "inline_key", config.inline_key, is_secret=False, 
                        description="Inline mode hotkey key")
        
        # Update the keyboard monitor
        if keyboard_monitor:
            popup_config = {"modifiers": config.modifiers, "key": config.key}
            inline_config = {"modifiers": config.inline_modifiers, "key": config.inline_key}
            success = keyboard_monitor.update_hotkey(popup_config, inline_config)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update keyboard monitor")
        
        return {
            "success": True,
            "modifiers": config.modifiers,
            "key": config.key,
            "inline_modifiers": config.inline_modifiers,
            "inline_key": config.inline_key,
            "message": "Hotkeys updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting hotkeys: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_hotkeys():
    """Reset both hotkeys to defaults (Popup: Cmd+Shift+K, Inline: Cmd+Shift+L)."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        default_popup_modifiers = ["cmd", "shift"]
        default_popup_key = "k"
        default_inline_modifiers = ["cmd", "shift"]
        default_inline_key = "l"
        
        # Save to database
        settings_mgr.set("hotkey", "modifiers", default_popup_modifiers, is_secret=False)
        settings_mgr.set("hotkey", "key", default_popup_key, is_secret=False)
        settings_mgr.set("hotkey", "inline_modifiers", default_inline_modifiers, is_secret=False)
        settings_mgr.set("hotkey", "inline_key", default_inline_key, is_secret=False)
        
        # Update the keyboard monitor
        if keyboard_monitor:
            popup_config = {"modifiers": default_popup_modifiers, "key": default_popup_key}
            inline_config = {"modifiers": default_inline_modifiers, "key": default_inline_key}
            keyboard_monitor.update_hotkey(popup_config, inline_config)
        
        return {
            "success": True,
            "hotkey": {
                "modifiers": default_popup_modifiers,
                "key": default_popup_key,
                "inline_modifiers": default_inline_modifiers,
                "inline_key": default_inline_key
            },
            "message": "Hotkeys reset to defaults"
        }
    except Exception as e:
        logger.error(f"Error resetting hotkeys: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
