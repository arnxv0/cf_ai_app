try:
    from Cocoa import NSCursor, NSImage, NSColor, NSApp, NSEvent
    from Quartz import (
        CGColorSpaceCreateDeviceRGB,
        CGDataProviderCreateWithData,
        CGImageCreate,
        kCGImageAlphaPremultipliedLast,
        kCGBitmapByteOrder32Big,
        CGDisplayHideCursor,
        CGDisplayShowCursor,
        CGAssociateMouseAndMouseCursorPosition,
        CGWarpMouseCursorPosition
    )
    from AppKit import NSScreen
    import Quartz.CoreGraphics as CG
except ImportError:
    print("Warning: PyObjC not available. Custom cursor will not work.")
    NSCursor = None
    NSImage = None
    NSColor = None
    NSApp = None
    NSEvent = None
    NSScreen = None
    CG = None

import os
import sys
import threading
import time
from typing import Tuple, Optional


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    In development: Uses the project directory.
    In PyInstaller bundle: Uses the bundled resources or falls back to programmatic cursors.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        resource_path = os.path.join(base_path, relative_path)
        
        # If file exists in bundle, use it
        if os.path.exists(resource_path):
            return resource_path
            
        # Otherwise, we'll create programmatic cursor (SVG not bundled)
        return None
    except AttributeError:
        # Not running in PyInstaller bundle - development mode
        # Get the project root (go up from src-python to project root)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resource_path = os.path.join(base_path, relative_path)
        
        if os.path.exists(resource_path):
            return resource_path
        return None


class CursorManager:
    """Manages system cursor appearance with customizable styles."""
    
    # Built-in cursor styles
    CURSOR_STYLES = {
        "default": {
            "name": "System Default",
            "description": "macOS standard arrow cursor"
        },
        "pointer": {
            "name": "Pointer",
            "description": "Custom pointer design",
            "file": "public/cursors/pointer.svg",
            "fallback": "circle"  # If SVG not found, use programmatic circle
        },
        "circle": {
            "name": "Circle",
            "description": "Simple circle cursor",
            "size": 24,
            "color": (0, 0, 0, 1.0)
        },
        "dot": {
            "name": "Dot",
            "description": "Minimal dot cursor",
            "size": 8,
            "color": (0, 0, 0, 1.0)
        },
        "crosshair": {
            "name": "Crosshair",
            "description": "Precision crosshair",
            "size": 20,
            "color": (0, 0, 0, 0.8)
        }
    }
    
    def __init__(self):
        self.custom_cursor = None
        self.current_style = "default"
        self.current_color = (0, 0, 0, 1.0)  # RGBA
        self.current_size = 24
        print("⚠️  Note: Cursor changes from Python backend won't persist system-wide.")
        print("   Cursor customization should be handled by the Tauri frontend app.")
    
    def set_custom_cursor(
        self, 
        style: str = "pointer",
        color: Optional[Tuple[float, float, float, float]] = None,
        size: Optional[int] = None,
        svg_path: Optional[str] = None
    ):
        """
        Set a custom cursor with the specified style.
        
        Args:
            style: Cursor style name (default, pointer, circle, dot, crosshair)
            color: RGBA color tuple (0-1 range)
            size: Cursor size in pixels
            svg_path: Optional custom SVG file path
        """
        if NSCursor is None or NSImage is None:
            print("Custom cursor not available without PyObjC")
            return False
        
        try:
            print(f"🖱️  Setting cursor: style={style}, color={color}, size={size}")
            
            # Pop any existing custom cursor from stack
            if self.custom_cursor:
                try:
                    NSCursor.pop()
                except:
                    pass
            
            self.current_style = style
            
            if style == "default":
                self.reset_cursor()
                return True
            
            # Use provided values or defaults from style
            style_config = self.CURSOR_STYLES.get(style, {})
            self.current_color = color or style_config.get("color", (0, 0, 0, 1.0))
            self.current_size = size or style_config.get("size", 24)
            
            # Try SVG file first if specified in config or provided
            if svg_path or "file" in style_config:
                svg_file = svg_path or style_config.get("file")
                if self._set_cursor_from_svg(svg_file):
                    return True
                else:
                    print(f"⚠️  SVG not available, falling back to programmatic cursor")
                    # Use fallback style if specified
                    fallback = style_config.get("fallback")
                    if fallback and fallback != style:
                        return self.set_custom_cursor(fallback, color, size)
            
            # Generate programmatic cursor based on style
            success = False
            if style == "circle" or style == "pointer":
                success = self._create_circle_cursor(self.current_size, self.current_color)
            elif style == "dot":
                success = self._create_dot_cursor(self.current_size, self.current_color)
            elif style == "crosshair":
                success = self._create_crosshair_cursor(self.current_size, self.current_color)
            else:
                print(f"Unknown cursor style: {style}, using circle")
                success = self._create_circle_cursor(self.current_size, self.current_color)
            
            return success
        
        except Exception as e:
            print(f"Error setting custom cursor: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _set_cursor_from_svg(self, svg_path: str) -> bool:
        """Load cursor from SVG file."""
        try:
            # Resolve the actual path
            resolved_path = get_resource_path(svg_path)
            
            if resolved_path and os.path.exists(resolved_path):
                image = NSImage.alloc().initWithContentsOfFile_(resolved_path)
                
                if image:
                    # Set hotspot to center
                    size = image.size()
                    hotspot = (size.width / 2, size.height / 2)
                    
                    cursor = NSCursor.alloc().initWithImage_hotSpot_(image, hotspot)
                    
                    # Push cursor onto cursor stack (makes it persistent)
                    cursor.push()
                    self.custom_cursor = cursor
                    
                    print(f"✅ Custom cursor set from SVG: {resolved_path}")
                    return True
                else:
                    print("❌ Failed to load cursor image")
                    return False
            else:
                print(f"⚠️  SVG cursor not available, using programmatic cursor instead")
                return False
        except Exception as e:
            print(f"Error loading SVG cursor: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_circle_cursor(self, size: int, color: Tuple[float, float, float, float]) -> bool:
        """Create a circular cursor programmatically."""
        try:
            print(f"🎨 Creating circle cursor: size={size}, color={color}")
            image = NSImage.alloc().initWithSize_((size, size))
            image.lockFocus()
            
            # Draw circle
            ns_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                color[0], color[1], color[2], color[3]
            )
            ns_color.set()
            
            from Cocoa import NSBezierPath
            circle = NSBezierPath.bezierPathWithOvalInRect_(((0, 0), (size, size)))
            circle.fill()
            
            # Add white border for visibility
            NSColor.whiteColor().set()
            circle.setLineWidth_(2)
            circle.stroke()
            
            image.unlockFocus()
            
            hotspot = (size / 2, size / 2)
            cursor = NSCursor.alloc().initWithImage_hotSpot_(image, hotspot)
            
            # Push cursor onto cursor stack (makes it persistent)
            cursor.push()
            self.custom_cursor = cursor
            
            print(f"✅ Circle cursor created and applied (size: {size})")
            return True
        except Exception as e:
            print(f"❌ Error creating circle cursor: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_dot_cursor(self, size: int, color: Tuple[float, float, float, float]) -> bool:
        """Create a minimal dot cursor."""
        try:
            canvas_size = max(size * 3, 24)  # Larger canvas for visibility
            image = NSImage.alloc().initWithSize_((canvas_size, canvas_size))
            image.lockFocus()
            
            # Draw dot in center
            ns_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                color[0], color[1], color[2], color[3]
            )
            ns_color.set()
            
            from Cocoa import NSBezierPath
            offset = (canvas_size - size) / 2
            dot = NSBezierPath.bezierPathWithOvalInRect_(((offset, offset), (size, size)))
            dot.fill()
            
            # White border
            NSColor.whiteColor().set()
            dot.setLineWidth_(1)
            dot.stroke()
            
            image.unlockFocus()
            
            hotspot = (canvas_size / 2, canvas_size / 2)
            cursor = NSCursor.alloc().initWithImage_hotSpot_(image, hotspot)
            
            # Push cursor onto cursor stack
            cursor.push()
            self.custom_cursor = cursor
            
            print(f"✅ Dot cursor created (size: {size})")
            return True
        except Exception as e:
            print(f"Error creating dot cursor: {e}")
            return False
    
    def _create_crosshair_cursor(self, size: int, color: Tuple[float, float, float, float]) -> bool:
        """Create a crosshair cursor."""
        try:
            image = NSImage.alloc().initWithSize_((size, size))
            image.lockFocus()
            
            ns_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                color[0], color[1], color[2], color[3]
            )
            ns_color.set()
            
            from Cocoa import NSBezierPath
            center = size / 2
            line_length = size / 2 - 2
            
            # Vertical line
            v_line = NSBezierPath.bezierPath()
            v_line.moveToPoint_((center, center - line_length))
            v_line.lineToPoint_((center, center + line_length))
            v_line.setLineWidth_(2)
            v_line.stroke()
            
            # Horizontal line
            h_line = NSBezierPath.bezierPath()
            h_line.moveToPoint_((center - line_length, center))
            h_line.lineToPoint_((center + line_length, center))
            h_line.setLineWidth_(2)
            h_line.stroke()
            
            # Center dot
            dot = NSBezierPath.bezierPathWithOvalInRect_(
                ((center - 2, center - 2), (4, 4))
            )
            dot.fill()
            
            image.unlockFocus()
            
            hotspot = (center, center)
            cursor = NSCursor.alloc().initWithImage_hotSpot_(image, hotspot)
            
            # Push cursor onto cursor stack
            cursor.push()
            self.custom_cursor = cursor
            
            print(f"✅ Crosshair cursor created (size: {size})")
            return True
        except Exception as e:
            print(f"Error creating crosshair cursor: {e}")
            return False
    
    def get_available_styles(self):
        """Get list of available cursor styles."""
        return {
            style: {
                "name": config.get("name", style),
                "description": config.get("description", "")
            }
            for style, config in self.CURSOR_STYLES.items()
        }
    
    def reset_cursor(self):
        """Reset to system default cursor."""
        if self.custom_cursor:
            try:
                NSCursor.pop()
            except:
                pass
        
        if NSCursor:
            NSCursor.arrowCursor().set()
            self.current_style = "default"
            self.custom_cursor = None
            print("✅ Reset to default cursor")
