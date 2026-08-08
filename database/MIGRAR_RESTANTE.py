import sqlite3
import requests
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SUPABASE_URL, SUPABASE_KEY, supabase_configurado

def migrar_tabela(cursor, tabela, url_supabase, key):
    try:
        print(f"Migrando {tabela}...")
        cursor.execute(f"SELECT * FROM {tabela}")
        dados = [dict(row) for row in cursor.fetchall()]
        
        for item in dados:
            if 'id' in item: del item['id']

        headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        response = requests.post(f"{url_supabase}/rest/v1/{tabela}", headers=headers, data=json.dumps(dados))
        
        if response.status_code in [200, 201]:
            print(f"Tabela {tabela} enviada com sucesso!")
        else:
            print(f"Erro em {tabela}: {response.text}")
    except Exception as e:
        print(f"Tabela {tabela} nao encontrada no PC ou erro: {e}")

def main():
    if not supabase_configurado():
        print("Erro: Credenciais do Supabase não configuradas (verifique o arquivo .env).")
        return

    diretorio = os.path.dirname(os.path.abspath(sys.argv[0]))
    db_path = None
    for arq in os.listdir(diretorio):
        if arq.lower().endswith('.db'):
            db_path = os.path.join(diretorio, arq)
            break
    
    if not db_path:
        print("Erro: Banco de dados nao encontrado.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Migra as outras duas tabelas importantes
    migrar_tabela(cursor, "turmas", SUPABASE_URL, SUPABASE_KEY)
    migrar_tabela(cursor, "dados_escola", SUPABASE_URL, SUPABASE_KEY)

    print("\n--- TUDO PRONTO NA NUVEM! ---")
    conn.close()

if __name__ == "__main__":
    main()
    input("\nPressione Enter para fechar...")
