"""
RegulAI - Agent IA ReAct avec intégration MCP pour recherche juridique.

Ce package contient l'agent LangGraph principal et ses composants.
"""

__version__ = "0.2.0"
__author__ = "RegulAI Team"

from .agent import create_agent
from .config import RegulAIConfig

__all__ = ["create_agent", "RegulAIConfig"] 