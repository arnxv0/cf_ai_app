import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { motion, AnimatePresence } from "framer-motion";

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

const TabContainer = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.sm};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
`;

const Tab = styled.button<{ $active: boolean }>`
  padding: ${({ theme }) => theme.spacing.md} ${({ theme }) => theme.spacing.lg};
  background: ${({ $active }) =>
    $active ? "rgba(0, 122, 255, 0.1)" : "transparent"};
  border: none;
  border-bottom: 2px solid
    ${({ $active }) => ($active ? "#007aff" : "transparent")};
  color: ${({ $active }) => ($active ? "#007aff" : "rgba(0, 0, 0, 0.6)")};
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(0, 122, 255, 0.05);
    color: #007aff;
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  min-height: 150px;
  padding: ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: all ${({ theme }) => theme.transition.fast};

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

const FileUploadArea = styled.div<{ $dragOver: boolean }>`
  border: 2px dashed
    ${({ $dragOver }) => ($dragOver ? "#007aff" : "rgba(0, 0, 0, 0.2)")};
  border-radius: 12px;
  padding: ${({ theme }) => theme.spacing.xl};
  text-align: center;
  background: ${({ $dragOver }) =>
    $dragOver ? "rgba(0, 122, 255, 0.05)" : "rgba(255, 255, 255, 0.5)"};
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: #007aff;
    background: rgba(0, 122, 255, 0.05);
  }

  p {
    color: rgba(0, 0, 0, 0.6);
    margin: ${({ theme }) => theme.spacing.sm} 0;
  }

  .icon {
    font-size: 48px;
    margin-bottom: ${({ theme }) => theme.spacing.md};
  }
`;

const HiddenFileInput = styled.input`
  display: none;
`;

const Button = styled.button<{ $variant?: "primary" | "secondary" }>`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.lg};
  background: ${({ $variant }) =>
    $variant === "primary" ? "#007aff" : "rgba(255, 255, 255, 0.8)"};
  color: ${({ $variant }) =>
    $variant === "primary" ? "white" : "rgba(0, 0, 0, 0.85)"};
  border: 0.5px solid
    ${({ $variant }) =>
      $variant === "primary" ? "#007aff" : "rgba(0, 0, 0, 0.2)"};
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px
      ${({ $variant }) =>
        $variant === "primary"
          ? "rgba(0, 122, 255, 0.3)"
          : "rgba(0, 0, 0, 0.1)"};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const SearchInput = styled.input`
  width: 100%;
  padding: ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-family: inherit;
  transition: all ${({ theme }) => theme.transition.fast};

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

const DocumentList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.md};
  max-height: 500px;
  overflow-y: auto;
  margin-top: ${({ theme }) => theme.spacing.lg};
`;

const DocumentItem = styled(motion.div)`
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: ${({ theme }) => theme.spacing.md};
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: ${({ theme }) => theme.spacing.md};

  &:hover {
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }
`;

const DocumentContent = styled.div`
  flex: 1;

  .doc-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: ${({ theme }) => theme.spacing.sm};
  }

  .doc-source {
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(0, 122, 255, 0.1);
    color: #007aff;
    font-weight: 600;
  }

  .doc-filename {
    font-size: 13px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
    margin-bottom: ${({ theme }) => theme.spacing.xs};
  }

  .doc-preview {
    font-size: 13px;
    color: rgba(0, 0, 0, 0.6);
    line-height: 1.5;
  }

  .doc-date {
    font-size: 11px;
    color: rgba(0, 0, 0, 0.4);
    margin-top: ${({ theme }) => theme.spacing.xs};
  }
`;

const DeleteButton = styled.button`
  background: transparent;
  border: none;
  color: #ff3b30;
  font-size: 18px;
  cursor: pointer;
  padding: ${({ theme }) => theme.spacing.xs};
  transition: all 0.2s;

  &:hover {
    transform: scale(1.1);
  }
`;

const Stats = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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

const ButtonGroup = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.md};
  margin-top: ${({ theme }) => theme.spacing.lg};
`;

interface Document {
  id: string;
  text: string;
  source: string;
  filename?: string;
  created_at: string;
  preview: string;
}

interface RagPanelProps {
  onShowToast: (message: string, type: "success" | "error" | "info") => void;
}

export default function RagPanel({ onShowToast }: RagPanelProps) {
  const [activeTab, setActiveTab] = useState<"add" | "browse" | "search">(
    "add"
  );
  const [textToAdd, setTextToAdd] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    files: 0,
    manual: 0,
    selection: 0,
  });
  const hasLoadedRef = React.useRef(false);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      loadDocuments();
    }
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8765/api/rag/documents");
      const data = await response.json();
      if (data.success) {
        setDocuments(data.documents);
        calculateStats(data.documents);
      }
    } catch (error) {
      console.error("Error loading documents:", error);
      onShowToast("Failed to load documents", "error");
    }
  };

  const calculateStats = (docs: Document[]) => {
    setStats({
      total: docs.length,
      files: docs.filter((d) => d.source === "file").length,
      manual: docs.filter((d) => d.source === "manual").length,
      selection: docs.filter((d) => d.source === "selection").length,
    });
  };

  const handleAddText = async () => {
    if (!textToAdd.trim()) {
      onShowToast("Please enter some text", "error");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8765/api/rag/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: textToAdd,
          source: "manual",
        }),
      });

      const data = await response.json();
      if (data.success) {
        onShowToast("Text added to knowledge base", "success");
        setTextToAdd("");
        loadDocuments();
      } else {
        onShowToast("Failed to add text", "error");
      }
    } catch (error) {
      console.error("Error adding text:", error);
      onShowToast("Failed to add text", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    try {
      let text: string;

      // Handle PDF files differently
      if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
        // For PDFs, we'll send the file directly to the upload endpoint
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("http://127.0.0.1:8765/api/rag/upload", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        if (data.success) {
          onShowToast(`File "${file.name}" indexed successfully`, "success");
          loadDocuments();
        } else {
          onShowToast(data.detail || "Failed to upload file", "error");
        }
        return;
      }

      // For text files, read as text
      text = await file.text();
      const response = await fetch("http://127.0.0.1:8765/api/rag/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          source: "file",
          filename: file.name,
        }),
      });

      const data = await response.json();
      if (data.success) {
        onShowToast(`File "${file.name}" indexed successfully`, "success");
        loadDocuments();
      } else {
        onShowToast("Failed to upload file", "error");
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      onShowToast("Failed to upload file", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (
      file &&
      (file.type.startsWith("text/") ||
        file.type === "application/pdf" ||
        file.name.endsWith(".pdf"))
    ) {
      handleFileUpload(file);
    } else {
      onShowToast("Please upload a text file or PDF", "error");
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      onShowToast("Please enter a search query", "error");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8765/api/rag/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: searchQuery,
          k: 10,
        }),
      });

      const data = await response.json();
      if (data.success) {
        setSearchResults(data.matches);
      } else {
        onShowToast("Search failed", "error");
      }
    } catch (error) {
      console.error("Error searching:", error);
      onShowToast("Search failed", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8765/api/rag/documents/${docId}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();
      if (data.success) {
        onShowToast("Document deleted", "success");
        loadDocuments();
      } else {
        onShowToast("Failed to delete document", "error");
      }
    } catch (error) {
      console.error("Error deleting document:", error);
      onShowToast("Failed to delete document", "error");
    }
  };

  const handleClear = async () => {
    if (!confirm("Are you sure you want to clear the entire knowledge base?")) {
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8765/api/rag/clear", {
        method: "POST",
      });

      const data = await response.json();
      if (data.success) {
        onShowToast("Knowledge base cleared", "success");
        setDocuments([]);
        setSearchResults([]);
        calculateStats([]);
      } else {
        onShowToast("Failed to clear knowledge base", "error");
      }
    } catch (error) {
      console.error("Error clearing knowledge base:", error);
      onShowToast("Failed to clear knowledge base", "error");
    }
  };

  return (
    <Container>
      <h2>Knowledge Base</h2>

      <Stats>
        <StatCard>
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Total Documents</div>
        </StatCard>
        <StatCard>
          <div className="stat-value">{stats.files}</div>
          <div className="stat-label">Files</div>
        </StatCard>
        <StatCard>
          <div className="stat-value">{stats.manual}</div>
          <div className="stat-label">Manual Entries</div>
        </StatCard>
        <StatCard>
          <div className="stat-value">{stats.selection}</div>
          <div className="stat-label">From Selections</div>
        </StatCard>
      </Stats>

      <Section>
        <TabContainer>
          <Tab
            $active={activeTab === "add"}
            onClick={() => setActiveTab("add")}
          >
            Add Content
          </Tab>
          <Tab
            $active={activeTab === "browse"}
            onClick={() => setActiveTab("browse")}
          >
            Browse ({documents.length})
          </Tab>
          <Tab
            $active={activeTab === "search"}
            onClick={() => setActiveTab("search")}
          >
            Search
          </Tab>
        </TabContainer>

        {activeTab === "add" && (
          <>
            <h3>Add Text or Upload File</h3>
            <TextArea
              placeholder="Paste or type text to add to your knowledge base..."
              value={textToAdd}
              onChange={(e) => setTextToAdd(e.target.value)}
            />
            <ButtonGroup>
              <Button
                $variant="primary"
                onClick={handleAddText}
                disabled={isLoading || !textToAdd.trim()}
              >
                {isLoading ? "Adding..." : "Add to Knowledge Base"}
              </Button>
            </ButtonGroup>

            <div style={{ marginTop: "2rem" }}>
              <h3>Or Upload a File</h3>
              <FileUploadArea
                $dragOver={dragOver}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => document.getElementById("file-input")?.click()}
              >
                <div className="icon">📄</div>
                <p>
                  <strong>Drop a file here</strong> or click to browse
                </p>
                <p style={{ fontSize: "12px", opacity: 0.6 }}>
                  Supports .txt, .md, .json, .pdf, and other text files
                </p>
              </FileUploadArea>
              <HiddenFileInput
                id="file-input"
                type="file"
                accept=".txt,.md,.json,.csv,.log,.pdf"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileUpload(file);
                }}
              />
            </div>
          </>
        )}

        {activeTab === "browse" && (
          <>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <h3>All Documents</h3>
              {documents.length > 0 && (
                <Button onClick={handleClear}>Clear All</Button>
              )}
            </div>
            {documents.length === 0 ? (
              <p style={{ textAlign: "center", color: "rgba(0,0,0,0.5)" }}>
                No documents yet. Add some content to get started!
              </p>
            ) : (
              <DocumentList>
                <AnimatePresence>
                  {documents.map((doc) => (
                    <DocumentItem
                      key={doc.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                    >
                      <DocumentContent>
                        <div className="doc-header">
                          <span className="doc-source">{doc.source}</span>
                        </div>
                        {doc.filename && (
                          <div className="doc-filename">📄 {doc.filename}</div>
                        )}
                        <div className="doc-preview">{doc.preview}</div>
                        <div className="doc-date">
                          {new Date(doc.created_at).toLocaleString()}
                        </div>
                      </DocumentContent>
                      <DeleteButton onClick={() => handleDelete(doc.id)}>
                        ×
                      </DeleteButton>
                    </DocumentItem>
                  ))}
                </AnimatePresence>
              </DocumentList>
            )}
          </>
        )}

        {activeTab === "search" && (
          <>
            <h3>Search Knowledge Base</h3>
            <SearchInput
              placeholder="Search for documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSearch()}
            />
            <ButtonGroup>
              <Button
                $variant="primary"
                onClick={handleSearch}
                disabled={isLoading || !searchQuery.trim()}
              >
                {isLoading ? "Searching..." : "Search"}
              </Button>
            </ButtonGroup>

            {searchResults.length > 0 && (
              <DocumentList>
                {searchResults.map((result, index) => (
                  <DocumentItem
                    key={result.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <DocumentContent>
                      <div className="doc-header">
                        <span className="doc-source">{result.source}</span>
                        <span
                          style={{
                            fontSize: "12px",
                            color: "#34c759",
                            fontWeight: 600,
                          }}
                        >
                          {(result.score * 100).toFixed(0)}% match
                        </span>
                      </div>
                      {result.filename && (
                        <div className="doc-filename">📄 {result.filename}</div>
                      )}
                      <div className="doc-preview">{result.preview}</div>
                    </DocumentContent>
                  </DocumentItem>
                ))}
              </DocumentList>
            )}
          </>
        )}
      </Section>
    </Container>
  );
}
