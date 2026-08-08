import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte, data_bd_para_tela, data_tela_para_bd
from modules.ia_engine import redigir_documento
from modules.pdf_engine import gerar_pdf_documento

class AtasModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()

    def _build_ui(self):
        # Título
        topo = ctk.CTkFrame(self, fg_color=CORES["sidebar"], height=50, corner_radius=0)
        topo.pack(fill="x", side="top")
        ctk.CTkLabel(topo, text="📝 Gestão de Atas", font=fonte(16, "bold"), text_color=CORES["texto_claro"]).pack(side="left", padx=20)
        
        btn_nova = ctk.CTkButton(topo, text="+ Nova Ata", fg_color=CORES["sucesso"], hover_color=CORES["sucesso_hover"],
                                 command=self._abrir_formulario, width=120)
        btn_nova.pack(side="right", padx=20, pady=10)

        # Filtros
        f_filtros = ctk.CTkFrame(self, fg_color="transparent")
        f_filtros.pack(fill="x", padx=20, pady=10)
        
        self.busca_ent = ctk.CTkEntry(f_filtros, placeholder_text="Buscar por pauta ou data...", width=300)
        self.busca_ent.pack(side="left", padx=(0, 10))
        ctk.CTkButton(f_filtros, text="🔍 Buscar", width=100, command=self._carregar_lista).pack(side="left")

        # Tabela (Treeview) - nome de estilo próprio, não sobrescreve o global
        style = ttk.Style()
        style.configure("Atas.Treeview", background=CORES["card"], foreground=CORES["texto_escuro"],
                        rowheight=25, fieldbackground=CORES["card"], borderwidth=0, font=fonte(11))
        style.map("Atas.Treeview", background=[('selected', CORES["dourado"])])
        style.configure("Atas.Treeview.Heading", background=CORES["primaria"],
                        foreground=CORES["texto_claro"], font=fonte(10, "bold"), relief="flat")

        f_tabela = ctk.CTkFrame(self, fg_color="transparent")
        f_tabela.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(f_tabela, columns=("num", "data", "pauta"), show="headings",
                                 style="Atas.Treeview")
        self.tree.heading("num", text="Nº/Ano")
        self.tree.heading("data", text="Data")
        self.tree.heading("pauta", text="Pauta")
        
        self.tree.column("num", width=100, anchor="center")
        self.tree.column("data", width=100, anchor="center")
        self.tree.column("pauta", width=500)
        self.tree.pack(fill="both", expand=True, side="left")

        # Barra lateral de ações
        f_acoes = ctk.CTkFrame(f_tabela, fg_color="transparent")
        f_acoes.pack(side="right", fill="y", padx=(10, 0))

        ctk.CTkButton(f_acoes, text="✏️ Editar", width=100, fg_color=CORES["acento"], 
                      command=lambda: self._abrir_formulario(editando=True)).pack(pady=5)
        ctk.CTkButton(f_acoes, text="🗑️ Excluir", width=100, fg_color=CORES["perigo"], 
                      command=self._excluir_ata).pack(pady=5)
        
        self.tree.bind("<Double-1>", lambda e: self._abrir_formulario(editando=True))

        self._carregar_lista()

    def _carregar_lista(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        busca = f"%{self.busca_ent.get()}%"
        conn = get_connection()
        try:
            res = conn.execute("SELECT id, numero, ano, data, pauta FROM atas WHERE (pauta LIKE ? OR data LIKE ?) AND (excluido IS NULL OR excluido = 0) ORDER BY ano DESC, numero DESC", (busca, busca)).fetchall()
            for r in res:
                dt = data_bd_para_tela(r['data'])
                self.tree.insert("", "end", iid=r['id'], values=(f"{r['numero']}/{r['ano']}", dt, r['pauta']))
        finally:
            conn.close()

    def _excluir_ata(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione uma ata para excluir.")
            return
        if not messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir esta ata?"):
            return
        
        conn = get_connection()
        try:
            conn.execute("UPDATE atas SET excluido=1 WHERE id=?", (sel[0],))
            conn.commit()
            self._carregar_lista()
        finally:
            conn.close()

    def _abrir_formulario(self, editando=False):
        ata_id = None
        dados = {}
        if editando:
            sel = self.tree.selection()
            if not sel:
                messagebox.showwarning("Atenção", "Selecione uma ata para editar.")
                return
            ata_id = sel[0]
            conn = get_connection()
            dados = conn.execute("SELECT * FROM atas WHERE id=?", (ata_id,)).fetchone()
            conn.close()

        form = ctk.CTkToplevel(self)
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        form.title("📝 Nova Ata" if not editando else "✏️ Editar Ata")
        form.geometry("900x700")
        form.grab_set()

        # Layout do formulário
        scroll = ctk.CTkScrollableFrame(form, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Cabeçalho (Nº, Ano, Data, Hora)
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

        ctk.CTkLabel(f_cab, text="Hora:", font=fonte(13, "bold")).grid(row=0, column=6, padx=5, sticky="w")
        hora_v = ctk.StringVar(value=dados['hora'] if editando else datetime.now().strftime("%H:%M"))
        ctk.CTkEntry(f_cab, textvariable=hora_v, width=80).grid(row=0, column=7, padx=5)

        # Local e Pauta
        ctk.CTkLabel(scroll, text="Local:", font=fonte(13, "bold")).pack(anchor="w", pady=(10,0))
        local_e = ctk.CTkEntry(scroll, placeholder_text="Ex: Sala da Direção")
        local_e.pack(fill="x", pady=5)
        if editando: local_e.insert(0, dados['local'])

        ctk.CTkLabel(scroll, text="Pauta:", font=fonte(13, "bold")).pack(anchor="w", pady=(10,0))
        pauta_e = ctk.CTkEntry(scroll, placeholder_text="Assunto principal da reunião")
        pauta_e.pack(fill="x", pady=5)
        if editando: pauta_e.insert(0, dados['pauta'])

        # Participantes
        ctk.CTkLabel(scroll, text="Participantes:", font=fonte(13, "bold")).pack(anchor="w", pady=(10,0))
        part_txt = ctk.CTkTextbox(scroll, height=100)
        part_txt.pack(fill="x", pady=5)
        if editando: part_txt.insert("1.0", dados['participantes'])

        # Redação
        ctk.CTkLabel(scroll, text="Redação da Ata:", font=fonte(13, "bold")).pack(anchor="w", pady=(10,0))
        f_red = ctk.CTkFrame(scroll, fg_color="transparent")
        f_red.pack(fill="both", expand=True)
        
        red_txt = ctk.CTkTextbox(f_red, height=300)
        red_txt.pack(fill="both", expand=True, pady=5)
        if editando: red_txt.insert("1.0", dados['redacao'])

        # Botões de ação
        f_btns = ctk.CTkFrame(form, fg_color="transparent")
        f_btns.pack(fill="x", padx=20, pady=20)

        def fechar():
            if messagebox.askyesno("Confirmar", "Deseja sair sem salvar?"):
                form.destroy()
        
        ctk.CTkButton(f_btns, text="❌ Fechar", fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"], command=fechar).pack(side="left", padx=10)

        def chamar_ia():
            dados = {
                'pauta': pauta_e.get(),
                'data': data_v.get(),
                'hora': hora_v.get(),
                'local': local_e.get(),
                'participantes': part_txt.get("1.0", "end-1c")
            }
            if not dados['pauta']:
                messagebox.showwarning("Atenção", "Preencha ao menos a Pauta para a IA redigir.")
                return
            
            # Mostrar que está processando
            form.config(cursor="watch")
            res = redigir_documento('ata', dados)
            form.config(cursor="")
            
            if res.startswith("Erro"):
                messagebox.showerror("Erro IA", res)
            else:
                red_txt.delete("1.0", "end")
                red_txt.insert("1.0", res)
                form.update_idletasks() # Força a atualização visual da caixa de texto
                messagebox.showinfo("Sucesso", "Ata redigida com a ajuda da SofIA! Verifique e faça possíveis correções no campo 'Redação da Ata'.")

        ctk.CTkButton(f_btns, text="🤖 REDIGIR COM SofIA", fg_color=CORES["dourado"], hover_color=CORES["dourado_hover"], 
                      text_color=CORES["texto_escuro"], command=chamar_ia).pack(side="left", padx=10)

        def salvar():
            conn = get_connection()
            try:
                vals = (num_v.get(), ano_v.get(), data_tela_para_bd(data_v.get()), hora_v.get(), 
                        local_e.get(), pauta_e.get(), part_txt.get("1.0", "end-1c"), red_txt.get("1.0", "end-1c"))
                if editando:
                    conn.execute("UPDATE atas SET numero=?, ano=?, data=?, hora=?, local=?, pauta=?, participantes=?, redacao=? WHERE id=?", vals + (ata_id,))
                else:
                    conn.execute("INSERT INTO atas (numero, ano, data, hora, local, pauta, participantes, redacao) VALUES (?,?,?,?,?,?,?,?)", vals)
                conn.commit()
                messagebox.showinfo("Sucesso", "Ata salva com sucesso!")
                form.destroy()
                self._carregar_lista()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
            finally:
                conn.close()

        def gerar_pdf():
            tipo = "Ata"
            titulo = f"Ata de Reunião nº {num_v.get()}/{ano_v.get()}"
            # REMOVIDA A PALAVRA 'REDAÇÃO:' ABAIXO
            conteudo = f"Data: {data_v.get()}  Hora: {hora_v.get()}\nLocal: {local_e.get()}\nPauta: {pauta_e.get()}\n\nParticipantes:\n{part_txt.get('1.0', 'end-1c')}\n\n{red_txt.get('1.0', 'end-1c')}"
            ok, path = gerar_pdf_documento("ata", titulo, conteudo)
            if ok:
                messagebox.showinfo("PDF Gerado", f"PDF salvo e aberto com sucesso!\nCaminho: {path}")
            else:
                messagebox.showerror("Erro PDF", f"Falha ao gerar PDF: {path}")

        ctk.CTkButton(f_btns, text="💾 Salvar", fg_color=CORES["sucesso"], hover_color=CORES["sucesso_hover"], command=salvar).pack(side="right", padx=10)
        ctk.CTkButton(f_btns, text="🖨 Gerar PDF", fg_color=CORES["acento"], hover_color=CORES["acento_hover"], command=gerar_pdf).pack(side="right", padx=10)
