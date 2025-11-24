"""
AI-Powered Plugin Selector
Uses Gemini to intelligently determine which plugin to use based on user query and context
"""

# Disable Google ADK telemetry FIRST - must be before any Google imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

import google.generativeai as genai
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger("arrow")


class PluginSelector:
    """Intelligent plugin selection using AI"""
    
    AVAILABLE_PLUGINS = {
        "calendar": "Add events to Google Calendar, schedule meetings, set reminders",
        "slack": "Create database queries, generate visualizations, charts, and graphs",
        "terminal": "Generate terminal commands, bash scripts, find files, grep patterns",
        "email": "Compose and send emails via Gmail, write professional messages",
        "notes": "Save notes to Notion, Excel, or text files, organize information",
        "screenshot": "Analyze and explain screenshots, extract information from images",
        "chat": "Generate witty chat replies, be a conversation wingman, flirty responses",
        "code": "Fix code errors, debug issues, explain code, refactor",
    }
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """Initialize the plugin selector with API credentials"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    async def select_plugin(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Use AI to intelligently select the most appropriate plugin
        
        Args:
            query: User's natural language query
            context: Additional context (selected_text, has_screenshot, etc.)
        
        Returns:
            Plugin name or None if no plugin is appropriate
        """
        
        logger.info("=" * 60)
        logger.info("🔍 PLUGIN SELECTOR - Starting selection process")
        logger.info(f"📝 Query: {query}")
        logger.info(f"📦 Context: {context}")
        logger.info("=" * 60)
        
        # Build context description
        context_info = []
        if context.get("selected_text"):
            context_info.append(f"Selected text: '{context['selected_text'][:100]}'")
        if context.get("has_screenshot"):
            context_info.append("Screenshot is available")
        
        context_str = "\n".join(context_info) if context_info else "No additional context"
        
        # Build plugin list for prompt
        plugin_list = "\n".join([
            f"- {name}: {description}"
            for name, description in self.AVAILABLE_PLUGINS.items()
        ])
        
        # Create prompt for AI
        prompt = f"""You are a plugin router for an AI assistant. Analyze the user's query and context, then select the MOST APPROPRIATE plugin.

Available Plugins:
{plugin_list}

User Query: "{query}"
Context: {context_str}

INSTRUCTIONS:
1. Analyze the user's intent carefully
2. Consider the context provided
3. Select the ONE plugin that best matches the request
4. Respond with ONLY the plugin name (e.g., "calendar", "chat", "terminal")
5. If NO plugin is appropriate, respond with "none"

Your response (plugin name only):"""
        
        try:
            # Get AI response
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,  # Low temperature for consistent routing
                    "max_output_tokens": 20,  # Short response
                }
            )
            
            plugin_name = response.text.strip().lower()
            
            # Validate response
            if plugin_name in self.AVAILABLE_PLUGINS:
                logger.info(f"🎯 Selected Plugin: {plugin_name}")
                return plugin_name
            elif plugin_name == "none":
                logger.info("🎯 Selected Plugin: none (using general AI handler)")
                return None
            else:
                # Fallback: try to match partial response
                for name in self.AVAILABLE_PLUGINS.keys():
                    if name in plugin_name:
                        logger.info(f"🎯 Selected Plugin: {name} (partial match)")
                        return name
                logger.info("🎯 Selected Plugin: none (no match found)")
                return None
                
        except Exception as e:
            logger.error(f"Error in AI plugin selection: {e}")
            # Fallback to None (will use general AI handler)
            return None
    
    def get_plugin_description(self, plugin_name: str) -> str:
        """Get description for a specific plugin"""
        return self.AVAILABLE_PLUGINS.get(plugin_name, "Unknown plugin")
