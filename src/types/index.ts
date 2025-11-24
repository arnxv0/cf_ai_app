export interface Module {
  id: string;
  name: string;
  icon: string;
}

export interface Settings {
  launchAtStartup: boolean;
  showMenuBar: boolean;
  primaryHotkey: string;
  screenshotHotkey: string;
  responseStyle: string;
  cursorColor: string;
}

export interface ToastMessage {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info';
}

export interface HotkeyEvent {
  mode: 'text' | 'screenshot' | 'inline';
  position: { x: number; y: number };
  selectedText?: string;
  screenshot?: string;
}
