import pyperclip

try:
    from Cocoa import NSPasteboard, NSImage
    from AppKit import NSBitmapImageRep, NSTIFFFileType
except ImportError:
    NSPasteboard = None
    NSImage = None


class ClipboardManager:
    def copy(self, text: str):
        pyperclip.copy(text)
    
    def paste(self) -> str:
        return pyperclip.paste()
    
    def has_image(self) -> bool:
        """Check if clipboard has an image"""
        print("🖼️  [ClipboardManager] Checking if has image...", flush=True)
        if NSPasteboard is None:
            print("🖼️  [ClipboardManager] NSPasteboard is None", flush=True)
            return False
        
        try:
            print("🖼️  [ClipboardManager] Getting general pasteboard...", flush=True)
            pasteboard = NSPasteboard.generalPasteboard()
            print("🖼️  [ClipboardManager] Getting types...", flush=True)
            types = pasteboard.types()
            print(f"🖼️  [ClipboardManager] Types: {types}", flush=True)
            result = types.containsObject_("public.tiff") or types.containsObject_("public.png")
            print(f"🖼️  [ClipboardManager] Has image: {result}", flush=True)
            return result
        except Exception as e:
            print(f"🖼️  [ClipboardManager] Error checking image: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False
    
    def copy_image(self, image):
        """Copy PIL Image to clipboard"""
        if NSPasteboard is None:
            print("Image clipboard not available")
            return
        
        try:
            import io
            buf = io.BytesIO()
            image.save(buf, format='PNG')
            buf.seek(0)
            
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            
            ns_image = NSImage.alloc().initWithData_(buf.read())
            pasteboard.writeObjects_([ns_image])
        except Exception as e:
            print(f"Error copying image: {e}")
    
    def get_image(self):
        if NSPasteboard is None:
            return None
        
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            
            if pasteboard.types().containsObject_("public.tiff"):
                image_data = pasteboard.dataForType_("public.tiff")
                if image_data:
                    return NSImage.alloc().initWithData_(image_data)
        except Exception as e:
            print(f"Error getting image from clipboard: {e}")
        
        return None
