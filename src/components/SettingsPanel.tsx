import { motion } from "framer-motion";
import styled from "styled-components";
import CalendarPanel from "./CalendarPanel";
import CloudflarePanel from "./CloudflarePanel";
import EnvVarsPanel from "./EnvVarsPanel";
import HotkeyPanel from "./HotkeyPanel";
import RagPanel from "./RagPanel";
import StoragePanel from "./StoragePanel";
import TadataPanel from "./TadataPanel";

const RightPanel = styled(motion.div)`
  flex: 1;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  overflow-y: auto;
  padding: ${({ theme }) => theme.spacing.xl};
`;

const SettingsContent = styled.div`
  h2 {
    font-size: 28px;
    margin-bottom: ${({ theme }) => theme.spacing.xl};
    color: rgba(0, 0, 0, 0.85);
    font-weight: 600;
  }

  p {
    color: rgba(0, 0, 0, 0.6);
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

const FormGroup = styled.div`
  margin-bottom: ${({ theme }) => theme.spacing.lg};
`;

const FormLabel = styled.label`
  display: block;
  margin-bottom: ${({ theme }) => theme.spacing.sm};
  font-weight: 500;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};

  input[type="checkbox"] {
    width: auto;
    cursor: pointer;
    accent-color: #007aff;
  }
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

const Select = styled.select`
  width: 100%;
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-family: inherit;
  transition: all ${({ theme }) => theme.transition.fast};
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
    background: rgba(255, 255, 255, 0.95);
  }

  option {
    background: rgba(255, 255, 255, 0.95);
  }
`;

const PluginList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.md};
`;

const PluginItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  color: rgba(0, 0, 0, 0.85);
`;

const Status = styled.span<{ $type: "success" | "not-installed" }>`
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  background: ${({ $type }) =>
    $type === "success"
      ? "rgba(52, 199, 89, 0.15)"
      : "rgba(255, 59, 48, 0.15)"};
  color: ${({ $type }) => ($type === "success" ? "#34C759" : "#FF3B30")};
`;

interface SettingsPanelProps {
  activeModule: string;
  settings: any;
  onSettingsChange: (key: string, value: any) => void;
  onShowToast: (message: string, type: "success" | "error" | "info") => void;
}

export default function SettingsPanel({
  activeModule,
  settings,
  onSettingsChange,
  onShowToast,
}: SettingsPanelProps) {
  const renderModuleContent = () => {
    switch (activeModule) {
      case "general":
        return (
          <SettingsContent>
            <h2>General Settings</h2>
            <Section>
              <h3>Application Behavior</h3>
              <FormGroup>
                <FormLabel>
                  <input
                    type="checkbox"
                    checked={settings.launchAtStartup}
                    onChange={(e) =>
                      onSettingsChange("launchAtStartup", e.target.checked)
                    }
                  />
                  Launch at Startup
                </FormLabel>
              </FormGroup>
              <FormGroup>
                <FormLabel>
                  <input
                    type="checkbox"
                    checked={settings.showMenuBar}
                    onChange={(e) =>
                      onSettingsChange("showMenuBar", e.target.checked)
                    }
                  />
                  Show Menu Bar Icon
                </FormLabel>
              </FormGroup>
            </Section>
          </SettingsContent>
        );

      case "hotkey":
        return <HotkeyPanel onShowToast={onShowToast} />;

      case "rag":
        return <RagPanel onShowToast={onShowToast} />;

      case "calendar":
        return <CalendarPanel onShowToast={onShowToast} />;

      case "tadata":
        return <TadataPanel />;

      case "cloudflare":
        return <CloudflarePanel onShowToast={onShowToast} />;

      case "hotkeys":
        return (
          <SettingsContent>
            <h2>Hotkey Configuration</h2>
            <Section>
              <h3>Global Shortcuts</h3>
              <FormGroup>
                <FormLabel>Primary Hotkey</FormLabel>
                <FormControl
                  type="text"
                  value={settings.primaryHotkey}
                  onChange={(e) =>
                    onSettingsChange("primaryHotkey", e.target.value)
                  }
                  placeholder="⌘+Shift+K"
                />
              </FormGroup>
              <FormGroup>
                <FormLabel>Screenshot Hotkey</FormLabel>
                <FormControl
                  type="text"
                  value={settings.screenshotHotkey}
                  onChange={(e) =>
                    onSettingsChange("screenshotHotkey", e.target.value)
                  }
                  placeholder="⌘+Shift+S"
                />
              </FormGroup>
            </Section>
          </SettingsContent>
        );

      case "env":
        return <EnvVarsPanel onShowToast={onShowToast} />;

      case "storage":
        return <StoragePanel onShowToast={onShowToast} />;

      case "plugins":
        return (
          <SettingsContent>
            <h2>Plugin Manager</h2>
            <Section>
              <h3>Installed Plugins</h3>
              <PluginList>
                {["Gmail"].map((plugin) => (
                  <PluginItem key={plugin}>
                    <span>{plugin}</span>
                    <Status $type="success">Active</Status>
                  </PluginItem>
                ))}
                {["VS Code", "Notion", "Slack"].map((plugin) => (
                  <PluginItem key={plugin}>
                    <span>{plugin}</span>
                    <Status $type="not-installed">Not installed</Status>
                  </PluginItem>
                ))}
              </PluginList>
            </Section>
          </SettingsContent>
        );

      default:
        return (
          <SettingsContent>
            <h2>{activeModule}</h2>
            <p>Configuration options for {activeModule} coming soon...</p>
          </SettingsContent>
        );
    }
  };

  return (
    <RightPanel
      key={activeModule}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      {renderModuleContent()}
    </RightPanel>
  );
}
