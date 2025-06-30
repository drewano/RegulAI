#!/usr/bin/env python3
"""
Script de test avec mock pour vérifier le streaming avec détection d'outils.

Ce script simule les événements LangGraph pour tester la logique de streaming
sans avoir besoin d'une clé API OpenAI valide.
"""

from typing import Dict, Any, Generator, List
from dataclasses import dataclass, field

@dataclass
class MockMessage:
    """Message simulé pour les tests."""
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_call_id: str = ""
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []

def simulate_status_display(message: str, expanded: bool = False):
    """Simule l'affichage d'un st.status."""
    print(f"📊 STATUS: {message} (expanded={expanded})")
    return {"message": message, "expanded": expanded, "state": "running"}

def simulate_status_update(status_obj: Dict[str, Any], label: str, state: str):
    """Simule la mise à jour d'un st.status."""
    print(f"🔄 STATUS UPDATE: {label} (state={state})")
    status_obj["message"] = label
    status_obj["state"] = state

def mock_stream_agent_conversation() -> Generator[Dict[str, Any], None, None]:
    """
    Générateur qui simule les événements de streaming d'un agent LangGraph.
    
    Cette fonction simule la séquence typique :
    1. L'agent décide d'utiliser un outil
    2. L'outil est exécuté 
    3. L'agent génère une réponse finale
    """
    
    # Étape 1: L'agent décide d'utiliser un outil de recherche
    yield {
        "agent": {
            "messages": [
                MockMessage(
                    content="",
                    tool_calls=[{
                        "name": "search_legifrance",
                        "id": "tool_call_123",
                        "args": {"query": "congés payés", "max_results": 10}
                    }]
                )
            ]
        }
    }
    
    # Étape 2: L'outil retourne un résultat
    yield {
        "tools": {
            "messages": [
                MockMessage(
                    content="Résultats de recherche trouvés: Articles L3141-1 à L3141-32 du Code du travail...",
                    tool_call_id="tool_call_123"
                )
            ]
        }
    }
    
    # Étape 3: L'agent génère une réponse finale
    yield {
        "agent": {
            "messages": [
                MockMessage(
                    content="Voici les informations sur les congés payés en France..."
                )
            ]
        }
    }

def test_process_streaming_events():
    """Test de la fonction process_streaming_events avec des données simulées."""
    print("🧪 Test de la logique de streaming avec détection d'outils")
    print("=" * 70)
    
    # Variables pour simuler le comportement de Streamlit
    active_statuses = {}
    last_content = ""
    yielded_content = []
    
    print("🎬 Simulation d'événements de streaming...")
    print("-" * 50)
    
    # Simuler la logique de process_streaming_events
    for event in mock_stream_agent_conversation():
        print(f"📥 Événement reçu: {list(event.keys())}")
        
        if isinstance(event, dict):
            # Parcourir chaque nœud dans l'événement
            for node_name, node_data in event.items():
                print(f"   🔸 Nœud: {node_name}")
                
                # Vérifier s'il y a des messages dans les données du nœud
                if isinstance(node_data, dict) and "messages" in node_data:
                    messages = node_data["messages"]
                    if messages:
                        last_message = messages[-1]
                        print(f"   📧 Message: {type(last_message).__name__}")
                        
                        # Détecter les appels d'outils dans les messages AI (nœud "agent")
                        if node_name == "agent" and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            print("   🔧 DÉTECTION D'APPEL D'OUTIL!")
                            for tool_call in last_message.tool_calls:
                                tool_name = tool_call.get('name', 'outil_inconnu')
                                tool_id = tool_call.get('id', f'tool_{len(active_statuses)}')
                                
                                # Mapper les noms d'outils vers des messages plus conviviaux
                                tool_display_names = {
                                    'search_legifrance': '🔍 Recherche sur Légifrance...',
                                    'get_article': '📄 Récupération d\'article juridique...',
                                    'browse_code': '📚 Navigation dans le code juridique...',
                                }
                                
                                status_message = tool_display_names.get(tool_name, f'⚙️ Exécution de {tool_name}...')
                                
                                # Créer un indicateur de statut pour cet outil
                                if tool_id not in active_statuses:
                                    active_statuses[tool_id] = simulate_status_display(status_message)
                                    print(f"   🆕 Nouveau statut créé pour {tool_name} (ID: {tool_id})")
                        
                        # Détecter les réponses d'outils (nœud "tools")
                        elif node_name == "tools" and hasattr(last_message, 'tool_call_id'):
                            print("   ✅ DÉTECTION DE RÉPONSE D'OUTIL!")
                            tool_call_id = last_message.tool_call_id
                            # Fermer le statut correspondant s'il existe
                            if tool_call_id in active_statuses:
                                simulate_status_update(
                                    active_statuses[tool_call_id], 
                                    "✅ Terminé", 
                                    "complete"
                                )
                                # Retirer de la liste des statuses actifs
                                del active_statuses[tool_call_id]
                                print(f"   🏁 Statut fermé pour {tool_call_id}")
                        
                        # Si c'est un message de réponse finale de l'agent (sans appels d'outils)
                        elif (node_name == "agent" and 
                              hasattr(last_message, 'content') and 
                              last_message.content and
                              not (hasattr(last_message, 'tool_calls') and last_message.tool_calls)):
                            
                            print("   💬 DÉTECTION DE CONTENU DE RÉPONSE!")
                            # Yielder seulement le nouveau contenu pour éviter la duplication
                            current_content = last_message.content
                            if current_content != last_content:
                                # Simuler le yield du contenu
                                yielded_content.append(current_content)
                                print(f"   📤 Contenu yielded: {current_content[:80]}{'...' if len(current_content) > 80 else ''}")
                                last_content = current_content
        
        print()  # Ligne vide pour séparer les événements
    
    print("=" * 70)
    print("✅ Test terminé avec succès !")
    print(f"📊 Statuts actifs restants: {len(active_statuses)}")
    print(f"📝 Contenu yielded total: {len(yielded_content)} éléments")
    
    if yielded_content:
        print("\n📋 Résumé du contenu yielded:")
        for i, content in enumerate(yielded_content, 1):
            print(f"   {i}. {content[:60]}{'...' if len(content) > 60 else ''}")

def test_edge_cases():
    """Test des cas limites et edge cases."""
    print("\n🧪 Test des cas limites")
    print("=" * 40)
    
    # Test avec événement vide
    print("📥 Test événement vide...")
    event = {}
    print(f"   Résultat: {isinstance(event, dict)} (dict vide)")
    
    # Test avec message sans tool_calls
    print("📥 Test message sans tool_calls...")
    message = MockMessage(content="Test simple")
    print(f"   tool_calls: {message.tool_calls}")
    print(f"   hasattr tool_calls: {hasattr(message, 'tool_calls')}")
    
    # Test avec message ayant tool_calls vide
    print("📥 Test message avec tool_calls vide...")
    message_with_empty_calls = MockMessage(content="Test", tool_calls=[])
    print(f"   tool_calls: {message_with_empty_calls.tool_calls}")
    print(f"   bool(tool_calls): {bool(message_with_empty_calls.tool_calls)}")
    
    print("✅ Tests des cas limites terminés")

if __name__ == "__main__":
    test_process_streaming_events()
    test_edge_cases() 