import base64
import io
import os
import sys
import uuid

import customtkinter as ctk
from tkinter import filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte

from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_GALERIA = os.path.join(BASE_DIR, "assets", "galeria")
TAMANHO_MINIATURA = (150, 150)
COLUNAS = 5


class GaleriaModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        os.makedirs(PASTA_GALERIA, exist_ok=True)
        self._build_ui()
        self.carregar()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🖼️ Galeria de Fotos", font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(header, text="+ Adicionar Foto", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=lambda: self._form(None),
                      width=160).pack(side="right", padx=15, pady=10)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        for c in range(COLUNAS):
            self.scroll.columnconfigure(c, weight=0, minsize=190)

    def carregar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        conn = get_connection()
        registros = conn.execute(
            "SELECT * FROM galeria_fotos WHERE excluido IS NULL OR excluido = 0 ORDER BY nome"
        ).fetchall()
        conn.close()

        if not registros:
            ctk.CTkLabel(self.scroll, text="Nenhuma foto cadastrada ainda. Clique em \"+ Adicionar Foto\".",
                         font=fonte(13), text_color=CORES["subtexto"]).grid(row=0, column=0, columnspan=4,
                                                                              pady=40)
            return

        for i, reg in enumerate(registros):
            self._card(dict(reg), i // COLUNAS, i % COLUNAS)

    def _garantir_arquivo_local(self, reg):
        """Se a foto veio sincronizada de outro PC (só tem o base64), recria o arquivo local."""
        nome_arquivo = reg.get("arquivo")
        caminho = os.path.join(PASTA_GALERIA, nome_arquivo) if nome_arquivo else None
        if caminho and os.path.exists(caminho):
            return caminho
        if reg.get("foto_base64"):
            try:
                dados_img = base64.b64decode(reg["foto_base64"])
                if not nome_arquivo:
                    nome_arquivo = f"{uuid.uuid4().hex}.jpg"
                    conn = get_connection()
                    conn.execute("UPDATE galeria_fotos SET arquivo=? WHERE id=?", (nome_arquivo, reg["id"]))
                    conn.commit()
                    conn.close()
                caminho = os.path.join(PASTA_GALERIA, nome_arquivo)
                with open(caminho, "wb") as f:
                    f.write(dados_img)
                return caminho
            except Exception:
                return None
        return None

    def _card(self, reg, row, col):
        card = ctk.CTkFrame(self.scroll, fg_color=CORES["card"], corner_radius=12,
                             border_width=1, border_color=CORES["borda"])
        card.grid(row=row, column=col, padx=8, pady=8, sticky="n")

        caminho_foto = self._garantir_arquivo_local(reg)
        img_label = None
        if caminho_foto and os.path.exists(caminho_foto):
            try:
                img = ctk.CTkImage(Image.open(caminho_foto), size=TAMANHO_MINIATURA)
                img_label = ctk.CTkLabel(card, image=img, text="", cursor="hand2")
                img_label.pack(padx=10, pady=(10, 6))
            except Exception:
                ctk.CTkLabel(card, text="📷", font=fonte(40)).pack(padx=10, pady=(20, 6))
        else:
            ctk.CTkLabel(card, text="📷", font=fonte(40)).pack(padx=10, pady=(20, 6))

        if img_label is not None and caminho_foto:
            img_label.bind("<Double-Button-1>", lambda e, c=caminho_foto, n=reg.get("nome", ""): self._visualizar_foto(c, n))

        ctk.CTkLabel(card, text=reg.get("nome", "") or "-", font=fonte(13, "bold"),
                     text_color=CORES["texto_claro"], wraplength=150).pack(padx=8)
        subtitulo = reg.get("cargo", "") or ""
        if reg.get("periodo"):
            subtitulo = f"{subtitulo} — {reg['periodo']}" if subtitulo else reg["periodo"]
        ctk.CTkLabel(card, text=subtitulo, font=fonte(10), text_color=CORES["subtexto"],
                     wraplength=150).pack(padx=8, pady=(0, 6))

        btn_f = ctk.CTkFrame(card, fg_color="transparent")
        btn_f.pack(pady=(0, 8))
        ctk.CTkButton(btn_f, text="✏", width=32, height=22, font=fonte(11),
                      fg_color=CORES["primaria_clara"], text_color=CORES["texto_claro"],
                      command=lambda r=reg: self._form(r)).pack(side="left", padx=3)
        ctk.CTkButton(btn_f, text="🗑", width=32, height=22, font=fonte(11),
                      fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"],
                      text_color=CORES["texto_claro"],
                      command=lambda r=reg: self._excluir(r)).pack(side="left", padx=3)

    def _visualizar_foto(self, caminho, nome=""):
        """Abre a foto em tamanho grande numa janela separada, com um X pra fechar."""
        try:
            img_original = Image.open(caminho)
        except Exception:
            return

        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title(nome or "Foto")
        win.grab_set()
        win.configure(fg_color="#111111")

        # Redimensiona mantendo proporção, respeitando um limite confortável de tela
        largura_max, altura_max = 900, 700
        w, h = img_original.size
        fator = min(largura_max / w, altura_max / h, 1)
        tam_final = (int(w * fator), int(h * fator))

        topo = ctk.CTkFrame(win, fg_color="#111111", corner_radius=0, height=40)
        topo.pack(fill="x")
        ctk.CTkButton(topo, text="✕ Fechar", width=90, height=28, fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=win.destroy).pack(side="right", padx=10, pady=6)

        img_grande = ctk.CTkImage(img_original, size=tam_final)
        lbl = ctk.CTkLabel(win, image=img_grande, text="")
        lbl.pack(padx=15, pady=15)
        win.bind("<Escape>", lambda e: win.destroy())

        win.update_idletasks()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        ww, wh = tam_final[0] + 30, tam_final[1] + 70
        win.geometry(f"{ww}x{wh}+{(sw - ww)//2}+{(sh - wh)//2}")

    def _excluir(self, reg):
        if not messagebox.askyesno("Confirmar", f"Remover a foto de {reg.get('nome', '')} da galeria?"):
            return
        conn = get_connection()
        conn.execute("UPDATE galeria_fotos SET excluido=1 WHERE id=?", (reg["id"],))
        conn.commit()
        conn.close()
        if reg.get("arquivo"):
            caminho = os.path.join(PASTA_GALERIA, reg["arquivo"])
            if os.path.exists(caminho):
                try:
                    os.remove(caminho)
                except Exception:
                    pass
        self.carregar()

    # ------------------------------------------------------------------ FORM
    def _form(self, reg):
        form = ctk.CTkToplevel(self.winfo_toplevel())
        form.title("Nova Foto" if not reg else "Editar Foto")
        form.geometry("420x560")
        form.grab_set()
        form.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(form, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="🖼️ Foto da Galeria", font=fonte(14, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        corpo = ctk.CTkFrame(form, fg_color=CORES["fundo"])
        corpo.pack(fill="both", expand=True, padx=20, pady=15)

        caminho_selecionado = {"valor": None}
        preview_label = ctk.CTkLabel(corpo, text="Nenhuma foto selecionada", font=fonte(11),
                                     text_color=CORES["subtexto"])

        def _mostrar_preview(caminho):
            try:
                img = ctk.CTkImage(Image.open(caminho), size=(160, 160))
                preview_label.configure(image=img, text="")
                preview_label.image = img
            except Exception:
                preview_label.configure(text="Não foi possível abrir essa imagem.", image=None)

        if reg:
            caminho_atual = self._garantir_arquivo_local(reg)
            if caminho_atual and os.path.exists(caminho_atual):
                _mostrar_preview(caminho_atual)

        preview_label.pack(pady=(0, 10))

        def selecionar_foto():
            caminho = filedialog.askopenfilename(
                title="Selecione a foto",
                filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp")])
            if caminho:
                caminho_selecionado["valor"] = caminho
                _mostrar_preview(caminho)

        ctk.CTkButton(corpo, text="📁 Selecionar Foto...", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      command=selecionar_foto).pack(pady=(0, 15))

        def lbl(t):
            ctk.CTkLabel(corpo, text=t, font=fonte(12, "bold"),
                         text_color=CORES["subtexto"]).pack(anchor="w", pady=(6, 0))

        lbl("Nome *")
        nome_e = ctk.CTkEntry(corpo, width=360)
        nome_e.insert(0, reg.get("nome", "") if reg else "")
        nome_e.pack(pady=(0, 4))

        lbl("Cargo")
        cargo_e = ctk.CTkEntry(corpo, width=360, placeholder_text="Ex: Diretor Escolar")
        cargo_e.insert(0, reg.get("cargo", "") if reg else "")
        cargo_e.pack(pady=(0, 4))

        lbl("Período (texto livre)")
        periodo_e = ctk.CTkEntry(corpo, width=360, placeholder_text="Ex: 2001 a 2004")
        periodo_e.insert(0, reg.get("periodo", "") if reg else "")
        periodo_e.pack(pady=(0, 4))

        def salvar():
            nome = nome_e.get().strip()
            if not nome:
                messagebox.showerror("Erro", "O nome é obrigatório!", parent=form)
                return
            if not reg and not caminho_selecionado["valor"]:
                messagebox.showerror("Erro", "Selecione uma foto!", parent=form)
                return

            nome_arquivo = reg.get("arquivo") if reg else None
            foto_b64 = reg.get("foto_base64") if reg else None

            if caminho_selecionado["valor"]:
                try:
                    img = Image.open(caminho_selecionado["valor"]).convert("RGB")
                    img.thumbnail((500, 500))
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=85)
                    dados_img = buffer.getvalue()

                    nome_arquivo = nome_arquivo or f"{uuid.uuid4().hex}.jpg"
                    with open(os.path.join(PASTA_GALERIA, nome_arquivo), "wb") as f:
                        f.write(dados_img)
                    foto_b64 = base64.b64encode(dados_img).decode("ascii")
                except Exception as e:
                    messagebox.showerror("Erro ao processar a foto", str(e), parent=form)
                    return

            conn = get_connection()
            try:
                if reg:
                    conn.execute(
                        "UPDATE galeria_fotos SET nome=?, cargo=?, periodo=?, arquivo=?, foto_base64=? WHERE id=?",
                        (nome, cargo_e.get().strip(), periodo_e.get().strip(), nome_arquivo, foto_b64, reg["id"]))
                else:
                    conn.execute(
                        "INSERT INTO galeria_fotos (nome, cargo, periodo, arquivo, foto_base64) VALUES (?,?,?,?,?)",
                        (nome, cargo_e.get().strip(), periodo_e.get().strip(), nome_arquivo, foto_b64))
                conn.commit()
                form.destroy()
                self.carregar()
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=form)
            finally:
                conn.close()

        btn_bar = ctk.CTkFrame(form, fg_color=CORES["card"], corner_radius=0, height=55)
        btn_bar.pack(fill="x", side="bottom")
        ctk.CTkButton(btn_bar, text="✖ Fechar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=form.destroy, width=110, height=36).pack(side="right", padx=10, pady=10)
        ctk.CTkButton(btn_bar, text="💾 Salvar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=salvar, width=130, height=36).pack(
                      side="right", padx=10, pady=10)
