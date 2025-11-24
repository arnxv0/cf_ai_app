# Runtime hook to force eager loading of Quartz functions
# This prevents PyObjC's lazy loading issues with PyInstaller

import sys
import os

# Disable PyObjC lazy loading
os.environ['PYOBJC_DISABLE_LAZY_IMPORT'] = '1'

# Force import and load all Quartz functions that pynput needs
try:
    import Quartz
    import warnings
    
    # Suppress deprecation warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    
    # Pre-load all functions that pynput.keyboard uses
    _ = Quartz.CGEventGetIntegerValueField
    _ = Quartz.CGEventGetFlags  
    _ = Quartz.CGEventGetType
    _ = Quartz.CGEventKeyboardGetUnicodeString
    _ = Quartz.CGEventCreateKeyboardEvent
    _ = Quartz.CGEventPost
    _ = Quartz.kCGEventKeyDown
    _ = Quartz.kCGEventKeyUp
    _ = Quartz.kCGHIDEventTap
    _ = Quartz.kCGSessionEventTap
    _ = Quartz.kCGHeadInsertEventTap
    _ = Quartz.CGEventTapCreate
    _ = Quartz.CGEventTapEnable
    _ = Quartz.CFMachPortCreateRunLoopSource
    _ = Quartz.CFRunLoopGetCurrent
    _ = Quartz.CFRunLoopAddSource
    _ = Quartz.kCFRunLoopCommonModes
    
    # Pre-load all functions that pynput.mouse uses
    _ = Quartz.CGDisplayPixelsHigh
    _ = Quartz.CGDisplayPixelsWide
    _ = Quartz.CGEventCreateMouseEvent
    _ = Quartz.CGEventSetType
    _ = Quartz.CGEventSetIntegerValueField
    _ = Quartz.kCGMouseEventNumber
    _ = Quartz.kCGMouseEventClickState
    _ = Quartz.kCGMouseButtonLeft
    _ = Quartz.kCGMouseButtonRight
    _ = Quartz.kCGMouseButtonCenter
    _ = Quartz.kCGEventLeftMouseDown
    _ = Quartz.kCGEventLeftMouseUp
    _ = Quartz.kCGEventRightMouseDown
    _ = Quartz.kCGEventRightMouseUp
    _ = Quartz.kCGEventOtherMouseDown
    _ = Quartz.kCGEventOtherMouseUp
    _ = Quartz.kCGEventMouseMoved
    _ = Quartz.kCGEventLeftMouseDragged
    _ = Quartz.kCGEventRightMouseDragged
    _ = Quartz.kCGEventScrollWheel
    _ = Quartz.kCGScrollWheelEventDeltaAxis1
    _ = Quartz.kCGScrollWheelEventDeltaAxis2
    _ = Quartz.CGEventSourceCreate
    _ = Quartz.kCGEventSourceStateHIDSystemState
    _ = Quartz.CGWarpMouseCursorPosition
    _ = Quartz.CGAssociateMouseAndMouseCursorPosition
    _ = Quartz.CGMainDisplayID
    _ = Quartz.CGEventGetLocation
    
    print("✅ Quartz functions pre-loaded successfully")
except Exception as e:
    print(f"⚠️  Warning: Could not pre-load Quartz functions: {e}")
