import sqlite3
import os

def criar_tabela():
    db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cria a tabela de membros do Xadrez
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xadrez_membros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER UNIQUE,
            data_inclusao TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Tabela de Xadrez criada com sucesso!")

if __name__ == "__main__":
    criar_tabela()