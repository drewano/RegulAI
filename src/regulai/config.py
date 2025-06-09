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
    # Configuration Serveur MCP  
    # ==========================================
    mcp_server_url: str = Field(
        default="http://localhost:8000",
        description="URL du serveur MCP Légifrance"
    )
    mcp_timeout: int = Field(
        default=30,
        description="Timeout en secondes pour les requêtes MCP"
    )
    
    # ==========================================
    # Configuration LLM
    # ==========================================
    openai_api_key: Optional[str] = Field(
        default=None,
        description="Clé API OpenAI pour le modèle de langage"
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        description="Nom du modèle OpenAI à utiliser"
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
    
    def validate_openai_key(self) -> str:
        """Valide que la clé OpenAI est présente."""
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY est requis. "
                "Définissez la variable d'environnement ou copiez .env.example vers .env"
            )
        return self.openai_api_key


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
    # La validation de la clé OpenAI sera faite lors de la création de l'agent
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