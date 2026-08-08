import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte

class DisciplinasModule(ctk.CTkFrame):
    def __init__(self, parent, somente_consulta=False):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.somente_consulta = somente_consulta
        self._build_ui()
        self.carregar()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="📚 Disciplinas", font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        if not self.somente_consulta:
            btn_f = ctk.CTkFrame(header, fg_color="transparent")
            btn_f.pack(side="right", padx=15, pady=10)
            ctk.CTkButton(btn_f, text="+ Nova Disciplina", fg_color=CORES["acento"],
                          hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                          command=lambda: self._form(None), width=150).pack(side="left", padx=5)
            ctk.CTkButton(btn_f, text="✏ Editar", fg_color=CORES["primaria_clara"],
                          text_color=CORES["texto_claro"], command=self.editar, width=100).pack(side="left", padx=5)
            ctk.CTkButton(btn_f, text="🗑 Excluir", fg_color=CORES["perigo"],
                          hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                          command=self.excluir, width=100).pack(side="left", padx=5)

        filtro = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        filtro.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(filtro, text="Filtrar por Turma:", text_color=CORES["subtexto"]).pack(side="left", padx=15, pady=10)
        self.turma_var = ctk.StringVar(value="Todas")
        self.turma_combo = ctk.CTkOptionMenu(filtro, variable=self.turma_var,
                                              command=lambda _: self.carregar(), width=200, values=["Todas"])
        self.turma_combo.pack(side="left", padx=5, pady=10)

        tabela_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        tabela_f.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("nome", "turma", "professor", "carga")
        self.tree = ttk.Treeview(tabela_f, columns=cols, show="headings", height=20)
        for col, (txt, w) in {"nome": ("Disciplina", 220), "turma": ("Turma", 160),
                               "professor": ("Professor", 240), "carga": ("Carga (h)", 100)}.items():
            self.tree.heading(col, text=txt, anchor="w")
            self.tree.column(col, width=w, anchor="w")
        scroll = ttk.Scrollbar(tabela_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scroll.pack(side="right", fill="y", pady=5)
        self.tree.bind("<Double-1>", lambda e: self.editar())

    def carregar(self):
        conn = get_connection()
        turmas = conn.execute("SELECT id, nome_completo FROM turmas WHERE ativo=1 ORDER BY nome_completo").fetchall()
        self.turmas_dict = {"Todas": None}
        self.turmas_dict.update({t["nome_completo"]: t["id"] for t in turmas})
        self.turma_combo.configure(values=list(self.turmas_dict.keys()))

        for item in self.tree.get_children():
            self.tree.delete(item)
        turma_id = self.turmas_dict.get(self.turma_var.get())
        query = """SELECT d.id, d.nome, t.nome_completo as turma, p.nome as professor, d.carga_horaria
                   FROM disciplinas d LEFT JOIN turmas t ON d.turma_id=t.id
                   LEFT JOIN professores p ON d.professor_id=p.id
                   WHERE (d.excluido IS NULL OR d.excluido = 0)"""
        params = []
        if turma_id:
            query += " AND d.turma_id=?"
            params.append(turma_id)
        query += " ORDER BY t.nome_completo, d.nome"
        for r in conn.execute(query, params).fetchall():
            self.tree.insert("", "end", iid=r["id"],
                             values=(r["nome"], r["turma"] or "-", r["professor"] or "-",
                                     f"{r['carga_horaria']}h" if r["carga_horaria"] else "-"))
        conn.close()

    def editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione uma disciplina.")
            return
        self._form(int(sel[0]))

    def excluir(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione uma disciplina.")
            return
        if messagebox.askyesno("Confirmar", "Excluir esta disciplina? Notas e horários vinculados serão perdidos."):
            conn = get_connection()
            conn.execute("UPDATE disciplinas SET excluido=1 WHERE id=?", (int(sel[0]),))
            conn.commit()
            conn.close()
            self.carregar()

    def _form(self, disc_id):
        form = ctk.CTkToplevel(self.winfo_toplevel())
        form.title("Nova Disciplina" if not disc_id else "Editar Disciplina")
        form.geometry("500x400")
        form.grab_set()
        form.configure(fg_color=CORES["fundo"])

        conn = get_connection()
        turmas = conn.execute("SELECT id, nome_completo FROM turmas WHERE ativo=1 ORDER BY nome_completo").fetchall()
        profs = conn.execute("SELECT id, nome FROM professores WHERE ativo=1 AND arquivado=0 ORDER BY nome").fetchall()
        conn.close()

        turmas_dict = {t["nome_completo"]: t["id"] for t in turmas}
        profs_dict = {"(Nenhum)": None}
        profs_dict.update({p["nome"]: p["id"] for p in profs})

        dados = {}
        if disc_id:
            conn = get_connection()
            dados = dict(conn.execute("SELECT * FROM disciplinas WHERE id=?", (disc_id,)).fetchone() or {})
            conn.close()

        topo = ctk.CTkFrame(form, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="📚 Cadastro de Disciplina", font=fonte(14, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        frame = ctk.CTkFrame(form, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True, padx=20, pady=15)

        def lbl(t, r):
            ctk.CTkLabel(frame, text=t, font=fonte(13, "bold"),
                         text_color=CORES["subtexto"]).grid(row=r, column=0, sticky="w", padx=5, pady=(8, 0))

        lbl("Nome da Disciplina *", 0)
        nome_e = ctk.CTkEntry(frame, width=420)
        nome_e.insert(0, dados.get("nome", "") or "")
        nome_e.grid(row=1, column=0, padx=5, pady=(0, 4), sticky="ew")

        lbl("Carga Horária (h/aula)", 2)
        carga_e = ctk.CTkEntry(frame, width=420)
        carga_e.insert(0, str(dados.get("carga_horaria", "") or ""))
        carga_e.grid(row=3, column=0, padx=5, pady=(0, 4), sticky="ew")

        lbl("Turma *", 4)
        turma_atual = ""
        if dados.get("turma_id"):
            conn = get_connection()
            t = conn.execute("SELECT nome_completo FROM turmas WHERE id=?", (dados["turma_id"],)).fetchone()
            conn.close()
            if t: turma_atual = t["nome_completo"]
        turma_var = ctk.StringVar(value=turma_atual or (list(turmas_dict.keys())[0] if turmas_dict else ""))
        ctk.CTkOptionMenu(frame, values=list(turmas_dict.keys()) if turmas_dict else ["(Nenhuma)"],
                          variable=turma_var, width=420).grid(row=5, column=0, padx=5, pady=(0, 4), sticky="ew")

        lbl("Professor", 6)
        prof_atual = "(Nenhum)"
        if dados.get("professor_id"):
            conn = get_connection()
            p = conn.execute("SELECT nome FROM professores WHERE id=?", (dados["professor_id"],)).fetchone()
            conn.close()
            if p: prof_atual = p["nome"]
        prof_var = ctk.StringVar(value=prof_atual)
        ctk.CTkOptionMenu(frame, values=list(profs_dict.keys()), variable=prof_var,
                          width=420).grid(row=7, column=0, padx=5, pady=(0, 4), sticky="ew")

        def salvar():
            nome = nome_e.get().strip()
            if not nome:
                messagebox.showerror("Erro", "Nome é obrigatório!", parent=form)
                return
            turma_id_sel = turmas_dict.get(turma_var.get())
            prof_id_sel = profs_dict.get(prof_var.get())
            try:
                carga = int(carga_e.get()) if carga_e.get().strip() else None
            except ValueError:
                carga = None
            conn = get_connection()
            try:
                if disc_id:
                    conn.execute("UPDATE disciplinas SET nome=?, carga_horaria=?, turma_id=?, professor_id=? WHERE id=?",
                                 (nome, carga, turma_id_sel, prof_id_sel, disc_id))
                else:
                    conn.execute("INSERT INTO disciplinas (nome, carga_horaria, turma_id, professor_id) VALUES (?,?,?,?)",
                                 (nome, carga, turma_id_sel, prof_id_sel))
                conn.commit()
                messagebox.showinfo("Sucesso", "Disciplina salva!", parent=form)
                form.destroy()
                self.carregar()
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=form)
            finally:
                conn.close()

        btn_bar = ctk.CTkFrame(form, fg_color=CORES["card"], corner_radius=0, height=55)
        btn_bar.pack(fill="x", side="bottom")
        ctk.CTkButton(btn_bar, text="✖ Fechar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=form.destroy, width=110, height=36).pack(side="right", padx=10, pady=10)
        ctk.CTkButton(btn_bar, text="💾 Salvar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=salvar, width=130, height=36).pack(side="right", padx=10, pady=10)
