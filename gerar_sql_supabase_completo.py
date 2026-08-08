"""
Gera um arquivo SQL completo, direto do seu banco de dados real, com TODAS
as tabelas e TODAS as colunas que existem hoje - sem precisar eu adivinhar
nada. Cole o resultado no SQL Editor do Supabase.

COMO USAR:
    python gerar_sql_supabase_completo.py

Isso cria o arquivo "supabase_completo.sql" na mesma pasta. Abra ele,
copie tudo, cole no SQL Editor do Supabase e rode.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import get_connection, inicializar_banco

# Atualiza o banco local primeiro - garante que TODAS as colunas mais novas
# já existam localmente antes de gerar o SQL, mesmo que você não tenha
# aberto o sistema com a versão mais recente ainda
inicializar_banco()

# Tradução de tipo do SQLite pro tipo mais parecido no Postgres (Supabase)
MAPA_TIPOS = {
    "INTEGER": "BIGINT",
    "INT": "BIGINT",
    "REAL": "DOUBLE PRECISION",
    "FLOAT": "DOUBLE PRECISION",
    "DOUBLE": "DOUBLE PRECISION",
    "TEXT": "TEXT",
    "VARCHAR": "TEXT",
    "CHAR": "TEXT",
    "BLOB": "TEXT",
    "BOOLEAN": "BOOLEAN",
    "DATE": "TEXT",
    "DATETIME": "TEXT",
}


def tipo_postgres(tipo_sqlite):
    tipo_sqlite = (tipo_sqlite or "TEXT").upper()
    for chave, valor in MAPA_TIPOS.items():
        if chave in tipo_sqlite:
            return valor
    return "TEXT"


def main():
    conn = get_connection()
    cursor = conn.cursor()

    tabelas = [r[0] for r in cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]

    linhas = [
        "-- ============================================================",
        "-- SQL COMPLETO - gerado automaticamente a partir do banco real",
        "-- Cole tudo isso no SQL Editor do Supabase e clique em RUN.",
        "-- Seguro rodar mais de uma vez (não apaga nenhum dado existente).",
        "-- ============================================================",
        "",
    ]

    for tabela in tabelas:
        colunas = cursor.execute(f"PRAGMA table_info({tabela})").fetchall()
        if not colunas:
            continue

        # Acha a coluna que é chave primária (geralmente "id")
        col_pk = next((c[1] for c in colunas if c[5] == 1), "id")

        linhas.append(f"-- Tabela: {tabela}")
        linhas.append(f'CREATE TABLE IF NOT EXISTS "{tabela}" ("{col_pk}" BIGINT PRIMARY KEY);')
        for col in colunas:
            nome_col = col[1]
            if nome_col == col_pk:
                continue
            tipo = tipo_postgres(col[2])
            linhas.append(f'ALTER TABLE "{tabela}" ADD COLUMN IF NOT EXISTS "{nome_col}" {tipo};')
        linhas.append(f'ALTER TABLE "{tabela}" ENABLE ROW LEVEL SECURITY;')
        linhas.append(f'DROP POLICY IF EXISTS "acesso_total" ON "{tabela}";')
        linhas.append(f'CREATE POLICY "acesso_total" ON "{tabela}" FOR ALL USING (true) WITH CHECK (true);')
        linhas.append("")

    conn.close()

    caminho_saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supabase_completo.sql")
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print("=" * 60)
    print(f"Pronto! Gerei {len(tabelas)} tabelas em:")
    print(f"  {caminho_saida}")
    print()
    print("Abra esse arquivo, copie tudo, cole no SQL Editor do Supabase")
    print("e clique em RUN.")
    print("=" * 60)


if __name__ == "__main__":
    main()
