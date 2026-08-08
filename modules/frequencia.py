import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte, vincular_mascara, mascara_data, data_bd_para_tela, data_tela_para_bd
import pdf_utils

class FrequenciaModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.turma_id = None
        self.presencas = {}
        self._build_ui()
        self.carregar_turmas()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="✅ Frequência / Chamada", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        f_right = ctk.CTkFrame(header, fg_color="transparent")
        f_right.pack(side="right", padx=15, pady=10)
        ctk.CTkLabel(f_right, text="Turma:", text_color=CORES["subtexto"]).pack(side="left", padx=5)
        self.turma_var = ctk.StringVar()
        self.turma_combo = ctk.CTkOptionMenu(f_right, variable=self.turma_var,
                                              command=self.ao_mudar_turma, width=160, values=[""])
        self.turma_combo.pack(side="left", padx=5)
        ctk.CTkLabel(f_right, text="Disciplina:", text_color=CORES["subtexto"]).pack(side="left", padx=5)
        self.disc_var = ctk.StringVar()
        self.disc_combo = ctk.CTkOptionMenu(f_right, variable=self.disc_var, width=150, values=[""])
        self.disc_combo.pack(side="left", padx=5)
        ctk.CTkLabel(f_right, text="Data:", text_color=CORES["subtexto"]).pack(side="left", padx=5)
        self.data_entry = ctk.CTkEntry(f_right, width=110, placeholder_text="DD/MM/AAAA")
        self.data_entry.insert(0, data_bd_para_tela(str(date.today())))
        vincular_mascara(self.data_entry, mascara_data)
        self.data_entry.pack(side="left", padx=5)
        ctk.CTkButton(f_right, text="🔄 Carregar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      command=self.carregar_chamada, width=110).pack(side="left", padx=5)

        leg = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=8)
        leg.pack(fill="x", padx=20, pady=(8, 0))
        ctk.CTkLabel(leg, text="✅ Presente   ❌ Falta   📝 Justificada",
                     text_color=CORES["subtexto"]).pack(side="left", padx=15, pady=8)
        self.label_resumo = ctk.CTkLabel(leg, text="", text_color=CORES["subtexto"])
        self.label_resumo.pack(side="right", padx=20)

        dica = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        dica.pack(fill="x", padx=20, pady=(6, 0))
        ctk.CTkLabel(dica, text="💡 Como usar: escolha Turma, Disciplina e a Data no topo, clique "
                                 "\"🔄 Carregar\" e marque a presença de cada aluno na lista abaixo. "
                                 "Para CORRIGIR um dia já lançado: escolha a mesma data antiga, clique "
                                 "Carregar de novo (os valores salvos aparecem), ajuste e clique "
                                 "\"💾 Salvar Chamada\" — ou use o botão \"✏ Corrigir 1 Falta\" para "
                                 "mudar só um aluno rapidamente.",
                     font=fonte(11), text_color=CORES["acento"], wraplength=950,
                     justify="left").pack(padx=15, pady=8, anchor="w")

        self.chamada_scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["card"], corner_radius=12)
        self.chamada_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkButton(btn_frame, text="💾 Salvar Chamada", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=self.salvar_chamada, width=180, height=40).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="✅ Todos Presentes", fg_color=CORES["primaria_clara"],
                      text_color=CORES["texto_claro"], command=self.marcar_todos_presentes, width=170, height=40).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="📈 Ver Histórico", fg_color=CORES["secundaria"],
                      text_color=CORES["texto_claro"], command=self.ver_historico, width=150, height=40).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📄 PDF Frequência", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                      font=fonte(12, "bold"), command=self.pdf_frequencia, width=160, height=40).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏ Corrigir 1 Falta", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      font=fonte(12, "bold"), command=self.corrigir_falta_individual,
                      width=170, height=40).pack(side="left", padx=5)

    def carregar_turmas(self):
        conn = get_connection()
        turmas = conn.execute("SELECT id, nome_completo FROM turmas WHERE ativo=1 ORDER BY nome_completo").fetchall()
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
        discs = conn.execute("SELECT id, nome FROM disciplinas WHERE turma_id=? AND (excluido IS NULL OR excluido=0) ORDER BY nome", (self.turma_id,)).fetchall()
        conn.close()
        self.discs_dict = {d["nome"]: d["id"] for d in discs}
        nomes = list(self.discs_dict.keys())
        self.disc_combo.configure(values=nomes if nomes else ["(Nenhuma)"])
        if nomes:
            self.disc_var.set(nomes[0])
        self.carregar_chamada()

    def carregar_chamada(self):
        for w in self.chamada_scroll.winfo_children():
            w.destroy()
        self.presencas = {}
        if not self.turma_id:
            return
        disc_id = self.discs_dict.get(self.disc_var.get()) if hasattr(self, "discs_dict") else None
        data_str = data_tela_para_bd(self.data_entry.get().strip())
        conn = get_connection()
        alunos = conn.execute("SELECT id, nome FROM alunos WHERE (turma_id=? OR turma_contraturno_id=?) AND ativo=1 AND arquivado=0 ORDER BY nome",
                              (self.turma_id, self.turma_id)).fetchall()

        hdr = ctk.CTkFrame(self.chamada_scroll, fg_color=CORES["primaria"], corner_radius=6)
        hdr.pack(fill="x", padx=5, pady=(5, 2))
        for txt, w in [("#", 40), ("Nome do Aluno", 280), ("Presença", 130), ("Observação", 200)]:
            ctk.CTkLabel(hdr, text=txt, width=w, font=fonte(13, "bold"),
                         text_color=CORES["texto_claro"]).pack(side="left", padx=5, pady=6)

        for i, aluno in enumerate(alunos):
            freq = conn.execute("SELECT * FROM frequencia WHERE aluno_id=? AND disciplina_id=? AND data=?",
                                (aluno["id"], disc_id, data_str)).fetchone() if disc_id and data_str else None
            row_bg = CORES["card"] if i % 2 == 0 else CORES["card_claro"]
            row = ctk.CTkFrame(self.chamada_scroll, fg_color=row_bg, corner_radius=4)
            row.pack(fill="x", padx=5, pady=1)
            ctk.CTkLabel(row, text=str(i + 1), width=40, text_color=CORES["subtexto"]).pack(side="left", padx=5, pady=6)
            ctk.CTkLabel(row, text=aluno["nome"], width=280, anchor="w",
                         text_color=CORES["texto"]).pack(side="left", padx=5)
            presente_val = "✅" if (not freq or freq["presente"]) else ("📝" if freq and freq["justificada"] else "❌")
            presenca_var = ctk.StringVar(value=presente_val)
            seg = ctk.CTkSegmentedButton(row, values=["✅", "❌", "📝"], width=130, variable=presenca_var,
                                          selected_color=CORES["acento"], selected_hover_color=CORES["acento_hover"])
            seg.pack(side="left", padx=10, pady=4)
            obs_e = ctk.CTkEntry(row, width=200, placeholder_text="Observação...")
            obs_e.insert(0, freq["observacao"] or "" if freq else "")
            obs_e.pack(side="left", padx=5, pady=4)
            self.presencas[aluno["id"]] = {"var": presenca_var, "obs": obs_e}

        conn.close()
        self.label_resumo.configure(text=f"{len(alunos)} alunos | {data_str}")

    def marcar_todos_presentes(self):
        for p in self.presencas.values():
            p["var"].set("✅")

    def salvar_chamada(self):
        if not self.turma_id:
            messagebox.showwarning("Atenção", "Selecione uma turma.")
            return
        disc_id = self.discs_dict.get(self.disc_var.get()) if hasattr(self, "discs_dict") else None
        if not disc_id:
            messagebox.showwarning("Atenção", "Selecione uma disciplina.")
            return
        data_tela = self.data_entry.get().strip()
        if not data_tela:
            messagebox.showwarning("Atenção", "Informe a data.")
            return
        data_str = data_tela_para_bd(data_tela)
        conn = get_connection()
        try:
            for aluno_id, dados in self.presencas.items():
                val = dados["var"].get()
                presente = 1 if val == "✅" else 0
                justificada = 1 if val == "📝" else 0
                obs = dados["obs"].get()
                ex = conn.execute("SELECT id FROM frequencia WHERE aluno_id=? AND disciplina_id=? AND data=?",
                                  (aluno_id, disc_id, data_str)).fetchone()
                if ex:
                    conn.execute("UPDATE frequencia SET presente=?, justificada=?, observacao=? WHERE aluno_id=? AND disciplina_id=? AND data=?",
                                (presente, justificada, obs, aluno_id, disc_id, data_str))
                else:
                    conn.execute("INSERT INTO frequencia (aluno_id, disciplina_id, data, presente, justificada, observacao) VALUES (?,?,?,?,?,?)",
                                (aluno_id, disc_id, data_str, presente, justificada, obs))
            conn.commit()
            messagebox.showinfo("Sucesso", f"Chamada salva para {data_tela}!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            conn.close()

    def ver_historico(self):
        if not self.turma_id:
            messagebox.showwarning("Atenção", "Selecione uma turma.")
            return
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Histórico de Frequência")
        win.geometry("760x500")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(win, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="📈 Histórico de Frequência", font=fonte(14, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        frame = ctk.CTkFrame(win, fg_color=CORES["card"], corner_radius=12)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        conn = get_connection()
        resumo = conn.execute("""
            SELECT a.id, a.nome, a.cgm,
                COUNT(f.id) total_aulas,
                SUM(f.presente) presentes,
                SUM(CASE WHEN f.presente=0 AND f.justificada=0 THEN 1 ELSE 0 END) faltas,
                SUM(f.justificada) justificadas,
                ROUND(SUM(f.presente)*100.0/NULLIF(COUNT(f.id),0),1) percentual
            FROM alunos a
            LEFT JOIN frequencia f ON f.aluno_id=a.id
            WHERE a.turma_id=? AND a.ativo=1 AND a.arquivado=0
            GROUP BY a.id ORDER BY a.nome
        """, (self.turma_id,)).fetchall()
        conn.close()

        ctk.CTkLabel(win, text="💡 Dê 2 cliques em um aluno para ver todos os dias registrados "
                                "e poder corrigir ou apagar faltas lançadas por engano.",
                     font=fonte(11), text_color=CORES["acento"]).pack(pady=(0, 4))

        cols = ("nome", "cgm", "aulas", "presentes", "faltas", "justif", "pct")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        for col, (txt, w) in {"nome": ("Aluno", 220), "cgm": ("CGM", 90), "aulas": ("Aulas", 60),
                               "presentes": ("Pres.", 60), "faltas": ("Faltas", 60),
                               "justif": ("Justif.", 60), "pct": ("% Freq.", 80)}.items():
            tree.heading(col, text=txt, anchor="w")
            tree.column(col, width=w, anchor="center" if col != "nome" else "w")
        for r in resumo:
            pct = r["percentual"] or 0
            tag = "critico" if pct < 75 else "ok"
            tree.insert("", "end", iid=str(r["id"]),
                        values=(r["nome"], r["cgm"] or "-", r["total_aulas"] or 0,
                                r["presentes"] or 0, r["faltas"] or 0,
                                r["justificadas"] or 0, f"{pct}%"), tags=(tag,))
        tree.tag_configure("critico", foreground="#c0392b")
        tree.tag_configure("ok", foreground="#17a589")
        tree.bind("<Double-1>", lambda e: self._detalhe_aluno(int(tree.selection()[0]),
                                                                 tree.item(tree.selection()[0])["values"][0],
                                                                 win) if tree.selection() else None)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scroll.pack(side="right", fill="y", pady=5)

        ctk.CTkLabel(win, text="⚠ Vermelho = frequência abaixo de 75%",
                     text_color=CORES["aviso"]).pack(pady=5)
        ctk.CTkButton(win, text="✖ Fechar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=win.destroy).pack(pady=5)

    def _detalhe_aluno(self, aluno_id, nome_aluno, janela_pai):
        conn = get_connection()
        registros = conn.execute("""
            SELECT f.id, f.data, f.presente, f.justificada, f.observacao, d.nome as disciplina
            FROM frequencia f
            LEFT JOIN disciplinas d ON d.id = f.disciplina_id
            WHERE f.aluno_id = ? AND (f.excluido IS NULL OR f.excluido = 0)
            ORDER BY f.data DESC
        """, (aluno_id,)).fetchall()
        conn.close()

        win = ctk.CTkToplevel(janela_pai)
        win.title(f"Dias registrados — {nome_aluno}")
        win.geometry("640x520")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(win, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text=f"📋 {nome_aluno}", font=fonte(14, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        ctk.CTkLabel(win, text="💡 Clique em ✅ ❌ 📝 pra mudar a situação daquele dia (salva na hora), "
                                "ou em 🗑 pra apagar o registro inteiro.",
                     font=fonte(11), text_color=CORES["acento"], wraplength=600,
                     justify="left").pack(padx=15, pady=(10, 4), anchor="w")

        scroll = ctk.CTkScrollableFrame(win, fg_color=CORES["card"], corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=15, pady=10)

        def recarregar():
            for w in scroll.winfo_children():
                w.destroy()
            conn2 = get_connection()
            regs = conn2.execute("""
                SELECT f.id, f.data, f.presente, f.justificada, f.observacao, d.nome as disciplina
                FROM frequencia f
                LEFT JOIN disciplinas d ON d.id = f.disciplina_id
                WHERE f.aluno_id = ? AND (f.excluido IS NULL OR f.excluido = 0)
                ORDER BY f.data DESC
            """, (aluno_id,)).fetchall()
            conn2.close()

            if not regs:
                ctk.CTkLabel(scroll, text="Nenhum dia registrado para este aluno.",
                             text_color=CORES["subtexto"], font=fonte(12)).pack(pady=20)
                return

            for reg in regs:
                linha = ctk.CTkFrame(scroll, fg_color=CORES["card_claro"], corner_radius=8)
                linha.pack(fill="x", pady=3, padx=4)

                ctk.CTkLabel(linha, text=data_bd_para_tela(reg["data"]), width=100, font=fonte(12, "bold"),
                             text_color=CORES["texto_card"]).pack(side="left", padx=(10, 5), pady=8)
                ctk.CTkLabel(linha, text=reg["disciplina"] or "-", width=140,
                             text_color=CORES["subtexto"]).pack(side="left", padx=5)

                status_atual = "📝" if reg["justificada"] else ("✅" if reg["presente"] else "❌")
                status_var = ctk.StringVar(value=status_atual)

                def salvar_status(reg_id=reg["id"], var=status_var):
                    val = var.get()
                    presente = 1 if val == "✅" else 0
                    justificada = 1 if val == "📝" else 0
                    conn3 = get_connection()
                    conn3.execute("UPDATE frequencia SET presente=?, justificada=? WHERE id=?",
                                  (presente, justificada, reg_id))
                    conn3.commit()
                    conn3.close()

                seg = ctk.CTkSegmentedButton(linha, values=["✅", "❌", "📝"], variable=status_var,
                                              width=140, selected_color=CORES["acento"],
                                              selected_hover_color=CORES["acento_hover"],
                                              command=lambda _v, f=salvar_status: f())
                seg.pack(side="left", padx=10, pady=4)

                def excluir(reg_id=reg["id"]):
                    if not messagebox.askyesno("Confirmar", "Apagar este registro de frequência?",
                                                parent=win):
                        return
                    conn4 = get_connection()
                    conn4.execute("UPDATE frequencia SET excluido=1 WHERE id=?", (reg_id,))
                    conn4.commit()
                    conn4.close()
                    recarregar()

                ctk.CTkButton(linha, text="🗑", width=36, height=28, fg_color=CORES["perigo"],
                              hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                              command=excluir).pack(side="right", padx=10, pady=6)

        recarregar()

        ctk.CTkButton(win, text="✖ Fechar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=lambda: [win.destroy(), self.carregar_chamada()]).pack(pady=10)

    def corrigir_falta_individual(self):
        if not self.turma_id:
            messagebox.showwarning("Atenção", "Selecione uma turma primeiro.")
            return
        disc_id = self.discs_dict.get(self.disc_var.get()) if hasattr(self, "discs_dict") else None
        if not disc_id:
            messagebox.showwarning("Atenção", "Selecione uma disciplina primeiro.")
            return

        conn = get_connection()
        alunos = conn.execute(
            "SELECT id, nome FROM alunos WHERE (turma_id=? OR turma_contraturno_id=?) AND ativo=1 AND arquivado=0 ORDER BY nome",
            (self.turma_id, self.turma_id)).fetchall()
        conn.close()
        if not alunos:
            messagebox.showwarning("Atenção", "Nenhum aluno encontrado nesta turma.")
            return
        alunos_dict = {a["nome"]: a["id"] for a in alunos}

        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Corrigir Falta de um Aluno")
        win.geometry("400x340")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(win, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="✏ Corrigir Falta de um Aluno", font=fonte(13, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        corpo = ctk.CTkFrame(win, fg_color=CORES["fundo"])
        corpo.pack(fill="both", expand=True, padx=25, pady=15)

        ctk.CTkLabel(corpo, text=f"Disciplina: {self.disc_var.get()}", font=fonte(11),
                     text_color=CORES["subtexto"]).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(corpo, text="Aluno", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).pack(anchor="w")
        aluno_var = ctk.StringVar(value=list(alunos_dict.keys())[0])
        ctk.CTkOptionMenu(corpo, variable=aluno_var, values=list(alunos_dict.keys()),
                          width=320).pack(anchor="w", pady=(2, 10))

        ctk.CTkLabel(corpo, text="Data (DD/MM/AAAA)", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).pack(anchor="w")
        data_e = ctk.CTkEntry(corpo, width=160, placeholder_text="DD/MM/AAAA")
        data_e.insert(0, self.data_entry.get().strip() or data_bd_para_tela(str(date.today())))
        vincular_mascara(data_e, mascara_data)
        data_e.pack(anchor="w", pady=(2, 10))

        status_var = ctk.StringVar(value="✅")
        ctk.CTkLabel(corpo, text="Situação nesse dia", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).pack(anchor="w")
        seg = ctk.CTkSegmentedButton(corpo, values=["✅", "❌", "📝"], variable=status_var,
                                      selected_color=CORES["acento"],
                                      selected_hover_color=CORES["acento_hover"], width=200)
        seg.pack(anchor="w", pady=(4, 15))

        def buscar_atual():
            aluno_id = alunos_dict[aluno_var.get()]
            data_str = data_tela_para_bd(data_e.get().strip())
            if not data_str:
                return
            conn2 = get_connection()
            freq = conn2.execute(
                "SELECT * FROM frequencia WHERE aluno_id=? AND disciplina_id=? AND data=?",
                (aluno_id, disc_id, data_str)).fetchone()
            conn2.close()
            if freq:
                status_var.set("📝" if freq["justificada"] else ("✅" if freq["presente"] else "❌"))
            else:
                status_var.set("✅")

        buscar_atual()

        def salvar():
            aluno_id = alunos_dict[aluno_var.get()]
            data_tela = data_e.get().strip()
            if not data_tela:
                messagebox.showerror("Erro", "Informe a data.", parent=win)
                return
            data_str = data_tela_para_bd(data_tela)
            val = status_var.get()
            presente = 1 if val == "✅" else 0
            justificada = 1 if val == "📝" else 0
            conn2 = get_connection()
            ex = conn2.execute(
                "SELECT id FROM frequencia WHERE aluno_id=? AND disciplina_id=? AND data=?",
                (aluno_id, disc_id, data_str)).fetchone()
            if ex:
                conn2.execute(
                    "UPDATE frequencia SET presente=?, justificada=? WHERE aluno_id=? AND disciplina_id=? AND data=?",
                    (presente, justificada, aluno_id, disc_id, data_str))
            else:
                conn2.execute(
                    "INSERT INTO frequencia (aluno_id, disciplina_id, data, presente, justificada, observacao) "
                    "VALUES (?,?,?,?,?,'')",
                    (aluno_id, disc_id, data_str, presente, justificada))
            conn2.commit()
            conn2.close()
            messagebox.showinfo("Sucesso", "Frequência corrigida!", parent=win)
            win.destroy()
            self.carregar_chamada()

        ctk.CTkButton(corpo, text="💾 Salvar Correção", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=salvar, width=320, height=38).pack(pady=6)

    def pdf_frequencia(self):
        if not self.turma_id:
            messagebox.showwarning("Atenção", "Selecione uma turma.")
            return
        conn = get_connection()
        turma = conn.execute("SELECT nome_completo FROM turmas WHERE id=?", (self.turma_id,)).fetchone()
        resumo = conn.execute("""
            SELECT a.nome, COUNT(f.id) total, SUM(f.presente) presentes,
                   SUM(CASE WHEN f.presente=0 AND f.justificada=0 THEN 1 ELSE 0 END) faltas,
                   ROUND(SUM(f.presente)*100.0/NULLIF(COUNT(f.id),0),1) pct
            FROM alunos a LEFT JOIN frequencia f ON f.aluno_id=a.id
            WHERE a.turma_id=? AND a.ativo=1 AND a.arquivado=0
            GROUP BY a.id ORDER BY a.nome
        """, (self.turma_id,)).fetchall()
        conn.close()

        linhas = [["Aluno", "Total Aulas", "Presentes", "Faltas", "Frequência"]]
        for r in resumo:
            linhas.append([r["nome"], str(r["total"] or 0), str(r["presentes"] or 0),
                           str(r["faltas"] or 0), f"{r['pct'] or 0}%"])
        blocos = [
            ("titulo", f"Turma: {turma['nome_completo'] if turma else '-'}"),
            ("tabela", linhas),
        ]
        pdf_utils.salvar_pdf_como("Frequência por Turma", blocos,
                                   f"Frequencia_{(turma['nome_completo'] if turma else 'turma').replace(' ', '_')}.pdf",
                                   parent=self)
