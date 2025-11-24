import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { open } from "@tauri-apps/plugin-shell";

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

const StatusCard = styled.div<{ $connected: boolean }>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${({ theme }) => theme.spacing.lg};
  background: ${({ $connected }) =>
    $connected ? "rgba(52, 199, 89, 0.1)" : "rgba(255, 255, 255, 0.8)"};
  border: 0.5px solid
    ${({ $connected }) =>
      $connected ? "rgba(52, 199, 89, 0.3)" : "rgba(0, 0, 0, 0.1)"};
  border-radius: 8px;
  margin-bottom: ${({ theme }) => theme.spacing.lg};
`;

const StatusInfo = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.md};
`;

const StatusIcon = styled.div<{ $connected: boolean }>`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: ${({ $connected }) =>
    $connected ? "#34c759" : "rgba(0, 0, 0, 0.1)"};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;

  .material-icons {
    font-size: 24px;
  }
`;

const StatusText = styled.div`
  .status-label {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.6);
    margin-bottom: 4px;
  }

  .status-value {
    font-size: 16px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
  }

  .account-email {
    font-size: 14px;
    color: rgba(0, 0, 0, 0.6);
    margin-top: 4px;
  }
`;

const Button = styled.button<{ $variant?: "primary" | "secondary" | "danger" }>`
  padding: ${({ theme }) => theme.spacing.sm} ${({ theme }) => theme.spacing.lg};
  background: ${({ $variant }) => {
    if ($variant === "danger") return "#ff3b30";
    if ($variant === "primary") return "#007aff";
    return "rgba(255, 255, 255, 0.8)";
  }};
  color: ${({ $variant }) =>
    $variant === "secondary" ? "rgba(0, 0, 0, 0.85)" : "white"};
  border: 0.5px solid
    ${({ $variant }) => {
      if ($variant === "danger") return "#ff3b30";
      if ($variant === "primary") return "#007aff";
      return "rgba(0, 0, 0, 0.2)";
    }};
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};

  .material-icons {
    font-size: 18px;
  }

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px
      ${({ $variant }) => {
        if ($variant === "danger") return "rgba(255, 59, 48, 0.3)";
        if ($variant === "primary") return "rgba(0, 122, 255, 0.3)";
        return "rgba(0, 0, 0, 0.1)";
      }};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const InfoBox = styled.div`
  padding: ${({ theme }) => theme.spacing.md};
  background: rgba(0, 122, 255, 0.1);
  border: 0.5px solid rgba(0, 122, 255, 0.3);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.7);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: ${({ theme }) => theme.spacing.lg};

  .material-icons {
    font-size: 18px;
    vertical-align: middle;
    margin-right: 8px;
    color: #007aff;
  }
`;

const FeatureList = styled.ul`
  list-style: none;
  padding: 0;
  margin: ${({ theme }) => theme.spacing.md} 0;

  li {
    padding: ${({ theme }) => theme.spacing.sm} 0;
    color: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    gap: ${({ theme }) => theme.spacing.sm};

    &:before {
      content: "✓";
      color: #34c759;
      font-weight: bold;
      font-size: 18px;
    }
  }
`;

const CredentialsInputSection = styled.div`
  background: rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: ${({ theme }) => theme.spacing.lg};
  margin-top: ${({ theme }) => theme.spacing.lg};

  h4 {
    font-size: 16px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
    margin-bottom: ${({ theme }) => theme.spacing.md};
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  padding: ${({ theme }) => theme.spacing.md};
  background: rgba(255, 255, 255, 0.9);
  border: 0.5px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 12px;
  font-family: "SF Mono", "Monaco", "Courier New", monospace;
  resize: vertical;
  line-height: 1.5;

  &:focus {
    outline: none;
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
  }

  &::placeholder {
    color: rgba(0, 0, 0, 0.3);
  }
`;

interface CalendarPanelProps {
  onShowToast: (message: string, type: "success" | "error" | "info") => void;
}

export default function CalendarPanel({ onShowToast }: CalendarPanelProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [accountEmail, setAccountEmail] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showCredentialsInput, setShowCredentialsInput] = useState(false);
  const [credentialsJson, setCredentialsJson] = useState("");
  const hasLoadedRef = React.useRef(false);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      checkConnectionStatus();
    }
  }, []);

  const checkConnectionStatus = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8765/api/calendar/status");
      const data = await response.json();

      if (data.connected) {
        setIsConnected(true);
        setAccountEmail(data.email || null);
      }
    } catch (error) {
      console.error("Error checking calendar status:", error);
    }
  };

  const handleSaveCredentials = async () => {
    try {
      // Validate JSON
      JSON.parse(credentialsJson);

      const response = await fetch(
        "http://127.0.0.1:8765/api/calendar/credentials",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ credentials: credentialsJson }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        onShowToast(error.detail || "Failed to save credentials", "error");
        return;
      }

      onShowToast("OAuth credentials saved successfully!", "success");
      setShowCredentialsInput(false);
      setCredentialsJson("");
    } catch (error) {
      if (error instanceof SyntaxError) {
        onShowToast("Invalid JSON format", "error");
      } else {
        console.error("Error saving credentials:", error);
        onShowToast("Failed to save credentials", "error");
      }
    }
  };

  const handleConnect = async () => {
    setIsLoading(true);
    try {
      console.log("Starting OAuth flow...");
      const response = await fetch(
        "http://127.0.0.1:8765/api/calendar/auth/start",
        {
          method: "POST",
        }
      );

      console.log("Response status:", response.status);

      if (!response.ok) {
        const error = await response.json();
        console.error("Auth start error:", error);

        // If credentials not found, show the input
        if (error.detail && error.detail.includes("not found")) {
          setShowCredentialsInput(true);
          onShowToast("Please add OAuth credentials first", "info");
          setIsLoading(false);
          return;
        }

        onShowToast(error.detail || "Failed to start authentication", "error");
        setIsLoading(false);
        return;
      }

      const data = await response.json();
      console.log("Auth data received:", data);

      if (data.auth_url) {
        // Open the authorization URL in the default browser using Tauri
        console.log("Opening auth URL:", data.auth_url);
        try {
          await open(data.auth_url);
          console.log("Browser opened successfully");
        } catch (openError) {
          console.error("Failed to open browser:", openError);
          onShowToast(`Failed to open browser: ${openError}`, "error");
          setIsLoading(false);
          return;
        }

        onShowToast("Please complete authorization in your browser", "info");

        // Poll for completion
        const pollInterval = setInterval(async () => {
          const statusResponse = await fetch(
            "http://127.0.0.1:8765/api/calendar/status"
          );
          const statusData = await statusResponse.json();

          if (statusData.connected) {
            clearInterval(pollInterval);
            setIsConnected(true);
            setAccountEmail(statusData.email || null);
            onShowToast("Calendar connected successfully!", "success");
            setIsLoading(false);
          }
        }, 2000);

        // Stop polling after 5 minutes
        setTimeout(() => {
          clearInterval(pollInterval);
          setIsLoading(false);
        }, 300000);
      }
    } catch (error) {
      console.error("Error connecting calendar:", error);
      onShowToast(`Failed to start calendar authorization: ${error}`, "error");
      setIsLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect your calendar?")) {
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8765/api/calendar/disconnect",
        {
          method: "POST",
        }
      );
      const data = await response.json();

      if (data.success) {
        setIsConnected(false);
        setAccountEmail(null);
        onShowToast("Calendar disconnected", "success");
      }
    } catch (error) {
      console.error("Error disconnecting calendar:", error);
      onShowToast("Failed to disconnect calendar", "error");
    }
  };

  return (
    <Container>
      <h2>Calendar Integration</h2>

      <Section>
        <h3>Connection Status</h3>
        <StatusCard $connected={isConnected}>
          <StatusInfo>
            <StatusIcon $connected={isConnected}>
              <span className="material-icons">
                {isConnected ? "check_circle" : "calendar_today"}
              </span>
            </StatusIcon>
            <StatusText>
              <div className="status-label">Google Calendar</div>
              <div className="status-value">
                {isConnected ? "Connected" : "Not Connected"}
              </div>
              {accountEmail && (
                <div className="account-email">{accountEmail}</div>
              )}
            </StatusText>
          </StatusInfo>
          {isConnected ? (
            <Button $variant="danger" onClick={handleDisconnect}>
              <span className="material-icons">logout</span>
              Disconnect
            </Button>
          ) : (
            <Button
              $variant="primary"
              onClick={handleConnect}
              disabled={isLoading}
            >
              <span className="material-icons">login</span>
              {isLoading ? "Connecting..." : "Connect Calendar"}
            </Button>
          )}
        </StatusCard>

        {!isConnected && !showCredentialsInput && (
          <>
            <InfoBox>
              <span className="material-icons">info</span>
              Connect your Google Calendar to enable voice-activated event
              creation and management.
            </InfoBox>
            <Button
              $variant="secondary"
              onClick={() => setShowCredentialsInput(true)}
              style={{ marginTop: "1rem" }}
            >
              <span className="material-icons">settings</span>
              Setup OAuth Credentials
            </Button>
          </>
        )}

        {showCredentialsInput && !isConnected && (
          <CredentialsInputSection>
            <h4>OAuth Client Credentials</h4>
            <InfoBox style={{ marginBottom: "1rem" }}>
              <span className="material-icons">info</span>
              <div>
                <p style={{ margin: 0, marginBottom: "0.5rem" }}>
                  <strong>Important:</strong> When creating the OAuth client in
                  Google Cloud Console, add this redirect URI:
                </p>
                <code
                  style={{
                    display: "block",
                    background: "rgba(0, 0, 0, 0.05)",
                    padding: "0.5rem",
                    borderRadius: "4px",
                    fontSize: "12px",
                    fontFamily: "monospace",
                    wordBreak: "break-all",
                  }}
                >
                  http://localhost:8765/api/calendar/auth/callback
                </code>
              </div>
            </InfoBox>
            <p
              style={{
                fontSize: "14px",
                color: "rgba(0, 0, 0, 0.6)",
                marginBottom: "1rem",
              }}
            >
              Paste the JSON credentials from Google Cloud Console:
            </p>
            <ol
              style={{
                fontSize: "14px",
                color: "rgba(0, 0, 0, 0.6)",
                paddingLeft: "1.5rem",
                marginBottom: "1rem",
                lineHeight: 1.6,
              }}
            >
              <li>
                Go to{" "}
                <a
                  href="https://console.cloud.google.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "#007aff" }}
                >
                  Google Cloud Console
                </a>
              </li>
              <li>Create a project and enable Google Calendar API</li>
              <li>Create OAuth 2.0 Client ID (Desktop app)</li>
              <li>Add the redirect URI shown above</li>
              <li>Download the JSON file and paste its contents below</li>
            </ol>
            <TextArea
              value={credentialsJson}
              onChange={(e) => setCredentialsJson(e.target.value)}
              placeholder='{"installed":{"client_id":"...","project_id":"...","auth_uri":"...","token_uri":"...","client_secret":"..."}}'
              rows={8}
            />
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
              <Button $variant="primary" onClick={handleSaveCredentials}>
                <span className="material-icons">save</span>
                Save Credentials
              </Button>
              <Button
                $variant="secondary"
                onClick={() => {
                  setShowCredentialsInput(false);
                  setCredentialsJson("");
                }}
              >
                Cancel
              </Button>
            </div>
          </CredentialsInputSection>
        )}
      </Section>

      <Section>
        <h3>Features</h3>
        <FeatureList>
          <li>Create calendar events with voice commands</li>
          <li>Schedule meetings by speaking naturally</li>
          <li>View upcoming events in your calendar</li>
          <li>Update or delete existing events</li>
          <li>Set reminders and notifications</li>
        </FeatureList>
      </Section>

      <Section>
        <h3>How to Use</h3>
        <p style={{ color: "rgba(0, 0, 0, 0.7)", lineHeight: 1.6 }}>
          Once connected, you can create calendar events by pressing{" "}
          <strong>Cmd+Shift+K</strong> and saying things like:
        </p>
        <ul
          style={{
            marginTop: "1rem",
            paddingLeft: "1.5rem",
            color: "rgba(0, 0, 0, 0.6)",
            lineHeight: 1.8,
          }}
        >
          <li>"Schedule a meeting with John tomorrow at 2pm"</li>
          <li>"Add 'Team standup' to my calendar every Monday at 9am"</li>
          <li>"Create a calendar event for lunch next Friday at noon"</li>
          <li>"Book a 30-minute call with the client on Wednesday"</li>
        </ul>
      </Section>

      <Section>
        <h3>Privacy & Security</h3>
        <p style={{ color: "rgba(0, 0, 0, 0.7)", lineHeight: 1.6 }}>
          Your calendar credentials are stored securely using OAuth 2.0. Pointer
          only requests the minimum permissions needed to manage your calendar
          events. You can disconnect at any time, and all stored credentials
          will be removed.
        </p>
      </Section>
    </Container>
  );
}
