import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import io
import sys
import threading
import webbrowser
import urllib.parse as urlparse

# Bibliotecas do Google
try:
    from pypdf import PdfReader, PdfWriter
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
    LIBS_OK = True
except ImportError as e:
    LIBS_OK = False
    ERRO_MSG = str(e)

# --- CONFIGURAÇÕES ---
# Escopos ampliados para evitar o erro 400 de permissão
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]
SERVICE_ACCOUNT_FILE = 'credentials.json' 
# !!! COLOQUE SEU ID DA PASTA AQUI !!!
ID_PASTA_DESTINO = "1xmpFX5kuoqApx27i1D97ckJ4b88fCZ_Q"

# Conta Google que deve ser usada para conectar ao Drive (é só uma sugestão pré-
# selecionada na tela de login do Google — quem confirma a senha continua sendo você).
# Troque aqui se um dia mudar a conta.
CONTA_GOOGLE_PADRAO = "secretarialorenzette@gmail.com"


def _registrar_chrome_como_preferido():
    """Tenta achar o Google Chrome instalado e registrá-lo como navegador
    preferido do Python, pra a tela de login do Google abrir nele em vez do
    navegador padrão do Windows. Se não achar, segue com o navegador padrão."""
    caminhos_possiveis = [
        os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"),
                      "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
                      "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                      "Google", "Chrome", "Application", "chrome.exe"),
    ]
    for caminho in caminhos_possiveis:
        if caminho and os.path.exists(caminho):
            try:
                webbrowser.register(
                    "chrome-joao", None,
                    webbrowser.BackgroundBrowser(caminho), preferred=True)
                return True
            except Exception:
                pass
    return False

class CentralDocumentosModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#e8edf5")
        
        self.pasta_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.caminho_creds = os.path.join(self.pasta_raiz, SERVICE_ACCOUNT_FILE)
        self.caminho_token = os.path.join(self.pasta_raiz, 'token.json')

        self.drive_service = None
        self._build_ui()
        
        # Tenta conexão automática apenas se o token já existir e for válido
        if os.path.exists(self.caminho_token):
            self.status_lbl.configure(text="⏳ Validando acesso anterior...")
            threading.Thread(target=self._tentar_reconectar_silencioso, daemon=True).start()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12)
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text="📁 Central de Documentos Digitalizados", font=("Segoe UI", 22, "bold"), text_color="#0a2463").pack(pady=15)

        self.container = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=15)
        self.container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Botão de Conexão
        self.btn_conectar = ctk.CTkButton(self.container, text="🔌 CONECTAR AO GOOGLE DRIVE", font=("Segoe UI", 12, "bold"), 
                                         fg_color="#1a73e8", height=40, command=self.iniciar_conexao)
        self.btn_conectar.pack(pady=40)

        # Widgets de Upload (Iniciam ocultos)
        self.widgets_upload = ctk.CTkFrame(self.container, fg_color="transparent")
        
        ctk.CTkLabel(self.widgets_upload, text="1. Selecione a Categoria:", font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))
        self.cat_var = ctk.StringVar(value="alunos")
        self.cb_cat = ctk.CTkOptionMenu(self.widgets_upload, values=["alunos", "professores", "funcionarios", "pedagogas", "secretarios", "diretores"], variable=self.cat_var, command=self.atualizar_nomes)
        self.cb_cat.pack()

        ctk.CTkLabel(self.widgets_upload, text="2. Selecione a Pessoa:", font=("Segoe UI", 12, "bold")).pack(pady=(15, 5))
        self.nome_var = ctk.StringVar(value="Selecione...")
        self.cb_nomes = ctk.CTkComboBox(self.widgets_upload, variable=self.nome_var, width=450)
        self.cb_nomes.pack()

        self.btn_upload = ctk.CTkButton(self.widgets_upload, text="🚀 SELECIONAR PDF E ENVIAR", font=("Segoe UI", 13, "bold"), 
                                        height=55, fg_color="#27ae60", command=self.upload_processo)
        self.btn_upload.pack(pady=30)

        self.status_lbl = ctk.CTkLabel(self.container, text="Aguardando conexão...", font=("Segoe UI", 11, "italic"))
        self.status_lbl.pack(side="bottom", pady=20)

    def iniciar_conexao(self):
        if not LIBS_OK:
            messagebox.showerror(
                "Bibliotecas faltando",
                "Não consegui conectar ao Google Drive porque uma ou mais bibliotecas "
                "necessárias não estão instaladas neste computador/ambiente:\n\n"
                f"{ERRO_MSG}\n\n"
                "Instale com:\n"
                "pip install pypdf google-auth google-auth-oauthlib google-api-python-client"
            )
            return
        self.btn_conectar.configure(text="⏳ Verifique seu Navegador...", state="disabled")
        # Rodar em thread separada para não travar o sistema
        t = threading.Thread(target=self._processo_login_google)
        t.daemon = True
        t.start()

    def _processo_login_google(self):
        try:
            if not os.path.exists(self.caminho_creds):
                self.after(0, lambda: messagebox.showerror("Erro", "Arquivo credentials.json não encontrado na raiz!"))
                return

            # Cria o fluxo de login
            flow = InstalledAppFlow.from_client_secrets_file(self.caminho_creds, SCOPES)

            # Abre a tela de login sempre no Chrome (se instalado) e já sugere
            # a conta certa — o Google ainda pede a senha normalmente, isso só
            # evita ter que escolher a conta na mão toda vez.
            _registrar_chrome_como_preferido()

            # Tenta abrir o servidor local para o login
            # Se der erro 400 ao copiar o link, tente NÃO copiar o link.
            # Deixe o sistema abrir o navegador sozinho.
            creds = flow.run_local_server(
                port=0, timeout_seconds=60,
                login_hint=CONTA_GOOGLE_PADRAO)
            
            with open(self.caminho_token, 'w') as token:
                token.write(creds.to_json())

            self.drive_service = build('drive', 'v3', credentials=creds, static_discovery=False)
            self.after(0, self._ativar_interface_sucesso)
            
        except Exception as e:
            self.after(0, lambda: self.btn_conectar.configure(text="🔌 TENTAR NOVAMENTE", state="normal"))
            self.after(0, lambda: messagebox.showerror("Erro no Google", f"Não foi possível autorizar: {e}"))

    def _tentar_reconectar_silencioso(self):
        try:
            creds = Credentials.from_authorized_user_file(self.caminho_token, SCOPES)
            if creds and creds.valid:
                self.drive_service = build('drive', 'v3', credentials=creds, static_discovery=False)
                self.after(0, self._ativar_interface_sucesso)
            elif creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self.drive_service = build('drive', 'v3', credentials=creds, static_discovery=False)
                self.after(0, self._ativar_interface_sucesso)
            else:
                self.after(0, lambda: self.status_lbl.configure(text="Conexão expirada. Clique em Conectar."))
        except:
            self.after(0, lambda: self.status_lbl.configure(text="Aguardando nova conexão."))

    def _ativar_interface_sucesso(self):
        self.btn_conectar.pack_forget()
        self.widgets_upload.pack(fill="both", expand=True)
        self.status_lbl.configure(text="✅ Google Drive Conectado!", text_color="green")
        self.atualizar_nomes()

    def atualizar_nomes(self, *_):
        from database.db import get_connection
        try:
            conn = get_connection(); tabela = self.cat_var.get()
            res = conn.execute(f"SELECT nome FROM {tabela} WHERE (arquivado=0 OR arquivado IS NULL) ORDER BY nome").fetchall()
            conn.close()
            lista = [str(r[0]) for r in res]
            self.cb_nomes.configure(values=lista)
            if lista: self.nome_var.set(lista[0])
        except: pass

    def upload_processo(self):
        caminho_novo = filedialog.askopenfilename(filetypes=[("Arquivos PDF", "*.pdf")])
        if not caminho_novo: return
        
        self.btn_upload.configure(state="disabled", text="⏳ ENVIANDO...")
        threading.Thread(target=self._executar_upload_seguro, args=(caminho_novo,), daemon=True).start()

    def _executar_upload_seguro(self, caminho_novo):
        import time
        # Criamos um nome temporário único usando o horário para evitar conflitos
        timestamp = int(time.time())
        caminho_temp = os.path.join(self.pasta_raiz, f"temp_unificar_{timestamp}.pdf")

        try:
            nome_pessoa, tabela = self.nome_var.get(), self.cat_var.get()
            from database.db import get_connection
            conn = get_connection()
            row = conn.execute(f"SELECT id, pasta_documentos FROM {tabela} WHERE nome=?", (nome_pessoa,)).fetchone()
            pid, link_atual = row[0], row[1]
            
            file_id = None
            if link_atual:
                if "id=" in link_atual: file_id = link_atual.split("id=")[1].split("&")[0]
                elif "/d/" in link_atual: file_id = link_atual.split("/d/")[1].split("/")[0]

            caminho_final = caminho_novo

            # --- LÓGICA DE MESCLAGEM (JUNÇÃO) ---
            if file_id:
                self.after(0, lambda: self.status_lbl.configure(text="📂 Unificando documentos na nuvem..."))
                try:
                    request = self.drive_service.files().get_media(fileId=file_id)
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request); done = False
                    while not done: _, done = downloader.next_chunk()
                    
                    merger = PdfWriter()
                    merger.append(io.BytesIO(fh.getvalue())) 
                    merger.append(caminho_novo) 
                    
                    with open(caminho_temp, "wb") as f_out:
                        merger.write(f_out)
                    
                    merger.close()
                    caminho_final = caminho_temp
                except Exception as e:
                    print(f"Erro na mesclagem: {e}")

            # --- UPLOAD PARA O DRIVE ---
            media = MediaFileUpload(caminho_final, mimetype='application/pdf', resumable=True)
            
            if file_id:
                self.drive_service.files().update(fileId=file_id, media_body=media).execute()
            else:
                meta = {'name': f"DOC_{tabela.upper()}_{nome_pessoa.replace(' ','_')}.pdf", 'parents': [ID_PASTA_DESTINO]}
                file = self.drive_service.files().create(body=meta, media_body=media, fields='id').execute()
                file_id = file.get('id')
                self.drive_service.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()

            # --- CORREÇÃO DO LINK (PARA NÃO FAZER DOWNLOAD DIRETO) ---
            # O link formatado com '/view' abre o visualizador do Google em vez de baixar
            link_visualizacao = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            
            conn.execute(f"UPDATE {tabela} SET pasta_documentos=? WHERE id=?", (link_visualizacao, pid))
            conn.commit()
            conn.close()
            
            # Pequena pausa antes de apagar para o Windows liberar o arquivo
            if caminho_final == caminho_temp:
                time.sleep(1) 
                try: os.remove(caminho_temp)
                except: pass
            
            self.after(0, lambda: [messagebox.showinfo("Sucesso", f"Documentos de {nome_pessoa} atualizados!"), 
                                   self.btn_upload.configure(state="normal", text="🚀 SELECIONAR PDF E ENVIAR")])
        except Exception as e:
            self.after(0, lambda: [messagebox.showerror("Erro no Drive", f"Falha: {e}"), 
                                   self.btn_upload.configure(state="normal", text="🚀 SELECIONAR PDF E ENVIAR")])