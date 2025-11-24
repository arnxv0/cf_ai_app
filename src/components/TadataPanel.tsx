import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { motion } from "framer-motion";
import { invoke } from "@tauri-apps/api/core";

const PanelContainer = styled.div`
  padding: ${({ theme }) => theme.spacing.xl};
`;

const Header = styled.div`
  margin-bottom: ${({ theme }) => theme.spacing.xl};

  h2 {
    font-size: 28px;
    margin-bottom: ${({ theme }) => theme.spacing.sm};
    color: rgba(0, 0, 0, 0.85);
    font-weight: 600;
  }

  p {
    color: rgba(0, 0, 0, 0.6);
    font-size: 14px;
  }
`;

const Section = styled.div`
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: ${({ theme }) => theme.spacing.xl};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);

  h3 {
    font-size: 18px;
    margin-bottom: ${({ theme }) => theme.spacing.lg};
    color: rgba(0, 0, 0, 0.85);
    font-weight: 600;
  }
`;

const FormGroup = styled.div`
  margin-bottom: ${({ theme }) => theme.spacing.lg};

  label {
    display: block;
    margin-bottom: ${({ theme }) => theme.spacing.sm};
    color: rgba(0, 0, 0, 0.7);
    font-size: 14px;
    font-weight: 500;
  }
`;

const ConnectorGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: ${({ theme }) => theme.spacing.md};
  margin-top: ${({ theme }) => theme.spacing.lg};
`;

const ConnectorCard = styled(motion.div)<{ $enabled: boolean }>`
  background: ${({ $enabled }) =>
    $enabled ? "rgba(52, 199, 89, 0.1)" : "rgba(255, 255, 255, 0.8)"};
  border: 1px solid
    ${({ $enabled }) =>
      $enabled ? "rgba(52, 199, 89, 0.3)" : "rgba(0, 0, 0, 0.1)"};
  border-radius: 10px;
  padding: ${({ theme }) => theme.spacing.lg};
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  h4 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: ${({ theme }) => theme.spacing.xs};
    color: rgba(0, 0, 0, 0.85);
  }

  p {
    font-size: 13px;
    color: rgba(0, 0, 0, 0.6);
    line-height: 1.4;
  }

  .status {
    display: inline-block;
    margin-top: ${({ theme }) => theme.spacing.sm};
    padding: 4px 8px;
    background: ${({ $enabled }) =>
      $enabled ? "rgba(52, 199, 89, 0.2)" : "rgba(0, 0, 0, 0.05)"};
    color: ${({ $enabled }) => ($enabled ? "#34c759" : "rgba(0, 0, 0, 0.5)")};
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
  }
`;

const InfoBox = styled.div`
  background: rgba(0, 122, 255, 0.05);
  border: 1px solid rgba(0, 122, 255, 0.2);
  border-radius: 8px;
  padding: ${({ theme }) => theme.spacing.md};
  margin-bottom: ${({ theme }) => theme.spacing.lg};

  p {
    font-size: 13px;
    color: rgba(0, 0, 0, 0.7);
    line-height: 1.5;
    margin: 0;
  }

  a {
    color: #007aff;
    text-decoration: none;
    font-weight: 500;

    &:hover {
      text-decoration: underline;
    }
  }
`;

interface Connector {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

const AVAILABLE_CONNECTORS: Connector[] = [
  {
    id: "notion",
    name: "Notion",
    description: "Docs and knowledge base",
    enabled: false,
  },
  {
    id: "supabase",
    name: "Supabase",
    description: "Database and backend",
    enabled: false,
  },
  { id: "exa", name: "Exa", description: "AI-powered search", enabled: false },
  {
    id: "linear",
    name: "Linear",
    description: "Issue tracking and project management",
    enabled: false,
  },
  {
    id: "github",
    name: "GitHub",
    description: "Code repositories and PRs",
    enabled: false,
  },
  {
    id: "slack",
    name: "Slack",
    description: "Team communication",
    enabled: false,
  },
  {
    id: "jira",
    name: "Jira",
    description: "Project management",
    enabled: false,
  },
  {
    id: "sentry",
    name: "Sentry",
    description: "Error tracking",
    enabled: false,
  },
  {
    id: "render",
    name: "Render",
    description: "Deployment platform",
    enabled: false,
  },
];

export default function TadataPanel() {
  const [connectors, setConnectors] = useState(AVAILABLE_CONNECTORS);
  const [notionUrl, setNotionUrl] = useState("");
  const [exaUrl, setExaUrl] = useState("");
  const [supabaseUrl, setSupabaseUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const hasLoadedRef = React.useRef(false);

  useEffect(() => {
    if (hasLoadedRef.current) return;
    hasLoadedRef.current = true;
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8765/api/settings/integrations?include_secrets=false"
      );
      const data = await response.json();

      const settings = data.settings || {};

      if (settings.TADATA_NOTION_URL)
        setNotionUrl(settings.TADATA_NOTION_URL);
      if (settings.TADATA_EXA_URL) setExaUrl(settings.TADATA_EXA_URL);
      if (settings.TADATA_SUPABASE_URL)
        setSupabaseUrl(settings.TADATA_SUPABASE_URL);

      if (settings.TADATA_CONNECTORS) {
        const enabledConnectors = JSON.parse(
          settings.TADATA_CONNECTORS || "[]"
        );
        setConnectors((prev) =>
          prev.map((c) => ({
            ...c,
            enabled: enabledConnectors.includes(c.id),
          }))
        );
      }
    } catch (error) {
      console.error("Failed to load Tadata settings:", error);
    }
  };

  const saveMCPUrls = async () => {
    setSaving(true);
    try {
      const updates = [];

      if (notionUrl)
        updates.push({
          category: "integrations",
          key: "TADATA_NOTION_URL",
          value: notionUrl,
          is_secret: false,
        });
      if (exaUrl)
        updates.push({
          category: "integrations",
          key: "TADATA_EXA_URL",
          value: exaUrl,
          is_secret: false,
        });
      if (supabaseUrl)
        updates.push({
          category: "integrations",
          key: "TADATA_SUPABASE_URL",
          value: supabaseUrl,
          is_secret: false,
        });

      for (const update of updates) {
        const response = await fetch("http://127.0.0.1:8765/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(update),
        });

        if (!response.ok) {
          throw new Error(`Failed to save ${update.key}`);
        }
      }

      await invoke("show_toast", {
        message: "Tadata MCP URLs saved",
        level: "success",
      });
    } catch (error) {
      console.error("Error saving MCP URLs:", error);
      await invoke("show_toast", {
        message: "Failed to save MCP URLs",
        level: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  const toggleConnector = async (connectorId: string) => {
    const updated = connectors.map((c) =>
      c.id === connectorId ? { ...c, enabled: !c.enabled } : c
    );
    setConnectors(updated);

    const enabledIds = updated.filter((c) => c.enabled).map((c) => c.id);

    try {
      await fetch("http://127.0.0.1:8765/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: "integrations",
          key: "TADATA_CONNECTORS",
          value: JSON.stringify(enabledIds),
          is_secret: false,
        }),
      });

      await invoke("show_toast", {
        message: `${connectorId} ${
          updated.find((c) => c.id === connectorId)?.enabled
            ? "enabled"
            : "disabled"
        }`,
        level: "info",
      });
    } catch (error) {
      console.error("Failed to update connectors:", error);
    }
  };

  return (
    <PanelContainer>
      <Header>
        <h2>Tadata MCP Integration</h2>
        <p>Connect to your Tadata MCP servers</p>
      </Header>

      <InfoBox>
        <p>
          <strong>Add your Tadata MCP server URLs below.</strong> Get them from{" "}
          <a
            href="https://app.tadata.com/connectors"
            target="_blank"
            rel="noopener noreferrer"
          >
            app.tadata.com/connectors
          </a>{" "}
          after connecting services via OAuth.
        </p>
      </InfoBox>

      <Section>
        <h3>MCP Server URLs</h3>
        <p
          style={{
            fontSize: "14px",
            color: "rgba(0, 0, 0, 0.6)",
            marginBottom: "16px",
          }}
        >
          Paste the MCP server URLs from your Tadata dashboard (including API
          keys)
        </p>

        <FormGroup>
          <label htmlFor="notion-url">Notion MCP URL</label>
          <input
            id="notion-url"
            type="text"
            value={notionUrl}
            onChange={(e) => setNotionUrl(e.target.value)}
            placeholder="https://cyan-kiwis-retire.mcp.tadata.com/?tadata-api-key=..."
            style={{
              width: "100%",
              padding: "12px 16px",
              background: "rgba(255, 255, 255, 0.9)",
              border: "1px solid rgba(0, 0, 0, 0.1)",
              borderRadius: "8px",
              fontSize: "14px",
              marginBottom: "16px",
            }}
          />
        </FormGroup>

        <FormGroup>
          <label htmlFor="exa-url">Exa MCP URL</label>
          <input
            id="exa-url"
            type="text"
            value={exaUrl}
            onChange={(e) => setExaUrl(e.target.value)}
            placeholder="https://wacky-brooms-swim.mcp.tadata.com/?tadata-api-key=..."
            style={{
              width: "100%",
              padding: "12px 16px",
              background: "rgba(255, 255, 255, 0.9)",
              border: "1px solid rgba(0, 0, 0, 0.1)",
              borderRadius: "8px",
              fontSize: "14px",
              marginBottom: "16px",
            }}
          />
        </FormGroup>

        <FormGroup>
          <label htmlFor="supabase-url">Supabase MCP URL</label>
          <input
            id="supabase-url"
            type="text"
            value={supabaseUrl}
            onChange={(e) => setSupabaseUrl(e.target.value)}
            placeholder="https://jolly-brooms-decide.mcp.tadata.com/?tadata-api-key=..."
            style={{
              width: "100%",
              padding: "12px 16px",
              background: "rgba(255, 255, 255, 0.9)",
              border: "1px solid rgba(0, 0, 0, 0.1)",
              borderRadius: "8px",
              fontSize: "14px",
              marginBottom: "16px",
            }}
          />
        </FormGroup>

        <button
          onClick={saveMCPUrls}
          disabled={saving}
          style={{
            padding: "12px 24px",
            background: saving ? "#ccc" : "#007aff",
            color: "white",
            border: "none",
            borderRadius: "8px",
            fontSize: "14px",
            fontWeight: "500",
            cursor: saving ? "not-allowed" : "pointer",
          }}
        >
          {saving ? "Saving..." : "Save MCP URLs"}
        </button>
      </Section>

      <Section>
        <h3>Connected Services</h3>
        <p
          style={{
            fontSize: "14px",
            color: "rgba(0, 0, 0, 0.6)",
            marginBottom: "16px",
          }}
        >
          Track which services you've configured
        </p>
        <ConnectorGrid>
          {connectors.map((connector) => (
            <ConnectorCard
              key={connector.id}
              $enabled={connector.enabled}
              onClick={() => toggleConnector(connector.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <h4>{connector.name}</h4>
              <p>{connector.description}</p>
              <span className="status">
                {connector.enabled ? "✓ Enabled" : "Disabled"}
              </span>
            </ConnectorCard>
          ))}
        </ConnectorGrid>
      </Section>
    </PanelContainer>
  );
}
