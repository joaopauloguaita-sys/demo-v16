import os
import sys
from datetime import date

import customtkinter as ctk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte, mascara_data, mascara_telefone, mascara_cgm, vincular_mascara, abrir_whatsapp
from modules.matriculas_shared import ORDEM_SERIES, abrir_dialogo_matricula


class FilaEsperaModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()
        self.carregar()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="⏳ Fila de Espera", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        form = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        form.pack(fill="x", padx=20, pady=(10, 0))
        linha1 = ctk.CTkFrame(form, fg_color="transparent")
        linha1.pack(fill="x", padx=15, pady=(15, 5))

        def campo(parent_f, label, largura=180, mascara=None, ph=""):
            f = ctk.CTkFrame(parent_f, fg_color="transparent")
            f.pack(side="left", padx=6)
            ctk.CTkLabel(f, text=label, font=fonte(10, "bold"), text_color=CORES["subtexto"],
                        anchor="w").pack(anchor="w")
            e = ctk.CTkEntry(f, width=largura, placeholder_text=ph)
            e.pack()
            if mascara:
                vincular_mascara(e, mascara)
            return e

        self.e_cgm = campo(linha1, "CGM (se já tiver)", 120, mascara_cgm)
        self.e_nome = campo(linha1, "Nome completo *", 220)
        self.e_nasc = campo(linha1, "Data de Nascimento", 120, mascara_data, "DD/MM/AAAA")

        ctk.CTkLabel(linha1, text="Série *", font=fonte(10, "bold"), text_color=CORES["subtexto"]).pack(
            side="left", padx=(6, 0), anchor="s")
        self.serie_var = ctk.StringVar(value=ORDEM_SERIES[0])
        f_serie = ctk.CTkFrame(linha1, fg_color="transparent")
        f_serie.pack(side="left", padx=6)
        ctk.CTkLabel(f_serie, text="Série *", font=fonte(10, "bold"),
                    text_color=CORES["subtexto"]).pack(anchor="w")
        ctk.CTkOptionMenu(f_serie, variable=self.serie_var, values=ORDEM_SERIES, width=130).pack()

        f_turno = ctk.CTkFrame(linha1, fg_color="transparent")
        f_turno.pack(side="left", padx=6)
        ctk.CTkLabel(f_turno, text="Turno de Preferência", font=fonte(10, "bold"),
                    text_color=CORES["subtexto"]).pack(anchor="w")
        self.turno_var = ctk.StringVar(value="Manhã")
        ctk.CTkOptionMenu(f_turno, variable=self.turno_var, values=["Manhã", "Tarde"], width=110).pack()

        linha2 = ctk.CTkFrame(form, fg_color="transparent")
        linha2.pack(fill="x", padx=15, pady=(5, 15))
        self.e_resp = campo(linha2, "Nome do Responsável *", 220)
        self.e_tel = campo(linha2, "Telefone (com WhatsApp)", 160, mascara_telefone, "(00) 00000-0000")

        ctk.CTkButton(linha2, text="💾 Adicionar à Fila", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(12, "bold"), command=self.salvar, width=160, height=36).pack(
                      side="left", padx=(20, 0), pady=(16, 0))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

    def salvar(self):
        nome = self.e_nome.get().strip()
        resp = self.e_resp.get().strip()
        if not nome or not resp:
            messagebox.showerror("Erro", "Nome do aluno e nome do responsável são obrigatórios.")
            return
        conn = get_connection()
        conn.execute("""INSERT INTO fila_espera
            (cgm, nome, data_nascimento, serie, turno_preferencia, responsavel, telefone, data_cadastro)
            VALUES (?,?,?,?,?,?,?,?)""",
            (self.e_cgm.get().strip(), nome, self.e_nasc.get().strip(), self.serie_var.get(),
             self.turno_var.get(), resp, self.e_tel.get().strip(), date.today().isoformat()))
        conn.commit()
        conn.close()

        for e in [self.e_cgm, self.e_nome, self.e_nasc, self.e_resp, self.e_tel]:
            e.delete(0, "end")
        self.carregar()

    def carregar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        conn = get_connection()
        registros = conn.execute(
            "SELECT * FROM fila_espera WHERE excluido IS NULL OR excluido = 0 ORDER BY data_cadastro"
        ).fetchall()
        conn.close()

        por_serie = {}
        for r in registros:
            por_serie.setdefault(r["serie"], []).append(r)

        if not registros:
            ctk.CTkLabel(self.scroll, text="Nenhuma criança na fila de espera no momento.",
                         text_color=CORES["subtexto"], font=fonte(12)).pack(pady=30)
            return

        for serie in ORDEM_SERIES:
            regs = por_serie.get(serie, [])
            if not regs:
                continue
            ctk.CTkLabel(self.scroll, text=f"📚 {serie} — {len(regs)} na fila", font=fonte(14, "bold"),
                         text_color=CORES["dourado"]).pack(anchor="w", pady=(15, 5))

            for reg in regs:
                linha = ctk.CTkFrame(self.scroll, fg_color=CORES["card"], corner_radius=8)
                linha.pack(fill="x", pady=3)

                info_f = ctk.CTkFrame(linha, fg_color="transparent")
                info_f.pack(side="left", padx=12, pady=8, fill="x", expand=True)
                ctk.CTkLabel(info_f, text=reg["nome"], font=fonte(12, "bold"), anchor="w",
                             text_color=CORES["texto_card"]).pack(anchor="w")
                sub = f"Nasc.: {reg['data_nascimento'] or '-'}  •  Turno: {reg['turno_preferencia'] or '-'}  " \
                      f"•  Resp.: {reg['responsavel']}  •  Tel.: {reg['telefone'] or '-'}"
                ctk.CTkLabel(info_f, text=sub, font=fonte(10),
                             text_color=CORES["subtexto"]).pack(anchor="w")

                btns = ctk.CTkFrame(linha, fg_color="transparent")
                btns.pack(side="right", padx=10, pady=6)

                if reg["telefone"]:
                    ctk.CTkButton(btns, text="💬 WhatsApp", width=100, height=30, font=fonte(10),
                                  fg_color="#25D366", hover_color="#1DA851", text_color="#ffffff",
                                  command=lambda t=reg["telefone"]: abrir_whatsapp(t)).pack(side="left", padx=3)

                ctk.CTkButton(btns, text="➡️ Encaminhar p/ Matrícula", width=190, height=30, font=fonte(10),
                              fg_color=CORES["acento"], hover_color=CORES["acento_hover"],
                              text_color=CORES["texto_claro"],
                              command=lambda r=reg: self.encaminhar(r)).pack(side="left", padx=3)

                ctk.CTkButton(btns, text="🗑", width=36, height=30, fg_color=CORES["perigo"],
                              hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                              command=lambda r=reg: self.excluir(r)).pack(side="left", padx=3)

    def excluir(self, reg):
        if not messagebox.askyesno("Confirmar", f"Remover {reg['nome']} da fila de espera?"):
            return
        conn = get_connection()
        conn.execute("UPDATE fila_espera SET excluido=1 WHERE id=?", (reg["id"],))
        conn.commit()
        conn.close()
        self.carregar()

    def encaminhar(self, reg):
        conn = get_connection()
        aluno_id = None
        if reg["cgm"]:
            existente = conn.execute("SELECT id FROM alunos WHERE cgm=?", (reg["cgm"],)).fetchone()
            if existente:
                aluno_id = existente["id"]
        if not aluno_id:
            conn.execute("""INSERT INTO alunos (cgm, nome, data_nascimento, ativo, arquivado)
                VALUES (?,?,?,1,0)""", (reg["cgm"] or None, reg["nome"], reg["data_nascimento"]))
            aluno_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        def ao_concluir(reg_id=reg["id"]):
            conn2 = get_connection()
            conn2.execute("UPDATE fila_espera SET excluido=1 WHERE id=?", (reg_id,))
            conn2.commit()
            conn2.close()
            self.carregar()
            messagebox.showinfo("Encaminhado",
                f"{reg['nome']} foi enviado(a) para a aba de Matrículas e Rematrículas!")

        abrir_dialogo_matricula(self.winfo_toplevel(), aluno_id, reg["nome"], on_concluido=ao_concluir)
