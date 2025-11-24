import { createGlobalStyle } from "styled-components";
import { Theme } from "./theme";

export const GlobalStyles = createGlobalStyle<{ theme: Theme }>`
  @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html, body {
    background: transparent;
    height: 100%;
    width: 100%;
  }

  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: ${({ theme }) => theme.colors.textDark};
    overflow: hidden;
    background: transparent;
  }
  
  #root {
    height: 100%;
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
    background: ${({ theme }) => theme.colors.primaryLight};
  }
  
  /* For overlay window, use white background with high contrast */
  body.overlay-window #root {
    background: #ffffff;
  }
  
  body.overlay-window {
    background: transparent;
  }

  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  ::-webkit-scrollbar-track {
    background: ${({ theme }) => theme.colors.secondaryLight};
  }

  ::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.colors.textGray};
    border-radius: 3px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: ${({ theme }) => theme.colors.accentBlue};
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;
