"""
Base genérica para: Professores, Funcionários, Pedagogas, Secretário(a) e Diretores.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection, nome_seguro
from tema import (CORES, fonte, maximizar, abrir_link, vincular_mascara,
                   mascara_cpf, mascara_cep, mascara_telefone, mascara_data,
                   mascara_nis, mascara_portaria, data_bd_para_tela, data_tela_para_bd,
                   ESTADOS_UF, COR_RACA_OPCOES, ESTADO_CIVIL_OPCOES, SITUACAO_FUNCIONAL_OPCOES)
from modules.widgets_extras import OcorrenciasWidget, AtestadosWidget
import pdf_utils


def _validar_tabela(tabela):
    if not nome_seguro(tabela):
        raise ValueError(f"Nome de tabela inválido: {tabela!r}")


class PessoaFuncionalModule(ctk.CTkFrame):
    def __init__(self, parent, tabela, titulo, icone,
                 mostrar_disciplinas=False, somente_consulta=False,
                 mostrar_portaria=False, tem_atestados=True,
                 modo_compacto=False, altura_lista=8):
        super().__init__(parent, fg_color=CORES["fundo"] if not modo_compacto else "transparent")
        self.tabela = tabela
        self.titulo = titulo
        self.icone = icone
        self.mostrar_disciplinas = mostrar_disciplinas
        self.somente_consulta = somente_consulta
        self.mostrar_portaria = mostrar_portaria
        self.tem_atestados = tem_atestados
        self.modo_compacto = modo_compacto
        self.altura_lista = altura_lista
        self._build_ui()
        self.carregar()

    # ------------------------------------------------------------------ LISTA
    def _build_ui(self):
        if self.modo_compacto:
            header = ctk.CTkFrame(self, fg_color=CORES["dourado"], corner_radius=10, height=40)
            header.pack(fill="x", padx=0, pady=(0, 8))
            header.pack_propagate(False)
            ctk.CTkLabel(header, text=f"{self.icone} {self.titulo}", font=fonte(15, "bold"),
                         text_color=CORES["sidebar"]).pack(side="left", padx=15, pady=6)

            if not self.somente_consulta:
                bf = ctk.CTkFrame(header, fg_color="transparent")
                bf.pack(side="right", padx=10, pady=4)
                ctk.CTkButton(bf, text="+ Novo(a)", fg_color=CORES["acento"],
                              hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                              font=fonte(11, "bold"), command=self.abrir_form_novo, width=90, height=26).pack(side="left", padx=3)
                ctk.CTkButton(bf, text="✏ Editar", fg_color=CORES["primaria_clara"],
                              text_color=CORES["texto_claro"], command=self.editar, width=80, height=26).pack(side="left", padx=3)
                ctk.CTkButton(bf, text="🗄 Arquivar", fg_color=CORES["sidebar"],
                              text_color=CORES["texto_claro"],
                              font=fonte(10, "bold"), command=self.arquivar, width=90, height=26).pack(side="left", padx=3)

            busca_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=10)
            busca_f.pack(fill="x", padx=0, pady=(0, 6))
            ctk.CTkLabel(busca_f, text="🔍", text_color=CORES["subtexto"]).pack(side="left", padx=(12, 4), pady=6)
            self.busca_var = ctk.StringVar()
            self.busca_var.trace("w", lambda *a: self.carregar())
            ctk.CTkEntry(busca_f, textvariable=self.busca_var,
                         placeholder_text="Nome, CPF ou cargo...", width=240, height=28).pack(side="left", pady=6)
            self.label_total = ctk.CTkLabel(busca_f, text="", text_color=CORES["subtexto"], font=fonte(10))
            self.label_total.pack(side="right", padx=15)

            tf = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=10)
            tf.pack(fill="x", padx=0, pady=(0, 4))
            cols = ("matricula", "nome", "cargo", "cpf", "telefone1", "situacao")
            self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=self.altura_lista)
            hdrs = {"matricula": ("Matrícula", 80), "nome": ("Nome", 220), "cargo": ("Cargo", 150),
                    "cpf": ("CPF", 130), "telefone1": ("Telefone", 130), "situacao": ("Situação", 130)}
            for col, (txt, w) in hdrs.items():
                self.tree.heading(col, text=txt, anchor="w")
                self.tree.column(col, width=w, anchor="w")
            scr = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=scr.set)
            self.tree.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            scr.pack(side="right", fill="y", pady=5)
            self.tree.bind("<Double-1>", lambda e: self.ver_ficha())
            return

        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text=f"{self.icone} {self.titulo}", font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        if not self.somente_consulta:
            bf = ctk.CTkFrame(header, fg_color="transparent")
            bf.pack(side="right", padx=15, pady=10)
            ctk.CTkButton(bf, text="+ Novo(a)", fg_color=CORES["acento"],
                          hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                          font=fonte(13, "bold"), command=self.abrir_form_novo, width=120).pack(side="left", padx=4)
            ctk.CTkButton(bf, text="✏ Editar", fg_color=CORES["primaria_clara"],
                          text_color=CORES["texto_claro"], command=self.editar, width=90).pack(side="left", padx=4)
            ctk.CTkButton(bf, text="🗄 Arquivar", fg_color=CORES["dourado"],
                          hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                          font=fonte(12, "bold"), command=self.arquivar, width=100).pack(side="left", padx=4)

        busca_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        busca_f.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(busca_f, text="🔍", text_color=CORES["subtexto"]).pack(side="left", padx=(15, 4), pady=10)
        self.busca_var = ctk.StringVar()
        self.busca_var.trace("w", lambda *a: self.carregar())
        ctk.CTkEntry(busca_f, textvariable=self.busca_var,
                     placeholder_text="Nome, CPF ou cargo...", width=300).pack(side="left", pady=10)
        self.label_total = ctk.CTkLabel(busca_f, text="", text_color=CORES["subtexto"])
        self.label_total.pack(side="right", padx=20)

        tf = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        tf.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("matricula", "nome", "cargo", "cpf", "telefone1", "situacao")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=20)
        hdrs = {"matricula": ("Matrícula", 80), "nome": ("Nome", 260), "cargo": ("Cargo", 160), 
                "cpf": ("CPF", 140), "telefone1": ("Telefone", 140), "situacao": ("Situação Funcional", 160)}
        for col, (txt, w) in hdrs.items():
            self.tree.heading(col, text=txt, anchor="w")
            self.tree.column(col, width=w, anchor="w")
        scr = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scr.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scr.pack(side="right", fill="y", pady=5)
        self.tree.bind("<Double-1>", lambda e: self.ver_ficha())

    def carregar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        busca = self.busca_var.get().strip()
        conn = get_connection()
        rows = conn.execute(
            f"SELECT * FROM {self.tabela} WHERE arquivado=0 "
            "AND (nome LIKE ? OR cpf LIKE ? OR cargo LIKE ?) ORDER BY nome",
            [f"%{busca}%"] * 3).fetchall()
        conn.close()
        for r in rows:
            # Pegamos os dados com segurança. Se a coluna "matricula" não existir, o sistema não trava.
            try: m_val = r["matricula"] if r["matricula"] else "-"
            except: m_val = "-"
            
            n_val = r["nome"].upper() if r["nome"] else "-"
            c_val = r["cargo"] if r["cargo"] else "-"
            cpf_val = r["cpf"] if r["cpf"] else "-"
            tel_val = r["telefone1"] if r["telefone1"] else "-"
            sit_val = r["situacao_funcional"] if r["situacao_funcional"] else "-"

            self.tree.insert("", "end", iid=r["id"],
                             values=(m_val, n_val, c_val, cpf_val, tel_val, sit_val))

    def _sel_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um registro na lista.")
            return None
        return int(sel[0])

    def abrir_form_novo(self): self._abrir_form(None)
    def editar(self):
        pid = self._sel_id()
        if pid: self._abrir_form(pid)
    def ver_ficha(self):
        pid = self._sel_id()
        if pid: self._abrir_form(pid, somente_visualizar=True)

    def abrir_para_reativar(self, _parent, registro_id, reativando=True, on_close=None):
        self._abrir_form(registro_id, somente_visualizar=False, reativando=True, on_close=on_close)

    def arquivar(self):
        pid = self._sel_id()
        if not pid: return
        if messagebox.askyesno("Confirmar", "Mover para o Arquivo Morto?"):
            _validar_tabela(self.tabela)
            conn = get_connection()
            conn.execute(f"UPDATE {self.tabela} SET arquivado=1, ativo=0, data_arquivamento=? WHERE id=?",
                        (str(date.today()), pid))
            conn.commit()
            conn.close()
            self.carregar()

    # ------------------------------------------------------------------ FORM
    def _abrir_form(self, reg_id, somente_visualizar=False, reativando=False, on_close=None):
        form = ctk.CTkToplevel(self.winfo_toplevel())
        form.title(f"{'Novo(a)' if not reg_id else 'Ficha'} — {self.titulo}")
        maximizar(form)
        form.grab_set()
        form.configure(fg_color=CORES["fundo"])

        dados = {}
        if reg_id:
            conn = get_connection()
            dados = dict(conn.execute(f"SELECT * FROM {self.tabela} WHERE id=?", (reg_id,)).fetchone() or {})
            conn.close()

        conn_esc = get_connection()
        esc = conn_esc.execute("SELECT nome_escola FROM dados_escola LIMIT 1").fetchone()
        conn_esc.close()
        nome_esc = esc["nome_escola"] if esc and esc["nome_escola"] else "Escola Municipal"

        # Topo
        topo = ctk.CTkFrame(form, fg_color=CORES["primaria"], corner_radius=0, height=60)
        topo.pack(fill="x", side="top")

        # Logo (se existir)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image
                img = ctk.CTkImage(Image.open(logo_path), size=(44, 44))
                ctk.CTkLabel(topo, image=img, text="").pack(side="left", padx=(15, 5), pady=8)
            except Exception:
                pass

        ctk.CTkLabel(topo, text=nome_esc,
                     font=fonte(15, "bold"), text_color=CORES["dourado"]).pack(side="left", padx=10, pady=15)
        ctk.CTkLabel(topo, text=f"{self.icone} {self.titulo}", font=fonte(13),
                     text_color=CORES["texto_claro"]).pack(side="right", padx=20)

        if reativando:
            faixa = ctk.CTkFrame(form, fg_color=CORES["dourado"], corner_radius=0, height=34)
            faixa.pack(fill="x", side="top")
            ctk.CTkLabel(faixa, text="🗄 Cadastro arquivado — revise e clique em Salvar para reativar.",
                         font=fonte(12, "bold"), text_color=CORES["sidebar"]).pack(pady=6)

        estado = "disabled" if somente_visualizar else "normal"
        scroll = ctk.CTkScrollableFrame(form, fg_color=CORES["fundo"])
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        scroll.columnconfigure((0, 1, 2, 3), weight=1)

        campos = {}

        def secao(txt, row, span=4):
            ctk.CTkLabel(scroll, text=txt, font=fonte(13, "bold"),
                         text_color=CORES["dourado"]).grid(
                row=row, column=0, columnspan=span, sticky="w", padx=10, pady=(18, 2))

        def f(label, key, row, col, w=220, mascara=None, ph=""):
            ctk.CTkLabel(scroll, text=label, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).grid(row=row, column=col, sticky="w", padx=8, pady=(5, 0))
            e = ctk.CTkEntry(scroll, width=w, placeholder_text=ph, state="normal")
            val = dados.get(key, "") or ""
            # Converter datas do banco para tela
            if "data" in key.lower() and val:
                val = data_bd_para_tela(val)
            e.insert(0, val)
            e.configure(state=estado)
            e.grid(row=row + 1, column=col, padx=8, pady=(0, 3), sticky="ew")
            if mascara and not somente_visualizar:
                vincular_mascara(e, mascara)
            campos[key] = e
            return e

        def fopc(label, key, row, col, opcoes, w=220):
            ctk.CTkLabel(scroll, text=label, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).grid(row=row, column=col, sticky="w", padx=8, pady=(5, 0))
            var = ctk.StringVar(value=dados.get(key, "") or (opcoes[0] if opcoes else ""))
            ctk.CTkOptionMenu(scroll, values=opcoes, variable=var, width=w,
                               state=estado).grid(row=row + 1, column=col, padx=8, pady=(0, 3), sticky="ew")
            campos[key] = var
            return var

        r = 0
        secao("👤 IDENTIFICAÇÃO", r); r += 1
        f("Matrícula (5 dígitos)", "matricula", r, 0, w=140)
        f("Nome Completo *", "nome", r, 1, w=350); r += 2
        
        f("Cargo", "cargo", r, 0, w=220)
        f("CPF", "cpf", r, 1, w=160, mascara=mascara_cpf)
        f("NIS", "nis", r, 2, w=170, mascara=mascara_nis); r += 2
        
        fopc("Cor/Raça", "cor_raca", r, 0, COR_RACA_OPCOES, w=180)
        fopc("Estado Civil", "estado_civil", r, 1, ESTADO_CIVIL_OPCOES, w=180)
        f("Nome da Mãe", "nome_mae", r, 2, w=260)
        f("E-mail", "email", r, 3, w=240); r += 2

        secao("📍 ENDEREÇO", r); r += 1
        f("Rua", "rua", r, 0, w=260)
        f("Nº", "numero", r, 1, w=80)
        f("Complemento", "complemento", r, 2, w=180)
        f("Bairro", "bairro", r, 3, w=180); r += 2
        f("Município", "municipio", r, 0, w=200)
        f("CEP", "cep", r, 1, w=130, mascara=mascara_cep)
        fopc("UF", "uf", r, 2, ESTADOS_UF, w=100); r += 2

        secao("📞 CONTATO", r); r += 1
        f("Telefone 1", "telefone1", r, 0, w=160, mascara=mascara_telefone)
        f("Telefone 2", "telefone2", r, 1, w=160, mascara=mascara_telefone); r += 2

        secao("🎓 FORMAÇÃO", r); r += 1
        f("Instituição de Formação", "instituicao_formacao", r, 0, w=280)
        f("Ano de Formação", "ano_formacao", r, 1, w=130)
        f("Pós-graduação", "pos_graduacao", r, 2, w=260)
        f("Outros Cursos", "outros_cursos", r, 3, w=240); r += 2

        secao("💼 SITUAÇÃO FUNCIONAL", r); r += 1
        fopc("Situação", "situacao_funcional", r, 0, SITUACAO_FUNCIONAL_OPCOES, w=180)
        f("Data de Admissão", "data_admissao", r, 1, w=140, mascara=mascara_data, ph="DD/MM/AAAA")
        if self.mostrar_disciplinas:
            f("Disciplinas (separe por vírgula)", "disciplinas", r, 2, w=400); r += 2
        else:
            r += 2

        if self.mostrar_portaria:
            secao("📋 NOMEAÇÃO", r); r += 1
            f("Portaria de Nomeação (NNN/AAAA)", "portaria_nomeacao", r, 0, w=200,
              mascara=mascara_portaria, ph="000/0000"); r += 2

        # Link de documentos
        secao("📁 PASTA DE DOCUMENTOS", r); r += 1
        ctk.CTkLabel(scroll, text="Link do Drive", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).grid(row=r, column=0, sticky="w", padx=8, pady=(5, 0))
        r += 1
        lf = ctk.CTkFrame(scroll, fg_color="transparent")
        lf.grid(row=r, column=0, columnspan=4, sticky="ew", padx=8, pady=(0, 3))
        link_e = ctk.CTkEntry(lf, width=580, placeholder_text="https://drive.google.com/...", state="normal")
        link_e.insert(0, dados.get("pasta_documentos", "") or "")
        link_e.configure(state=estado)
        link_e.pack(side="left", padx=(0, 8))
        campos["pasta_documentos"] = link_e
        ctk.CTkButton(lf, text="📂 Abrir", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      command=lambda: abrir_link(link_e.get()), width=90).pack(side="left")
        r += 1

        # Atestados e Ocorrências (apenas se registro já existe)
        if reg_id:
            if self.tem_atestados:
                secao("📄 ATESTADOS / DECLARAÇÕES", r); r += 1
                at_w = AtestadosWidget(scroll, self.tabela, reg_id, somente_leitura=self.somente_consulta)
                at_w.grid(row=r, column=0, columnspan=4, padx=8, pady=(0, 10), sticky="w")
                r += 1

            secao("📋 OCORRÊNCIAS", r); r += 1
            oc_w = OcorrenciasWidget(scroll, self.tabela, reg_id, somente_leitura=self.somente_consulta)
            oc_w.grid(row=r, column=0, columnspan=4, padx=8, pady=(0, 10), sticky="w")
            r += 1

        secao("📝 OBSERVAÇÕES", r); r += 1
        obs = ctk.CTkTextbox(scroll, height=70, width=900, state="normal")
        obs.insert("1.0", dados.get("observacoes", "") or "")
        obs.configure(state=estado)
        obs.grid(row=r, column=0, columnspan=4, padx=8, pady=(0, 15), sticky="ew")
        campos["observacoes"] = obs
        r += 1

        # ---- Ações ----
        def coletar():
            d = {}
            for key, wid in campos.items():
                if isinstance(wid, ctk.StringVar):
                    d[key] = wid.get()
                elif isinstance(wid, ctk.CTkTextbox):
                    d[key] = wid.get("1.0", "end-1c")
                else:
                    d[key] = wid.get()
            # Converter datas de tela para banco
            for key in ["data_admissao"]:
                if key in d:
                    d[key] = data_tela_para_bd(d[key])
            return d

        campos_db = ["matricula","nome","cargo","rua","numero","complemento","bairro","municipio","cep","uf",
                     "telefone1","telefone2","cpf","nis","cor_raca","nome_mae","estado_civil",
                     "instituicao_formacao","ano_formacao","pos_graduacao","outros_cursos",
                     "situacao_funcional","disciplinas","email","data_admissao",
                     "pasta_documentos","observacoes"]
        if self.mostrar_portaria:
            campos_db.append("portaria_nomeacao")

        def salvar():
            d = coletar()
            if not d.get("nome", "").strip():
                messagebox.showerror("Erro", "Nome é obrigatório!", parent=form)
                return
            vals = {k: d.get(k, "") for k in campos_db}
            if "disciplinas" not in vals:
                vals["disciplinas"] = dados.get("disciplinas", "")
            conn = get_connection()
            try:
                _validar_tabela(self.tabela)
                if any(not nome_seguro(k) for k in campos_db):
                    invalidas = [k for k in campos_db if not nome_seguro(k)]
                    messagebox.showerror("Erro", f"Campos inválidos: {invalidas}", parent=form)
                    return
                if reg_id:
                    sc = ", ".join([f"{k}=:{k}" for k in campos_db])
                    if reativando:
                        sc += ", arquivado=0, ativo=1, data_arquivamento=NULL"
                    vals["_id"] = reg_id
                    conn.execute(f"UPDATE {self.tabela} SET {sc} WHERE id=:_id", vals)
                else:
                    cs = ", ".join(campos_db)
                    ph = ", ".join([f":{k}" for k in campos_db])
                    conn.execute(f"INSERT INTO {self.tabela} ({cs},ativo,arquivado) VALUES ({ph},1,0)", vals)
                conn.commit()
                msg = "Reativado e salvo!" if reativando else "Salvo com sucesso!"
                messagebox.showinfo("Sucesso", msg, parent=form)
                form.destroy()
                self.carregar()
                if on_close: on_close()
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=form)
            finally:
                conn.close()

        def blocos_pdf():
            d = coletar()
            blocos = [
                ("titulo", "Identificação"),
                ("tabela", [["Campo","Valor"],
                            ["Matrícula", d.get("matricula", "-")],
                    ["Nome", d.get("nome","-")], ["Cargo", d.get("cargo","-")],
                    ["CPF", d.get("cpf","-")], ["NIS", d.get("nis","-")],
                    ["E-mail", d.get("email","-")], ["Cor/Raça", d.get("cor_raca","-")],
                    ["Estado Civil", d.get("estado_civil","-")],
                    ["Nome da Mãe", d.get("nome_mae","-")]]),
                ("titulo", "Endereço e Contato"),
                ("tabela", [["Campo","Valor"],
                    ["Rua/Nº", f"{d.get('rua','-')}, {d.get('numero','-')}"],
                    ["Município/UF", f"{d.get('municipio','-')}/{d.get('uf','-')}"],
                    ["CEP", d.get("cep","-")],
                    ["Telefone 1", d.get("telefone1","-")],
                    ["Telefone 2", d.get("telefone2","-")]]),
                ("titulo", "Formação / Situação Funcional"),
                ("tabela", [["Campo","Valor"],
                    ["Formação", d.get("instituicao_formacao","-")],
                    ["Ano", d.get("ano_formacao","-")],
                    ["Pós-graduação", d.get("pos_graduacao","-")],
                    ["Situação", d.get("situacao_funcional","-")],
                    ["Admissão", d.get("data_admissao","-")]]),
            ]

            if reg_id and messagebox.askyesno("Imprimir Extras", "Deseja incluir Ocorrências e Atestados na impressão?"):
                conn = get_connection()
                ocorr = conn.execute(f"SELECT data, descricao, registrado_por FROM ocorrencias WHERE entidade='{self.tabela}' AND entidade_id=? AND (excluido IS NULL OR excluido=0) ORDER BY data DESC", (reg_id,)).fetchall()
                if ocorr:
                    blocos.append(("titulo", "Histórico de Ocorrências"))
                    linhas_oc = [["Data", "Descrição", "Registrado por"]]
                    for oc in ocorr:
                        linhas_oc.append([data_bd_para_tela(oc["data"]), oc["descricao"], oc["registrado_por"] or "-"] )
                    blocos.append(("tabela", linhas_oc))
                
                atest = conn.execute(f"SELECT tipo, data, duracao, unidade_duracao, observacao FROM atestados WHERE entidade='{self.tabela}' AND entidade_id=? AND (excluido IS NULL OR excluido=0) ORDER BY data DESC", (reg_id,)).fetchall()
                if atest:
                    blocos.append(("titulo", "Atestados / Declarações"))
                    linhas_at = [["Tipo", "Data", "Duração", "Observação"]]
                    for at in atest:
                        linhas_at.append([at["tipo"], data_bd_para_tela(at["data"]), f"{at['duracao']} {at['unidade_duracao']}", at["observacao"] or "-"])
                    blocos.append(("tabela", linhas_at))
                conn.close()

            return blocos

        def pdf_acao():
            pdf_utils.salvar_pdf_como(
                f"Ficha — {self.titulo}",
                blocos_pdf(),
                f"Ficha_{dados.get('nome','').replace(' ','_')}.pdf",
                parent=form)

        def impr_acao():
            pdf_utils.imprimir_pdf(
                f"Ficha — {self.titulo}",
                blocos_pdf(),
                f"Ficha_{dados.get('nome','').replace(' ','_')}.pdf",
                parent=form)

        # Barra inferior
        bb = ctk.CTkFrame(form, fg_color=CORES["card"], corner_radius=0, height=58)
        bb.pack(fill="x", side="bottom")
        ctk.CTkButton(bb, text="✖ Fechar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=form.destroy, width=110, height=38).pack(side="right", padx=10, pady=10)
        if not somente_visualizar:
            ctk.CTkButton(bb, text="💾 Salvar", fg_color=CORES["acento"],
                          hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                          font=fonte(13, "bold"), command=salvar, width=130, height=38).pack(side="right", padx=8, pady=10)
        elif reg_id and not self.somente_consulta:
            def _abrir_em_edicao():
                form.destroy()
                self._abrir_form(reg_id, somente_visualizar=False)
            ctk.CTkButton(bb, text="✏ Editar", fg_color=CORES["primaria_clara"],
                          text_color=CORES["texto_claro"], font=fonte(13, "bold"),
                          command=_abrir_em_edicao, width=110, height=38).pack(side="right", padx=8, pady=10)
        ctk.CTkButton(bb, text="🖨 Imprimir", fg_color=CORES["primaria_clara"],
                      text_color=CORES["texto_claro"], command=impr_acao, width=120, height=38).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(bb, text="📄 Salvar PDF", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                      font=fonte(12, "bold"), command=pdf_acao, width=130, height=38).pack(side="left", padx=6, pady=10)
        # Créditos desenvolvedor
        ctk.CTkLabel(bb, text="Sistema desenvolvido por João Paulo A. Guaita - Licença de uso cedida gratuitamente",
                     font=fonte(11), text_color=CORES["subtexto"]).pack(side="left", padx=20)
