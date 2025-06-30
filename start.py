#!/usr/bin/env python3
"""
Script de lancement principal pour RegulAI.

Ce script lance séquentiellement :
1. Le serveur MCP (services/mcp/main.py) en arrière-plan
2. Vérifie que le serveur MCP est opérationnel via health check
3. Lance l'application Streamlit une fois le serveur MCP prêt

Usage:
    python start.py [--host HOST] [--port PORT] [--mcp-port MCP_PORT] [--timeout TIMEOUT]
"""

import asyncio
import atexit
import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import httpx


class RegulAILauncher:
    """Lanceur principal pour RegulAI - gère le serveur MCP et l'application Streamlit."""
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        streamlit_port: int = 8501,
        mcp_port: int = 8000,
        health_check_timeout: int = 30,
        health_check_interval: float = 1.0
    ):
        """
        Initialise le lanceur.
        
        Args:
            host: Adresse d'écoute pour les serveurs
            streamlit_port: Port pour l'application Streamlit
            mcp_port: Port pour le serveur MCP
            health_check_timeout: Timeout total pour le health check (secondes)
            health_check_interval: Intervalle entre les tentatives de health check (secondes)
        """
        self.host = host
        self.streamlit_port = streamlit_port
        self.mcp_port = mcp_port
        self.health_check_timeout = health_check_timeout
        self.health_check_interval = health_check_interval
        
        # Références vers les processus
        self.mcp_process: Optional[subprocess.Popen] = None
        self.streamlit_process: Optional[subprocess.Popen] = None
        
        # URLs des services
        self.mcp_url = f"http://{host}:{mcp_port}"
        self.streamlit_url = f"http://{host}:{streamlit_port}"
        
        # Registrer le nettoyage automatique
        atexit.register(self.cleanup)
        
        # Gestionnaire de signaux pour un arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour arrêt propre."""
        print(f"\n🛑 Signal {signum} reçu, arrêt en cours...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Nettoie les processus en cours."""
        print("🧹 Nettoyage des processus...")
        
        # Arrêter Streamlit en premier (moins critique)
        if self.streamlit_process and self.streamlit_process.poll() is None:
            print("   ⏹️  Arrêt de Streamlit...")
            try:
                self.streamlit_process.terminate()
                self.streamlit_process.wait(timeout=5)
                print("   ✅ Streamlit arrêté")
            except subprocess.TimeoutExpired:
                print("   ⚠️  Timeout - forçage de l'arrêt de Streamlit")
                self.streamlit_process.kill()
                self.streamlit_process.wait()
            except Exception as e:
                print(f"   ❌ Erreur lors de l'arrêt de Streamlit: {e}")
        
        # Arrêter le serveur MCP
        if self.mcp_process and self.mcp_process.poll() is None:
            print("   ⏹️  Arrêt du serveur MCP...")
            try:
                self.mcp_process.terminate()
                self.mcp_process.wait(timeout=5)
                print("   ✅ Serveur MCP arrêté")
            except subprocess.TimeoutExpired:
                print("   ⚠️  Timeout - forçage de l'arrêt du serveur MCP")
                self.mcp_process.kill()
                self.mcp_process.wait()
            except Exception as e:
                print(f"   ❌ Erreur lors de l'arrêt du serveur MCP: {e}")
    
    def _get_python_executable(self) -> str:
        """Trouve l'exécutable Python approprié."""
        # Utiliser le même Python que celui qui exécute ce script
        return sys.executable
    
    def _validate_paths(self) -> bool:
        """Valide que les fichiers requis existent."""
        mcp_main_path = Path("services/mcp/main.py")
        streamlit_app_path = Path("streamlit_app.py")
        
        if not mcp_main_path.exists():
            print(f"❌ Fichier MCP non trouvé: {mcp_main_path}")
            return False
        
        if not streamlit_app_path.exists():
            print(f"❌ Fichier Streamlit non trouvé: {streamlit_app_path}")
            return False
        
        return True
    
    def start_mcp_server(self) -> bool:
        """
        Lance le serveur MCP en arrière-plan.
        
        Returns:
            True si le processus a été lancé avec succès, False sinon
        """
        print("🚀 Lancement du serveur MCP...")
        
        try:
            # Définir les variables d'environnement pour le serveur MCP
            env = os.environ.copy()
            env["HOST"] = self.host
            env["PORT"] = str(self.mcp_port)
            
            # Lancer le serveur MCP
            self.mcp_process = subprocess.Popen(
                [self._get_python_executable(), "services/mcp/main.py"],
                cwd=os.getcwd(),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',  # Forcer l'encodage UTF-8
                errors='replace',  # Remplacer les caractères non décodables
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            print(f"   ✅ Processus MCP lancé (PID: {self.mcp_process.pid})")
            print(f"   🌐 URL du serveur: {self.mcp_url}")
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur lors du lancement du serveur MCP: {e}")
            return False
    
    def wait_for_mcp_health(self) -> bool:
        """
        Attend que le serveur MCP soit opérationnel via health check.
        
        Returns:
            True si le serveur répond correctement, False si timeout
        """
        print("🔍 Vérification de l'état du serveur MCP...")
        
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < self.health_check_timeout:
            attempt += 1
            
            try:
                # Essayer de se connecter au serveur MCP
                with httpx.Client(timeout=5.0) as client:
                    # Essayer le endpoint /invoke qui est le point d'entrée principal du serveur MCP
                    # selon l'architecture FastMCP streamable-http
                    try:
                        # Envoyer une requête de "ping" via le protocole MCP
                        payload = {
                            "method": "tools/list",
                            "params": {}
                        }
                        response = client.post(
                            f"{self.mcp_url}/invoke",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if response.status_code == 200:
                            # Vérifier que la réponse est au format MCP attendu
                            try:
                                result = response.json()
                                if "result" in result:
                                    print(f"   ✅ Serveur MCP opérationnel (tentative {attempt})")
                                    return True
                            except ValueError:
                                # Réponse non-JSON, mais le serveur répond
                                pass
                    except httpx.HTTPStatusError:
                        pass
                    
                    # Alternative: tester la connectivité de base sur l'endpoint racine
                    try:
                        response = client.get(f"{self.mcp_url}/")
                        if response.status_code in [200, 404, 405]:  # Le serveur répond
                            print(f"   ✅ Serveur MCP accessible (tentative {attempt})")
                            return True
                    except httpx.HTTPStatusError:
                        pass
                        
            except httpx.RequestError as e:
                # Serveur pas encore prêt
                if attempt % 5 == 0:  # Afficher les erreurs seulement toutes les 5 tentatives
                    print(f"   ⏳ Tentative {attempt}: {e}")
            
            except Exception as e:
                print(f"   ⚠️  Erreur inattendue (tentative {attempt}): {e}")
            
            # Vérifier si le processus MCP est toujours vivant
            if self.mcp_process and self.mcp_process.poll() is not None:
                print("   ❌ Le processus MCP s'est arrêté de manière inattendue")
                return_code = self.mcp_process.returncode
                print(f"   📊 Code de sortie: {return_code}")
                
                # Lire les logs d'erreur et de sortie
                try:
                    if self.mcp_process.stderr:
                        stderr_output = self.mcp_process.stderr.read()
                        if stderr_output.strip():
                            print(f"   📝 Erreurs MCP:")
                            for line in stderr_output.strip().split('\n'):
                                print(f"     {line}")
                    
                    if self.mcp_process.stdout:
                        stdout_output = self.mcp_process.stdout.read()
                        if stdout_output.strip():
                            print(f"   📄 Sortie MCP:")
                            for line in stdout_output.strip().split('\n'):
                                print(f"     {line}")
                except Exception as e:
                    print(f"   ⚠️  Impossible de lire les logs: {e}")
                return False
            
            time.sleep(self.health_check_interval)
        
        print(f"   ❌ Timeout après {self.health_check_timeout} secondes")
        return False
    
    def start_streamlit(self) -> bool:
        """
        Lance l'application Streamlit.
        
        Returns:
            True si le processus a été lancé avec succès, False sinon
        """
        print("🎨 Lancement de l'application Streamlit...")
        
        try:
            # Définir les variables d'environnement pour Streamlit
            env = os.environ.copy()
            
            # S'assurer que l'URL du serveur MCP est configurée
            env["MCP_SERVER_URL"] = self.mcp_url
            
            # Lancer Streamlit
            streamlit_cmd = [
                self._get_python_executable(),
                "-m", "streamlit", "run",
                "streamlit_app.py",
                "--server.address", self.host,
                "--server.port", str(self.streamlit_port),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ]
            
            self.streamlit_process = subprocess.Popen(
                streamlit_cmd,
                cwd=os.getcwd(),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',  # Forcer l'encodage UTF-8
                errors='replace'   # Remplacer les caractères non décodables
            )
            
            print(f"   ✅ Processus Streamlit lancé (PID: {self.streamlit_process.pid})")
            print(f"   🌐 URL de l'application: {self.streamlit_url}")
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur lors du lancement de Streamlit: {e}")
            return False
    
    def run(self) -> int:
        """
        Lance l'ensemble de l'application RegulAI.
        
        Returns:
            Code de sortie (0 = succès, 1 = erreur)
        """
        print("⚖️  === Démarrage de RegulAI ===")
        print(f"🏠 Répertoire de travail: {os.getcwd()}")
        print(f"🐍 Python: {self._get_python_executable()}")
        print()
        
        # Validation des fichiers
        if not self._validate_paths():
            return 1
        
        try:
            # Étape 1: Lancer le serveur MCP
            if not self.start_mcp_server():
                return 1
            
            # Étape 2: Attendre que le serveur MCP soit prêt
            if not self.wait_for_mcp_health():
                print("❌ Le serveur MCP n'a pas pu démarrer correctement")
                print()
                print("💡 Conseils de dépannage :")
                print("   • Vérifiez que les variables d'environnement OAuth sont configurées")
                print("   • Copiez .env.example vers .env et remplissez les valeurs")
                print("   • Vérifiez la documentation : cat USAGE_START.md")
                print("   • Consultez les logs ci-dessus pour plus de détails")
                return 1
            
            # Étape 3: Lancer Streamlit
            if not self.start_streamlit():
                return 1
            
            # Succès !
            print()
            print("🎉 === RegulAI lancé avec succès ! ===")
            print(f"🔗 Serveur MCP:        {self.mcp_url}")
            print(f"🌐 Application web:    {self.streamlit_url}")
            print()
            print("💡 Appuyez sur Ctrl+C pour arrêter tous les services")
            print("📖 Pour accéder à l'application, ouvrez votre navigateur sur:")
            print(f"   {self.streamlit_url}")
            print()
            
            # Attendre que les processus se terminent ou soient interrompus
            try:
                while True:
                    # Vérifier que les processus sont toujours vivants
                    if self.mcp_process and self.mcp_process.poll() is not None:
                        print("⚠️  Le serveur MCP s'est arrêté")
                        break
                    
                    if self.streamlit_process and self.streamlit_process.poll() is not None:
                        print("⚠️  L'application Streamlit s'est arrêtée")
                        break
                    
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n🛑 Arrêt demandé par l'utilisateur")
            
            return 0
            
        except Exception as e:
            print(f"❌ Erreur critique: {e}")
            return 1
        finally:
            self.cleanup()


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Lance RegulAI (serveur MCP + interface Streamlit)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="""
Exemples d'usage:
  python start.py                                   # Lancement par défaut
  python start.py --port 8080 --mcp-port 9000       # Ports personnalisés
  python start.py --host 0.0.0.0                    # Accessible depuis l'extérieur
  python start.py --timeout 60                      # Timeout plus long
        """
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Adresse d'écoute pour les serveurs"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port pour l'application Streamlit"
    )
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=8000,
        help="Port pour le serveur MCP"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout pour le health check du serveur MCP (secondes)"
    )
    parser.add_argument(
        "--check-interval",
        type=float,
        default=1.0,
        help="Intervalle entre les vérifications de health check (secondes)"
    )
    
    args = parser.parse_args()
    
    # Créer et lancer le lanceur
    launcher = RegulAILauncher(
        host=args.host,
        streamlit_port=args.port,
        mcp_port=args.mcp_port,
        health_check_timeout=args.timeout,
        health_check_interval=args.check_interval
    )
    
    exit_code = launcher.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 