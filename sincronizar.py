import sys
import os
import re
import requests
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import get_connection
from config import SUPABASE_URL, SUPABASE_KEY, supabase_configurado
from logger_config import get_logger

logger = get_logger(__name__)

# Configurações do Supabase
URL = f"{SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

TIMEOUT_PADRAO = 30
MAX_TENTATIVAS = 3

def _requisicao_com_retry(metodo, url, **kwargs):
    """Executa a requisição com tentativas em caso de falha de rede."""
    kwargs.setdefault("timeout", TIMEOUT_PADRAO)
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            return requests.request(metodo, url, **kwargs)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if tentativa == MAX_TENTATIVAS: raise e
            logger.warning(f"Tentativa {tentativa} falhou. Tentando novamente...")

def executar_sincronismo():
    if not supabase_configurado():
        return ["Credenciais do Supabase não configuradas."]

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Descobre as tabelas, mas ignora tabelas internas do SQLite
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tabelas = [r[0] for r in cursor.fetchall()]
    
    erros = []

    for tab in tabelas:
        try:
            # 1. ENVIAR PARA A NUVEM (SELECT * garante que abas como Diretores enviem tudo)
            cursor.execute(f"SELECT * FROM {tab}")
            dados_locais = [dict(row) for row in cursor.fetchall()]
            
            if dados_locais:
                _requisicao_com_retry("POST", f"{URL}/{tab}", headers=HEADERS, json=dados_locais)

            # 2. BUSCAR DA NUVEM
            res = _requisicao_com_retry("GET", f"{URL}/{tab}", headers=HEADERS)
            if res.status_code == 200:
                dados_nuvem = res.json()
                
                # Sincroniza colunas dinamicamente
                cursor.execute(f"PRAGMA table_info({tab})")
                colunas_locais = [c[1] for c in cursor.fetchall()]

                for reg in dados_nuvem:
                    reg_filtrado = {k: v for k, v in reg.items() if k in colunas_locais}
                    id_val = reg_filtrado.get("id")
                    if not id_val: continue

                    cursor.execute(f"SELECT 1 FROM {tab} WHERE id = ?", (id_val,))
                    if cursor.fetchone():
                        # Atualiza localmente
                        sets = ", ".join([f"{k}=?" for k in reg_filtrado.keys()])
                        cursor.execute(f"UPDATE {tab} SET {sets} WHERE id=?", list(reg_filtrado.values()) + [id_val])
                    else:
                        # Insere novo localmente
                        cols = ", ".join(reg_filtrado.keys())
                        placeholders = ", ".join(["?" for _ in reg_filtrado])
                        cursor.execute(f"INSERT INTO {tab} ({cols}) VALUES ({placeholders})", list(reg_filtrado.values()))
            
            conn.commit()
        except Exception as e:
            erros.append(f"{tab}: {str(e)}")
            logger.error(f"Erro em {tab}: {e}")

    conn.close()
    return erros