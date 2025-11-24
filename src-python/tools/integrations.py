"""
Tools for Notion, Supabase, and Exa integrations
"""

from tool_adapter import FunctionTool
import httpx
import os
import logging

logger = logging.getLogger("arrow.tools.integrations")


# ============================================
# NOTION TOOLS
# ============================================

async def notion_search(query: str) -> str:
    """
    Search your Notion workspace for pages and databases. 
    Use this when user wants to find notes, docs, or information stored in Notion.
    
    Args:
        query: Search query to find in Notion workspace
    """
    notion_token = os.getenv("NOTION_API_TOKEN")
    if not notion_token:
        return "❌ Notion not configured. Add NOTION_API_TOKEN to settings."
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.notion.com/v1/search",
                headers={
                    "Authorization": f"Bearer {notion_token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                },
                json={"query": query},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                return f"No results found for: {query}"
            
            # Format results
            results = []
            for item in data["results"][:5]:  # Top 5 results
                title = "Untitled"
                if item.get("properties", {}).get("title", {}).get("title"):
                    title = item["properties"]["title"]["title"][0]["plain_text"]
                results.append(f"• {title} ({item.get('url', 'No URL')})")
            
            return f"Found {len(data['results'])} results:\n" + "\n".join(results)
            
    except Exception as e:
        logger.error(f"Notion search error: {e}")
        return f"❌ Notion search failed: {str(e)}"


NotionSearchTool = FunctionTool(notion_search)


# ============================================
# SUPABASE TOOLS
# ============================================

async def supabase_query(table: str, limit: int = 10) -> str:
    """
    Query data from your Supabase database. 
    Use this to fetch user data, analytics, or any database information.
    
    Args:
        table: Table name to query (e.g., 'users', 'products', 'orders')
        limit: Maximum number of rows to return (default: 10)
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        return "❌ Supabase not configured. Add SUPABASE_URL and SUPABASE_KEY to settings."
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{supabase_url}/rest/v1/{table}",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}"
                },
                params={"limit": limit},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return f"No data found in table: {table}"
            
            return f"✅ Retrieved {len(data)} rows from '{table}':\n{data[:3]}"  # Show first 3 rows
            
    except Exception as e:
        logger.error(f"Supabase query error: {e}")
        return f"❌ Supabase query failed: {str(e)}"


SupabaseQueryTool = FunctionTool(supabase_query)


# ============================================
# EXA TOOLS
# ============================================

async def exa_search(query: str, num_results: int = 5) -> str:
    """
    Search the web using Exa AI for high-quality, semantic results. 
    Perfect for research, finding papers, or discovering relevant content.
    
    Args:
        query: Search query (use natural language)
        num_results: Number of results to return (default: 5)
    """
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        return "❌ Exa not configured. Add EXA_API_KEY to settings."
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.exa.ai/search",
                headers={
                    "x-api-key": exa_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "query": query,
                    "num_results": num_results,
                    "type": "neural",
                    "contents": {
                        "text": True,
                        "highlights": True
                    }
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                return f"No results found for: {query}"
            
            # Format results
            results = []
            for item in data["results"]:
                title = item.get("title", "No title")
                url = item.get("url", "")
                snippet = item.get("text", "")[:200] + "..." if item.get("text") else ""
                results.append(f"• **{title}**\n  {url}\n  {snippet}")
            
            return f"🔍 Exa found {len(data['results'])} results:\n\n" + "\n\n".join(results)
            
    except Exception as e:
        logger.error(f"Exa search error: {e}")
        return f"❌ Exa search failed: {str(e)}"


ExaSearchTool = FunctionTool(exa_search)
