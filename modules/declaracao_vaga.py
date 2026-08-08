import customtkinter as ctk
from tkinter import messagebox
import sys, os
from database.db import get_connection
from tema import (CORES, fonte, vincular_mascara, mascara_data, 
                   mascara_cpf, mascara_telefone, data_bd_para_tela)
from modules.requerimentos_seed import gerar_documento_word

class DeclaracaoVagaModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.alunos_data = {} 
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # --- COLUNA ESQUERDA: DECLARAÇÃO DE VAGA (em cima) + COMPARECIMENTO (embaixo) ---
        coluna_esquerda = ctk.CTkScrollableFrame(self, fg_color="transparent")
        coluna_esquerda.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        frame_vaga = ctk.CTkFrame(coluna_esquerda, fg_color=CORES["card"], corner_radius=15)
        frame_vaga.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(frame_vaga, text="🎟️ Declaração de Vaga", font=fonte(18, "bold"), text_color=CORES["dourado"]).pack(pady=15)
        self.v_nome = self.criar_input(frame_vaga, "Nome do Aluno:")
        self.v_nasc = self.criar_input(frame_vaga, "Data de Nascimento:", mascara_data)
        
        ctk.CTkLabel(frame_vaga, text="Série Destino:", font=fonte(12, "bold")).pack(anchor="w", padx=30)
        self.v_serie = ctk.CTkOptionMenu(frame_vaga, width=300, values=self.get_turmas())
        self.v_serie.pack(pady=(0, 10))
        self.v_turno = self.criar_opcao(frame_vaga, "Turno:", ["Manhã", "Tarde", "Integral"])

        ctk.CTkButton(frame_vaga, text="🖨️ EMITIR VAGA", fg_color="#2980b9", height=45, width=250, command=self.emitir_vaga).pack(pady=(10, 25))

        # --- DECLARAÇÃO DE COMPARECIMENTO (embaixo, mesma coluna) ---
        frame_comp = ctk.CTkFrame(coluna_esquerda, fg_color=CORES["card"], corner_radius=15)
        frame_comp.pack(fill="x")

        ctk.CTkLabel(frame_comp, text="🗓 Declaração de Comparecimento", font=fonte(18, "bold"),
                     text_color="#d68910").pack(pady=(15, 5))
        ctk.CTkLabel(frame_comp, text="Para pais, responsáveis ou profissionais que compareceram à "
                     "escola e precisam do comprovante para o trabalho.",
                     font=fonte(11), text_color=CORES["subtexto"], wraplength=320, justify="center").pack(pady=(0, 15))

        self.c_nome = self.criar_input(frame_comp, "Nome do Comparecente:")
        self.c_cpf = ctk.CTkEntry(frame_comp, width=300)
        ctk.CTkLabel(frame_comp, text="CPF:", font=fonte(12, "bold")).pack(anchor="w", padx=30)
        self.c_cpf.pack(pady=(0, 10))
        vincular_mascara(self.c_cpf, mascara_cpf)

        linha_horarios = ctk.CTkFrame(frame_comp, fg_color="transparent")
        linha_horarios.pack(pady=(0, 15))
        col_h1 = ctk.CTkFrame(linha_horarios, fg_color="transparent")
        col_h1.pack(side="left", padx=8)
        ctk.CTkLabel(col_h1, text="Entrada:", font=fonte(12, "bold")).pack(anchor="w")
        self.c_hora_inicio = ctk.CTkEntry(col_h1, width=100, placeholder_text="00:00")
        self.c_hora_inicio.pack()
        col_h2 = ctk.CTkFrame(linha_horarios, fg_color="transparent")
        col_h2.pack(side="left", padx=8)
        ctk.CTkLabel(col_h2, text="Saída:", font=fonte(12, "bold")).pack(anchor="w")
        self.c_hora_fim = ctk.CTkEntry(col_h2, width=100, placeholder_text="00:00")
        self.c_hora_fim.pack()

        ctk.CTkButton(frame_comp, text="🖨️ EMITIR DECLARAÇÃO", fg_color="#d68910",
                      hover_color="#b9750d", height=45, width=250,
                      command=self.emitir_comparecimento).pack(pady=(5, 25))

        # --- COLUNA DIREITA: AUTORIZAÇÃO DE SAÍDA (ocupa a coluna inteira) ---
        frame_saida = ctk.CTkScrollableFrame(self, fg_color=CORES["card"], corner_radius=15, label_text="SISTEMA DE SAÍDA")
        frame_saida.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        
        ctk.CTkLabel(frame_saida, text="🛡️ Autorização de Saída", font=fonte(18, "bold"), text_color="#27ae60").pack(pady=15)

        ctk.CTkLabel(frame_saida, text="🔍 Buscar Aluno Cadastrado:", font=fonte(11, "bold"), text_color=CORES["acento"]).pack(anchor="w", padx=30)
        self.combo_busca = ctk.CTkComboBox(frame_saida, width=300, values=self.carregar_lista_alunos(), command=self.preencher_aluno_automatico)
        self.combo_busca.pack(pady=(0, 15))

        self.s_aluno = self.criar_input(frame_saida, "Nome do Aluno:")
        self.s_nasc = self.criar_input(frame_saida, "Data de Nascimento:", mascara_data)
        self.s_turma = self.criar_input(frame_saida, "Série/Turma:")
        self.s_resp = self.criar_input(frame_saida, "Responsável (Pai/Mãe):")
        self.s_cpf = self.criar_input(frame_saida, "CPF do Responsável:", mascara_cpf)
        self.s_tel = self.criar_input(frame_saida, "Telefone:", mascara_telefone)
        self.s_modo = self.criar_opcao(frame_saida, "Autorizado a sair como:", ["SOZINHO", "VAN ESCOLAR"])
        
        ctk.CTkLabel(frame_saida, text="Observação:", font=fonte(12, "bold")).pack(anchor="w", padx=30)
        self.s_obs = ctk.CTkEntry(frame_saida, width=300)
        self.s_obs.pack(pady=(0, 10))

        ctk.CTkButton(frame_saida, text="🚀 EMITIR AUTORIZAÇÃO", fg_color="#27ae60", hover_color="#219150", height=45, width=250, command=self.emitir_saida).pack(pady=30)

    def criar_input(self, master, label, mascara=None):
        ctk.CTkLabel(master, text=label, font=fonte(12, "bold")).pack(anchor="w", padx=30)
        e = ctk.CTkEntry(master, width=300)
        e.pack(pady=(0, 10))
        if mascara: vincular_mascara(e, mascara)
        return e

    def criar_opcao(self, master, label, opcoes):
        ctk.CTkLabel(master, text=label, font=fonte(12, "bold")).pack(anchor="w", padx=30)
        var = ctk.StringVar(value=opcoes[0])
        ctk.CTkOptionMenu(master, width=300, values=opcoes, variable=var).pack(pady=(0, 10))
        return var

    def get_turmas(self):
        try:
            conn = get_connection(); res = conn.execute("SELECT nome_completo FROM turmas WHERE ativo=1").fetchall(); conn.close()
            return [r[0] for r in res] if res else ["Sem Turmas"]
        except: return ["Erro ao carregar"]

    def carregar_lista_alunos(self):
        try:
            conn = get_connection()
            # SQL ALTERADA: Agora pegamos cpf_mae e cpf_pai
            query = """
                SELECT a.nome, a.data_nascimento, a.responsavel, a.cpf_mae, a.cpf_pai, a.telefone_responsavel, t.nome_completo 
                FROM alunos a 
                LEFT JOIN turmas t ON a.turma_id = t.id 
                WHERE a.ativo=1 AND a.arquivado=0
            """
            res = conn.execute(query).fetchall(); conn.close()
            nomes = []
            for r in res:
                # LÓGICA DE PRIORIDADE: Mãe > Pai > Vazio
                cpf_responsavel = r[3] if (r[3] and r[3].strip()) else (r[4] if (r[4] and r[4].strip()) else "")
                
                self.alunos_data[r[0]] = {
                    "nasc": data_bd_para_tela(r[1]), 
                    "resp": r[2], 
                    "cpf": cpf_responsavel, 
                    "tel": r[5], 
                    "turma": r[6] or ""
                }
                nomes.append(r[0])
            return sorted(nomes)
        except: return ["Nenhum aluno encontrado"]

    def preencher_aluno_automatico(self, nome_sel):
        if nome_sel in self.alunos_data:
            d = self.alunos_data[nome_sel]
            self.s_aluno.delete(0, "end"); self.s_aluno.insert(0, nome_sel)
            self.s_nasc.delete(0, "end"); self.s_nasc.insert(0, d["nasc"])
            self.s_resp.delete(0, "end"); self.s_resp.insert(0, d["resp"])
            self.s_cpf.delete(0, "end"); self.s_cpf.insert(0, d["cpf"])
            self.s_tel.delete(0, "end"); self.s_tel.insert(0, d["tel"])
            self.s_turma.delete(0, "end"); self.s_turma.insert(0, d["turma"])

    def emitir_vaga(self):
        dados = {"nome": self.v_nome.get().upper(), "data_nascimento": self.v_nasc.get(), "turma_var": self.v_serie.get(), "turno": self.v_turno.get()}
        gerar_documento_word("vaga", dados, parent=self)

    def emitir_saida(self):
        dados = {
            "aluno": self.s_aluno.get().upper(),
            "data_nascimento": self.s_nasc.get(),
            "responsavel": self.s_resp.get().upper(),
            "cpf": self.s_cpf.get(),
            "telefone": self.s_tel.get(),
            "como_vai": self.s_modo.get(),
            "obs": self.s_obs.get(),
            "turma_var": self.s_turma.get()
        }
        gerar_documento_word("saida", dados, parent=self)

    def emitir_comparecimento(self):
        if not self.c_nome.get().strip():
            messagebox.showerror("Erro", "Informe o nome do comparecente.", parent=self)
            return
        dados = {
            "nome": self.c_nome.get().upper(),
            "cpf": self.c_cpf.get(),
            "hora_inicio": self.c_hora_inicio.get(),
            "hora_fim": self.c_hora_fim.get(),
        }
        gerar_documento_word("comparecimento", dados, parent=self)