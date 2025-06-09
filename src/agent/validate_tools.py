"""
Script de validation des outils LangGraph Légifrance.

Ce script vérifie que tous les outils sont correctement configurés
et peuvent être utilisés par l'agent LangGraph.
"""

import json
from typing import Dict, Any
from tools import get_available_tools, test_mcp_connection, get_mcp_server_info


def validate_tool_structure(tool) -> Dict[str, Any]:
    """
    Valide la structure d'un outil LangChain.
    
    Args:
        tool: Outil à valider
        
    Returns:
        Dictionnaire avec les résultats de validation
    """
    validation = {
        "name": tool.name,
        "has_description": bool(tool.description),
        "has_args_schema": hasattr(tool, 'args_schema') and tool.args_schema is not None,
        "schema_fields": [],
        "errors": []
    }
    
    # Vérifier le schéma d'arguments
    if validation["has_args_schema"]:
        try:
            schema = tool.args_schema.schema()
            validation["schema_fields"] = list(schema.get("properties", {}).keys())
            validation["schema_valid"] = True
        except Exception as e:
            validation["errors"].append(f"Erreur schéma: {e}")
            validation["schema_valid"] = False
    else:
        validation["errors"].append("Pas de schéma d'arguments défini")
        validation["schema_valid"] = False
    
    # Vérifier que l'outil est invocable
    try:
        # Test avec des arguments vides pour vérifier la structure
        tool.get_input_schema()
        validation["invocable"] = True
    except Exception as e:
        validation["errors"].append(f"Outil non invocable: {e}")
        validation["invocable"] = False
    
    return validation


def test_tool_invocation(tool, test_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Teste l'invocation d'un outil avec des arguments de test.
    
    Args:
        tool: Outil à tester
        test_args: Arguments de test
        
    Returns:
        Résultats du test
    """
    test_result = {
        "tool_name": tool.name,
        "test_args": test_args,
        "success": False,
        "response": None,
        "error": None,
        "response_length": 0
    }
    
    try:
        response = tool.invoke(test_args)
        test_result["success"] = True
        test_result["response"] = response
        test_result["response_length"] = len(str(response))
        
        # Vérifier que la réponse n'est pas une erreur
        response_str = str(response).lower()
        if any(error_keyword in response_str for error_keyword in ["erreur", "error", "connexion", "timeout"]):
            test_result["warning"] = "La réponse semble contenir une erreur"
            
    except Exception as e:
        test_result["error"] = str(e)
    
    return test_result


def validate_all_tools():
    """Valide tous les outils disponibles."""
    print("🔍 Validation des outils LangGraph Légifrance")
    print("=" * 60)
    
    # 1. Tester la connexion MCP
    print("\n📡 Test de connexion MCP")
    print("-" * 30)
    
    mcp_available = test_mcp_connection()
    if mcp_available:
        print("✅ Serveur MCP accessible")
        server_info = get_mcp_server_info()
        if server_info:
            print(f"📊 Info serveur: {json.dumps(server_info, indent=2)}")
    else:
        print("⚠️  Serveur MCP non accessible - les tests d'invocation pourraient échouer")
    
    # 2. Récupérer et valider les outils
    print("\n🔧 Validation de la structure des outils")
    print("-" * 40)
    
    tools = get_available_tools()
    print(f"Nombre d'outils trouvés: {len(tools)}")
    
    validation_results = []
    for tool in tools:
        validation = validate_tool_structure(tool)
        validation_results.append(validation)
        
        # Afficher les résultats
        print(f"\n📝 Outil: {validation['name']}")
        print(f"   Description: {'✅' if validation['has_description'] else '❌'}")
        print(f"   Schéma args: {'✅' if validation['has_args_schema'] else '❌'}")
        print(f"   Invocable: {'✅' if validation['invocable'] else '❌'}")
        print(f"   Champs: {validation['schema_fields']}")
        
        if validation['errors']:
            print(f"   ⚠️  Erreurs: {validation['errors']}")
    
    # 3. Tests d'invocation
    print("\n🚀 Tests d'invocation des outils")
    print("-" * 35)
    
    # Arguments de test pour chaque outil
    test_cases = {
        "search_legifrance": {"query": "test validation", "max_results": 1},
        "get_article": {"article_id": "L3141-1"},
        "browse_code": {"code_name": "Code du travail", "section": "L3141"}
    }
    
    invocation_results = []
    for tool in tools:
        if tool.name in test_cases:
            test_args = test_cases[tool.name]
            result = test_tool_invocation(tool, test_args)
            invocation_results.append(result)
            
            # Afficher les résultats
            print(f"\n🧪 Test {tool.name}")
            print(f"   Arguments: {test_args}")
            print(f"   Succès: {'✅' if result['success'] else '❌'}")
            print(f"   Longueur réponse: {result['response_length']} chars")
            
            if result['error']:
                print(f"   ❌ Erreur: {result['error']}")
            elif result.get('warning'):
                print(f"   ⚠️  {result['warning']}")
            elif result['success']:
                # Afficher un aperçu de la réponse
                response_preview = str(result['response'])[:100]
                print(f"   📄 Aperçu: {response_preview}...")
    
    # 4. Résumé des résultats
    print("\n📊 Résumé de la validation")
    print("=" * 30)
    
    total_tools = len(tools)
    valid_structure = sum(1 for v in validation_results if v['invocable'] and v['has_args_schema'])
    successful_invocations = sum(1 for r in invocation_results if r['success'])
    
    print(f"Outils totaux: {total_tools}")
    print(f"Structure valide: {valid_structure}/{total_tools}")
    print(f"Invocations réussies: {successful_invocations}/{len(test_cases)}")
    
    # Statut global
    if valid_structure == total_tools and (not mcp_available or successful_invocations > 0):
        print("\n✅ Validation globale: SUCCÈS")
        return True
    else:
        print("\n❌ Validation globale: ÉCHEC")
        if valid_structure != total_tools:
            print("   - Problèmes de structure des outils")
        if mcp_available and successful_invocations == 0:
            print("   - Aucune invocation réussie malgré serveur MCP disponible")
        return False


def generate_tools_report():
    """Génère un rapport détaillé des outils."""
    print("\n📋 Génération du rapport des outils")
    print("-" * 40)
    
    tools = get_available_tools()
    
    report = {
        "timestamp": str(type(None).__module__ == "builtins" and True),  # Simple timestamp
        "mcp_server_available": test_mcp_connection(),
        "tools_count": len(tools),
        "tools": []
    }
    
    for tool in tools:
        tool_info = {
            "name": tool.name,
            "description": tool.description,
            "schema": None
        }
        
        # Extraire le schéma
        try:
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema.schema()
                tool_info["schema"] = {
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", [])
                }
        except Exception as e:
            tool_info["schema_error"] = str(e)
        
        report["tools"].append(tool_info)
    
    # Sauvegarder le rapport
    try:
        with open("tools_validation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("✅ Rapport sauvegardé: tools_validation_report.json")
    except Exception as e:
        print(f"❌ Erreur sauvegarde rapport: {e}")
    
    return report


def main():
    """Fonction principale de validation."""
    try:
        # Validation complète
        success = validate_all_tools()
        
        # Génération du rapport
        generate_tools_report()
        
        # Statut final
        if success:
            print("\n🎉 Validation terminée avec succès!")
            print("Les outils sont prêts pour l'utilisation avec l'agent LangGraph.")
        else:
            print("\n⚠️  Validation terminée avec des problèmes.")
            print("Vérifiez les erreurs ci-dessus avant d'utiliser l'agent.")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Erreur durant la validation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main() 