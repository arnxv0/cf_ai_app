/**
 * Pointer AI — Cloudflare Worker
 *
 * Endpoints:
 *   POST /api/chat           — Streaming chat via Llama-3.3-70B on Workers AI
 *                              Uses ChatSession Durable Object for per-session history
 *   POST /api/memory/ingest  — Chunk text, embed, insert into Vectorize
 *   POST /api/memory/search  — Embed query, return top-K Vectorize matches
 *
 * Auth: Bearer token via API_TOKEN secret (all endpoints)
 */

export interface Env {
  AI: Ai;
  VECTORIZE: VectorizeIndex;
  API_TOKEN: string;
  CHAT_SESSION: DurableObjectNamespace;
}

const CHAT_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast";
const EMBED_MODEL = "@cf/baai/bge-small-en-v1.5";
const CHUNK_SIZE = 512;    // characters per chunk
const CHUNK_OVERLAP = 64;  // overlapping chars for context continuity
const DEFAULT_TOP_K = 5;
const MAX_HISTORY = 50;    // max messages kept in DO storage per session

// ─────────────────────────── Durable Object ──────────────────────────────────

/**
 * ChatSession — Durable Object for per-session chat history.
 *
 * Each session (identified by session_id from the client) gets its own DO
 * instance. The DO stores the last MAX_HISTORY messages so the Worker can
 * prepend full multi-turn context to every LLM call without the client
 * replaying the entire conversation.
 */
export class ChatSession {
  private state: DurableObjectState;

  constructor(state: DurableObjectState) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/history") {
      const history = (await this.state.storage.get<ChatMessage[]>("history")) ?? [];
      return new Response(JSON.stringify({ history }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    if (request.method === "POST" && url.pathname === "/append") {
      const { role, content } = (await request.json()) as ChatMessage;
      const history = (await this.state.storage.get<ChatMessage[]>("history")) ?? [];
      history.push({ role, content });
      // Cap history at MAX_HISTORY messages
      if (history.length > MAX_HISTORY) history.splice(0, history.length - MAX_HISTORY);
      await this.state.storage.put("history", history);
      return new Response(JSON.stringify({ ok: true, length: history.length }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    if (request.method === "DELETE" && url.pathname === "/clear") {
      await this.state.storage.delete("history");
      return new Response(JSON.stringify({ ok: true }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ error: "Not Found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  }
}

// ─────────────────────────── Auth ────────────────────────────────────────────

function authenticate(request: Request, env: Env): Response | null {
  const auth = request.headers.get("Authorization") ?? "";
  if (!auth.startsWith("Bearer ") || auth.slice(7) !== env.API_TOKEN) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }
  return null;
}

// ─────────────────────────── Helpers ─────────────────────────────────────────

function corsHeaders(): HeadersInit {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
  };
}

function chunkText(text: string, size: number, overlap: number): string[] {
  const chunks: string[] = [];
  let start = 0;
  while (start < text.length) {
    chunks.push(text.slice(start, start + size));
    start += size - overlap;
  }
  return chunks;
}

/**
 * Get or create a ChatSession DO stub for a given session_id.
 * Uses a deterministic name so the same session_id always maps to the same DO.
 */
function getSessionStub(env: Env, sessionId: string): DurableObjectStub {
  const id = env.CHAT_SESSION.idFromName(sessionId);
  return env.CHAT_SESSION.get(id);
}

// ─────────────────────────── Handlers ────────────────────────────────────────

interface ChatMessage {
  role: string;
  content: string;
}

async function handleChat(request: Request, env: Env): Promise<Response> {
  const { messages, system, session_id } = (await request.json()) as {
    messages: ChatMessage[];
    system?: string;
    session_id?: string;
  };

  const systemPrompt = system ??
    "You are Pointer, a helpful AI assistant. Be concise and accurate.";

  // If a session_id is provided, prepend stored history from the DO
  let historyMessages: ChatMessage[] = [];
  if (session_id) {
    const stub = getSessionStub(env, session_id);
    const histResp = await stub.fetch("http://do/history");
    const { history } = (await histResp.json()) as { history: ChatMessage[] };
    historyMessages = history;
  }

  // Build final message list: history + new messages from client
  const aiMessages = [
    { role: "system" as const, content: systemPrompt },
    ...historyMessages.map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
    ...messages.map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
  ];

  // Workers AI streaming response
  const aiResponse = await env.AI.run(
    CHAT_MODEL,
    { messages: aiMessages, stream: true } as any
  );

  // After streaming we need to persist context. We do this with a streaming
  // transform — collect the full assistant reply, then write to DO.
  // We use a TransformStream to observe the SSE bytes without buffering for
  // the client (the client still gets full streaming speed).
  if (session_id && messages.length > 0) {
    const lastUserMsg = messages[messages.length - 1];
    const stub = getSessionStub(env, session_id);

    // Append the user message to history
    await stub.fetch("http://do/append", {
      method: "POST",
      body: JSON.stringify({ role: lastUserMsg.role, content: lastUserMsg.content }),
    });

    // Observe the SSE stream, collect full assistant reply, append to DO
    let assistantReply = "";
    const { readable, writable } = new TransformStream({
      transform(chunk, controller) {
        const text = new TextDecoder().decode(chunk);
        for (const line of text.split("\n")) {
          const data = line.startsWith("data: ") ? line.slice(6).trim() : null;
          if (data && data !== "[DONE]") {
            try {
              const parsed = JSON.parse(data);
              if (parsed.response) assistantReply += parsed.response;
            } catch { }
          }
        }
        controller.enqueue(chunk);
      },
      flush() {
        // Fire-and-forget: persist assistant reply to DO
        if (assistantReply) {
          stub.fetch("http://do/append", {
            method: "POST",
            body: JSON.stringify({ role: "assistant", content: assistantReply }),
          });
        }
      },
    });

    (aiResponse as ReadableStream).pipeTo(writable);

    return new Response(readable, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        ...corsHeaders(),
      },
    });
  }

  // No session_id — plain passthrough
  return new Response(aiResponse as ReadableStream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
      ...corsHeaders(),
    },
  });
}

async function handleMemoryIngest(
  request: Request,
  env: Env
): Promise<Response> {
  const { text, metadata } = (await request.json()) as {
    text: string;
    metadata?: Record<string, string | number | boolean>;
  };

  if (!text || text.trim().length === 0) {
    return new Response(JSON.stringify({ error: "text is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders() },
    });
  }

  const chunks = chunkText(text, CHUNK_SIZE, CHUNK_OVERLAP);

  // Embed all chunks in one batch call
  const embedResponse = await env.AI.run(EMBED_MODEL, {
    text: chunks,
  } as any) as { data: number[][] };

  const vectors = chunks.map((chunk, i) => ({
    id: `chunk-${Date.now()}-${i}`,
    values: embedResponse.data[i],
    metadata: {
      text: chunk,
      chunk_index: i,
      total_chunks: chunks.length,
      ingested_at: new Date().toISOString(),
      ...(metadata ?? {}),
    },
  }));

  await env.VECTORIZE.upsert(vectors);

  return new Response(
    JSON.stringify({ ok: true, chunks_ingested: vectors.length }),
    {
      headers: { "Content-Type": "application/json", ...corsHeaders() },
    }
  );
}

async function handleMemorySearch(
  request: Request,
  env: Env
): Promise<Response> {
  const { query, top_k } = (await request.json()) as {
    query: string;
    top_k?: number;
  };

  if (!query || query.trim().length === 0) {
    return new Response(JSON.stringify({ error: "query is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders() },
    });
  }

  const k = top_k ?? DEFAULT_TOP_K;

  const embedResponse = await env.AI.run(EMBED_MODEL, {
    text: [query],
  } as any) as { data: number[][] };

  const queryVector = embedResponse.data[0];

  const results = await env.VECTORIZE.query(queryVector, {
    topK: k,
    returnMetadata: "all",
  });

  const matches = results.matches.map((m) => ({
    id: m.id,
    score: m.score,
    text: (m.metadata as any)?.text ?? "",
    metadata: m.metadata,
  }));

  return new Response(JSON.stringify({ matches }), {
    headers: { "Content-Type": "application/json", ...corsHeaders() },
  });
}

// ─────────────────────────── Router ──────────────────────────────────────────

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // Handle CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    // Health check (unauthenticated)
    if (url.pathname === "/health" && request.method === "GET") {
      return new Response(JSON.stringify({ status: "ok" }), {
        headers: { "Content-Type": "application/json", ...corsHeaders() },
      });
    }

    // All other routes require authentication
    const authError = authenticate(request, env);
    if (authError) return authError;

    if (url.pathname === "/api/chat" && request.method === "POST") {
      return handleChat(request, env);
    }

    if (url.pathname === "/api/memory/ingest" && request.method === "POST") {
      return handleMemoryIngest(request, env);
    }

    if (url.pathname === "/api/memory/search" && request.method === "POST") {
      return handleMemorySearch(request, env);
    }

    // Clear session history for a given session_id
    if (url.pathname === "/api/session/clear" && request.method === "DELETE") {
      const { session_id } = (await request.json()) as { session_id: string };
      if (!session_id) {
        return new Response(JSON.stringify({ error: "session_id required" }), {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders() },
        });
      }
      const stub = getSessionStub(env, session_id);
      await stub.fetch("http://do/clear", { method: "DELETE" });
      return new Response(JSON.stringify({ ok: true }), {
        headers: { "Content-Type": "application/json", ...corsHeaders() },
      });
    }

    return new Response(JSON.stringify({ error: "Not Found" }), {
      status: 404,
      headers: { "Content-Type": "application/json", ...corsHeaders() },
    });
  },
} satisfies ExportedHandler<Env>;
