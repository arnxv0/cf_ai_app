/**
 * Pointer AI — Cloudflare Worker
 *
 * Endpoints:
 *   POST /api/chat           — Streaming chat via Llama-3.3-70B on Workers AI
 *   POST /api/memory/ingest  — Chunk text, embed, insert into Vectorize
 *   POST /api/memory/search  — Embed query, return top-K Vectorize matches
 *
 * Auth: Bearer token via API_TOKEN secret (all endpoints)
 */

export interface Env {
  AI: Ai;
  VECTORIZE: VectorizeIndex;
  API_TOKEN: string;
}

const CHAT_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast";
const EMBED_MODEL = "@cf/baai/bge-small-en-v1.5";
const CHUNK_SIZE = 512;    // characters per chunk
const CHUNK_OVERLAP = 64;  // overlapping chars for context continuity
const DEFAULT_TOP_K = 5;

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
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
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

// ─────────────────────────── Handlers ────────────────────────────────────────

async function handleChat(request: Request, env: Env): Promise<Response> {
  const { messages, system } = (await request.json()) as {
    messages: { role: string; content: string }[];
    system?: string;
  };

  const systemPrompt = system ??
    "You are Pointer, a helpful AI assistant. Be concise and accurate.";

  const aiMessages = [
    { role: "system" as const, content: systemPrompt },
    ...messages.map((m) => ({
      role: m.role as "user" | "assistant",
      content: m.content,
    })),
  ];

  // Workers AI streaming response
  const aiResponse = await env.AI.run(
    CHAT_MODEL,
    { messages: aiMessages, stream: true } as any
  );

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

    return new Response(JSON.stringify({ error: "Not Found" }), {
      status: 404,
      headers: { "Content-Type": "application/json", ...corsHeaders() },
    });
  },
} satisfies ExportedHandler<Env>;
