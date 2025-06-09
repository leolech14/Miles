"""
Natural Language Processing Module for Miles Bot

This module provides natural language understanding capabilities
that replace the traditional command-based interface with
conversational AI powered by OpenAI function calling.
"""

from .conversation_manager import conversation_manager
from .function_registry import function_registry

__all__ = ["conversation_manager", "function_registry"]
