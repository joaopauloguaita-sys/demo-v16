import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte
from auth_utils import gerar_hash_senha, parece_hash_bcrypt

PERFIS = {
    "secretaria": "Secretaria (acesso total)",
    "direcao":    "Direção (acesso total)",
    "pedagoga":   "Pedagoga (acesso total)",
    "professor":  "Professor (somente pedagógico)",
}

class UsuariosModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()
        self.carregar()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="👥 Gerenciamento de Usuários", font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        btn_f = ctk.CTkFrame(header, fg_color="transparent")
        btn_f.pack(side="right", padx=15, pady=10)
        ctk.CTkButton(btn_f, text="+ Novo Usuário", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=lambda: self._form(None), width=140).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="✏ Editar", fg_color=CORES["primaria_clara"],
                      text_color=CORES["texto_claro"], command=self.editar, width=100).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="🗑 Remover", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=self.remover, width=100).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="🔒 Alterar Senha de Acesso", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                      font=fonte(12, "bold"), command=self._alterar_senha_acesso, width=190).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="🕒 Histórico de Atividades", fg_color=CORES["primaria_clara"],
                      text_color=CORES["texto_claro"], font=fonte(12, "bold"),
                      command=self._ver_historico_acessos, width=180).pack(side="left", padx=5)

        tabela_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        tabela_f.pack(fill="both", expand=True, padx=20, pady=10)

        aviso = ctk.CTkLabel(tabela_f,
                              text="⚠  Perfil Professor: acesso somente a Turmas, Disciplinas, Notas e Frequência.\n"
                                   "Perfis Secretaria / Direção / Pedagoga: acesso total e irrestrito ao sistema.",
                              font=fonte(11), text_color=CORES["dourado"])
        aviso.pack(anchor="w", padx=15, pady=(10, 5))

        cols = ("login", "nome", "perfil", "status")
        self.tree = ttk.Treeview(tabela_f, columns=cols, show="headings", height=18)
        for col, (txt, w) in {"login": ("Login", 150), "nome": ("Nome", 240),
                               "perfil": ("Perfil", 220), "status": ("Status", 80)}.items():
            self.tree.heading(col, text=txt, anchor="w")
            self.tree.column(col, width=w, anchor="w")
        scroll = ttk.Scrollbar(tabela_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scroll.pack(side="right", fill="y", pady=5)

    def _ver_historico_acessos(self):
        conn = get_connection()
        registros = conn.execute(
            "SELECT usuario_nome, usuario_login, data_hora, acao FROM log_acessos ORDER BY data_hora DESC LIMIT 500"
        ).fetchall()
        conn.close()

        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Histórico de Atividades")
        win.geometry("620x600")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(win, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="🕒 Histórico de Atividades do Sistema", font=fonte(14, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        ctk.CTkLabel(win, text="💡 ESTE CAMPO NÃO EXPIRA - NÃO PODE SER APAGADO.",
                     font=fonte(10), text_color=CORES["subtexto"]).pack(pady=(2, 0))

        tabela_f = ctk.CTkFrame(win, fg_color=CORES["card"], corner_radius=12)
        tabela_f.pack(fill="both", expand=True, padx=15, pady=15)

        cols = ("nome", "login", "acao", "data_hora")
        tree = ttk.Treeview(tabela_f, columns=cols, show="headings", height=22)
        for col, (txt, w) in {"nome": ("Usuário", 200), "login": ("Login", 110),
                               "acao": ("Ação", 100), "data_hora": ("Data e Hora", 160)}.items():
            tree.heading(col, text=txt, anchor="w")
            tree.column(col, width=w, anchor="w")
        for r in registros:
            tree.insert("", "end", values=(r["usuario_nome"], r["usuario_login"],
                                           r["acao"] or "login", r["data_hora"]))
        scroll = ttk.Scrollbar(tabela_f, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scroll.pack(side="right", fill="y", pady=5)

        if not registros:
            ctk.CTkLabel(win, text="Nenhuma atividade registrada ainda.",
                         text_color=CORES["subtexto"]).pack(pady=10)

    def _alterar_senha_acesso(self):
        conn = get_connection()
        row = conn.execute("SELECT gestao_usuarios_login, gestao_usuarios_senha FROM dados_escola LIMIT 1").fetchone()
        conn.close()
        login_atual = (row["gestao_usuarios_login"] if row and row["gestao_usuarios_login"] else "Admin")
        senha_atual = (row["gestao_usuarios_senha"] if row and row["gestao_usuarios_senha"] else "Admin123")

        dlg = ctk.CTkToplevel(self.winfo_toplevel())
        dlg.title("Alterar Senha de Acesso")
        dlg.geometry("360x300")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CORES["fundo"])
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="🔒 Login e Senha desta tela", font=fonte(15, "bold"),
                     text_color=CORES["dourado"]).pack(pady=(20, 15))

        ctk.CTkLabel(dlg, text="Novo Login", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"], anchor="w").pack(padx=40, fill="x")
        e_login = ctk.CTkEntry(dlg, width=280, height=36)
        e_login.insert(0, login_atual)
        e_login.pack(padx=40, pady=(2, 10))

        ctk.CTkLabel(dlg, text="Nova Senha", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"], anchor="w").pack(padx=40, fill="x")
        e_senha = ctk.CTkEntry(dlg, width=280, height=36)
        e_senha.insert(0, "" if parece_hash_bcrypt(senha_atual) else senha_atual)
        e_senha.pack(padx=40, pady=(2, 15))

        def salvar():
            novo_login = e_login.get().strip()
            nova_senha = e_senha.get().strip()
            if not novo_login or not nova_senha:
                messagebox.showerror("Erro", "Login e senha não podem ficar em branco.", parent=dlg)
                return
            conn2 = get_connection()
            conn2.execute("UPDATE dados_escola SET gestao_usuarios_login=?, gestao_usuarios_senha=?",
                          (novo_login, gerar_hash_senha(nova_senha)))
            conn2.commit()
            conn2.close()
            messagebox.showinfo("Sucesso", "Login e senha atualizados!", parent=dlg)
            dlg.destroy()

        ctk.CTkButton(dlg, text="💾 Salvar", fg_color=CORES["acento"], hover_color=CORES["acento_hover"],
                      text_color=CORES["texto_claro"], font=fonte(13, "bold"),
                      command=salvar, width=280, height=38).pack(padx=40, pady=6)

    def carregar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = get_connection()
        for row in conn.execute(
            "SELECT * FROM usuarios WHERE login != 'admin' AND (excluido IS NULL OR excluido = 0) ORDER BY nome"
        ).fetchall():
            perfil_txt = PERFIS.get(row["perfil"], row["perfil"])
            status = "✅ Ativo" if row["ativo"] else "❌ Inativo"
            self.tree.insert("", "end", iid=row["id"],
                             values=(row["login"], row["nome"], perfil_txt, status))
        conn.close()

    def editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um usuário.")
            return
        self._form(int(sel[0]))

    def remover(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um usuário.")
            return
        uid = int(sel[0])
        conn = get_connection()
        u = conn.execute("SELECT login FROM usuarios WHERE id=?", (uid,)).fetchone()
        conn.close()
        if u and u["login"] == "admin":
            messagebox.showerror("Erro", "O usuário 'admin' não pode ser removido.")
            return
        if messagebox.askyesno("Confirmar", "Remover este usuário permanentemente?"):
            conn = get_connection()
            conn.execute("UPDATE usuarios SET excluido=1 WHERE id=?", (uid,))
            conn.commit()
            conn.close()
            self.carregar()

    def _form(self, uid):
        form = ctk.CTkToplevel(self.winfo_toplevel())
        form.title("Novo Usuário" if not uid else "Editar Usuário")
        form.geometry("460x560")
        form.grab_set()
        form.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(form, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="👥 Usuário do Sistema", font=fonte(14, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        dados = {}
        if uid:
            conn = get_connection()
            dados = dict(conn.execute("SELECT * FROM usuarios WHERE id=?", (uid,)).fetchone() or {})
            conn.close()

        frame = ctk.CTkFrame(form, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        def lbl(t, r):
            ctk.CTkLabel(frame, text=t, font=fonte(13, "bold"),
                         text_color=CORES["subtexto"]).grid(row=r, column=0, sticky="w", padx=5, pady=(10, 0))

        lbl("Nome Completo *", 0)
        nome_e = ctk.CTkEntry(frame, width=380)
        nome_e.insert(0, dados.get("nome", ""))
        nome_e.grid(row=1, column=0, padx=5, pady=(0, 4), sticky="ew")

        lbl("Login (nome de acesso) *", 2)
        login_e = ctk.CTkEntry(frame, width=380)
        login_e.insert(0, dados.get("login", ""))
        login_e.grid(row=3, column=0, padx=5, pady=(0, 4), sticky="ew")

        lbl("Senha *  (deixe em branco para não alterar)", 4)
        senha_e = ctk.CTkEntry(frame, width=380, show="•")
        senha_e.grid(row=5, column=0, padx=5, pady=(0, 4), sticky="ew")

        lbl("Perfil de Acesso *", 6)
        perfil_var = ctk.StringVar(value=dados.get("perfil", "secretaria"))
        ctk.CTkOptionMenu(frame, values=list(PERFIS.keys()), variable=perfil_var, width=380).grid(
            row=7, column=0, padx=5, pady=(0, 4), sticky="ew")

        lbl("Status", 8)
        ativo_var = ctk.StringVar(value="ativo" if dados.get("ativo", 1) else "inativo")
        ctk.CTkOptionMenu(frame, values=["ativo", "inativo"], variable=ativo_var, width=380).grid(
            row=9, column=0, padx=5, pady=(0, 4), sticky="ew")

        def salvar():
            nome = nome_e.get().strip()
            login = login_e.get().strip()
            senha = senha_e.get().strip()
            if not nome or not login:
                messagebox.showerror("Erro", "Nome e Login são obrigatórios!", parent=form)
                return
            if not uid and not senha:
                messagebox.showerror("Erro", "Informe a senha para o novo usuário.", parent=form)
                return
            ativo = 1 if ativo_var.get() == "ativo" else 0
            conn = get_connection()
            try:
                if uid:
                    if senha:
                        conn.execute("UPDATE usuarios SET nome=?, login=?, senha=?, perfil=?, ativo=? WHERE id=?",
                                    (nome, login, gerar_hash_senha(senha), perfil_var.get(), ativo, uid))
                    else:
                        conn.execute("UPDATE usuarios SET nome=?, login=?, perfil=?, ativo=? WHERE id=?",
                                    (nome, login, perfil_var.get(), ativo, uid))
                else:
                    conn.execute("INSERT INTO usuarios (nome, login, senha, perfil, ativo) VALUES (?,?,?,?,?)",
                                (nome, login, gerar_hash_senha(senha), perfil_var.get(), ativo))
                conn.commit()
                messagebox.showinfo("Sucesso", "Usuário salvo!", parent=form)
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
                      font=fonte(13, "bold"), command=salvar, width=130, height=36).pack(side="right", padx=10, pady=10)
