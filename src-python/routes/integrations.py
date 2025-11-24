"""
Direct integration routes for Notion, Supabase, Exa
Alternative to Tadata - gives you full control
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import httpx
import logging

logger = logging.getLogger("arrow.routes.integrations")

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


# ============================================
# NOTION INTEGRATION
# ============================================

class NotionSearchRequest(BaseModel):
    query: str


class NotionPageCreateRequest(BaseModel):
    title: str
    content: str
    parent_id: Optional[str] = None


@router.post("/notion/search")
async def notion_search(request: NotionSearchRequest):
    """Search Notion workspace"""
    notion_token = os.getenv("NOTION_API_TOKEN")
    if not notion_token:
        raise HTTPException(status_code=400, detail="NOTION_API_TOKEN not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.notion.com/v1/search",
                headers={
                    "Authorization": f"Bearer {notion_token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                },
                json={"query": request.query},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Notion API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notion/create-page")
async def notion_create_page(request: NotionPageCreateRequest):
    """Create a new Notion page"""
    notion_token = os.getenv("NOTION_API_TOKEN")
    if not notion_token:
        raise HTTPException(status_code=400, detail="NOTION_API_TOKEN not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            # Simple page creation - you'll need to configure parent database/page
            response = await client.post(
                "https://api.notion.com/v1/pages",
                headers={
                    "Authorization": f"Bearer {notion_token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                },
                json={
                    "parent": {"page_id": request.parent_id} if request.parent_id else {"type": "workspace"},
                    "properties": {
                        "title": {
                            "title": [{"text": {"content": request.title}}]
                        }
                    },
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": request.content}}]
                            }
                        }
                    ]
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Notion API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SUPABASE INTEGRATION
# ============================================

class SupabaseQueryRequest(BaseModel):
    table: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10


@router.post("/supabase/query")
async def supabase_query(request: SupabaseQueryRequest):
    """Query Supabase table"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=400, detail="SUPABASE_URL or SUPABASE_KEY not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            # Build query URL
            url = f"{supabase_url}/rest/v1/{request.table}"
            params = {"limit": request.limit}
            
            # Add filters if provided
            if request.filters:
                for key, value in request.filters.items():
                    params[key] = f"eq.{value}"
            
            response = await client.get(
                url,
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}"
                },
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Supabase API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# EXA INTEGRATION
# ============================================

class ExaSearchRequest(BaseModel):
    query: str
    num_results: int = 10
    search_type: str = "neural"  # "neural" or "keyword"


@router.post("/exa/search")
async def exa_search(request: ExaSearchRequest):
    """Search using Exa AI"""
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        raise HTTPException(status_code=400, detail="EXA_API_KEY not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.exa.ai/search",
                headers={
                    "x-api-key": exa_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "query": request.query,
                    "num_results": request.num_results,
                    "type": request.search_type,
                    "contents": {
                        "text": True,
                        "highlights": True
                    }
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Exa API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# HEALTH CHECK
# ============================================

@router.get("/status")
async def integrations_status():
    """Check which integrations are configured"""
    return {
        "notion": bool(os.getenv("NOTION_API_TOKEN")),
        "supabase": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")),
        "exa": bool(os.getenv("EXA_API_KEY"))
    }
