# src/main.py
import os
import signal
import sys
from dotenv import load_dotenv
from utils import create_mcp_from_openapi

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

print("Création du serveur MCP à partir de la spécification OpenAPI...")

# Créer l'instance du serveur en utilisant notre fonction utilitaire
mcp = create_mcp_from_openapi()

print(f"Serveur MCP '{mcp.name}' créé avec succès. Démarrage...")

def signal_handler(signum, frame):
    """
    Gestionnaire de signal pour un arrêt propre du serveur
    """
    print("\n🛑 Arrêt du serveur demandé...")
    print("👋 Serveur arrêté proprement!")
    sys.exit(0)

# Le bloc d'exécution principal
if __name__ == "__main__":
    # Configurer le gestionnaire de signal pour Ctrl+C (SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Récupérer l'hôte et le port depuis les variables d'environnement, avec des valeurs par défaut
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    try:
        print(f"🚀 Serveur démarré sur http://{host}:{port}")
        print("💡 Appuyez sur Ctrl+C pour arrêter le serveur")
        
        # Lancer le serveur avec le transport HTTP recommandé pour ce cas d'usage
        # Voir : https://gofastmcp.com/deployment/running-server#streamable-http
        mcp.run(transport="streamable-http", host=host, port=port)
    except KeyboardInterrupt:
        # Au cas où le signal handler ne capture pas l'interruption
        print("\n🛑 Arrêt du serveur demandé...")
        print("👋 Serveur arrêté proprement!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du serveur : {e}")
        sys.exit(1)