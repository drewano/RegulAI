"""
Agent LangGraph principal utilisant l'API fonctionnelle pour interagir avec le serveur MCP Légifrance.

Cet agent suit le patron d'architecture ReAct et utilise les décorateurs @task et @entrypoint
de LangGraph pour orchestrer les interactions avec le serveur MCP.

Implementation fidèle du guide how-tos/react-agent-from-scratch-functional.ipynb
"""

import os
from typing import cast
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.func import entrypoint, task
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from .tools import get_available_tools


def _set_env(var: str):
    """Helper pour définir une variable d'environnement si elle n'existe pas."""
    if not os.environ.get(var):
        import getpass
        os.environ[var] = getpass.getpass(f"{var}: ")


# Configuration du modèle LLM
_set_env("OPENAI_API_KEY")
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Récupération des outils MCP disponibles
tools = get_available_tools()
tools_by_name = {tool.name: tool for tool in tools}

# Configuration du checkpointer pour la persistance
checkpointer = MemorySaver()


@task
def call_model(messages):
    """Call model with a sequence of messages."""
    response = model.bind_tools(tools).invoke(messages)
    return response


@task
def call_tool(tool_call):
    """Execute tool call and return result as ToolMessage."""
    tool = tools_by_name[tool_call["name"]]
    observation = tool.invoke(tool_call["args"])
    return ToolMessage(content=str(observation), tool_call_id=tool_call["id"])


@entrypoint(checkpointer=checkpointer)
def agent(messages, previous):
    """
    Agent principal utilisant l'architecture ReAct.
    
    Implementation fidèle de l'exemple react-agent-from-scratch-functional.ipynb
    avec persistance des conversations.
    """
    # Ajouter les messages précédents si ils existent (persistance)
    if previous is not None:
        messages = add_messages(previous, messages)
    
    # Appel initial du modèle
    llm_response = cast(AIMessage, call_model(messages).result())
    
    # Boucle ReAct: raisonnement et action
    while True:
        # Si pas d'appels d'outils, on termine
        if not llm_response.tool_calls:
            break
        
        # Exécuter les outils en parallèle
        tool_result_futures = [
            call_tool(tool_call) for tool_call in llm_response.tool_calls
        ]
        tool_results = [fut.result() for fut in tool_result_futures]
        
        # Ajouter la réponse du LLM et les résultats des outils aux messages
        messages = add_messages(messages, [llm_response, *tool_results])
        
        # Appeler le modèle à nouveau avec les nouveaux résultats
        llm_response = cast(AIMessage, call_model(messages).result())
    
    # Générer la réponse finale et sauvegarder l'état
    messages = add_messages(messages, llm_response)
    return entrypoint.final(value=llm_response, save=messages)


def main():
    """Fonction principale pour tester l'agent."""
    # Message de test
    user_message = HumanMessage(content="Aide-moi à chercher des informations sur le droit du travail français.")
    
    print("🤖 Agent Légifrance démarré!")
    print(f"User: {user_message.content}")
    print("\n--- Réponse de l'agent ---")
    
    # Configuration pour la persistance
    config: RunnableConfig = {"configurable": {"thread_id": "test-thread"}}
    
    # Streaming de la réponse
    for step in agent.stream([user_message], config=config):
        for task_name, message in step.items():
            if task_name == "agent":
                continue  # On affiche seulement les mises à jour des tâches
            print(f"\n{task_name}:")
            if hasattr(message, 'pretty_print'):
                message.pretty_print()
            else:
                print(message)


if __name__ == "__main__":
    main() 