"""
Configuracao central do EscolaGest.

Le as credenciais do Supabase de variaveis de ambiente / arquivo .env,
em vez de deixar chaves gravadas direto no codigo-fonte.

Como usar em qualquer arquivo do projeto:
    from config import SUPABASE_URL, SUPABASE_KEY
"""
import os

# Ponte com os "Secrets" do Streamlit Cloud: lá as chaves ficam em st.secrets,
# não em variável de ambiente comum. Isso copia pra os.environ pra não
# precisar mudar o resto do código, que já usa os.getenv() normalmente.
# Se não estiver rodando no Streamlit Cloud (ex: local), simplesmente não
# encontra nada e segue em frente sem erro.
try:
    import streamlit as st
    for _k, _v in st.secrets.items():
        os.environ.setdefault(_k, str(_v))
except Exception:
    pass

try:
    from dotenv import load_dotenv
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(_BASE_DIR, ".env"))
except ImportError:
    # python-dotenv nao instalado: segue usando so as variaveis de
    # ambiente do sistema (ex: definidas no Windows), sem travar o app.
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def supabase_configurado():
    """Retorna True se as credenciais do Supabase foram configuradas."""
    return bool(SUPABASE_URL and SUPABASE_KEY)
