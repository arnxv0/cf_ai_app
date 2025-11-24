// cloudflare.rs — Cloudflare Worker HTTP client for Pointer AI
//
// Implements three thin async functions:
//   stream_chat_cloudflare  — POST /api/chat, emits token events to frontend
//   ingest_memory_cloudflare — POST /api/memory/ingest
//   search_memory_cloudflare — POST /api/memory/search
//
// Config comes in as arguments from the frontend (which reads it from the
// Python backend's /api/settings endpoint at startup).

use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use tauri::{AppHandle, Emitter};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CloudflareConfig {
    pub endpoint: String,
    pub api_token: String,
    pub rag_top_k: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub role: String,
    pub content: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MemoryMatch {
    pub id: String,
    pub score: f64,
    pub text: String,
}

fn build_client() -> Client {
    Client::builder()
        .timeout(std::time::Duration::from_secs(60))
        .build()
        .unwrap_or_default()
}

fn auth_header(token: &str) -> String {
    format!("Bearer {}", token)
}

// ─────────────────────────── Chat ────────────────────────────────────────────

/// Stream chat tokens from the Cloudflare Worker and emit them as Tauri events.
/// Each token is emitted as `cloudflare-token` event with a `{token: "..."}` payload.
/// A final `cloudflare-done` event is emitted when streaming ends.
/// On error, falls back gracefully and emits `cloudflare-error`.
#[tauri::command]
pub async fn stream_chat_cloudflare(
    app: AppHandle,
    config: CloudflareConfig,
    messages: Vec<ChatMessage>,
    system: Option<String>,
) -> Result<(), String> {
    let client = build_client();
    let url = format!("{}/api/chat", config.endpoint.trim_end_matches('/'));

    let mut payload = json!({ "messages": messages });
    if let Some(sys) = system {
        payload["system"] = json!(sys);
    }

    let response = match client
        .post(&url)
        .header("Authorization", auth_header(&config.api_token))
        .header("Content-Type", "application/json")
        .json(&payload)
        .send()
        .await
    {
        Ok(r) => r,
        Err(e) => {
            eprintln!("[Cloudflare] chat request failed: {}", e);
            let _ = app.emit("cloudflare-error", json!({"message": e.to_string()}));
            return Err(format!("Cloudflare chat failed: {}", e));
        }
    };

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        eprintln!("[Cloudflare] chat HTTP {}: {}", status, body);
        let _ = app.emit("cloudflare-error", json!({"message": format!("HTTP {}: {}", status, body)}));
        return Err(format!("Cloudflare HTTP {}", status));
    }

    use futures_util::StreamExt;
    let mut stream = response.bytes_stream();

    while let Some(chunk) = stream.next().await {
        match chunk {
            Ok(bytes) => {
                let text = String::from_utf8_lossy(&bytes);
                for line in text.lines() {
                    if let Some(data) = line.strip_prefix("data: ") {
                        if data.trim() == "[DONE]" {
                            let _ = app.emit("cloudflare-done", json!({}));
                            return Ok(());
                        }
                        // Try to extract `response` field from Workers AI SSE JSON
                        if let Ok(v) = serde_json::from_str::<serde_json::Value>(data) {
                            if let Some(token) = v.get("response").and_then(|t| t.as_str()) {
                                let _ = app.emit("cloudflare-token", json!({"token": token}));
                            }
                        }
                    }
                }
            }
            Err(e) => {
                eprintln!("[Cloudflare] stream error: {}", e);
                let _ = app.emit("cloudflare-error", json!({"message": e.to_string()}));
                return Err(format!("Stream error: {}", e));
            }
        }
    }

    let _ = app.emit("cloudflare-done", json!({}));
    Ok(())
}

// ─────────────────────────── Memory ──────────────────────────────────────────

/// Send text to the Worker for chunking + embedding + Vectorize upsert.
#[tauri::command]
pub async fn ingest_memory_cloudflare(
    config: CloudflareConfig,
    text: String,
    metadata: Option<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    let client = build_client();
    let url = format!("{}/api/memory/ingest", config.endpoint.trim_end_matches('/'));

    let mut payload = json!({ "text": text });
    if let Some(m) = metadata {
        payload["metadata"] = m;
    }

    let resp = client
        .post(&url)
        .header("Authorization", auth_header(&config.api_token))
        .header("Content-Type", "application/json")
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !resp.status().is_success() {
        return Err(format!("HTTP {}", resp.status()));
    }

    resp.json::<serde_json::Value>()
        .await
        .map_err(|e| format!("JSON parse error: {}", e))
}

/// Query Vectorize for top-K semantic matches.
#[tauri::command]
pub async fn search_memory_cloudflare(
    config: CloudflareConfig,
    query: String,
    top_k: Option<u32>,
) -> Result<Vec<MemoryMatch>, String> {
    let client = build_client();
    let url = format!("{}/api/memory/search", config.endpoint.trim_end_matches('/'));

    let payload = json!({
        "query": query,
        "top_k": top_k.unwrap_or(config.rag_top_k.unwrap_or(5)),
    });

    let resp = client
        .post(&url)
        .header("Authorization", auth_header(&config.api_token))
        .header("Content-Type", "application/json")
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !resp.status().is_success() {
        return Err(format!("HTTP {}", resp.status()));
    }

    let data: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| format!("JSON parse error: {}", e))?;

    let matches = data["matches"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .filter_map(|m| {
                    Some(MemoryMatch {
                        id: m["id"].as_str()?.to_string(),
                        score: m["score"].as_f64().unwrap_or(0.0),
                        text: m["text"].as_str().unwrap_or("").to_string(),
                    })
                })
                .collect()
        })
        .unwrap_or_default();

    Ok(matches)
}
