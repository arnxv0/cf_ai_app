import { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { motion } from "framer-motion";
import { ThemeProvider } from "styled-components";
import styled from "styled-components";
import { theme } from "./styles/theme";
import { GlobalStyles } from "./styles/GlobalStyles";

interface OverlayContext {
  selected_text: string;
  has_screenshot: boolean;
}

const OverlayContainer = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin: 0;
  background: transparent;
  position: fixed;
  top: 0;
  left: 0;
`;

const OverlayContent = styled(motion.div)`
  width: 100%;
  height: 100%;
  background: #ffffff;
  border-radius: 12px;
  padding: 0;
  margin: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(0, 0, 0, 0.1);
`;

const StyledForm = styled.form`
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  flex: 1;
`;

const InputContainer = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
`;

const SearchIcon = styled.span`
  font-size: 20px;
  color: rgba(0, 0, 0, 0.5);
  margin-right: 12px;
`;

const OverlayInput = styled.input`
  flex: 1;
  background: transparent;
  border: none;
  color: #000000;
  font-size: 18px;
  font-family: inherit;
  font-weight: 400;

  &:focus {
    outline: none;
  }

  &::placeholder {
    color: rgba(0, 0, 0, 0.4);
  }

  &:disabled {
    opacity: 0.5;
  }
`;

const Footer = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 8px 20px;
  gap: 16px;
  background: rgba(0, 0, 0, 0.03);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
`;

const KeyHintsGroup = styled.div`
  display: flex;
  gap: 16px;
`;

const KeyHint = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
`;

const Key = styled.kbd`
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 4px;
  font-size: 11px;
  font-family: inherit;
  color: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.12);
  font-weight: 500;
`;

const Spinner = styled.div`
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top-color: #007aff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(0, 0, 0, 0.6);
  font-size: 14px;
  font-weight: 500;
`;

const LoadingText = styled.span`
  animation: pulse 1.5s ease-in-out infinite;

  @keyframes pulse {
    0%,
    100% {
      opacity: 0.6;
    }
    50% {
      opacity: 1;
    }
  }
`;

export default function Overlay() {
  const [query, setQuery] = useState("");
  const [context, setContext] = useState<OverlayContext | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("Analyzing...");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Fetch context from Tauri state (eliminates race condition)
    const fetchContext = async () => {
      try {
        const ctx = await invoke<OverlayContext>("get_overlay_context");
        setContext(ctx);
      } catch (error) {
        console.error("[OVERLAY] Failed to fetch context:", error);
      }
    };

    fetchContext();

    // Focus input after a short delay
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeOverlay();
      }
    };

    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const closeOverlay = async () => {
    try {
      await invoke("hide_overlay");
    } catch (error) {
      console.error("Error closing overlay:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isProcessing) return;

    setIsProcessing(true);

    const messages = [
      "Analyzing...",
      "Thinking...",
      "Generating plan...",
      "Processing...",
      "Almost there...",
    ];
    let messageIndex = 0;
    setLoadingMessage(messages[0]);

    const messageInterval = setInterval(() => {
      messageIndex = (messageIndex + 1) % messages.length;
      setLoadingMessage(messages[messageIndex]);
    }, 2000);

    try {
      // Check if Cloudflare is enabled
      let cfEnabled = false;
      let cfConfig: { endpoint: string; api_token: string; rag_top_k: number } | null = null;
      try {
        const settings = await fetch("http://127.0.0.1:8765/api/settings").then((r) => r.json());
        cfEnabled = settings?.cloudflare?.enabled === true;
        if (cfEnabled) {
          cfConfig = {
            endpoint: settings.cloudflare.endpoint,
            api_token: settings.cloudflare.api_token ?? "",
            rag_top_k: settings.cloudflare.rag_top_k ?? 5,
          };
        }
      } catch {
        cfEnabled = false;
      }

      // Build context parts
      const contextParts: { type: string; content: string }[] = [];
      if (context?.selected_text) {
        contextParts.push({
          type: "text",
          content: `Selected text: ${context.selected_text}`,
        });
      }

      let responseText = "";

      if (cfEnabled && cfConfig) {
        // ── Cloudflare path ──────────────────────────────────────────────────
        try {
          let tokenBuffer = "";

          const unlisten = await listen<{ token: string }>("cloudflare-token", (event) => {
            tokenBuffer += event.payload.token;
          });

          await new Promise<void>((resolve, reject) => {
            listen<Record<string, never>>("cloudflare-done", () => resolve());
            listen<{ message: string }>("cloudflare-error", (event) => reject(new Error(event.payload.message ?? "Cloudflare error")));

            const chatMessages = [
              { role: "user", content: query },
            ];
            if (contextParts.length > 0) {
              chatMessages.unshift({
                role: "system",
                content: contextParts.map((p) => p.content).join("\n"),
              });
            }

            invoke("stream_chat_cloudflare", {
              config: cfConfig,
              messages: chatMessages,
              system: undefined,
            }).catch(reject);
          });

          unlisten();
          responseText = tokenBuffer || "No response from Cloudflare.";
        } catch (cfErr) {
          console.warn("[OVERLAY] Cloudflare failed, falling back to local:", cfErr);
          cfEnabled = false; // fall through to local
        }
      }

      if (!cfEnabled) {
        // ── Local Python backend path ────────────────────────────────────────
        const response = await fetch("http://127.0.0.1:8765/api/agent", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: query,
            context_parts: contextParts.length > 0 ? contextParts : null,
            session_id: null,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        responseText = result.response || "No response generated";
      }

      clearInterval(messageInterval);

      await invoke("show_response_window", {
        response: responseText,
        originalQuery: query,
        metadata: null,
      });

      closeOverlay();
    } catch (error) {
      console.error("Error processing query:", error);
      clearInterval(messageInterval);
      const errorMessage = error instanceof Error ? error.message : "Unknown error";

      await invoke("show_response_window", {
        response: `Error: ${errorMessage}`,
        originalQuery: query,
        metadata: null,
      });

      closeOverlay();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    } else if (e.key === "Escape") {
      closeOverlay();
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeOverlay();
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyles theme={theme} />
      <OverlayContainer onClick={handleBackdropClick}>
        <OverlayContent
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          onClick={(e) => e.stopPropagation()}
        >
          <StyledForm onSubmit={handleSubmit}>
            <InputContainer>
              <SearchIcon className="material-icons">search</SearchIcon>
              <OverlayInput
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything..."
                disabled={isProcessing}
                autoFocus
              />
              {isProcessing && (
                <LoadingContainer>
                  <Spinner />
                  <LoadingText>{loadingMessage}</LoadingText>
                </LoadingContainer>
              )}
            </InputContainer>

            <Footer>
              <KeyHintsGroup>
                <KeyHint>
                  <Key>↵</Key>
                  <span>to submit</span>
                </KeyHint>
                <KeyHint>
                  <Key>esc</Key>
                  <span>to cancel</span>
                </KeyHint>
              </KeyHintsGroup>
            </Footer>
          </StyledForm>
        </OverlayContent>
      </OverlayContainer>
    </ThemeProvider>
  );
}
