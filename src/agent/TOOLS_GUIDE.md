# Guide des Outils LangGraph pour Légifrance

Ce guide explique comment les outils de l'agent LangGraph sont construits avec le décorateur `@tool` pour interagir avec le serveur MCP Légifrance.

## 🏗️ Architecture des Outils

### Décorateur `@tool`

Chaque outil utilise le décorateur `@tool` de LangChain avec :
- **Nom personnalisé** : Identifiant unique pour l'agent
- **Schéma Pydantic** : Validation stricte des paramètres
- **Docstring parsée** : Description automatique pour le LLM

```python
@tool("search_legifrance", args_schema=SearchParams, parse_docstring=True)
def search_legifrance(query: str, max_results: int = 10) -> str:
    """
    Recherche des textes juridiques dans la base de données Légifrance.
    
    Args:
        query: Requête de recherche en français
        max_results: Nombre maximum de résultats
        
    Returns:
        Liste formatée des textes juridiques trouvés
    """
```

## 🔧 Outils Disponibles

### 1. `search_legifrance`
**Objectif** : Recherche de textes juridiques dans Légifrance

**Paramètres** :
- `query` (str) : Requête en français (ex: "congés payés")
- `max_results` (int) : Limite de résultats (défaut: 10)

**Exemples d'utilisation** :
```python
# Via l'agent
"Recherche des informations sur les congés payés"

# Appel direct
tool.invoke({"query": "droit du travail", "max_results": 5})
```

### 2. `get_article`
**Objectif** : Récupération d'articles juridiques spécifiques

**Paramètres** :
- `article_id` (str) : Identifiant de l'article (ex: "L3141-1")

**Exemples d'utilisation** :
```python
# Via l'agent
"Montre-moi l'article L3141-1 du Code du travail"

# Appel direct
tool.invoke({"article_id": "LEGIARTI000006900846"})
```

### 3. `browse_code`
**Objectif** : Navigation dans la structure des codes juridiques

**Paramètres** :
- `code_name` (str) : Nom du code (ex: "Code du travail")
- `section` (str, optionnel) : Section spécifique

**Exemples d'utilisation** :
```python
# Via l'agent
"Explore la structure du Code civil"

# Appel direct
tool.invoke({"code_name": "Code du travail", "section": "L3141"})
```

## 🔄 Communication avec le Serveur MCP

### Fonction `_make_mcp_request`

Point central de communication HTTP avec le serveur MCP :

```python
def _make_mcp_request(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """
    Fait un appel HTTP vers le serveur MCP pour exécuter un outil.
    
    Args:
        tool_name: Nom de l'outil MCP
        tool_args: Arguments à passer
    
    Returns:
        Réponse formatée en chaîne
    """
```

### Format de Requête

```json
{
    "method": "tools/call",
    "params": {
        "name": "search_legifrance",
        "arguments": {
            "query": "congés payés",
            "max_results": 10
        }
    }
}
```

### Endpoint

- **URL** : `http://localhost:8000/invoke`
- **Méthode** : POST
- **Headers** : `Content-Type: application/json`
- **Timeout** : 30 secondes

## 📝 Schémas Pydantic

### `SearchParams`
```python
class SearchParams(BaseModel):
    query: str = Field(description="Requête de recherche en français")
    max_results: int = Field(default=10, description="Nombre maximum de résultats")
```

### `ArticleParams`
```python
class ArticleParams(BaseModel):
    article_id: str = Field(description="Identifiant de l'article")
```

### `BrowseCodeParams`
```python
class BrowseCodeParams(BaseModel):
    code_name: str = Field(description="Nom du code juridique")
    section: Optional[str] = Field(default=None, description="Section spécifique")
```

## 🤖 Intégration avec l'Agent

### Création de l'Agent

```python
from langgraph.prebuilt import create_react_agent
from tools import get_available_tools

# Récupérer les outils
tools = get_available_tools()

# Créer l'agent ReAct
agent = create_react_agent(model, tools)
```

### Utilisation

```python
# Configuration de session
config = {"configurable": {"thread_id": "session-123"}}

# Question utilisateur
message = HumanMessage(content="Quelles sont les règles sur les congés payés ?")

# Exécution
result = agent.invoke({"messages": [message]}, config=config)
```

## 🔍 Exemples Concrets

### Recherche Simple
```
User: "Trouve des informations sur le licenciement économique"

Agent: 
1. 🔍 search_legifrance(query="licenciement économique", max_results=10)
2. 📖 Analyse des résultats
3. 💬 Réponse structurée avec références
```

### Consultation d'Article
```
User: "Que dit l'article L1233-3 ?"

Agent:
1. 📄 get_article(article_id="L1233-3")  
2. 📖 Analyse du contenu
3. 💬 Explication claire avec contexte
```

### Exploration de Code
```
User: "Comment est organisé le Code du travail ?"

Agent:
1. 🗂️ browse_code(code_name="Code du travail")
2. 📊 Présentation de la structure
3. 💬 Explication de l'organisation
```

## ⚙️ Configuration et Débogage

### Variables d'Environnement
```bash
export OPENAI_API_KEY="sk-..."
export MCP_SERVER_URL="http://localhost:8000"  # Optionnel
```

### Test de Connexion
```python
from tools import test_mcp_connection

if test_mcp_connection():
    print("✅ Serveur MCP accessible")
else:
    print("❌ Serveur MCP indisponible")
```

### Gestion d'Erreurs

Les outils gèrent automatiquement :
- **Erreurs de connexion** : Timeout, serveur indisponible
- **Erreurs HTTP** : Codes d'erreur, réponses malformées
- **Erreurs de parsing** : Validation des paramètres

## 📋 Bonnes Pratiques

### Pour l'Agent
1. **Descriptions claires** : Le LLM utilise les docstrings pour décider
2. **Validation stricte** : Schémas Pydantic pour éviter les erreurs
3. **Gestion d'erreurs** : Messages informatifs pour l'utilisateur

### Pour le Développeur
1. **Tests unitaires** : Chaque outil peut être testé individuellement
2. **Logging** : Traçabilité des appels MCP
3. **Configuration** : Paramètres via variables d'environnement

## 🚀 Extension des Outils

### Ajouter un Nouvel Outil

1. **Définir le schéma Pydantic** :
```python
class NewToolParams(BaseModel):
    param1: str = Field(description="Description du paramètre")
```

2. **Créer la fonction outil** :
```python
@tool("new_tool", args_schema=NewToolParams, parse_docstring=True)
def new_tool(param1: str) -> str:
    """Description de l'outil."""
    return _make_mcp_request("new_tool", {"param1": param1})
```

3. **Mettre à jour la liste** :
```python
def get_available_tools():
    return [search_legifrance, get_article, browse_code, new_tool]
```

### Personnaliser le Parsing

```python
def custom_parse_response(response: dict) -> str:
    """Parser personnalisé pour des réponses complexes."""
    # Logique de parsing spécifique
    return formatted_result
```

Cette architecture garantit une intégration robuste et extensible entre l'agent LangGraph et le serveur MCP Légifrance ! 🎯 