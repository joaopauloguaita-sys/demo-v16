import sqlite3
import os

def atualizar_banco():
    db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tabelas = ["professores", "funcionarios"]
    
    for tabela in tabelas:
        try:
            # Tenta adicionar a coluna matricula
            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN matricula TEXT")
            print(f"✅ Coluna 'matricula' adicionada na tabela {tabela}!")
        except sqlite3.OperationalError:
            print(f"ℹ️ A coluna 'matricula' já existia na tabela {tabela}.")
            
    conn.commit()
    conn.close()
    print("\nPronto! O banco de dados do seu PC foi atualizado.")

if __name__ == "__main__":
    atualizar_banco()