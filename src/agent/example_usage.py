"""
Exemple d'utilisation de l'agent LangGraph avec les outils Légifrance.

Ce script montre comment utiliser l'agent avec les nouveaux outils décorés avec @tool
pour interagir avec le serveur MCP Légifrance.
"""

import os
from typing import Any, Dict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from tools import get_available_tools, test_mcp_connection


def _set_env(var: str):
    """Helper pour définir une variable d'environnement si elle n'existe pas."""
    if not os.environ.get(var):
        import getpass
        os.environ[var] = getpass.getpass(f"{var}: ")


def test_individual_tools():
    """Teste chaque outil individuellement."""
    print("🔧 Test des outils individuels")
    print("=" * 50)
    
    tools = get_available_tools()
    
    for tool in tools:
        print(f"\n📝 Test de l'outil: {tool.name}")
        print(f"Description: {tool.description}")
        
        # Exemples d'utilisation pour chaque outil
        if tool.name == "search_legifrance":
            try:
                result = tool.invoke({"query": "congés payés", "max_results": 3})
                print(f"Résultat: {result[:200]}...")
            except Exception as e:
                print(f"Erreur: {e}")
                
        elif tool.name == "get_article":
            try:
                result = tool.invoke({"article_id": "L3141-1"})
                print(f"Résultat: {result[:200]}...")
            except Exception as e:
                print(f"Erreur: {e}")
                
        elif tool.name == "browse_code":
            try:
                result = tool.invoke({"code_name": "Code du travail", "section": "L3141"})
                print(f"Résultat: {result[:200]}...")
            except Exception as e:
                print(f"Erreur: {e}")


def create_legifrance_agent():
    """Crée un agent LangGraph avec les outils Légifrance."""
    # Configuration du modèle
    _set_env("OPENAI_API_KEY")
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Récupération des outils
    tools = get_available_tools()
    
    # Création de l'agent ReAct avec prompt système
    from langchain_core.messages import SystemMessage
    
    system_prompt = SystemMessage(content="""Tu es un assistant juridique spécialisé dans le droit français.
    Tu peux rechercher et analyser des textes juridiques via la base Légifrance.
    
    Utilise les outils disponibles pour :
    - Rechercher des textes juridiques (search_legifrance)
    - Récupérer des articles spécifiques (get_article)  
    - Explorer la structure des codes (browse_code)
    
    Réponds toujours en français et cite tes sources.""")
    
    agent = create_react_agent(model, tools)
    
    return agent


def test_agent_conversation():
    """Teste une conversation complète avec l'agent."""
    print("\n🤖 Test de conversation avec l'agent")
    print("=" * 50)
    
    # Vérifier la connexion MCP
    if not test_mcp_connection():
        print("⚠️  Serveur MCP non disponible. Certains tests pourraient échouer.")
    
    agent = create_legifrance_agent()
    
    # Questions de test
    questions = [
        "Peux-tu me parler des règles sur les congés payés en France ?",
        "Combien de jours de congés payés a droit un salarié par an ?",
        "Trouve-moi l'article L3141-1 du Code du travail",
        "Explore la structure du Code du travail autour des congés payés"
    ]
    
    config = {"configurable": {"thread_id": "demo-session"}}
    
    for i, question in enumerate(questions, 1):
        print(f"\n📋 Question {i}: {question}")
        print("-" * 40)
        
        try:
            # Invoquer l'agent
            result = agent.invoke(
                {"messages": [HumanMessage(content=question)]},
                config=config
            )
            
            # Afficher la réponse finale
            final_message = result["messages"][-1]
            print(f"🤖 Réponse: {final_message.content}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("\n" + "="*50)


def demo_streaming_response():
    """Démontre le streaming des réponses de l'agent."""
    print("\n🔄 Démonstration du streaming")
    print("=" * 50)
    
    agent = create_legifrance_agent()
    config = {"configurable": {"thread_id": "streaming-demo"}}
    
    question = "Recherche des informations détaillées sur le droit aux congés payés et cite les articles pertinents"
    
    print(f"Question: {question}")
    print("\nRéponse en streaming:")
    print("-" * 30)
    
    try:
        for chunk in agent.stream(
            {"messages": [HumanMessage(content=question)]},
            config=config,
            stream_mode="values"
        ):
            if chunk.get("messages"):
                last_message = chunk["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    print(f"💭 {last_message.content}")
                    
    except Exception as e:
        print(f"❌ Erreur lors du streaming: {e}")


def main():
    """Fonction principale du script de démonstration."""
    print("🚀 Démonstration de l'agent LangGraph Légifrance")
    print("="*60)
    
    try:
        # 1. Test des outils individuels
        test_individual_tools()
        
        # 2. Test de conversation avec l'agent
        test_agent_conversation()
        
        # 3. Démonstration du streaming
        demo_streaming_response()
        
        print("\n✅ Démonstration terminée avec succès!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur durant la démonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 