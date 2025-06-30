# RegulAI - Assistant Juridique IA

Assistant IA spécialisé dans la recherche juridique française, utilisant l'architecture LangGraph et le protocole MCP (Model Context Protocol).

## 🚀 Démarrage Rapide

### Méthode recommandée (script de lancement automatique)

```bash
# Lancer l'ensemble de l'application
python start.py
```

Le script `start.py` lance automatiquement :
1. Le serveur MCP Légifrance
2. L'interface web Streamlit (une fois le serveur MCP opérationnel)

📖 **Documentation complète** : [USAGE_START.md](USAGE_START.md)

### Méthode manuelle (développement)

```bash
# Terminal 1 - Serveur MCP
cd services/mcp
python main.py

# Terminal 2 - Interface Streamlit
streamlit run streamlit_app.py
```

## ⚙️ Configuration

1. **Copiez le fichier de configuration** :
   ```bash
   cp .env.example .env
   ```

2. **Configurez vos variables d'environnement** dans `.env` :
   - `OAUTH_CLIENT_ID` et `OAUTH_CLIENT_SECRET` (API Légifrance)
   - `OPENAI_API_KEY` (OpenAI)

3. **Installez les dépendances** :
   ```bash
   pip install -e .
   # ou
   poetry install
   ```

## 📋 Prérequis

- Python 3.12+
- Accès à l'API Légifrance/PISTE (identifiants OAuth)
- Clé API OpenAI
- Connexion Internet

## 🏗️ Architecture

- **Frontend** : Streamlit (interface web conversationnelle)
- **Backend** : LangGraph (agent IA ReAct)  
- **API** : FastMCP (serveur MCP pour Légifrance)
- **LLM** : OpenAI GPT-4

## 📚 Documentation

- [Guide de lancement](USAGE_START.md) - Script `start.py`
- [Structure du projet](PROJET_STRUCTURE.md)
- `examples/` - Exemples d'utilisation
- `scripts/` - Scripts utilitaires

## 🛠️ Développement

```bash
# Tests
pytest tests/

# Validation des outils
python -m scripts.validate_tools

# Lancement en mode développement
python start.py --timeout 60
```

## 📄 Licence

MIT License - voir le fichier LICENSE pour plus de détails.
