"""
Application Streamlit pour RegulAI - Assistant Juridique IA.

Cette application fournit une interface web pour interagir avec l'agent RegulAI,
spécialisé dans la recherche juridique française.
"""

import streamlit as st
import os
import uuid
import traceback
from typing import Optional, Dict, Any, Generator

# Configuration de la page
st.set_page_config(
    page_title="RegulAI - Assistant Juridique",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def generate_thread_id() -> str:
    """Génère un identifiant unique pour la conversation."""
    return f"streamlit-session-{uuid.uuid4().hex[:8]}"


def get_api_key_from_sources() -> tuple[Optional[str], str]:
    """
    Récupère la clé API Google depuis différentes sources.
    
    Returns:
        tuple: (clé_api, source) où source indique d'où vient la clé
    """
    # Vérifier les secrets Streamlit
    try:
        api_key_from_secrets = st.secrets.get("GOOGLE_API_KEY")
        if api_key_from_secrets:
            return api_key_from_secrets, "secrets.toml"
    except (KeyError, FileNotFoundError):
        pass
    
    # Vérifier les variables d'environnement
    api_key_from_env = os.getenv("GOOGLE_API_KEY")
    if api_key_from_env:
        return api_key_from_env, "variables d'environnement"
    
    return None, "non trouvée"


def mask_api_key(api_key: str) -> str:
    """Masque la clé API pour l'affichage sécurisé."""
    if len(api_key) > 12:
        return f"{api_key[:8]}...{api_key[-4:]}"
    return "clé trop courte"


# ============================================
# GESTION DES ERREURS ET VALIDATION
# ============================================

def test_mcp_server_connection() -> tuple[bool, str]:
    """
    Test la connexion au serveur MCP.
    
    Returns:
        tuple: (succès, message_status)
    """
    try:
        from src.regulai.tools import test_mcp_connection
        is_connected = test_mcp_connection()
        if is_connected:
            return True, "✅ Serveur MCP accessible"
        else:
            return False, "❌ Serveur MCP non accessible"
    except ImportError:
        return False, "❌ Modules RegulAI non disponibles"
    except Exception as e:
        return False, f"❌ Erreur de connexion MCP : {str(e)}"


def validate_agent_configuration() -> tuple[bool, str]:
    """
    Valide la configuration de l'agent.
    
    Returns:
        tuple: (valide, message_status)
    """
    try:
        from src.regulai.config import get_config
        config = get_config()
        return True, "✅ Configuration validée"
    except Exception as e:
        return False, f"❌ Erreur de configuration : {str(e)}"


# ============================================
# INITIALISATION ET CACHE DE L'AGENT
# ============================================

@st.cache_resource
def initialize_agent(google_api_key: str):
    """
    Initialise l'agent RegulAI une seule fois et le met en cache.
    
    Args:
        google_api_key: Clé API Google pour l'initialisation
        
    Returns:
        Agent LangGraph compilé ou None en cas d'erreur
    """
    try:
        # Configurer temporairement la clé API dans l'environnement
        os.environ["GOOGLE_API_KEY"] = google_api_key
        
        # Import et création de l'agent
        from src.regulai.agent import create_agent
        agent = create_agent()
        
        return agent
    except ImportError as e:
        st.error(f"❌ Erreur d'import des modules RegulAI : {e}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur lors de l'initialisation de l'agent : {e}")
        return None


# ============================================
# TRAITEMENT DU STREAMING
# ============================================

def process_streaming_events(stream_generator) -> Generator[str, None, None]:
    """
    Traite les événements de streaming de l'agent pour afficher les étapes intermédiaires.
    
    Args:
        stream_generator: Générateur d'événements de streaming de l'agent (mode "updates")
        
    Yields:
        str: Contenu à afficher pour le streaming de texte
        
    Cette fonction intercepte les événements de streaming pour:
    - Détecter les appels d'outils et afficher un indicateur de statut
    - Permettre l'affichage des étapes intermédiaires de l'agent
    - Maintenir la compatibilité avec st.write_stream
    """
    active_statuses = {}  # Pour traquer les statuses actifs par outil
    last_content = ""  # Pour éviter la duplication de contenu
    
    try:
        for event in stream_generator:
            # Les événements en mode "updates" sont des dictionnaires avec des clés de nœuds
            if isinstance(event, dict):
                # Parcourir chaque nœud dans l'événement
                for node_name, node_data in event.items():
                    # Vérifier s'il y a des messages dans les données du nœud
                    if isinstance(node_data, dict) and "messages" in node_data:
                        messages = node_data["messages"]
                        if messages:
                            last_message = messages[-1]
                            
                            # Détecter les appels d'outils dans les messages AI (nœud "agent")
                            if node_name == "agent" and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
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
                                        active_statuses[tool_id] = st.status(status_message, expanded=False)
                            
                            # Détecter les réponses d'outils (nœud "tools")
                            elif node_name == "tools" and hasattr(last_message, 'tool_call_id'):
                                tool_call_id = last_message.tool_call_id
                                # Fermer le statut correspondant s'il existe
                                if tool_call_id in active_statuses:
                                    status = active_statuses[tool_call_id]
                                    status.update(label="✅ Terminé", state="complete")
                                    # Retirer de la liste des statuses actifs
                                    del active_statuses[tool_call_id]
                            
                            # Si c'est un message de réponse finale de l'agent (sans appels d'outils)
                            elif (node_name == "agent" and 
                                  hasattr(last_message, 'content') and 
                                  last_message.content and
                                  not (hasattr(last_message, 'tool_calls') and last_message.tool_calls)):
                                
                                # Yielder seulement le nouveau contenu pour éviter la duplication
                                current_content = last_message.content
                                if current_content != last_content:
                                    # Yield le contenu complet (st.write_stream gère l'affichage progressif)
                                    yield current_content
                                    last_content = current_content
            else:
                # Si ce n'est pas un événement structuré attendu, essayer de le traiter comme du texte
                content_str = str(event) if event else ""
                if content_str and content_str.strip() and content_str != last_content:
                    yield content_str
                    last_content = content_str
    
    except Exception as e:
        yield f"❌ Erreur lors du traitement du streaming : {str(e)}"


# ============================================
# GESTION DE LA CONVERSATION
# ============================================

def handle_user_message(prompt: str, agent) -> Optional[str]:
    """
    Traite un message utilisateur et retourne la réponse de l'agent.
    
    Args:
        prompt: Message de l'utilisateur
        agent: Instance de l'agent RegulAI
        
    Returns:
        Réponse de l'agent ou None en cas d'erreur
    """
    try:
        # Import de la fonction de streaming
        from src.regulai.agent import stream_agent_conversation
        
        # Créer le générateur de streaming pour l'agent RegulAI avec détection d'outils
        raw_stream_generator = stream_agent_conversation(
            message=prompt,
            thread_id=st.session_state.thread_id,
            agent=agent
        )
        
        # Traiter les événements pour afficher les statuts d'outils
        processed_stream = process_streaming_events(raw_stream_generator)
        
        # Utiliser st.write_stream pour afficher la réponse en temps réel
        # st.write_stream consomme le générateur et retourne le contenu complet
        response_content = st.write_stream(processed_stream)
        
        # S'assurer que le retour est toujours une chaîne
        if isinstance(response_content, list):
            return "\n".join(str(item) for item in response_content)
        elif response_content is not None:
            return str(response_content)
        else:
            return None
        
    except ImportError as e:
        st.error(f"❌ Erreur d'import : {e}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur lors du traitement de votre demande : {str(e)}")
        st.error("💡 Vérifiez votre configuration et réessayez.")
        return None


def reset_conversation():
    """Réinitialise complètement la conversation."""
    if "messages" in st.session_state:
        st.session_state.messages = []
    
    # Générer un nouveau thread_id pour une nouvelle conversation
    st.session_state.thread_id = generate_thread_id()
    
    # Remettre le message de bienvenue
    welcome_message = {
        "role": "assistant", 
        "content": "Bonjour ! Je suis RegulAI, votre assistant juridique spécialisé dans le droit français. Comment puis-je vous aider aujourd'hui ?"
    }
    st.session_state.messages.append(welcome_message)


# ============================================
# COMPOSANTS DE L'INTERFACE
# ============================================

def render_welcome_section():
    """Affiche la section de bienvenue."""
    st.title("⚖️ RegulAI - Assistant Juridique")
    st.subheader("🤖 Votre assistant IA spécialisé en recherche juridique française")
    
    st.markdown("""
    ---
    ### Bienvenue sur RegulAI !

    RegulAI est un assistant IA intelligent spécialisé dans la recherche juridique française. 
    Il utilise l'architecture LangGraph et des outils MCP pour vous fournir des réponses précises 
    et actualisées sur le droit français.

    **Fonctionnalités principales :**
    - 🔍 Recherche juridique avancée
    - 📚 Accès aux bases de données légales
    - 🎯 Réponses contextuelles et précises
    - 💬 Interface conversationnelle intuitive

    ---
    """)


def render_api_key_configuration():
    """
    Gère la configuration de la clé API Google dans la sidebar.
    
    Returns:
        bool: True si la clé API est configurée, False sinon
    """
    st.subheader("🔑 Clé API Google")
    
    # Vérifier les sources existantes
    api_key_from_sources, source = get_api_key_from_sources()
    
    # Initialiser la session state pour la clé API
    if "google_api_key" not in st.session_state:
        st.session_state.google_api_key = api_key_from_sources or ""
    
    # Champ de saisie de la clé API (type password pour la sécurité)
    user_api_key = st.text_input(
        label="Entrez votre clé API Google :",
        type="password",
        value=st.session_state.google_api_key if source == "non trouvée" else "",
        placeholder="AI..." if source == "non trouvée" else f"Clé configurée via {source}",
        help="Votre clé API sera stockée de manière sécurisée dans la session.",
        disabled=bool(source != "non trouvée"),
        key="api_key_input"
    )
    
    # Mettre à jour la session state si l'utilisateur a saisi une clé
    if user_api_key and source == "non trouvée":
        st.session_state.google_api_key = user_api_key
    
    # Affichage du statut de la clé API
    if st.session_state.google_api_key:
        if source != "non trouvée":
            st.success(f"✅ Clé API chargée depuis {source}")
        else:
            st.success("✅ Clé API saisie par l'utilisateur")
        
        # Masquer la clé (afficher seulement les premiers et derniers caractères)
        masked_key = mask_api_key(st.session_state.google_api_key)
        st.caption(f"🔒 Clé active : `{masked_key}`")
        
        return True
    else:
        st.error("❌ Aucune clé API configurée")
        return False


def render_system_status():
    """Affiche l'état du système dans la sidebar."""
    st.header("📋 État du système")
    
    # Vérifier la configuration
    config_valid, config_msg = validate_agent_configuration()
    
    # Vérifier la connexion MCP
    mcp_connected, mcp_msg = test_mcp_server_connection()
    
    # État de l'agent
    agent_status = "❌ Non initialisé"
    if st.session_state.get("google_api_key"):
        try:
            agent = initialize_agent(st.session_state.google_api_key)
            agent_status = "✅ Opérationnel" if agent else "❌ Erreur d'initialisation"
        except:
            agent_status = "❌ Erreur d'initialisation"
    
    st.markdown(f"""
    **Version :** 0.2.0
    
    **État des composants :**
    - 🔧 Configuration : {config_msg}
    - 🤖 Agent RegulAI : {agent_status}
    - 🔗 Serveur MCP : {mcp_msg}
    - ✅ Interface Streamlit : Opérationnelle
    
    **Besoin d'aide ?**
    - 📖 Documentation dans le README
    - 🔧 Exemples dans `/examples`
    - 🔑 [Obtenir une clé API Google](https://aistudio.google.com/app/apikey)
    """)


def render_conversation_actions():
    """Affiche les actions de conversation dans la sidebar."""
    if not st.session_state.get("google_api_key"):
        return
    
    st.subheader("💬 Actions")
    
    col1, col2 = st.columns(2)
    
    # Bouton pour nouvelle conversation
    with col1:
        if st.button("🆕 Nouvelle", help="Démarrer une nouvelle conversation", type="primary"):
            reset_conversation()
            st.rerun()
    
    # Bouton pour réinitialiser l'agent
    with col2:
        if st.button("🔄 Reset Agent", help="Réinitialiser l'agent en cas de problème", type="secondary"):
            # Vider le cache de l'agent pour le forcer à se réinitialiser
            initialize_agent.clear()
            st.rerun()
    
    # Afficher les informations de session
    if "messages" in st.session_state:
        msg_count = len(st.session_state.messages)
        st.caption(f"📝 Messages : {msg_count}")
    
    if "thread_id" in st.session_state:
        st.caption(f"🔗 Session : `{st.session_state.thread_id}`")
    
    # Indicateur de streaming
    st.caption("💬 Mode streaming activé")


def render_chat_interface():
    """Affiche l'interface de chat principale."""
    # Initialiser l'identifiant de conversation unique
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = generate_thread_id()
    
    # Initialiser l'historique de conversation dans session_state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Message de bienvenue
        welcome_message = {
            "role": "assistant", 
            "content": "Bonjour ! Je suis RegulAI, votre assistant juridique spécialisé dans le droit français. Comment puis-je vous aider aujourd'hui ?"
        }
        st.session_state.messages.append(welcome_message)
    
    # Afficher l'historique des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Champ de saisie pour les nouveaux messages
    if prompt := st.chat_input("Posez votre question juridique..."):
        # Ajouter le message utilisateur à l'historique
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)
        
        # Afficher le message utilisateur
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Obtenir l'agent initialisé
        try:
            agent = initialize_agent(st.session_state.google_api_key)
            
            if agent:
                # Afficher la réponse de l'agent avec streaming et statut des outils
                with st.chat_message("assistant"):
                    response_content = handle_user_message(prompt, agent)
                    
                    if response_content:
                        # Ajouter la réponse à l'historique
                        assistant_message = {"role": "assistant", "content": response_content}
                        st.session_state.messages.append(assistant_message)
                    else:
                        # En cas d'erreur, ajouter un message d'erreur générique
                        error_msg = "❌ Impossible de traiter votre demande. Veuillez réessayer."
                        st.markdown(error_msg)
                        assistant_message = {"role": "assistant", "content": error_msg}
                        st.session_state.messages.append(assistant_message)
            else:
                # Agent non initialisé - afficher un message d'erreur
                error_msg = "❌ **Agent non disponible**\n\nL'agent RegulAI n'a pas pu être initialisé. Vérifiez votre clé API Google."
                
                with st.chat_message("assistant"):
                    st.markdown(error_msg)
                
                assistant_message = {"role": "assistant", "content": error_msg}
                st.session_state.messages.append(assistant_message)
                
        except Exception as e:
            # Erreur générale d'initialisation
            error_msg = f"❌ **Erreur système**\n\n{str(e)}"
            
            with st.chat_message("assistant"):
                st.markdown(error_msg)
            
            assistant_message = {"role": "assistant", "content": error_msg}
            st.session_state.messages.append(assistant_message)


def render_configuration_warning():
    """Affiche les instructions de configuration si nécessaire."""
    st.warning("""
    ⚠️ **Configuration requise**
    
    Pour utiliser RegulAI, vous devez configurer votre clé API Google. 
    
    **Options de configuration :**
    
    1. **Via la barre latérale** ← Saisissez votre clé dans le champ à gauche
    2. **Via un fichier secrets.toml** ← Créez `.streamlit/secrets.toml` :
       ```toml
       GOOGLE_API_KEY = "AI-votre-clé-ici"
       ```
    3. **Via les variables d'environnement** ← Définissez `GOOGLE_API_KEY`
    
    [🔗 Obtenir une clé API Google](https://aistudio.google.com/app/apikey)
    """)
    
    st.info("💡 **Votre clé API est sécurisée** - Elle est stockée uniquement dans votre session et jamais transmise ailleurs que vers l'API Google.")


# ============================================
# APPLICATION PRINCIPALE
# ============================================

def main():
    """Fonction principale de l'application."""
    try:
        # Afficher la section de bienvenue
        render_welcome_section()
        
        # Sidebar - Configuration et état
        with st.sidebar:
            st.header("🔧 Configuration")
            
            # Configuration de la clé API
            api_key_configured = render_api_key_configuration()
            
            st.divider()
            
            # Actions de conversation
            render_conversation_actions()
            
            st.divider()
            
            # État du système
            render_system_status()
        
        # Interface principale
        if not api_key_configured:
            render_configuration_warning()
        else:
            st.success("✅ Configuration terminée ! Vous pouvez maintenant commencer à converser avec RegulAI.")
            render_chat_interface()
    
    except Exception as e:
        st.error(f"❌ **Erreur critique de l'application**")
        st.error(f"Détails : {str(e)}")
        
        # Afficher la stack trace en mode développement
        if st.checkbox("🔧 Afficher les détails techniques", help="Pour le debugging"):
            st.code(traceback.format_exc())
        
        st.info("💡 Essayez de recharger la page ou contactez le support si le problème persiste.")


if __name__ == "__main__":
    main() 