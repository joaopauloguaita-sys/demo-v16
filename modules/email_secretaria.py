import customtkinter as ctk
from tkinter import messagebox, filedialog
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
import threading
import sys, os
import webbrowser
from tkinterweb import HtmlFrame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tema import CORES, fonte

# --- TRADUTOR DE TEXTO E PASTAS DO GMAIL ---
def decodificar_texto(texto):
    if not texto: return ""
    # Traduz o formato de pastas do Gmail (UTF-7 modificado)
    if "&" in texto and "-" in texto:
        try:
            texto = texto.replace("&AMk-", "é").replace("&AMU-", "õ").replace("&AOM-", "ã").replace("&AOc-", "ç").replace("&AM8-", "ó").replace("&AIE-", "í")
        except: pass
    
    partes = decode_header(texto)
    resultado = ""
    for parte, codificacao in partes:
        if isinstance(parte, bytes):
            try: resultado += parte.decode(codificacao or "utf-8", errors="ignore")
            except: resultado += str(parte)
        else: resultado += parte
    return resultado

class EmailModule(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=CORES["fundo"])
        
        self.contas = [{
            "label": "Gmail Secretaria",
            "email": "joaopaulo.guaita@gmail.com", 
            "senha": "grkd nqbd xccn jhvb", 
            "imap": "imap.gmail.com", 
            "smtp": "smtp.gmail.com"
        }]

        self.emails_data = {} 
        self.cards_widgets = {} 
        self.lista_pastas_info = [] 
        self.pasta_atual = "INBOX"
        self.filtro_busca = ""
        
        self._build_ui()
        self.atualizar_caixa_entrada()

    def _build_ui(self):
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL DE PASTAS ---
        self.frame_pastas = ctk.CTkFrame(self, width=190, fg_color="#f8f9fa", corner_radius=0)
        self.frame_pastas.grid(row=0, column=0, sticky="nsew")
        self.frame_pastas.pack_propagate(False)
        
        ctk.CTkLabel(self.frame_pastas, text="PASTAS", font=fonte(11, "bold"), text_color="#5f6368").pack(pady=(20,10))
        self.scroll_pastas = ctk.CTkScrollableFrame(self.frame_pastas, fg_color="transparent", corner_radius=0)
        self.scroll_pastas.pack(fill="both", expand=True)

        # --- LISTA DE EMAILS ---
        self.frame_lista = ctk.CTkFrame(self, width=360, fg_color="#f1f4f9", corner_radius=0)
        self.frame_lista.grid(row=0, column=1, sticky="nsew")
        self.frame_lista.pack_propagate(False)

        search_f = ctk.CTkFrame(self.frame_lista, fg_color="transparent")
        search_f.pack(fill="x", padx=10, pady=(15,5))
        self.ent_busca = ctk.CTkEntry(search_f, placeholder_text="🔍 Buscar nesta pasta...", height=35)
        self.ent_busca.pack(side="left", fill="x", expand=True)
        self.ent_busca.bind("<Return>", lambda e: self.atualizar_caixa_entrada())
        
        self.scroll_emails = ctk.CTkScrollableFrame(self.frame_lista, fg_color="transparent", corner_radius=0)
        self.scroll_emails.pack(fill="both", expand=True, padx=5, pady=5)

        # --- VISUALIZAÇÃO ---
        self.frame_direita = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        self.frame_direita.grid(row=0, column=2, sticky="nsew")

        self.toolbar = ctk.CTkFrame(self.frame_direita, fg_color="#f8f9fa", height=60, corner_radius=0)
        self.toolbar.pack(fill="x", side="top"); self.toolbar.pack_propagate(False)

        ctk.CTkButton(self.toolbar, text="📝 Novo", width=70, height=32, fg_color="#27ae60", command=self.janela_compor).pack(side="left", padx=10)
        self.btn_responder = ctk.CTkButton(self.toolbar, text="↩️ Responder", width=90, height=32, command=self.responder_clicado)
        self.btn_encaminhar = ctk.CTkButton(self.toolbar, text="➡️ Encaminhar", width=90, height=32, fg_color="#5f6368", command=self.encaminhar_clicado)
        self.var_marcadores = ctk.StringVar(value="🏷️ Mover para...")
        self.menu_marcadores = ctk.CTkOptionMenu(self.toolbar, variable=self.var_marcadores, values=[], command=self.mover_para_marcador, width=150, height=32)
        self.btn_excluir = ctk.CTkButton(self.toolbar, text="🗑️", width=40, height=32, fg_color="#c62828", command=self.excluir_email_clicado)

        self.view_scroll = ctk.CTkScrollableFrame(self.frame_direita, fg_color="white", corner_radius=0)
        self.view_scroll.pack(fill="both", expand=True)

        self.lbl_remetente = ctk.CTkLabel(self.view_scroll, text="", font=fonte(13, "bold"), text_color="black", anchor="w")
        self.lbl_remetente.pack(fill="x", padx=25, pady=(15, 0))
        self.lbl_assunto = ctk.CTkLabel(self.view_scroll, text="Selecione um e-mail", font=fonte(17, "bold"), text_color="#1a73e8", wraplength=700, justify="left", anchor="w")
        self.lbl_assunto.pack(fill="x", padx=25, pady=(0, 10))

        self.frame_anexos = ctk.CTkFrame(self.view_scroll, fg_color="#fff4e5", corner_radius=10)
        self.frame_anexos.pack(fill="x", padx=25, pady=5); self.frame_anexos.pack_forget()

        self.browser_frame = HtmlFrame(self.view_scroll, messages_enabled=False)
        self.browser_frame.pack(fill="both", expand=True, padx=15, pady=10)

    def atualizar_caixa_entrada(self):
        self.filtro_busca = self.ent_busca.get().strip()
        for w in self.scroll_emails.winfo_children(): w.destroy()
        self.cards_widgets = {}
        self.btn_responder.pack_forget(); self.btn_encaminhar.pack_forget(); self.btn_excluir.pack_forget(); self.menu_marcadores.pack_forget()
        self.browser_frame.load_html("<body style='font-family:sans-serif; padding:20px;'>⏳ Sincronizando e-mails...</body>")
        threading.Thread(target=self._buscar_dados, daemon=True).start()

    def _buscar_dados(self):
        try:
            c = self.contas[0]
            mail = imaplib.IMAP4_SSL(c["imap"]); mail.login(c["email"], c["senha"])
            
            # --- ATUALIZA LISTA DE PASTAS ---
            _, folder_list = mail.list()
            self.lista_pastas_info = []
            for f in folder_list:
                nome_pasta_bruto = f.decode().split(' "/" ')[1].replace('"', '')
                nome_pasta_decod = decodificar_texto(nome_pasta_bruto)
                self.lista_pastas_info.append({"real": nome_pasta_bruto, "label": nome_pasta_decod})
            
            self.after(0, self._desenhar_sidebar_pastas)
            self.after(0, lambda: self.menu_marcadores.configure(values=[m["label"] for m in self.lista_pastas_info if m["label"].upper() not in ["INBOX", "TRASH", "SPAM"]]))

            # --- BUSCA EMAILS ---
            mail.select(f'"{self.pasta_atual}"')
            
            if self.filtro_busca:
                status, messages = mail.uid('search', None, f'TEXT "{self.filtro_busca}"')
            elif self.pasta_atual == "INBOX":
                # FILTRO ANTI-PROPAGANDA: Apenas categoria Primary no Gmail
                status, messages = mail.uid('search', None, 'X-GM-RAW "category:primary"')
                if status != 'OK' or not messages[0]: status, messages = mail.uid('search', None, "ALL")
            else:
                status, messages = mail.uid('search', None, 'ALL')

            uids = messages[0].split()[-25:] 
            self.emails_data = {}
            for uid in reversed(uids):
                _, data = mail.uid('fetch', uid, "(RFC822 FLAGS)")
                msg = email.message_from_bytes(data[0][1])
                lido = "\\Seen" in str(data[1])
                assunto = decodificar_texto(msg["Subject"])
                remetente = decodificar_texto(msg.get("From"))
                
                corpo_txt = ""; corpo_html = ""; anexos = []
                for part in msg.walk():
                    dispo = str(part.get("Content-Disposition"))
                    if part.get_content_type() == "text/plain" and "attachment" not in dispo:
                        try: corpo_txt = part.get_payload(decode=True).decode(errors="ignore")
                        except: pass
                    elif part.get_content_type() == "text/html" and "attachment" not in dispo:
                        try: corpo_html = part.get_payload(decode=True).decode(errors="ignore")
                        except: pass
                    elif "attachment" in dispo:
                        fname = decodificar_texto(part.get_filename())
                        if fname: anexos.append({"name": fname, "payload": part.get_payload(decode=True)})

                item = {"uid": uid, "de": remetente, "assunto": assunto, "corpo": corpo_txt, "html": corpo_html, "anexos": anexos, "lido": lido}
                self.emails_data[uid] = item
                self.after(0, lambda i=item: self._adicionar_card(i))
            
            mail.logout()
            self.after(0, lambda: self.browser_frame.load_html("<body style='font-family:sans-serif; padding:20px;'>Pronto! Selecione uma mensagem.</body>"))
        except Exception as e:
            self.after(0, lambda: self.browser_frame.load_html(f"<body>Erro de conexão: {e}</body>"))

    def _desenhar_sidebar_pastas(self):
        for w in self.scroll_pastas.winfo_children(): w.destroy()
        
        # Pastas principais fixas
        mapeamento = [("INBOX", "📥 Principal"), ("\"[Gmail]/Sent Mail\"", "📤 Enviados")]
        for path, label in mapeamento:
            is_ativa = (self.pasta_atual == path)
            btn = ctk.CTkButton(self.scroll_pastas, text=label, anchor="w", height=38, corner_radius=8,
                                fg_color=CORES["acento"] if is_ativa else "transparent",
                                text_color="white" if is_ativa else "black", hover_color="#dfe9ff",
                                command=lambda p=path: self.mudar_pasta(p))
            btn.pack(fill="x", padx=8, pady=2)

        ctk.CTkLabel(self.scroll_pastas, text="MEUS MARCADORES", font=fonte(9, "bold"), text_color="#999").pack(pady=(15,5))
        
        for m in self.lista_pastas_info:
            nome_limpo = m["label"]
            # Esconde pastas do sistema para focar nos marcadores do João
            if nome_limpo.upper() not in ["INBOX", "SENT MAIL", "DRAFTS", "SPAM", "TRASH", "SENT", "ALL MAIL", "STARRED", "IMPORTANT", "CHATS"]:
                path_real = m["real"]
                is_ativa = (self.pasta_atual == f'"{path_real}"')
                btn = ctk.CTkButton(self.scroll_pastas, text=f"🏷️ {nome_limpo}", anchor="w", height=32, corner_radius=8,
                                    fg_color="#0a2463" if is_ativa else "transparent",
                                    text_color="white" if is_ativa else "#444", hover_color="#dfe9ff",
                                    command=lambda p=path_real: self.mudar_pasta(f'"{p}"'))
                btn.pack(fill="x", padx=8, pady=1)

    def mudar_pasta(self, nova_pasta):
        self.pasta_atual = nova_pasta
        self.atualizar_caixa_entrada()

    def _adicionar_card(self, item):
        card = ctk.CTkFrame(self.scroll_emails, fg_color="white", border_width=1, border_color="#dbe3ff", corner_radius=15, height=95)
        card.pack(fill="x", padx=10, pady=6); card.pack_propagate(False)
        indicador = ctk.CTkLabel(card, text="●" if not item["lido"] else "", font=("Arial", 14), text_color="#1a73e8")
        indicador.place(x=10, y=10)
        
        nome = item["de"].split("<")[0].replace('"', '').strip()
        lbl_de = ctk.CTkLabel(card, text=nome, font=fonte(12, "bold" if not item["lido"] else "normal"), text_color="#0a2463", anchor="w")
        lbl_de.pack(fill="x", padx=(30, 15), pady=(12, 0))
        lbl_ass = ctk.CTkLabel(card, text=item["assunto"], font=fonte(11, "normal"), text_color="#555", anchor="w")
        lbl_ass.pack(fill="x", padx=(30, 15))
        self.cards_widgets[item["uid"]] = {"de": lbl_de, "ass": lbl_ass, "ind": indicador}
        for w in [card, lbl_de, lbl_ass]: w.bind("<Button-1>", lambda e, i=item: self.selecionar_email(i))

    def selecionar_email(self, item):
        self.email_atual = item
        self.lbl_remetente.configure(text=f"De: {item['de']}")
        self.lbl_assunto.configure(text=item['assunto'])
        self.var_marcadores.set("🏷️ Mover para...")
        
        # Marca como lido visualmente e no servidor
        w = self.cards_widgets.get(item["uid"])
        if w:
            w["de"].configure(font=fonte(12, "normal")); w["ind"].configure(text="")
            if not item["lido"]:
                threading.Thread(target=self._marcar_como_lido_servidor, args=(item["uid"],), daemon=True).start()
                item["lido"] = True

        if item['html']: self.browser_frame.load_html(item['html'])
        else: self.browser_frame.load_html(f"<body style='font-family:sans-serif; padding:20px;'>{item['corpo']}</body>")

        self.btn_responder.pack(side="left", padx=10, pady=11)
        self.btn_encaminhar.pack(side="left", padx=5)
        self.menu_marcadores.pack(side="left", padx=5)
        self.btn_excluir.pack(side="left", padx=5)
        
        for widget in self.frame_anexos.winfo_children(): widget.destroy()
        if item["anexos"]:
            self.frame_anexos.pack(fill="x", padx=25, pady=5, before=self.browser_frame)
            ctk.CTkLabel(self.frame_anexos, text="📎 Anexos:", font=fonte(11, "bold")).grid(row=0, column=0, padx=10, pady=10)
            col, row = 1, 0
            for a in item["anexos"]:
                if col > 3: col, row = 1, row + 1
                btn = ctk.CTkButton(self.frame_anexos, text=a["name"][:18]+"...", width=100, height=28, fg_color="#e67e22", command=lambda x=a: self.baixar_anexo(x))
                btn.grid(row=row, column=col, padx=2, pady=5); col += 1
        else: self.frame_anexos.pack_forget()

    def mover_para_marcador(self, escolha):
        if not self.email_atual: return
        nome_real = next((m["real"] for m in self.lista_pastas_info if m["label"] == escolha), escolha)
        if messagebox.askyesno("Mover", f"Deseja arquivar este e-mail em '{escolha}'?"):
            threading.Thread(target=self._executar_movimento, args=(self.email_atual["uid"], nome_real), daemon=True).start()

    def _executar_movimento(self, uid, destino):
        try:
            c = self.contas[0]; mail = imaplib.IMAP4_SSL(c["imap"]); mail.login(c["email"], c["senha"])
            mail.select(f'"{self.pasta_atual}"')
            result = mail.uid('COPY', uid, f'"{destino}"')
            if result[0] == 'OK':
                mail.uid('STORE', uid, '+FLAGS', '(\\Deleted)')
                mail.expunge()
            mail.logout()
            self.after(0, self.atualizar_caixa_entrada)
        except Exception as e: self.after(0, lambda: messagebox.showerror("Erro ao mover", str(e)))

    def _marcar_como_lido_servidor(self, uid):
        try:
            c = self.contas[0]; mail = imaplib.IMAP4_SSL(c["imap"]); mail.login(c["email"], c["senha"]); mail.select(f'"{self.pasta_atual}"')
            mail.uid('STORE', uid, '+FLAGS', '(\\Seen)'); mail.logout()
        except: pass

    def baixar_anexo(self, a):
        path = filedialog.asksaveasfilename(initialfile=a["name"])
        if path:
            with open(path, "wb") as f: f.write(a["payload"])
            messagebox.showinfo("Sucesso", "Arquivo guardado!")

    def responder_clicado(self): self.janela_compor(para=self.email_atual["de"], assunto=f"RE: {self.email_atual['assunto']}")
    def encaminhar_clicado(self): self.janela_compor(assunto=f"ENC: {self.email_atual['assunto']}", corpo=self.email_atual["corpo"])

    def excluir_email_clicado(self):
        if messagebox.askyesno("Excluir", "Deseja apagar este e-mail?"):
            self.mover_para_marcador("[Gmail]/Trash")

    def janela_compor(self, para="", assunto="", corpo=""):
        win = ctk.CTkToplevel(self); win.title("Mensagem"); win.geometry("650x750"); win.grab_set(); win.attributes("-topmost", True)
        ctk.CTkLabel(win, text="Para:", font=fonte(12, "bold")).pack(padx=25, anchor="w", pady=(20,0))
        e_p = ctk.CTkEntry(win, width=600, height=35); e_p.insert(0, para); e_p.pack(padx=25)
        ctk.CTkLabel(win, text="Assunto:", font=fonte(12, "bold")).pack(padx=25, anchor="w", pady=(10,0))
        e_a = ctk.CTkEntry(win, width=600, height=35); e_a.insert(0, assunto); e_a.pack(padx=25)
        t_m = ctk.CTkTextbox(win, width=600, height=400, font=("Segoe UI", 12)); t_m.insert("1.0", f"\n\n--- Original ---\n{corpo}"); t_m.pack(padx=25, pady=10)
        t_m.mark_set("insert", "1.0")
        def send():
            try:
                c = self.contas[0]; server = smtplib.SMTP_SSL(c["smtp"], 465); server.login(c["email"], c["senha"])
                msg = MIMEText(t_m.get("1.0", "end"), 'plain', 'utf-8')
                msg['Subject'] = e_a.get(); msg['From'] = c["email"]; msg['To'] = e_p.get()
                server.sendmail(c["email"], e_p.get(), msg.as_string()); server.quit()
                messagebox.showinfo("Sucesso", "E-mail enviado!"); win.destroy()
            except Exception as e: messagebox.showerror("Erro", str(e))
        ctk.CTkButton(win, text="🚀 ENVIAR", font=fonte(13, "bold"), fg_color="#27ae60", height=45, width=200, command=send).pack(pady=15)