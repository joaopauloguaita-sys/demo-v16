"""
Arquivo Morto unificado para Diretores(as), Pedagogas, Secretário(a) e
Funcionários — mesmo espírito do "Gestão e Equipe": um bloco por categoria,
cabeçalho amarelo, lista compacta. Cada linha tem "♻ Reativar" (abre a ficha
de reativação, igual antes) e "🗑 Excluir Definitivamente" (apaga de vez,
com confirmação).
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import get_connection, nome_seguro
from tema import CORES, fonte, abrir_link


class ArquivoMortoEquipeModule(ctk.CTkFrame):
    """
    tabelas: lista de tuplas (tabela, titulo, icone)
    on_reativar(tabela, titulo, icone, reg_id): callback pra abrir a ficha de reativação
    """
    def __init__(self, parent, tabelas, on_reativar):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.tabelas = tabelas
        self.on_reativar = on_reativar
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🗄 Arquivo Morto — Gestão e Equipe", font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)
        self.carregar()

    def carregar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        for tabela, titulo, icone in self.tabelas:
            card = ctk.CTkFrame(self.scroll, fg_color=CORES["card"], corner_radius=14)
            card.pack(fill="x", pady=(0, 18))

            bloco_header = ctk.CTkFrame(card, fg_color=CORES["dourado"], corner_radius=10, height=40)
            bloco_header.pack(fill="x", padx=15, pady=(15, 8))
            bloco_header.pack_propagate(False)
            ctk.CTkLabel(bloco_header, text=f"{icone} {titulo}", font=fonte(15, "bold"),
                         text_color=CORES["sidebar"]).pack(side="left", padx=15, pady=6)

            if not nome_seguro(tabela):
                continue
            conn = get_connection()
            regs = conn.execute(
                f"SELECT * FROM {tabela} WHERE arquivado=1 ORDER BY nome"
            ).fetchall()
            conn.close()

            lista_f = ctk.CTkFrame(card, fg_color="transparent")
            lista_f.pack(fill="x", padx=15, pady=(0, 15))

            if not regs:
                ctk.CTkLabel(lista_f, text=f"Nenhum(a) {titulo.lower()} no arquivo morto.",
                             text_color=CORES["subtexto"], font=fonte(11)).pack(anchor="w", pady=8)
                continue

            for reg in regs:
                linha = ctk.CTkFrame(lista_f, fg_color=CORES["card_claro"], corner_radius=8)
                linha.pack(fill="x", pady=2)

                info = ctk.CTkFrame(linha, fg_color="transparent")
                info.pack(side="left", padx=10, pady=6, fill="x", expand=True)
                nome_val = reg["nome"] if "nome" in reg.keys() else "-"
                cargo_val = reg["cargo"] if "cargo" in reg.keys() and reg["cargo"] else "-"
                ctk.CTkLabel(info, text=nome_val, font=fonte(12, "bold"), anchor="w",
                             text_color=CORES["texto_card"]).pack(anchor="w")
                ctk.CTkLabel(info, text=cargo_val, font=fonte(10),
                             text_color=CORES["subtexto"]).pack(anchor="w")

                btns = ctk.CTkFrame(linha, fg_color="transparent")
                btns.pack(side="right", padx=8, pady=6)
                pasta_val = reg["pasta_documentos"] if "pasta_documentos" in reg.keys() else None
                ctk.CTkButton(btns, text="📁 Abrir Pasta (Drive)", width=150, height=26, font=fonte(10, "bold"),
                              fg_color=CORES["dourado"], hover_color=CORES["dourado_hover"],
                              text_color=CORES["sidebar"],
                              state="normal" if pasta_val else "disabled",
                              command=lambda p=pasta_val: abrir_link(p) if p else None
                              ).pack(side="left", padx=3)
                ctk.CTkButton(btns, text="♻ Reativar", width=90, height=26, font=fonte(10, "bold"),
                              fg_color=CORES["acento"], hover_color=CORES["acento_hover"],
                              text_color=CORES["texto_claro"],
                              command=lambda t=tabela, ti=titulo, ic=icone, rid=reg["id"]:
                                  self.on_reativar(t, ti, ic, rid)
                              ).pack(side="left", padx=3)
                ctk.CTkButton(btns, text="🗑 Excluir Definitivamente", width=170, height=26, font=fonte(10),
                              fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"],
                              text_color=CORES["texto_claro"],
                              command=lambda t=tabela, rid=reg["id"], n=nome_val:
                                  self._excluir_definitivo(t, rid, n)
                              ).pack(side="left", padx=3)

    def _excluir_definitivo(self, tabela, reg_id, nome):
        if not messagebox.askyesno(
                "Excluir definitivamente",
                f"Isso vai apagar {nome} PERMANENTEMENTE, sem possibilidade de recuperar.\n\n"
                "Tem certeza que quer continuar?"):
            return
        if not nome_seguro(tabela):
            return
        conn = get_connection()
        conn.execute(f"DELETE FROM {tabela} WHERE id=?", (reg_id,))
        conn.commit()
        conn.close()
        self.carregar()
