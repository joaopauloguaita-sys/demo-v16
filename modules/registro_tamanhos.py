import os
import sys

import customtkinter as ctk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte
import pdf_utils

CALCADO_OPCOES = [""] + [str(n) for n in range(24, 45)]
ROUPA_OPCOES = ["", "2", "4", "6", "8", "10", "12", "14", "16", "P", "M", "G", "GG", "XG"]


def _calcular_imc(peso_txt, altura_txt):
    """Calcula o IMC a partir de textos livres de peso (kg) e altura (cm ou m)."""
    import re
    try:
        peso = float(re.sub(r"[^0-9,\.]", "", peso_txt or "").replace(",", "."))
        altura = float(re.sub(r"[^0-9,\.]", "", altura_txt or "").replace(",", "."))
        if not peso or not altura:
            return ""
        if altura > 3:  # veio em cm
            altura = altura / 100
        imc = peso / (altura ** 2)
        if imc <= 0 or imc > 100:
            return ""
        return f"{imc:.1f}"
    except Exception:
        return ""


class RegistroTamanhosModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._campos = {}  # aluno_id -> dict de widgets
        self._build_ui()
        self.carregar_turmas()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="📏 Medidas Individuais", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        ctk.CTkLabel(header, text="Turma:", text_color=CORES["subtexto"]).pack(side="left", padx=(20, 5))
        self.turma_var = ctk.StringVar()
        self.turma_combo = ctk.CTkOptionMenu(header, variable=self.turma_var,
                                              command=lambda _: self.carregar_alunos(),
                                              width=220, values=[""])
        self.turma_combo.pack(side="left", padx=5)

        ctk.CTkButton(header, text="📄 Gerar PDF desta Turma", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                      font=fonte(12, "bold"), command=self.gerar_pdf, width=190).pack(side="right", padx=(5, 15))
        ctk.CTkButton(header, text="💾 Salvar Tudo", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=self.salvar, width=140).pack(side="right", padx=5)

        dica = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        dica.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(dica, text="💡 Escolha a turma, preencha os tamanhos de cada aluno e clique em "
                                 "\"Salvar Tudo\" (salva a turma inteira de uma vez). Útil para "
                                 "organizar doações e pedidos de uniforme.",
                     font=fonte(11), text_color=CORES["acento"], wraplength=950,
                     justify="left").pack(padx=15, pady=8, anchor="w")

        cabec = ctk.CTkFrame(self, fg_color=CORES["primaria"], corner_radius=8)
        cabec.pack(fill="x", padx=20, pady=(10, 0))
        for txt, w in [("Aluno", 240), ("Calçado", 90), ("Calça/Saia", 90),
                       ("Camiseta", 90), ("Blusa", 90), ("Peso", 80), ("Altura", 80), ("IMC", 70)]:
            ctk.CTkLabel(cabec, text=txt, font=fonte(11, "bold"), text_color=CORES["dourado"],
                         width=w, anchor="w").pack(side="left", padx=4, pady=8)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(5, 15))

    def carregar_turmas(self):
        conn = get_connection()
        turmas = conn.execute(
            "SELECT nome_completo FROM turmas WHERE ativo=1 AND (tipo IS NULL OR tipo != 'contraturno') "
            "ORDER BY nome_completo").fetchall()
        conn.close()
        nomes = [t["nome_completo"] for t in turmas]
        self.turma_combo.configure(values=nomes or [""])
        if nomes:
            self.turma_var.set(nomes[0])
            self.carregar_alunos()

    def carregar_alunos(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._campos = {}

        nome_turma = self.turma_var.get()
        if not nome_turma:
            return

        conn = get_connection()
        turma = conn.execute("SELECT id FROM turmas WHERE nome_completo=?", (nome_turma,)).fetchone()
        if not turma:
            conn.close()
            return
        alunos = conn.execute(
            "SELECT id, nome FROM alunos WHERE turma_id=? AND ativo=1 AND arquivado=0 ORDER BY nome",
            (turma["id"],)).fetchall()
        registros = {r["aluno_id"]: r for r in conn.execute(
            "SELECT * FROM registro_tamanhos WHERE aluno_id IN "
            f"({','.join('?' * len(alunos))})", [a["id"] for a in alunos]).fetchall()} if alunos else {}
        conn.close()

        if not alunos:
            ctk.CTkLabel(self.scroll, text="Nenhum aluno ativo nesta turma.",
                         text_color=CORES["subtexto"]).pack(pady=20)
            return

        for aluno in alunos:
            reg = registros.get(aluno["id"])
            linha = ctk.CTkFrame(self.scroll, fg_color=CORES["card"], corner_radius=8)
            linha.pack(fill="x", pady=2)

            ctk.CTkLabel(linha, text=aluno["nome"], width=260, anchor="w",
                         text_color=CORES["texto_card"]).pack(side="left", padx=4, pady=6)

            campos = {}
            for chave, opcoes, largura in [("calcado", CALCADO_OPCOES, 100), ("calca_saia", ROUPA_OPCOES, 100),
                                            ("camiseta", ROUPA_OPCOES, 100), ("blusa", ROUPA_OPCOES, 100)]:
                var = ctk.StringVar(value=(reg[chave] if reg and reg[chave] else ""))
                ctk.CTkOptionMenu(linha, variable=var, values=opcoes, width=largura - 15,
                                  font=fonte(11)).pack(side="left", padx=4, pady=4)
                campos[chave] = var

            for chave, largura in [("peso", 80), ("altura", 80)]:
                e = ctk.CTkEntry(linha, width=largura - 15, placeholder_text="kg" if chave == "peso" else "cm")
                if reg and reg[chave]:
                    e.insert(0, reg[chave])
                e.pack(side="left", padx=4, pady=4)
                campos[chave] = e

            lbl_imc = ctk.CTkLabel(linha, text=_calcular_imc(campos["peso"].get(), campos["altura"].get()),
                                   width=55, font=fonte(11, "bold"), text_color=CORES["subtexto"])
            lbl_imc.pack(side="left", padx=4, pady=4)

            def _atualiza_imc(event, p=campos["peso"], a=campos["altura"], lbl=lbl_imc):
                lbl.configure(text=_calcular_imc(p.get(), a.get()))

            campos["peso"].bind("<KeyRelease>", _atualiza_imc)
            campos["altura"].bind("<KeyRelease>", _atualiza_imc)

            self._campos[aluno["id"]] = campos

    def salvar(self):
        if not self._campos:
            messagebox.showwarning("Atenção", "Nenhum aluno carregado.")
            return
        conn = get_connection()
        for aluno_id, campos in self._campos.items():
            valores = {}
            for chave, widget in campos.items():
                valores[chave] = widget.get().strip() if hasattr(widget, "get") else ""
            ex = conn.execute("SELECT id FROM registro_tamanhos WHERE aluno_id=?", (aluno_id,)).fetchone()
            if ex:
                conn.execute(
                    "UPDATE registro_tamanhos SET calcado=?, calca_saia=?, camiseta=?, blusa=?, peso=?, altura=? "
                    "WHERE aluno_id=?",
                    (valores["calcado"], valores["calca_saia"], valores["camiseta"], valores["blusa"],
                     valores["peso"], valores["altura"], aluno_id))
            else:
                conn.execute(
                    "INSERT INTO registro_tamanhos (aluno_id, calcado, calca_saia, camiseta, blusa, peso, altura) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (aluno_id, valores["calcado"], valores["calca_saia"], valores["camiseta"],
                     valores["blusa"], valores["peso"], valores["altura"]))
        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Medidas salvas com sucesso!")

    def gerar_pdf(self):
        self.salvar()
        nome_turma = self.turma_var.get()
        conn = get_connection()
        turma = conn.execute("SELECT id FROM turmas WHERE nome_completo=?", (nome_turma,)).fetchone()
        alunos = conn.execute(
            "SELECT a.nome, r.calcado, r.calca_saia, r.camiseta, r.blusa, r.peso, r.altura "
            "FROM alunos a LEFT JOIN registro_tamanhos r ON r.aluno_id = a.id "
            "WHERE a.turma_id=? AND a.ativo=1 AND a.arquivado=0 ORDER BY a.nome",
            (turma["id"],)).fetchall() if turma else []
        conn.close()

        linhas = [["Aluno", "Calçado", "Calça/Saia", "Camiseta", "Blusa", "Peso", "Altura"]]
        for a in alunos:
            linhas.append([a["nome"], a["calcado"] or "-", a["calca_saia"] or "-",
                           a["camiseta"] or "-", a["blusa"] or "-", a["peso"] or "-", a["altura"] or "-"])

        blocos = [("titulo", f"Registro de Tamanhos — {nome_turma}"), ("tabela", linhas)]
        try:
            caminho = pdf_utils.gerar_pdf(f"Registro de Tamanhos - {nome_turma}", blocos,
                                          f"Tamanhos_{nome_turma.replace(' ', '_')}.pdf")
            pdf_utils._abrir_arquivo(caminho)
        except Exception as e:
            messagebox.showerror("Erro ao gerar PDF", str(e))
