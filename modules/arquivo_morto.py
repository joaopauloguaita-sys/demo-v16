"""
Arquivo Morto — lista registros arquivados.
Duplo clique ou botão abre a ficha completa.
Botão Excluir Definitivamente remove permanentemente.
CORREÇÃO: usa apenas pack() — sem mistura com grid().
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection, nome_seguro
from tema import CORES, fonte, data_bd_para_tela


def _validar_tabela(tabela):
    if not nome_seguro(tabela):
        raise ValueError(f"Nome de tabela inválido: {tabela!r}")


class ArquivoMortoModule(ctk.CTkFrame):
    """
    tabela        : 'alunos', 'professores', 'funcionarios', 'pedagogas', 'secretarios', 'diretores'
    titulo        : texto do cabeçalho
    icone         : emoji
    campo_nome    : coluna de nome (sempre 'nome')
    form_callback : função(parent, id, reativando=True, on_close=fn) que abre a ficha
    """
    def __init__(self, parent, tabela, titulo, icone,
                 campo_nome="nome", form_callback=None):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.tabela        = tabela
        self.titulo        = titulo
        self.icone         = icone
        self.campo_nome    = campo_nome
        self.form_callback = form_callback
        self._build_ui()
        self.carregar()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        # ── Cabeçalho ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))

        ctk.CTkLabel(header,
                     text=f"🗄 Arquivo Morto — {self.titulo}",
                     font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        self.label_total = ctk.CTkLabel(header, text="",
                                         text_color=CORES["subtexto"])
        self.label_total.pack(side="right", padx=20)

        # ── Busca ──────────────────────────────────────────────────────────
        busca_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        busca_f.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(busca_f, text="🔍",
                     text_color=CORES["subtexto"]).pack(side="left", padx=(15, 4), pady=10)
        self.busca_var = ctk.StringVar()
        self.busca_var.trace("w", lambda *a: self.carregar())
        ctk.CTkEntry(busca_f, textvariable=self.busca_var,
                     placeholder_text="Buscar pelo nome...",
                     width=300).pack(side="left", pady=10)

        # ── Aviso de uso ───────────────────────────────────────────────────
        aviso = ctk.CTkFrame(self, fg_color=CORES["card_claro"], corner_radius=8)
        aviso.pack(fill="x", padx=20, pady=(8, 0))
        ctk.CTkLabel(aviso,
                     text="💡  Dê DUPLO CLIQUE em um nome para abrir a ficha completa e reativar o cadastro.",
                     font=fonte(11), text_color=CORES["dourado"]).pack(padx=15, pady=8)

        # ── Tabela ─────────────────────────────────────────────────────────
        tabela_frame = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        tabela_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("nome", "cargo_turma", "data_arquivamento")
        self.tree = ttk.Treeview(tabela_frame, columns=cols,
                                  show="headings", height=20)

        self.tree.heading("nome",              text="Nome",          anchor="w")
        self.tree.column ("nome",              width=320, anchor="w")
        self.tree.heading("cargo_turma",       text="Cargo / Turma", anchor="w")
        self.tree.column ("cargo_turma",       width=220, anchor="w")
        self.tree.heading("data_arquivamento", text="Arquivado em",  anchor="w")
        self.tree.column ("data_arquivamento", width=130, anchor="w")

        scr = ttk.Scrollbar(tabela_frame, orient="vertical",
                             command=self.tree.yview)
        self.tree.configure(yscrollcommand=scr.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scr.pack(side="right", fill="y", pady=5)

        self.tree.bind("<Double-1>", lambda e: self._abrir_ficha())

        # ── Botões de ação ─────────────────────────────────────────────────
        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(btn_f,
                      text="📂 Abrir Ficha / Reativar",
                      fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"],
                      text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"),
                      command=self._abrir_ficha,
                      width=220, height=40).pack(side="left", padx=5)

        ctk.CTkButton(btn_f,
                      text="🗑 Excluir Definitivamente",
                      fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"],
                      text_color=CORES["texto_claro"],
                      font=fonte(12, "bold"),
                      command=self._excluir_definitivo,
                      width=220, height=40).pack(side="left", padx=10)

        ctk.CTkButton(btn_f,
                      text="🌐 Abrir Pasta (Google Drive)",
                      fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"],
                      text_color=CORES["sidebar"],
                      font=fonte(12, "bold"),
                      command=self._abrir_pasta_drive,
                      width=240, height=40).pack(side="right", padx=5)

    # ------------------------------------------------------------------ DADOS
    def carregar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        busca = self.busca_var.get().strip()
        conn  = get_connection()

        try:
            # Coluna extra: cargo para pessoas funcionais, turma para alunos
            if self.tabela == "alunos":
                rows = conn.execute(f"""
                    SELECT a.id, a.{self.campo_nome} as nome,
                           t.nome_completo as extra,
                           a.data_arquivamento
                    FROM {self.tabela} a
                    LEFT JOIN turmas t ON a.turma_id = t.id
                    WHERE a.arquivado = 1
                      AND a.{self.campo_nome} LIKE ?
                    ORDER BY a.{self.campo_nome}
                """, (f"%{busca}%",)).fetchall()
            else:
                rows = conn.execute(f"""
                    SELECT id,
                           {self.campo_nome} as nome,
                           COALESCE(cargo, '') as extra,
                           data_arquivamento
                    FROM {self.tabela}
                    WHERE arquivado = 1
                      AND {self.campo_nome} LIKE ?
                    ORDER BY {self.campo_nome}
                """, (f"%{busca}%",)).fetchall()
        except Exception as e:
            conn.close()
            # Se a tabela não existir ainda, mostrar aviso amigável
            ctk.CTkLabel(self, text=f"⚠ Nenhum registro arquivado ainda.\n({e})",
                         font=fonte(14), text_color=CORES["subtexto"]).pack(expand=True)
            return

        conn.close()

        for r in rows:
            data_fmt = data_bd_para_tela(r["data_arquivamento"]) if r["data_arquivamento"] else "-"
            self.tree.insert("", "end", iid=r["id"],
                             values=(r["nome"],
                                     r["extra"] or "-",
                                     data_fmt))

        total = len(rows)
        self.label_total.configure(
            text=f"Total arquivado: {total}" if total > 0
                 else "Nenhum registro arquivado")

    # ------------------------------------------------------------------ AÇÕES
    def _abrir_ficha(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção",
                                   "Selecione um registro para abrir.")
            return
        registro_id = int(sel[0])

        if self.form_callback:
            self.form_callback(self, registro_id,
                               reativando=True, on_close=self.carregar)
        else:
            # Fallback simples
            if messagebox.askyesno("Reativar", "Deseja reativar este cadastro?"):
                _validar_tabela(self.tabela)
                conn = get_connection()
                conn.execute(
                    f"UPDATE {self.tabela} SET arquivado=0, ativo=1, "
                    f"data_arquivamento=NULL WHERE id=?",
                    (registro_id,))
                conn.commit()
                conn.close()
                self.carregar()
                messagebox.showinfo("Sucesso", "Cadastro reativado!")

    def _excluir_definitivo(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção",
                                   "Selecione um registro para excluir.")
            return

        registro_id = int(sel[0])
        nome = self.tree.item(sel[0])["values"][0]

        # Primeira confirmação
        if not messagebox.askyesno(
            "⚠ Excluir Definitivamente",
            f"ATENÇÃO: Esta ação é IRREVERSÍVEL!\n\n"
            f"Deseja excluir permanentemente:\n\n"
            f"  {nome}\n\n"
            f"Todos os dados serão apagados para sempre.",
            icon="warning"
        ):
            return

        # Segunda confirmação — segurança extra
        if not messagebox.askyesno(
            "Confirmar exclusão permanente",
            f"Tem certeza absoluta?\n\n"
            f"'{nome}' será excluído e NÃO poderá ser recuperado.",
            icon="warning"
        ):
            return

        conn = get_connection()
        try:
            # Remover registros relacionados
            conn.execute(
                "DELETE FROM ocorrencias WHERE entidade=? AND entidade_id=?",
                (self.tabela, registro_id))
            conn.execute(
                "DELETE FROM atestados WHERE entidade=? AND entidade_id=?",
                (self.tabela, registro_id))

            if self.tabela == "alunos":
                conn.execute("DELETE FROM frequencia WHERE aluno_id=?",
                             (registro_id,))
                conn.execute("DELETE FROM notas WHERE aluno_id=?",
                             (registro_id,))
                conn.execute(
                    "DELETE FROM matriculas_contraturno WHERE aluno_id=?",
                    (registro_id,))

            # Excluir o registro principal
            _validar_tabela(self.tabela)
            conn.execute(f"DELETE FROM {self.tabela} WHERE id=?",
                         (registro_id,))
            conn.commit()
            messagebox.showinfo(
                "Excluído",
                f"Cadastro de '{nome}' excluído permanentemente.")
            self.carregar()

        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            conn.close()

    def _abrir_pasta_drive(self):
        _validar_tabela(self.tabela)
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um registro para abrir a pasta.")
            return
        
        reg_id = int(sel[0])
        conn = get_connection()
        try:
            _validar_tabela(self.tabela)
            r = conn.execute(f"SELECT pasta_documentos FROM {self.tabela} WHERE id=?", (reg_id,)).fetchone()
            if r and r["pasta_documentos"]:
                from tema import abrir_link
                abrir_link(r["pasta_documentos"])
            else:
                messagebox.showinfo("Informação", "Este registro não possui link da pasta do Google Drive cadastrado.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao acessar link: {e}")
        finally:
            conn.close()
