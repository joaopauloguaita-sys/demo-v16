import os
import subprocess
import sys
import shutil

def proteger_e_compilar():
    print("🚀 Iniciando proteção do sistema João - O Secretário...")
    
    # Caminho do Python atual para garantir que usaremos as ferramentas instaladas nele
    python_exe = sys.executable

    # 1. Ofusca o código
    # Usamos 'python -m pyarmor.cli' em vez de apenas 'pyarmor' para evitar o erro de arquivo não encontrado
    print("🔐 Ofuscando código com PyArmor...")
    try:
        subprocess.run([python_exe, "-m", "pyarmor.cli", "gen", "main.py"], check=True)
    except Exception as e:
        print(f"❌ Erro no PyArmor: {e}")
        print("Tentando compilar apenas com PyInstaller para não te deixar parado...")
    
    # 2. Compilar com PyInstaller
    print("📦 Compilando em arquivo único .exe...")
    
    # Se o PyArmor funcionou, a main ofuscada estará em dist/main.py
    # Se não funcionou, usamos a main.py original
    caminho_main = os.path.join("dist", "main.py") if os.path.exists(os.path.join("dist", "main.py")) else "main.py"
    
    cmd_pyinstaller = [
        python_exe, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name=Joao_Secretario",
        "--add-data=assets;assets",
        "--add-data=database;database",
        "--collect-all", "customtkinter", # Garante que a interface visual não quebre
        caminho_main
    ]

    try:
        subprocess.run(cmd_pyinstaller, check=True)
        print("\n✅ PROCESSO CONCLUÍDO!")
        print(f"O arquivo pronto para instalação está na pasta: {os.path.join(os.getcwd(), 'dist')}")
    except Exception as e:
        print(f"❌ Erro fatal na compilação: {e}")

if __name__ == "__main__":
    proteger_e_compilar()