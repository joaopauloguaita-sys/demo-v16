import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import date
from database.db import get_connection
from tema import CORES, fonte
from modules.requerimentos_seed import gerar_documento_word
import pdf_utils

class FanfarraModule(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.aluno_encontrado = None
        
        # GARANTE QUE A TABELA EXISTE ANTES DE CARREGAR A TELA
        self._garantir_tabela_existe()
        
        self._build_ui()
        self.carregar_listas()

    def _garantir_tabela_existe(self):
        """Cria a tabela no banco local automaticamente se ela não existir"""
        conn = get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fanfarra_membros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aluno_id INTEGER UNIQUE,
                    categoria TEXT, 
                    data_inclusao TEXT
                )
            """)
            conn.commit()
        except Exception as e:
            print(f"Erro ao criar tabela fanfarra: {e}")
        finally:
            conn.close()

    def _build_ui(self):
        # --- CABEÇALHO ---
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(header, text="🎺 Gestão de Fanfarra e Balizas", font=fonte(22, "bold"), text_color=CORES["dourado"]).pack(pady=15)

        # --- ÁREA DE INCLUSÃO ---
        input_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        input_f.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(input_f, text="Digite o CGM do Aluno:", font=fonte(12, "bold")).grid(row=0, column=0, padx=20, pady=(15,0), sticky="w")
        self.ent_cgm = ctk.CTkEntry(input_f, width=150)
        self.ent_cgm.grid(row=1, column=0, padx=20, pady=5)
        self.ent_cgm.bind("<Return>", lambda e: self.buscar_aluno())
        
        ctk.CTkButton(input_f, text="🔍 Buscar", width=100, command=self.buscar_aluno).grid(row=1, column=1, padx=5, pady=5)

        self.lbl_info_aluno = ctk.CTkLabel(input_f, text="Aguardando CGM...", font=fonte(12, "normal"), text_color="#555")
        self.lbl_info_aluno.grid(row=1, column=2, padx=20, pady=5)

        ctk.CTkLabel(input_f, text="Categoria:", font=fonte(12, "bold")).grid(row=0, column=3, padx=20, pady=(15,0), sticky="w")
        self.combo_cat = ctk.CTkOptionMenu(input_f, values=["FANFARRA", "BALIZA"], width=150)
        self.combo_cat.grid(row=1, column=3, padx=20, pady=5)

        ctk.CTkButton(input_f, text="➕ Incluir na Lista", fg_color="#27ae60", hover_color="#219150", command=self.incluir_membro).grid(row=1, column=4, padx=20, pady=5)

        # --- QUADROS DE LISTAGEM ---
        listas_f = ctk.CTkFrame(self, fg_color="transparent")
        listas_f.pack(fill="both", expand=True, pady=10)

        self.frame_fan = self.criar_quadro_lista(listas_f, "LISTA DA FANFARRA", "#0a2463")
        self.frame_fan["frame"].pack(fill="x", padx=10, pady=10)
        
        self.frame_bal = self.criar_quadro_lista(listas_f, "LISTA DAS BALIZAS", "#8e44ad")
        self.frame_bal["frame"].pack(fill="x", padx=10, pady=10)

        # --- BOTÕES DE AÇÃO FINAL ---
        btn_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        btn_f.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkButton(btn_f, text="📄 Baixar Listas (PDF)", fg_color="#555", command=self.exportar_pdf).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(btn_f, text="📝 Gerar Autorização", fg_color=CORES["acento"], command=self.gerar_autorizacao).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="🎓 GERAR TODOS OS CERTIFICADOS", fg_color="#d35400", command=self.gerar_certificados).pack(side="right", padx=20)

    def criar_quadro_lista(self, master, titulo, cor):
        f = ctk.CTkFrame(master, fg_color=CORES["card"], border_width=2, border_color=cor)
        ctk.CTkLabel(f, text=titulo, font=fonte(14, "bold"), text_color=cor).pack(pady=10)
        
        tree = ttk.Treeview(f, columns=("nome", "cgm", "turma", "turno"), show="headings", height=8)
        tree.heading("nome", text="Nome do Aluno"); tree.column("nome", width=350)
        tree.heading("cgm", text="CGM"); tree.column("cgm", width=100)
        tree.heading("turma", text="Série/Turma"); tree.column("turma", width=150)
        tree.heading("turno", text="Turno"); tree.column("turno", width=100)
        tree.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(f, text="🗑️ Excluir Selecionado", fg_color="#c62828", width=150, height=25, 
                      command=lambda t=tree: self.excluir_membro(t)).pack(pady=5, anchor="e", padx=10)
        return {"frame": f, "tree": tree}

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
            conn.execute("INSERT INTO fanfarra_membros (aluno_id, categoria, data_inclusao) VALUES (?,?,?)",
                         (self.aluno_encontrado["id"], self.combo_cat.get(), date.today().isoformat()))
            conn.commit()
            self.carregar_listas()
            self.ent_cgm.delete(0, "end")
            self.lbl_info_aluno.configure(text="Incluso com sucesso!", text_color="blue")
        except:
            messagebox.showerror("Erro", "Este aluno já está na lista!")
        finally:
            conn.close()

    def carregar_listas(self):
        for t in [self.frame_fan["tree"], self.frame_bal["tree"]]:
            for i in t.get_children(): t.delete(i)
            
        conn = get_connection()
        try:
            query = """
                SELECT f.id, a.nome, a.cgm, t.nome_completo, t.turno, f.categoria
                FROM fanfarra_membros f
                JOIN alunos a ON f.aluno_id = a.id
                LEFT JOIN turmas t ON a.turma_id = t.id
                ORDER BY a.nome ASC
            """
            membros = conn.execute(query).fetchall()
            for m in membros:
                dados = (m[1], m[2], m[3], m[4])
                if m[5] == "FANFARRA": self.frame_fan["tree"].insert("", "end", iid=m[0], values=dados)
                else: self.frame_bal["tree"].insert("", "end", iid=m[0], values=dados)
        except:
            pass
        finally:
            conn.close()

    def excluir_membro(self, tree):
        sel = tree.selection()
        if not sel: return
        if messagebox.askyesno("Confirmar", "Remover este integrante definitivamente?"):
            conn = get_connection()
            conn.execute("DELETE FROM fanfarra_membros WHERE id = ?", (sel[0],))
            conn.commit(); conn.close()
            self.carregar_listas()

    def gerar_autorizacao(self):
        sel = self.frame_fan["tree"].selection() or self.frame_bal["tree"].selection()
        if not sel: 
            messagebox.showwarning("Aviso", "Selecione um aluno na lista primeiro!")
            return
        
        conn = get_connection()
        dados = conn.execute("""
            SELECT a.nome, t.nome_completo, t.turno, a.responsavel, a.cpf_mae, a.cpf_pai, f.categoria, a.data_nascimento
            FROM fanfarra_membros f
            JOIN alunos a ON f.aluno_id = a.id
            LEFT JOIN turmas t ON a.turma_id = t.id
            WHERE f.id = ?
        """, (sel[0],)).fetchone()
        conn.close()
        
        cpf = dados[4] if (dados[4] and dados[4].strip()) else (dados[5] if dados[5] else "")
        
        # --- AQUI ESTÁ A CORREÇÃO ---
        from tema import data_bd_para_tela # Importamos a função de inverter data
        data_formatada = data_bd_para_tela(dados[7]) # Converte de 2015-10-10 para 10/10/2015
        
        contexto = {
            "aluno": dados[0], 
            "turma_var": dados[1], 
            "turno": dados[2],
            "responsavel": dados[3], 
            "cpf": cpf, 
            "como_vai": dados[6],
            "data_nascimento": data_formatada # Agora a data vai correta para o Word
        }
        gerar_documento_word("autorizacao_fanfarra", contexto, parent=self)

    def gerar_certificados(self):
        conn = get_connection()
        # BUSCA NOME E CATEGORIA (Fanfarra/Baliza)
        query = """
            SELECT a.nome, f.categoria 
            FROM fanfarra_membros f 
            JOIN alunos a ON f.aluno_id = a.id 
            ORDER BY a.nome ASC
        """
        membros = conn.execute(query).fetchall()
        conn.close()
        
        if not membros:
            messagebox.showwarning("Aviso", "Não há ninguém na lista para gerar certificados!")
            return
        
        # PREPARA A LISTA COM NOME E CATEGORIA PARA CADA ITEM
        lista_membros = [{"nome": m[0], "categoria": m[1]} for m in membros]
        
        messagebox.showinfo("Dica de Impressão", 
            "O Word será aberto com todos os certificados.\n\n"
            "Certifique-se de que a tag da categoria no Word seja: {{ item.categoria }}")

        # Envia para o gerador de Word
        gerar_documento_word("certificado_fanfarra", {"membros": lista_membros}, parent=self)

    def exportar_pdf(self):
        conn = get_connection()
        membros = conn.execute("""
            SELECT a.nome, a.cgm, t.nome_completo, f.categoria 
            FROM fanfarra_membros f 
            JOIN alunos a ON f.aluno_id = a.id 
            LEFT JOIN turmas t ON a.turma_id = t.id 
            ORDER BY f.categoria, a.nome
        """).fetchall()
        conn.close()
        
        if not membros: return
        
        linhas = [["Nome do Aluno", "CGM", "Turma", "Categoria"]]
        for m in membros:
            linhas.append([m[0], m[1], m[2] or "-", m[3]])
            
        pdf_utils.salvar_pdf_como("Listagem Fanfarra e Balizas", 
                                   [("titulo", "Integrantes da Fanfarra e Balizas"), ("tabela", linhas)], 
                                   "Lista_Fanfarra.pdf", parent=self)