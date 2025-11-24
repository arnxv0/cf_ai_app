#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[cfg(target_os = "macos")]
#[macro_use]
extern crate objc;

use tauri::{Manager, Emitter};
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{TrayIconBuilder};
use tauri_plugin_shell::ShellExt;
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use futures_util::{StreamExt, SinkExt};

mod cloudflare;
use cloudflare::{stream_chat_cloudflare, ingest_memory_cloudflare, search_memory_cloudflare};

#[cfg(target_os = "macos")]
use cocoa::appkit::{NSWindow, NSWindowStyleMask};
#[cfg(target_os = "macos")]
use cocoa::base::id;
#[cfg(target_os = "macos")]
use objc::runtime::YES;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OverlayContextData {
    selected_text: String,
    has_screenshot: bool,
    #[serde(default)]
    has_selection: bool,
    #[serde(default)]
    is_text_field: bool,
    #[serde(default)]
    focused_element: String,
}

// Global state to store overlay context and response data
struct AppState {
    overlay_context: Mutex<Option<serde_json::Value>>,
    response_data: Mutex<Option<ResponseData>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ResponseData {
    response: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    original_query: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    metadata: Option<serde_json::Value>,
}

#[cfg(target_os = "macos")]
fn apply_macos_window_effects(window: &tauri::WebviewWindow) {
    use cocoa::appkit::NSWindowTitleVisibility;
    use cocoa::base::nil;
    
    let window_label = window.label().to_string();
    let app_handle = window.app_handle().clone();
    
    window.run_on_main_thread(move || {
        if let Some(window) = app_handle.get_webview_window(&window_label) {
            unsafe {
                let ns_window_ptr = match window.ns_window() {
                    Ok(ptr) => ptr,
                    Err(e) => {
                        eprintln!("⚠️  Could not get NSWindow for macOS effects: {}", e);
                        return;
                    }
                };
                let ns_window = ns_window_ptr as id;
                
                // Enable rounded corners
                ns_window.setTitlebarAppearsTransparent_(YES);
                ns_window.setTitleVisibility_(NSWindowTitleVisibility::NSWindowTitleHidden);
                
                let mut style_mask = ns_window.styleMask();
                style_mask.insert(NSWindowStyleMask::NSFullSizeContentViewWindowMask);
                ns_window.setStyleMask_(style_mask);
                
                // CRITICAL: Make window background transparent to avoid black corners
                let _: () = msg_send![ns_window, setOpaque: 0];
                let clear_color: id = msg_send![class!(NSColor), clearColor];
                let _: () = msg_send![ns_window, setBackgroundColor: clear_color];
                
                // Also make sure the content view background is transparent
                let content_view: id = ns_window.contentView();
                let _: () = msg_send![content_view, setWantsLayer: 1];
                let layer: id = msg_send![content_view, layer];
                if !layer.is_null() {
                    let _: () = msg_send![layer, setBackgroundColor: nil];
                }
            }
        }
    }).ok();
}

#[tauri::command]
async fn get_overlay_context(state: tauri::State<'_, AppState>) -> Result<serde_json::Value, String> {
    let context = state.overlay_context.lock().unwrap();
    context.clone().ok_or_else(|| "No context available".to_string())
}

#[tauri::command]
fn show_settings(app: tauri::AppHandle) -> Result<String, String> {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
        Ok("Settings shown".to_string())
    } else {
        Err("Settings window not found".to_string())
    }
}

#[tauri::command]
async fn show_overlay(
    app: tauri::AppHandle,
    x: f64,
    y: f64,
    context: serde_json::Value,
) -> Result<String, String> {
    #[cfg(debug_assertions)]
    println!("📍 Showing overlay at: ({}, {})", x, y);
    
    // Store context in state for overlay to fetch
    if let Some(state) = app.try_state::<AppState>() {
        let mut stored_context = state.overlay_context.lock().unwrap();
        *stored_context = Some(context.clone());
        #[cfg(debug_assertions)]
        println!("✅ Stored overlay context in state");
    } else {
        return Err("AppState not available".to_string());
    }
    
    if let Some(window) = app.get_webview_window("overlay") {
        let _ = window.destroy();
    }
    
    use tauri::webview::WebviewWindowBuilder;
    
    // Overlay dimensions
    let overlay_width = 600.0;
    let overlay_height = 80.0;
    
    // Get screen size
    let monitor = match app.primary_monitor() {
        Ok(Some(m)) => m,
        _ => {
            // Fallback: use default position without bounds checking
            #[cfg(debug_assertions)]
            println!("⚠️ Could not get monitor info, using unbounded position");
            let overlay = WebviewWindowBuilder::new(
                &app,
                "overlay",
                tauri::WebviewUrl::App("index.html#overlay".into())
            )
            .title("Pointer Overlay")
            .inner_size(overlay_width, overlay_height)
            .position(x - (overlay_width / 2.0), y)
            .decorations(false)
            .transparent(true)
            .always_on_top(true)
            .resizable(false)
            .skip_taskbar(true)
            .visible(false)
            .content_protected(false)
            .build();
            
            match overlay {
                Ok(window) => {
                    #[cfg(target_os = "macos")]
                    apply_macos_window_effects(&window);
                    
                    // Show immediately - context is fetched from state
                    let _ = window.show();
                    let _ = window.set_focus();
                    return Ok("Overlay shown".to_string());
                }
                Err(e) => return Err(format!("Failed to create overlay: {}", e)),
            }
        }
    };
    
    let screen_size = monitor.size();
    let screen_width = screen_size.width as f64;
    let screen_height = screen_size.height as f64;
    
    // Buffer zones
    let left_buffer = 20.0;
    let right_buffer = 20.0;
    let top_buffer = 40.0;  // For menu bar
    let bottom_buffer = 100.0;  // For dock bar
    
    // Calculate centered position around cursor
    let mut overlay_x = x - (overlay_width / 2.0);
    let mut overlay_y = y;
    
    // Constrain X position within screen bounds
    if overlay_x < left_buffer {
        overlay_x = left_buffer;
    } else if overlay_x + overlay_width > screen_width - right_buffer {
        overlay_x = screen_width - overlay_width - right_buffer;
    }
    
    // Constrain Y position within screen bounds
    if overlay_y < top_buffer {
        overlay_y = top_buffer;
    } else if overlay_y + overlay_height > screen_height - bottom_buffer {
        overlay_y = screen_height - overlay_height - bottom_buffer;
    }
    
    #[cfg(debug_assertions)]
    println!("📍 Adjusted overlay position to: ({}, {})", overlay_x, overlay_y);
    
    let overlay = WebviewWindowBuilder::new(
        &app,
        "overlay",
        tauri::WebviewUrl::App("index.html#overlay".into())
    )
    .title("Pointer Overlay")
    .inner_size(overlay_width, overlay_height)
    .position(overlay_x, overlay_y)
    .decorations(false)
    .transparent(true)
    .always_on_top(true)
    .resizable(false)
    .skip_taskbar(true)
    .visible(false)
    .content_protected(false)
    .build();
    
    match overlay {
        Ok(window) => {
            #[cfg(target_os = "macos")]
            apply_macos_window_effects(&window);
            
            // Show immediately - context is fetched from state
            let _ = window.show();
            let _ = window.set_focus();
            Ok("Overlay shown".to_string())
        }
        Err(e) => Err(format!("Failed to create overlay: {}", e)),
    }
}

#[tauri::command]
async fn hide_overlay(app: tauri::AppHandle) -> Result<String, String> {
    #[cfg(debug_assertions)]
    println!("Hiding overlay...");
    
    if let Some(window) = app.get_webview_window("overlay") {
        let _ = window.close();
    }
    
    // Ensure main window stays hidden (prevent it from showing when overlay closes)
    if let Some(main_window) = app.get_webview_window("main") {
        let _ = main_window.hide();
    }
    
    Ok("Overlay hidden".to_string())
}

#[tauri::command]
async fn show_response_window(
    app: tauri::AppHandle,
    state: tauri::State<'_, AppState>,
    response: String,
    original_query: Option<String>,
    metadata: Option<serde_json::Value>,
    _x: Option<f64>,
    _y: Option<f64>,
) -> Result<String, String> {
    #[cfg(debug_assertions)]
    println!("📋 Showing response window");
    
    // Store response data in state
    let response_data = ResponseData {
        response,
        original_query,
        metadata,
    };
    
    let mut stored_data = state.response_data.lock().unwrap();
    *stored_data = Some(response_data.clone());
    #[cfg(debug_assertions)]
    println!("✅ Stored response data in state");
    
    // Close existing response window if any
    if let Some(window) = app.get_webview_window("response") {
        let _ = window.destroy();
    }
    
    use tauri::webview::WebviewWindowBuilder;
    
    // Response window dimensions - compact and clean
    let window_width = 600.0;
    let window_height = 400.0;
    
    // Center on screen with slight offset for better visual balance
    let monitor = match app.primary_monitor() {
        Ok(Some(m)) => m,
        _ => {
            return Err("Could not get monitor info".to_string());
        }
    };
    
    let screen_size = monitor.size();
    let screen_width = screen_size.width as f64;
    let screen_height = screen_size.height as f64;
    
    // Offset slightly left and up for better visual centering
    let window_x = (screen_width - window_width) / 2.0 - 50.0;
    let window_y = (screen_height - window_height) / 2.0 - 100.0;
    
    #[cfg(debug_assertions)]
    println!("📍 Centering response window at: ({}, {})", window_x, window_y);
    
    let response_window = WebviewWindowBuilder::new(
        &app,
        "response",
        tauri::WebviewUrl::App("index.html#response".into())
    )
    .title("Response")
    .inner_size(window_width, window_height)
    .decorations(false)
    .transparent(true)
    .always_on_top(true)
    .resizable(false)
    .skip_taskbar(true)
    .visible(false)
    .build();
    
    match response_window {
        Ok(window) => {
            #[cfg(target_os = "macos")]
            apply_macos_window_effects(&window);
            
            // Set position AFTER window creation (more reliable on macOS)
            use tauri::Position;
            let _ = window.set_position(Position::Physical(tauri::PhysicalPosition {
                x: window_x as i32,
                y: window_y as i32,
            }));
            #[cfg(debug_assertions)]
            println!("🎯 Set window position to: ({}, {})", window_x, window_y);
            
            std::thread::sleep(std::time::Duration::from_millis(100));
            let _ = window.show();
            let _ = window.set_focus();
            Ok("Response window shown".to_string())
        }
        Err(e) => Err(format!("Failed to create response window: {}", e)),
    }
}

#[tauri::command]
async fn get_response_data(state: tauri::State<'_, AppState>) -> Result<ResponseData, String> {
    let data = state.response_data.lock().unwrap();
    data.clone().ok_or_else(|| "No response data available".to_string())
}

#[tauri::command]
async fn close_response_window(app: tauri::AppHandle, state: tauri::State<'_, AppState>) -> Result<String, String> {
    // Clear the data when closing
    let mut data = state.response_data.lock().unwrap();
    *data = None;
    
    if let Some(window) = app.get_webview_window("response") {
        let _ = window.close();
    }
    Ok("Response window closed".to_string())
}

#[tauri::command]
async fn start_backend(app: tauri::AppHandle) -> Result<String, String> {
    #[cfg(debug_assertions)]
    println!("🚀 Starting Python backend...");
    
    match app.shell().sidecar("pointer-backend") {
        Ok(sidecar_command) => {
            match sidecar_command.spawn() {
                Ok((mut rx, _child)) => {
                    #[cfg(debug_assertions)]
                    println!("✅ Backend process spawned successfully");
                    
                    // Spawn a task to read and print backend output
                    tauri::async_runtime::spawn(async move {
                        use tauri_plugin_shell::process::CommandEvent;
                        while let Some(event) = rx.recv().await {
                            match event {
                                CommandEvent::Stdout(line) => {
                                    print!("[Backend] {}", String::from_utf8_lossy(&line));
                                }
                                CommandEvent::Stderr(line) => {
                                    eprint!("[Backend Error] {}", String::from_utf8_lossy(&line));
                                }
                                CommandEvent::Error(err) => {
                                    eprintln!("[Backend Process Error] {}", err);
                                }
                                CommandEvent::Terminated(payload) => {
                                    println!("[Backend] Process terminated with code: {:?}", payload.code);
                                    break;
                                }
                                _ => {}
                            }
                        }
                    });
                    
                    Ok("Backend started".to_string())
                }
                Err(e) => {
                    let err_msg = format!("Failed to spawn backend: {}", e);
                    eprintln!("❌ {}", err_msg);
                    Err(err_msg)
                }
            }
        }
        Err(e) => {
            let err_msg = format!("Failed to create sidecar command: {}", e);
            eprintln!("❌ {}", err_msg);
            Err(err_msg)
        }
    }
}

fn start_websocket_listener(app: tauri::AppHandle) {
    #[cfg(debug_assertions)]
    println!("🔌 Starting WebSocket listener for Python backend...");
    
    tauri::async_runtime::spawn(async move {
        let mut reconnect_delay = 2u64; // Start with 2 seconds
        let max_delay = 30u64; // Cap at 30 seconds
        
        loop {
            match connect_async("ws://127.0.0.1:8765/ws").await {
                Ok((ws_stream, _)) => {
                    #[cfg(debug_assertions)]
                    println!("✅ Rust WebSocket connected to Python backend");
                    reconnect_delay = 2; // Reset delay on successful connection
                    
                    // Emit connection state to frontend
                    let _ = app.emit("backend-connection", serde_json::json!({"connected": true}));
                    
                    let (mut write, mut read) = ws_stream.split();
                    
                    // Spawn ping task for keep-alive
                    let ping_task = tauri::async_runtime::spawn(async move {
                        loop {
                            tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
                            if write.send(Message::Ping(vec![])).await.is_err() {
                                break;
                            }
                        }
                    });
                    
                    while let Some(msg_result) = read.next().await {
                        match msg_result {
                            Ok(Message::Text(text)) => {
                                if let Ok(data) = serde_json::from_str::<serde_json::Value>(&text) {
                                    if data["type"] == "hotkey-pressed" {
                                        #[cfg(debug_assertions)]
                                        println!("🎯 Rust received hotkey event from Python");
                                        let context = data["data"].clone();
                                        
                                        // Extract position
                                        if let (Some(x), Some(y)) = (
                                            context["position"]["x"].as_f64(),
                                            context["position"]["y"].as_f64()
                                        ) {
                                            let app_clone = app.clone();
                                            // Create overlay on main thread
                                            tauri::async_runtime::spawn(async move {
                                                match show_overlay(app_clone, x, y, context).await {
                                                    Ok(_) => {
                                                        #[cfg(debug_assertions)]
                                                        println!("✅ Overlay created from Rust WebSocket");
                                                    }
                                                    Err(e) => eprintln!("❌ Failed to create overlay: {}", e),
                                                }
                                            });
                                        }
                                    }
                                }
                            }
                            Ok(Message::Pong(_)) => {} // Ignore pong responses
                            Ok(_) => {} // Ignore other message types
                            Err(e) => {
                                eprintln!("❌ WebSocket error: {}", e);
                                break;
                            }
                        }
                    }
                    
                    // Abort ping task on disconnect
                    ping_task.abort();
                    
                    // Emit disconnection state
                    let _ = app.emit("backend-connection", serde_json::json!({"connected": false}));
                    
                    #[cfg(debug_assertions)]
                    println!("⚠️  WebSocket connection closed, reconnecting in {}s...", reconnect_delay);
                    tokio::time::sleep(tokio::time::Duration::from_secs(reconnect_delay)).await;
                    
                    // Exponential backoff
                    reconnect_delay = (reconnect_delay * 2).min(max_delay);
                }
                Err(e) => {
                    eprintln!("❌ Failed to connect to Python WebSocket: {}", e);
                    
                    // Emit disconnection state
                    let _ = app.emit("backend-connection", serde_json::json!({"connected": false}));
                    
                    #[cfg(debug_assertions)]
                    println!("⏳ Retrying in {}s (exponential backoff)...", reconnect_delay);
                    tokio::time::sleep(tokio::time::Duration::from_secs(reconnect_delay)).await;
                    
                    // Exponential backoff
                    reconnect_delay = (reconnect_delay * 2).min(max_delay);
                }
            }
        }
    });
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState {
            overlay_context: Mutex::new(None),
            response_data: Mutex::new(None),
        })
        .setup(|app| {
            // Create system tray menu
            let settings_item = MenuItem::with_id(app, "settings", "Settings", true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", "Quit Pointer", true, None::<&str>)?;
            
            let menu = Menu::with_items(app, &[&settings_item, &quit_item])?;
            
            // Create tray icon
            let icon = app.default_window_icon()
                .ok_or_else(|| "No default window icon available")?;
            let _tray = TrayIconBuilder::new()
                .icon(icon.clone())
                .menu(&menu)
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "settings" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        "quit" => {
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;
            
            // Prevent app from quitting when main window closes
            if let Some(main_window) = app.get_webview_window("main") {
                #[cfg(target_os = "macos")]
                apply_macos_window_effects(&main_window);
                
                let window_clone = main_window.clone();
                main_window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = window_clone.hide();
                    }
                });
            }
            
            // Auto-start Python backend in the background
            let app_handle = app.handle().clone();
            std::thread::spawn(move || {
                // Give the app a moment to fully initialize
                std::thread::sleep(std::time::Duration::from_millis(500));
                
                #[cfg(debug_assertions)]
                println!("🔄 Attempting to auto-start backend...");
                tauri::async_runtime::block_on(async move {
                    match start_backend(app_handle.clone()).await {
                        Ok(_) => {
                            #[cfg(debug_assertions)]
                            println!("✅ Backend auto-started successfully");
                            // Start WebSocket listener after backend starts
                            std::thread::sleep(std::time::Duration::from_millis(1000));
                            start_websocket_listener(app_handle);
                        },
                        Err(e) => eprintln!("⚠️  Failed to auto-start backend: {}", e),
                    }
                });
            });
            
            println!("✅ Pointer running in menu bar");
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            show_settings,
            show_overlay,
            hide_overlay,
            get_overlay_context,
            show_response_window,
            get_response_data,
            close_response_window,
            start_backend,
            stream_chat_cloudflare,
            ingest_memory_cloudflare,
            search_memory_cloudflare
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
