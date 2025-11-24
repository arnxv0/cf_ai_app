import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { motion, AnimatePresence } from "framer-motion";

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
    display: flex;
    align-items: center;
    gap: ${({ theme }) => theme.spacing.sm};
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.md};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
`;

const Button = styled.button<{ $variant?: "primary" | "secondary" | "danger" }>`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.lg};
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all ${({ theme }) => theme.transition.fast};
  border: none;
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};

  ${({ $variant = "primary" }) => {
    if ($variant === "primary") {
      return `
        background: #007AFF;
        color: white;
        &:hover {
          background: #0051D5;
        }
      `;
    } else if ($variant === "danger") {
      return `
        background: #FF3B30;
        color: white;
        &:hover {
          background: #D70015;
        }
      `;
    } else {
      return `
        background: rgba(0, 0, 0, 0.05);
        color: rgba(0, 0, 0, 0.75);
        &:hover {
          background: rgba(0, 0, 0, 0.1);
        }
      `;
    }
  }}

  .material-icons {
    font-size: 18px;
  }
`;

const VarList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.md};
`;

const VarItem = styled(motion.div)`
  display: grid;
  grid-template-columns: 200px 1fr auto auto;
  gap: ${({ theme }) => theme.spacing.md};
  padding: ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  align-items: center;
`;

const VarKey = styled.div`
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-family: "Monaco", "Courier New", monospace;
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
`;

const VarValue = styled.div`
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
  font-family: "Monaco", "Courier New", monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const Badge = styled.span`
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: rgba(255, 149, 0, 0.15);
  color: #ff9500;
`;

const IconButton = styled.button`
  background: transparent;
  border: none;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.5);
  transition: color ${({ theme }) => theme.transition.fast};
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    color: rgba(0, 0, 0, 0.85);
  }

  .material-icons {
    font-size: 18px;
  }
`;

const FormGroup = styled.div`
  margin-bottom: ${({ theme }) => theme.spacing.md};
`;

const FormLabel = styled.label`
  display: block;
  margin-bottom: ${({ theme }) => theme.spacing.sm};
  font-weight: 500;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.75);
`;

const FormControl = styled.input`
  width: 100%;
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.md};
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

const TextArea = styled.textarea`
  width: 100%;
  min-height: 200px;
  padding: ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-family: "Monaco", "Courier New", monospace;
  transition: all ${({ theme }) => theme.transition.fast};
  resize: vertical;

  &:focus {
    outline: none;
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
    background: rgba(255, 255, 255, 0.95);
  }
`;

const Checkbox = styled.label`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  font-size: 14px;
  color: rgba(0, 0, 0, 0.75);
  cursor: pointer;

  input[type="checkbox"] {
    cursor: pointer;
    accent-color: #007aff;
  }
`;

const Modal = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
`;

const ModalContent = styled(motion.div)`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(40px);
  border-radius: 16px;
  padding: ${({ theme }) => theme.spacing.xl};
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);

  h3 {
    margin-bottom: ${({ theme }) => theme.spacing.lg};
    color: rgba(0, 0, 0, 0.85);
  }
`;

const CategoryBadge = styled.div`
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(0, 122, 255, 0.15);
  color: #007aff;
  margin-left: ${({ theme }) => theme.spacing.sm};
`;

interface EnvVar {
  category: string;
  key: string;
  value: string;
  is_secret: boolean;
}

interface EnvVarsPanelProps {
  onShowToast: (message: string, type: "success" | "error" | "info") => void;
}

export default function EnvVarsPanel({ onShowToast }: EnvVarsPanelProps) {
  const [variables, setVariables] = useState<
    Record<string, Record<string, string>>
  >({});
  const [categories, setCategories] = useState<string[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [newVar, setNewVar] = useState<EnvVar>({
    category: "api_keys",
    key: "",
    value: "",
    is_secret: false,
  });
  const [importContent, setImportContent] = useState("");
  const [importCategory, setImportCategory] = useState("imported");
  const hasLoadedRef = React.useRef(false);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      loadCategories();
    }
  }, []);

  const loadCategories = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8765/api/settings/categories"
      );
      const data = await response.json();
      const cats = data.categories || [];
      setCategories(cats);

      // Load all categories
      for (const category of cats) {
        await loadCategory(category);
      }
    } catch (error) {
      console.error("Error loading categories:", error);
      onShowToast("Failed to load categories", "error");
    }
  };

  const loadCategory = async (category: string) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8765/api/settings/${category}?include_secrets=true`
      );
      const data = await response.json();
      setVariables((prev) => ({
        ...prev,
        [category]: data.settings || {},
      }));
    } catch (error) {
      console.error(`Error loading category ${category}:`, error);
    }
  };

  const handleAddVariable = async () => {
    if (!newVar.key || !newVar.value) {
      onShowToast("Please fill in all fields", "error");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8765/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newVar),
      });

      if (response.ok) {
        onShowToast("Variable added successfully", "success");
        setShowAddModal(false);
        setNewVar({
          category: "api_keys",
          key: "",
          value: "",
          is_secret: false,
        });
        loadCategories();
      } else {
        onShowToast("Failed to add variable", "error");
      }
    } catch (error) {
      console.error("Error adding variable:", error);
      onShowToast("Failed to add variable", "error");
    }
  };

  const handleDeleteVariable = async (category: string, key: string) => {
    if (!confirm(`Delete ${key}?`)) return;

    try {
      console.log(`Deleting ${category}/${key}...`);
      const url = `http://127.0.0.1:8765/api/settings/${category}/${key}`;
      console.log("DELETE URL:", url);

      const response = await fetch(url, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      console.log("Response status:", response.status);
      const responseData = await response.json();
      console.log("Response data:", responseData);

      if (response.ok) {
        onShowToast("Variable deleted", "success");
        loadCategories();
      } else {
        onShowToast("Failed to delete variable", "error");
      }
    } catch (error) {
      console.error("Error deleting variable:", error);
      onShowToast("Failed to delete variable", "error");
    }
  };

  const handleImport = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8765/api/settings/import",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: importContent,
            category: importCategory,
          }),
        }
      );

      const data = await response.json();
      if (response.ok) {
        onShowToast(`Imported ${data.count} variables`, "success");
        setShowImportModal(false);
        setImportContent("");
        loadCategories();
      } else {
        onShowToast("Failed to import", "error");
      }
    } catch (error) {
      console.error("Error importing:", error);
      onShowToast("Failed to import", "error");
    }
  };

  const handleExport = async (category: string) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8765/api/settings/export/${category}`
      );
      const data = await response.json();

      if (response.ok) {
        // Download as file
        const blob = new Blob([data.content], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${category}.env`;
        a.click();
        URL.revokeObjectURL(url);
        onShowToast("Exported successfully", "success");
      }
    } catch (error) {
      console.error("Error exporting:", error);
      onShowToast("Failed to export", "error");
    }
  };

  return (
    <PanelContainer>
      <Header>
        <h2>Environment Variables</h2>
        <p>
          Manage your API keys and configuration securely with encrypted storage
        </p>
      </Header>

      <ButtonGroup>
        <Button $variant="primary" onClick={() => setShowAddModal(true)}>
          <span className="material-icons">add</span>
          Add Variable
        </Button>
        <Button $variant="secondary" onClick={() => setShowImportModal(true)}>
          <span className="material-icons">upload_file</span>
          Import .env
        </Button>
      </ButtonGroup>

      {categories.length === 0 ? (
        <Section>
          <p style={{ textAlign: "center", color: "rgba(0, 0, 0, 0.5)" }}>
            No environment variables set. Click "Add Variable" to get started.
          </p>
        </Section>
      ) : (
        categories.map((category) => (
          <Section key={category}>
            <h3>
              <span className="material-icons">folder</span>
              {category}
              <CategoryBadge>
                {Object.keys(variables[category] || {}).length} vars
              </CategoryBadge>
              <div style={{ marginLeft: "auto" }}>
                <IconButton
                  onClick={() => handleExport(category)}
                  title="Export"
                >
                  <span className="material-icons">download</span>
                </IconButton>
              </div>
            </h3>
            <VarList>
              {Object.entries(variables[category] || {}).map(([key, value]) => (
                <VarItem
                  key={key}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <VarKey>
                    {key}
                    {value === "********" && <Badge>SECRET</Badge>}
                  </VarKey>
                  <VarValue>{value}</VarValue>
                  <IconButton
                    onClick={() => {
                      navigator.clipboard.writeText(
                        value !== "********" ? value : ""
                      );
                      onShowToast("Copied to clipboard", "info");
                    }}
                    title="Copy"
                  >
                    <span className="material-icons">content_copy</span>
                  </IconButton>
                  <IconButton
                    onClick={() => handleDeleteVariable(category, key)}
                    title="Delete"
                  >
                    <span className="material-icons">delete</span>
                  </IconButton>
                </VarItem>
              ))}
            </VarList>
          </Section>
        ))
      )}

      {/* Add Variable Modal */}
      <AnimatePresence>
        {showAddModal && (
          <Modal
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAddModal(false)}
          >
            <ModalContent
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3>Add Environment Variable</h3>
              <FormGroup>
                <FormLabel>Category</FormLabel>
                <FormControl
                  value={newVar.category}
                  onChange={(e) =>
                    setNewVar({ ...newVar, category: e.target.value })
                  }
                  placeholder="e.g., api_keys, email, database"
                />
              </FormGroup>
              <FormGroup>
                <FormLabel>Key</FormLabel>
                <FormControl
                  value={newVar.key}
                  onChange={(e) =>
                    setNewVar({ ...newVar, key: e.target.value })
                  }
                  placeholder="e.g., GOOGLE_API_KEY"
                />
              </FormGroup>
              <FormGroup>
                <FormLabel>Value</FormLabel>
                <FormControl
                  type={newVar.is_secret ? "password" : "text"}
                  value={newVar.value}
                  onChange={(e) =>
                    setNewVar({ ...newVar, value: e.target.value })
                  }
                  placeholder="Enter value"
                />
              </FormGroup>
              <FormGroup>
                <Checkbox>
                  <input
                    type="checkbox"
                    checked={newVar.is_secret}
                    onChange={(e) =>
                      setNewVar({ ...newVar, is_secret: e.target.checked })
                    }
                  />
                  This is a secret value (encrypt in database)
                </Checkbox>
              </FormGroup>
              <ButtonGroup>
                <Button $variant="primary" onClick={handleAddVariable}>
                  Add Variable
                </Button>
                <Button
                  $variant="secondary"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </Button>
              </ButtonGroup>
            </ModalContent>
          </Modal>
        )}
      </AnimatePresence>

      {/* Import Modal */}
      <AnimatePresence>
        {showImportModal && (
          <Modal
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowImportModal(false)}
          >
            <ModalContent
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3>Import from .env File</h3>
              <FormGroup>
                <FormLabel>Category</FormLabel>
                <FormControl
                  value={importCategory}
                  onChange={(e) => setImportCategory(e.target.value)}
                  placeholder="Category for imported variables"
                />
              </FormGroup>
              <FormGroup>
                <FormLabel>Paste .env content</FormLabel>
                <TextArea
                  value={importContent}
                  onChange={(e) => setImportContent(e.target.value)}
                  placeholder="GOOGLE_API_KEY=your_key_here&#10;SMTP_HOST=smtp.gmail.com&#10;..."
                />
              </FormGroup>
              <ButtonGroup>
                <Button $variant="primary" onClick={handleImport}>
                  Import
                </Button>
                <Button
                  $variant="secondary"
                  onClick={() => setShowImportModal(false)}
                >
                  Cancel
                </Button>
              </ButtonGroup>
            </ModalContent>
          </Modal>
        )}
      </AnimatePresence>
    </PanelContainer>
  );
}
