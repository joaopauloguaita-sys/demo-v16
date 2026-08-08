import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte, data_bd_para_tela, data_tela_para_bd
from modules.ia_engine import redigir_documento
from modules.pdf_engine import gerar_pdf_documento

class OficiosModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()

    def _build_ui(self):
        # Título
        topo = ctk.CTkFrame(self, fg_color=CORES["sidebar"], height=50, corner_radius=0)
        topo.pack(fill="x", side="top")
        ctk.CTkLabel(topo, text="📩 Gestão de Ofícios", font=fonte(16, "bold"), text_color=CORES["texto_claro"]).pack(side="left", padx=20)
        
        btn_novo = ctk.CTkButton(topo, text="+ Novo Ofício", fg_color=CORES["sucesso"], hover_color=CORES["sucesso_hover"],
                                 command=self._abrir_formulario, width=120)
        btn_novo.pack(side="right", padx=20, pady=10)

        # Filtros
        f_filtros = ctk.CTkFrame(self, fg_color="transparent")
        f_filtros.pack(fill="x", padx=20, pady=10)
        
        self.busca_ent = ctk.CTkEntry(f_filtros, placeholder_text="Buscar por destinatário ou assunto...", width=300)
        self.busca_ent.pack(side="left", padx=(0, 10))
        ctk.CTkButton(f_filtros, text="🔍 Buscar", width=100, command=self._carregar_lista).pack(side="left")

        # Tabela (Treeview) - usa um NOME DE ESTILO PRÓPRIO ("Oficios.Treeview"),
        # nunca "Treeview" puro, porque esse nome é compartilhado com o resto do
        # sistema - sobrescrever ele mudava a fonte de TODAS as tabelas do app.
        style = ttk.Style()
        style.configure("Oficios.Treeview", background=CORES["card"], foreground=CORES["texto_escuro"],
                        rowheight=25, fieldbackground=CORES["card"], borderwidth=0, font=fonte(11))
        style.map("Oficios.Treeview", background=[('selected', CORES["dourado"])])
        style.configure("Oficios.Treeview.Heading", background=CORES["primaria"],
                        foreground=CORES["texto_claro"], font=fonte(10, "bold"), relief="flat")

        f_tabela = ctk.CTkFrame(self, fg_color="transparent")
        f_tabela.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(f_tabela, columns=("num", "data", "dest", "assunto"), show="headings",
                                 style="Oficios.Treeview")
        self.tree.heading("num", text="Nº/Ano")
        self.tree.heading("data", text="Data")
        self.tree.heading("dest", text="Destinatário")
        self.tree.heading("assunto", text="Assunto")
        
        self.tree.column("num", width=100, anchor="center")
        self.tree.column("data", width=100, anchor="center")
        self.tree.column("dest", width=250)
        self.tree.column("assunto", width=350)
        self.tree.pack(fill="both", expand=True, side="left")

        # Barra lateral de ações
        f_acoes = ctk.CTkFrame(f_tabela, fg_color="transparent")
        f_acoes.pack(side="right", fill="y", padx=(10, 0))

        ctk.CTkButton(f_acoes, text="✏️ Editar", width=100, fg_color=CORES["acento"], 
                      command=lambda: self._abrir_formulario(editando=True)).pack(pady=5)
        ctk.CTkButton(f_acoes, text="🗑️ Excluir", width=100, fg_color=CORES["perigo"], 
                      command=self._excluir_oficio).pack(pady=5)
        
        self.tree.bind("<Double-1>", lambda e: self._abrir_formulario(editando=True))

        self._carregar_lista()

    def _carregar_lista(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        busca = f"%{self.busca_ent.get()}%"
        conn = get_connection()
        try:
            res = conn.execute("SELECT id, numero, ano, data, destinatario, assunto FROM oficios WHERE (destinatario LIKE ? OR assunto LIKE ?) AND (excluido IS NULL OR excluido = 0) ORDER BY ano DESC, numero DESC", (busca, busca)).fetchall()
            for r in res:
                dt = data_bd_para_tela(r['data'])
                self.tree.insert("", "end", iid=r['id'], values=(f"{r['numero']}/{r['ano']}", dt, r['destinatario'], r['assunto']))
        finally:
            conn.close()

    def _excluir_oficio(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um ofício para excluir.")
            return
        if not messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir este ofício?"):
            return
        
        conn = get_connection()
        try:
            conn.execute("UPDATE oficios SET excluido=1 WHERE id=?", (sel[0],))
            conn.commit()
            self._carregar_lista()
        finally:
            conn.close()

    def _abrir_formulario(self, editando=False):
        oficio_id = None
        dados = {}
        if editando:
            sel = self.tree.selection()
            if not sel:
                messagebox.showwarning("Atenção", "Selecione um ofício para editar.")
                return
            oficio_id = sel[0]
            conn = get_connection()
            dados = conn.execute("SELECT * FROM oficios WHERE id=?", (oficio_id,)).fetchone()
            conn.close()

        form = ctk.CTkToplevel(self)
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        form.title("📩 Novo Ofício" if not editando else "✏️ Editar Ofício")
        form.geometry("900x700")
        form.grab_set()

        scroll = ctk.CTkScrollableFrame(form, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Cabeçalho
        f_cab = ctk.CTkFrame(scroll, fg_color="transparent")
        f_cab.pack(fill="x", pady=10)

        ctk.CTkLabel(f_cab, text="Nº:", font=fonte(13, "bold")).grid(row=0, column=0, padx=5, sticky="w")
        num_v = ctk.StringVar(value=dados['numero'] if editando else "")
        ctk.CTkEntry(f_cab, textvariable=num_v, width=80).grid(row=0, column=1, padx=5)

        ctk.CTkLabel(f_cab, text="Ano:", font=fonte(13, "bold")).grid(row=0, column=2, padx=5, sticky="w")
        ano_v = ctk.StringVar(value=dados['ano'] if editando else datetime.now().year)
        ctk.CTkEntry(f_cab, textvariable=ano_v, width=80).grid(row=0, column=3, padx=5)

        ctk.CTkLabel(f_cab, text="Data:", font=fonte(13, "bold")).grid(row=0, column=4, padx=5, sticky="w")
        data_v = ctk.StringVar(value=data_bd_para_tela(dados['data']) if editando else datetime.now().strftime("%d/%m/%Y"))
        ctk.CTkEntry(f_cab, textvariable=data_v, width=120).grid(row=0, column=5, padx=5)

        # Destinatário
        ctk.CTkLabel(scroll, text="Destinatário (Nome):", font=fonte(13, "bold")).pack(anchor="w", pady=(10,0))
        dest_e = ctk.CTkEntry(scroll, placeholder_text="Ex: João da Silva")
        dest_e.pack(fill="x", pady=5)
        if editando: dest_e.insert(0, dados['destinatario'])

        f_dest = ctk.CTkFrame(scroll, fg_color="transparent")
        f_dest.pack(fill="x")
        
        ctk.CTkLabel(f_dest, text="Cargo:", font=fonte(13, "bold")).grid(row=0, column=0, sticky="w")
        cargo_e = ctk.CTkEntry(f_dest, width=300)
        cargo_e.grid(row=1, column=0, padx=(0,10), pady=5)
        if editando: cargo_e.insert(0, dados['cargo_destinatario'])

        ctk.CTkLabel(f_dest, text="Órgão/Setor:", font=fonte(13, "bold")).grid(row=0, column=1, sticky="w")
        orgao_e = ctk.CTkEntry(f_dest, width=350)
        orgao_e.grid(row=1, column=1, pady=5)
        if editando: orgao_e.insert(0, dados['orgao_destinatario'])

        # Assunto e Tratamento
        f_ass = ctk.CTkFrame(scroll, fg_color="transparent")
        f_ass.pack(fill="x", pady=10)

        ctk.CTkLabel(f_ass, text="Assunto:", font=fonte(13, "bold")).grid(row=0, column=0, sticky="w")
        assunto_e = ctk.CTkEntry(f_ass, width=500)
        assunto_e.grid(row=1, column=0, padx=(0,10), pady=5)
        if editando: assunto_e.insert(0, dados['assunto'])

        ctk.CTkLabel(f_ass, text="Forma de Tratamento:", font=fonte(13, "bold")).grid(row=0, column=1, sticky="w")
        trat_e = ctk.CTkEntry(f_ass, width=150)
        trat_e.grid(row=1, column=1, pady=5)
        if editando: trat_e.insert(0, dados['forma_tratamento'])

        # Redação
        ctk.CTkLabel(scroll, text="Conteúdo do Ofício:", font=fonte(13, "bold")).pack(anchor="w", pady=(10,0))
        red_txt = ctk.CTkTextbox(scroll, height=350)
        red_txt.pack(fill="both", expand=True, pady=5)
        if editando: red_txt.insert("1.0", dados['redacao'])

        # Botões
        f_btns = ctk.CTkFrame(form, fg_color="transparent")
        f_btns.pack(fill="x", padx=20, pady=20)

        def fechar():
            if messagebox.askyesno("Confirmar", "Deseja sair sem salvar?"):
                form.destroy()
        
        ctk.CTkButton(f_btns, text="❌ Fechar", fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"], command=fechar).pack(side="left", padx=10)

        def chamar_ia():
            dados = {
                'destinatario': dest_e.get(),
                'cargo': cargo_e.get(),
                'orgao': orgao_e.get(),
                'assunto': assunto_e.get(),
                'tratamento': trat_e.get()
            }
            if not dados['assunto']:
                messagebox.showwarning("Atenção", "Preencha ao menos o Assunto para a IA redigir.")
                return
            
            form.config(cursor="watch")
            res = redigir_documento('oficio', dados)
            form.config(cursor="")
            
            if res.startswith("Erro"):
                messagebox.showerror("Erro IA", res)
            else:
                red_txt.delete("1.0", "end")
                red_txt.insert("1.0", res)
                form.update_idletasks() # Força a atualização visual da caixa de texto
                messagebox.showinfo("Sucesso", "Ofício redigido com a ajuda da SofIA! Por favor, antes de enviar, verifique o campo 'Conteúdo do Ofício'.")

        ctk.CTkButton(f_btns, text="🤖 REDIGIR COM SofIA", fg_color=CORES["dourado"], hover_color=CORES["dourado_hover"], 
                      text_color=CORES["texto_escuro"], command=chamar_ia).pack(side="left", padx=10)

        def salvar():
            conn = get_connection()
            try:
                vals = (num_v.get(), ano_v.get(), data_tela_para_bd(data_v.get()), dest_e.get(), 
                        cargo_e.get(), orgao_e.get(), assunto_e.get(), trat_e.get(), red_txt.get("1.0", "end-1c"))
                if editando:
                    conn.execute("UPDATE oficios SET numero=?, ano=?, data=?, destinatario=?, cargo_destinatario=?, orgao_destinatario=?, assunto=?, forma_tratamento=?, redacao=? WHERE id=?", vals + (oficio_id,))
                else:
                    conn.execute("INSERT INTO oficios (numero, ano, data, destinatario, cargo_destinatario, orgao_destinatario, assunto, forma_tratamento, redacao) VALUES (?,?,?,?,?,?,?,?,?)", vals)
                conn.commit()
                messagebox.showinfo("Sucesso", "Ofício salvo com sucesso!")
                form.destroy()
                self._carregar_lista()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
            finally:
                conn.close()

        def gerar_pdf():
            tipo = "Ofício"
            titulo = f"Ofício nº {num_v.get()}/{ano_v.get()}"
            conteudo = f"Destinatário: {dest_e.get()}\nCargo: {cargo_e.get()}\nÓrgão: {orgao_e.get()}\n\nAssunto: {assunto_e.get()}\n\n{red_txt.get('1.0', 'end-1c')}"
            ok, path = gerar_pdf_documento("oficio", titulo, conteudo)
            if ok:
                messagebox.showinfo("PDF Gerado", f"PDF salvo e aberto com sucesso!\nCaminho: {path}")
            else:
                messagebox.showerror("Erro PDF", f"Falha ao gerar PDF: {path}")

        ctk.CTkButton(f_btns, text="💾 Salvar", fg_color=CORES["sucesso"], hover_color=CORES["sucesso_hover"], command=salvar).pack(side="right", padx=10)
        ctk.CTkButton(f_btns, text="🖨 Gerar PDF", fg_color=CORES["acento"], hover_color=CORES["acento_hover"], command=gerar_pdf).pack(side="right", padx=10)
