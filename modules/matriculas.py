import os
import subprocess
import sys

import customtkinter as ctk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte
from modules.matriculas_shared import listar_turmas_ordenadas

URL_SERE = "https://www.sere.pr.gov.br/sere/"
CAMINHOS_CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


class MatriculasModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()
        self.carregar()

    def _build_ui(self):
        topo = ctk.CTkFrame(self, fg_color=CORES["primaria"], corner_radius=12)
        topo.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(topo, text="📝 Matrículas e Rematrículas", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(topo, text="🖥️ AUXILIAR NO SERE", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                      font=fonte(13, "bold"), command=self.abrir_sere_dividido,
                      width=200, height=40).pack(side="right", padx=20, pady=10)

        dica = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        dica.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(dica, text="💡 Clique em \"AUXILIAR NO SERE\" pra abrir o SERE ao lado do sistema, "
                                 "lado a lado. Use \"📋 Copiar CGM\" em cada aluno e cole direto no SERE "
                                 "pra fazer a matrícula/rematrícula. Marque a situação de cada um "
                                 "conforme for confirmando.",
                     font=fonte(11), text_color=CORES["acento"], wraplength=950,
                     justify="left").pack(padx=15, pady=8, anchor="w")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(10, 15))

    def abrir_sere_dividido(self):
        import tempfile

        root = self.winfo_toplevel()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        metade = w // 2

        chrome_path = next((p for p in CAMINHOS_CHROME if os.path.exists(p)), None)
        if chrome_path:
            try:
                # Perfil temporário exclusivo: garante que o Chrome abra uma janela
                # REALMENTE nova (não reaproveita uma já aberta), senão o tamanho e
                # a posição pedidos são ignorados.
                perfil_temp = os.path.join(tempfile.gettempdir(), "chrome_sere_dividido")
                subprocess.Popen([
                    chrome_path,
                    f"--user-data-dir={perfil_temp}",
                    "--new-window",
                    f"--window-position={metade},0",
                    f"--window-size={w - metade},{h}",
                    URL_SERE,
                ])

                # "Desmaximiza" a janela do sistema antes de redimensionar - se ela
                # estiver em modo "zoomed" (tela cheia), o Windows ignora geometry()
                try:
                    root.state("normal")
                except Exception:
                    pass
                root.update_idletasks()
                root.geometry(f"{metade}x{h}+0+0")
                root.lift()
                root.focus_force()
            except Exception as e:
                messagebox.showerror("Erro", f"Não consegui abrir o Chrome automaticamente:\n{e}")
        else:
            import webbrowser
            webbrowser.open(URL_SERE)
            messagebox.showinfo(
                "Chrome não encontrado automaticamente",
                "Abri o SERE no seu navegador padrão, mas não consegui posicionar as telas "
                "lado a lado automaticamente porque não achei o Google Chrome instalado no "
                "local de costume. Você pode arrastar as janelas manualmente lado a lado.")

    def copiar_cgm(self, cgm):
        self.clipboard_clear()
        self.clipboard_append(cgm)
        self.update()

    def carregar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        conn = get_connection()
        turmas = listar_turmas_ordenadas(conn)
        registros = conn.execute("""
            SELECT m.id as matricula_id, m.status, m.observacao, m.turma_destino_id,
                   a.id as aluno_id, a.nome, a.cgm
            FROM matriculas_proximo_ano m
            JOIN alunos a ON a.id = m.aluno_id
            WHERE m.excluido IS NULL OR m.excluido = 0
        """).fetchall()
        conn.close()

        por_turma = {}
        for r in registros:
            por_turma.setdefault(r["turma_destino_id"], []).append(r)

        algum = False
        for turma in turmas:
            regs = sorted(por_turma.get(turma["id"], []), key=lambda r: r["nome"])
            if not regs:
                continue
            algum = True
            ctk.CTkLabel(self.scroll, text=f"🏫 {turma['nome_completo']} ({turma['turno']}) — {len(regs)} aluno(s)",
                         font=fonte(14, "bold"), text_color=CORES["dourado"]).pack(anchor="w", pady=(15, 5))

            for reg in regs:
                linha = ctk.CTkFrame(self.scroll, fg_color=CORES["card"], corner_radius=8)
                linha.pack(fill="x", pady=3)

                linha1 = ctk.CTkFrame(linha, fg_color="transparent")
                linha1.pack(fill="x", padx=12, pady=(8, 2))

                info_f = ctk.CTkFrame(linha1, fg_color="transparent")
                info_f.pack(side="left")
                ctk.CTkLabel(info_f, text=reg["nome"], font=fonte(12, "bold"), width=220, anchor="w",
                             text_color=CORES["texto_card"]).pack(anchor="w")
                cgm_txt = reg["cgm"] if reg["cgm"] else "incluir novo"
                ctk.CTkLabel(info_f, text=f"CGM: {cgm_txt}", font=fonte(10),
                             text_color=CORES["subtexto"]).pack(anchor="w")

                if reg["cgm"]:
                    ctk.CTkButton(linha1, text="📋 Copiar CGM", width=110, height=28, font=fonte(10),
                                  fg_color=CORES["primaria_clara"], text_color=CORES["texto_claro"],
                                  command=lambda c=reg["cgm"]: self.copiar_cgm(c)).pack(side="left", padx=8)

                status_var = ctk.StringVar(value=reg["status"] or "pendente")
                radios_f = ctk.CTkFrame(linha1, fg_color="transparent")
                radios_f.pack(side="left", padx=12)

                linha2 = ctk.CTkFrame(linha, fg_color="transparent")
                linha2.pack(fill="x", padx=12, pady=(2, 8))

                obs_e = ctk.CTkEntry(linha2, width=260, placeholder_text="Motivo da pendência...")
                if reg["observacao"]:
                    obs_e.insert(0, reg["observacao"])
                obs_e.configure(state="normal" if status_var.get() == "pendente" else "disabled")
                obs_e.pack(side="left")
                obs_e.bind("<KeyRelease>", lambda e, mid=reg["matricula_id"], widget=obs_e:
                          self._salvar_observacao(mid, widget))

                def salvar_status(matricula_id=reg["matricula_id"], var=status_var, obs_widget=obs_e):
                    obs_widget.configure(state="normal" if var.get() == "pendente" else "disabled")
                    conn2 = get_connection()
                    conn2.execute("UPDATE matriculas_proximo_ano SET status=?, observacao=? WHERE id=?",
                                  (var.get(), obs_widget.get().strip() if var.get() == "pendente" else "",
                                   matricula_id))
                    conn2.commit()
                    conn2.close()

                for valor, texto, cor in [("matriculado", "Matriculado", CORES["sucesso"]),
                                           ("pendente", "Pendente", CORES["dourado"]),
                                           ("nao_matriculado", "Não Matriculado", CORES["perigo"])]:
                    ctk.CTkRadioButton(radios_f, text=texto, variable=status_var, value=valor,
                                       text_color=CORES["texto_card"], fg_color=cor,
                                       command=salvar_status, font=fonte(10)).pack(side="left", padx=4)

                ctk.CTkButton(linha2, text="🗑 Remover da Lista", width=150, height=28, font=fonte(10),
                              fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"],
                              text_color=CORES["texto_claro"],
                              command=lambda mid=reg["matricula_id"], nome=reg["nome"]:
                              self._remover(mid, nome)).pack(side="right")

        if not algum:
            ctk.CTkLabel(self.scroll, text="Nenhum aluno enviado para matrícula/rematrícula ainda.\n"
                                            "Vá até a ficha de um aluno e clique em \"Matrícula/Rematrícula\".",
                         text_color=CORES["subtexto"], font=fonte(12), justify="center").pack(pady=40)

    def _remover(self, matricula_id, nome):
        if not messagebox.askyesno("Confirmar",
                                    f"Remover {nome} da lista de Matrículas/Rematrículas?\n\n"
                                    "Use isso quando o aluno não vai mais ser matriculado aqui "
                                    "(foi pra outra escola, mudou de município, etc). O cadastro "
                                    "do aluno em si NÃO é apagado, só sai desta lista."):
            return
        conn = get_connection()
        conn.execute("UPDATE matriculas_proximo_ano SET excluido=1 WHERE id=?", (matricula_id,))
        conn.commit()
        conn.close()
        self.carregar()

    def _salvar_observacao(self, matricula_id, widget):
        conn = get_connection()
        conn.execute("UPDATE matriculas_proximo_ano SET observacao=? WHERE id=?",
                    (widget.get().strip(), matricula_id))
        conn.commit()
        conn.close()
