import sqlite3, os

db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"
print(f"📂 Usando banco: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

migracoes = [
    ("professores", "telefone", "TEXT"),
    ("funcionarios", "telefone", "TEXT"),
]

for tabela, coluna, tipo in migracoes:
    try:
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
        print(f"✅ Coluna '{coluna}' adicionada em '{tabela}'.")
    except sqlite3.OperationalError as e:
        # Se a coluna já existir, o SQLite avisa aqui e o script segue normalmente.
        print(f"⚠️ '{tabela}.{coluna}': {e}")

conn.commit()
conn.close()

print("\n✅ Migração concluída. Pressione ENTER.")
input()
