# PROMPTS.md — AI Prompts Used During Development

> **Note:** This is a **public fork** of a private repository that has been in active development. The vast majority of the codebase — including the Tauri/Rust shell, the Python FastAPI sidecar, the React overlay UI, agent orchestration logic, and the core Cloudflare Worker — was **written by hand**. AI assistance was used only for narrowly scoped tasks (filling in boilerplate, syntax lookups, and debugging specific issues) after the architecture and design decisions were already made. Those specific prompts are documented below for full transparency per the challenge rules.

---

## 1. Initial Architecture Design

I started by describing the overall system I had in mind and asking for implementation scaffolding.

> **Prompt:**
> I want to build a macOS desktop app that pops up an AI overlay when you press a hotkey. The user should be able to select text on screen or take a screenshot and the overlay picks up the context automatically. The AI backend should run on Cloudflare Workers AI (Llama 3.3). The app shell should use Tauri with a Rust core, a React frontend, and a Python FastAPI sidecar for local agent logic. Help me scaffold the project structure.

---

## 2. Cloudflare Worker — Chat + Memory Endpoints

After deciding on the Cloudflare layer, I designed the three endpoints myself and asked for implementation help:

> **Prompt:**
> Write a Cloudflare Worker in TypeScript with three endpoints:
> - `POST /api/chat`: run Llama-3.3-70B via Workers AI, stream the response as SSE
> - `POST /api/memory/ingest`: chunk incoming text, embed each chunk with bge-small-en-v1.5, and upsert into a Vectorize index called `pointer-memory`
> - `POST /api/memory/search`: embed the query and return the top-K matches from the same Vectorize index
> All endpoints should be gated by a Bearer token stored as a Wrangler secret.

---

## 3. Durable Object — Session State

I decided I wanted per-session conversation history to persist across requests on the edge, so that the Worker can maintain multi-turn context without relying on the client to replay the full message list. I designed the schema and asked for help wiring it up:

> **Prompt:**
> Add a Durable Object called `ChatSession` to my Cloudflare Worker. It should store a capped message history (last 50 turns) in its storage. Expose two internal methods: `appendMessage(role, content)` and `getHistory()`. The `/api/chat` endpoint should look up or create a session by `session_id` (from the request body), prepend the stored history before calling Workers AI, and append both the user message and the assistant reply into the DO storage after the response completes.

---

## 4. Rust Streaming Client

I designed the Tauri command interface (what data types to pass from the frontend, what events to emit back) and asked for the Rust implementation:

> **Prompt:**
> Write a Rust module for Tauri that implements `stream_chat_cloudflare`. It should POST to `/api/chat` on my Cloudflare Worker with a Bearer token, consume the SSE response byte-by-byte, parse `data: {...}` lines, and emit each token as a `cloudflare-token` Tauri event. Emit `cloudflare-done` when it sees `[DONE]`. On any error, emit `cloudflare-error` and return an Err. Also write `ingest_memory_cloudflare` and `search_memory_cloudflare` as standard async Tauri commands.

---

## 5. Python Sidecar — Memory-Augmented Agent Route

I designed the RAG injection logic (fetch memory before each agent run, prepend as context) and asked for help wiring it into the FastAPI route:

> **Prompt:**
> I have a Python FastAPI route that runs a local AI agent. Before each agent run, I want to hit my Cloudflare Worker's `/api/memory/search` endpoint to fetch semantically similar past context, then prepend it to the user's message. If Cloudflare is disabled or the call fails, just continue without context. Show me how to integrate this into the existing `/api/agent` route without blocking the fallback path.

---

## 6. React Frontend — Cloudflare Settings Panel

I designed the UX (enable/disable toggle, endpoint + token fields, test connection button, ingest panel, search panel) and asked for the component:

> **Prompt:**
> Build a React + TypeScript settings panel component for my Tauri app that lets the user configure the Cloudflare Worker integration. It should have a toggle to enable/disable Cloudflare AI, text fields for the Worker URL and API token, a "Test Connection" button that hits `/health` and shows a result toast, a text area to ingest new content into Vectorize, and a search box to query the vector index. Use Tauri's `invoke` to call the Rust commands and the Python sidecar's `/api/settings` endpoint to persist config.

---

## 7. Debugging SSE Streaming in Tauri

Ran into an issue where the byte stream wasn't being parsed correctly because Workers AI sometimes sends multiple SSE events in a single TCP chunk:

> **Prompt:**
> My Tauri Rust code reads SSE from a reqwest byte stream. Sometimes a single chunk from the server contains multiple `data:` lines. My current loop only processes the last line. Fix the loop so it splits each chunk by newline and processes every line individually.

---

## 8. Vectorize Memory Schema Design

I decided to use overlapping chunks (64-char overlap) for better semantic coverage at boundaries, and asked for feedback on chunk size:

> **Prompt:**
> I'm chunking text into 512-character pieces with a 64-character overlap before embedding with bge-small-en-v1.5 (384 dimensions). Is this a reasonable chunk size for a general-purpose memory store where queries are typically 1-3 sentences? Would you change anything?

---

## Notes

- This is a **public fork** of a private repository. The private repo contains the full development history; this fork was created specifically for the Cloudflare AI Challenge submission.
- The overwhelming majority of the code — Tauri/Rust shell, Python FastAPI sidecar, React overlay + settings UI, agent orchestration, Cloudflare Worker, and full RAG pipeline — was **written by hand**.
- All architectural decisions (multi-layer stack, edge AI + local fallback, RAG before every agent call, per-session Durable Objects, hotkey trigger model) were made by me before any AI tool was consulted.
- AI assistance was used only for narrowly scoped implementation tasks after the design was already decided — primarily boilerplate reduction, unfamiliar API syntax, and debugging specific issues.
- No code was copied from other submissions or sample projects.
