"""
Configuracao central do EscolaGest.

Le as credenciais do Supabase de variaveis de ambiente / arquivo .env,
em vez de deixar chaves gravadas direto no codigo-fonte.

Como usar em qualquer arquivo do projeto:
    from config import SUPABASE_URL, SUPABASE_KEY
"""
import os

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
