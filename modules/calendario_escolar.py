import base64
import os
import sys

import customtkinter as ctk
from tkinter import filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte

from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_CALENDARIO = os.path.join(BASE_DIR, "assets", "calendario")
ARQUIVO_LOCAL = os.path.join(PASTA_CALENDARIO, "calendario.png")
LARGURA_MAXIMA_EXIBICAO = 980


class CalendarioEscolarModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        os.makedirs(PASTA_CALENDARIO, exist_ok=True)
        self._build_ui()
        self._garantir_arquivo_local()
        self._exibir_calendario()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="📅 Calendário Escolar", font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(header, text="🔄 Carregar / Trocar Calendário", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=self.carregar_novo,
                      width=230).pack(side="right", padx=15, pady=10)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        self.lbl_imagem = ctk.CTkLabel(self.scroll, text="", fg_color=CORES["card"], corner_radius=12)
        self.lbl_imagem.pack(padx=10, pady=10)

    # ------------------------------------------------------------ dados
    def _garantir_arquivo_local(self):
        """Se o calendário só existir sincronizado (base64) de outro PC, recria o arquivo local."""
        if os.path.exists(ARQUIVO_LOCAL):
            return
        conn = get_connection()
        row = conn.execute("SELECT calendario_base64 FROM dados_escola LIMIT 1").fetchone()
        conn.close()
        if row and row["calendario_base64"]:
            try:
                with open(ARQUIVO_LOCAL, "wb") as f:
                    f.write(base64.b64decode(row["calendario_base64"]))
            except Exception:
                pass

    def _exibir_calendario(self):
        if not os.path.exists(ARQUIVO_LOCAL):
            self.lbl_imagem.configure(
                image=None,
                text="Nenhum calendário carregado ainda.\nClique em \"Carregar / Trocar Calendário\".",
                font=fonte(14), text_color=CORES["subtexto"], width=800, height=400)
            return
        try:
            img = Image.open(ARQUIVO_LOCAL)
            largura, altura = img.size
            if largura > LARGURA_MAXIMA_EXIBICAO:
                fator = LARGURA_MAXIMA_EXIBICAO / largura
                largura, altura = int(largura * fator), int(altura * fator)
            ctk_img = ctk.CTkImage(img, size=(largura, altura))
            self.lbl_imagem.configure(image=ctk_img, text="", width=largura, height=altura)
            self.lbl_imagem.image = ctk_img
        except Exception as e:
            self.lbl_imagem.configure(image=None, text=f"Não foi possível abrir o calendário:\n{e}",
                                       font=fonte(12), text_color=CORES["perigo"])

    # ------------------------------------------------------------ ações
    def carregar_novo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o calendário (PDF ou imagem)",
            filetypes=[("PDF ou imagem", "*.pdf *.jpg *.jpeg *.png"), ("PDF", "*.pdf"),
                       ("Imagem", "*.jpg *.jpeg *.png")])
        if not caminho:
            return

        try:
            ext = os.path.splitext(caminho)[1].lower()
            if ext == ".pdf":
                import fitz  # PyMuPDF
                doc = fitz.open(caminho)
                pagina = doc[0]
                pix = pagina.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                doc.close()
            else:
                img = Image.open(caminho).convert("RGB")

            # Evita imagens gigantes no banco - máximo 2000px no maior lado
            maior_lado = max(img.size)
            if maior_lado > 2000:
                fator = 2000 / maior_lado
                img = img.resize((int(img.width * fator), int(img.height * fator)))

            img.save(ARQUIVO_LOCAL, format="PNG", optimize=True)

            with open(ARQUIVO_LOCAL, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            conn = get_connection()
            conn.execute("UPDATE dados_escola SET calendario_base64=?", (b64,))
            conn.commit()
            conn.close()

            self._exibir_calendario()
            messagebox.showinfo("Sucesso", "Calendário atualizado!")
        except ImportError:
            messagebox.showerror(
                "Biblioteca faltando",
                "Para carregar um PDF é necessário o PyMuPDF (pymupdf). "
                "Se o problema persistir, tente selecionar uma imagem (JPG/PNG) em vez do PDF.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar o calendário:\n{e}")
