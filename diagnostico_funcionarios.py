import sqlite3, os

db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"
print(f"📂 Usando banco: {db_path}\n")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("===== COLUNAS DA TABELA 'funcionarios' =====")
cursor.execute("PRAGMA table_info(funcionarios)")
colunas = cursor.fetchall()
for c in colunas:
    print(f" - {c['name']} ({c['type']})")

print("\n===== PRIMEIROS 3 REGISTROS =====")
cursor.execute("SELECT * FROM funcionarios LIMIT 3")
linhas = cursor.fetchall()
if not linhas:
    print("⚠️ A tabela 'funcionarios' está vazia (nenhum registro cadastrado ainda).")
else:
    for linha in linhas:
        print(dict(linha))

conn.close()
print("\nPressione ENTER para sair.")
input()
