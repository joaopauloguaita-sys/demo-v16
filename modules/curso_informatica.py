import os
import sys

import customtkinter as ctk
from tkinter import messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte


class CursoInformaticaModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()
        self.carregar()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🖥️ Curso de Informática", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(header, text="+ Nova Matrícula", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=lambda: self._form(None),
                      width=170).pack(side="right", padx=15, pady=10)

        dica = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        dica.pack(fill="x", padx=20, pady=(10, 0))
        lbl_dica = ctk.CTkLabel(dica, text="💡 Esse curso é independente do restante do sistema — pode matricular "
                                 "alunos da escola ou da comunidade. Não entra no quadro de chamada nem "
                                 "de notas normal. Cadastre a disciplina \"Informática\" (com a professora "
                                 "responsável) na aba Disciplinas/Grade Curricular pra ela aparecer aqui.",
                     font=fonte(11), text_color=CORES["acento"], justify="left")
        lbl_dica.pack(padx=15, pady=8, anchor="w", fill="x")
        dica.bind("<Configure>", lambda e: lbl_dica.configure(wraplength=max(200, e.width - 30)))

        tabela_f = ctk.CTkFrame(self, fg_color="transparent")
        tabela_f.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("nome", "serie", "disciplina", "dia", "periodo", "horario", "obs")
        self.tree = ttk.Treeview(tabela_f, columns=cols, show="headings", height=18)
        for col, (txt, w) in {"nome": ("Aluno", 220), "serie": ("Série/Turma", 130),
                               "disciplina": ("Disciplina", 140), "dia": ("Dia", 100),
                               "periodo": ("Período", 90), "horario": ("Horário", 110),
                               "obs": ("Observação", 200)}.items():
            self.tree.heading(col, text=txt, anchor="w")
            self.tree.column(col, width=w, anchor="w")
        self.tree.bind("<Double-1>", lambda e: self._editar_selecionado())

        scroll = ttk.Scrollbar(tabela_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkButton(btn_f, text="🗑 Remover Selecionado", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=self._excluir_selecionado, width=180).pack(side="left")

    def _disciplinas_disponiveis(self):
        conn = get_connection()
        discs = conn.execute("""
            SELECT d.id, d.nome, p.nome as professor
            FROM disciplinas d LEFT JOIN professores p ON p.id = d.professor_id
            WHERE d.excluido IS NULL OR d.excluido = 0
            ORDER BY d.nome
        """).fetchall()
        conn.close()
        return discs

    def carregar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            conn = get_connection()
            registros = conn.execute("""
                SELECT c.*, d.nome as disciplina_nome
                FROM curso_informatica c LEFT JOIN disciplinas d ON d.id = c.disciplina_id
                WHERE c.excluido IS NULL OR c.excluido = 0
                ORDER BY c.dia_semana, c.horario, c.nome_aluno
            """).fetchall()
            conn.close()
            for r in registros:
                self.tree.insert("", "end", iid=str(r["id"]),
                                 values=(r["nome_aluno"], r["serie_turma"] or "-", r["disciplina_nome"] or "-",
                                         r["dia_semana"] or "-", r["periodo"] or "-", r["horario"] or "-",
                                         r["observacao"] or ""))
        except Exception as e:
            messagebox.showerror("Erro ao carregar a lista", str(e))

    def _sel_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _editar_selecionado(self):
        rid = self._sel_id()
        if not rid:
            return
        conn = get_connection()
        reg = conn.execute("SELECT * FROM curso_informatica WHERE id=?", (rid,)).fetchone()
        conn.close()
        if reg:
            self._form(dict(reg))

    def _excluir_selecionado(self):
        rid = self._sel_id()
        if not rid:
            messagebox.showwarning("Atenção", "Selecione um registro na lista.")
            return
        if not messagebox.askyesno("Confirmar", "Remover esta matrícula do Curso de Informática?"):
            return
        conn = get_connection()
        conn.execute("UPDATE curso_informatica SET excluido=1 WHERE id=?", (rid,))
        conn.commit()
        conn.close()
        self.carregar()

    def _form(self, reg):
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Matrícula — Curso de Informática" if not reg else "Editar Matrícula")
        win.geometry("460x680")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(win, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="🖥️ Curso de Informática", font=fonte(14, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        corpo = ctk.CTkFrame(win, fg_color=CORES["fundo"])
        corpo.pack(fill="both", expand=True, padx=25, pady=15)

        def lbl(t):
            ctk.CTkLabel(corpo, text=t, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).pack(anchor="w", pady=(6, 0))

        lbl("Nome do Aluno *")
        e_nome = ctk.CTkEntry(corpo, width=340, placeholder_text="Nome completo")
        if reg: e_nome.insert(0, reg.get("nome_aluno", "") or "")
        e_nome.pack()

        lbl("Série/Turma (ou \"Comunidade\")")
        e_serie = ctk.CTkEntry(corpo, width=340, placeholder_text="Ex: 5º Ano B, ou Comunidade")
        if reg: e_serie.insert(0, reg.get("serie_turma", "") or "")
        e_serie.pack()

        lbl("Disciplina *")
        discs = self._disciplinas_disponiveis()
        if not discs:
            ctk.CTkLabel(corpo, text="⚠ Nenhuma disciplina cadastrada ainda. Cadastre em "
                                     "Disciplinas/Grade Curricular primeiro.",
                         text_color=CORES["perigo"], font=fonte(10), wraplength=340,
                         justify="left").pack(anchor="w")
        opcoes_disc = {f"{d['nome']}" + (f" — {d['professor']}" if d["professor"] else ""): d["id"]
                       for d in discs}
        disc_var = ctk.StringVar(value=list(opcoes_disc.keys())[0] if opcoes_disc else "")
        if reg and reg.get("disciplina_id"):
            for texto, did in opcoes_disc.items():
                if did == reg["disciplina_id"]:
                    disc_var.set(texto)
        ctk.CTkOptionMenu(corpo, variable=disc_var, values=list(opcoes_disc.keys()) or [""],
                          width=340).pack()

        lbl("Dia da Semana")
        dia_var = ctk.StringVar(value=(reg.get("dia_semana") if reg else "Terça-feira") or "Terça-feira")
        ctk.CTkOptionMenu(corpo, variable=dia_var,
                          values=["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"],
                          width=340).pack()

        lbl("Período")
        periodo_var = ctk.StringVar(value=(reg.get("periodo") if reg else "Manhã") or "Manhã")
        ctk.CTkOptionMenu(corpo, variable=periodo_var, values=["Manhã", "Tarde"], width=340).pack()

        lbl("Horário (Ex: 09:00 às 10:00)")
        e_horario = ctk.CTkEntry(corpo, width=340, placeholder_text="09:00 às 10:00")
        if reg: e_horario.insert(0, reg.get("horario", "") or "")
        e_horario.pack()

        lbl("Observação")
        e_obs = ctk.CTkEntry(corpo, width=340)
        if reg: e_obs.insert(0, reg.get("observacao", "") or "")
        e_obs.pack()

        def salvar():
            nome = e_nome.get().strip()
            if not nome or not opcoes_disc:
                messagebox.showerror("Erro", "Nome do aluno e disciplina são obrigatórios.", parent=win)
                return
            disc_id = opcoes_disc[disc_var.get()]
            try:
                conn = get_connection()
                if reg:
                    conn.execute("""UPDATE curso_informatica SET nome_aluno=?, serie_turma=?, disciplina_id=?,
                        dia_semana=?, periodo=?, horario=?, observacao=? WHERE id=?""",
                        (nome, e_serie.get().strip(), disc_id, dia_var.get(), periodo_var.get(),
                         e_horario.get().strip(), e_obs.get().strip(), reg["id"]))
                else:
                    conn.execute("""INSERT INTO curso_informatica
                        (nome_aluno, serie_turma, disciplina_id, dia_semana, periodo, horario, observacao)
                        VALUES (?,?,?,?,?,?,?)""",
                        (nome, e_serie.get().strip(), disc_id, dia_var.get(), periodo_var.get(),
                         e_horario.get().strip(), e_obs.get().strip()))
                conn.commit()
                conn.close()
            except Exception as e:
                messagebox.showerror("Erro ao salvar", str(e), parent=win)
                return
            win.destroy()
            self.carregar()

        ctk.CTkButton(corpo, text="💾 Salvar", fg_color=CORES["acento"], hover_color=CORES["acento_hover"],
                      text_color=CORES["texto_claro"], font=fonte(13, "bold"),
                      command=salvar, width=340, height=38).pack(pady=15)
