"""
Configuration pytest pour les tests RegulAI.

Ce fichier contient les fixtures communes et la configuration de test.
"""

import pytest
import os
import sys
from unittest.mock import Mock

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from regulai.config import RegulAIConfig


@pytest.fixture
def mock_config():
    """Fixture qui fournit une configuration mockée pour les tests."""
    config = RegulAIConfig(
        google_api_key="test_key_123",
        mcp_server_url="http://localhost:8000",
        mcp_timeout=30,
        model_name="gemini-2.0-flash",
        model_temperature=0.0,
        max_iterations=20,
        default_max_results=10,
        log_level="INFO"
    )
    return config


@pytest.fixture
def mock_mcp_client():
    """Fixture qui fournit un client MCP mocké."""
    client = Mock()
    client.call_tool.return_value = "Réponse de test du serveur MCP"
    client.test_connection.return_value = True
    client.get_server_info.return_value = {"version": "1.0.0", "status": "running"}
    return client


@pytest.fixture
def mock_google_response():
    """Fixture qui fournit une réponse Google Gemini mockée."""
    response = Mock()
    response.content = "Réponse de test de l'agent"
    response.tool_calls = []
    return response 