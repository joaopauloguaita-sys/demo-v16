import customtkinter as ctk
from tkinter import messagebox, filedialog
import sys, os
from datetime import datetime
from database.db import get_connection
from tema import CORES, fonte
from modules.requerimentos_seed import gerar_documento_word

class CertificadoConclusaoModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.turmas_dict = {}
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header, text="📜 Emissão de Certificados de Conclusão", font=fonte(22, "bold"), text_color=CORES["dourado"]).pack(pady=15)

        container = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=15)
        container.pack(pady=20, padx=50, fill="both", expand=True)

        # 1. Seleção de Turma
        ctk.CTkLabel(container, text="1. Selecione a Turma:", font=fonte(13, "bold"), text_color=CORES["subtexto"]).pack(pady=(30, 5))
        self.combo_turma = ctk.CTkOptionMenu(container, width=400, values=self.carregar_turmas())
        self.combo_turma.pack(pady=5)

        # 2. Nome do Professor
        ctk.CTkLabel(container, text="2. Nome do(a) Professor(a):", font=fonte(13, "bold"), text_color=CORES["subtexto"]).pack(pady=(20, 5))
        self.ent_professor = ctk.CTkEntry(container, width=400, placeholder_text="Ex: Prof. Maria Silva")
        self.ent_professor.pack(pady=5)

        # Botão Gerar
        ctk.CTkButton(container, text="🚀 GERAR TODOS OS CERTIFICADOS", font=fonte(14, "bold"), 
                      fg_color="#27ae60", hover_color="#219150", height=55, width=400,
                      command=self.gerar_em_lote).pack(pady=40)

        ctk.CTkLabel(container, text="Dica: O sistema criará um único arquivo Word com uma página para cada aluno da turma.", 
                     font=fonte(11), text_color="#777").pack(pady=10)

    def carregar_turmas(self):
        try:
            conn = get_connection()
            res = conn.execute("SELECT id, nome_completo FROM turmas WHERE ativo=1 ORDER BY nome_completo").fetchall()
            conn.close()
            self.turmas_dict = {r[1]: r[0] for r in res}
            return list(self.turmas_dict.keys()) if res else ["Nenhuma turma encontrada"]
        except: return ["Erro ao carregar"]

    def gerar_em_lote(self):
        turma_nome = self.combo_turma.get()
        turma_id = self.turmas_dict.get(turma_nome)
        professor = self.ent_professor.get().strip()

        if not turma_id:
            messagebox.showwarning("Aviso", "Selecione uma turma válida.")
            return
        if not professor:
            messagebox.showwarning("Aviso", "Informe o nome do professor(a).")
            return

        conn = get_connection()
        # Busca alunos ativos daquela turma
        query = "SELECT nome FROM alunos WHERE turma_id=? AND ativo=1 AND arquivado=0 ORDER BY nome ASC"
        alunos_res = conn.execute(query, (turma_id,)).fetchall()
        conn.close()

        if not alunos_res:
            messagebox.showwarning("Aviso", "Não há alunos ativos nesta turma.")
            return

        # Prepara os dados para o loop do Word
        # A tag 'alunos' é a que você usará no Word para o loop
        lista_para_word = [{"nome": a[0], "turma": turma_nome} for a in alunos_res]

        contexto = {
            "alunos": lista_para_word,
            "professor": professor.upper(),
            "nome": f"Turma_{turma_nome}" # Usado apenas para sugerir nome de arquivo
        }

        messagebox.showinfo("Processando", f"Gerando {len(lista_para_word)} certificados...")
        gerar_documento_word("certificado_conclusao", contexto, parent=self)