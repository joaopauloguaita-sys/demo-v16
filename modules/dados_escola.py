import customtkinter as ctk
from tkinter import messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
import pdf_utils
from tema import (CORES, fonte, abrir_link, vincular_mascara,
                   mascara_inep, mascara_resolucao, mascara_cep,
                   mascara_telefone, mascara_data, data_bd_para_tela, data_tela_para_bd)


class DadosEscolaModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._campos = {}
        self.modo_edicao = False
        self._build_ui()
        self.carregar()

    def _build_ui(self):
        topo = ctk.CTkFrame(self, fg_color=CORES["primaria"], corner_radius=0, height=60)
        topo.pack(fill="x")
        
        conn = get_connection()
        esc = conn.execute("SELECT nome_escola FROM dados_escola LIMIT 1").fetchone()
        conn.close()
        nome_esc = esc["nome_escola"] if esc and esc["nome_escola"] else "Escola Municipal"

        ctk.CTkLabel(topo, text=nome_esc,
                     font=fonte(15, "bold"), text_color=CORES["dourado"]).pack(side="left", padx=25, pady=15)

        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(15, 0))
        ctk.CTkLabel(header, text="🏛 Dados da Escola", font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        self.btn_salvar = ctk.CTkButton(header, text="💾 Salvar", fg_color=CORES["sucesso"],
                      hover_color=CORES["sucesso_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=self.salvar, width=130)
        self.btn_editar = ctk.CTkButton(header, text="✏ Editar", fg_color=CORES["primaria_clara"],
                      text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=self.entrar_edicao, width=130)
        ctk.CTkButton(header, text="📄 Gerar PDF", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                      font=fonte(13, "bold"), command=self.gerar_pdf, width=130).pack(side="right", padx=(0, 8), pady=10)
        self._atualizar_botoes()

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.scroll.columnconfigure((0, 1, 2, 3), weight=1)

    def _atualizar_botoes(self):
        if self.modo_edicao:
            self.btn_editar.pack_forget()
            self.btn_salvar.pack(side="right", padx=15, pady=10)
        else:
            self.btn_salvar.pack_forget()
            self.btn_editar.pack(side="right", padx=15, pady=10)

    def entrar_edicao(self):
        self.modo_edicao = True
        self._atualizar_botoes()
        self.carregar()

    def _secao(self, txt, row, span=4):
        ctk.CTkLabel(self.scroll, text=txt, font=fonte(13, "bold"),
                     text_color=CORES["dourado"]).grid(
            row=row, column=0, columnspan=span, sticky="w", padx=10, pady=(18, 2))

    def _campo(self, label, key, row, col, w=220, mascara=None, ph="", readonly=False, span=1):
        ctk.CTkLabel(self.scroll, text=label, font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).grid(row=row, column=col, sticky="w", padx=8, pady=(5, 0))
        pode_editar = self.modo_edicao and not readonly
        e = ctk.CTkEntry(self.scroll, width=w, placeholder_text=ph,
                          state="normal" if pode_editar else "disabled")
        e.grid(row=row + 1, column=col, columnspan=span, padx=8, pady=(0, 3), sticky="ew")
        if mascara and pode_editar:
            vincular_mascara(e, mascara)
        self._campos[key] = e
        return e

    def carregar(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._campos = {}

        conn = get_connection()
        d = dict(conn.execute("SELECT * FROM dados_escola LIMIT 1").fetchone() or {})
        total_matriculados = conn.execute(
            "SELECT COUNT(*) FROM alunos WHERE ativo=1 AND arquivado=0").fetchone()[0]
        conn.close()

        r = 0
        self._secao("🏫 IDENTIFICAÇÃO", r); r += 1
        self._campo("Nome da Escola", "nome_escola", r, 0, w=500, span=2)
        self._campo("Código INEP (8 dígitos)", "inep", r, 2, w=180,
                    mascara=mascara_inep, ph="00000000"); r += 2
        self._campo("CNPJ", "cnpj", r, 0, w=220)
        self._campo("Razão Social da Mantenedora", "mantenedora", r, 1, w=400, span=3); r += 2

        self._secao("📍 ENDEREÇO", r); r += 1
        self._campo("Rua / Logradouro", "rua", r, 0, w=300)
        self._campo("Número", "numero", r, 1, w=90)
        self._campo("Bairro", "bairro", r, 2, w=200)
        self._campo("Município", "municipio", r, 3, w=200); r += 2
        self._campo("CEP", "cep", r, 0, w=130, mascara=mascara_cep)
        self._campo("UF", "uf", r, 1, w=80)
        self._campo("Complemento", "complemento", r, 2, w=400, span=2); r += 2

        self._secao("📞 CONTATO E COMUNICAÇÃO", r); r += 1
        self._campo("Telefone Principal", "telefone", r, 0, w=170, mascara=mascara_telefone)
        self._campo("Telefone Alternativo", "telefone2", r, 1, w=170, mascara=mascara_telefone)
        self._campo("E-mail Institucional", "email", r, 2, w=300, span=2); r += 2

        self._secao("📊 DADOS GERAIS", r); r += 1
        self._campo("Nº de Salas de Aula", "num_salas", r, 0, w=120)
        ctk.CTkLabel(self.scroll, text="Alunos Matriculados (automático)",
                     font=fonte(11, "bold"), text_color=CORES["subtexto"]
                     ).grid(row=r, column=1, sticky="w", padx=8, pady=(5, 0))
        alunos_e = ctk.CTkEntry(self.scroll, width=140, state="disabled")
        alunos_e.configure(state="normal")
        alunos_e.insert(0, str(total_matriculados))
        alunos_e.configure(state="disabled")
        alunos_e.grid(row=r + 1, column=1, padx=8, pady=(0, 3), sticky="ew"); r += 2

        self._secao("🔗 LINK DE DOCUMENTAÇÃO", r); r += 1
        lf = ctk.CTkFrame(self.scroll, fg_color="transparent")
        lf.grid(row=r, column=0, columnspan=4, sticky="ew", padx=8, pady=(0, 3))
        link_e = ctk.CTkEntry(lf, width=580, placeholder_text="https://...")
        link_e.pack(side="left", padx=(0, 8))
        self._campos["link_documentacao"] = link_e
        ctk.CTkButton(lf, text="🔗 Abrir", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      command=lambda: abrir_link(link_e.get()), width=90).pack(side="left")
        r += 1

        self._secao("📜 RESOLUÇÕES E PARECERES", r); r += 1
        labels_res = [f"Resolução/Parecer {i}" for i in range(1, 17)]
        for i, lbl in enumerate(labels_res):
            col = i % 4
            if i % 4 == 0 and i > 0: r += 2
            self._campo(lbl, f"resolucao_{i+1}", r, col, w=200, mascara=mascara_resolucao)
        r += 2

        if self.modo_edicao:
            self._secao("🤖 INTELIGÊNCIA ARTIFICIAL (GEMINI)", r); r += 1
            self._campo("Chave API do Google Gemini", "gemini_api_key", r, 0, w=500, ph="Cole sua chave aqui...")
            r += 2

        self._secao("📅 DATAS DOS BIMESTRES (usado para calcular o bimestre atual sozinho)", r); r += 1
        for n, col in [(1, 0), (2, 2)]:
            self._campo(f"{n}º Bimestre - Início", f"bim{n}_inicio", r, col, w=140,
                        mascara=mascara_data, ph="DD/MM/AAAA")
            self._campo(f"{n}º Bimestre - Fim", f"bim{n}_fim", r, col + 1, w=140,
                        mascara=mascara_data, ph="DD/MM/AAAA")
        r += 2
        for n, col in [(3, 0), (4, 2)]:
            self._campo(f"{n}º Bimestre - Início", f"bim{n}_inicio", r, col, w=140,
                        mascara=mascara_data, ph="DD/MM/AAAA")
            self._campo(f"{n}º Bimestre - Fim", f"bim{n}_fim", r, col + 1, w=140,
                        mascara=mascara_data, ph="DD/MM/AAAA")
        r += 2

        campos_data_bimestre = ["bim1_inicio", "bim1_fim", "bim2_inicio", "bim2_fim",
                                 "bim3_inicio", "bim3_fim", "bim4_inicio", "bim4_fim"]

        for key, widget in self._campos.items():
            if hasattr(widget, "insert"):
                s = widget.cget("state")
                widget.configure(state="normal")
                widget.delete(0, "end")
                valor = d.get(key, "") or ""
                if key in campos_data_bimestre and valor:
                    valor = data_bd_para_tela(valor)
                widget.insert(0, valor)
                widget.configure(state=s)

    def gerar_pdf(self):
        conn = get_connection()
        d = dict(conn.execute("SELECT * FROM dados_escola LIMIT 1").fetchone() or {})
        conn.close()

        def v(chave):
            return d.get(chave, "") or "-"

        blocos = [
            ("titulo", "Identificação"),
            ("tabela", [["Campo", "Valor"],
                ["Nome da Escola", v("nome_escola")],
                ["Código INEP", v("inep")],
                ["CNPJ", v("cnpj")],
                ["Razão Social da Mantenedora", v("mantenedora")]]),
            ("titulo", "Endereço"),
            ("tabela", [["Campo", "Valor"],
                ["Rua/Nº", f"{v('rua')}, {v('numero')}"],
                ["Bairro", v("bairro")],
                ["Município/UF", f"{v('municipio')}/{v('uf')}"],
                ["CEP", v("cep")],
                ["Complemento", v("complemento")]]),
            ("titulo", "Contato e Comunicação"),
            ("tabela", [["Campo", "Valor"],
                ["Telefone Principal", v("telefone") or v("telefone1")],
                ["Telefone Alternativo", v("telefone2")],
                ["E-mail Institucional", v("email")]]),
            ("titulo", "Dados Gerais"),
            ("tabela", [["Campo", "Valor"],
                ["Nº de Salas de Aula", v("num_salas")],
                ["Link de Documentação", v("link_documentacao")]]),
        ]

        resolucoes = [["Resolução/Parecer", "Número"]]
        for i in range(1, 17):
            resolucoes.append([f"Resolução/Parecer {i}", v(f"resolucao_{i}")])
        blocos.append(("titulo", "Resoluções e Pareceres"))
        blocos.append(("tabela", resolucoes))

        try:
            caminho = pdf_utils.gerar_pdf("Dados da Escola", blocos, "Dados_da_Escola.pdf")
            pdf_utils._abrir_arquivo(caminho)
        except Exception as e:
            messagebox.showerror("Erro ao gerar PDF", str(e))

    def salvar(self):
        vals = {}
        campos_data_bimestre = ["bim1_inicio", "bim1_fim", "bim2_inicio", "bim2_fim",
                                 "bim3_inicio", "bim3_fim", "bim4_inicio", "bim4_fim"]
        for key, widget in self._campos.items():
            if hasattr(widget, "get"):
                s = widget.cget("state")
                if s == "disabled": continue
                valor = widget.get().strip()
                if key in campos_data_bimestre and valor:
                    valor = data_tela_para_bd(valor)
                vals[key] = valor
        
        if "telefone" in vals: vals["telefone1"] = vals["telefone"]

        if not vals.get("nome_escola", "").strip():
            messagebox.showerror("Erro", "O nome da escola é obrigatório.", parent=self)
            return

        from database.db import nome_seguro
        if any(not nome_seguro(k) for k in vals):
            invalidas = [k for k in vals if not nome_seguro(k)]
            messagebox.showerror("Erro", f"Campos inválidos: {invalidas}", parent=self)
            return

        conn = get_connection()
        try:
            ex = conn.execute("SELECT id FROM dados_escola LIMIT 1").fetchone()
            if ex:
                sc = ", ".join([f"{k}=:{k}" for k in vals])
                conn.execute(f"UPDATE dados_escola SET {sc} WHERE id={ex['id']}", vals)
            else:
                cs = ", ".join(vals.keys())
                ph = ", ".join([f":{k}" for k in vals])
                conn.execute(f"INSERT INTO dados_escola ({cs}) VALUES ({ph})", vals)
            conn.commit()
            messagebox.showinfo("Sucesso", "Dados da escola salvos!")
            self.modo_edicao = False
            self._atualizar_botoes()
            self.carregar()
        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            conn.close()
