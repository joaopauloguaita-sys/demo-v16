import os
import sys
import threading

import customtkinter as ctk
from tkinter import filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tema import CORES, fonte
from modules import rag


class BaseConhecimentoModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()
        self._atualizar_lista()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="📄 Base de Conhecimento da SofIA", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(header, text="+ Adicionar Documento", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=self.adicionar_arquivo,
                      width=190).pack(side="right", padx=15, pady=10)

        ctk.CTkLabel(self, text="Adicione PDFs, Word (.docx) ou TXT — regimento, PPP, normas da "
                                 "SEED-PR, etc. A SofIA vai consultar esses documentos antes de "
                                 "responder perguntas relacionadas, na aba \"Consulte a SofIA\".",
                     font=fonte(12), text_color=CORES["subtexto"],
                     wraplength=900, justify="left").pack(anchor="w", padx=25, pady=(10, 0))

        self.lbl_status = ctk.CTkLabel(self, text="", font=fonte(12, "bold"),
                                        text_color=CORES["acento"])
        self.lbl_status.pack(anchor="w", padx=25, pady=(4, 0))

        self.lista_frame = ctk.CTkScrollableFrame(self, fg_color=CORES["card"], corner_radius=12,
                                                    label_text="Documentos cadastrados",
                                                    label_font=fonte(12, "bold"))
        self.lista_frame.pack(fill="both", expand=True, padx=20, pady=15)

    def _atualizar_lista(self):
        for w in self.lista_frame.winfo_children():
            w.destroy()

        docs = rag.listar_documentos()
        if not docs:
            ctk.CTkLabel(self.lista_frame, text="Nenhum documento adicionado ainda.",
                         font=fonte(12), text_color=CORES["subtexto"]).pack(pady=15)
            return

        for nome in docs:
            linha = ctk.CTkFrame(self.lista_frame, fg_color=CORES["card_claro"], corner_radius=8)
            linha.pack(fill="x", pady=4, padx=4)
            ctk.CTkLabel(linha, text=f"📄 {nome}", font=fonte(12), anchor="w",
                         text_color=CORES["texto_card"]).pack(side="left", padx=12, pady=10)
            ctk.CTkButton(linha, text="🗑 Remover", width=90, height=28, font=fonte(11),
                          fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"],
                          text_color=CORES["texto_claro"],
                          command=lambda n=nome: self.remover(n)).pack(side="right", padx=12, pady=8)

    def adicionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione um documento",
            filetypes=[("Documentos suportados", "*.pdf *.docx *.txt")])
        if not caminho:
            return

        def processar():
            try:
                rag.adicionar_documento(caminho, callback_status=self._set_status)
                self.after(0, self._atualizar_lista)
                self.after(0, lambda: self._set_status("Pronto!"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Erro", f"Não foi possível processar o arquivo:\n{e}"))
                self.after(0, lambda: self._set_status(""))

        threading.Thread(target=processar, daemon=True).start()

    def _set_status(self, texto):
        self.lbl_status.configure(text=texto)

    def remover(self, nome):
        if not messagebox.askyesno("Confirmar", f"Remover \"{nome}\" da base de conhecimento?"):
            return
        rag.remover_documento(nome)
        self._atualizar_lista()
