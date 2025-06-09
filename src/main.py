# src/main.py
import os
from dotenv import load_dotenv
from utils import create_mcp_from_openapi

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

print("Création du serveur MCP à partir de la spécification OpenAPI...")

# Créer l'instance du serveur en utilisant notre fonction utilitaire
mcp = create_mcp_from_openapi()

print(f"Serveur MCP '{mcp.name}' créé avec succès. Démarrage...")

# Le bloc d'exécution principal
if __name__ == "__main__":
    # Récupérer l'hôte et le port depuis les variables d'environnement, avec des valeurs par défaut
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    # Lancer le serveur avec le transport HTTP recommandé pour ce cas d'usage
    # Voir : https://gofastmcp.com/deployment/running-server#streamable-http
    mcp.run(transport="streamable-http", host=host, port=port)