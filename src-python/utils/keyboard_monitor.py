from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Controller as MouseController
import threading
import time
import asyncio


class KeyboardMonitor:
    def __init__(self, connection_manager=None, hotkey_config=None, inline_hotkey_config=None):
        self.listener = None
        self.hotkey_callback = None
        self.current_keys = set()
        
        # Parse POPUP hotkey from config or use default
        if hotkey_config:
            self.popup_hotkey = self._parse_hotkey_config(hotkey_config)
        else:
            self.popup_hotkey = {Key.cmd, Key.shift, KeyCode.from_char('k')}
        
        # Parse INLINE hotkey from config or use default  
        if inline_hotkey_config:
            self.inline_hotkey = self._parse_hotkey_config(inline_hotkey_config)
        else:
            self.inline_hotkey = {Key.cmd, Key.shift, KeyCode.from_char('l')}
        
        self.mouse = MouseController()
        self.connection_manager = connection_manager
        self.popup_hotkey_active = False  # Debounce flag for popup hotkey
        self.inline_hotkey_active = False  # Debounce flag for inline hotkey
        self.last_trigger_time = 0  # Track last trigger time for cooldown
        self.cooldown_seconds = 0.5  # Reduced cooldown for inline mode
        
        # Inline mode state
        self.inline_mode_active = False
        self.captured_keystrokes = []  # Store captured keystrokes
        self.keyboard_controller = None  # Will be initialized when needed
    
    def _parse_hotkey_config(self, config):
        """
        Parse hotkey configuration into a set of keys.
        Config format: {"modifiers": ["cmd", "shift"], "key": "k"}
        """
        hotkey_set = set()
        
        # Add modifiers
        modifier_map = {
            "cmd": Key.cmd,
            "ctrl": Key.ctrl,
            "alt": Key.alt,
            "shift": Key.shift,
        }
        
        for modifier in config.get("modifiers", []):
            if modifier.lower() in modifier_map:
                hotkey_set.add(modifier_map[modifier.lower()])
        
        # Add main key
        key = config.get("key", "k")
        if len(key) == 1:
            hotkey_set.add(KeyCode.from_char(key.lower()))
        
        return hotkey_set
    
    def update_hotkey(self, hotkey_config, inline_hotkey_config=None):
        """
        Update the hotkey configuration dynamically.
        Config format: {"modifiers": ["cmd", "shift"], "key": "k"}
        """
        new_popup_hotkey = self._parse_hotkey_config(hotkey_config)
        self.popup_hotkey = new_popup_hotkey
        print(f"🔄 Popup hotkey updated to: {hotkey_config}")
        
        if inline_hotkey_config:
            new_inline_hotkey = self._parse_hotkey_config(inline_hotkey_config)
            self.inline_hotkey = new_inline_hotkey
            print(f"🔄 Inline hotkey updated to: {inline_hotkey_config}")
        
        return True
    
    def start(self):
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False  # Don't suppress keys so they reach the system
        )
        self.listener.start()
        print("⌨️  Keyboard monitor started")
    
    def stop(self):
        if self.listener:
            self.listener.stop()
    
    def _on_press(self, key):
        try:
            self.current_keys.add(key)
            
            # Check which hotkey combo is being pressed
            is_popup_hotkey = self.current_keys >= self.popup_hotkey
            is_inline_hotkey = self.current_keys >= self.inline_hotkey
            
            # If in inline mode, capture keystrokes (but not when any hotkey is pressed)
            if self.inline_mode_active and not is_inline_hotkey and not is_popup_hotkey:
                # Capture the keystroke
                if hasattr(key, 'char') and key.char:
                    self.captured_keystrokes.append(key.char)
                elif key == Key.space:
                    self.captured_keystrokes.append(' ')
                elif key == Key.backspace and len(self.captured_keystrokes) > 0:
                    self.captured_keystrokes.pop()
                elif key == Key.enter:
                    self.captured_keystrokes.append('\n')
            
            current_time = time.time()
            time_since_last_trigger = current_time - self.last_trigger_time
            
            # Check POPUP hotkey
            if is_popup_hotkey and not self.popup_hotkey_active:
                if time_since_last_trigger >= self.cooldown_seconds:
                    self.popup_hotkey_active = True
                    self.last_trigger_time = current_time
                    self._trigger_popup_mode()
                else:
                    print(f"⏳ Popup hotkey cooldown active ({self.cooldown_seconds - time_since_last_trigger:.1f}s remaining)", flush=True)
            
            # Check INLINE hotkey
            elif is_inline_hotkey and not self.inline_hotkey_active:
                if time_since_last_trigger >= self.cooldown_seconds:
                    self.inline_hotkey_active = True
                    self.last_trigger_time = current_time
                    self._trigger_inline_mode()
                else:
                    print(f"⏳ Inline hotkey cooldown active ({self.cooldown_seconds - time_since_last_trigger:.1f}s remaining)", flush=True)
                    
        except Exception as e:
            print(f"❌ Error in _on_press: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    def _on_release(self, key):
        if key in self.current_keys:
            self.current_keys.remove(key)
        # Reset hotkey_active flags when respective keys are released
        if key in self.popup_hotkey:
            self.popup_hotkey_active = False
        if key in self.inline_hotkey:
            self.inline_hotkey_active = False
    
    def _trigger_popup_mode(self):
        """Trigger POPUP mode hotkey - shows overlay window"""
        try:
            print("\n" + "="*60, flush=True)
            print("🔥 POPUP MODE TRIGGERED!", flush=True)
            print("="*60, flush=True)
            
            # Get mouse position
            print("📍 Getting mouse position...", flush=True)
            mouse_pos = self.mouse.position
            print(f"📍 Mouse position: {mouse_pos}", flush=True)
            
            # Check if focused element is a text input
            print("🔍 Checking focused element...", flush=True)
            is_text_field = False
            focused_element_info = ""
            try:
                import subprocess
                # Use AppleScript to check if focused element is a text field
                script = '''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    tell process frontApp
                        try
                            set focusedElement to focused
                            set elementRole to role of focusedElement
                            set elementDescription to description of focusedElement
                            return elementRole & "|" & elementDescription & "|" & frontApp
                        on error
                            return "none|none|" & frontApp
                        end try
                    end tell
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=1)
                element_info = result.stdout.strip().split('|')
                if len(element_info) >= 3:
                    role = element_info[0]
                    description = element_info[1]
                    app_name = element_info[2]
                    focused_element_info = f"Role: {role}, Description: {description}, App: {app_name}"
                    # Check if it's a text input field OR a terminal app
                    is_text_field = (
                        role in ['AXTextField', 'AXTextArea', 'AXComboBox', 'text field', 'text area'] or
                        app_name in ['Terminal', 'iTerm', 'iTerm2', 'ghostty', 'Alacritty', 'kitty', 'Warp']
                    )
                    print(f"🔍 Focused element: {focused_element_info}", flush=True)
                    print(f"📝 Is text field: {is_text_field}", flush=True)
            except Exception as e:
                print(f"⚠️  Could not check focused element: {e}", flush=True)
            
            # POPUP MODE: Get selected text using AppleScript
            print("📝 Getting selected text via AppleScript...", flush=True)
            selected_text = ""
            has_selection = False
            try:
                import subprocess
                # Use AppleScript to copy selected text temporarily
                script = '''
                tell application "System Events"
                    keystroke "c" using command down
                end tell
                '''
                subprocess.run(['osascript', '-e', script], capture_output=True, timeout=1)
                # Small delay for clipboard to update
                time.sleep(0.1)
                # Get from clipboard
                from .clipboard_manager import ClipboardManager
                clipboard = ClipboardManager()
                selected_text = clipboard.paste()
                has_selection = len(selected_text.strip()) > 0
                print(f"📝 Selected text: {selected_text[:50]}..." if len(selected_text) > 50 else f"📝 Selected text: {selected_text}", flush=True)
                print(f"✅ Has selection: {has_selection}", flush=True)
            except Exception as e:
                print(f"⚠️  Could not get selected text: {e}", flush=True)
            
            # Skip clipboard check - PyObjC pasteboard.types() causes fatal crash
            print("🖼️  Skipping clipboard check (PyObjC causes crashes)...", flush=True)
            has_screenshot = False
            
            # Send event to frontend via websocket or HTTP
            context = {
                "position": {"x": mouse_pos[0], "y": mouse_pos[1]},
                "selected_text": selected_text,
                "has_selection": has_selection,
                "is_text_field": is_text_field,
                "focused_element": focused_element_info,
                "has_screenshot": has_screenshot,
                "timestamp": time.time()
            }

            print("📦 Context:", flush=True)
            print(context, flush=True)
            
            # Broadcast directly to all WebSocket connections
            print("📡 About to broadcast...", flush=True)
            self._broadcast_to_frontend(context)
            print("✅ Broadcast completed!", flush=True)
            
        except Exception as e:
            print(f"❌ Error in _trigger_hotkey: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    def _broadcast_to_frontend(self, context):
        """Broadcast hotkey event directly via WebSocket"""
        if not self.connection_manager:
            print("⚠️  No connection manager available!", flush=True)
            return
            
        conn_count = self.connection_manager.count()
        print(f"📡 Broadcasting to {conn_count} WebSocket connections", flush=True)
        
        if conn_count == 0:
            print("⚠️  No active WebSocket connections! Frontend not connected.", flush=True)
            return
            
        message = {
            "type": "hotkey-pressed",
            "data": context
        }
        
        print(f"📤 Sending message: {message}", flush=True)
        
        # Since we're in a different thread (pynput's thread), we need to schedule
        # the async operations in the main event loop
        import threading
        
        def send_to_all():
            """Send message to all connections"""
            connections = self.connection_manager.get_all()
            print(f"🔄 [WebSocket Thread] Starting send_to_all with {len(connections)} connections", flush=True)
            for i, connection in enumerate(connections):
                try:
                    print(f"📡 [WebSocket] Sending to connection {i+1}...", flush=True)
                    print(f"📡 [WebSocket] Creating new event loop...", flush=True)
                    loop = asyncio.new_event_loop()
                    print(f"📡 [WebSocket] Setting event loop...", flush=True)
                    asyncio.set_event_loop(loop)
                    print(f"📡 [WebSocket] Running send_json...", flush=True)
                    loop.run_until_complete(connection.send_json(message))
                    print(f"📡 [WebSocket] Closing loop...", flush=True)
                    loop.close()
                    print(f"✅ [WebSocket] Sent to connection {i+1}", flush=True)
                except Exception as e:
                    print(f"❌ [WebSocket] Failed to send to connection {i+1}: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
            print(f"🔄 [WebSocket Thread] Finished send_to_all", flush=True)
        
        # Run in a separate thread to avoid blocking the keyboard listener
        thread = threading.Thread(target=send_to_all, daemon=True)
        thread.start()
        
        print("="*60 + "\n", flush=True)
    
    def _trigger_inline_mode(self):
        """Trigger INLINE mode hotkey - works directly in text fields/terminal"""
        try:
            print("\n" + "="*60, flush=True)
            print("🎯 INLINE MODE HOTKEY TRIGGERED!", flush=True)
            print("="*60, flush=True)
            
            if not self.inline_mode_active:
                # START inline mode - start capturing keystrokes
                print("🎯 INLINE MODE ACTIVATED - type your query and press hotkey again to execute", flush=True)
                self.inline_mode_active = True
                self.captured_keystrokes = []  # Clear previous captures
            else:
                # END inline mode - process captured keystrokes
                print("🎯 INLINE MODE ENDING - processing captured text...", flush=True)
                self.inline_mode_active = False
                
                # Build query from captured keystrokes
                query = ''.join(self.captured_keystrokes).strip()
                # The 'L' from both hotkey presses gets typed to the terminal
                # So we need to backspace 2 extra characters (L at start and L at end)
                backspace_count = len(self.captured_keystrokes) + 2
                
                print(f"📝 Query captured: {query}", flush=True)
                print(f"📏 Captured keystrokes: {len(self.captured_keystrokes)}", flush=True)
                print(f"📏 Backspace count (including 2 L's): {backspace_count}", flush=True)
                
                if query:
                    # Process inline query
                    self._process_inline_query(query, backspace_count)
                else:
                    print("⚠️  No query text captured", flush=True)
                
                # Clear captured keystrokes
                self.captured_keystrokes = []
            
            print("="*60 + "\n", flush=True)
            
        except Exception as e:
            print(f"❌ Error in _trigger_inline_mode: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    def _process_inline_query(self, query, query_length):
        """Process inline query - backspace, show thinking, call AI, type response"""
        import threading
        
        def process():
            try:
                # Initialize keyboard controller if not already done
                if not self.keyboard_controller:
                    from pynput.keyboard import Controller
                    self.keyboard_controller = Controller()
                
                kb = self.keyboard_controller
                
                print(f"🎯 Processing inline query: {query}", flush=True)
                
                # Step 1: Backspace the query
                print(f"⌫ Backspacing {query_length} characters...", flush=True)
                time.sleep(0.1)
                for _ in range(query_length):
                    kb.press(Key.backspace)
                    kb.release(Key.backspace)
                    time.sleep(0.05)
                
                # Step 2: Show cycling loading messages with animated dots
                print("💭 Typing loading messages...", flush=True)
                loading_messages = [
                    "Analyzing",
                    "Thinking",
                    "Generating plan",
                    "Processing"
                ]
                
                current_message = ""
                message_index = 0
                
                def type_message_with_dots(message_base):
                    """Type a message and animate the dots"""
                    # Type base message
                    for char in message_base:
                        kb.type(char)
                        time.sleep(0.05)
                    
                    # Add initial dots
                    kb.type("...")
                    time.sleep(0.05)
                    
                    return len(message_base) + 3  # Return total length including dots
                
                def animate_dots():
                    """Animate the dots by backspacing and retyping"""
                    # Backspace the three dots
                    for _ in range(3):
                        kb.press(Key.backspace)
                        kb.release(Key.backspace)
                        time.sleep(0.03)
                    
                    time.sleep(0.2)
                    
                    # Retype the dots
                    kb.type("...")
                    time.sleep(0.05)
                
                # Start typing first message
                current_message = loading_messages[message_index]
                message_length = type_message_with_dots(current_message)
                
                # Step 3: Call AI in background and cycle messages while waiting
                print("🤖 Calling AI...", flush=True)
                import requests
                import threading
                
                ai_response_container = {"response": None, "error": None}
                
                def call_ai():
                    try:
                        response = requests.post(
                            "http://127.0.0.1:8765/api/agent",
                            json={"message": query, "context_parts": []},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            ai_response_container["response"] = response.json().get("response", "")
                            print(f"✅ AI response: {ai_response_container['response']}", flush=True)
                        else:
                            ai_response_container["error"] = f"Error: {response.status_code}"
                            print(f"❌ AI error: {ai_response_container['error']}", flush=True)
                    except Exception as e:
                        ai_response_container["error"] = f"Error: {str(e)}"
                        print(f"❌ AI exception: {ai_response_container['error']}", flush=True)
                
                # Start AI call in background thread
                ai_thread = threading.Thread(target=call_ai)
                ai_thread.start()
                
                # Animate dots and cycle through messages while waiting for AI response
                animation_count = 0
                while ai_response_container["response"] is None and ai_response_container["error"] is None:
                    time.sleep(0.5)  # Animate dots every 0.5 seconds
                    
                    if ai_response_container["response"] is not None or ai_response_container["error"] is not None:
                        break
                    
                    # Animate the dots
                    animate_dots()
                    animation_count += 1
                    
                    # Change message every 4 animations (2 seconds)
                    if animation_count >= 4:
                        animation_count = 0
                        
                        # Backspace current message
                        for _ in range(message_length):
                            kb.press(Key.backspace)
                            kb.release(Key.backspace)
                            time.sleep(0.02)
                        
                        # Move to next message
                        message_index = (message_index + 1) % len(loading_messages)
                        current_message = loading_messages[message_index]
                        
                        # Type new message with dots
                        message_length = type_message_with_dots(current_message)
                
                # Wait for AI thread to complete
                ai_thread.join()
                
                # Get final response
                ai_response = ai_response_container["response"] or ai_response_container["error"] or "No response"
                
                # Step 4: Backspace loading message
                print("⌫ Removing loading message...", flush=True)
                for _ in range(message_length):
                    kb.press(Key.backspace)
                    kb.release(Key.backspace)
                    time.sleep(0.05)
                
                # Step 5: Type the AI response
                print("⌨️  Typing AI response...", flush=True)
                for char in ai_response:
                    kb.type(char)
                    time.sleep(0.02)
                
                print("✅ Inline query complete!", flush=True)
                
            except Exception as e:
                print(f"❌ Error processing inline query: {e}", flush=True)
                import traceback
                traceback.print_exc()
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def set_hotkey_callback(self, callback):
        self.hotkey_callback = callback
