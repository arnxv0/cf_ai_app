"""
Tool Adapter - Converts Google ADK FunctionTools to Gradient AI Tools
"""

from gradient_agent import Tool as GradientTool
from typing import Callable, Any
import inspect


def FunctionTool(func: Callable, name: str = None, description: str = None) -> GradientTool:
    """
    Create a Gradient AI Tool from a function (compatible with Google ADK's FunctionTool interface)
    
    Args:
        func: The function to wrap as a tool
        name: Optional name for the tool (defaults to function name)
        description: Optional description (defaults to function docstring)
    
    Returns:
        GradientTool instance
    """
    tool_name = name or func.__name__
    tool_description = description or func.__doc__ or f"Tool: {tool_name}"
    
    return GradientTool(
        name=tool_name,
        description=tool_description,
        func=func
    )


# Alias for compatibility
Tool = GradientTool
