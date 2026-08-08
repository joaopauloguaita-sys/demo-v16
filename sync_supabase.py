import sqlite3, requests, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import SUPABASE_URL, SUPABASE_KEY, supabase_configurado
from logger_config import get_logger

logger = get_logger(__name__)

TIMEOUT_PADRAO = 30

def sync_table(cursor, local_query, remote_table):
    print(f"Sincronizando: {remote_table}...", end=" ")
    try:
        cursor.execute(local_query)
        data = [dict(row) for row in cursor.fetchall()]
        if not data:
            print("⚠️ Vazia.")
            return
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        response = requests.post(f"{SUPABASE_URL}/rest/v1/{remote_table}", headers=headers,
                                  data=json.dumps(data), timeout=TIMEOUT_PADRAO)
        if response.status_code in [200, 201]:
            print("✅ OK")
        else:
            print(f"❌ Erro Supabase: {response.text}")
            logger.error("Erro Supabase ao sincronizar %s: %s", remote_table, response.text[:300])
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        print(f"❌ Sem conexão: {e}")
        logger.exception("Erro de rede ao sincronizar %s", remote_table)
    except Exception as e:
        # Antes isso mostrava sempre a mesma mensagem genérica ("Coluna não encontrada").
        # Agora mostra o erro real, pra facilitar descobrir o que aconteceu (ex: tabela
        # local que não existe, coluna com nome diferente, etc.)
        print(f"❌ Erro local: {e}")
        logger.exception("Erro local ao sincronizar %s", remote_table)

def sync():
    if not supabase_configurado():
        print("❌ Credenciais do Supabase não configuradas (verifique o arquivo .env).")
        logger.error("Credenciais do Supabase não configuradas.")
        return
    db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    print("🚀 Sincronização...\n")

    # Básicos
    sync_table(cursor, "SELECT * FROM alunos WHERE ativo = 1", "alunos")
    sync_table(cursor, "SELECT * FROM turmas", "turmas")
    sync_table(cursor, "SELECT * FROM dados_escola", "dados_escola")
    sync_table(cursor, "SELECT id, nome, cargo, situacao_funcional, telefone1, telefone2 FROM professores", "professores")
    sync_table(cursor, "SELECT id, nome FROM diretores", "diretores")
    sync_table(cursor, "SELECT id, nome FROM secretarios", "secretarios")

    # Funcionários (equipe de apoio, fora do quadro de professores)
    sync_table(cursor, "SELECT id, nome, cargo, situacao_funcional, telefone1, telefone2 FROM funcionarios", "funcionarios")

    # Tenta enviar as Atas de qualquer jeito (SELECT *)
    sync_table(cursor, "SELECT * FROM atas", "atas")

    # Tenta enviar os Horários de qualquer jeito (SELECT *)
    sync_table(cursor, "SELECT * FROM horarios", "horarios")

    conn.close()
    print("\n✅ FIM! Pressione ENTER.")
    input()

if __name__ == "__main__":
    sync()
