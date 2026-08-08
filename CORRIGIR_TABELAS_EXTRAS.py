import sqlite3
import os

def corrigir():
    db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tabelas = ["alunos", "professores", "funcionarios", "pedagogas", "secretarios", "diretores"]
    
    for tab in tabelas:
        print(f"Verificando tabela: {tab}")
        # Garante que a coluna 'arquivado' existe (padrão do seu sistema para ativos/inativos)
        try:
            cursor.execute(f"ALTER TABLE {tab} ADD COLUMN arquivado INTEGER DEFAULT 0")
            print(f"  ✅ Coluna 'arquivado' adicionada em {tab}")
        except: pass

        try:
            cursor.execute(f"ALTER TABLE {tab} ADD COLUMN ativo INTEGER DEFAULT 1")
            print(f"  ✅ Coluna 'ativo' adicionada em {tab}")
        except: pass

    conn.commit()
    conn.close()
    print("\n--- Tabelas sincronizadas! Pode abrir o sistema. ---")

if __name__ == "__main__":
    corrigir()