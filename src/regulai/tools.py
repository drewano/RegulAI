"""
Outils pour interagir avec le serveur MCP Légifrance via HTTP.

Ce module contient la classe MCPClient pour la communication HTTP et les outils 
LangChain décorés avec @tool pour l'intégration avec l'agent LangGraph.
"""

import httpx
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from .config import get_config


# =============================================================================
# SCHÉMAS PYDANTIC POUR VALIDATION DES ARGUMENTS
# =============================================================================

class SearchParams(BaseModel):
    """Paramètres pour la recherche dans Légifrance."""
    query: str = Field(
        description="Requête de recherche en français (ex: 'congés payés', 'droit du travail')"
    )
    max_results: int = Field(
        default=10,
        description="Nombre maximum de résultats à retourner"
    )


class ArticleParams(BaseModel):
    """Paramètres pour récupérer un article spécifique."""
    article_id: str = Field(
        description="Identifiant de l'article (ex: 'LEGIARTI000006900846' ou 'L3141-1')"
    )


class BrowseCodeParams(BaseModel):
    """Paramètres pour naviguer dans un code juridique."""
    code_name: str = Field(
        description="Nom du code juridique (ex: 'Code du travail', 'Code civil')"
    )
    section: Optional[str] = Field(
        default=None,
        description="Section spécifique à explorer (optionnel)"
    )


# =============================================================================
# CLIENT MCP POUR COMMUNICATION HTTP
# =============================================================================

class MCPClient:
    """
    Client HTTP pour communiquer avec le serveur MCP Légifrance.
    
    Cette classe encapsule toute la logique de communication HTTP avec le serveur MCP,
    permettant d'abstraire les détails du protocole MCP pour les outils.
    """
    
    def __init__(self, server_url: Optional[str] = None, timeout: Optional[int] = None):
        """
        Initialise le client MCP.
        
        Args:
            server_url: URL du serveur MCP (utilise la config par défaut si None)
            timeout: Timeout en secondes (utilise la config par défaut si None)
        """
        config = get_config()
        self.server_url = server_url or config.mcp_server_url
        self.timeout = timeout or config.mcp_timeout
    
    def call_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Appelle un outil sur le serveur MCP via HTTP.
        
        Args:
            tool_name: Nom de l'outil MCP à appeler
            tool_args: Arguments à passer à l'outil
        
        Returns:
            Réponse de l'outil sous forme de chaîne formatée
            
        Raises:
            Exception: En cas d'erreur de communication ou de serveur
        """
        try:
            # Préparer la requête selon le format attendu par le serveur MCP
            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": tool_args
                }
            }
            
            # Faire la requête HTTP au serveur MCP
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.server_url}/invoke",  # Point d'entrée principal du serveur
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return self._parse_mcp_response(result)
                else:
                    return self._handle_error_response(response)
                    
        except httpx.RequestError as e:
            return f"Erreur de connexion au serveur MCP ({self.server_url}): {e}"
        except Exception as e:
            return f"Erreur lors de l'appel de l'outil {tool_name}: {e}"
    
    def _parse_mcp_response(self, result: Dict[str, Any]) -> str:
        """
        Parse la réponse du serveur MCP selon son format.
        
        Args:
            result: Réponse JSON du serveur MCP
            
        Returns:
            Contenu formaté de la réponse
        """
        # Parser la réponse MCP selon son format
        if "result" in result:
            content = result["result"]
            
            # Si la réponse contient du contenu structuré
            if isinstance(content, dict) and "content" in content:
                content_data = content["content"]
                
                # Gérer les réponses avec liste de contenus
                if isinstance(content_data, list) and len(content_data) > 0:
                    first_item = content_data[0]
                    if isinstance(first_item, dict) and "text" in first_item:
                        return first_item["text"]
                    else:
                        return str(first_item)
                else:
                    return str(content_data)
            else:
                return str(content)
        else:
            return f"Réponse inattendue du serveur MCP: {result}"
    
    def _handle_error_response(self, response: httpx.Response) -> str:
        """
        Gère les réponses d'erreur HTTP.
        
        Args:
            response: Réponse HTTP d'erreur
            
        Returns:
            Message d'erreur formaté
        """
        error_msg = f"Erreur HTTP {response.status_code}"
        try:
            error_detail = response.json()
            error_msg += f": {error_detail}"
        except:
            error_msg += f": {response.text}"
        return error_msg
    
    def test_connection(self) -> bool:
        """
        Teste la connexion au serveur MCP.
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.server_url}/health")
                return response.status_code == 200
        except:
            return False
    
    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations du serveur MCP.
        
        Returns:
            Informations du serveur ou None en cas d'erreur
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.server_url}/info")
                if response.status_code == 200:
                    return response.json()
        except:
            pass
        return None


# Instance globale du client MCP
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """
    Récupère l'instance globale du client MCP.
    
    Returns:
        Instance du client MCP
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


# =============================================================================
# OUTILS LÉGIFRANCE AVEC DÉCORATEUR @tool
# =============================================================================

@tool("search_legifrance", args_schema=SearchParams, parse_docstring=True)
def search_legifrance(query: str, max_results: int = 10) -> str:
    """
    Recherche des textes juridiques dans la base de données Légifrance.
    
    Cet outil permet de chercher des lois, décrets, codes, jurisprudence et autres 
    textes juridiques français. Utilisez des termes de recherche en français.
    
    Args:
        query: Requête de recherche en français (ex: "congés payés", "licenciement économique")
        max_results: Nombre maximum de résultats à retourner (défaut: 10)
        
    Returns:
        Liste formatée des textes juridiques trouvés avec leurs références
    """
    client = get_mcp_client()
    return client.call_tool("search_legifrance", {
        "query": query,
        "max_results": max_results
    })


@tool("get_article", args_schema=ArticleParams, parse_docstring=True)  
def get_article(article_id: str) -> str:
    """
    Récupère le contenu complet d'un article juridique spécifique.
    
    Permet d'obtenir le texte intégral d'un article de loi, de code ou de décret
    à partir de son identifiant Légifrance ou de sa référence standard.
    
    Args:
        article_id: Identifiant de l'article (ex: "LEGIARTI000006900846", "L3141-1", "R1234-5")
        
    Returns:
        Texte complet de l'article avec ses métadonnées (version, dates, etc.)
    """
    client = get_mcp_client()
    return client.call_tool("get_article", {
        "article_id": article_id
    })


@tool("browse_code", args_schema=BrowseCodeParams, parse_docstring=True)
def browse_code(code_name: str, section: Optional[str] = None) -> str:
    """
    Navigate dans la structure hiérarchique d'un code juridique français.
    
    Permet d'explorer l'organisation d'un code (livres, titres, chapitres, sections)
    et d'obtenir la liste des articles dans une section donnée.
    
    Args:
        code_name: Nom du code juridique (ex: "Code du travail", "Code civil", "Code pénal")
        section: Section spécifique à explorer (ex: "L3141", "Livre III", optionnel)
        
    Returns:
        Structure hiérarchique du code ou contenu de la section demandée
    """
    client = get_mcp_client()
    return client.call_tool("browse_code", {
        "code_name": code_name,
        "section": section
    })


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_available_tools() -> List:
    """
    Retourne la liste des outils disponibles pour l'agent.
    
    Returns:
        Liste des fonctions-outils décorées avec @tool
    """
    return [search_legifrance, get_article, browse_code]


def test_mcp_connection() -> bool:
    """
    Teste la connexion au serveur MCP.
    
    Returns:
        True si la connexion fonctionne, False sinon
    """
    client = get_mcp_client()
    return client.test_connection()


def get_mcp_server_info() -> Optional[Dict[str, Any]]:
    """
    Récupère les informations du serveur MCP.
    
    Returns:
        Informations du serveur ou None en cas d'erreur
    """
    client = get_mcp_client()
    return client.get_server_info() 