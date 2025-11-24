import { useState, useEffect } from "react";
import styled from "styled-components";
import { invoke } from "@tauri-apps/api/core";
import { motion } from "framer-motion";

const Container = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
`;

const Header = styled.div`
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
`;

const HeaderLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const SuccessIcon = styled(motion.div)`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #34c759 0%, #30d158 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(52, 199, 89, 0.3);
`;

const Title = styled.div`
  font-size: 15px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.9);
`;

const CloseButton = styled.button`
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: rgba(0, 0, 0, 0.4);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;

  &:hover {
    background: rgba(0, 0, 0, 0.05);
    color: rgba(0, 0, 0, 0.7);
  }
`;

const ResponseContainer = styled.div`
  flex: 1;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
`;

const ResponseContent = styled.div`
  font-size: 14px;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.85);
  white-space: pre-wrap;
  word-wrap: break-word;
  text-align: center;
  max-width: 100%;

  img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 16px auto;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    display: block;
  }

  code {
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: "SF Mono", Monaco, monospace;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.8);
  }

  pre {
    background: #f5f5f7;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
    border: 1px solid rgba(0, 0, 0, 0.06);

    code {
      background: transparent;
      padding: 0;
      color: rgba(0, 0, 0, 0.85);
    }
  }

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    margin-top: 20px;
    margin-bottom: 10px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.95);
  }

  h1 {
    font-size: 20px;
  }
  h2 {
    font-size: 18px;
  }
  h3 {
    font-size: 16px;
  }

  p {
    margin: 10px 0;
  }

  ul,
  ol {
    margin: 10px 0;
    padding-left: 24px;
  }

  li {
    margin: 6px 0;
  }

  a {
    color: #007aff;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  blockquote {
    border-left: 3px solid rgba(0, 0, 0, 0.1);
    padding-left: 16px;
    margin: 12px 0;
    color: rgba(0, 0, 0, 0.65);
    font-style: italic;
  }
`;

const Footer = styled.div`
  padding: 14px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(0, 0, 0, 0.02);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
`;

const KeyHint = styled.kbd`
  padding: 3px 8px;
  background: white;
  border-radius: 4px;
  font-size: 11px;
  font-family: inherit;
  color: rgba(0, 0, 0, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.12);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
`;

interface ResponseData {
  response: string;
  original_query?: string;
  metadata?: Record<string, any>;
}

export default function ResponseWindow() {
  const [response, setResponse] = useState<ResponseData | null>(null);

  useEffect(() => {
    // Get response data from Tauri
    const fetchResponseData = async () => {
      try {
        const data = await invoke<ResponseData>("get_response_data");
        console.log("[RESPONSE WINDOW] Received data:", data);
        setResponse(data);
      } catch (error) {
        console.error(
          "[RESPONSE WINDOW] Failed to fetch response data:",
          error
        );
      }
    };

    fetchResponseData();

    // ESC key handler
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        handleClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleClose = async () => {
    try {
      await invoke("close_response_window");
    } catch (error) {
      console.error("Error closing response window:", error);
    }
  };

  // Function to render response with image support
  const renderResponse = (text: string) => {
    // Check if response contains image URLs or base64 images
    const imageRegex =
      /(https?:\/\/[^\s]+?\.(jpg|jpeg|png|gif|webp|svg))|(data:image\/[^;]+;base64,[^\s]+)/gi;
    const parts = text.split(imageRegex);

    return parts.map((part, index) => {
      if (part && (part.match(/^https?:\/\//) || part.match(/^data:image/))) {
        return <img key={index} src={part} alt="Generated content" />;
      }
      return part;
    });
  };

  return (
    <Container>
      <Header>
        <HeaderLeft>
          <SuccessIcon
            initial={{ scale: 0, rotate: -90 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 20,
            }}
          >
            <span className="material-icons">check</span>
          </SuccessIcon>
          <Title>Done ✓</Title>
        </HeaderLeft>
        <CloseButton onClick={handleClose} title="Close (ESC)">
          <span className="material-icons">close</span>
        </CloseButton>
      </Header>

      <ResponseContainer>
        {response ? (
          <ResponseContent>{renderResponse(response.response)}</ResponseContent>
        ) : (
          <ResponseContent>Loading...</ResponseContent>
        )}
      </ResponseContainer>

      <Footer>
        Press <KeyHint>ESC</KeyHint> to close
      </Footer>
    </Container>
  );
}
