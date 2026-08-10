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
            # 1. ENVIAR PARA A NUVEM PRIMEIRO (SELECT * garante que abas
            # como Diretores enviem tudo) — é o estado local atual, já
            # incluindo o que você acabou de editar/salvar agora.
            cursor.execute(f"SELECT * FROM {tab}")
            dados_locais = [dict(row) for row in cursor.fetchall()]

            envio_ok = True
            if dados_locais:
                res_envio = _requisicao_com_retry("POST", f"{URL}/{tab}", headers=HEADERS, json=dados_locais)
                if res_envio is None or res_envio.status_code not in (200, 201):
                    envio_ok = False
                    status = res_envio.status_code if res_envio is not None else "sem resposta"
                    texto = res_envio.text[:300] if res_envio is not None else ""
                    erros.append(f"{tab}: falha ao enviar pra nuvem (status {status})")
                    logger.error(f"Falha ao enviar {tab} pra nuvem: status {status} — {texto}")

            # 2. BUSCAR DA NUVEM DE VOLTA — só faz isso se o envio acima
            # funcionou. Se o envio falhou, a nuvem ainda está com uma
            # versão desatualizada, e trazer ela de volta agora apagaria
            # a sua edição local que nem chegou a ser enviada.
            if not envio_ok:
                continue

            res_busca = _requisicao_com_retry("GET", f"{URL}/{tab}", headers=HEADERS)
            if res_busca is not None and res_busca.status_code == 200:
                dados_nuvem = res_busca.json()

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
            elif res_busca is not None:
                erros.append(f"{tab}: falha ao buscar da nuvem (status {res_busca.status_code})")
                logger.error(f"Falha ao buscar {tab} da nuvem: status {res_busca.status_code} — {res_busca.text[:300]}")

        except Exception as e:
            erros.append(f"{tab}: {str(e)}")
            logger.error(f"Erro em {tab}: {e}")

    conn.close()
    return erros
