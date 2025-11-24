import { useState, useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { AnimatePresence } from "framer-motion";
import { ThemeProvider } from "styled-components";
import styled from "styled-components";
import Sidebar from "./components/Sidebar";
import SettingsPanel from "./components/SettingsPanel";
import Toast from "./components/Toast";
import { useSettings } from "./hooks/useSettings";
import { theme } from "./styles/theme";
import { GlobalStyles } from "./styles/GlobalStyles";

interface ToastMessage {
  id: number;
  message: string;
  type: "success" | "error" | "info";
}

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background: ${({ theme }) => theme.colors.primaryLight};
`;

const TopBar = styled.div`
  background: ${({ theme }) => theme.colors.primaryLight};
  border-bottom: 1px solid ${({ theme }) => theme.colors.tertiaryLight};
  display: flex;
  flex-direction: column;
  padding: ${({ theme }) => theme.spacing.lg} ${({ theme }) => theme.spacing.xl};
  box-shadow: ${({ theme }) => theme.shadow.sm};
  z-index: 100;
`;

const TopRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${({ theme }) => theme.spacing.sm};
`;

const BottomRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.md};
  font-size: 24px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.textDark};
`;

const PoweredBy = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  font-size: 14px;
  color: ${({ theme }) => theme.colors.textGray};
`;

const Highlight = styled.span`
  color: ${({ theme }) => theme.colors.accentBlue};
  font-weight: 600;
`;

const ConnectionStatus = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
`;

const StatusDot = styled.div<{ $isActive: boolean }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${({ theme, $isActive }) =>
    $isActive ? theme.colors.successGreen : theme.colors.errorRed};
  animation: ${({ $isActive }) => ($isActive ? "pulse 2s infinite" : "none")};
`;

const MainContent = styled.div`
  display: flex;
  flex: 1;
  overflow: hidden;
`;

const ToastContainer = styled.div`
  position: fixed;
  bottom: ${({ theme }) => theme.spacing.xl};
  right: ${({ theme }) => theme.spacing.xl};
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.sm};
`;

function App() {
  const [activeModule, setActiveModule] = useState("general");
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const { settings, updateSettings } = useSettings();

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    let healthCheckTimeout: NodeJS.Timeout | undefined;
    let currentDelay = 5000; // Start with 5 seconds
    const maxDelay = 30000; // Max 30 seconds

    // Listen for WebSocket connection events from Rust
    listen<{ connected: boolean }>("backend-connection", (event) => {
      setIsConnected(event.payload.connected);

      // If connected, clear any pending health check
      if (event.payload.connected) {
        currentDelay = 5000; // Reset delay
        if (healthCheckTimeout) {
          clearTimeout(healthCheckTimeout);
          healthCheckTimeout = undefined;
        }
      } else {
        // If disconnected, start fallback health check
        scheduleHealthCheck();
      }
    }).then((unlistenFn) => {
      unlisten = unlistenFn;
    });

    // Fallback HTTP health check with exponential backoff (only when disconnected)
    // Note: Initial check may fail if backend is still starting, but WebSocket
    // events will update status once backend is ready
    const checkBackendHealth = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8765/api/health");
        if (response.ok) {
          setIsConnected(true);
          currentDelay = 5000; // Reset delay on successful connection
        } else {
          setIsConnected(false);
          currentDelay = Math.min(currentDelay * 2, maxDelay);
          scheduleHealthCheck();
        }
      } catch (error) {
        setIsConnected(false);
        currentDelay = Math.min(currentDelay * 2, maxDelay);
        scheduleHealthCheck();
      }
    };

    const scheduleHealthCheck = () => {
      if (healthCheckTimeout) clearTimeout(healthCheckTimeout);
      healthCheckTimeout = setTimeout(checkBackendHealth, currentDelay);
    };

    // Initial check after 1 second
    setTimeout(checkBackendHealth, 1000);

    return () => {
      if (unlisten) unlisten();
      if (healthCheckTimeout) clearTimeout(healthCheckTimeout);
    };
  }, []);

  const showToast = (message: string, type: ToastMessage["type"]) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyles theme={theme} />
      <AppContainer>
        <TopBar>
          <TopRow>
            <Logo>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2L2 7L12 12L22 7L12 2Z"
                  fill={theme.colors.accentBlue}
                />
                <path
                  d="M2 17L12 22L22 17"
                  stroke={theme.colors.accentBlue}
                  strokeWidth="2"
                />
              </svg>
              <span>Arrow - AI Anywhere</span>
            </Logo>
            <ConnectionStatus>
              <StatusDot $isActive={isConnected} />
              <span>{isConnected ? "Connected" : "Disconnected"}</span>
            </ConnectionStatus>
          </TopRow>
        </TopBar>

        <MainContent>
          <Sidebar
            activeModule={activeModule}
            onModuleChange={setActiveModule}
          />
          <SettingsPanel
            activeModule={activeModule}
            settings={settings}
            onSettingsChange={updateSettings}
            onShowToast={showToast}
          />
        </MainContent>

        <ToastContainer>
          <AnimatePresence>
            {toasts.map((toast) => (
              <Toast
                key={toast.id}
                message={toast.message}
                type={toast.type}
                onClose={() => removeToast(toast.id)}
              />
            ))}
          </AnimatePresence>
        </ToastContainer>
      </AppContainer>
    </ThemeProvider>
  );
}

export default App;
