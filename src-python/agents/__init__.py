"""
subagents package init.

Avoid importing `agent` here to prevent circular imports. Subagent modules
should import `backend.agent` lazily inside functions or use fully-qualified
imports where necessary.
"""

__all__ = []
