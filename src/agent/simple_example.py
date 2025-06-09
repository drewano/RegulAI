"""
Exemple simple d'utilisation de l'agent ReAct LangGraph.

Cet exemple montre comment interagir avec l'agent en utilisant l'API fonctionnelle
et la persistance des conversations.
"""

import uuid
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from .main import agent


def test_simple_query():
    """Test avec une requête simple."""
    
    # Message de l'utilisateur
    user_message = HumanMessage(
        content="Recherche des informations sur les congés payés en France"
    )
    
    # Configuration avec un thread ID unique
    config: RunnableConfig = {
        "configurable": {"thread_id": str(uuid.uuid4())}
    }
    
    print("🔍 Requête: ", user_message.content)
    print("\n--- Streaming de la réponse ---")
    
    # Streaming de la réponse avec suivi des étapes
    for step in agent.stream([user_message], config=config):
        for task_name, message in step.items():
            if task_name == "agent":
                continue  # Ignorer le message final de l'agent dans le streaming
            
            print(f"\n📋 {task_name}:")
            if hasattr(message, 'pretty_print'):
                message.pretty_print()
            else:
                print(message)


def test_conversation_persistence():
    """Test de la persistance des conversations."""
    
    # ID de thread fixe pour la persistance
    thread_id = "conversation-persistante"
    config: RunnableConfig = {
        "configurable": {"thread_id": thread_id}
    }
    
    print("🔄 Test de persistance des conversations")
    print("=" * 50)
    
    # Premier message
    message1 = HumanMessage(content="Cherche des informations sur le Code du travail")
    print(f"\n💬 Message 1: {message1.content}")
    
    response1 = agent.invoke([message1], config=config)
    # L'agent retourne un AIMessage via entrypoint.final()
    content1 = getattr(response1, 'content', str(response1))
    print(f"🤖 Réponse 1: {content1[:100]}...")
    
    # Deuxième message dans la même conversation
    message2 = HumanMessage(content="Peux-tu être plus spécifique sur les horaires de travail?")
    print(f"\n💬 Message 2: {message2.content}")
    
    response2 = agent.invoke([message2], config=config)
    content2 = getattr(response2, 'content', str(response2))
    print(f"🤖 Réponse 2: {content2[:100]}...")
    
    print("\n✅ Les deux messages font partie de la même conversation persistante")


def test_multiple_tools():
    """Test avec utilisation de plusieurs outils."""
    
    user_message = HumanMessage(
        content="Je veux naviguer dans le Code du travail, puis chercher des articles sur les contrats de travail"
    )
    
    config: RunnableConfig = {
        "configurable": {"thread_id": "multi-tools"}
    }
    
    print("🛠️ Test avec outils multiples")
    print("=" * 50)
    print(f"💬 Requête: {user_message.content}")
    
    # Utilisation avec invoke pour récupérer la réponse finale
    response = agent.invoke([user_message], config=config)
    content = getattr(response, 'content', str(response))
    print(f"\n🤖 Réponse finale: {content}")


if __name__ == "__main__":
    print("🚀 Tests de l'agent ReAct Légifrance\n")
    
    # Test 1: Requête simple avec streaming
    test_simple_query()
    
    print("\n" + "="*80 + "\n")
    
    # Test 2: Persistance des conversations
    test_conversation_persistence()
    
    print("\n" + "="*80 + "\n")
    
    # Test 3: Utilisation de plusieurs outils
    test_multiple_tools()
    
    print("\n✨ Tous les tests terminés!") 