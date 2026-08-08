import sqlite3, os

db_path = "database/database.db" if os.path.exists("database/database.db") else "database.db"
print(f"📂 Usando banco: {db_path}\n")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def inspecionar(tabela):
    print(f"\n===== COLUNAS DA TABELA '{tabela}' =====")
    try:
        cursor.execute(f"PRAGMA table_info({tabela})")
        colunas = cursor.fetchall()
        if not colunas:
            print("⚠️ Tabela não encontrada.")
            return
        for c in colunas:
            print(f" - {c['name']} ({c['type']})")

        print(f"\n----- 1 REGISTRO DE EXEMPLO ({tabela}) -----")
        cursor.execute(f"SELECT * FROM {tabela} LIMIT 1")
        linha = cursor.fetchone()
        if linha:
            print(dict(linha))
        else:
            print("⚠️ Tabela vazia.")
    except Exception as e:
        print(f"❌ Erro ao inspecionar '{tabela}': {e}")

# Tabela principal de alunos
inspecionar("alunos")

# Tabelas de turma/série (para ver como série/turma/turno estão nomeados)
inspecionar("turmas")

# Possíveis tabelas de responsável (tenta os nomes mais comuns; ignora as que não existirem)
for nome_tabela in ["responsaveis", "responsavel", "pais", "familia"]:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (nome_tabela,))
    if cursor.fetchone():
        inspecionar(nome_tabela)

# Lista todas as tabelas existentes no banco, só pra termos o panorama completo
print("\n===== TODAS AS TABELAS DO BANCO =====")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for t in cursor.fetchall():
    print(f" - {t['name']}")

conn.close()
print("\nPressione ENTER para sair.")
input()
