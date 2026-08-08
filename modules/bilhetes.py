import customtkinter as ctk
from tkinter import messagebox, ttk
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from modules.ia_engine import redigir_documento
from logger_config import get_logger

logger = get_logger(__name__)

class BilhetesModulo(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Tabs para "Novo Bilhete" e "Bilhetes Salvos"
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tab_novo = self.tabview.add("Novo Bilhete")
        self.tab_salvos = self.tabview.add("Bilhetes Salvos")
        
        self.setup_tab_novo()
        self.setup_tab_salvos()

    def setup_tab_novo(self):
        container = ctk.CTkFrame(self.tab_novo)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- Painel Esquerdo: Destinatários ---
        filtros_frame = ctk.CTkFrame(container, width=280)
        filtros_frame.pack(side="left", fill="both", padx=10, pady=10)
        
        ctk.CTkLabel(filtros_frame, text="1. Selecionar Turma", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        # Lista de opções para o Combobox
        self.opcoes_turmas = ["Todas as Turmas", "Apenas Matutino", "Apenas Vespertino"]
        self.combo_turmas = ctk.CTkComboBox(filtros_frame, values=self.opcoes_turmas, width=220)
        self.combo_turmas.pack(pady=10, padx=20)
        self.combo_turmas.set("Todas as Turmas")
        
        # Botão para atualizar a lista de turmas do banco
        btn_refresh = ctk.CTkButton(filtros_frame, text="🔄 Atualizar Lista", width=100, height=25, command=self.carregar_turmas)
        btn_refresh.pack(pady=5)

        # --- Painel Central: Conteúdo ---
        conteudo_frame = ctk.CTkFrame(container)
        conteudo_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(conteudo_frame, text="2. Conteúdo", font=("Helvetica", 14, "bold")).pack(pady=10)
        self.ent_assunto = ctk.CTkEntry(conteudo_frame, placeholder_text="Assunto...")
        self.ent_assunto.pack(fill="x", padx=20, pady=5)
        self.txt_mensagem = ctk.CTkTextbox(conteudo_frame, height=200)
        self.txt_mensagem.pack(fill="both", padx=20, pady=5, expand=True)
        
        btn_ia = ctk.CTkButton(conteudo_frame, text="🤖 Redigir com SofIA", fg_color="#27ae60", command=self.redigir_ia)
        btn_ia.pack(pady=5)
        
        btn_salvar = ctk.CTkButton(conteudo_frame, text="💾 Salvar Bilhete", fg_color="#2980b9", command=self.salvar_bilhete_db)
        btn_salvar.pack(pady=5)

        # --- Painel Direito: Extras ---
        extra_frame = ctk.CTkFrame(container, width=250)
        extra_frame.pack(side="left", fill="both", padx=10, pady=10)
        
        ctk.CTkLabel(extra_frame, text="3. Opções", font=("Helvetica", 14, "bold")).pack(pady=10)
        self.check_autorizacao = ctk.CTkCheckBox(extra_frame, text="Incluir Autorização")
        self.check_autorizacao.pack(anchor="w", padx=20, pady=5)
        self.check_assinatura = ctk.CTkCheckBox(extra_frame, text="Campo de Assinatura")
        self.check_assinatura.pack(anchor="w", padx=20, pady=5)
        self.ent_assinante = ctk.CTkEntry(extra_frame, placeholder_text="Assinado por (Ex: A Direção)")
        self.ent_assinante.pack(fill="x", padx=20, pady=10)
        
        btn_gerar = ctk.CTkButton(extra_frame, text="🖨️ GERAR PDF", height=40, font=("bold", 14), command=self.gerar_bilhetes_pdf)
        btn_gerar.pack(side="bottom", pady=20, fill="x", padx=10)

        # Inicializa a lista de turmas
        self.carregar_turmas()

    def carregar_turmas(self):
        try:
            novas_opcoes = ["Todas as Turmas", "Apenas Matutino", "Apenas Vespertino"]
            conn = get_connection()
            try:
                # Busca turmas da tabela 'turmas' que é onde o usuário cadastra
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome_completo, turno FROM turmas WHERE ativo=1 ORDER BY nome_completo")
                res = cursor.fetchall()
                # Dicionário para guardar o ID e o Turno para uso posterior se necessário
                self.dados_turmas_map = {}
                for r in res:
                    # r[1] é nome_completo, r[2] é turno
                    label = f"{r[1]} ({r[2]})"
                    if label not in novas_opcoes:
                        novas_opcoes.append(label)
                        self.dados_turmas_map[label] = {"id": r[0], "turno": r[2]}
            except Exception as e:
                print(f"Erro ao carregar turmas: {e}")
            finally:
                conn.close()
            
            self.combo_turmas.configure(values=novas_opcoes)
        except:
            pass

    def setup_tab_salvos(self):
        columns = ("id", "data", "assunto")
        self.tree = ttk.Treeview(self.tab_salvos, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("data", text="Data")
        self.tree.heading("assunto", text="Assunto")
        self.tree.column("id", width=50)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        btn_frame = ctk.CTkFrame(self.tab_salvos)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(btn_frame, text="🔄 Atualizar", command=self.carregar_bilhetes_salvos).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📂 Carregar no Editor", command=self.carregar_no_editor).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑️ Excluir", fg_color="#c0392b", command=self.excluir_bilhete).pack(side="left", padx=5)
        
        self.carregar_bilhetes_salvos()

    def redigir_ia(self):
        assunto = self.ent_assunto.get()
        if not assunto: return
        prompt = f"Escreva um bilhete escolar curto sobre: {assunto}. Seja direto."
        texto = redigir_documento('oficio', {"assunto": assunto, "destinatario": "Pais", "pauta": prompt})
        self.txt_mensagem.delete("1.0", "end")
        self.txt_mensagem.insert("1.0", texto)

    def salvar_bilhete_db(self):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO bilhetes (data, assunto, mensagem, assinante, autorizacao, assinatura) VALUES (?,?,?,?,?,?)",
                        (datetime.now().strftime("%d/%m/%Y"), self.ent_assunto.get(), self.txt_mensagem.get("1.0", "end"),
                         self.ent_assinante.get(), int(self.check_autorizacao.get()), int(self.check_assinatura.get())))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Bilhete salvo com sucesso!")
            self.carregar_bilhetes_salvos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def carregar_bilhetes_salvos(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            conn = get_connection()
            bilhetes = conn.execute(
                "SELECT id, data, assunto FROM bilhetes WHERE excluido IS NULL OR excluido = 0 ORDER BY id DESC"
            ).fetchall()
            for b in bilhetes: self.tree.insert("", "end", values=(b['id'], b['data'], b['assunto']))
            conn.close()
        except Exception as e:
            logger.error("Erro ao carregar bilhetes salvos: %s", e)

    def carregar_no_editor(self):
        sel = self.tree.selection()
        if not sel: return
        id_bilhete = self.tree.item(sel[0])['values'][0]
        try:
            conn = get_connection()
            b = conn.execute("SELECT * FROM bilhetes WHERE id=?", (id_bilhete,)).fetchone()
            conn.close()
            self.ent_assunto.delete(0, "end"); self.ent_assunto.insert(0, b['assunto'])
            self.txt_mensagem.delete("1.0", "end"); self.txt_mensagem.insert("1.0", b['mensagem'])
            self.ent_assinante.delete(0, "end"); self.ent_assinante.insert(0, b['assinante'])
            self.check_autorizacao.select() if b['autorizacao'] else self.check_autorizacao.deselect()
            self.check_assinatura.select() if b['assinatura'] else self.check_assinatura.deselect()
            self.tabview.set("Novo Bilhete")
        except Exception as e:
            logger.error("Erro ao carregar bilhete no editor: %s", e)

    def excluir_bilhete(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Excluir", "Deseja excluir este bilhete?"):
            id_bilhete = self.tree.item(sel[0])['values'][0]
            conn = get_connection(); conn.execute("UPDATE bilhetes SET excluido=1 WHERE id=?", (id_bilhete,)); conn.commit(); conn.close()
            self.carregar_bilhetes_salvos()

    def gerar_bilhetes_pdf(self):
        assunto = self.ent_assunto.get()
        mensagem = self.txt_mensagem.get("1.0", "end-1c")
        if not assunto or not mensagem: 
            messagebox.showwarning("Aviso", "Preencha assunto e mensagem.")
            return
        
        selecao = self.combo_turmas.get()
        assinante = self.ent_assinante.get()
        
        try:
            total = 0
            conn = get_connection()
            cursor = conn.cursor()
            
            try:
                if selecao == "Todas as Turmas":
                    cursor.execute("SELECT count(*) FROM alunos WHERE ativo=1 AND arquivado=0")
                    total = cursor.fetchone()[0]
                elif selecao == "Apenas Matutino":
                    # Busca turmas que são do matutino e conta seus alunos
                    cursor.execute("""
                        SELECT count(*) FROM alunos a
                        JOIN turmas t ON (a.turma_id = t.id OR a.turma_contraturno_id = t.id)
                        WHERE t.turno IN ('Manhã', 'Integral', 'Horário Diferenciado')
                        AND a.ativo=1 AND a.arquivado=0
                    """)
                    total = cursor.fetchone()[0]
                    
                    # Se der 0, tenta busca simples por texto no campo periodo do aluno
                    if total == 0:
                        cursor.execute("SELECT count(*) FROM alunos WHERE (periodo LIKE 'Manhã%' OR periodo LIKE 'Matutino%') AND ativo=1 AND arquivado=0")
                        total = cursor.fetchone()[0]
                        
                elif selecao == "Apenas Vespertino":
                    cursor.execute("""
                        SELECT count(*) FROM alunos a
                        JOIN turmas t ON (a.turma_id = t.id OR a.turma_contraturno_id = t.id)
                        WHERE t.turno IN ('Tarde')
                        AND a.ativo=1 AND a.arquivado=0
                    """)
                    total = cursor.fetchone()[0]
                    
                    if total == 0:
                        cursor.execute("SELECT count(*) FROM alunos WHERE (periodo LIKE 'Tarde%' OR periodo LIKE 'Vespertino%') AND ativo=1 AND arquivado=0")
                        total = cursor.fetchone()[0]
                else:
                    # É uma turma específica da combo: "Nome (Turno)"
                    turma_info = self.dados_turmas_map.get(selecao)
                    if turma_info:
                        t_id = turma_info['id']
                        cursor.execute("SELECT count(*) FROM alunos WHERE (turma_id=? OR turma_contraturno_id=?) AND ativo=1 AND arquivado=0", (t_id, t_id))
                        total = cursor.fetchone()[0]
                    else:
                        # Fallback por nome
                        nome_limpo = selecao.split(" (")[0]
                        cursor.execute("SELECT count(*) FROM alunos WHERE (turma=? OR periodo=?) AND ativo=1 AND arquivado=0", (nome_limpo, nome_limpo))
                        total = cursor.fetchone()[0]
            except Exception as e:
                print(f"Erro na contagem: {e}")
                total = 0
            finally:
                conn.close()
            
            if total == 0:
                if messagebox.askyesno("Info", f"Nenhum aluno encontrado para '{selecao}'. Gerar folha de teste (4 bilhetes)?"):
                    total = 4
                else:
                    return

            if messagebox.askyesno("Confirmar", f"Gerar para {total} alunos?"):
                from modules.pdf_engine import gerar_pdf_bilhetes
                dados = {
                    "assunto": assunto, 
                    "mensagem": mensagem, 
                    "autorizacao": int(self.check_autorizacao.get()), 
                    "assinatura": int(self.check_assinatura.get()), 
                    "assinante": assinante, 
                    "total": total
                }
                if gerar_pdf_bilhetes(dados):
                    messagebox.showinfo("Sucesso", "PDF Gerado na Área de Trabalho!")
                else:
                    messagebox.showerror("Erro", "Erro ao gerar PDF.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha: {e}")
