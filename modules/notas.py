"""
Módulo de Notas e Boletins.
Regras:
  - Se o professor lança as 2 notas do bimestre: Total bimestral = MÉDIA (nota_1 + nota_2) / 2
  - Se o professor lança só 1 nota no bimestre: Total bimestral = essa nota mesma
  - Aprovação bimestral: total >= 6.0  → azul escuro
  - Reprovação bimestral: total < 6.0  → vermelho escuro
  - Aprovação final: soma dos 4 totais >= 24.0
  - Boletim inclui faltas do bimestre
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte, vincular_mascara, mascara_nota, MEDIA_APROVACAO_BIMESTRAL, MEDIA_APROVACAO_FINAL, bimestre_atual
import pdf_utils


def _calcular_total(n1, n2):
    """Se as duas notas foram lançadas, retorna a MÉDIA delas (não a soma).
    Se só uma foi lançada (professor que dá uma nota só no bimestre),
    a nota final do bimestre é essa nota mesma."""
    tem_n1 = n1 not in (None, "")
    tem_n2 = n2 not in (None, "")
    if tem_n1 and tem_n2:
        return round((float(n1) + float(n2)) / 2, 1)
    elif tem_n1:
        return round(float(n1), 1)
    elif tem_n2:
        return round(float(n2), 1)
    return 0.0


def _cor_nota(total):
    return CORES["nota_aprovado"] if total >= MEDIA_APROVACAO_BIMESTRAL else CORES["nota_reprovado"]


def _situacao(total):
    return "✅ Aprovado" if total >= MEDIA_APROVACAO_BIMESTRAL else "❌ Reprovado"


class NotasModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.turma_id = None
        self.discs_dict = {}
        self._build_ui()
        self.carregar_turmas()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        filtros = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        filtros.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(filtros, text="📊 Notas e Boletins", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        fr = ctk.CTkFrame(filtros, fg_color="transparent")
        fr.pack(side="right", padx=15, pady=10)

        ctk.CTkLabel(fr, text="Turma:", text_color=CORES["subtexto"]).pack(side="left", padx=5)
        self.turma_var = ctk.StringVar()
        self.turma_combo = ctk.CTkOptionMenu(fr, variable=self.turma_var,
                                              command=self.ao_mudar_turma, width=160, values=[""])
        self.turma_combo.pack(side="left", padx=5)

        ctk.CTkLabel(fr, text="Bimestre:", text_color=CORES["subtexto"]).pack(side="left", padx=5)
        self.bim_var = ctk.StringVar(value=str(bimestre_atual()))
        ctk.CTkOptionMenu(fr, values=["1", "2", "3", "4"], variable=self.bim_var,
                          command=lambda _: self.carregar_notas(), width=70).pack(side="left", padx=5)

        ctk.CTkLabel(fr, text="Disciplina:", text_color=CORES["subtexto"]).pack(side="left", padx=5)
        self.disc_var = ctk.StringVar()
        self.disc_combo = ctk.CTkOptionMenu(fr, variable=self.disc_var,
                                             command=lambda _: self.carregar_notas(), width=160, values=[""])
        self.disc_combo.pack(side="left", padx=5)

        # Legenda de cores
        leg = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        leg.pack(fill="x", padx=20, pady=(6, 0))
        ctk.CTkLabel(leg, text="🔵 Total ≥ 6.0 = Aprovado no bimestre   🔴 Total < 6.0 = Reprovado   "
                               "✅ Aprovação final: soma dos 4 bimestres ≥ 24.0",
                     font=fonte(11), text_color=CORES["subtexto"]).pack(padx=15, pady=6)

        dica = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        dica.pack(fill="x", padx=20, pady=(6, 0))
        ctk.CTkLabel(dica, text="💡 Como lançar: escolha a Turma, o Bimestre e a Disciplina acima, "
                                 "clique 2x no nome do aluno na lista (ou selecione e clique em "
                                 "\"Lançar / Editar Nota\").",
                     font=fonte(11), text_color=CORES["acento"]).pack(padx=15, pady=6, anchor="w")

        tabela_frame = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        tabela_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("aluno", "nota1", "nota2", "total", "faltas", "situacao")
        self.tree = ttk.Treeview(tabela_frame, columns=cols, show="headings", height=20)
        for col, (txt, w) in {
            "aluno":    ("Aluno", 280),
            "nota1":    ("Nota 1", 80),
            "nota2":    ("Nota 2", 80),
            "total":    ("Total Bim.", 90),
            "faltas":   ("Faltas", 70),
            "situacao": ("Situação", 120),
        }.items():
            self.tree.heading(col, text=txt, anchor="w")
            self.tree.column(col, width=w, anchor="center" if col != "aluno" else "w")

        self.tree.tag_configure("aprovado",  foreground=CORES["nota_aprovado"])
        self.tree.tag_configure("reprovado", foreground=CORES["nota_reprovado"])
        self.tree.tag_configure("sem_nota",  foreground=CORES["subtexto"])

        scr = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scr.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scr.pack(side="right", fill="y", pady=5)
        self.tree.bind("<Double-1>", lambda e: self.lancar_nota())

        btn_frame = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkButton(btn_frame, text="✏ Lançar / Editar Nota", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=self.lancar_nota, width=190).pack(side="left", padx=15, pady=10)
        ctk.CTkButton(btn_frame, text="📄 Boletim PDF", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                      font=fonte(12, "bold"), command=self.gerar_boletim_pdf, width=150).pack(side="left", padx=5, pady=10)
        ctk.CTkButton(btn_frame, text="🖨 Imprimir Boletim", fg_color=CORES["primaria_clara"],
                      text_color=CORES["texto_claro"], command=self.imprimir_boletim, width=160).pack(side="left", padx=5, pady=10)
        self.label_resumo = ctk.CTkLabel(btn_frame, text="", text_color=CORES["subtexto"])
        self.label_resumo.pack(side="right", padx=20)

    # ------------------------------------------------------------------ DADOS
    def carregar_turmas(self):
        conn = get_connection()
        turmas = conn.execute(
            "SELECT id, nome_completo FROM turmas WHERE ativo=1 ORDER BY nome_completo").fetchall()
        conn.close()
        self.turmas_dict = {t["nome_completo"]: t["id"] for t in turmas}
        nomes = list(self.turmas_dict.keys())
        self.turma_combo.configure(values=nomes if nomes else ["(Nenhuma)"])
        if nomes:
            self.turma_var.set(nomes[0])
            self.ao_mudar_turma(nomes[0])

    def ao_mudar_turma(self, nome):
        self.turma_id = self.turmas_dict.get(nome)
        if not self.turma_id:
            return
        conn = get_connection()
        discs = conn.execute(
            "SELECT id, nome FROM disciplinas WHERE turma_id=? ORDER BY nome",
            (self.turma_id,)).fetchall()
        conn.close()
        self.discs_dict = {d["nome"]: d["id"] for d in discs}
        nomes = list(self.discs_dict.keys())
        self.disc_combo.configure(values=nomes if nomes else ["(Nenhuma)"])
        if nomes:
            self.disc_var.set(nomes[0])
        self.carregar_notas()

    def carregar_notas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.turma_id:
            return

        disc_id  = self.discs_dict.get(self.disc_var.get())
        bimestre = int(self.bim_var.get())

        conn = get_connection()
        alunos = conn.execute(
            "SELECT id, nome FROM alunos WHERE (turma_id=? OR turma_contraturno_id=?) AND ativo=1 AND arquivado=0 ORDER BY nome",
            (self.turma_id, self.turma_id)).fetchall()

        aprov = reprov = sem = 0
        for aluno in alunos:
            nota = conn.execute(
                "SELECT * FROM notas WHERE aluno_id=? AND disciplina_id=? AND bimestre=?",
                (aluno["id"], disc_id, bimestre)).fetchone() if disc_id else None

            # Contar faltas do bimestre para esta disciplina
            # (aproximamos: faltas no mês correspondente ao bimestre)
            faltas = 0
            if disc_id:
                faltas = conn.execute(
                    "SELECT COUNT(*) FROM frequencia WHERE aluno_id=? AND disciplina_id=? AND presente=0",
                    (aluno["id"], disc_id)).fetchone()[0] or 0

            if nota:
                n1_raw = nota["nota_1"]
                n2_raw = nota["nota_2"]
                total = _calcular_total(n1_raw, n2_raw)
                sit   = _situacao(total)
                tag   = "aprovado" if total >= MEDIA_APROVACAO_BIMESTRAL else "reprovado"
                if total >= MEDIA_APROVACAO_BIMESTRAL:
                    aprov += 1
                else:
                    reprov += 1
                n1_txt = f"{n1_raw:.1f}" if n1_raw not in (None, "") else "-"
                n2_txt = f"{n2_raw:.1f}" if n2_raw not in (None, "") else "-"
                self.tree.insert("", "end", iid=str(aluno["id"]),
                                 values=(aluno["nome"],
                                         n1_txt, n2_txt,
                                         f"{total:.1f}", str(faltas), sit),
                                 tags=(tag,))
            else:
                sem += 1
                self.tree.insert("", "end", iid=str(aluno["id"]),
                                 values=(aluno["nome"], "-", "-", "-", str(faltas), "⏳ Sem nota"),
                                 tags=("sem_nota",))

        conn.close()
        self.label_resumo.configure(
            text=f"Aprovados: {aprov}  |  Reprovados: {reprov}  |  Sem nota: {sem}")

    # ------------------------------------------------------------------ LANÇAMENTO
    def lancar_nota(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um aluno na lista.")
            return
        aluno_id = int(sel[0])
        disc_id  = self.discs_dict.get(self.disc_var.get())
        bimestre = int(self.bim_var.get())
        if not disc_id:
            messagebox.showwarning("Atenção", "Selecione uma disciplina.")
            return

        conn = get_connection()
        aluno   = conn.execute("SELECT nome FROM alunos WHERE id=?", (aluno_id,)).fetchone()
        nota_ex = conn.execute(
            "SELECT * FROM notas WHERE aluno_id=? AND disciplina_id=? AND bimestre=?",
            (aluno_id, disc_id, bimestre)).fetchone()
        conn.close()

        form = ctk.CTkToplevel(self.winfo_toplevel())
        form.title(f"Nota — {aluno['nome']}")
        form.geometry("520x340")
        form.grab_set()
        form.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(form, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text=f"📝 {aluno['nome']}", font=fonte(13, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        frame = ctk.CTkFrame(form, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True, padx=25, pady=15)

        try:
            ctk.CTkLabel(frame, text=f"Disciplina: {self.disc_var.get()}  |  {bimestre}º Bimestre",
                         text_color=CORES["subtexto"], font=fonte(11)).pack(anchor="w", pady=(0, 12))

            campos_nota = {}
            for label, key, dica in [
                ("Nota 1  (0.0 – 10.0)", "nota_1",  "Ex: 7.5"),
                ("Nota 2  (0.0 – 10.0)", "nota_2",  "Ex: 8.0"),
            ]:
                ctk.CTkLabel(frame, text=label, font=fonte(peso="bold"),
                             text_color=CORES["subtexto"]).pack(anchor="w")
                e = ctk.CTkEntry(frame, width=160, placeholder_text=dica)
                val = nota_ex[key] if nota_ex and nota_ex[key] is not None else ""
                e.insert(0, str(val))
                e.pack(anchor="w", pady=(2, 10))
                vincular_mascara(e, mascara_nota)
                campos_nota[key] = e
        except Exception as e:
            ctk.CTkLabel(frame, text=f"⚠ Não foi possível montar o formulário:\n{e}",
                         text_color=CORES["perigo"], font=fonte(12), wraplength=350,
                         justify="left").pack(anchor="w", pady=10)
            ctk.CTkButton(form, text="Fechar", fg_color=CORES["perigo"],
                          text_color=CORES["texto_claro"], command=form.destroy).pack(pady=10)
            return

        # Preview do total em tempo real
        lbl_preview = ctk.CTkLabel(frame, text="Total bimestral: —",
                                    font=fonte(13, "bold"), text_color=CORES["subtexto"])
        lbl_preview.pack(anchor="w", pady=(4, 0))

        def atualizar_preview(*_):
            try:
                n1_s = campos_nota["nota_1"].get().strip()
                n2_s = campos_nota["nota_2"].get().strip()
                n1 = float(n1_s) if n1_s else None
                n2 = float(n2_s) if n2_s else None
                if n1 is None and n2 is None:
                    lbl_preview.configure(text="Total bimestral: —", text_color=CORES["subtexto"])
                    return
                total = _calcular_total(n1, n2)
                cor = _cor_nota(total)
                sit = _situacao(total)
                lbl_preview.configure(text=f"Total bimestral: {total:.1f}  →  {sit}", text_color=cor)
            except ValueError:
                lbl_preview.configure(text="Total bimestral: —", text_color=CORES["subtexto"])

        campos_nota["nota_1"].bind("<KeyRelease>", lambda e: atualizar_preview())
        campos_nota["nota_2"].bind("<KeyRelease>", lambda e: atualizar_preview())
        atualizar_preview()

        def salvar():
            try:
                n1_s = campos_nota["nota_1"].get().strip()
                n2_s = campos_nota["nota_2"].get().strip()
                if not n1_s and not n2_s:
                    messagebox.showerror("Erro", "Preencha pelo menos uma das notas.", parent=form)
                    return
                n1 = float(n1_s) if n1_s else None
                n2 = float(n2_s) if n2_s else None
                for n in (n1, n2):
                    if n is not None and not (0 <= n <= 10):
                        messagebox.showerror("Erro", "Notas devem ser entre 0 e 10.", parent=form)
                        return
                total = _calcular_total(n1, n2)
                conn = get_connection()
                if nota_ex:
                    conn.execute(
                        "UPDATE notas SET nota_1=?, nota_2=?, total_bimestral=? "
                        "WHERE aluno_id=? AND disciplina_id=? AND bimestre=?",
                        (n1, n2, total, aluno_id, disc_id, bimestre))
                else:
                    conn.execute(
                        "INSERT INTO notas (aluno_id,disciplina_id,bimestre,nota_1,nota_2,total_bimestral) "
                        "VALUES (?,?,?,?,?,?)",
                        (aluno_id, disc_id, bimestre, n1, n2, total))
                conn.commit()
                conn.close()
                messagebox.showinfo("Sucesso",
                    f"Total bimestral: {total:.1f}  →  {_situacao(total)}", parent=form)
                form.destroy()
                self.carregar_notas()
            except ValueError:
                messagebox.showerror("Erro", "Digite valores numéricos válidos.", parent=form)

        bb = ctk.CTkFrame(form, fg_color=CORES["card"], corner_radius=0, height=55)
        bb.pack(fill="x", side="bottom")
        ctk.CTkButton(bb, text="✖ Fechar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=form.destroy, width=100, height=36).pack(side="right", padx=(5, 15), pady=10)
        ctk.CTkButton(bb, text="💾 Salvar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=salvar, width=120, height=36).pack(side="right", padx=5, pady=10)

    # ------------------------------------------------------------------ BOLETIM
    def _montar_boletim(self, aluno_id):
        conn = get_connection()
        aluno = conn.execute("SELECT nome, cgm FROM alunos WHERE id=?", (aluno_id,)).fetchone()
        turma = conn.execute("SELECT nome_completo FROM turmas WHERE id=?", (self.turma_id,)).fetchone()
        discs = conn.execute(
            "SELECT id, nome FROM disciplinas WHERE turma_id=? ORDER BY nome",
            (self.turma_id,)).fetchall()

        # Cabeçalho da tabela
        linhas = [["Disciplina", "B1", "B2", "B3", "B4", "Total Anual", "Situação", "Faltas"]]

        total_anual_global = 0
        for d in discs:
            notas = {n["bimestre"]: n["total_bimestral"] for n in conn.execute(
                "SELECT bimestre, total_bimestral FROM notas WHERE aluno_id=? AND disciplina_id=?",
                (aluno_id, d["id"])).fetchall()}
            bims = [str(notas.get(b, "-")) for b in range(1, 5)]
            vals  = [notas[b] for b in range(1, 5) if b in notas]
            total_anual = round(sum(vals), 1) if vals else "-"
            if isinstance(total_anual, float):
                total_anual_global += total_anual
            sit = ("Aprovado" if isinstance(total_anual, float) and total_anual >= MEDIA_APROVACAO_FINAL
                   else ("Reprovado" if isinstance(total_anual, float) else "—"))
            # Faltas totais na disciplina
            faltas = conn.execute(
                "SELECT COUNT(*) FROM frequencia WHERE aluno_id=? AND disciplina_id=? AND presente=0",
                (aluno_id, d["id"])).fetchone()[0] or 0
            linhas.append([d["nome"]] + bims + [str(total_anual), sit, str(faltas)])

        conn.close()
        sit_final = ("APROVADO" if total_anual_global >= MEDIA_APROVACAO_FINAL
                     else "REPROVADO" if total_anual_global > 0 else "—")
        blocos = [
            ("titulo", "Identificação do Aluno"),
            ("tabela", [["Campo", "Informação"],
                        ["Nome",  aluno["nome"]],
                        ["CGM",   aluno["cgm"] or "-"],
                        ["Turma", turma["nome_completo"] if turma else "-"]]),
            ("titulo", "Notas por Bimestre  |  Total Bimestral = Nota 1 + Nota 2  |  Aprovação ≥ 6.0 por bimestre / ≥ 24.0 no ano"),
            ("tabela", linhas),
            ("texto",  f"SITUAÇÃO FINAL: {sit_final}  (Total anual: {total_anual_global:.1f})"),
        ]
        nome_arq = f"Boletim_{aluno['nome'].replace(' ', '_')}.pdf"
        return blocos, nome_arq, aluno["nome"]

    def gerar_boletim_pdf(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um aluno.")
            return
        blocos, nome_arq, nome = self._montar_boletim(int(sel[0]))
        pdf_utils.salvar_pdf_como(f"Boletim Escolar — {nome}", blocos, nome_arq, parent=self)

    def imprimir_boletim(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um aluno.")
            return
        blocos, nome_arq, nome = self._montar_boletim(int(sel[0]))
        pdf_utils.imprimir_pdf(f"Boletim Escolar — {nome}", blocos, nome_arq, parent=self)
