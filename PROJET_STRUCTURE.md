# Structure du Projet RegulAI

## 🎯 Objectif

Construire un agent IA avec LangGraph qui interagit avec le serveur MCP Légifrance existant. L'architecture suit le pattern client-serveur où le serveur MCP s'exécute comme un service indépendant et l'agent LangGraph agit comme un client HTTP.

## 📁 Structure des Fichiers

```
RegulAI/
├── src/
│   ├── mcp/                    # Serveur MCP existant
│   └── agent/                  # 🆕 Nouvel agent LangGraph
│       ├── __init__.py         # Package Python
│       ├── main.py             # Agent principal (ReAct)
│       ├── tools.py            # Interface HTTP vers MCP
│       ├── test_agent.py       # Tests avec outils simulés
│       └── README.md           # Documentation agent
├── pyproject.toml              # ✅ Dépendances mises à jour
├── README.md                   # Documentation projet
└── PROJET_STRUCTURE.md         # Ce fichier
```

## 🏗️ Architecture

L'agent utilise l'**API fonctionnelle de LangGraph** avec les décorateurs :
- `@task` : Tâches individuelles (call_model, call_tool)
- `@entrypoint` : Workflow principal avec persistance
- **Pattern ReAct** : Reasoning → Action → Observation

## 📦 Dépendances Ajoutées

```toml
dependencies = [
    "fastmcp @ git+https://github.com/jlowin/fastmcp.git",  # Existant
    "langgraph>=0.2.16",           # 🆕 Framework principal
    "langchain-openai>=0.2.0",     # 🆕 Provider LLM
    "langchain-core>=0.3.0",       # 🆕 Messages et outils
    "httpx>=0.27.0",               # 🆕 Client HTTP
    "pydantic>=2.0.0"              # 🆕 Validation données
]
```

## 🔧 Composants Principaux

### 1. Agent Principal (`main.py`)
- **Architecture ReAct** avec boucle raisonnement/action
- **Persistance** des conversations via MemorySaver
- **Streaming** des réponses en temps réel
- **Gestion d'erreurs** robuste

### 2. Interface MCP (`tools.py`)
- **Client HTTP** vers le serveur MCP (localhost:8000)
- **Conversion** outils MCP → format LangChain
- **Outils disponibles** :
  - `search_legifrance` : Recherche textes juridiques
  - `get_article` : Récupération article par ID
  - `browse_code` : Navigation codes juridiques

### 3. Tests Simulés (`test_agent.py`)
- **Tests indépendants** sans serveur MCP
- **Outils mockés** avec données réalistes
- **Validation** du pattern ReAct

## 🚀 Utilisation

### Installation
```bash
pip install langgraph langchain-openai langchain-core httpx pydantic
```

### Test rapide
```bash
python src/agent/test_agent.py
```

### Utilisation avec serveur MCP
```python
from src.agent.main import agent
from langchain_core.messages import HumanMessage

# Configuration
config = {"configurable": {"thread_id": "session-123"}}
message = HumanMessage(content="Quelles sont les règles sur les congés payés?")

# Exécution
for step in agent.stream([message], config=config):
    for task_name, result in step.items():
        if task_name != "agent":
            print(f"{task_name}: {result}")
```

## 📋 Prochaines Étapes

### Phase 1 : Tests et Validation ✅
- [x] Structure du projet créée
- [x] Agent LangGraph implémenté
- [x] Interface HTTP vers MCP
- [x] Tests simulés fonctionnels
- [x] Outils avec décorateur @tool
- [x] Schémas Pydantic pour validation
- [x] Scripts de validation et exemples

### Phase 2 : Intégration MCP
- [ ] Démarrer le serveur MCP Légifrance
- [ ] Tester l'intégration complète
- [ ] Récupération dynamique des outils MCP
- [ ] Améliorer le parsing des réponses

### Phase 3 : Fonctionnalités Avancées
- [ ] Interface web (Streamlit/FastAPI)
- [ ] Cache des requêtes fréquentes
- [ ] Métriques et observabilité
- [ ] Tests automatisés complets

### Phase 4 : Production
- [ ] Déploiement containerisé
- [ ] Configuration via variables d'environnement
- [ ] Monitoring et alertes
- [ ] Documentation utilisateur

## 🔍 Points d'Attention

1. **Variables d'environnement** : OPENAI_API_KEY requis
2. **Serveur MCP** : Doit être démarré sur localhost:8000
3. **Format des réponses** : Adapter le parsing selon l'API MCP
4. **Gestion d'erreurs** : Timeout HTTP, erreurs réseau
5. **Rate limiting** : Limites API OpenAI et Légifrance

## 📚 Documentation de Référence

- **LangGraph Functional API** : how-tos/react-agent-from-scratch-functional.ipynb
- **Pattern ReAct** : Reasoning and Acting avec outils
- **MCP Protocol** : Model Context Protocol pour l'interopérabilité
- **Légifrance API** : Base de données juridique française

L'architecture est maintenant prête pour les tests d'intégration avec le serveur MCP réel ! 🎉 