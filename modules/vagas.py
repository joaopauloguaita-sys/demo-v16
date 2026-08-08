import os
import sys

import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte
from modules.matriculas_shared import listar_turmas_ordenadas, vagas_padrao_para


class VagasModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()
        self.carregar()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🎟️ Vagas para o Próximo Ano Letivo", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(header, text="🔄 Atualizar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(12, "bold"), command=self.carregar, width=130).pack(side="right", padx=15)

        dica = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        dica.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(dica, text="💡 O número de vagas totais já vem preenchido pela regra da SEED "
                                 "(Infantil 4/5: 20 | 1º ao 3º ano: 25 | 4º e 5º ano: 30), mas você "
                                 "pode ajustar se precisar. As vagas preenchidas contam os alunos já "
                                 "marcados como \"Matriculado\" na aba de Matrículas/Rematrículas.",
                     font=fonte(11), text_color=CORES["acento"], wraplength=950,
                     justify="left").pack(padx=15, pady=8, anchor="w")

        cabec = ctk.CTkFrame(self, fg_color=CORES["primaria"], corner_radius=8)
        cabec.pack(fill="x", padx=20, pady=(10, 0))
        for txt, w in [("Turma", 260), ("Vagas Totais", 130), ("Preenchidas", 110),
                       ("Restantes", 110), ("Pendentes", 110)]:
            ctk.CTkLabel(cabec, text=txt, font=fonte(11, "bold"), text_color=CORES["dourado"],
                         width=w, anchor="w").pack(side="left", padx=4, pady=8)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(5, 15))

    def carregar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        conn = get_connection()
        turmas = listar_turmas_ordenadas(conn)
        vagas_config = {v["turma_id"]: v["vagas_totais"] for v in
                        conn.execute("SELECT turma_id, vagas_totais FROM vagas_ano_letivo").fetchall()}
        contagens = conn.execute("""
            SELECT turma_destino_id, status, COUNT(*) as qtd
            FROM matriculas_proximo_ano
            WHERE excluido IS NULL OR excluido = 0
            GROUP BY turma_destino_id, status
        """).fetchall()
        conn.close()

        cont_por_turma = {}
        for c in contagens:
            cont_por_turma.setdefault(c["turma_destino_id"], {})[c["status"]] = c["qtd"]

        for turma in turmas:
            total = vagas_config.get(turma["id"]) or vagas_padrao_para(turma["nome_completo"])
            preenchidas = cont_por_turma.get(turma["id"], {}).get("matriculado", 0)
            pendentes = cont_por_turma.get(turma["id"], {}).get("pendente", 0)
            restantes = total - preenchidas

            linha = ctk.CTkFrame(self.scroll, fg_color=CORES["card"], corner_radius=8)
            linha.pack(fill="x", pady=2)

            ctk.CTkLabel(linha, text=f"{turma['nome_completo']} ({turma['turno']})", width=260,
                         anchor="w", font=fonte(12, "bold"),
                         text_color=CORES["texto_card"]).pack(side="left", padx=4, pady=8)

            e_total = ctk.CTkEntry(linha, width=100)
            e_total.insert(0, str(total))
            e_total.pack(side="left", padx=30, pady=4)

            def salvar_total(turma_id=turma["id"], widget=e_total):
                try:
                    novo_total = int(widget.get().strip())
                except ValueError:
                    return
                conn2 = get_connection()
                existe = conn2.execute("SELECT id FROM vagas_ano_letivo WHERE turma_id=?",
                                       (turma_id,)).fetchone()
                if existe:
                    conn2.execute("UPDATE vagas_ano_letivo SET vagas_totais=? WHERE turma_id=?",
                                  (novo_total, turma_id))
                else:
                    conn2.execute("INSERT INTO vagas_ano_letivo (turma_id, vagas_totais) VALUES (?,?)",
                                  (turma_id, novo_total))
                conn2.commit()
                conn2.close()
                self.carregar()

            e_total.bind("<Return>", lambda e, f=salvar_total: f())
            e_total.bind("<FocusOut>", lambda e, f=salvar_total: f())

            ctk.CTkLabel(linha, text=str(preenchidas), width=90, anchor="w",
                         text_color=CORES["sucesso"], font=fonte(12, "bold")).pack(side="left", padx=20)
            cor_restante = CORES["perigo"] if restantes <= 0 else CORES["texto_card"]
            ctk.CTkLabel(linha, text=str(restantes), width=90, anchor="w",
                         text_color=cor_restante, font=fonte(12, "bold")).pack(side="left", padx=20)
            ctk.CTkLabel(linha, text=str(pendentes), width=90, anchor="w",
                         text_color=CORES["dourado_escuro"] if "dourado_escuro" in CORES else CORES["dourado"],
                         font=fonte(12, "bold")).pack(side="left", padx=20)
