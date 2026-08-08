import sqlite3
import os

def criar_tabela():
    db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cria a tabela de membros da Fanfarra/Baliza
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fanfarra_membros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER UNIQUE,
            categoria TEXT, -- 'FANFARRA' ou 'BALIZA'
            data_inclusao TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Tabela da Fanfarra criada com sucesso!")

if __name__ == "__main__":
    criar_tabela()