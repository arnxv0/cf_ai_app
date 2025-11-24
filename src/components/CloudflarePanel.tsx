import { useState, useEffect, useCallback } from "react";
import styled from "styled-components";


// ─── Styled components (match existing SettingsPanel aesthetic) ───────────────

const Container = styled.div`
  h2 {
    font-size: 28px;
    margin-bottom: 24px;
    color: rgba(0, 0, 0, 0.85);
    font-weight: 600;
  }
`;

const Section = styled.div`
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);

  h3 {
    font-size: 18px;
    margin-bottom: 16px;
    color: rgba(0, 0, 0, 0.85);
    font-weight: 600;
  }
`;

const FormGroup = styled.div`
  margin-bottom: 16px;
`;

const FormLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.75);

  input[type="checkbox"] {
    width: auto;
    cursor: pointer;
    accent-color: #007aff;
  }
`;

const FormControl = styled.input`
  width: 100%;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
  transition: all 0.15s;

  &:focus {
    outline: none;
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
    background: rgba(255, 255, 255, 0.95);
  }

  &::placeholder {
    color: rgba(0, 0, 0, 0.3);
  }
`;

const SaveButton = styled.button`
  padding: 8px 20px;
  background: #007aff;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: #0062cc;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const TestButton = styled(SaveButton)`
  background: #34c759;
  &:hover {
    background: #28a745;
  }
`;

const ButtonRow = styled.div`
  display: flex;
  gap: 12px;
  margin-top: 8px;
  flex-wrap: wrap;
`;

const StatusRow = styled.div<{ $ok?: boolean }>`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  background: ${({ $ok }) =>
        $ok ? "rgba(52, 199, 89, 0.12)" : "rgba(255, 59, 48, 0.12)"};
  color: ${({ $ok }) => ($ok ? "#28a745" : "#dc3545")};
  margin-top: 8px;
`;

const MemoryCard = styled.div`
  background: rgba(0, 122, 255, 0.06);
  border: 0.5px solid rgba(0, 122, 255, 0.2);
  border-radius: 10px;
  padding: 16px 20px;
`;

const StatLine = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.7);
  margin-bottom: 12px;

  span:last-child {
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
  }
`;

const DestructiveButton = styled(SaveButton)`
  background: #ff3b30;
  &:hover {
    background: #c0392b;
  }
`;

const HintText = styled.p`
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin: 4px 0 0;
`;

// ─── Types ────────────────────────────────────────────────────────────────────

interface CloudflareSettings {
    enabled: boolean;
    endpoint: string;
    api_token: string;
    default_model: string;
    rag_top_k: number;
}

interface CloudflarePanelProps {
    onShowToast?: (message: string, type: "success" | "error" | "info") => void;
}

const BACKEND = "http://127.0.0.1:8765";

// ─── Component ────────────────────────────────────────────────────────────────

export default function CloudflarePanel({ onShowToast }: CloudflarePanelProps) {
    const [settings, setSettings] = useState<CloudflareSettings>({
        enabled: false,
        endpoint: "",
        api_token: "",
        default_model: "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        rag_top_k: 5,
    });
    const [isSaving, setIsSaving] = useState(false);
    const [testStatus, setTestStatus] = useState<"idle" | "ok" | "error">("idle");
    const [testMsg, setTestMsg] = useState("");
    const [chunkCount, setChunkCount] = useState<number | null>(null);
    const [isReindexing, setIsReindexing] = useState(false);

    // Load settings from Python backend
    useEffect(() => {
        fetch(`${BACKEND}/api/settings`)
            .then((r) => r.json())
            .then((data) => {
                const cf = data?.cloudflare ?? {};
                setSettings((prev) => ({
                    ...prev,
                    enabled: cf.enabled ?? false,
                    endpoint: cf.endpoint ?? "",
                    default_model: cf.default_model ?? prev.default_model,
                    rag_top_k: cf.rag_top_k ?? prev.rag_top_k,
                    // api_token is masked — only update if user types a new one
                }));
            })
            .catch(() => { });
    }, []);

    const save = useCallback(async () => {
        setIsSaving(true);
        try {
            const fields: Record<string, { value: unknown; is_secret?: boolean }> = {
                "cloudflare.enabled": { value: settings.enabled },
                "cloudflare.endpoint": { value: settings.endpoint },
                "cloudflare.default_model": { value: settings.default_model },
                "cloudflare.rag_top_k": { value: settings.rag_top_k },
            };
            if (settings.api_token && !settings.api_token.includes("*")) {
                fields["cloudflare.api_token"] = {
                    value: settings.api_token,
                    is_secret: true,
                };
            }

            await Promise.all(
                Object.entries(fields).map(([key, { value, is_secret }]) =>
                    fetch(`${BACKEND}/api/settings`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ key, value, is_secret: is_secret ?? false }),
                    })
                )
            );
            onShowToast?.("Cloudflare settings saved", "success");
        } catch {
            onShowToast?.("Failed to save settings", "error");
        } finally {
            setIsSaving(false);
        }
    }, [settings, onShowToast]);

    const testConnection = useCallback(async () => {
        setTestStatus("idle");
        setTestMsg("");
        if (!settings.endpoint) {
            setTestStatus("error");
            setTestMsg("Endpoint URL is required");
            return;
        }
        try {
            const url = `${settings.endpoint.replace(/\/$/, "")}/health`;
            const resp = await fetch(url, { signal: AbortSignal.timeout(5000) });
            if (resp.ok) {
                setTestStatus("ok");
                setTestMsg("Worker is reachable ✓");
            } else {
                setTestStatus("error");
                setTestMsg(`HTTP ${resp.status}`);
            }
        } catch (e: unknown) {
            setTestStatus("error");
            setTestMsg(e instanceof Error ? e.message : "Connection failed");
        }
    }, [settings.endpoint]);

    const reindex = useCallback(async () => {
        setIsReindexing(true);
        try {
            const resp = await fetch(`${BACKEND}/api/cloudflare/reindex`, {
                method: "POST",
            });
            const data = await resp.json();
            setChunkCount(data.chunks_ingested ?? null);
            onShowToast?.(`Re-indexed ${data.chunks_ingested ?? 0} chunks`, "success");
        } catch {
            onShowToast?.("Re-index failed", "error");
        } finally {
            setIsReindexing(false);
        }
    }, [onShowToast]);

    const clearMemory = useCallback(async () => {
        try {
            await fetch(`${BACKEND}/api/cloudflare/memory`, { method: "DELETE" });
            setChunkCount(0);
            onShowToast?.("Memory cleared", "info");
        } catch {
            onShowToast?.("Clear failed", "error");
        }
    }, [onShowToast]);

    const update = <K extends keyof CloudflareSettings>(
        key: K,
        value: CloudflareSettings[K]
    ) => setSettings((prev) => ({ ...prev, [key]: value }));

    return (
        <Container>
            <h2>Cloudflare AI</h2>

            {/* Connection Settings */}
            <Section>
                <h3>Connection</h3>

                <FormGroup>
                    <FormLabel>
                        <input
                            type="checkbox"
                            checked={settings.enabled}
                            onChange={(e) => update("enabled", e.target.checked)}
                        />
                        Enable Cloudflare AI (overrides local backend)
                    </FormLabel>
                </FormGroup>

                <FormGroup>
                    <FormLabel>Worker Endpoint URL</FormLabel>
                    <FormControl
                        type="url"
                        value={settings.endpoint}
                        onChange={(e) => update("endpoint", e.target.value)}
                        placeholder="https://cloudflare.<your-subdomain>.workers.dev"
                    />
                    <HintText>Deploy with: cd cloudflare && npx wrangler deploy</HintText>
                </FormGroup>

                <FormGroup>
                    <FormLabel>API Token</FormLabel>
                    <FormControl
                        type="password"
                        value={settings.api_token}
                        onChange={(e) => update("api_token", e.target.value)}
                        placeholder="Set with: npx wrangler secret put API_TOKEN"
                    />
                </FormGroup>

                {testStatus !== "idle" && (
                    <StatusRow $ok={testStatus === "ok"}>{testMsg}</StatusRow>
                )}

                <ButtonRow>
                    <TestButton onClick={testConnection}>Test Connection</TestButton>
                    <SaveButton disabled={isSaving} onClick={save}>
                        {isSaving ? "Saving…" : "Save Settings"}
                    </SaveButton>
                </ButtonRow>
            </Section>

            {/* Model Settings */}
            <Section>
                <h3>Model</h3>
                <FormGroup>
                    <FormLabel>Default Chat Model</FormLabel>
                    <FormControl
                        type="text"
                        value={settings.default_model}
                        onChange={(e) => update("default_model", e.target.value)}
                        placeholder="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
                    />
                </FormGroup>

                <FormGroup>
                    <FormLabel>RAG Top-K Results</FormLabel>
                    <FormControl
                        type="number"
                        min={1}
                        max={20}
                        value={settings.rag_top_k}
                        onChange={(e) => update("rag_top_k", Number(e.target.value))}
                    />
                    <HintText>Number of memory chunks prepended to each query</HintText>
                </FormGroup>
            </Section>

            {/* Memory Status */}
            <Section>
                <h3>Memory (Vectorize)</h3>
                <MemoryCard>
                    <StatLine>
                        <span>Indexed chunks</span>
                        <span>{chunkCount === null ? "—" : chunkCount}</span>
                    </StatLine>
                    <ButtonRow>
                        <TestButton disabled={isReindexing} onClick={reindex}>
                            {isReindexing ? "Indexing…" : "Re-index"}
                        </TestButton>
                        <DestructiveButton onClick={clearMemory}>
                            Clear Memory
                        </DestructiveButton>
                    </ButtonRow>
                    <HintText style={{ marginTop: 12 }}>
                        Re-index pushes your local knowledge base into Cloudflare Vectorize.
                    </HintText>
                </MemoryCard>
            </Section>
        </Container>
    );
}
