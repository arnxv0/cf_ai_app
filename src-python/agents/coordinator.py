# Disable telemetry
import os
os.environ["GRADIENT_DISABLE_TELEMETRY"] = "1"

import logging
from gradient_agent import GradientAgent
from agents.summarize import SummarizerAgent
from agents.terminal_cmd import TerminalCmdAgent
from tools.calendar import CalendarTool
from tools.emailer import EmailTool
from tools.rag import RagAddTool, RagQueryTool
from tools.vision import AttachContextTool , ListContextHelpTool
from tools.tadata import get_tadata_integration
from tools.integrations import NotionSearchTool, SupabaseQueryTool, ExaSearchTool

logger = logging.getLogger("arrow.router")
logger.info("🎯 Initializing Coordinator agent...")
print("[DEBUG ROUTER] Initializing Coordinator agent...")

Coordinator = GradientAgent(
    name="PointerCoordinator",
    model="openai-gpt-oss-120b",
    description="Routes commands to tools. Email→send_email, Schedule→calendar, Summary→Summarizer, Terminal→TerminalCmdGen, Knowledge→RAG.",
    instruction=(
        "YOU MUST USE TOOLS DIRECTLY. Never delegate or transfer tasks. Execute actions immediately.\n\n"

        "RESPONSE STYLE:\n"
        "- Be EXTREMELY CONCISE and DIRECT\n"
        "- ONE sentence maximum for inline mode responses\n"
        "- NO questions, NO confirmations, NO follow-ups\n"
        "- Just provide the factual answer or execute the action\n"
        "- Example: 'GitHub: arnxv0' NOT 'I found that your GitHub username is arnxv0. Would you like me to...'\n\n"

        "You receive the user's spoken/typed command, plus any selected text from their screen.\n\n"

        "NOTION/TADATA TOOLS - HIGHEST PRIORITY:\n"
        "- When user mentions 'Notion', 'my notes', 'incident', 'page', or asks to search their workspace:\n"
        "  → IMMEDIATELY use notion_notion-search(query='search term') to search their Notion\n"
        "  → To get specific page details: notion_notion-fetch(input='page_id or url')\n"
        "- Example: 'tell me about incident 323' → MUST call notion_notion-search(query='incident 323')\n"
        "- Example: 'what's in my Notion' → MUST call notion_notion-search(query='') to list pages\n"
        "- These tools are ALREADY AUTHENTICATED - no credentials needed\n"
        "- NEVER say 'I don't have access' - YOU DO via notion_notion-search and notion_notion-fetch\n"
        "- Also available: exa_web_search_exa for web searches, supabase_* for database queries\n\n"
        
        "AUTOMATIC CONTEXT RETRIEVAL:\n"
        "- For ANY user question or request, FIRST query the knowledge base with rag_query() to find relevant stored information\n"
        "- Use the query results to enhance your response with personalized context\n"
        "- If relevant documents are found, incorporate them naturally into your answer\n"
        "- If no results found, say 'No information found' - nothing else\n\n"
        
        "CALENDAR EVENTS (HIGHEST PRIORITY):\n"
        "When user says 'add to calendar', 'schedule', 'create event', 'add this event':\n"
        "1. Parse the selected text or user message for: title, date, time, location\n"
        "2. Convert to ISO 8601 format: YYYY-MM-DDTHH:MM:SS\n"
        "3. IMMEDIATELY call add_to_calendar(title, start_iso, end_iso, description, location)\n"
        "4. Use current date (October 25, 2025) as reference for 'tomorrow', 'Sunday', etc.\n"
        "5. Examples:\n"
        "   Selected text: 'Brunch 9:30 AM - 11:00 AM Sunday'\n"
        "   → add_to_calendar(title='Brunch', start_iso='2025-10-27T09:30:00', end_iso='2025-10-27T11:00:00')\n\n"
        
        "EMAIL: When user wants to send an email, write a professional email using both their command and the selected text, then send it using send_email(to, subject, body).\n\n"
        
        "KNOWLEDGE BASE STORAGE:\n"
        "- Detect when user wants to remember/save/store information\n"
        "- Use rag_add(id, text, source) to store content\n"
        "- Confirm storage with a friendly message\n\n"
        
        "NEVER transfer to other agents. ALWAYS use tools directly.\n"
    ),
    tools=[
        CalendarTool,
        EmailTool,
        RagAddTool,
        RagQueryTool,
        AttachContextTool,
        ListContextHelpTool,
        NotionSearchTool,
        SupabaseQueryTool,
        ExaSearchTool,
    ],
    sub_agents=[
        SummarizerAgent,
        TerminalCmdAgent,
    ],
)

# Add Tadata tools if configured
# Note: Tools will be loaded lazily when first accessed, or explicitly via reload
tadata = get_tadata_integration()
if tadata.is_configured():
    # Don't try to get tools here - they need async connection
    # Tools will be added via reload_tadata_integration() after startup
    logger.info(f"✅ Tadata configured with {len(tadata.servers)} server(s) - tools will load on first use")

logger.info("✅ Coordinator agent initialized successfully")
logger.info(f"   Tools: {len(Coordinator.tools)} tool(s)")
logger.info(f"   Sub-agents: {len(Coordinator.sub_agents)} sub-agent(s)")
print(f"[DEBUG ROUTER] Coordinator initialized with {len(Coordinator.tools)} tools and {len(Coordinator.sub_agents)} sub-agents")

# Print all tools for debugging
print("\n" + "="*60)
print("🔧 COORDINATOR TOOLS:")
print("="*60)
for idx, tool in enumerate(Coordinator.tools, 1):
    if isinstance(tool, tuple):
        server_name, tool_info = tool
        tool_name = tool_info.get('name', 'unknown') if isinstance(tool_info, dict) else str(tool_info)
        print(f"  {idx}. [{server_name}] {tool_name} (Tadata MCP)")
    else:
        # Try to get the tool name from various attributes
        tool_name = None
        if hasattr(tool, 'name'):
            tool_name = tool.name
        elif hasattr(tool, '_name'):
            tool_name = tool._name
        elif hasattr(tool, 'function_name'):
            tool_name = tool.function_name
        elif hasattr(tool, '__name__'):
            tool_name = tool.__name__
        else:
            tool_name = type(tool).__name__
        print(f"  {idx}. {tool_name}")
print("="*60 + "\n")
