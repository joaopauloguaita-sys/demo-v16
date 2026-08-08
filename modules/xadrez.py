import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import date
from database.db import get_connection
from tema import CORES, fonte, data_bd_para_tela
from modules.requerimentos_seed import gerar_documento_word
import pdf_utils

class XadrezModule(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.aluno_encontrado = None
        self._garantir_tabela_existe()
        self._build_ui()
        self.carregar_lista()

    def _garantir_tabela_existe(self):
        conn = get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS xadrez_membros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aluno_id INTEGER UNIQUE,
                    data_inclusao TEXT
                )
            """)
            conn.commit()
        except: pass
        finally: conn.close()

    def _build_ui(self):
        # --- CABEÇALHO ---
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(header, text="♟️ Projeto de Xadrez Escolar", font=fonte(22, "bold"), text_color="#2c3e50").pack(pady=15)

        # --- ÁREA DE INCLUSÃO ---
        input_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        input_f.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(input_f, text="Digite o CGM do Aluno:", font=fonte(12, "bold")).grid(row=0, column=0, padx=20, pady=(15,0), sticky="w")
        self.ent_cgm = ctk.CTkEntry(input_f, width=200, placeholder_text="CGM do aluno...")
        self.ent_cgm.grid(row=1, column=0, padx=20, pady=10)
        self.ent_cgm.bind("<Return>", lambda e: self.buscar_aluno())
        
        ctk.CTkButton(input_f, text="🔍 Buscar", width=120, command=self.buscar_aluno).grid(row=1, column=1, padx=5, pady=10)
        self.lbl_info_aluno = ctk.CTkLabel(input_f, text="Aguardando CGM...", font=fonte(12, "normal"), text_color="#555")
        self.lbl_info_aluno.grid(row=1, column=2, padx=20, pady=10)
        ctk.CTkButton(input_f, text="➕ Incluir no Xadrez", fg_color="#27ae60", hover_color="#219150", width=180, command=self.incluir_membro).grid(row=1, column=3, padx=20, pady=10)

        # --- QUADRO DE LISTAGEM ---
        f_lista = ctk.CTkFrame(self, fg_color=CORES["card"], border_width=2, border_color="#2c3e50", corner_radius=12)
        f_lista.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(f_lista, text="LISTA DE ALUNOS - XADREZ", font=fonte(14, "bold"), text_color="#2c3e50").pack(pady=10)
        
        self.tree = ttk.Treeview(f_lista, columns=("nome", "cgm", "turma", "turno"), show="headings", height=15)
        self.tree.heading("nome", text="Nome do Aluno"); self.tree.column("nome", width=400)
        self.tree.heading("cgm", text="CGM"); self.tree.column("cgm", width=120)
        self.tree.heading("turma", text="Série/Turma"); self.tree.column("turma", width=150)
        self.tree.heading("turno", text="Turno"); self.tree.column("turno", width=120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkButton(f_lista, text="🗑️ Remover Selecionado", fg_color="#c62828", width=180, height=25, 
                      command=self.excluir_membro).pack(pady=10, anchor="e", padx=10)

        # --- BOTÕES DE AÇÃO ---
        btn_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        btn_f.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(btn_f, text="📄 Gerar Lista em PDF", fg_color="#555", command=self.exportar_pdf).pack(side="left", padx=20, pady=20)
        
        # NOVO BOTÃO: Gerar Autorização
        ctk.CTkButton(btn_f, text="📝 Gerar Autorização", fg_color=CORES["acento"], command=self.gerar_autorizacao).pack(side="left", padx=5, pady=20)
        
        ctk.CTkButton(btn_f, text="🎓 GERAR TODOS OS CERTIFICADOS", fg_color="#d35400", height=45, command=self.gerar_certificados).pack(side="right", padx=20, pady=20)

    def buscar_aluno(self):
        cgm = self.ent_cgm.get().strip()
        if not cgm: return
        conn = get_connection()
        res = conn.execute("""
            SELECT a.id, a.nome, t.nome_completo, t.turno 
            FROM alunos a 
            LEFT JOIN turmas t ON a.turma_id = t.id 
            WHERE a.cgm = ? AND a.ativo = 1
        """, (cgm,)).fetchone()
        conn.close()
        if res:
            self.aluno_encontrado = {"id": res[0], "nome": res[1], "turma": res[2], "turno": res[3]}
            self.lbl_info_aluno.configure(text=f"✅ {res[1]}", text_color="green")
        else:
            self.aluno_encontrado = None
            self.lbl_info_aluno.configure(text="❌ Aluno não encontrado!", text_color="red")

    def incluir_membro(self):
        if not self.aluno_encontrado:
            messagebox.showwarning("Aviso", "Busque um aluno pelo CGM primeiro!")
            return
        conn = get_connection()
        try:
            conn.execute("INSERT INTO xadrez_membros (aluno_id, data_inclusao) VALUES (?,?)",
                         (self.aluno_encontrado["id"], date.today().isoformat()))
            conn.commit()
            self.carregar_lista()
            self.ent_cgm.delete(0, "end")
            self.lbl_info_aluno.configure(text="Incluso com sucesso!", text_color="blue")
        except: messagebox.showerror("Erro", "Este aluno já está na lista de Xadrez!")
        finally: conn.close()

    def carregar_lista(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_connection()
        membros = conn.execute("""
            SELECT x.id, a.nome, a.cgm, t.nome_completo, t.turno
            FROM xadrez_membros x
            JOIN alunos a ON x.aluno_id = a.id
            LEFT JOIN turmas t ON a.turma_id = t.id
            ORDER BY a.nome ASC
        """).fetchall()
        conn.close()
        for m in membros:
            self.tree.insert("", "end", iid=m[0], values=(m[1], m[2], m[3], m[4]))

    def excluir_membro(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Confirmar", "Remover este aluno do Xadrez?"):
            conn = get_connection()
            conn.execute("DELETE FROM xadrez_membros WHERE id = ?", (sel[0],))
            conn.commit(); conn.close()
            self.carregar_lista()

    def gerar_autorizacao(self):
        sel = self.tree.selection()
        if not sel: 
            messagebox.showwarning("Aviso", "Selecione um aluno na lista primeiro!")
            return
        
        conn = get_connection()
        dados = conn.execute("""
            SELECT a.nome, t.nome_completo, t.turno, a.responsavel, a.cpf_mae, a.cpf_pai, a.data_nascimento
            FROM xadrez_membros x
            JOIN alunos a ON x.aluno_id = a.id
            LEFT JOIN turmas t ON a.turma_id = t.id
            WHERE x.id = ?
        """, (sel[0],)).fetchone()
        conn.close()
        
        cpf = dados[4] if (dados[4] and dados[4].strip()) else (dados[5] if dados[5] else "")
        data_formatada = data_bd_para_tela(dados[6])
        
        contexto = {
            "aluno": dados[0], "turma_var": dados[1], "turno": dados[2],
            "responsavel": dados[3], "cpf": cpf, "data_nascimento": data_formatada
        }
        gerar_documento_word("autorizacao_xadrez", contexto, parent=self)

    def gerar_certificados(self):
        conn = get_connection()
        membros = conn.execute("SELECT a.nome FROM xadrez_membros x JOIN alunos a ON x.aluno_id = a.id ORDER BY a.nome ASC").fetchall()
        conn.close()
        if not membros: return
        lista_membros = [{"nome": m[0], "categoria": "AULA DE XADREZ"} for m in membros]
        gerar_documento_word("certificado_fanfarra", {"membros": lista_membros}, parent=self)

    def exportar_pdf(self):
        conn = get_connection()
        membros = conn.execute("""
            SELECT a.nome, a.cgm, t.nome_completo, t.turno FROM xadrez_membros x JOIN alunos a ON x.aluno_id = a.id LEFT JOIN turmas t ON a.turma_id = t.id ORDER BY a.nome ASC
        """).fetchall(); conn.close()
        if not membros: return
        linhas = [["Nome do Aluno", "CGM", "Série/Turma", "Turno"]]
        for m in membros: linhas.append([m[0], m[1], m[2] or "-", m[3] or "-"])
        pdf_utils.salvar_pdf_como("Lista Alunos Xadrez", [("titulo", "Alunos de Xadrez"), ("tabela", linhas)], "Lista_Xadrez.pdf", parent=self)