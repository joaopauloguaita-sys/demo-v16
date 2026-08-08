"""
Widgets reutilizáveis: OcorrenciasWidget e AtestadosWidget.
Usados nas fichas de alunos, professores, funcionários, pedagogas, secretários e diretores.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte, vincular_mascara, mascara_data, data_tela_para_bd, data_bd_para_tela


def _redirecionar_scroll_para_pagina(widget_interno):
    """Faz a roda do mouse, quando estiver sobre uma tabela interna (Treeview),
    rolar a página inteira (o CTkScrollableFrame mais próximo) em vez de tentar
    rolar só a tabelinha — evita a sensação de 'travar' ao passar por cima dela."""

    def _achar_canvas_scrollavel(widget):
        atual = widget
        while atual is not None:
            canvas = getattr(atual, "_parent_canvas", None)
            if canvas is not None:
                return canvas
            atual = getattr(atual, "master", None)
        return None

    def _handler(event):
        canvas = _achar_canvas_scrollavel(widget_interno)
        if canvas is not None:
            if getattr(event, "num", None) == 4:
                canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                canvas.yview_scroll(1, "units")
            elif getattr(event, "delta", 0) != 0:
                canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    widget_interno.bind("<MouseWheel>", _handler)
    widget_interno.bind("<Button-4>", _handler)
    widget_interno.bind("<Button-5>", _handler)


class OcorrenciasWidget(ctk.CTkFrame):
    """
    entidade: 'alunos', 'professores', 'funcionarios', etc.
    entidade_id: id do registro
    somente_leitura: True = apenas visualiza
    """
    def __init__(self, parent, entidade, entidade_id, somente_leitura=False):
        super().__init__(parent, fg_color=CORES["card_claro"], corner_radius=10)
        self.entidade = entidade
        self.entidade_id = entidade_id
        self.somente_leitura = somente_leitura
        self._build()
        self.carregar()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(header, text="📋 Ocorrências", font=fonte(13, "bold"),
                     text_color=CORES["dourado"]).pack(side="left")
        if not self.somente_leitura:
            ctk.CTkButton(header, text="+ Registrar", fg_color=CORES["acento"],
                          hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                          command=self._nova, width=110, height=28).pack(side="right")
            ctk.CTkButton(header, text="🗑 Remover", fg_color=CORES["perigo"],
                          hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                          command=self._remover, width=100, height=28).pack(side="right", padx=5)

        cols = ("data", "descricao", "registrado_por")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=4)
        self.tree.heading("data", text="Data", anchor="w")
        self.tree.column("data", width=100, anchor="w")
        self.tree.heading("descricao", text="Descrição", anchor="w")
        self.tree.column("descricao", width=400, anchor="w")
        self.tree.heading("registrado_por", text="Registrado por", anchor="w")
        self.tree.column("registrado_por", width=160, anchor="w")
        self.tree.pack(fill="x", padx=10, pady=(0, 8))
        self.tree.bind("<Double-1>", lambda e: self._ver_detalhe())
        _redirecionar_scroll_para_pagina(self.tree)

    def carregar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.entidade_id:
            return
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, data, descricao, registrado_por FROM ocorrencias "
            "WHERE entidade=? AND entidade_id=? AND (excluido IS NULL OR excluido=0) ORDER BY data DESC",
            (self.entidade, self.entidade_id)).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", iid=r["id"],
                             values=(data_bd_para_tela(r["data"]), r["descricao"], r["registrado_por"] or "-"))

    def _nova(self):
        if not self.entidade_id:
            messagebox.showwarning("Atenção", "Salve o cadastro antes de registrar ocorrências.")
            return
        self._abrir_formulario()

    def _abrir_formulario(self, ocorrencia_id=None):
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Registrar Ocorrência" if not ocorrencia_id else "Editar Ocorrência")
        win.geometry("550x420")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        dados = {"data": date.today().strftime("%d/%m/%Y"), "descricao": "", "registrado_por": ""}
        if ocorrencia_id:
            conn = get_connection()
            r = conn.execute("SELECT * FROM ocorrencias WHERE id=?", (ocorrencia_id,)).fetchone()
            conn.close()
            if r:
                dados = {
                    "data": data_bd_para_tela(r["data"]),
                    "descricao": r["descricao"],
                    "registrado_por": r["registrado_por"] or ""
                }

        frame = ctk.CTkFrame(win, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(frame, text="Data", font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w")
        data_e = ctk.CTkEntry(frame, width=140, placeholder_text="DD/MM/AAAA")
        data_e.insert(0, dados["data"])
        data_e.pack(anchor="w", pady=(2, 15))
        vincular_mascara(data_e, mascara_data)

        ctk.CTkLabel(frame, text="Descrição da Ocorrência *", font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w")
        desc_txt = ctk.CTkTextbox(frame, height=140, width=480, border_width=1, border_color=CORES["borda"])
        desc_txt.insert("1.0", dados["descricao"])
        desc_txt.pack(pady=(2, 15))

        ctk.CTkLabel(frame, text="Registrado por", font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w")
        reg_e = ctk.CTkEntry(frame, width=350)
        reg_e.insert(0, dados["registrado_por"])
        reg_e.pack(anchor="w", pady=(2, 10))

        def salvar():
            desc = desc_txt.get("1.0", "end-1c").strip()
            if not desc:
                messagebox.showerror("Erro", "A descrição é obrigatória.", parent=win)
                return
            data_bd = data_tela_para_bd(data_e.get().strip())
            conn = get_connection()
            if ocorrencia_id:
                conn.execute("UPDATE ocorrencias SET data=?, descricao=?, registrado_por=? WHERE id=?",
                             (data_bd, desc, reg_e.get().strip(), ocorrencia_id))
            else:
                conn.execute("INSERT INTO ocorrencias (entidade,entidade_id,data,descricao,registrado_por) VALUES (?,?,?,?,?)",
                            (self.entidade, self.entidade_id, data_bd, desc, reg_e.get().strip()))
            conn.commit()
            conn.close()
            win.destroy()
            self.carregar()

        btn_f = ctk.CTkFrame(win, fg_color=CORES["card"], height=60)
        btn_f.pack(fill="x", side="bottom")
        btn_f.pack_propagate(False)

        ctk.CTkButton(btn_f, text="✖ Cancelar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=win.destroy, width=120, height=36).pack(side="right", padx=15, pady=12)
        ctk.CTkButton(btn_f, text="💾 Salvar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(12, "bold"), command=salvar, width=130, height=36).pack(side="right", padx=0, pady=12)

    def _remover(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione uma ocorrência.")
            return
        if messagebox.askyesno("Confirmar", "Remover esta ocorrência?"):
            conn = get_connection()
            conn.execute("UPDATE ocorrencias SET excluido=1 WHERE id=?", (int(sel[0]),))
            conn.commit()
            conn.close()
            self.carregar()

    def _ver_detalhe(self):
        sel = self.tree.selection()
        if not sel: return
        self._abrir_formulario(int(sel[0]))


class AtestadosWidget(ctk.CTkFrame):
    def __init__(self, parent, entidade, entidade_id, somente_leitura=False):
        super().__init__(parent, fg_color=CORES["card_claro"], corner_radius=10)
        self.entidade = entidade
        self.entidade_id = entidade_id
        self.somente_leitura = somente_leitura
        self._build()
        self.carregar()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(header, text="📄 Atestados / Declarações", font=fonte(13, "bold"),
                     text_color=CORES["dourado"]).pack(side="left")
        if not self.somente_leitura:
            ctk.CTkButton(header, text="+ Registrar", fg_color=CORES["acento"],
                          hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                          command=self._novo, width=110, height=28).pack(side="right")
            ctk.CTkButton(header, text="🗑 Remover", fg_color=CORES["perigo"],
                          hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                          command=self._remover, width=100, height=28).pack(side="right", padx=5)

        cols = ("tipo", "data", "duracao", "obs")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=4)
        for col, (txt, w) in {"tipo": ("Tipo", 120), "data": ("Data", 100),
                               "duracao": ("Duração", 110), "obs": ("Observação", 270)}.items():
            self.tree.heading(col, text=txt, anchor="w")
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="x", padx=10, pady=(0, 8))
        self.tree.bind("<Double-1>", lambda e: self._ver_detalhe())
        _redirecionar_scroll_para_pagina(self.tree)

    def carregar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.entidade_id:
            return
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, tipo, data, duracao, unidade_duracao, observacao FROM atestados "
            "WHERE entidade=? AND entidade_id=? AND (excluido IS NULL OR excluido=0) ORDER BY data DESC",
            (self.entidade, self.entidade_id)).fetchall()
        conn.close()
        for r in rows:
            dur = f"{r['duracao']} {r['unidade_duracao']}"
            self.tree.insert("", "end", iid=r["id"],
                             values=(r["tipo"], data_bd_para_tela(r["data"]), dur, r["observacao"] or "-"))

    def _novo(self):
        if not self.entidade_id:
            messagebox.showwarning("Atenção", "Salve o cadastro antes de registrar atestados.")
            return
        self._abrir_formulario()

    def _abrir_formulario(self, atestado_id=None):
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Registrar Atestado / Declaração" if not atestado_id else "Editar Registro")
        win.geometry("560x480")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        dados = {
            "tipo": "Atestado",
            "data": date.today().strftime("%d/%m/%Y"),
            "duracao": "1",
            "unidade": "dias",
            "observacao": ""
        }
        if atestado_id:
            conn = get_connection()
            r = conn.execute("SELECT * FROM atestados WHERE id=?", (atestado_id,)).fetchone()
            conn.close()
            if r:
                dados = {
                    "tipo": r["tipo"],
                    "data": data_bd_para_tela(r["data"]),
                    "duracao": str(r["duracao"]),
                    "unidade": r["unidade_duracao"],
                    "observacao": r["observacao"] or ""
                }

        frame = ctk.CTkFrame(win, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(frame, text="Tipo de Registro", font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w")
        tipo_var = ctk.StringVar(value=dados["tipo"])
        tipo_menu = ctk.CTkOptionMenu(frame, values=["Atestado", "Declaração"], variable=tipo_var, width=200)
        tipo_menu.pack(anchor="w", pady=(2, 15))

        # Data e Duração na mesma linha
        f_linha1 = ctk.CTkFrame(frame, fg_color="transparent")
        f_linha1.pack(fill="x", pady=(0, 15))

        # Data
        f_data = ctk.CTkFrame(f_linha1, fg_color="transparent")
        f_data.pack(side="left")
        ctk.CTkLabel(f_data, text="Data", font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w")
        data_e = ctk.CTkEntry(f_data, width=130, placeholder_text="DD/MM/AAAA")
        data_e.insert(0, dados["data"])
        data_e.pack(anchor="w", pady=(2, 0))
        vincular_mascara(data_e, mascara_data)

        # Duração
        f_dur = ctk.CTkFrame(f_linha1, fg_color="transparent")
        f_dur.pack(side="left", padx=20)
        ctk.CTkLabel(f_dur, text="Duração", font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w")

        f_dur_in = ctk.CTkFrame(f_dur, fg_color="transparent")
        f_dur_in.pack(anchor="w", pady=(2, 0))

        dur_e = ctk.CTkEntry(f_dur_in, width=70)
        dur_e.insert(0, dados["duracao"])
        dur_e.pack(side="left")

        unid_var = ctk.StringVar(value=dados["unidade"])
        unid_menu = ctk.CTkOptionMenu(f_dur_in, values=["dias", "horas"], variable=unid_var, width=90)
        unid_menu.pack(side="left", padx=8)

        # Automatizar unidade baseada no tipo (apenas para novo registro)
        if not atestado_id:
            def atualizar_unidade(*_):
                unid_var.set("dias" if tipo_var.get() == "Atestado" else "horas")
            tipo_var.trace("w", atualizar_unidade)

        # Motivo / Afastamento
        ctk.CTkLabel(frame, text="Motivo / Tipo de Afastamento", font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w")
        opcoes_motivo = [
            "Decisão Médica", "INSS", "Maternidade", "Paternidade", "Luto",
            "Casamento", "Consulta Médica", "Exames", "Outros"
        ]
        motivo_var = ctk.StringVar(value=dados["observacao"] if dados["observacao"] in opcoes_motivo else "Decisão Médica")
        motivo_menu = ctk.CTkOptionMenu(frame, values=opcoes_motivo, variable=motivo_var, width=300)
        motivo_menu.pack(anchor="w", pady=(2, 15))

        ctk.CTkLabel(frame, text="Observações Adicionais", font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w")
        obs_txt = ctk.CTkTextbox(frame, height=100, width=480, border_width=1, border_color=CORES["borda"])
        # Se for editar e a obs não estiver no menu, colocar no textbox
        obs_inicial = dados["observacao"] if dados["observacao"] not in opcoes_motivo else ""
        obs_txt.insert("1.0", obs_inicial)
        obs_txt.pack(pady=(2, 10))

        def salvar():
            dur = dur_e.get().strip()
            if not dur:
                messagebox.showerror("Erro", "Informe a duração.", parent=win)
                return

            # Se selecionou "Outros" ou escreveu algo no texto, prioriza o texto se houver
            obs_final = motivo_var.get()
            texto_extra = obs_txt.get("1.0", "end-1c").strip()
            if texto_extra:
                obs_final = texto_extra if motivo_var.get() == "Outros" else f"{motivo_var.get()}: {texto_extra}"

            data_bd = data_tela_para_bd(data_e.get().strip())
            conn = get_connection()
            if atestado_id:
                conn.execute("UPDATE atestados SET tipo=?, data=?, duracao=?, unidade_duracao=?, observacao=? WHERE id=?",
                             (tipo_var.get(), data_bd, dur, unid_var.get(), obs_final, atestado_id))
            else:
                conn.execute("INSERT INTO atestados (entidade,entidade_id,tipo,data,duracao,unidade_duracao,observacao) VALUES (?,?,?,?,?,?,?)",
                            (self.entidade, self.entidade_id, tipo_var.get(), data_bd, dur, unid_var.get(), obs_final))
            conn.commit()
            conn.close()
            win.destroy()
            self.carregar()

        btn_f = ctk.CTkFrame(win, fg_color=CORES["card"], height=60)
        btn_f.pack(fill="x", side="bottom")
        btn_f.pack_propagate(False)

        ctk.CTkButton(btn_f, text="✖ Cancelar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=win.destroy, width=120, height=36).pack(side="right", padx=15, pady=12)
        ctk.CTkButton(btn_f, text="💾 Salvar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(12, "bold"), command=salvar, width=130, height=36).pack(side="right", padx=0, pady=12)

    def _remover(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um registro.")
            return
        if messagebox.askyesno("Confirmar", "Remover este registro?"):
            conn = get_connection()
            conn.execute("UPDATE atestados SET excluido=1 WHERE id=?", (int(sel[0]),))
            conn.commit()
            conn.close()
            self.carregar()

    def _ver_detalhe(self):
        sel = self.tree.selection()
        if not sel: return
        self._abrir_formulario(int(sel[0]))
