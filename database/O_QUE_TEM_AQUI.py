import os

print("--- DIAGNÓSTICO DE PASTA ---")
print(f"Caminho atual: {os.getcwd()}")
print("\nArquivos encontrados nesta pasta:")

arquivos = os.listdir('.')
for arq in arquivos:
    # Mostra o nome real do arquivo e o tamanho dele
    tamanho = os.path.getsize(arq) if os.path.isfile(arq) else "Pasta"
    print(f" - {arq} (Tamanho: {tamanho} bytes)")

print("\n---------------------------")
input("Tire uma foto dessa tela e me mande. Pressione Enter para fechar...")
