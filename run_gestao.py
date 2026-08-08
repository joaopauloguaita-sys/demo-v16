"""
Empacotador do "Painel de Gestão" (gestao.py).
Não edite gestao.py por causa disso — este arquivo só chama ele por dentro.
"""
import os
import sys

def _pasta_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    os.chdir(_pasta_base())
    caminho_app = os.path.join(_pasta_base(), "gestao.py")

    try:
        from streamlit.web import cli as stcli
    except ImportError:
        from streamlit import cli as stcli  # versões mais antigas do Streamlit

    sys.argv = [
        "streamlit", "run", caminho_app,
        "--global.developmentMode=false",
        "--server.headless=false",
    ]
    sys.exit(stcli.main())
