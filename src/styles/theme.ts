export const theme = {
  colors: {
    primaryLight: "#FFFFFF",
    secondaryLight: "#F5F5F7",
    secondaryDark: "#2C2C2E",
    tertiaryLight: "#E8E8ED",
    textDark: "#1D1D1F",
    textGray: "#86868B",
    accentBlue: "#007AFF",
    accentNeon: "#00D9FF",
    errorRed: "#FF3B30",
    successGreen: "#34C759",
  },

  spacing: {
    xs: "4px",
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "32px",
  },

  radius: {
    sm: "4px",
    md: "8px",
    lg: "12px",
  },

  shadow: {
    sm: "0 1px 3px rgba(0, 0, 0, 0.08)",
    md: "0 4px 12px rgba(0, 0, 0, 0.1)",
    lg: "0 8px 24px rgba(0, 0, 0, 0.12)",
  },

  transition: {
    fast: "0.15s ease",
    normal: "0.25s ease",
  },
};

export type Theme = typeof theme;
