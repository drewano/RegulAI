# Agent LangGraph pour Légifrance

Cet agent utilise LangGraph avec l'API fonctionnelle pour interagir avec le serveur MCP Légifrance via HTTP. Il suit le patron d'architecture ReAct (Reasoning and Acting) pour fournir des réponses intelligentes aux questions juridiques.

## Architecture

```
┌─────────────────┐    HTTP    ┌─────────────────┐
│                 │           │                 │
│  Agent LangGraph│◄─────────►│ Serveur MCP     │
│  (Client)       │           │ Légifrance      │
│                 │           │                 │
└─────────────────┘           └─────────────────┘
```

### Composants

1. **Agent Principal** (`main.py`) : 
   - Utilise l'API fonctionnelle de LangGraph avec `@entrypoint` et `@task`
   - Implémente le pattern ReAct avec persistance des conversations
   - Gère le cycle raisonnement → action → observation

2. **Outils MCP** (`tools.py`) :
   - Interface HTTP avec le serveur MCP Légifrance
   - Conversion des outils MCP en format LangChain
   - Gestion des erreurs et timeouts

3. **Fonctionnalités** :
   - Recherche dans la base Légifrance
   - Récupération d'articles spécifiques
   - Navigation dans les codes juridiques
   - Persistance des conversations

## API Fonctionnelle LangGraph

L'agent utilise les décorateurs suivants :

- `@task` : Pour définir des tâches individuelles (call_model, call_tool)
- `@entrypoint` : Pour le workflow principal avec persistance automatique
- `MemorySaver` : Pour la sauvegarde des états de conversation

## Utilisation

### Démarrage simple

```python
from src.agent.main import agent
from langchain_core.messages import HumanMessage

# Configuration
config = {"configurable": {"thread_id": "session-123"}}

# Message utilisateur
message = HumanMessage(content="Explique-moi le droit du travail français")

# Exécution avec streaming
for step in agent.stream([message], config=config):
    for task_name, result in step.items():
        if task_name != "agent":
            print(f"{task_name}: {result}")
```

### Test de connexion MCP

```python
from src.agent.tools import test_mcp_connection, get_mcp_server_info

# Vérifier la connexion
if test_mcp_connection():
    print("✅ Connexion MCP OK")
    info = get_mcp_server_info()
    print(f"Serveur: {info}")
else:
    print("❌ Serveur MCP indisponible")
```

## Configuration

### Variables d'environnement

- `OPENAI_API_KEY` : Clé API OpenAI (sera demandée interactivement si absente)
- `MCP_SERVER_URL` : URL du serveur MCP (par défaut: http://localhost:8000)

### Modèle LLM

Par défaut utilise `gpt-4o-mini`. Modifiable dans `main.py` :

```python
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

## Outils disponibles

1. **search_legifrance** : Recherche de textes juridiques
2. **get_article** : Récupération d'articles par ID
3. **browse_code** : Navigation dans les codes juridiques

## Exemple d'interaction

```
User: Quelles sont les règles sur les congés payés ?

Agent: Je vais chercher les informations sur les congés payés dans le Code du travail...

[call_tool: search_legifrance]
→ Recherche: "congés payés code du travail"

[call_model]
→ Analyse des résultats et formulation de la réponse

Réponse: D'après le Code du travail français, les congés payés sont régis par les articles L3141-1 et suivants...
```

## Prochaines étapes

1. **Récupération dynamique des outils** : Interroger le serveur MCP pour obtenir la liste des outils disponibles
2. **Amélioration du parsing** : Meilleure gestion des réponses complexes du serveur MCP
3. **Interface web** : Ajouter une interface Streamlit ou FastAPI
4. **Tests automatisés** : Suite de tests pour l'agent et les outils 