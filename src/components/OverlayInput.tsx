import { useState, useEffect, useRef } from "react";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { motion } from "framer-motion";

interface OverlayContext {
  selected_text: string;
  has_screenshot: boolean;
}

export default function Overlay() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"execute" | "Add to knowledge">("execute");
  const [context, setContext] = useState<OverlayContext | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // Listen for context from main window
    const unlisten = listen("overlay-context", (event: any) => {
      console.log("Received context:", event.payload);
      setContext(event.payload);
    });

    // Focus input when overlay appears
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);

    // Handle escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeOverlay();
      }
    };

    window.addEventListener("keydown", handleEscape);

    return () => {
      unlisten.then((fn) => fn());
      window.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const closeOverlay = async () => {
    const window = getCurrentWindow();
    await window.close();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isProcessing) return;

    setIsProcessing(true);

    try {
      const response = await fetch("http://127.0.0.1:8765/api/process-query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          mode,
          settings: {}, // Load from storage if needed
          context: {
            selected_text: context?.selected_text,
            has_screenshot: context?.has_screenshot,
          },
        }),
      });

      const result = await response.json();
      console.log("Result:", result);

      // Close overlay after processing
      setTimeout(closeOverlay, 500);
    } catch (error) {
      console.error("Error processing query:", error);
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <motion.div
      className="overlay-container"
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
    >
      {context?.selected_text && (
        <div className="context-indicator">
          <span className="material-icons">content_copy</span>
          <span>{context.selected_text.substring(0, 50)}...</span>
        </div>
      )}

      {context?.has_screenshot && (
        <div className="context-indicator">
          <span className="material-icons">screenshot</span>
          <span>Screenshot detected</span>
        </div>
      )}

      <div className="mode-selector">
        <button
          className={`mode-btn ${mode === "execute" ? "active" : ""}`}
          onClick={() => setMode("execute")}
          disabled={isProcessing}
        >
          Execute
        </button>
        <button
          className={`mode-btn ${mode === "Add to knowledge" ? "active" : ""}`}
          onClick={() => setMode("Add to knowledge")}
          disabled={isProcessing}
        >
          Explain
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <textarea
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isProcessing
              ? "Processing..."
              : "Type your command... (Enter to submit, Esc to close)"
          }
          className="overlay-textarea"
          rows={4}
          disabled={isProcessing}
        />

        {isProcessing && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Processing your request...</span>
          </div>
        )}

        <div className="overlay-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={closeOverlay}
            disabled={isProcessing}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={isProcessing || !query.trim()}
          >
            {isProcessing ? (
              <>
                <span className="spinner-small"></span>
                Processing...
              </>
            ) : (
              "Submit"
            )}
          </button>
        </div>
      </form>
    </motion.div>
  );
}
