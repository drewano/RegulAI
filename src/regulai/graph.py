"""
Définition de l'état et des nœuds du graphe LangGraph pour l'agent RegulAI.

Ce module contient la structure de données de l'état de l'agent et les fonctions
des nœuds qui composent le workflow ReAct.
"""

from typing import TypedDict, Literal, List, Dict, Any
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI

from .config import get_config
from .tools import get_available_tools


# =============================================================================
# ÉTAT DU GRAPHE (StateGraph)
# =============================================================================

class AgentState(TypedDict):
    """
    État de l'agent RegulAI pour le StateGraph.
    
    Attributes:
        messages: Liste des messages de la conversation
    """
    messages: List[BaseMessage]


# =============================================================================
# CONFIGURATION ET OUTILS
# =============================================================================

def get_configured_model() -> ChatOpenAI:
    """
    Crée une instance configurée du modèle OpenAI.
    
    Returns:
        Instance configurée de ChatOpenAI
        
    Raises:
        ValueError: Si la clé API OpenAI n'est pas configurée
    """
    config = get_config()
    
    # Valider la clé API
    if not config.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY est requis. "
            "Définissez la variable d'environnement ou copiez .env.example vers .env"
        )
    
    # Définir la variable d'environnement si elle n'est pas déjà définie
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = config.openai_api_key
    
    return ChatOpenAI(
        model=config.model_name,
        temperature=config.model_temperature
    )


def get_tools_dict() -> Dict[str, Any]:
    """
    Récupère les outils disponibles sous forme de dictionnaire.
    
    Returns:
        Dictionnaire des outils indexés par nom
    """
    tools = get_available_tools()
    return {tool.name: tool for tool in tools}


# =============================================================================
# NŒUDS DU GRAPHE
# =============================================================================

def call_model(state: AgentState) -> Dict[str, List[BaseMessage]]:
    """
    Nœud qui appelle le modèle de langage avec les messages actuels.
    
    Args:
        state: État actuel de l'agent
        
    Returns:
        Dictionnaire avec la nouvelle liste de messages incluant la réponse du modèle
    """
    model = get_configured_model()
    tools = get_available_tools()
    
    # Lier les outils au modèle et invoquer
    response = model.bind_tools(tools).invoke(state["messages"])
    
    # Retourner l'état mis à jour avec la réponse du modèle
    return {"messages": [response]}


def call_tools(state: AgentState) -> Dict[str, List[BaseMessage]]:
    """
    Nœud qui exécute les outils appelés par le modèle.
    
    Args:
        state: État actuel de l'agent
        
    Returns:
        Dictionnaire avec les messages des résultats des outils
    """
    # Récupérer le dernier message (doit être un AIMessage avec tool_calls)
    last_message = state["messages"][-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}
    
    # Récupérer les outils disponibles
    tools_dict = get_tools_dict()
    tool_messages = []
    
    # Exécuter chaque outil appelé
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        
        if tool_name in tools_dict:
            tool = tools_dict[tool_name]
            try:
                # Invoquer l'outil avec ses arguments
                result = tool.invoke(tool_call["args"])
                
                # Créer un ToolMessage avec le résultat
                tool_message = ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
                tool_messages.append(tool_message)
                
            except Exception as e:
                # En cas d'erreur, créer un message d'erreur
                error_message = ToolMessage(
                    content=f"Erreur lors de l'exécution de {tool_name}: {e}",
                    tool_call_id=tool_call["id"]
                )
                tool_messages.append(error_message)
        else:
            # Outil non trouvé
            error_message = ToolMessage(
                content=f"Outil '{tool_name}' non disponible",
                tool_call_id=tool_call["id"]
            )
            tool_messages.append(error_message)
    
    return {"messages": tool_messages}


# =============================================================================
# FONCTIONS CONDITIONNELLES
# =============================================================================

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Détermine si l'agent doit continuer avec les outils ou terminer.
    
    Args:
        state: État actuel de l'agent
        
    Returns:
        "tools" si des outils doivent être exécutés, "__end__" pour terminer
    """
    # Récupérer le dernier message
    last_message = state["messages"][-1]
    
    # Si c'est un AIMessage avec des appels d'outils, continuer
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    
    # Sinon, terminer
    return "__end__"


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def validate_state(state: AgentState) -> bool:
    """
    Valide que l'état de l'agent est correct.
    
    Args:
        state: État à valider
        
    Returns:
        True si l'état est valide, False sinon
    """
    if not isinstance(state, dict):
        return False
    
    if "messages" not in state:
        return False
    
    if not isinstance(state["messages"], list):
        return False
    
    # Vérifier que tous les éléments sont des BaseMessage
    for msg in state["messages"]:
        if not isinstance(msg, BaseMessage):
            return False
    
    return True


def get_last_ai_message(state: AgentState) -> AIMessage | None:
    """
    Récupère le dernier message AI de l'état.
    
    Args:
        state: État de l'agent
        
    Returns:
        Le dernier AIMessage ou None si aucun trouvé
    """
    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage):
            return message
    return None 