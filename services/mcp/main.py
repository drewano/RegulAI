# src/main.py
import os
import signal
import sys
from typing import Optional, Literal
from dotenv import load_dotenv
from utils import create_mcp_from_openapi


def start_mcp_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    transport: Literal["stdio", "streamable-http", "sse"] = "streamable-http"
) -> None:
    """
    Lance le serveur MCP avec les paramètres spécifiés.
    
    Cette fonction peut être appelée directement depuis d'autres scripts Python
    ou utilisée via le bloc __main__ pour l'exécution autonome.
    
    Args:
        host: Adresse d'écoute du serveur (par défaut: HOST env var ou 127.0.0.1)
        port: Port d'écoute du serveur (par défaut: PORT env var ou 8000)
        transport: Type de transport à utiliser (par défaut: streamable-http)
        
    Raises:
        Exception: En cas d'erreur lors du démarrage du serveur
    """
    # Charger les variables d'environnement depuis un fichier .env
    load_dotenv()
    
    print("Création du serveur MCP à partir de la spécification OpenAPI...")
    
    # Créer l'instance du serveur en utilisant notre fonction utilitaire
    mcp = create_mcp_from_openapi()
    
    print(f"Serveur MCP '{mcp.name}' créé avec succès. Démarrage...")
    
    # Utiliser les paramètres fournis ou les variables d'environnement/valeurs par défaut
    server_host = host or os.getenv("HOST", "127.0.0.1")
    server_port = port or int(os.getenv("PORT", "8000"))
    
    def signal_handler(signum, frame):
        """Gestionnaire de signal pour un arrêt propre du serveur"""
        print("\n🛑 Arrêt du serveur demandé...")
        print("👋 Serveur arrêté proprement!")
        sys.exit(0)
    
    # Configurer le gestionnaire de signal pour Ctrl+C (SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print(f"🚀 Serveur démarré sur http://{server_host}:{server_port}")
        print("💡 Appuyez sur Ctrl+C pour arrêter le serveur")
        
        # Lancer le serveur avec le transport spécifié
        # Documentation : https://github.com/jlowin/fastmcp/blob/main/docs/deployment/running-server.mdx
        mcp.run(transport=transport, host=server_host, port=server_port)
        
    except KeyboardInterrupt:
        # Au cas où le signal handler ne capture pas l'interruption
        print("\n🛑 Arrêt du serveur demandé...")
        print("👋 Serveur arrêté proprement!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du serveur : {e}")
        raise


async def start_mcp_server_async(
    host: Optional[str] = None,
    port: Optional[int] = None,
    transport: Literal["stdio", "streamable-http", "sse"] = "streamable-http"
) -> None:
    """
    Version asynchrone du démarrage du serveur MCP.
    
    Utile pour intégration dans des applications asynchrones existantes.
    
    Args:
        host: Adresse d'écoute du serveur (par défaut: HOST env var ou 127.0.0.1)
        port: Port d'écoute du serveur (par défaut: PORT env var ou 8000)
        transport: Type de transport à utiliser (par défaut: streamable-http)
        
    Raises:
        Exception: En cas d'erreur lors du démarrage du serveur
    """
    # Charger les variables d'environnement depuis un fichier .env
    load_dotenv()
    
    print("Création du serveur MCP à partir de la spécification OpenAPI...")
    
    # Créer l'instance du serveur en utilisant notre fonction utilitaire
    mcp = create_mcp_from_openapi()
    
    print(f"Serveur MCP '{mcp.name}' créé avec succès. Démarrage asynchrone...")
    
    # Utiliser les paramètres fournis ou les variables d'environnement/valeurs par défaut
    server_host = host or os.getenv("HOST", "127.0.0.1")
    server_port = port or int(os.getenv("PORT", "8000"))
    
    try:
        print(f"🚀 Serveur démarré (async) sur http://{server_host}:{server_port}")
        
        # Lancer le serveur de manière asynchrone
        # Documentation : https://github.com/jlowin/fastmcp/blob/main/docs/deployment/running-server.mdx
        await mcp.run_async(transport=transport, host=server_host, port=server_port)
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage asynchrone du serveur : {e}")
        raise


def get_mcp_instance():
    """
    Crée et retourne une instance du serveur MCP sans le démarrer.
    
    Utile pour les tests ou l'intégration dans d'autres applications.
    
    Returns:
        FastMCP: Instance du serveur MCP configuré
        
    Raises:
        Exception: En cas d'erreur lors de la création du serveur
    """
    # Charger les variables d'environnement depuis un fichier .env
    load_dotenv()
    
    print("Création de l'instance du serveur MCP...")
    
    # Créer l'instance du serveur en utilisant notre fonction utilitaire
    mcp = create_mcp_from_openapi()
    
    print(f"Instance MCP '{mcp.name}' créée avec succès.")
    
    return mcp


# Le bloc d'exécution principal pour l'usage autonome
if __name__ == "__main__":
    # Mode d'exécution autonome - permet l'exécution directe du fichier
    # Usage: python services/mcp/main.py
    
    try:
        start_mcp_server()
    except Exception as e:
        print(f"❌ Erreur critique lors du démarrage : {e}")
        sys.exit(1)