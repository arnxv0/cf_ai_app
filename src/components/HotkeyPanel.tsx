import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { motion } from "framer-motion";

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

  p {
    font-size: 14px;
    color: rgba(0, 0, 0, 0.6);
    margin-bottom: ${({ theme }) => theme.spacing.lg};
    line-height: 1.6;
  }
`;

const HotkeyBuilder = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.lg};
`;

const ModifierGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.sm};
`;

const Label = styled.label`
  font-size: 14px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.75);
  margin-bottom: ${({ theme }) => theme.spacing.xs};
`;

const ModifierButtons = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.sm};
  flex-wrap: wrap;
`;

const ModifierButton = styled.button<{ $active: boolean }>`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.md};
  background: ${({ $active }) =>
    $active ? "rgba(0, 122, 255, 0.15)" : "rgba(255, 255, 255, 0.8)"};
  border: 1.5px solid
    ${({ $active }) => ($active ? "#007aff" : "rgba(0, 0, 0, 0.2)")};
  border-radius: 8px;
  color: ${({ $active }) => ($active ? "#007aff" : "rgba(0, 0, 0, 0.85)")};
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all ${({ theme }) => theme.transition.fast};
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro", "Segoe UI",
    sans-serif;

  &:hover {
    background: ${({ $active }) =>
      $active ? "rgba(0, 122, 255, 0.25)" : "rgba(255, 255, 255, 1)"};
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  &:active {
    transform: translateY(0);
  }
`;

const KeyInput = styled.input`
  width: 100px;
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  text-transform: uppercase;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro", "Segoe UI",
    monospace;
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

const Preview = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: ${({ theme }) => theme.spacing.xl};
  background: rgba(0, 122, 255, 0.05);
  border: 2px dashed rgba(0, 122, 255, 0.3);
  border-radius: 12px;
  margin: ${({ theme }) => theme.spacing.lg} 0;
`;

const PreviewKeys = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  font-size: 20px;
  font-weight: 600;
  color: #007aff;
`;

const Key = styled.span`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.9);
  border: 1.5px solid rgba(0, 122, 255, 0.4);
  border-radius: 8px;
  min-width: 40px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const Plus = styled.span`
  color: rgba(0, 122, 255, 0.6);
  font-weight: 400;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: ${({ theme }) => theme.spacing.md};
  margin-top: ${({ theme }) => theme.spacing.lg};
`;

const Button = styled(motion.button)<{ $variant?: "primary" | "secondary" }>`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.lg};
  background: ${({ $variant }) =>
    $variant === "primary"
      ? "linear-gradient(135deg, #007aff 0%, #0051d5 100%)"
      : "rgba(255, 255, 255, 0.8)"};
  color: ${({ $variant }) =>
    $variant === "primary" ? "white" : "rgba(0, 0, 0, 0.85)"};
  border: ${({ $variant }) =>
    $variant === "primary" ? "none" : "0.5px solid rgba(0, 0, 0, 0.2)"};
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all ${({ theme }) => theme.transition.fast};
  font-family: inherit;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const InfoBox = styled.div`
  background: rgba(255, 193, 7, 0.1);
  border-left: 3px solid #ffc107;
  padding: ${({ theme }) => theme.spacing.md};
  border-radius: 8px;
  margin-top: ${({ theme }) => theme.spacing.lg};
  font-size: 13px;
  color: rgba(0, 0, 0, 0.7);
  line-height: 1.6;
`;

interface HotkeyPanelProps {
  onShowToast: (message: string, type: "success" | "error" | "info") => void;
}

interface HotkeyConfig {
  modifiers: string[];
  key: string;
  inline_modifiers: string[];
  inline_key: string;
}

const AVAILABLE_MODIFIERS = [
  { id: "cmd", label: "⌘ Cmd" },
  { id: "ctrl", label: "⌃ Ctrl" },
  { id: "alt", label: "⌥ Alt" },
  { id: "shift", label: "⇧ Shift" },
];

export default function HotkeyPanel({ onShowToast }: HotkeyPanelProps) {
  const [hotkey, setHotkey] = useState<HotkeyConfig>({
    modifiers: ["cmd", "shift"],
    key: "k",
    inline_modifiers: ["cmd", "shift"],
    inline_key: "l",
  });
  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const hasLoadedRef = React.useRef(false);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      loadHotkey();
    }
  }, []);

  const loadHotkey = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8765/api/hotkey");
      if (response.ok) {
        const data = await response.json();
        setHotkey(data);
      }
    } catch (error) {
      console.error("Failed to load hotkey:", error);
      onShowToast("Failed to load hotkey configuration", "error");
    }
  };

  const toggleModifier = (modifierId: string, isInline: boolean = false) => {
    setHotkey((prev) => {
      const field = isInline ? "inline_modifiers" : "modifiers";
      const currentModifiers = prev[field];
      const newModifiers = currentModifiers.includes(modifierId)
        ? currentModifiers.filter((m) => m !== modifierId)
        : [...currentModifiers, modifierId];

      return { ...prev, [field]: newModifiers };
    });
    setHasChanges(true);
  };

  const handleKeyChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    isInline: boolean = false
  ) => {
    const value = e.target.value.toLowerCase();
    if (value.length <= 1 && /^[a-z]?$/.test(value)) {
      const field = isInline ? "inline_key" : "key";
      setHotkey((prev) => ({ ...prev, [field]: value }));
      setHasChanges(true);
    }
  };

  const handleSave = async () => {
    if (hotkey.modifiers.length === 0 || hotkey.inline_modifiers.length === 0) {
      onShowToast(
        "Please select at least one modifier key for each hotkey",
        "error"
      );
      return;
    }

    if (!hotkey.key || !hotkey.inline_key) {
      onShowToast("Please enter a key for each hotkey", "error");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8765/api/hotkey", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(hotkey),
      });

      if (response.ok) {
        onShowToast("Hotkeys updated successfully! 🎉", "success");
        setHasChanges(false);
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update hotkeys");
      }
    } catch (error: any) {
      console.error("Failed to save hotkeys:", error);
      onShowToast(error.message || "Failed to update hotkeys", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8765/api/hotkey/reset", {
        method: "POST",
      });

      if (response.ok) {
        const data = await response.json();
        setHotkey(data.hotkey);
        onShowToast("Hotkeys reset to default", "success");
        setHasChanges(false);
      } else {
        throw new Error("Failed to reset hotkeys");
      }
    } catch (error) {
      console.error("Failed to reset hotkeys:", error);
      onShowToast("Failed to reset hotkeys", "error");
    } finally {
      setLoading(false);
    }
  };

  const formatHotkeyDisplay = (isInline: boolean = false) => {
    const mods = isInline ? hotkey.inline_modifiers : hotkey.modifiers;
    const key = isInline ? hotkey.inline_key : hotkey.key;

    const modifierLabels = mods
      .map((m) => AVAILABLE_MODIFIERS.find((mod) => mod.id === m)?.label || m)
      .map((label) => label.split(" ")[0]); // Get just the symbol

    return [...modifierLabels, key.toUpperCase()];
  };

  return (
    <Container>
      <h2>Hotkey Configuration</h2>

      <Section>
        <h3>🪟 Popup Mode Hotkey</h3>
        <p>
          Opens the overlay window anywhere on screen - works with selected
          text, screenshots, and context.
        </p>

        <HotkeyBuilder>
          <ModifierGroup>
            <Label>Modifier Keys (choose at least one)</Label>
            <ModifierButtons>
              {AVAILABLE_MODIFIERS.map((mod) => (
                <ModifierButton
                  key={mod.id}
                  $active={hotkey.modifiers.includes(mod.id)}
                  onClick={() => toggleModifier(mod.id, false)}
                >
                  {mod.label}
                </ModifierButton>
              ))}
            </ModifierButtons>
          </ModifierGroup>

          <ModifierGroup>
            <Label>Main Key (single letter)</Label>
            <KeyInput
              type="text"
              value={hotkey.key}
              onChange={(e) => handleKeyChange(e, false)}
              placeholder="K"
              maxLength={1}
            />
          </ModifierGroup>
        </HotkeyBuilder>

        <Preview>
          <PreviewKeys>
            {formatHotkeyDisplay(false).map((key, index) => (
              <span key={index}>
                {index > 0 && <Plus>+</Plus>}
                <Key>{key}</Key>
              </span>
            ))}
          </PreviewKeys>
        </Preview>
      </Section>

      <Section>
        <h3>⚡ Inline Mode Hotkey</h3>
        <p>
          Works directly in text fields and terminals - press once to start
          typing your query, press again to execute and get AI response typed
          directly.
        </p>

        <HotkeyBuilder>
          <ModifierGroup>
            <Label>Modifier Keys (choose at least one)</Label>
            <ModifierButtons>
              {AVAILABLE_MODIFIERS.map((mod) => (
                <ModifierButton
                  key={mod.id}
                  $active={hotkey.inline_modifiers.includes(mod.id)}
                  onClick={() => toggleModifier(mod.id, true)}
                >
                  {mod.label}
                </ModifierButton>
              ))}
            </ModifierButtons>
          </ModifierGroup>

          <ModifierGroup>
            <Label>Main Key (single letter)</Label>
            <KeyInput
              type="text"
              value={hotkey.inline_key}
              onChange={(e) => handleKeyChange(e, true)}
              placeholder="L"
              maxLength={1}
            />
          </ModifierGroup>
        </HotkeyBuilder>

        <Preview>
          <PreviewKeys>
            {formatHotkeyDisplay(true).map((key, index) => (
              <span key={index}>
                {index > 0 && <Plus>+</Plus>}
                <Key>{key}</Key>
              </span>
            ))}
          </PreviewKeys>
        </Preview>

        <ButtonGroup>
          <Button
            $variant="primary"
            onClick={handleSave}
            disabled={loading || !hasChanges}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? "Saving..." : "Apply Hotkeys"}
          </Button>
          <Button
            $variant="secondary"
            onClick={handleReset}
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Reset to Defaults
          </Button>
        </ButtonGroup>

        <InfoBox>
          ℹ️ Both hotkeys will be updated immediately after saving. You don't
          need to restart the application.
        </InfoBox>
      </Section>
    </Container>
  );
}
