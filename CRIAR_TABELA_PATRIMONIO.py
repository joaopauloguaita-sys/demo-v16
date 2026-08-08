import sqlite3
import os

def criar_tabela():
    db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patrimonio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_nome TEXT NOT NULL,
            numero_patrimonio TEXT,
            estado TEXT, -- Novo, Bom, Regular, Inservível
            localizacao TEXT, -- Sala 1, Biblioteca, etc.
            data_entrada TEXT,
            origem TEXT, -- Prefeitura, Escola, Doação
            observacao TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Tabela de Patrimônio criada!")

if __name__ == "__main__":
    criar_tabela()