"""
Gradient AI Agent System - Custom agent implementation using Digital Ocean's Gradient AI
Replaces Google ADK with direct HTTP API calls to Gradient AI
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
import asyncio
import httpx

logger = logging.getLogger("arrow.gradient_agent")


@dataclass
class Message:
    """Represents a message in the conversation"""
    role: str
    content: str
    
    def to_dict(self):
        return {"role": self.role, "content": self.content}


@dataclass
class Session:
    """Represents a conversation session"""
    session_id: str
    user_id: str
    app_name: str
    history: List[Message] = field(default_factory=list)
    
    def add_message(self, role: str, content: str):
        """Add a message to the session history"""
        self.history.append(Message(role=role, content=content))
    
    def get_messages_dict(self) -> List[Dict[str, str]]:
        """Get all messages as dictionaries for API calls"""
        return [msg.to_dict() for msg in self.history]


class SessionService:
    """Manages conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
    def create_session(self, app_name: str, user_id: str, session_id: str) -> Session:
        """Create a new session"""
        session = Session(session_id=session_id, user_id=user_id, app_name=app_name)
        self.sessions[f"{app_name}:{user_id}:{session_id}"] = session
        logger.info(f"Created session: {session_id}")
        return session
    
    def get_session(self, app_name: str, user_id: str, session_id: str) -> Optional[Session]:
        """Get an existing session"""
        key = f"{app_name}:{user_id}:{session_id}"
        return self.sessions.get(key)
    
    def delete_session(self, app_name: str, user_id: str, session_id: str):
        """Delete a session"""
        key = f"{app_name}:{user_id}:{session_id}"
        if key in self.sessions:
            del self.sessions[key]
            logger.info(f"Deleted session: {session_id}")


class Tool:
    """Base class for tools that agents can use"""
    
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func
        self._is_async = asyncio.iscoroutinefunction(func)
    
    async def execute(self, **kwargs) -> Any:
        """Execute the tool function"""
        if self._is_async:
            return await self.func(**kwargs)
        else:
            return self.func(**kwargs)
    
    def to_function_definition(self) -> Dict[str, Any]:
        """Convert tool to function definition for Gradient AI"""
        # Extract parameter info from function signature
        import inspect
        sig = inspect.signature(self.func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            param_type = "string"  # Default to string
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == float:
                    param_type = "number"
            
            parameters["properties"][param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }
            
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters
        }


class GradientAgent:
    """Custom agent implementation using Gradient AI SDK"""
    
    def __init__(
        self,
        name: str,
        model: str = "alibaba-qwen3-32b",
        description: str = "",
        instruction: str = "",
        tools: Optional[List[Tool]] = None,
        sub_agents: Optional[List['GradientAgent']] = None,
    ):
        self.name = name
        self.model = model
        self.description = description
        self.instruction = instruction
        self.tools = tools or []
        self.sub_agents = sub_agents or []
        
        # Initialize API configuration based on model
        if model.startswith("anthropic-") or model.startswith("claude-"):
            # Use Anthropic API for Claude models
            self.api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GRADIENT_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            self.api_url = "https://api.anthropic.com/v1/messages"
            self.is_anthropic = True
            # Convert model name: anthropic-claude-3.7-sonnet -> claude-3-7-sonnet-20241022
            if "3.7" in model or "3-7" in model:
                self.model = "claude-3-7-sonnet-20241022"
            else:
                self.model = model.replace("anthropic-", "")
        else:
            # Use Gradient AI (Digital Ocean) for other models
            self.api_key = os.environ.get("GRADIENT_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            self.api_url = "https://inference.do-ai.run/v1/chat/completions"
            self.is_anthropic = False
        
        if not self.api_key:
            raise ValueError("API key must be set in environment variables (ANTHROPIC_API_KEY, GRADIENT_API_KEY, or GOOGLE_API_KEY)")
        
        # Build tools map for quick lookup
        self.tools_map = {tool.name: tool for tool in self.tools}
        
        logger.info(f"Initialized Gradient agent: {name} with model {model}")
        logger.info(f"  Tools: {len(self.tools)}")
        logger.info(f"  Sub-agents: {len(self.sub_agents)}")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with instructions and tool descriptions"""
        prompt = f"{self.instruction}\n\n"
        
        if self.tools:
            prompt += "AVAILABLE TOOLS:\n"
            for tool in self.tools:
                prompt += f"- {tool.name}: {tool.description}\n"
            prompt += "\n"
        
        if self.sub_agents:
            prompt += "AVAILABLE SUB-AGENTS:\n"
            for agent in self.sub_agents:
                prompt += f"- {agent.name}: {agent.description}\n"
            prompt += "\n"
        
        return prompt
    
    async def _call_gradient(self, messages: List[Dict[str, str]], max_tokens: int = 2000) -> str:
        """Make a call to Gradient AI API using HTTP"""
        try:
            async with httpx.AsyncClient() as client:
                if self.is_anthropic:
                    # Anthropic API format
                    system_message = None
                    anthropic_messages = []
                    
                    for msg in messages:
                        if msg["role"] == "system":
                            system_message = msg["content"]
                        else:
                            anthropic_messages.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })
                    
                    request_body = {
                        "model": self.model,
                        "messages": anthropic_messages,
                        "max_tokens": max_tokens
                    }
                    
                    if system_message:
                        request_body["system"] = system_message
                    
                    response = await client.post(
                        self.api_url,
                        headers={
                            "Content-Type": "application/json",
                            "x-api-key": self.api_key,
                            "anthropic-version": "2023-06-01"
                        },
                        json=request_body,
                        timeout=60.0
                    )
                else:
                    # Gradient AI format
                    response = await client.post(
                        self.api_url,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {self.api_key}"
                        },
                        json={
                            "model": self.model,
                            "messages": messages,
                            "max_tokens": max_tokens
                        },
                        timeout=60.0
                    )
                
                response.raise_for_status()
                result = response.json()
                
                if self.is_anthropic:
                    return result["content"][0]["text"]
                else:
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"API error: {e}")
            raise
    
    async def _handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result"""
        if tool_name not in self.tools_map:
            return f"Error: Tool '{tool_name}' not found"
        
        tool = self.tools_map[tool_name]
        try:
            result = await tool.execute(**arguments)
            return str(result)
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return f"Error executing tool: {str(e)}"
    
    async def _handle_agent_delegation(self, agent_name: str, message: str, session: Session) -> str:
        """Delegate to a sub-agent"""
        sub_agent = next((a for a in self.sub_agents if a.name == agent_name), None)
        if not sub_agent:
            return f"Error: Sub-agent '{agent_name}' not found"
        
        try:
            # Create temporary session for sub-agent
            result = await sub_agent._process_message(message, session)
            return result
        except Exception as e:
            logger.error(f"Sub-agent delegation error for {agent_name}: {e}")
            return f"Error delegating to sub-agent: {str(e)}"
    
    async def _process_message(self, message: str, session: Session) -> str:
        """Process a single message and return response"""
        # Build messages with system prompt and history
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        # Add conversation history
        messages.extend(session.get_messages_dict())
        
        # Add current user message
        messages.append({"role": "user", "content": message})
        
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Call Gradient AI
            response = await self._call_gradient(messages)
            
            # Check if response contains tool call or agent delegation
            try:
                # Try to parse as JSON
                response_data = json.loads(response)
                
                if "tool" in response_data:
                    # Tool call
                    tool_name = response_data["tool"]
                    arguments = response_data.get("arguments", {})
                    logger.info(f"Tool call: {tool_name} with args {arguments}")
                    
                    tool_result = await self._handle_tool_call(tool_name, arguments)
                    
                    # Add tool result to messages and continue
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
                    continue
                
                elif "agent" in response_data:
                    # Sub-agent delegation
                    agent_name = response_data["agent"]
                    agent_message = response_data.get("message", "")
                    logger.info(f"Delegating to sub-agent: {agent_name}")
                    
                    agent_result = await self._handle_agent_delegation(agent_name, agent_message, session)
                    
                    # Add delegation result to messages and continue
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"Sub-agent result: {agent_result}"})
                    continue
                
            except json.JSONDecodeError:
                # Not a JSON response, treat as final answer
                pass
            
            # Final response
            return response
        
        return "Error: Maximum iterations reached"
    
    async def run_async(
        self,
        user_id: str,
        session_id: str,
        new_message: Dict[str, Any]
    ) -> AsyncGenerator[Any, None]:
        """
        Main entry point for processing user messages
        Yields events similar to Google ADK for compatibility
        """
        session_key = f"{self.name}:{user_id}:{session_id}"
        
        # Extract message text
        message_text = ""
        if "content" in new_message and "parts" in new_message["content"]:
            for part in new_message["content"]["parts"]:
                if "text" in part:
                    message_text += part["text"] + " "
        
        message_text = message_text.strip()
        logger.info(f"Processing message: {message_text[:100]}...")
        
        # Get or create session
        session = Session(session_id=session_id, user_id=user_id, app_name=self.name)
        
        # Add user message to history
        session.add_message("user", message_text)
        
        # Process message and get response
        response_text = await self._process_message(message_text, session)
        
        # Add assistant response to history
        session.add_message("assistant", response_text)
        
        # Yield response event (compatible with existing code)
        @dataclass
        class ResponseEvent:
            content: Any
            
            @dataclass
            class Content:
                parts: List[Any]
                
                @dataclass
                class Part:
                    text: str
        
        # Yield final response event
        yield ResponseEvent(
            content=ResponseEvent.Content(
                parts=[ResponseEvent.Content.Part(text=response_text)]
            )
        )


class InMemoryRunner:
    """Runner for Gradient agents - mimics Google ADK's InMemoryRunner interface"""
    
    def __init__(self, agent: GradientAgent, app_name: str):
        self.agent = agent
        self.app_name = app_name
        self.session_service = SessionService()
        logger.info(f"Initialized InMemoryRunner for app: {app_name}")
    
    async def run_async(
        self,
        user_id: str,
        session_id: str,
        new_message: Dict[str, Any]
    ) -> AsyncGenerator[Any, None]:
        """Run the agent asynchronously"""
        async for event in self.agent.run_async(user_id, session_id, new_message):
            yield event
