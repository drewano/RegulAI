# src/utils.py
import os
import json
import httpx
from pathlib import Path
from fastmcp import FastMCP

def get_access_token() -> str:
    """
    Récupère un jeton d'accès (access token) auprès du serveur OAuth de PISTE
    en utilisant les identifiants client (Client Credentials).
    """
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")
    token_url = os.getenv("OAUTH_TOKEN_URL")

    if not all([client_id, client_secret, token_url]):
        raise ValueError("Les variables d'environnement OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, et OAUTH_TOKEN_URL sont requises.")

    # Assurance pour le type checker que token_url n'est pas None après la vérification
    assert token_url is not None

    print("Demande d'un jeton d'accès (access token) à PISTE...")
    
    # Le corps de la requête pour obtenir le token
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        # On utilise un client synchrone ici car c'est une action unique au démarrage
        response = httpx.post(token_url, data=data)
        response.raise_for_status()  # Lève une exception si la requête échoue (ex: 401, 500)
        
        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise ValueError("La réponse du serveur OAuth ne contient pas d'access_token.")
            
        print("Jeton d'accès obtenu avec succès !")
        return access_token

    except httpx.HTTPStatusError as e:
        print(f"Erreur HTTP lors de l'obtention du token : {e.response.status_code}")
        print(f"Réponse du serveur : {e.response.text}")
        raise
    except Exception as e:
        print(f"Une erreur inattendue est survenue lors de l'obtention du token : {e}")
        raise


def create_mcp_from_openapi() -> FastMCP:
    """
    Crée une instance de serveur FastMCP à partir de la spécification OpenAPI de Légifrance.
    """
    # 1. Récupérer l'URL de base de l'API
    api_base_url = os.getenv("API_BASE_URL")
    if not api_base_url:
        raise ValueError("La variable d'environnement API_BASE_URL n'est pas définie.")

    # 2. Obtenir le jeton d'accès via OAuth 2.0
    access_token = get_access_token()

    # 3. Charger le fichier de spécification OpenAPI
    project_root = Path(__file__).parent.parent.parent
    spec_path = project_root / "openapi.json"
    if not spec_path.exists():
        raise FileNotFoundError(f"Fichier openapi.json non trouvé à l'emplacement : {spec_path}")

    with open(spec_path, "r", encoding="utf-8") as f:
        openapi_spec = json.load(f)

    # 4. Configurer le client HTTP avec le jeton d'accès obtenu
    headers = {
        "Authorization": f"Bearer {access_token}",
        # L'API PISTE requiert aussi ce header pour les appels
        "accept": "application/json",
    }
    
    http_client = httpx.AsyncClient(base_url=api_base_url, headers=headers)

    # 5. Générer le serveur MCP
    server_name = openapi_spec.get("info", {}).get("title", "Légifrance MCP Server")
    
    mcp_server = FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=http_client,
        name=server_name,
        timeout=30.0
    )

    return mcp_server