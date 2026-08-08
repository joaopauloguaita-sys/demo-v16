import sqlite3
import os

def find_and_check():
    print("Buscando banco de dados na pasta v15...")
    db_path = None
    
    # Busca em todas as pastas e subpastas
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db'):
                db_path = os.path.join(root, file)
                print(f"Encontrado: {db_path}")
                break
        if db_path: break

    if not db_path:
        print("\nErro: Nenhum arquivo .db encontrado na pasta v15.")
        print("Verifique se o arquivo database.db esta realmente dentro desta pasta.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n--- ESTRUTURA DO BANCO ENCONTRADO ---")
        for table in tables:
            table_name = table[0]
            if table_name.startswith('sqlite_'): continue
            print(f"\nTabela: {table_name}")
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = cursor.fetchall()
            for col in columns:
                print(f" - {col[1]} ({col[2]})")
        
        conn.close()
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")

if __name__ == "__main__":
    find_and_check()
    input("\nPressione Enter para fechar...")
