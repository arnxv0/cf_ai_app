import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";

interface Settings {
  launchAtStartup: boolean;
  showMenuBar: boolean;
  primaryHotkey: string;
  screenshotHotkey: string;
  responseStyle: string;
  cursorColor: string;
}

const DEFAULT_SETTINGS: Settings = {
  launchAtStartup: false,
  showMenuBar: true,
  primaryHotkey: "⌘+Shift+K",
  screenshotHotkey: "⌘+Shift+S",
  responseStyle: "professional",
  cursorColor: "#00FFFF",
};

export function useSettings() {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const savedSettings = await invoke<Settings>("load_settings");
      setSettings({ ...DEFAULT_SETTINGS, ...savedSettings });
    } catch (error) {
      console.error("Failed to load settings:", error);
    }
  };

  const updateSettings = async (key: string, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);

    try {
      await invoke("save_settings", { settings: newSettings });
    } catch (error) {
      console.error("Failed to save settings:", error);
    }
  };

  return { settings, updateSettings };
}
