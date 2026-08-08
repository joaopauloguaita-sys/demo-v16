import sqlite3
import requests
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SUPABASE_URL, SUPABASE_KEY, supabase_configurado

def migrar():
    if not supabase_configurado():
        print("ERRO: Credenciais do Supabase não configuradas (verifique o arquivo .env).")
        return

    diretorio = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # PEGA O PRIMEIRO ARQUIVO QUE TERMINAR COM .DB NA PASTA
    db_path = None
    for arq in os.listdir(diretorio):
        if arq.lower().endswith('.db'):
            db_path = os.path.join(diretorio, arq)
            break
    
    if not db_path:
        print(f"ERRO: Nao encontrei NENHUM arquivo .db na pasta:\n{diretorio}")
        return

    print(f"BANCO ENCONTRADO: {os.path.basename(db_path)}")
    print("Iniciando migracao...")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM alunos")
        alunos = [dict(row) for row in cursor.fetchall()]
        for aluno in alunos:
            if 'id' in aluno: del aluno['id']

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        for i in range(0, len(alunos), 50):
            lote = alunos[i:i+50]
            response = requests.post(f"{SUPABASE_URL}/rest/v1/alunos", headers=headers, data=json.dumps(lote))
            if response.status_code in [200, 201]:
                print(f"Lote {i//50 + 1} enviado com sucesso!")
            else:
                print(f"Erro no lote {i//50 + 1}: {response.text}")

        print("\n--- MIGRACAO CONCLUIDA! SEUS ALUNOS ESTAO NA NUVEM! ---")
    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrar()
    input("\nPressione Enter para fechar...")
