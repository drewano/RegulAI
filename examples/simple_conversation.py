#!/usr/bin/env python3
"""
Exemple simple d'utilisation de l'agent RegulAI.

Ce script démontre comment utiliser l'agent RegulAI pour une conversation
basique sur le droit français.
"""

import os
import sys

# Ajouter le répertoire src au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from regulai.agent import create_agent, run_agent_conversation, stream_agent_conversation
from regulai.config import get_config


def exemple_conversation_simple():
    """Exemple de conversation simple avec l'agent."""
    print("🤖 RegulAI - Exemple de Conversation Simple")
    print("=" * 60)
    
    try:
        # Vérifier la configuration
        config = get_config()
        print(f"📋 Configuration:")
        print(f"   - Modèle: {config.model_name}")
        print(f"   - Serveur MCP: {config.mcp_server_url}")
        print(f"   - API Key configurée: {'✅' if config.openai_api_key else '❌'}")
        
        if not config.openai_api_key:
            print("\n❌ OPENAI_API_KEY n'est pas configuré")
            print("Veuillez copier .env.example vers .env et remplir votre clé API")
            return
        
        # Créer l'agent
        print(f"\n🏗️  Création de l'agent...")
        agent = create_agent()
        print("✅ Agent créé avec succès")
        
        # Messages d'exemple
        messages_test = [
            "Bonjour ! Peux-tu m'expliquer ce qu'est le droit du travail en France ?",
            "Comment fonctionne la recherche dans Légifrance ?",
            "Peux-tu rechercher des informations sur les congés payés ?",
        ]
        
        for i, message in enumerate(messages_test, 1):
            print(f"\n" + "─" * 60)
            print(f"💬 Exemple {i}: {message}")
            print("─" * 60)
            
            # Utiliser l'agent pour répondre
            response = run_agent_conversation(
                message, 
                thread_id=f"exemple-{i}",
                agent=agent
            )
            
            print(f"🤖 Réponse: {response}")
        
        print(f"\n" + "=" * 60)
        print("✅ Tous les exemples ont été exécutés avec succès !")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        print("\nVérifiez votre configuration et réessayez.")


def exemple_conversation_streaming():
    """Exemple de conversation avec streaming en temps réel."""
    print("\n🌊 RegulAI - Exemple avec Streaming")
    print("=" * 60)
    
    try:
        # Créer l'agent
        agent = create_agent()
        
        # Message de test pour le streaming
        message = "Peux-tu me donner un aperçu complet du Code du travail français ?"
        print(f"💬 Question: {message}")
        print("🤖 Réponse en streaming:")
        print("─" * 40)
        
        # Utiliser le streaming
        for step in stream_agent_conversation(message, "streaming-example", agent):
            if "messages" in step:
                last_message = step["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    # Afficher le contenu s'il ne s'agit pas d'appels d'outils
                    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
                        print(f"📝 {last_message.content}")
                    else:
                        print(f"🔧 [Appel d'outils en cours...]")
        
        print("─" * 40)
        print("✅ Streaming terminé")
        
    except Exception as e:
        print(f"❌ Erreur lors du streaming: {e}")


def main():
    """Fonction principale."""
    print("🚀 Exemples d'utilisation de RegulAI")
    print("=" * 60)
    
    # Vérifier les dépendances
    try:
        import regulai
        print("✅ Package RegulAI importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Assurez-vous d'avoir installé le package avec: pip install -e .")
        return
    
    # Exécuter les exemples
    try:
        exemple_conversation_simple()
        print("\n" + "="*20)
        exemple_conversation_streaming()
        
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 