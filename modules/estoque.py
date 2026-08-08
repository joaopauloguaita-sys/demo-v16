import os
import sys
from datetime import date

import customtkinter as ctk
from tkinter import messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte, numero_por_extenso
import pdf_utils


class EstoqueModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._carrinho = {}  # item_id -> quantidade a pedir
        self._build_ui()
        self.carregar()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="📦 Controle de Materiais", font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(header, text="+ Adicionar Item", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=lambda: self._form_item(None),
                      width=160).pack(side="right", padx=15, pady=10)
        ctk.CTkButton(header, text="📄 PDF do Estoque", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                      font=fonte(12, "bold"), command=self.gerar_pdf_estoque,
                      width=160).pack(side="right", padx=(0, 5), pady=10)

        dica = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        dica.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(dica, text="💡 ➕ Entrada = chegou material novo (pode registrar em caixas/pacotes, "
                                 "o sistema calcula o total sozinho). ➖ Baixa = alguém pegou/usou o item "
                                 "(desconta do estoque automaticamente). 🛒 = colocar num pedido pra "
                                 "Secretaria de Educação. Itens em vermelho estão abaixo do mínimo.",
                     font=fonte(11), text_color=CORES["acento"], wraplength=950,
                     justify="left").pack(padx=15, pady=8, anchor="w")

        busca_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=8)
        busca_f.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(busca_f, text="🔍", text_color=CORES["subtexto"]).pack(side="left", padx=(15, 4), pady=8)
        self.busca_var = ctk.StringVar()
        self.busca_var.trace("w", lambda *a: self.carregar())
        ctk.CTkEntry(busca_f, textvariable=self.busca_var, placeholder_text="Buscar item...",
                     width=280).pack(side="left", pady=8)
        self.label_carrinho = ctk.CTkLabel(busca_f, text="🛒 Pedido: 0 itens",
                                            font=fonte(12, "bold"), text_color=CORES["acento"])
        self.label_carrinho.pack(side="right", padx=10)
        self.btn_gerar_pedido = ctk.CTkButton(busca_f, text="📝 Gerar Pedido", fg_color=CORES["perigo"],
                                               hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                                               font=fonte(12, "bold"), command=self.gerar_pedido,
                                               width=150, state="disabled")
        self.btn_gerar_pedido.pack(side="right", padx=10, pady=8)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(10, 15))

    def carregar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        busca = self.busca_var.get().strip()
        conn = get_connection()
        itens = conn.execute(
            "SELECT * FROM estoque_itens WHERE nome LIKE ? AND (excluido IS NULL OR excluido = 0) ORDER BY nome", (f"%{busca}%",)).fetchall()
        conn.close()

        if not itens:
            ctk.CTkLabel(self.scroll, text="Nenhum item cadastrado ainda.",
                         text_color=CORES["subtexto"]).pack(pady=30)
            return

        for item in itens:
            item = dict(item)
            baixo = (item["quantidade"] or 0) < (item["estoque_minimo"] or 0)
            linha = ctk.CTkFrame(self.scroll, fg_color=CORES["card"], corner_radius=8,
                                 border_width=2 if baixo else 0,
                                 border_color=CORES["perigo"] if baixo else None)
            linha.pack(fill="x", pady=3, padx=2)

            cor_nome = CORES["perigo"] if baixo else CORES["texto_card"]
            info_f = ctk.CTkFrame(linha, fg_color="transparent")
            info_f.pack(side="left", fill="x", expand=True, padx=12, pady=8)
            ctk.CTkLabel(info_f, text=item["nome"], font=fonte(13, "bold"),
                         text_color=cor_nome, anchor="w").pack(anchor="w")
            sub = f"{item['categoria'] or 'Sem categoria'}  •  Qtd: {item['quantidade'] or 0} {item['unidade'] or ''}" \
                  f"  •  Mínimo: {item['estoque_minimo'] or 0}"
            if baixo:
                sub += "  ⚠ ABAIXO DO MÍNIMO"
            ctk.CTkLabel(info_f, text=sub, font=fonte(11),
                         text_color=CORES["subtexto"], anchor="w").pack(anchor="w")

            btns = ctk.CTkFrame(linha, fg_color="transparent")
            btns.pack(side="right", padx=10, pady=6)
            no_carrinho = item["id"] in self._carrinho
            ctk.CTkButton(btns, text="➕", width=36, height=30, fg_color=CORES["sucesso"],
                          hover_color=CORES["sucesso_hover"], text_color=CORES["texto_claro"],
                          command=lambda it=item: self._entrada(it)).pack(side="left", padx=2)
            ctk.CTkButton(btns, text="➖", width=36, height=30, fg_color="#e67e22",
                          hover_color="#ca6510", text_color=CORES["texto_claro"],
                          command=lambda it=item: self._baixa(it)).pack(side="left", padx=2)
            ctk.CTkButton(btns, text=f"🛒{' ✓' if no_carrinho else ''}", width=50, height=30,
                          fg_color=CORES["acento"] if no_carrinho else CORES["primaria_clara"],
                          text_color=CORES["texto_claro"],
                          command=lambda it=item: self._adicionar_ao_pedido(it)).pack(side="left", padx=2)
            ctk.CTkButton(btns, text="✏", width=36, height=30, fg_color=CORES["dourado"],
                          hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                          command=lambda it=item: self._form_item(it)).pack(side="left", padx=2)
            ctk.CTkButton(btns, text="🗑", width=36, height=30, fg_color=CORES["perigo"],
                          hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                          command=lambda it=item: self._excluir(it)).pack(side="left", padx=2)

    def _entrada(self, item):
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title(f"Entrada — {item['nome']}")
        win.geometry("360x340")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        ctk.CTkLabel(win, text=f"➕ {item['nome']}", font=fonte(14, "bold"),
                     text_color=CORES["dourado"], wraplength=320).pack(pady=(20, 5))
        ctk.CTkLabel(win, text=f"Estoque atual: {item['quantidade'] or 0} {item['unidade'] or ''}",
                     font=fonte(11), text_color=CORES["subtexto"]).pack()

        ctk.CTkLabel(win, text="Chegou em pacotes/caixas? Preencha os dois campos abaixo.\n"
                                "Se for solto (unidade por unidade), só preencha o de baixo.",
                     font=fonte(10), text_color=CORES["subtexto"], wraplength=320,
                     justify="left").pack(pady=(10, 5))

        ctk.CTkLabel(win, text="Quantidade de pacotes/caixas:", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).pack(pady=(8, 2))
        e_pacotes = ctk.CTkEntry(win, width=120, justify="center", placeholder_text="Ex: 3")
        e_pacotes.pack()

        ctk.CTkLabel(win, text="Unidades por pacote (ou quantidade solta):", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).pack(pady=(8, 2))
        e_unid = ctk.CTkEntry(win, width=120, justify="center", placeholder_text="Ex: 6")
        e_unid.pack()

        def confirmar():
            try:
                pacotes = int(e_pacotes.get().strip() or 1)
                unid = int(e_unid.get().strip() or 0)
            except ValueError:
                messagebox.showerror("Erro", "Preencha com números.", parent=win)
                return
            total = pacotes * unid if e_pacotes.get().strip() else unid
            if total <= 0:
                messagebox.showerror("Erro", "Informe uma quantidade válida.", parent=win)
                return
            conn = get_connection()
            conn.execute("UPDATE estoque_itens SET quantidade = quantidade + ? WHERE id=?",
                        (total, item["id"]))
            conn.execute("INSERT INTO estoque_movimentacoes (item_id, tipo, quantidade, data, observacao) "
                        "VALUES (?, 'entrada', ?, ?, ?)",
                        (item["id"], total, date.today().isoformat(), f"{pacotes}x{unid}" if pacotes > 1 else ""))
            conn.commit()
            conn.close()
            win.destroy()
            self.carregar()

        ctk.CTkButton(win, text="✅ Confirmar Entrada", fg_color=CORES["sucesso"],
                      hover_color=CORES["sucesso_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=confirmar, width=220).pack(pady=20)

    def _baixa(self, item):
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title(f"Baixa — {item['nome']}")
        win.geometry("340x280")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        ctk.CTkLabel(win, text=f"➖ {item['nome']}", font=fonte(14, "bold"),
                     text_color=CORES["dourado"], wraplength=300).pack(pady=(20, 5))
        ctk.CTkLabel(win, text=f"Estoque atual: {item['quantidade'] or 0} {item['unidade'] or ''}",
                     font=fonte(11), text_color=CORES["subtexto"]).pack()

        ctk.CTkLabel(win, text="Quantidade retirada:", font=fonte(12, "bold"),
                     text_color=CORES["subtexto"]).pack(pady=(15, 2))
        e_qtd = ctk.CTkEntry(win, width=120, justify="center")
        e_qtd.pack()
        e_qtd.focus()

        ctk.CTkLabel(win, text="Para quem / motivo (opcional):", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).pack(pady=(10, 2))
        e_obs = ctk.CTkEntry(win, width=260)
        e_obs.pack()

        def confirmar():
            try:
                qtd = int(e_qtd.get().strip())
                if qtd <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erro", "Informe uma quantidade válida.", parent=win)
                return
            atual = item["quantidade"] or 0
            if qtd > atual and not messagebox.askyesno(
                    "Atenção", f"Só tem {atual} em estoque. Confirmar mesmo assim (vai ficar negativo)?",
                    parent=win):
                return
            conn = get_connection()
            conn.execute("UPDATE estoque_itens SET quantidade = quantidade - ? WHERE id=?",
                        (qtd, item["id"]))
            conn.execute("INSERT INTO estoque_movimentacoes (item_id, tipo, quantidade, data, observacao) "
                        "VALUES (?, 'saida', ?, ?, ?)",
                        (item["id"], qtd, date.today().isoformat(), e_obs.get().strip()))
            conn.commit()
            conn.close()
            win.destroy()
            self.carregar()

        ctk.CTkButton(win, text="✅ Confirmar Baixa", fg_color="#e67e22", hover_color="#ca6510",
                      text_color=CORES["texto_claro"], font=fonte(13, "bold"),
                      command=confirmar, width=220).pack(pady=15)

    def _excluir(self, item):
        if not messagebox.askyesno("Confirmar", f"Remover \"{item['nome']}\" do estoque?"):
            return
        conn = get_connection()
        conn.execute("UPDATE estoque_itens SET excluido=1 WHERE id=?", (item["id"],))
        conn.commit()
        conn.close()
        self._carrinho.pop(item["id"], None)
        self.carregar()

    # ------------------------------------------------------------ cadastro/edição
    def _form_item(self, item):
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Item do Estoque" if not item else f"Editar — {item['nome']}")
        win.geometry("380x600")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(win, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="📦 Item do Estoque", font=fonte(14, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        corpo = ctk.CTkFrame(win, fg_color=CORES["fundo"])
        corpo.pack(fill="both", expand=True, padx=25, pady=15)

        def campo(label, chave, largura=320, ph=""):
            ctk.CTkLabel(corpo, text=label, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).pack(anchor="w", pady=(6, 0))
            e = ctk.CTkEntry(corpo, width=largura, placeholder_text=ph)
            if item and item.get(chave) is not None:
                e.insert(0, str(item[chave]))
            e.pack(anchor="w", pady=(2, 0))
            return e

        e_nome = campo("Nome do Item *", "nome", ph="Ex: Caderno brochura 96 folhas")
        e_categoria = campo("Categoria", "categoria", ph="Ex: Material Escolar, Limpeza, Escritório")
        e_unidade = campo("Unidade", "unidade", largura=150, ph="Ex: unid., caixa, pacote")
        e_qtd = campo("Quantidade em Estoque", "quantidade", largura=150, ph="0")
        e_min = campo("Estoque Mínimo", "estoque_minimo", largura=150, ph="0")
        e_obs = campo("Observação", "observacao", ph="Opcional")

        def salvar():
            nome = e_nome.get().strip()
            if not nome:
                messagebox.showerror("Erro", "O nome é obrigatório!", parent=win)
                return
            try:
                qtd = int(e_qtd.get().strip() or 0)
                minimo = int(e_min.get().strip() or 0)
            except ValueError:
                messagebox.showerror("Erro", "Quantidade e Estoque Mínimo devem ser números.", parent=win)
                return

            conn = get_connection()
            if item:
                conn.execute(
                    "UPDATE estoque_itens SET nome=?, categoria=?, unidade=?, quantidade=?, "
                    "estoque_minimo=?, observacao=? WHERE id=?",
                    (nome, e_categoria.get().strip(), e_unidade.get().strip(), qtd, minimo,
                     e_obs.get().strip(), item["id"]))
            else:
                conn.execute(
                    "INSERT INTO estoque_itens (nome, categoria, unidade, quantidade, estoque_minimo, observacao) "
                    "VALUES (?,?,?,?,?,?)",
                    (nome, e_categoria.get().strip(), e_unidade.get().strip(), qtd, minimo,
                     e_obs.get().strip()))
            conn.commit()
            conn.close()
            win.destroy()
            self.carregar()

        ctk.CTkButton(corpo, text="💾 Salvar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=salvar, width=320, height=38).pack(pady=15)

    # ------------------------------------------------------------ pedido
    def _adicionar_ao_pedido(self, item):
        if item["id"] in self._carrinho:
            del self._carrinho[item["id"]]
            self.carregar()
            self._atualizar_carrinho()
            return

        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title(f"Pedir — {item['nome']}")
        win.geometry("340x220")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        ctk.CTkLabel(win, text=f"📝 {item['nome']}", font=fonte(14, "bold"),
                     text_color=CORES["dourado"], wraplength=300).pack(pady=(20, 5))
        ctk.CTkLabel(win, text=f"Estoque atual: {item['quantidade'] or 0} {item['unidade'] or ''}",
                     font=fonte(11), text_color=CORES["subtexto"]).pack()

        ctk.CTkLabel(win, text="Quantidade a pedir:", font=fonte(12, "bold"),
                     text_color=CORES["subtexto"]).pack(pady=(15, 2))
        e_qtd = ctk.CTkEntry(win, width=120, justify="center")
        e_qtd.pack()
        e_qtd.focus()

        def confirmar():
            try:
                qtd = int(e_qtd.get().strip())
                if qtd <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erro", "Informe uma quantidade válida.", parent=win)
                return
            self._carrinho[item["id"]] = {"nome": item["nome"], "unidade": item["unidade"] or "", "qtd": qtd}
            win.destroy()
            self.carregar()
            self._atualizar_carrinho()

        ctk.CTkButton(win, text="Adicionar ao Pedido", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=confirmar, width=220).pack(pady=15)

    def _atualizar_carrinho(self):
        n = len(self._carrinho)
        self.label_carrinho.configure(text=f"🛒 Pedido: {n} {'item' if n == 1 else 'itens'}")
        self.btn_gerar_pedido.configure(state="normal" if n else "disabled")

    def gerar_pedido(self):
        if not self._carrinho:
            return
        hoje = date.today()
        linhas = [["Item", "Quantidade", "Por Extenso", "Unidade"]]
        for dados in self._carrinho.values():
            linhas.append([dados["nome"], str(dados["qtd"]),
                           numero_por_extenso(dados["qtd"]).capitalize(), dados["unidade"]])

        blocos = [
            ("titulo", "Pedido de Materiais à Secretaria de Educação"),
            ("tabela", [["Data do Pedido", hoje.strftime("%d/%m/%Y")]]),
            ("tabela", linhas),
        ]
        try:
            caminho = pdf_utils.gerar_pdf("Pedido de Materiais", blocos,
                                          f"Pedido_{hoje.strftime('%Y%m%d')}.pdf")
            pdf_utils._abrir_arquivo(caminho)
            self._carrinho = {}
            self._atualizar_carrinho()
            self.carregar()
        except Exception as e:
            messagebox.showerror("Erro ao gerar PDF", str(e))

    def gerar_pdf_estoque(self):
        conn = get_connection()
        itens = conn.execute(
            "SELECT * FROM estoque_itens WHERE excluido IS NULL OR excluido = 0 ORDER BY categoria, nome"
        ).fetchall()
        conn.close()

        linhas = [["Item", "Categoria", "Qtd.", "Mínimo", "Unidade", "Situação"]]
        for it in itens:
            baixo = (it["quantidade"] or 0) < (it["estoque_minimo"] or 0)
            linhas.append([it["nome"], it["categoria"] or "-", str(it["quantidade"] or 0),
                           str(it["estoque_minimo"] or 0), it["unidade"] or "-",
                           "⚠ ABAIXO DO MÍNIMO" if baixo else "OK"])

        blocos = [("titulo", "Controle de Estoque — Secretaria"), ("tabela", linhas)]
        try:
            caminho = pdf_utils.gerar_pdf("Controle de Estoque", blocos, "Controle_de_Estoque.pdf")
            pdf_utils._abrir_arquivo(caminho)
        except Exception as e:
            messagebox.showerror("Erro ao gerar PDF", str(e))
