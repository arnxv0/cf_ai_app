import React, { useState, useEffect } from "react";
import styled from "styled-components";

const Container = styled.div`
  h2 {
    font-size: 28px;
    margin-bottom: ${({ theme }) => theme.spacing.xl};
    color: rgba(0, 0, 0, 0.85);
    font-weight: 600;
  }
`;

const Section = styled.div`
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
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

const PathList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.md};
`;

const PathItem = styled.div`
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: ${({ theme }) => theme.spacing.lg};

  &:hover {
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }
`;

const PathHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${({ theme }) => theme.spacing.sm};
`;

const PathTitle = styled.div`
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};

  .material-icons {
    font-size: 18px;
    color: #007aff;
  }
`;

const PathValue = styled.div`
  font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code", monospace;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.6);
  background: rgba(0, 0, 0, 0.03);
  padding: ${({ theme }) => theme.spacing.sm};
  border-radius: 4px;
  overflow-x: auto;
  white-space: nowrap;
  margin-bottom: ${({ theme }) => theme.spacing.sm};

  &::-webkit-scrollbar {
    height: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 2px;
  }
`;

const PathInfo = styled.div`
  font-size: 12px;
  color: rgba(0, 0, 0, 0.5);
  margin-top: ${({ theme }) => theme.spacing.xs};
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.sm};
  margin-top: ${({ theme }) => theme.spacing.md};
`;

const Button = styled.button<{ $variant?: "primary" | "secondary" | "danger" }>`
  padding: ${({ theme }) => theme.spacing.xs} ${({ theme }) => theme.spacing.md};
  background: ${({ $variant }) => {
    if ($variant === "danger") return "#ff3b30";
    if ($variant === "primary") return "#007aff";
    return "rgba(255, 255, 255, 0.8)";
  }};
  color: ${({ $variant }) =>
    $variant === "secondary" ? "rgba(0, 0, 0, 0.85)" : "white"};
  border: 0.5px solid
    ${({ $variant }) => {
      if ($variant === "danger") return "#ff3b30";
      if ($variant === "primary") return "#007aff";
      return "rgba(0, 0, 0, 0.2)";
    }};
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.xs};

  .material-icons {
    font-size: 16px;
  }

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px
      ${({ $variant }) => {
        if ($variant === "danger") return "rgba(255, 59, 48, 0.3)";
        if ($variant === "primary") return "rgba(0, 122, 255, 0.3)";
        return "rgba(0, 0, 0, 0.1)";
      }};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${({ theme }) => theme.spacing.md};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
`;

const StatCard = styled.div`
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  padding: ${({ theme }) => theme.spacing.md};
  border: 0.5px solid rgba(0, 0, 0, 0.1);

  .stat-value {
    font-size: 24px;
    font-weight: 700;
    color: #007aff;
  }

  .stat-label {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.6);
    margin-top: ${({ theme }) => theme.spacing.xs};
  }
`;

interface StorageLocation {
  id: string;
  title: string;
  path: string;
  description: string;
  icon: string;
  exists?: boolean;
  size?: string;
}

interface StoragePanelProps {
  onShowToast: (message: string, type: "success" | "error" | "info") => void;
}

export default function StoragePanel({ onShowToast }: StoragePanelProps) {
  const [locations, setLocations] = useState<StorageLocation[]>([]);
  const [stats, setStats] = useState({
    totalSize: "0 MB",
    knowledgeBaseDocs: 0,
  });
  const hasLoadedRef = React.useRef(false);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      loadStorageInfo();
    }
  }, []);

  const loadStorageInfo = async () => {
    try {
      // Get storage paths from backend
      const response = await fetch("http://127.0.0.1:8765/api/storage/paths");
      const data = await response.json();

      if (data.success) {
        setLocations(data.locations);
      }

      // Get RAG stats
      const ragResponse = await fetch("http://127.0.0.1:8765/api/rag/stats");
      const ragData = await ragResponse.json();

      // Get storage stats
      const storageResponse = await fetch(
        "http://127.0.0.1:8765/api/storage/stats"
      );
      const storageData = await storageResponse.json();

      setStats({
        totalSize: storageData.total_size || "0 B",
        knowledgeBaseDocs: ragData.total_documents || 0,
      });
    } catch (error) {
      console.error("Error loading storage info:", error);

      // Fallback to default paths if API fails
      setLocations([
        {
          id: "knowledge_base",
          title: "Knowledge Base Database",
          path: "~/Library/Application Support/Pointer/knowledge_base.db",
          description:
            "SQLite database containing RAG documents and embeddings",
          icon: "storage",
        },
        {
          id: "settings",
          title: "Settings Database",
          path: "~/Library/Application Support/Pointer/settings.db",
          description: "Encrypted settings and environment variables",
          icon: "settings",
        },
        {
          id: "data_dir",
          title: "Application Data Directory",
          path: "~/Library/Application Support/Pointer/",
          description: "Main directory containing all Pointer data",
          icon: "folder",
        },
      ]);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    onShowToast("Path copied to clipboard", "success");
  };

  const openInFinder = (path: string) => {
    // Expand tilde to home directory
    const expandedPath = path.replace("~", process.env.HOME || "");

    // For Tauri, we'd need to invoke a command to open Finder
    // For now, just copy the path
    copyToClipboard(expandedPath);
    onShowToast("Path copied - paste in Finder's 'Go to Folder'", "info");
  };

  const clearData = async (locationId: string) => {
    if (
      !confirm(
        "Are you sure you want to delete this data? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      if (locationId === "knowledge_base") {
        // Clear knowledge base
        const response = await fetch("http://127.0.0.1:8765/api/rag/clear", {
          method: "POST",
        });
        const data = await response.json();
        if (data.success) {
          onShowToast("Knowledge base cleared", "success");
          loadStorageInfo();
        }
      } else {
        onShowToast("Delete functionality coming soon", "info");
      }
    } catch (error) {
      console.error("Error clearing data:", error);
      onShowToast("Failed to clear data", "error");
    }
  };

  return (
    <Container>
      <h2>Data & Storage</h2>

      <StatsGrid>
        <StatCard>
          <div className="stat-value">{stats.knowledgeBaseDocs}</div>
          <div className="stat-label">Knowledge Base Documents</div>
        </StatCard>
        <StatCard>
          <div className="stat-value">{stats.totalSize}</div>
          <div className="stat-label">Total Storage Used</div>
        </StatCard>
      </StatsGrid>

      <Section>
        <h3>Storage Locations</h3>
        <PathList>
          {locations.map((location) => (
            <PathItem key={location.id}>
              <PathHeader>
                <PathTitle>
                  <span className="material-icons">{location.icon}</span>
                  {location.title}
                </PathTitle>
              </PathHeader>
              <PathValue>{location.path}</PathValue>
              <PathInfo>
                {location.description}
                {location.size && (
                  <span style={{ marginLeft: "1rem", fontWeight: 600 }}>
                    • {location.size}
                  </span>
                )}
                {location.exists !== undefined && !location.exists && (
                  <span style={{ marginLeft: "1rem", color: "#ff3b30" }}>
                    • Not found
                  </span>
                )}
              </PathInfo>
              <ButtonGroup>
                <Button
                  $variant="secondary"
                  onClick={() => copyToClipboard(location.path)}
                >
                  <span className="material-icons">content_copy</span>
                  Copy Path
                </Button>
                <Button
                  $variant="secondary"
                  onClick={() => openInFinder(location.path)}
                >
                  <span className="material-icons">folder_open</span>
                  Open in Finder
                </Button>
                {location.id === "knowledge_base" && (
                  <Button
                    $variant="danger"
                    onClick={() => clearData(location.id)}
                  >
                    <span className="material-icons">delete</span>
                    Clear Data
                  </Button>
                )}
              </ButtonGroup>
            </PathItem>
          ))}
        </PathList>
      </Section>

      <Section>
        <h3>About Storage</h3>
        <p style={{ color: "rgba(0, 0, 0, 0.6)", lineHeight: 1.6 }}>
          Pointer stores all data locally on your machine. Your environment
          variables and settings are encrypted at rest.
        </p>
        <p
          style={{
            color: "rgba(0, 0, 0, 0.6)",
            lineHeight: 1.6,
            marginTop: "1rem",
          }}
        >
          To completely remove Pointer data, delete the{" "}
          <code
            style={{
              background: "rgba(0, 0, 0, 0.05)",
              padding: "2px 6px",
              borderRadius: "4px",
            }}
          >
            ~/Library/Application Support/Pointer
          </code>{" "}
          folder.
        </p>
      </Section>
    </Container>
  );
}
