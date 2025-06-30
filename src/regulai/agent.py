"""
Agent RegulAI principal avec architecture StateGraph.

Ce module assemble les nœuds définis dans graph.py pour créer l'agent LangGraph
complet avec persistance et streaming.
"""

from typing import Optional, Any, Dict
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph

from .config import get_config
from .graph import AgentState, call_model, call_tools, should_continue


def create_agent(checkpointer: Optional[MemorySaver] = None) -> CompiledGraph:
    """
    Crée et compile l'agent RegulAI avec architecture StateGraph.
    
    Args:
        checkpointer: Checkpointer pour la persistance (utilise MemorySaver par défaut)
        
    Returns:
        Agent LangGraph compilé et prêt à utiliser
        
    Raises:
        ValueError: Si la configuration est invalide
    """
    # Valider la configuration
    config = get_config()
    
    # Créer le StateGraph avec l'état AgentState
    workflow = StateGraph(AgentState)
    
    # Ajouter les nœuds
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", call_tools)
    
    # Définir le point d'entrée
    workflow.set_entry_point("agent")
    
    # Ajouter les arêtes conditionnelles
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        },
    )
    
    # Après les outils, retourner à l'agent
    workflow.add_edge("tools", "agent")
    
    # Compiler le graphe avec un checkpointer
    if checkpointer is None:
        checkpointer = MemorySaver()
    
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    
    return compiled_graph


def run_agent_conversation(
    message: str, 
    thread_id: str = "default-session",
    agent: Optional[CompiledGraph] = None
) -> str:
    """
    Lance une conversation avec l'agent RegulAI.
    
    Args:
        message: Message de l'utilisateur
        thread_id: ID de session pour la persistance
        agent: Instance de l'agent (créée automatiquement si None)
        
    Returns:
        Réponse finale de l'agent
        
    Raises:
        ValueError: Si la configuration est invalide
    """
    if agent is None:
        agent = create_agent()
    
    # Créer le message utilisateur
    user_message = HumanMessage(content=message)
    
    # Configuration pour la persistance
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    
    # Invoquer l'agent
    result = agent.invoke(
        {"messages": [user_message]},
        config=config
    )
    
    # Récupérer la réponse finale
    if result and "messages" in result:
        last_message = result["messages"][-1]
        if hasattr(last_message, 'content'):
            return last_message.content
    
    return "Aucune réponse de l'agent"


def stream_agent_conversation(
    message: str,
    thread_id: str = "default-session", 
    agent: Optional[CompiledGraph] = None
):
    """
    Lance une conversation avec streaming avec l'agent RegulAI.
    
    Args:
        message: Message de l'utilisateur
        thread_id: ID de session pour la persistance
        agent: Instance de l'agent (créée automatiquement si None)
        
    Yields:
        Étapes intermédiaires et réponse finale de l'agent
        
    Raises:
        ValueError: Si la configuration est invalide
    """
    if agent is None:
        agent = create_agent()
    
    # Créer le message utilisateur
    user_message = HumanMessage(content=message)
    
    # Configuration pour la persistance
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    
    # Streamer les étapes avec mode "updates" pour capturer les appels d'outils
    # et les transitions entre nœuds
    for step in agent.stream(
        {"messages": [user_message]},
        config=config,
        stream_mode="updates"
    ):
        yield step


def stream_agent_conversation_with_tokens(
    message: str,
    thread_id: str = "default-session", 
    agent: Optional[CompiledGraph] = None
):
    """
    Lance une conversation avec streaming token par token avec l'agent RegulAI.
    
    Cette fonction utilise le mode "messages" pour obtenir les tokens individuels
    du modèle de langage, permettant un affichage progressif plus granulaire.
    
    Args:
        message: Message de l'utilisateur
        thread_id: ID de session pour la persistance
        agent: Instance de l'agent (créée automatiquement si None)
        
    Yields:
        Tokens et métadonnées de streaming
        
    Raises:
        ValueError: Si la configuration est invalide
    """
    if agent is None:
        agent = create_agent()
    
    # Créer le message utilisateur
    user_message = HumanMessage(content=message)
    
    # Configuration pour la persistance
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    
    # Streamer avec mode "messages" pour obtenir les tokens individuels
    for token, metadata in agent.stream(
        {"messages": [user_message]},
        config=config,
        stream_mode="messages"
    ):
        yield token, metadata


def main():
    """
    Fonction principale pour tester l'agent RegulAI.
    
    Lance une conversation de test avec l'agent et affiche les résultats.
    """
    try:
        print("🤖 Agent RegulAI - Test de démarrage")
        print("=" * 50)
        
        # Vérifier la configuration
        config = get_config()
        if not config.google_api_key:
            print("❌ Erreur: GOOGLE_API_KEY non configuré")
            print("Copiez .env.example vers .env et remplissez votre clé API Google")
            return
        
        print(f"✅ Configuration validée")
        print(f"   - Modèle: {config.model_name}")
        print(f"   - Serveur MCP: {config.mcp_server_url}")
        print(f"   - Temperature: {config.model_temperature}")
        
        # Créer l'agent
        print("\n📝 Création de l'agent...")
        agent = create_agent()
        print("✅ Agent créé avec succès")
        
        # Message de test
        test_message = "Bonjour ! Peux-tu m'aider à rechercher des informations sur les congés payés en France ?"
        print(f"\n👤 Utilisateur: {test_message}")
        print("\n🤖 Agent RegulAI:")
        print("-" * 30)
        
        # Lancer la conversation avec streaming
        for step in stream_agent_conversation(test_message, "test-session", agent):
            if "messages" in step:
                last_message = step["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    # Afficher seulement les nouveaux contenus (pas les appels d'outils)
                    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
                        print(f"💬 {last_message.content}")
        
        print("\n" + "=" * 50)
        print("✅ Test terminé avec succès !")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        print("\nVérifiez votre configuration :")
        print("1. GOOGLE_API_KEY est défini dans .env")
        print("2. Le serveur MCP est démarré (optionnel pour ce test)")


if __name__ == "__main__":
    main() 