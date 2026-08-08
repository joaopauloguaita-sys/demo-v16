import os
import sys

import customtkinter as ctk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte
from modules.matriculas_shared import ORDEM_SERIES, listar_turmas_ordenadas


class ConfigTurmasProximoAnoModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()
        self.carregar()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🏫 Configurar Turmas do Próximo Ano", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        dica = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        dica.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(dica, text="💡 Aqui você define quantas turmas de cada série vão existir no próximo "
                                 "ano (pode ser diferente de hoje — por exemplo, 3 turmas de 4º ano em "
                                 "vez de 2). Essa lista é só o \"molde\" usado nas abas de Matrículas/"
                                 "Rematrículas e Vagas — não mexe nas turmas de hoje.",
                     font=fonte(11), text_color=CORES["acento"], wraplength=950,
                     justify="left").pack(padx=15, pady=8, anchor="w")

        form = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        form.pack(fill="x", padx=20, pady=(10, 0))
        linha = ctk.CTkFrame(form, fg_color="transparent")
        linha.pack(padx=15, pady=15)

        ctk.CTkLabel(linha, text="Série", font=fonte(10, "bold"), text_color=CORES["subtexto"]).grid(
            row=0, column=0, sticky="w")
        self.serie_var = ctk.StringVar(value=ORDEM_SERIES[0])
        ctk.CTkOptionMenu(linha, variable=self.serie_var, values=ORDEM_SERIES, width=160).grid(
            row=1, column=0, padx=(0, 10))

        ctk.CTkLabel(linha, text="Letra da Turma", font=fonte(10, "bold"), text_color=CORES["subtexto"]).grid(
            row=0, column=1, sticky="w")
        self.e_letra = ctk.CTkEntry(linha, width=100, placeholder_text="Ex: A")
        self.e_letra.grid(row=1, column=1, padx=10)

        ctk.CTkLabel(linha, text="Turno", font=fonte(10, "bold"), text_color=CORES["subtexto"]).grid(
            row=0, column=2, sticky="w")
        self.turno_var = ctk.StringVar(value="Manhã")
        ctk.CTkOptionMenu(linha, variable=self.turno_var, values=["Manhã", "Tarde", "Integral"], width=140).grid(
            row=1, column=2, padx=10)

        ctk.CTkButton(linha, text="+ Adicionar Turma", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(12, "bold"), command=self.adicionar, width=160, height=32).grid(
                      row=1, column=3, padx=(15, 0))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

    def adicionar(self):
        letra = self.e_letra.get().strip().upper()
        if not letra:
            messagebox.showerror("Erro", "Informe a letra da turma (ex: A, B, C).")
            return
        serie = self.serie_var.get()
        nome_completo = f"{serie} {letra}"

        conn = get_connection()
        existe = conn.execute("SELECT id, excluido FROM turmas_proximo_ano WHERE nome_completo=?",
                              (nome_completo,)).fetchone()
        if existe and not existe["excluido"]:
            messagebox.showwarning("Atenção", f'"{nome_completo}" já está cadastrada.')
            conn.close()
            return
        if existe and existe["excluido"]:
            conn.execute("UPDATE turmas_proximo_ano SET excluido=0, turno=? WHERE id=?",
                        (self.turno_var.get(), existe["id"]))
        else:
            conn.execute("INSERT INTO turmas_proximo_ano (serie, letra, turno, nome_completo) VALUES (?,?,?,?)",
                        (serie, letra, self.turno_var.get(), nome_completo))
        conn.commit()
        conn.close()
        self.e_letra.delete(0, "end")
        self.carregar()

    def carregar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        conn = get_connection()
        turmas = listar_turmas_ordenadas(conn)
        conn.close()

        if not turmas:
            ctk.CTkLabel(self.scroll, text="Nenhuma turma configurada ainda pro próximo ano.",
                         text_color=CORES["subtexto"], font=fonte(12)).pack(pady=30)
            return

        for t in turmas:
            linha = ctk.CTkFrame(self.scroll, fg_color=CORES["card"], corner_radius=8)
            linha.pack(fill="x", pady=3)
            ctk.CTkLabel(linha, text=f"{t['nome_completo']} — {t['turno']}", font=fonte(12, "bold"),
                         text_color=CORES["texto_card"]).pack(side="left", padx=15, pady=10)
            ctk.CTkButton(linha, text="🗑 Remover", width=100, height=28, font=fonte(10),
                          fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"],
                          text_color=CORES["texto_claro"],
                          command=lambda tid=t["id"], nome=t["nome_completo"]:
                          self.remover(tid, nome)).pack(side="right", padx=15, pady=6)

    def remover(self, turma_id, nome):
        conn = get_connection()
        em_uso = conn.execute(
            "SELECT COUNT(*) FROM matriculas_proximo_ano WHERE turma_destino_id=? "
            "AND (excluido IS NULL OR excluido = 0)", (turma_id,)
        ).fetchone()[0]
        if em_uso > 0:
            conn.close()
            messagebox.showerror(
                "Não é possível remover",
                f'"{nome}" já tem {em_uso} aluno(s) direcionado(s) pra ela em Matrículas/Rematrículas. '
                "Mude esses alunos de turma primeiro (ou remova-os da lista) antes de excluir esta turma.")
            return
        if not messagebox.askyesno("Confirmar", f'Remover "{nome}" da lista do próximo ano?'):
            conn.close()
            return
        conn.execute("UPDATE turmas_proximo_ano SET excluido=1 WHERE id=?", (turma_id,))
        conn.execute("DELETE FROM vagas_ano_letivo WHERE turma_id=?", (turma_id,))
        conn.commit()
        conn.close()
        self.carregar()
