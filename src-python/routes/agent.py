from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import uuid

try:
    import cloudflare_client as cf_client
except ImportError:
    cf_client = None

logger = logging.getLogger("arrow.routes.agent")

router = APIRouter(prefix="/api", tags=["agent"])

# Will be set by main.py
arrow_runner = None


class AgentRequest(BaseModel):
    message: str
    context_parts: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/process-query")
async def process_query(request: dict):
    """Legacy endpoint - converts old format to new /api/agent format."""
    try:
        query = request.get("query", "")
        context = request.get("context", {})
        
        # Convert to Pointer backend format
        agent_request = AgentRequest(
            message=query,
            context_parts=[
                {"type": "text", "content": f"Selected text: {context.get('selected_text', '')}"}
            ] if context.get('selected_text') else None,
            session_id=None
        )
        
        # Forward to Pointer backend
        result = await process_agent_request(agent_request)
        
        return {"success": True, "response": result.response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest):
    """
    Process user message through the Pointer agent and return results.
    
    Args:
        request: AgentRequest containing message, optional context, and session_id
    
    Returns:
        AgentResponse with agent's response and metadata
    """
    if not arrow_runner:
        raise HTTPException(status_code=503, detail="Arrow backend not available")
    
    try:
        logger.info("=" * 60)
        logger.info("🚀 ARROW AGENT REQUEST")
        logger.info(f"📝 Message: {request.message}")
        logger.info(f"🔑 Session ID: {request.session_id}")
        logger.info("=" * 60)
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        user_id = "default_user"
        
        # Create or get session
        session = arrow_runner.session_service.get_session(
            app_name=arrow_runner.app_name,
            user_id=user_id,
            session_id=session_id
        )
        if not session:
            session = arrow_runner.session_service.create_session(
                app_name=arrow_runner.app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        # Prepare the message content
        message_parts = [request.message]
        logger.info(f"📝 User message: {request.message}")
        print(f"[DEBUG] User message: {request.message}")
        
        # Add context parts if provided
        if request.context_parts:
            for ctx_part in request.context_parts:
                message_parts.append(ctx_part.get("content", ""))
            logger.info(f"📎 Added {len(request.context_parts)} context part(s)")
        
        # Combine all parts into a single message
        combined_message = " ".join(message_parts)

        # Prepend Cloudflare Vectorize memory context if enabled
        if cf_client and cf_client.is_enabled():
            try:
                memory_context = await cf_client.build_cloudflare_context(request.message)
                if memory_context:
                    combined_message = memory_context + combined_message
                    logger.info("📡 Prepended Cloudflare memory context")
            except Exception as cf_exc:
                logger.warning("Cloudflare context fetch failed (continuing without): %s", cf_exc)
        # Create message object for the agent
        new_message = {
            "content": {
                "parts": [{"text": combined_message}]
            }
        }
        
        logger.info(f"📨 Message prepared for agent")
        print(f"[DEBUG] Message length: {len(combined_message)}")
        
        # Run the agent and collect the response
        logger.info("🤖 Starting agent execution...")
        print("[DEBUG] Starting agent execution...")
        response_text = ""
        event_count = 0
        
        import time
        start_time = time.time()
        
        async for event in arrow_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            event_count += 1
            elapsed = time.time() - start_time
            logger.info(f"⏱️  Event {event_count} at {elapsed:.2f}s - Type: {type(event).__name__}")
            print(f"[DEBUG] Event {event_count}: {type(event).__name__}")
            
            # Log function calls
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        func_name = part.function_call.name if part.function_call.name else "unknown"
                        print("\n" + "="*60)
                        print(f"🔧 TOOL CALLED: {func_name}")
                        print(f"📋 Arguments: {part.function_call.args}")
                        print("="*60 + "\n")
                        logger.info(f"🔧 Function call: {func_name}")
                        logger.info(f"📋 Arguments: {part.function_call.args}")
                    elif hasattr(part, 'function_response') and part.function_response:
                        func_name = part.function_response.name if part.function_response.name else "unknown"
                        response_preview = str(part.function_response.response)[:200]
                        print("\n" + "="*60)
                        print(f"✅ TOOL RESPONSE: {func_name}")
                        print(f"📤 Response preview: {response_preview}...")
                        print("="*60 + "\n")
                        logger.info(f"✅ Function response: {func_name}")
                    elif hasattr(part, 'text') and part.text:
                        response_text += part.text
                        logger.info(f"💬 Agent response chunk: {part.text[:100]}...")
                        print(f"[DEBUG] 💬 Text: {part.text[:200]}...")
        
        total_time = time.time() - start_time
        logger.info(f"✅ Agent execution complete in {total_time:.2f}s. Total events: {event_count}")
        logger.info(f"📤 Final response length: {len(response_text)} characters")
        logger.info(f"📤 Full response: {response_text}")
        print(f"[DEBUG] Full response: {response_text}")

        
        return AgentResponse(
            response=response_text or "No response generated",
            session_id=session_id,
            metadata={"event_count": event_count}
        )
    
    except Exception as e:
        logger.error(f"❌ Error processing agent request: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
