import sqlite3
import os

db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Ver colunas da tabela professores
print("\n🔍 Investigando tabela PROFESSORES:")
try:
    cursor.execute("PRAGMA table_info(professores)")
    cols = cursor.fetchall()
    if not cols: print("X Tabela professores está vazia ou não existe.")
    for col in cols:
        print(f"- {col[1]}")
except Exception as e:
    print(f"X Erro ao ler professores: {e}")

# 2. Listar todas as tabelas para achar as Atas
print("\n📋 Todas as tabelas no seu banco:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
for tab in cursor.fetchall():
    print(f"- {tab[0]}")

conn.close()
input("\nCopie o resultado acima e me mande. Pressione ENTER para sair...")
