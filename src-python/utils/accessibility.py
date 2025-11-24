try:
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
        AXUIElementCopyAttributeValue,
    )
    from Cocoa import NSWorkspace, NSPasteboard
except ImportError:
    print("Warning: PyObjC not available")

from pynput.keyboard import Controller, Key
import time


class AccessibilityManager:
    def __init__(self):
        self.keyboard = Controller()
    
    def get_selected_text(self) -> str:
        try:
            return self._get_text_via_clipboard()
        except Exception as e:
            print(f"Error getting selected text: {e}")
            return ""
    
    def _get_text_via_clipboard(self) -> str:
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            old_contents = pasteboard.stringForType_("public.utf8-plain-text")
            
            self.keyboard.press(Key.cmd)
            self.keyboard.press('c')
            self.keyboard.release('c')
            self.keyboard.release(Key.cmd)
            
            time.sleep(0.1)
            
            new_contents = pasteboard.stringForType_("public.utf8-plain-text")
            
            if old_contents:
                pasteboard.clearContents()
                pasteboard.setString_forType_(old_contents, "public.utf8-plain-text")
            
            return new_contents or ""
        except Exception as e:
            print(f"Clipboard error: {e}")
            return ""
    
    async def replace_with_text(self, new_text: str, chars_to_delete: int):
        for _ in range(chars_to_delete):
            self.keyboard.press(Key.backspace)
            self.keyboard.release(Key.backspace)
            time.sleep(0.01)
        
        self.type_text(new_text)
    
    def type_text(self, text: str):
        for char in text:
            self.keyboard.type(char)
            time.sleep(0.02)
    
    def paste(self):
        """Trigger paste command"""
        self.keyboard.press(Key.cmd)
        self.keyboard.press('v')
        self.keyboard.release('v')
        self.keyboard.release(Key.cmd)
