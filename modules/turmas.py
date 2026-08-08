"""
Módulo de Turmas — grade curricular + lista de alunos clicável abaixo.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte, maximizar, TURNOS, DIAS_SEMANA, SERIES_REGULARES
import pdf_utils

HORARIOS_MANHA = [
    ("Aula 1", "07:30", "08:20"),
    ("Aula 2", "08:20", "09:10"),
    ("Aula 3", "09:25", "10:30"),
    ("Aula 4", "10:30", "11:30"),
]
HORARIOS_TARDE = [
    ("Aula 1", "13:30", "14:20"),
    ("Aula 2", "14:20", "15:10"),
    ("Aula 3", "15:25", "16:20"),
    ("Aula 4", "16:20", "17:00"),
]
HORARIOS_DIFERENCIADO = [
    ("Aula 1", "07:30", "08:20"),
    ("Aula 2", "08:20", "09:10"),
    ("Aula 3", "09:25", "10:30"),
    ("Aula 4", "10:30", "11:30"),
]


def horarios_por_turno(turno):
    if "Tarde" in turno:    return HORARIOS_TARDE
    if "Diferenciado" in turno: return HORARIOS_DIFERENCIADO
    return HORARIOS_MANHA


class TurmasModule(ctk.CTkFrame):
    def __init__(self, parent, somente_consulta=False):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.somente_consulta     = somente_consulta
        self.turma_selecionada_id = None
        self._build_ui()
        self.carregar_turmas()

    # ─────────────────────────────────────────── UI
    def _build_ui(self):
        # Layout: painel esquerdo (lista de turmas) + painel direito (grade + alunos)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        # ═══ PAINEL ESQUERDO — Turmas ═══════════════════════════════════════
        left = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        left.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)
        left.rowconfigure(1, weight=1)

        header_l = ctk.CTkFrame(left, fg_color=CORES["card"], corner_radius=12)
        header_l.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(header_l, text="🏫 Turmas", font=fonte(18, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=15, pady=12)

        if not self.somente_consulta:
            bf = ctk.CTkFrame(header_l, fg_color="transparent")
            bf.pack(side="right", padx=8, pady=8)
            ctk.CTkButton(bf, text="+ Nova", fg_color=CORES["acento"],
                          hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                          command=self.nova_turma, width=80).pack(side="left", padx=3)
            ctk.CTkButton(bf, text="✏", fg_color=CORES["primaria_clara"],
                          text_color=CORES["texto_claro"],
                          command=self.editar_turma, width=36).pack(side="left", padx=3)
            ctk.CTkButton(bf, text="🗑", fg_color=CORES["perigo"],
                          hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                          command=self.excluir_turma, width=36).pack(side="left", padx=3)

        # Filtro turno
        filtro_f = ctk.CTkFrame(left, fg_color=CORES["card"], corner_radius=8)
        filtro_f.grid(row=0, column=0, sticky="ew", pady=(62, 0))
        ctk.CTkLabel(filtro_f, text="Turno:", text_color=CORES["subtexto"]).pack(side="left", padx=10, pady=6)
        self.filtro_turno = ctk.StringVar(value="Todos")
        ctk.CTkOptionMenu(filtro_f, values=["Todos", "Manhã", "Tarde", "Integral", "Horário Diferenciado"],
                          variable=self.filtro_turno,
                          command=lambda _: self.carregar_turmas(), width=180).pack(side="left", padx=5, pady=6)

        tf = ctk.CTkFrame(left, fg_color=CORES["card"], corner_radius=12)
        tf.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)

        cols = ("nome", "turno", "tipo", "alunos")
        self.tree_turmas = ttk.Treeview(tf, columns=cols, show="headings")
        for col, (txt, w, anc) in {
            "nome":   ("Turma",  140, "w"),
            "turno":  ("Turno",  90,  "center"),
            "tipo":   ("Tipo",   80,  "center"),
            "alunos": ("Alunos", 55,  "center"),
        }.items():
            self.tree_turmas.heading(col, text=txt, anchor="w")
            self.tree_turmas.column(col, width=w, anchor=anc)

        self.tree_turmas.tag_configure("regular",    foreground=CORES["acento"])
        self.tree_turmas.tag_configure("contraturno",foreground=CORES["dourado"])

        scr_t = ttk.Scrollbar(tf, orient="vertical", command=self.tree_turmas.yview)
        self.tree_turmas.configure(yscrollcommand=scr_t.set)
        self.tree_turmas.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
        scr_t.grid(row=0, column=1, sticky="ns", pady=5)
        self.tree_turmas.bind("<<TreeviewSelect>>", self.ao_selecionar_turma)

        # ═══ PAINEL DIREITO — Grade + Alunos ════════════════════════════════
        right = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        right.rowconfigure(1, weight=1)   # grade ocupa 60%
        right.rowconfigure(2, weight=1)   # alunos ocupa 40%
        right.columnconfigure(0, weight=1)

        # ── Cabeçalho grade
        header_r = ctk.CTkFrame(right, fg_color=CORES["card"], corner_radius=12)
        header_r.grid(row=0, column=0, sticky="ew")
        self.label_turma_sel = ctk.CTkLabel(
            header_r, text="📅 Grade — selecione uma turma",
            font=fonte(15, "bold"), text_color=CORES["dourado"])
        self.label_turma_sel.pack(side="left", padx=15, pady=12)

        if not self.somente_consulta:
            bg = ctk.CTkFrame(header_r, fg_color="transparent")
            bg.pack(side="right", padx=8, pady=8)
            ctk.CTkButton(bg, text="+ Aula", fg_color=CORES["acento"],
                          hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                          command=self.adicionar_aula, width=80).pack(side="left", padx=3)
            ctk.CTkButton(bg, text="🗑 Remover", fg_color=CORES["perigo"],
                          hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                          command=self.remover_aula, width=100).pack(side="left", padx=3)
        ctk.CTkButton(header_r, text="📄 PDF Grade", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["primaria"],
                      font=fonte(11, "bold"),
                      command=self.pdf_grade, width=110).pack(side="right", padx=8, pady=8)

        # ── Notebook de dias (grade)
        grade_frame = ctk.CTkFrame(right, fg_color=CORES["card"], corner_radius=12)
        grade_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 4))
        grade_frame.rowconfigure(0, weight=1)
        grade_frame.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(grade_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.frames_dias = {}
        self.trees_dias  = {}
        for dia in DIAS_SEMANA:
            fd = ctk.CTkFrame(self.notebook, fg_color=CORES["card"])
            self.notebook.add(fd, text=dia[:3])
            cols_g = ("aula", "horario", "disciplina", "professor")
            tg = ttk.Treeview(fd, columns=cols_g, show="headings", height=5)
            for col, (txt, w) in {
                "aula":       ("Aula",       70),
                "horario":    ("Horário",   130),
                "disciplina": ("Disciplina", 200),
                "professor":  ("Professor",  220),
            }.items():
                tg.heading(col, text=txt, anchor="w")
                tg.column(col, width=w, anchor="w")
            tg.pack(fill="both", expand=True, padx=5, pady=5)
            tg.tag_configure("preenchida", foreground=CORES["acento"])
            tg.tag_configure("vazio",      foreground=CORES["subtexto"])
            self.frames_dias[dia] = fd
            self.trees_dias[dia]  = tg

        # Legenda de horários
        self.label_legenda = ctk.CTkLabel(grade_frame, text="",
                                           text_color=CORES["subtexto"], font=fonte(11))
        self.label_legenda.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))

        # ── Painel de alunos da turma
        alunos_header = ctk.CTkFrame(right, fg_color=CORES["card"], corner_radius=12)
        alunos_header.grid(row=2, column=0, sticky="nsew", pady=(4, 0))
        alunos_header.rowconfigure(1, weight=1)
        alunos_header.columnconfigure(0, weight=1)

        topo_alunos = ctk.CTkFrame(alunos_header, fg_color="transparent")
        topo_alunos.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        self.label_alunos_titulo = ctk.CTkLabel(
            topo_alunos, text="👨‍🎓 Alunos da Turma — selecione uma turma",
            font=fonte(13, "bold"), text_color=CORES["dourado"])
        self.label_alunos_titulo.pack(side="left")
        ctk.CTkLabel(topo_alunos,
                     text="Dê duplo clique no nome para abrir a ficha cadastral",
                     font=fonte(10), text_color=CORES["subtexto"]).pack(side="right")

        cols_a = ("num", "nome", "sexo", "cgm", "nascimento")
        self.tree_alunos = ttk.Treeview(
            alunos_header, columns=cols_a, show="headings", height=8)
        for col, (txt, w, anc) in {
            "num":        ("Nº",          40,  "center"),
            "nome":       ("Nome",        300, "w"),
            "sexo":       ("Sexo",        70,  "center"),
            "cgm":        ("CGM",         110, "w"),
            "nascimento": ("Nascimento",  100, "center"),
        }.items():
            self.tree_alunos.heading(col, text=txt, anchor="w")
            self.tree_alunos.column(col, width=w, anchor=anc)

        self.tree_alunos.tag_configure("masc", foreground=CORES["acento"])
        self.tree_alunos.tag_configure("fem",  foreground="#c0392b")
        self.tree_alunos.tag_configure("outro",foreground=CORES["subtexto"])

        scr_a = ttk.Scrollbar(alunos_header, orient="vertical", command=self.tree_alunos.yview)
        self.tree_alunos.configure(yscrollcommand=scr_a.set)
        self.tree_alunos.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=(0, 5))
        scr_a.grid(row=1, column=1, sticky="ns", pady=(0, 5), padx=(0, 5))

        self.tree_alunos.bind("<Double-1>", lambda e: self._abrir_ficha_aluno())

    # ─────────────────────────────────────────── DADOS
    def carregar_turmas(self):
        for item in self.tree_turmas.get_children():
            self.tree_turmas.delete(item)
        filtro = self.filtro_turno.get()
        conn   = get_connection()
        q = """SELECT t.id, t.nome_completo, t.turno, t.tipo,
                      COUNT(a.id) alunos
               FROM turmas t
               LEFT JOIN alunos a ON (a.turma_id=t.id OR a.turma_contraturno_id=t.id) AND a.ativo=1 AND a.arquivado=0
               WHERE t.ativo=1"""
        params = []
        if filtro != "Todos":
            q += " AND t.turno=?"
            params.append(filtro)
        q += " GROUP BY t.id ORDER BY t.nome_completo"
        for t in conn.execute(q, params).fetchall():
            tipo_txt = "Contraturno" if t["tipo"] == "contraturno" else "Regular"
            tag      = "contraturno" if t["tipo"] == "contraturno" else "regular"
            self.tree_turmas.insert("", "end", iid=t["id"],
                                    values=(t["nome_completo"], t["turno"],
                                            tipo_txt, t["alunos"]),
                                    tags=(tag,))
        conn.close()

    def ao_selecionar_turma(self, event=None):
        sel = self.tree_turmas.selection()
        if not sel: return
        self.turma_selecionada_id = int(sel[0])
        conn  = get_connection()
        turma = conn.execute("SELECT * FROM turmas WHERE id=?", (self.turma_selecionada_id,)).fetchone()
        conn.close()
        if not turma: return
        self.label_turma_sel.configure(text=f"📅 {turma['nome_completo']} — {turma['turno']}")
        slots = horarios_por_turno(turma["turno"])
        leg   = "  |  ".join([f"Aula {i+1}: {s[1]}–{s[2]}" for i, s in enumerate(slots)])
        self.label_legenda.configure(text=f"🕐 {leg}")
        self.carregar_grade(self.turma_selecionada_id)
        self.carregar_alunos_turma(self.turma_selecionada_id, turma["nome_completo"])

    def carregar_grade(self, turma_id):
        for dia in DIAS_SEMANA:
            for item in self.trees_dias[dia].get_children():
                self.trees_dias[dia].delete(item)

        conn  = get_connection()
        turma = conn.execute("SELECT turno FROM turmas WHERE id=?",
                             (turma_id,)).fetchone()
        if not turma:
            conn.close()
            return

        slots = horarios_por_turno(turma["turno"])

        rows = conn.execute("""
            SELECT h.id, h.dia_semana, h.horario_inicio, h.horario_fim,
                   d.nome disciplina, p.nome professor
            FROM horarios h
            JOIN disciplinas d ON h.disciplina_id = d.id
            LEFT JOIN professores p ON d.professor_id = p.id
            WHERE h.turma_id = ?
            ORDER BY h.dia_semana, h.horario_inicio
        """, (turma_id,)).fetchall()
        conn.close()

        from collections import defaultdict
        por_dia = defaultdict(list)
        for r in rows:
            if r["dia_semana"] in DIAS_SEMANA:
                por_dia[r["dia_semana"]].append(r)

        # Contador global para iids únicos dos slots vazios
        # Evita qualquer conflito entre dias/slots
        contador_vazio = 0

        for dia in DIAS_SEMANA:
            tree  = self.trees_dias[dia]
            aulas = por_dia.get(dia, [])

            # Mapear horário_inicio → registro real
            mapa_horario = {a["horario_inicio"]: a for a in aulas}

            for i, (nome_slot, ini, fim) in enumerate(slots):
                aula = mapa_horario.get(ini)
                if aula:
                    # Slot preenchido — iid = id real do banco (inteiro)
                    tree.insert("", "end",
                                iid=f"h{aula['id']}",
                                values=(nome_slot,
                                        f"{aula['horario_inicio']}–{aula['horario_fim']}",
                                        aula["disciplina"],
                                        aula["professor"] or "-"),
                                tags=("preenchida",))
                else:
                    # Slot vazio — iid único garantido
                    contador_vazio += 1
                    tree.insert("", "end",
                                iid=f"vz{contador_vazio}",
                                values=(nome_slot, f"{ini}–{fim}", "(Vaga)", "-"),
                                tags=("vazio",))

    def carregar_alunos_turma(self, turma_id, turma_nome):
        for item in self.tree_alunos.get_children():
            self.tree_alunos.delete(item)
        self.label_alunos_titulo.configure(
            text=f"👨‍🎓 Alunos — {turma_nome}")
        conn   = get_connection()
        alunos = conn.execute("""
            SELECT id, nome, sexo, cgm, data_nascimento
            FROM alunos WHERE (turma_id=? OR turma_contraturno_id=?) AND ativo=1 AND arquivado=0 ORDER BY nome
        """, (turma_id, turma_id)).fetchall()
        conn.close()
        from tema import data_bd_para_tela
        for i, a in enumerate(alunos, 1):
            sx  = a["sexo"] or ""
            tag = "masc" if sx == "Masculino" else ("fem" if sx == "Feminino" else "outro")
            self.tree_alunos.insert("", "end", iid=a["id"],
                                    values=(i, a["nome"], sx or "-",
                                            a["cgm"] or "-",
                                            data_bd_para_tela(a["data_nascimento"]) or "-"),
                                    tags=(tag,))

    def _abrir_ficha_aluno(self):
        sel = self.tree_alunos.selection()
        if not sel: return
        aluno_id = int(sel[0])
        from modules.alunos import AlunosModule
        # Criar instância temporária apenas para abrir o form
        mod = AlunosModule.__new__(AlunosModule)
        mod.somente_consulta = self.somente_consulta
        mod.winfo_toplevel   = self.winfo_toplevel
        mod.carregar_alunos  = lambda: self.carregar_alunos_turma(
            self.turma_selecionada_id,
            self.label_alunos_titulo.cget("text").replace("👨‍🎓 Alunos — ", ""))
        mod._abrir_form(aluno_id, somente_visualizar=self.somente_consulta)

    # ─────────────────────────────────────────── TURMAS CRUD
    def nova_turma(self):   self._form_turma(None)
    def editar_turma(self):
        sel = self.tree_turmas.selection()
        if not sel: messagebox.showwarning("Atenção", "Selecione uma turma."); return
        self._form_turma(int(sel[0]))

    def excluir_turma(self):
        sel = self.tree_turmas.selection()
        if not sel: messagebox.showwarning("Atenção", "Selecione uma turma."); return
        if messagebox.askyesno("Confirmar", "Desativar esta turma?"):
            conn = get_connection()
            conn.execute("UPDATE turmas SET ativo=0 WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close()
            self.turma_selecionada_id = None
            self.carregar_turmas()

    def _form_turma(self, turma_id):
        form = ctk.CTkToplevel(self.winfo_toplevel())
        form.title("Nova Turma" if not turma_id else "Editar Turma")
        form.geometry("520x560")
        form.grab_set()
        form.configure(fg_color=CORES["fundo"])

        conn  = get_connection()
        profs = conn.execute(
            "SELECT id, nome FROM professores WHERE ativo=1 AND arquivado=0 ORDER BY nome"
        ).fetchall()
        conn.close()
        profs_dict = {"(Nenhum)": None}
        profs_dict.update({p["nome"]: p["id"] for p in profs})

        dados = {}
        if turma_id:
            conn  = get_connection()
            dados = dict(conn.execute(
                "SELECT * FROM turmas WHERE id=?", (turma_id,)).fetchone() or {})
            conn.close()

        # ── Cabeçalho fixo no topo ────────────────────────────────────────
        topo = ctk.CTkFrame(form, fg_color=CORES["primaria"],
                             corner_radius=0, height=50)
        topo.pack(fill="x", side="top")
        topo.pack_propagate(False)
        ctk.CTkLabel(topo, text="🏫 Cadastro de Turma",
                     font=fonte(14, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        # ── Barra de botões fixo no bottom ────────────────────────────────
        bb = ctk.CTkFrame(form, fg_color=CORES["card"],
                          corner_radius=0, height=55)
        bb.pack(fill="x", side="bottom")
        bb.pack_propagate(False)

        # ── Área de scroll no meio ────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(form, fg_color=CORES["fundo"])
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # ── Campos usando pack ─────────────────────────────────────────────
        def campo_entry(label, key, default=""):
            ctk.CTkLabel(scroll, text=label, font=fonte(12, "bold"),
                         text_color=CORES["subtexto"]).pack(
                anchor="w", padx=5, pady=(10, 2))
            e = ctk.CTkEntry(scroll, width=460)
            e.insert(0, dados.get(key, default) or "")
            e.pack(anchor="w", padx=5, pady=(0, 4))
            return e

        def campo_opcao(label, key, opcoes):
            ctk.CTkLabel(scroll, text=label, font=fonte(12, "bold"),
                         text_color=CORES["subtexto"]).pack(
                anchor="w", padx=5, pady=(10, 2))
            var = ctk.StringVar(
                value=dados.get(key, "") or (opcoes[0] if opcoes else ""))
            ctk.CTkOptionMenu(scroll, values=opcoes, variable=var,
                               width=460).pack(anchor="w", padx=5, pady=(0, 4))
            return var

        nome_e  = campo_entry("Nome Completo da Turma *", "nome_completo")
        serie_v = campo_opcao("Série / Ano", "serie",
                               SERIES_REGULARES + ["Sala de Reforço",
                                                   "Sala de Recursos Multifuncionais"])
        letra_e = campo_entry("Letra  (A, B, C...)", "letra")
        turno_v = campo_opcao("Turno *", "turno", TURNOS)
        tipo_v  = campo_opcao("Tipo", "tipo", ["regular", "contraturno"])
        sala_e  = campo_entry("Sala", "sala")
        ano_e   = campo_entry("Ano Letivo", "ano_letivo")

        # Professor responsável
        ctk.CTkLabel(scroll, text="Professor Responsável", font=fonte(12, "bold"),
                     text_color=CORES["subtexto"]).pack(
            anchor="w", padx=5, pady=(10, 2))
        prof_atual = "(Nenhum)"
        if dados.get("professor_id"):
            conn = get_connection()
            p = conn.execute("SELECT nome FROM professores WHERE id=?",
                             (dados["professor_id"],)).fetchone()
            conn.close()
            if p: prof_atual = p["nome"]
        prof_var = ctk.StringVar(value=prof_atual)
        ctk.CTkOptionMenu(scroll, values=list(profs_dict.keys()),
                          variable=prof_var, width=460).pack(
            anchor="w", padx=5, pady=(0, 4))

        # ── Salvar ────────────────────────────────────────────────────────
        def salvar():
            nome_c = nome_e.get().strip()
            if not nome_c:
                # Gerar nome automático a partir de série + letra
                serie = serie_v.get()
                letra = letra_e.get().strip()
                nome_c = f"{serie} {letra}".strip() if letra else serie
            if not nome_c:
                messagebox.showerror("Erro", "Informe o nome da turma!", parent=form)
                return

            d = {
                "nome_completo": nome_c,
                "serie":         serie_v.get(),
                "letra":         letra_e.get().strip(),
                "turno":         turno_v.get(),
                "tipo":          tipo_v.get(),
                "sala":          sala_e.get().strip(),
                "ano_letivo":    ano_e.get().strip(),
                "professor_id":  profs_dict.get(prof_var.get()),
            }
            conn = get_connection()
            try:
                if turma_id:
                    conn.execute("""
                        UPDATE turmas
                        SET nome_completo=:nome_completo, serie=:serie,
                            letra=:letra, turno=:turno, tipo=:tipo,
                            sala=:sala, ano_letivo=:ano_letivo,
                            professor_id=:professor_id
                        WHERE id=""" + str(turma_id), d)
                else:
                    conn.execute("""
                        INSERT INTO turmas
                            (nome_completo, serie, letra, turno, tipo,
                             sala, ano_letivo, professor_id, ativo)
                        VALUES
                            (:nome_completo, :serie, :letra, :turno, :tipo,
                             :sala, :ano_letivo, :professor_id, 1)""", d)
                conn.commit()
                messagebox.showinfo("Sucesso", "Turma salva com sucesso!", parent=form)
                form.destroy()
                self.carregar_turmas()
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=form)
            finally:
                conn.close()

        # ── Botões na barra inferior ──────────────────────────────────────
        ctk.CTkButton(bb, text="✖ Fechar",
                      fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"],
                      text_color=CORES["texto_claro"],
                      command=form.destroy,
                      width=110, height=36).pack(side="right", padx=10, pady=10)
        ctk.CTkButton(bb, text="💾 Salvar",
                      fg_color=CORES["acento"], hover_color=CORES["acento_hover"],
                      text_color=CORES["texto_claro"], font=fonte(13, "bold"),
                      command=salvar,
                      width=130, height=36).pack(side="right", padx=8, pady=10)

    # ─────────────────────────────────────────── GRADE CRUD
    def adicionar_aula(self):
        if not self.turma_selecionada_id:
            messagebox.showwarning("Atenção", "Selecione uma turma primeiro.")
            return
        conn  = get_connection()
        turma = conn.execute("SELECT * FROM turmas WHERE id=?",
                             (self.turma_selecionada_id,)).fetchone()
        discs = conn.execute(
            "SELECT id, nome FROM disciplinas WHERE turma_id=? ORDER BY nome",
            (self.turma_selecionada_id,)).fetchall()
        conn.close()

        if not discs:
            messagebox.showwarning("Atenção",
                "Esta turma não tem disciplinas.\n"
                "Cadastre-as na aba Disciplinas primeiro.")
            return

        slots      = horarios_por_turno(turma["turno"])
        discs_dict = {d["nome"]: d["id"] for d in discs}

        form = ctk.CTkToplevel(self.winfo_toplevel())
        form.title("Adicionar Aula")
        form.geometry("460x380")
        form.grab_set()
        form.configure(fg_color=CORES["fundo"])

        # Cabeçalho
        topo = ctk.CTkFrame(form, fg_color=CORES["primaria"],
                             corner_radius=0, height=50)
        topo.pack(fill="x", side="top")
        topo.pack_propagate(False)
        ctk.CTkLabel(topo,
                     text=f"📅 Adicionar Aula — {turma['nome_completo']}",
                     font=fonte(13, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        # Barra de botões (fica no bottom antes do frame central)
        bb = ctk.CTkFrame(form, fg_color=CORES["card"],
                          corner_radius=0, height=55)
        bb.pack(fill="x", side="bottom")
        bb.pack_propagate(False)

        # Frame central com os campos — usa pack para tudo
        frame = ctk.CTkFrame(form, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True, padx=25, pady=15)

        # ── Dia da Semana ──────────────────────────────────────────────────
        ctk.CTkLabel(frame, text="Dia da Semana",
                     font=fonte(12, "bold"),
                     text_color=CORES["subtexto"]).pack(anchor="w", pady=(0, 3))
        dia_var = ctk.StringVar(value=DIAS_SEMANA[0])
        ctk.CTkOptionMenu(frame, values=DIAS_SEMANA,
                          variable=dia_var, width=400).pack(anchor="w", pady=(0, 14))

        # ── Slot de Aula ───────────────────────────────────────────────────
        ctk.CTkLabel(frame, text="Número da Aula (horário)",
                     font=fonte(12, "bold"),
                     text_color=CORES["subtexto"]).pack(anchor="w", pady=(0, 3))
        slot_nomes = [f"{s[0]} ({s[1]}–{s[2]})" for s in slots]
        slot_var   = ctk.StringVar(value=slot_nomes[0])
        ctk.CTkOptionMenu(frame, values=slot_nomes,
                          variable=slot_var, width=400).pack(anchor="w", pady=(0, 14))

        # ── Disciplina ─────────────────────────────────────────────────────
        ctk.CTkLabel(frame, text="Disciplina",
                     font=fonte(12, "bold"),
                     text_color=CORES["subtexto"]).pack(anchor="w", pady=(0, 3))
        disc_var = ctk.StringVar(value=list(discs_dict.keys())[0])
        ctk.CTkOptionMenu(frame, values=list(discs_dict.keys()),
                          variable=disc_var, width=400).pack(anchor="w", pady=(0, 14))

        # ── Salvar ─────────────────────────────────────────────────────────
        def salvar_aula():
            dia      = dia_var.get()
            slot_idx = slot_nomes.index(slot_var.get())
            slot     = slots[slot_idx]
            disc_id  = discs_dict[disc_var.get()]

            conn = get_connection()
            existente = conn.execute(
                "SELECT id FROM horarios "
                "WHERE turma_id=? AND dia_semana=? AND horario_inicio=?",
                (self.turma_selecionada_id, dia, slot[1])).fetchone()

            if existente:
                if not messagebox.askyesno(
                        "Conflito",
                        f"Já existe uma aula no {slot[0]} de {dia}.\n"
                        f"Deseja substituir?",
                        parent=form):
                    conn.close()
                    return
                conn.execute("DELETE FROM horarios WHERE id=?",
                             (existente["id"],))

            conn.execute(
                "INSERT INTO horarios "
                "(turma_id, disciplina_id, dia_semana, horario_inicio, horario_fim) "
                "VALUES (?, ?, ?, ?, ?)",
                (self.turma_selecionada_id, disc_id, dia, slot[1], slot[2]))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Aula adicionada com sucesso!", parent=form)
            form.destroy()
            self.carregar_grade(self.turma_selecionada_id)

        ctk.CTkButton(bb, text="✖ Cancelar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"],
                      text_color=CORES["texto_claro"],
                      command=form.destroy,
                      width=110, height=36).pack(side="right", padx=10, pady=10)
        ctk.CTkButton(bb, text="💾 Adicionar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"],
                      text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"),
                      command=salvar_aula,
                      width=140, height=36).pack(side="right", padx=5, pady=10)

    def remover_aula(self):
        try:
            dia_atual = DIAS_SEMANA[self.notebook.index("current")]
        except Exception:
            messagebox.showwarning("Atenção", "Selecione uma aba de dia da semana.")
            return
        tree = self.trees_dias[dia_atual]
        sel  = tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione uma aula para remover.")
            return
        iid = sel[0]
        # Slots vazios começam com "vz", slots reais começam com "h"
        if str(iid).startswith("vz"):
            messagebox.showinfo("Info", "Este slot já está vazio.")
            return
        if messagebox.askyesno("Confirmar", "Remover esta aula da grade?"):
            # iid real = "h{id_do_banco}"
            horario_id = int(str(iid).replace("h", ""))
            conn = get_connection()
            conn.execute("DELETE FROM horarios WHERE id=?", (horario_id,))
            conn.commit()
            conn.close()
            self.carregar_grade(self.turma_selecionada_id)

    def pdf_grade(self):
        if not self.turma_selecionada_id:
            messagebox.showwarning("Atenção", "Selecione uma turma."); return
        conn  = get_connection()
        turma = conn.execute("SELECT * FROM turmas WHERE id=?", (self.turma_selecionada_id,)).fetchone()
        rows  = conn.execute("""
            SELECT h.dia_semana, h.horario_inicio, h.horario_fim,
                   d.nome disciplina, p.nome professor
            FROM horarios h JOIN disciplinas d ON h.disciplina_id=d.id
            LEFT JOIN professores p ON d.professor_id=p.id
            WHERE h.turma_id=? ORDER BY h.dia_semana, h.horario_inicio
        """, (self.turma_selecionada_id,)).fetchall()
        conn.close()
        from collections import defaultdict
        por_dia = defaultdict(list)
        for r in rows: por_dia[r["dia_semana"]].append(r)
        slots  = horarios_por_turno(turma["turno"])
        linhas = [["Aula / Horário"] + DIAS_SEMANA]
        for i, (nome_slot, ini, fim) in enumerate(slots):
            linha = [f"{nome_slot}\n{ini}–{fim}"]
            for dia in DIAS_SEMANA:
                aulas = por_dia.get(dia, [])
                if i < len(aulas):
                    a = aulas[i]
                    linha.append(f"{a['disciplina']}\n{a['professor'] or '-'}")
                else:
                    linha.append("—")
            linhas.append(linha)
        blocos = [
            ("titulo", f"Turma: {turma['nome_completo']}  |  Turno: {turma['turno']}"),
            ("tabela", linhas),
        ]
        pdf_utils.salvar_pdf_como(
            f"Grade Curricular — {turma['nome_completo']}", blocos,
            f"Grade_{turma['nome_completo'].replace(' ','_')}.pdf")
