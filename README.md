> This is a public fork submitted to the Cloudflare AI Challenge. The private repo is in active development.

# Pointer

A macOS app that opens an AI overlay at your cursor when you press a hotkey. Select text, take a screenshot, or just start typing — it picks up the context automatically.

Built with Tauri (Rust shell), React frontend, and a Python FastAPI sidecar. AI runs on Cloudflare.

## How Cloudflare is used

When you submit a query, the Tauri layer makes a streaming request to a Cloudflare Worker (`/api/chat`). The Worker runs **Llama-3.3-70B** via Workers AI and streams tokens back as SSE. The frontend listens to Tauri events (`cloudflare-token`) and renders them as they arrive.

Memory works through **Vectorize**. Before every LLM call, the Python sidecar hits `/api/memory/search` to find relevant chunks from past context, then prepends them to the prompt. You can push new content into the index via `/api/memory/ingest` from the settings panel.

All three endpoints are gated by a Bearer token stored as a Wrangler secret.

```
User presses ⌘+Shift+K
        │
        ▼
  Tauri (Rust)
  stream_chat_cloudflare command
        │
        ▼  POST /api/chat  Bearer token
  Cloudflare Worker
        ├── Workers AI → Llama-3.3-70B  (streams tokens back)
        └── Vectorize  → pointer-memory (memory search/ingest)
        │
        ▼  SSE token stream
  React Overlay  (renders as tokens arrive)

Python sidecar also calls /api/memory/search before each agent run
and prepends the top-K chunks to the LLM context.
```

If Cloudflare is disabled or a request fails, it falls back to the local Python backend.

## Setup

```bash
npm install
npm run tauri:dev
```

Cloudflare one-time setup:

```bash
cd cloudflare
npx wrangler vectorize create pointer-memory --dimensions=384 --metric=cosine
npx wrangler secret put API_TOKEN
npx wrangler deploy
```

Then open Settings → Cloudflare AI, paste the worker URL and token, and enable it.

## Stack

- Tauri 2 (Rust) — desktop shell and native APIs
- React + TypeScript — overlay and settings UI
- Python FastAPI — local agent, plugins, keyboard monitoring
- Cloudflare Workers — AI inference (Llama-3.3-70B) and vector memory (Vectorize)
