import { useEffect } from 'react';

interface HotkeyOptions {
  key: string;
  modifiers?: ('ctrl' | 'shift' | 'alt' | 'meta')[];
  callback: () => void;
}

export function useHotkey({ key, modifiers = [], callback }: HotkeyOptions) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const hasCtrl = !modifiers.includes('ctrl') || event.ctrlKey;
      const hasShift = !modifiers.includes('shift') || event.shiftKey;
      const hasAlt = !modifiers.includes('alt') || event.altKey;
      const hasMeta = !modifiers.includes('meta') || event.metaKey;

      if (
        event.key.toLowerCase() === key.toLowerCase() &&
        hasCtrl &&
        hasShift &&
        hasAlt &&
        hasMeta
      ) {
        event.preventDefault();
        callback();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [key, modifiers, callback]);
}
