"""
Tests pour les outils RegulAI.

Ce module teste les fonctionnalités des outils MCP et leur intégration LangChain.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import os
import sys

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from regulai.tools import get_available_tools, MCPClient, search_legifrance


def test_get_available_tools():
    """Test que les outils sont correctement chargés."""
    tools = get_available_tools()
    
    assert len(tools) == 3
    tool_names = [tool.name for tool in tools]
    assert "search_legifrance" in tool_names
    assert "get_article" in tool_names
    assert "browse_code" in tool_names


def test_mcp_client_initialization():
    """Test l'initialisation du client MCP."""
    client = MCPClient("http://test:8000", 60)
    
    assert client.server_url == "http://test:8000"
    assert client.timeout == 60


def test_search_legifrance_tool_structure():
    """Test la structure de l'outil search_legifrance."""
    tools = get_available_tools()
    search_tool = next(tool for tool in tools if tool.name == "search_legifrance")
    
    assert search_tool.name == "search_legifrance"
    assert search_tool.description is not None
    assert "Recherche des textes juridiques" in search_tool.description
    
    # Vérifier le schéma d'arguments
    schema = search_tool.args_schema.model_json_schema()
    properties = schema.get("properties", {})
    assert "query" in properties
    assert "max_results" in properties


@patch('regulai.tools.get_mcp_client')
def test_search_legifrance_tool_call(mock_get_client):
    """Test l'appel de l'outil search_legifrance."""
    # Mock du client MCP
    mock_client = Mock()
    mock_client.call_tool.return_value = "Résultats de recherche mockés"
    mock_get_client.return_value = mock_client
    
    # Appeler l'outil directement avec invoke
    result = search_legifrance.invoke({"query": "test query", "max_results": 5})
    
    # Vérifications
    assert result == "Résultats de recherche mockés"
    mock_client.call_tool.assert_called_once_with(
        "search_legifrance", 
        {"query": "test query", "max_results": 5}
    )


def test_mcp_client_parse_response():
    """Test le parsing des réponses MCP."""
    client = MCPClient()
    
    # Test réponse normale
    response = {
        "result": {
            "content": [
                {"text": "Contenu de test"}
            ]
        }
    }
    
    result = client._parse_mcp_response(response)
    assert result == "Contenu de test"
    
    # Test réponse simple
    response_simple = {
        "result": "Réponse simple"
    }
    
    result_simple = client._parse_mcp_response(response_simple)
    assert result_simple == "Réponse simple"


@patch('httpx.Client')
def test_mcp_client_connection_test(mock_httpx_client):
    """Test la vérification de connexion MCP."""
    
    # Mock de la réponse HTTP
    mock_response = Mock()
    mock_response.status_code = 200
    
    # Créer un mock pour la session HTTP qui fonctionne comme context manager
    mock_session = Mock()
    mock_session.get.return_value = mock_response
    
    # Utiliser MagicMock pour supporter automatiquement les context managers
    mock_context_manager = MagicMock()
    mock_context_manager.__enter__.return_value = mock_session
    mock_context_manager.__exit__.return_value = None
    
    # Le Client() retourne le context manager
    mock_httpx_client.return_value = mock_context_manager
    
    # Test de connexion
    client = MCPClient("http://test:8000")
    result = client.test_connection()
    
    assert result is True
    mock_session.get.assert_called_once_with("http://test:8000/health") 