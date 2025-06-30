#!/usr/bin/env python3
"""
Script de test pour vérifier le streaming avec détection d'outils.

Ce script simule le comportement de l'application Streamlit pour tester
la logique de streaming et d'affichage des statuts d'outils.
"""

import os
from typing import Dict, Any

# Configuration temporaire de la clé API pour le test
# Assurez-vous d'avoir une clé API valide dans votre .env
from dotenv import load_dotenv
load_dotenv()

def simulate_status_display(message: str, expanded: bool = False):
    """Simule l'affichage d'un st.status."""
    print(f"📊 STATUS: {message} (expanded={expanded})")
    return {"message": message, "expanded": expanded, "state": "running"}

def simulate_status_update(status_obj: Dict[str, Any], label: str, state: str):
    """Simule la mise à jour d'un st.status."""
    print(f"🔄 STATUS UPDATE: {label} (state={state})")
    status_obj["message"] = label
    status_obj["state"] = state

def test_streaming_with_tool_detection():
    """Test la fonction de streaming avec détection d'outils."""
    print("🧪 Test du streaming avec détection d'outils")
    print("=" * 60)
    
    try:
        # Import des fonctions nécessaires
        from src.regulai.agent import create_agent, stream_agent_conversation
        
        # Créer l'agent
        print("📝 Création de l'agent...")
        agent = create_agent()
        print("✅ Agent créé avec succès")
        
        # Message de test qui devrait déclencher un appel d'outil
        test_message = "Peux-tu rechercher des informations sur les congés payés en France ?"
        print(f"\n👤 Message de test: {test_message}")
        print("\n🤖 Streaming de la réponse:")
        print("-" * 40)
        
        # Variables pour simuler le comportement de Streamlit
        active_statuses = {}
        last_content = ""
        
        # Streamer la conversation
        for event in stream_agent_conversation(test_message, "test-streaming", agent):
            print(f"📥 Événement reçu: {type(event)}")
            
            # Simuler la logique de process_streaming_events
            if isinstance(event, dict):
                for node_name, node_data in event.items():
                    print(f"   🔸 Nœud: {node_name}")
                    
                    if isinstance(node_data, dict) and "messages" in node_data:
                        messages = node_data["messages"]
                        if messages:
                            last_message = messages[-1]
                            print(f"   📧 Message: {type(last_message).__name__}")
                            
                            # Détecter les appels d'outils
                            if (node_name == "agent" and 
                                hasattr(last_message, 'tool_calls') and 
                                last_message.tool_calls):
                                
                                print("   🔧 DÉTECTION D'APPEL D'OUTIL!")
                                for tool_call in last_message.tool_calls:
                                    tool_name = tool_call.get('name', 'outil_inconnu')
                                    tool_id = tool_call.get('id', f'tool_{len(active_statuses)}')
                                    
                                    tool_display_names = {
                                        'search_legifrance': '🔍 Recherche sur Légifrance...',
                                        'get_article': '📄 Récupération d\'article juridique...',
                                        'browse_code': '📚 Navigation dans le code juridique...',
                                    }
                                    
                                    status_message = tool_display_names.get(tool_name, f'⚙️ Exécution de {tool_name}...')
                                    
                                    if tool_id not in active_statuses:
                                        active_statuses[tool_id] = simulate_status_display(status_message)
                                        print(f"   🆕 Nouveau statut créé pour {tool_name}")
                            
                            # Détecter les réponses d'outils
                            elif (node_name == "tools" and 
                                  hasattr(last_message, 'tool_call_id')):
                                
                                print("   ✅ DÉTECTION DE RÉPONSE D'OUTIL!")
                                tool_call_id = last_message.tool_call_id
                                if tool_call_id in active_statuses:
                                    simulate_status_update(
                                        active_statuses[tool_call_id], 
                                        "✅ Terminé", 
                                        "complete"
                                    )
                                    del active_statuses[tool_call_id]
                                    print(f"   🏁 Statut fermé pour {tool_call_id}")
                            
                            # Détecter le contenu de réponse
                            elif (node_name == "agent" and 
                                  hasattr(last_message, 'content') and 
                                  last_message.content and
                                  not (hasattr(last_message, 'tool_calls') and last_message.tool_calls)):
                                
                                current_content = last_message.content
                                if current_content != last_content:
                                    print("   💬 CONTENU DE RÉPONSE:")
                                    print(f"      {current_content[:100]}{'...' if len(current_content) > 100 else ''}")
                                    last_content = current_content
        
        print("\n" + "=" * 60)
        print("✅ Test terminé avec succès !")
        print(f"📊 Statuts actifs restants: {len(active_statuses)}")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_streaming_with_tool_detection() 