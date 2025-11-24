"""
Tadata MCP Client Integration for Pointer using LangChain MCP Adapters
Connects to Tadata's MCP servers to use OAuth-enabled tools (Notion, Supabase, Exa)
"""

import os
import logging
from typing import List, Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)


class TadataMCPClient:
    """Client for connecting to Tadata MCP servers using LangChain"""

    def __init__(self):
        """Initialize Tadata MCP client"""
        self.servers = self._load_server_config()
        self.client = None
        self.tools = []
        self._connected = False

        # Don't connect during __init__ - no event loop yet
        # Connection will happen lazily on first use

    def _load_server_config(self) -> Dict[str, Dict[str, str]]:
        """Load Tadata MCP server URLs from settings or environment"""
        servers = {}

        # Try loading from settings manager first
        try:
            from utils.settings_manager import get_settings_manager
            settings_mgr = get_settings_manager()

            notion_url = settings_mgr.get("integrations", "TADATA_NOTION_URL")
            exa_url = settings_mgr.get("integrations", "TADATA_EXA_URL")
            supabase_url = settings_mgr.get("integrations", "TADATA_SUPABASE_URL")

            if notion_url:
                servers["notion"] = {
                    "transport": "streamable_http",
                    "url": notion_url
                }
            if exa_url:
                servers["exa"] = {
                    "transport": "streamable_http",
                    "url": exa_url
                }
            if supabase_url:
                servers["supabase"] = {
                    "transport": "streamable_http",
                    "url": supabase_url
                }

            if servers:
                logger.info(f"Loaded {len(servers)} Tadata server(s) from settings database")
                return servers
        except Exception as e:
            logger.warning(f"Failed to load Tadata config from settings: {e}")

        # Fallback to environment variables
        notion_url = os.getenv("TADATA_NOTION_URL")
        exa_url = os.getenv("TADATA_EXA_URL")
        supabase_url = os.getenv("TADATA_SUPABASE_URL")

        if notion_url:
            servers["notion"] = {
                "transport": "streamable_http",
                "url": notion_url
            }
        if exa_url:
            servers["exa"] = {
                "transport": "streamable_http",
                "url": exa_url
            }
        if supabase_url:
            servers["supabase"] = {
                "transport": "streamable_http",
                "url": supabase_url
            }

        if servers:
            logger.info(f"Loaded {len(servers)} Tadata server(s) from environment variables")

        return servers

    async def _connect_all(self):
        """Connect to all configured Tadata MCP servers using LangChain adapter"""
        if self._connected or not self.servers:
            return

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            from gradient_agent import Tool as GradientTool

            logger.info(f"Connecting to {len(self.servers)} Tadata MCP server(s)...")

            # Create the multi-server client
            self.client = MultiServerMCPClient(self.servers)

            # Get all tools from all servers (these are LangChain tools)
            langchain_tools = await self.client.get_tools()

            # Convert LangChain tools to GradientTool format
            def create_tool_wrapper(langchain_tool):
                """Create a wrapper with proper closure"""
                async def tool_wrapper(**kwargs):
                    # This will invoke the LangChain tool
                    try:
                        if hasattr(langchain_tool, 'ainvoke'):
                            return await langchain_tool.ainvoke(kwargs)
                        elif hasattr(langchain_tool, 'invoke'):
                            return langchain_tool.invoke(kwargs)
                        elif hasattr(langchain_tool, '_arun'):
                            return await langchain_tool._arun(**kwargs)
                        elif hasattr(langchain_tool, '_run'):
                            return langchain_tool._run(**kwargs)
                        else:
                            tool_name = getattr(langchain_tool, 'name', 'unknown')
                            return f"❌ Tool {tool_name} cannot be invoked"
                    except Exception as e:
                        logger.error(f"Error invoking tool: {e}")
                        return f"❌ Tool invocation failed: {str(e)}"
                return tool_wrapper

            self.tools = []
            for lc_tool in langchain_tools:
                try:
                    # Get tool name and description from LangChain tool
                    tool_name = getattr(lc_tool, 'name', 'unknown_tool')
                    tool_desc = getattr(lc_tool, 'description', f'Tool: {tool_name}')

                    # Create wrapper with proper closure
                    wrapper = create_tool_wrapper(lc_tool)

                    # Create GradientTool from the wrapper
                    gradient_tool = GradientTool(
                        name=tool_name,
                        description=tool_desc,
                        func=wrapper
                    )

                    self.tools.append(gradient_tool)
                    logger.info(f"   ✅ Converted: {tool_name}")

                except Exception as e:
                    logger.error(f"Failed to convert tool: {e}")
                    continue

            self._connected = True
            logger.info(f"✅ Connected to Tadata: {len(self.tools)} tools converted to GradientTool format")

        except Exception as e:
            logger.error(f"Failed to connect to Tadata servers: {e}")
            import traceback
            traceback.print_exc()

    async def ensure_connected(self):
        """Ensure connections are established (call this before using tools)"""
        if not self._connected and self.servers:
            await self._connect_all()

    def get_tools(self) -> List[Any]:
        """Get list of LangChain tools from Tadata MCP servers"""
        return self.tools

    def is_configured(self) -> bool:
        """Check if any Tadata servers are configured"""
        return bool(self.servers)

    def reload(self):
        """Reload configuration"""
        self.servers = self._load_server_config()
        self.client = None
        self.tools = []
        self._connected = False

        # Connection will happen lazily on next use


# Global instance
_tadata_client: Optional[TadataMCPClient] = None


def get_tadata_integration() -> TadataMCPClient:
    """Get or create global Tadata MCP client instance"""
    global _tadata_client

    if _tadata_client is None:
        _tadata_client = TadataMCPClient()

    return _tadata_client


async def reload_tadata_integration_async():
    """Async version - actually connects and fetches tools"""
    global _tadata_client

    if _tadata_client is not None:
        _tadata_client.reload()
    else:
        _tadata_client = TadataMCPClient()

    # Actually connect to get the tools
    if _tadata_client.is_configured():
        await _tadata_client.ensure_connected()

    # Update Coordinator agent with new tools
    try:
        from agents.coordinator import Coordinator

        # Remove old Tadata tools (LangChain tools have 'name' attribute)
        Coordinator.tools = [
            tool for tool in Coordinator.tools
            if not (hasattr(tool, 'name') and any(
                server in getattr(tool, 'name', '')
                for server in ['notion', 'exa', 'supabase', 'tadata']
            ))
        ]

        # Add new Tadata tools
        if _tadata_client.is_configured():
            tadata_tools = _tadata_client.get_tools()
            Coordinator.tools.extend(tadata_tools)
            logger.info(f"✅ Reloaded Coordinator with {len(tadata_tools)} Tadata tools")

            # Print tools for debugging
            print("\n" + "="*60)
            print("🔄 TADATA TOOLS RELOADED:")
            print("="*60)
            for idx, tool in enumerate(tadata_tools, 1):
                tool_name = getattr(tool, 'name', 'unknown')
                tool_desc = getattr(tool, 'description', 'No description')
                print(f"  {idx}. {tool_name}")
                print(f"      {tool_desc[:80]}...")
            print("="*60 + "\n")
        else:
            logger.info("ℹ️  No Tadata tools configured")

    except Exception as e:
        logger.error(f"Failed to update Coordinator tools: {e}")
        import traceback
        traceback.print_exc()


def reload_tadata_integration():
    """Reload Tadata MCP client configuration and update Coordinator tools"""
    # Schedule the async version to run
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule as task
            asyncio.create_task(reload_tadata_integration_async())
        else:
            # If no loop, run it
            asyncio.run(reload_tadata_integration_async())
    except RuntimeError:
        # No event loop, run in new one
        asyncio.run(reload_tadata_integration_async())
