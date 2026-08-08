import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import sys, os
from datetime import date
import sqlite3
from database.db import get_connection
from tema import CORES, fonte, data_bd_para_tela, data_tela_para_bd, vincular_mascara, mascara_data
import pdf_utils

class PatrimonioModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        
        # GARANTE QUE A TABELA E AS COLUNAS NOVAS EXISTAM
        self._garantir_tabela_existe()
        
        self._build_ui()
        self.carregar_lista()

    def _garantir_tabela_existe(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patrimonio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_nome TEXT NOT NULL,
                    tipo_item TEXT,
                    numero_patrimonio TEXT,
                    estado TEXT,
                    localizacao TEXT,
                    data_entrada TEXT,
                    origem TEXT,
                    descricao TEXT
                )
            """)
            
            cursor.execute("PRAGMA table_info(patrimonio)")
            colunas = [col[1] for col in cursor.fetchall()]
            
            if "tipo_item" not in colunas:
                cursor.execute("ALTER TABLE patrimonio ADD COLUMN tipo_item TEXT")
            if "descricao" not in colunas:
                cursor.execute("ALTER TABLE patrimonio ADD COLUMN descricao TEXT")
            
            conn.commit()
        except: pass
        finally: conn.close()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header, text="📦 Controle de Patrimônio da Instituição", font=fonte(22, "bold"), text_color=CORES["dourado"]).pack(pady=15)

        self.main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20)

        # --- ÁREA DE CADASTRO ---
        form_f = ctk.CTkFrame(self.main_container, fg_color=CORES["card"], corner_radius=15)
        form_f.pack(fill="x", pady=10)
        
        ctk.CTkLabel(form_f, text="➕ Cadastrar Novo Patrimônio", font=fonte(14, "bold"), text_color=CORES["primaria"]).grid(row=0, column=0, columnspan=4, pady=15)

        # Campos (Organizados corretamente)
        self.e_nome = self._add_field(form_f, "Nome do Item:", 1, 0, "Ex: Computador, Mesa")
        self.e_tipo = self._add_field(form_f, "Tipo/Categoria:", 1, 1, "Ex: Informática, Mobiliário")

        self.e_patrimonio = self._add_field(form_f, "Nº Patrimônio:", 2, 0, "Deixe vazio se não tiver")
        
        ctk.CTkLabel(form_f, text="Estado de Conservação:", font=fonte(11, "bold")).grid(row=4, column=1, padx=20, sticky="w")
        self.cb_estado = ctk.CTkOptionMenu(form_f, values=["Novo", "Bom", "Regular", "Inservível"], width=200)
        self.cb_estado.grid(row=5, column=1, padx=20, pady=(0,10), sticky="ew")

        self.e_local = self._add_field(form_f, "Localização (Sala/Setor):", 3, 0, "Ex: Secretaria, Sala 05")
        
        ctk.CTkLabel(form_f, text="Origem do Bem:", font=fonte(11, "bold")).grid(row=6, column=1, padx=20, sticky="w")
        self.cb_origem = ctk.CTkOptionMenu(form_f, values=["Prefeitura", "Escola", "Doação", "Estado"], width=200)
        self.cb_origem.grid(row=7, column=1, padx=20, pady=(0,10), sticky="ew")

        self.e_data = self._add_field(form_f, "Data de Entrada:", 4, 0)
        vincular_mascara(self.e_data, mascara_data)
        self.e_data.insert(0, date.today().strftime("%d/%m/%Y"))
        
        ctk.CTkLabel(form_f, text="Quantidade de Itens:", font=fonte(11, "bold"), text_color="#1a73e8").grid(row=8, column=1, padx=20, sticky="w")
        self.e_qtd = ctk.CTkEntry(form_f, width=100); self.e_qtd.insert(0, "1"); self.e_qtd.grid(row=9, column=1, padx=20, pady=(0,10), sticky="w")

        ctk.CTkLabel(form_f, text="Descrição Detalhada / Observações:", font=fonte(11, "bold")).grid(row=10, column=0, padx=20, sticky="w")
        self.e_desc = ctk.CTkEntry(form_f, placeholder_text="Marca, Modelo, detalhes adicionais...", width=600); 
        self.e_desc.grid(row=11, column=0, columnspan=2, padx=20, pady=(0,20), sticky="ew")

        ctk.CTkButton(form_f, text="💾 SALVAR NO PATRIMÔNIO", font=fonte(13, "bold"), fg_color="#27ae60", height=45, command=self.salvar_item).grid(row=11, column=2, columnspan=2, padx=20, pady=(0,20), sticky="ew")

        # --- ÁREA DE LISTAGEM ---
        list_f = ctk.CTkFrame(self.main_container, fg_color=CORES["card"], corner_radius=15)
        list_f.pack(fill="both", expand=True, pady=10)

        filter_f = ctk.CTkFrame(list_f, fg_color="transparent")
        filter_f.pack(fill="x", padx=10, pady=10)
        
        self.e_busca = ctk.CTkEntry(filter_f, placeholder_text="🔍 Buscar item ou patrimônio...", width=350)
        self.e_busca.pack(side="left", padx=10)
        self.e_busca.bind("<KeyRelease>", lambda e: self.carregar_lista())

        ctk.CTkButton(filter_f, text="🖨️ Relatório Geral", font=fonte(11, "bold"), fg_color="#555", command=self.exportar_pdf).pack(side="right", padx=10)

        # Tabela
        table_container = ctk.CTkFrame(list_f, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "nome", "tipo", "pat", "estado", "local", "origem", "data", "desc")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=15)
        
        titulos = [("id", "ID", 40), ("nome", "Item", 180), ("tipo", "Tipo", 120), ("pat", "Patr.", 100), 
                   ("estado", "Estado", 100), ("local", "Local", 120), ("origem", "Origem", 100), 
                   ("data", "Data", 100), ("desc", "Descrição", 250)]
        
        for cid, txt, larg in titulos:
            self.tree.heading(cid, text=txt, anchor="w")
            self.tree.column(cid, width=larg, anchor="w")

        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview); vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(list_f, orient="horizontal", command=self.tree.xview); hsb.pack(side="bottom", fill="x", padx=10)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(fill="both", expand=True)

        ctk.CTkButton(list_f, text="🗑️ Remover Selecionado", font=fonte(11, "bold"), fg_color="#c62828", command=self.excluir_item).pack(pady=10, anchor="e", padx=15)

    def _add_field(self, master, label, r, c, ph=""):
        ctk.CTkLabel(master, text=label, font=fonte(11, "bold")).grid(row=r*2, column=c, padx=20, pady=(10,0), sticky="w")
        e = ctk.CTkEntry(master, width=300, placeholder_text=ph)
        e.grid(row=r*2+1, column=c, padx=20, pady=(0,10), sticky="ew")
        return e

    def salvar_item(self):
        nome = self.e_nome.get().strip()
        try: qtd = int(self.e_qtd.get() or 1)
        except: qtd = 1
        if not nome: return messagebox.showwarning("Erro", "O nome do item é obrigatório!")

        conn = get_connection()
        try:
            for _ in range(qtd):
                conn.execute("""
                    INSERT INTO patrimonio (item_nome, tipo_item, numero_patrimonio, estado, localizacao, data_entrada, origem, descricao)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (nome.upper(), self.e_tipo.get().upper(), self.e_patrimonio.get(), self.cb_estado.get(), 
                      self.e_local.get().upper(), data_tela_para_bd(self.e_data.get()), self.cb_origem.get(), self.e_desc.get()))
            conn.commit()
            messagebox.showinfo("Sucesso", f"{qtd} item(ns) salvo(s)!")
            self.carregar_lista()
            for ent in [self.e_nome, self.e_tipo, self.e_patrimonio, self.e_local, self.e_desc]: ent.delete(0, 'end')
        except Exception as e: messagebox.showerror("Erro ao Salvar", str(e))
        finally: conn.close()

    def carregar_lista(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        busca = f"%{self.e_busca.get()}%"
        conn = get_connection()
        try:
            res = conn.execute("""
                SELECT id, item_nome, tipo_item, numero_patrimonio, estado, localizacao, origem, data_entrada, descricao 
                FROM patrimonio 
                WHERE item_nome LIKE ? OR numero_patrimonio LIKE ? OR tipo_item LIKE ?
                ORDER BY item_nome ASC
            """, (busca, busca, busca)).fetchall()
            
            for r in res:
                # CONVERSÃO MANUAL PARA TEXTO (Corrige o erro do Row object)
                valores = (str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), data_bd_para_tela(r[7]), str(r[8]))
                self.tree.insert("", "end", values=valores)
        except: pass
        finally: conn.close()

    def excluir_item(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Confirmar", "Deseja excluir este item definitivamente?"):
            conn = get_connection()
            conn.execute("DELETE FROM patrimonio WHERE id = ?", (self.tree.item(sel[0])['values'][0],))
            conn.commit(); conn.close()
            self.carregar_lista()

    def exportar_pdf(self):
        conn = get_connection()
        res = conn.execute("SELECT numero_patrimonio, item_nome, tipo_item, estado, localizacao, origem FROM patrimonio ORDER BY localizacao ASC").fetchall(); conn.close()
        if not res: return
        l = [["Nº PATR.", "ITEM", "TIPO", "ESTADO", "LOCALIZAÇÃO", "ORIGEM"]]
        for r in res: l.append([str(r[0]) if r[0] else "-", str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5])])
        pdf_utils.salvar_pdf_como("Inventário", [("titulo", "INVENTÁRIO DE PATRIMÔNIO"), ("tabela", l)], "Patrimonio_Geral.pdf", parent=self)