import { motion } from "framer-motion";
import styled from "styled-components";

interface Module {
  id: string;
  name: string;
  icon: string;
}

const MODULES: Module[] = [
  { id: "hotkey", name: "Hotkey Configuration", icon: "keyboard" },
  { id: "rag", name: "Knowledge Base", icon: "auto_stories" },
  { id: "calendar", name: "Calendar", icon: "calendar_today" },
  { id: "tadata", name: "Tadata Integration", icon: "hub" },
  { id: "cloudflare", name: "Cloudflare AI", icon: "cloud" },
  { id: "env", name: "Environment Variables", icon: "vpn_key" },
  { id: "storage", name: "Data & Storage", icon: "folder_open" },
];

const SidebarContainer = styled.div`
  width: 280px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border-right: 0.5px solid rgba(0, 0, 0, 0.1);
  z-index: 50;
`;

const SidebarNav = styled.div`
  flex: 1;
  padding: ${({ theme }) => theme.spacing.lg} 0;
  overflow-y: auto;
`;

const NavItem = styled(motion.div) <{ $isActive: boolean }>`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.md};
  padding: ${({ theme }) => theme.spacing.md} ${({ theme }) => theme.spacing.xl};
  cursor: pointer;
  transition: all ${({ theme }) => theme.transition.normal};
  border-left: 3px solid
    ${({ $isActive }) => ($isActive ? "#007AFF" : "transparent")};
  background: ${({ $isActive }) =>
    $isActive ? "rgba(0, 122, 255, 0.15)" : "transparent"};
  color: ${({ $isActive }) =>
    $isActive ? "rgba(0, 0, 0, 0.85)" : "rgba(0, 0, 0, 0.7)"};
  border-radius: 8px;
  margin: 0 12px 4px 12px;

  &:hover {
    background: rgba(0, 0, 0, 0.05);
    color: rgba(0, 0, 0, 0.85);
  }

  .material-icons {
    font-size: 20px;
    color: inherit;
  }
`;

const SidebarFooter = styled.div`
  padding: ${({ theme }) => theme.spacing.lg} ${({ theme }) => theme.spacing.xl};
  border-top: 0.5px solid rgba(0, 0, 0, 0.1);
  color: rgba(0, 0, 0, 0.6);
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
  margin-bottom: ${({ theme }) => theme.spacing.sm};
  font-size: 14px;
`;

const StatusDot = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34c759;
  animation: pulse 2s infinite;
`;

const Version = styled.div`
  font-size: 12px;
  color: rgba(0, 0, 0, 0.4);
`;

interface SidebarProps {
  activeModule: string;
  onModuleChange: (moduleId: string) => void;
}

export default function Sidebar({
  activeModule,
  onModuleChange,
}: SidebarProps) {
  return (
    <SidebarContainer>
      <SidebarNav>
        {MODULES.map((module) => (
          <NavItem
            key={module.id}
            $isActive={activeModule === module.id}
            onClick={() => onModuleChange(module.id)}
            whileHover={{ x: 4 }}
            transition={{ duration: 0.2 }}
          >
            <span className="material-icons">{module.icon}</span>
            <span>{module.name}</span>
          </NavItem>
        ))}
      </SidebarNav>

      <SidebarFooter>
        <StatusIndicator>
          <StatusDot />
          <span>Service Active</span>
        </StatusIndicator>
        <Version>v1.0.0</Version>
      </SidebarFooter>
    </SidebarContainer>
  );
}
