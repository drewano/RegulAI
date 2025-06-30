"""
Configuration centralisée pour RegulAI avec validation Pydantic.

Ce module gère toutes les variables d'environnement et paramètres de configuration
du projet de manière type-safe avec validation automatique.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class RegulAIConfig(BaseSettings):
    """Configuration centralisée avec validation Pydantic."""
    
    # ==========================================
    # Configuration OAuth/API Légifrance
    # ==========================================
    oauth_client_id: Optional[str] = Field(
        default=None,
        description="Identifiant client OAuth pour l'API Légifrance/PISTE"
    )
    oauth_client_secret: Optional[str] = Field(
        default=None,
        description="Secret client OAuth pour l'API Légifrance/PISTE"
    )
    oauth_token_url: str = Field(
        default="https://oauth.piste.gouv.fr/api/oauth/token",
        description="URL du serveur OAuth pour obtenir les tokens"
    )
    api_base_url: str = Field(
        default="https://api.piste.gouv.fr",
        description="URL de base de l'API Légifrance/PISTE"
    )
    
    # ==========================================
    # Configuration Serveur MCP  
    # ==========================================
    mcp_server_url: str = Field(
        default="http://127.0.0.1:8000/mcp/",
        description="URL du serveur MCP Légifrance"
    )
    mcp_timeout: int = Field(
        default=30,
        description="Timeout en secondes pour les requêtes MCP"
    )
    
    # ==========================================
    # Configuration LLM
    # ==========================================
    google_api_key: Optional[str] = Field(
        default=None,
        description="Clé API Google pour le modèle de langage Gemini"
    )
    model_name: str = Field(
        default="gemini-2.0-flash",
        description="Nom du modèle Google Gemini à utiliser"
    )
    model_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Température du modèle (0.0 = déterministe, 2.0 = très créatif)"
    )
    
    # ==========================================
    # Configuration Agent
    # ==========================================
    max_iterations: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Nombre maximum d'itérations pour l'agent ReAct"
    )
    default_max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Nombre par défaut de résultats pour les recherches"
    )
    
    # ==========================================
    # Configuration Logging
    # ==========================================
    log_level: str = Field(
        default="INFO",
        description="Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Format des logs"
    )
    
    # ==========================================
    # Configuration Persistance
    # ==========================================
    thread_id: Optional[str] = Field(
        default=None,
        description="ID de thread par défaut pour la persistance des conversations"
    )
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "validate_assignment": True,
        "env_prefix": "",
    }
    
    def validate_google_key(self) -> str:
        """Valide que la clé Google API est présente."""
        if not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY est requis. "
                "Définissez la variable d'environnement ou copiez .env.example vers .env"
            )
        return self.google_api_key
    
    def validate_oauth_config(self) -> bool:
        """
        Valide que la configuration OAuth est complète pour l'API Légifrance.
        
        Returns:
            True si la configuration OAuth est complète, False sinon
        """
        return bool(
            self.oauth_client_id and 
            self.oauth_client_secret and 
            self.oauth_token_url and 
            self.api_base_url
        )
    
    def get_oauth_missing_fields(self) -> list[str]:
        """
        Retourne la liste des champs OAuth manquants.
        
        Returns:
            Liste des noms de champs OAuth non configurés
        """
        missing = []
        if not self.oauth_client_id:
            missing.append("OAUTH_CLIENT_ID")
        if not self.oauth_client_secret:
            missing.append("OAUTH_CLIENT_SECRET")
        if not self.oauth_token_url:
            missing.append("OAUTH_TOKEN_URL")
        if not self.api_base_url:
            missing.append("API_BASE_URL")
        return missing


# Fonction pour créer une instance de configuration avec validation
def create_config() -> RegulAIConfig:
    """
    Crée et valide une instance de configuration.
    
    Returns:
        Instance configurée et validée de RegulAIConfig
        
    Raises:
        ValueError: Si une configuration requise est manquante
    """
    config = RegulAIConfig()
    # La validation de la clé Google API sera faite lors de la création de l'agent
    return config


# Instance globale de configuration (lazy loading)
_config: Optional[RegulAIConfig] = None


def get_config() -> RegulAIConfig:
    """
    Récupère l'instance de configuration globale.
    
    Returns:
        Instance configurée de RegulAIConfig
    """
    global _config
    if _config is None:
        _config = create_config()
    return _config


def reload_config() -> RegulAIConfig:
    """
    Recharge la configuration depuis les variables d'environnement.
    
    Utile pour les tests ou les changements de configuration à l'exécution.
    
    Returns:
        Nouvelle instance de RegulAIConfig
    """
    global _config
    _config = create_config()
    return _config 