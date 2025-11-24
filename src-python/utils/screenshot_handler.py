from PIL import Image
import io

try:
    from Cocoa import NSPasteboard
except ImportError:
    NSPasteboard = None


class ScreenshotHandler:
    def get_from_clipboard(self):
        if NSPasteboard is None:
            return None
        
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            
            if pasteboard.types().containsObject_("public.tiff"):
                image_data = pasteboard.dataForType_("public.tiff")
                
                if image_data:
                    img = Image.open(io.BytesIO(image_data.bytes()))
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    return buf.getvalue()
        except Exception as e:
            print(f"Error getting screenshot: {e}")
        
        return None
