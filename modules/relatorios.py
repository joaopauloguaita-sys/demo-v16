"""
Relatórios do João - Secretário Escolar.
Cada relatório tem três opções: Exibir (janela interna), PDF e Imprimir.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte
import pdf_utils


# ─────────────────────────────────────────────────────────────────────────────
# Janela de exibição interna
# ─────────────────────────────────────────────────────────────────────────────
class JanelaExibir(ctk.CTkToplevel):
    """
    Exibe os dados de um relatório em uma janela do próprio sistema,
    com tabelas formatadas e botões para PDF e Imprimir.
    """
    def __init__(self, parent, titulo, blocos):
        super().__init__(parent.winfo_toplevel())
        self.titulo  = titulo
        self.blocos  = blocos
        self.title(f"📊 {titulo}")
        try:
            self.state("zoomed")
        except Exception:
            pass
        self.configure(fg_color=CORES["fundo"])
        self.grab_set()
        self._build(titulo, blocos)

    def _build(self, titulo, blocos):
        conn_esc = get_connection()
        esc = conn_esc.execute("SELECT nome_escola FROM dados_escola LIMIT 1").fetchone()
        conn_esc.close()
        nome_esc = esc["nome_escola"] if esc and esc["nome_escola"] else "Escola Municipal"

        # Topo
        topo = ctk.CTkFrame(self, fg_color=CORES["primaria"], corner_radius=0, height=58)
        topo.pack(fill="x", side="top")
        ctk.CTkLabel(topo, text=nome_esc,
                     font=fonte(14, "bold"), text_color=CORES["dourado"]).pack(side="left", padx=20, pady=14)
        ctk.CTkLabel(topo, text=f"📊 {titulo}", font=fonte(12),
                     text_color=CORES["texto_claro"]).pack(side="right", padx=20)

        # Barra de ações
        bb = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=0, height=55)
        bb.pack(fill="x", side="bottom")
        ctk.CTkButton(bb, text="✖ Fechar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=self.destroy, width=110, height=36).pack(side="right", padx=12, pady=10)
        ctk.CTkButton(bb, text="📄 Salvar PDF", fg_color=CORES["dourado"],
                      hover_color=CORES["dourado_hover"], text_color=CORES["primaria"],
                      font=fonte(12, "bold"),
                      command=lambda: pdf_utils.salvar_pdf_como(
                          titulo, blocos,
                          f"{titulo.replace(' ', '_')}.pdf", parent=self),
                      width=140, height=36).pack(side="right", padx=5, pady=10)
        ctk.CTkButton(bb, text="🖨 Imprimir", fg_color=CORES["primaria_clara"],
                      text_color=CORES["texto_claro"],
                      command=lambda: pdf_utils.imprimir_pdf(
                          titulo, blocos,
                          f"{titulo.replace(' ', '_')}.pdf", parent=self),
                      width=120, height=36).pack(side="right", padx=5, pady=10)
        ctk.CTkLabel(bb, text=f"Gerado em {date.today().strftime('%d/%m/%Y')}  |  "
                               "Sistema desenvolvido por João Paulo A. Guaita - Licença de uso cedida gratuitamente",
                     font=fonte(10), text_color=CORES["subtexto"]).pack(side="left", padx=20)

        # Conteúdo
        scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"])
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        for bloco in blocos:
            tipo = bloco[0]

            if tipo == "titulo":
                ctk.CTkLabel(scroll, text=str(bloco[1]),
                             font=fonte(14, "bold"), text_color=CORES["dourado"],
                             anchor="w").pack(fill="x", padx=5, pady=(14, 4))
                # Linha separadora
                ctk.CTkFrame(scroll, fg_color=CORES["dourado"], height=2,
                             corner_radius=0).pack(fill="x", padx=5, pady=(0, 6))

            elif tipo == "texto":
                ctk.CTkLabel(scroll, text=str(bloco[1]),
                             font=fonte(12), text_color=CORES["texto"],
                             anchor="w", wraplength=900).pack(fill="x", padx=5, pady=3)

            elif tipo == "espaco":
                ctk.CTkFrame(scroll, fg_color="transparent",
                             height=int(float(bloco[1]) * 20)).pack()

            elif tipo == "tabela":
                dados = bloco[1]
                if not dados:
                    continue
                self._montar_tabela(scroll, dados)

    def _montar_tabela(self, parent, dados):
        """Monta uma tabela TTK com estilo da escola dentro da janela."""
        frame = ctk.CTkFrame(parent, fg_color=CORES["card"], corner_radius=10)
        frame.pack(fill="x", padx=5, pady=(0, 12))

        if not dados:
            return

        # Definir colunas
        cabecalho = [str(c) for c in dados[0]]
        n_cols    = len(cabecalho)
        ids_cols  = [f"c{i}" for i in range(n_cols)]

        # Calcular largura proporcional de cada coluna
        maximos = [len(h) for h in cabecalho]
        for row in dados[1:]:
            for j, cell in enumerate(row):
                if j < n_cols:
                    maximos[j] = max(maximos[j], len(str(cell) if cell else ""))
        total_chars = sum(maximos) or 1
        # Largura da janela estimada em ~900px disponíveis
        largura_total = 880
        larguras = [max(60, int(largura_total * m / total_chars)) for m in maximos]

        tree = ttk.Treeview(frame, columns=ids_cols, show="headings",
                             height=min(len(dados) - 1, 20))

        for i, (col_id, header, larg) in enumerate(zip(ids_cols, cabecalho, larguras)):
            tree.heading(col_id, text=header, anchor="w")
            tree.column(col_id, width=larg, anchor="w", stretch=True)

        # Linhas alternadas
        tree.tag_configure("par",   background="#ffffff", foreground=CORES["texto"])
        tree.tag_configure("impar", background=CORES["card_claro"], foreground=CORES["texto"])

        for i, row in enumerate(dados[1:]):
            valores = [str(c) if c is not None else "-" for c in row]
            # Completar se faltar colunas
            while len(valores) < n_cols:
                valores.append("-")
            tag = "par" if i % 2 == 0 else "impar"
            tree.insert("", "end", values=valores, tags=(tag,))

        # Scrollbar horizontal se necessário
        scr_v = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
        scr_h = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scr_v.set, xscrollcommand=scr_h.set)

        tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scr_v.grid(row=0, column=1, sticky="ns", pady=5)
        scr_h.grid(row=1, column=0, sticky="ew", padx=5)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)


# ─────────────────────────────────────────────────────────────────────────────
# Módulo principal de relatórios
# ─────────────────────────────────────────────────────────────────────────────
class RelatoriosModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._build_ui()

    def _build_ui(self):
        topo = ctk.CTkFrame(self, fg_color=CORES["primaria"], corner_radius=0, height=60)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="Escola Municipal TRÁ LÁ LÁ",
                     font=fonte(15, "bold"), text_color=CORES["dourado"]).pack(
                     side="left", padx=25, pady=15)

        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(15, 0))
        ctk.CTkLabel(header, text="📄 Relatórios e Documentos",
                     font=fonte(22, "bold"), text_color=CORES["dourado"]).pack(
                     side="left", padx=20, pady=15)
        ctk.CTkLabel(header,
                     text="Clique em EXIBIR para ver na tela  |  PDF para salvar  |  Imprimir para enviar à impressora",
                     font=fonte(11), text_color=CORES["subtexto"]).pack(side="right", padx=20)

        grid = ctk.CTkScrollableFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=20, pady=12)
        grid.columnconfigure((0, 1, 2), weight=1)

        relatorios = [
            ("📋", "Lista de Alunos por Turma",
             "Lista completa com dados dos alunos de uma turma",
             CORES["acento"], self.rel_lista_alunos),

            ("👨‍🏫", "Lista de Professores",
             "Todos os professores ativos com disciplinas e contatos",
             "#7e3af2", self.rel_lista_professores),

            ("🧑‍💼", "Lista de Funcionários",
             "Todos os funcionários ativos com cargos",
             CORES["primaria_clara"], self.rel_lista_funcionarios),

            ("📊", "Boletim Geral da Turma",
             "Notas de todos os alunos por bimestre",
             CORES["secundaria"], self.rel_boletim_geral),

            ("✅", "Frequência por Turma",
             "Percentual de presença de cada aluno",
             CORES["sucesso"], self.rel_frequencia),

            ("⚠️", "Alunos com Baixa Frequência",
             "Alunos com menos de 75% de presença",
             CORES["perigo"], self.rel_baixa_frequencia),

            ("📈", "Desempenho por Disciplina",
             "Média geral de cada disciplina por turma",
             CORES["dourado"], self.rel_desempenho),

            ("🏫", "Turmas — Alunos por Sexo",
             "Quantidade de alunos, meninos e meninas por turma",
             CORES["acento"], self.rel_turmas_sexo),

            ("📅", "Grade Curricular",
             "Grade de horários de uma turma específica",
             CORES["secundaria"], self.rel_grade),

            ("📏", "Registro de Tamanhos",
             "Tamanhos de uniforme/calçado de uma turma, para doações e pedidos",
             CORES["acento"], self.rel_tamanhos),

            ("📦", "Histórico de Retiradas (30 dias)",
             "Retiradas de materiais do estoque nos últimos 30 dias",
             CORES["dourado"], self.rel_historico_retiradas_estoque),

            ("⏳", "Fila de Espera",
             "Lista completa da fila de espera por vagas",
             CORES["primaria_clara"], self.rel_fila_espera),

            ("🖥️", "Curso de Informática",
             "Alunos matriculados no curso de informática, com horários",
             CORES["secundaria"], self.rel_curso_informatica),

            ("🎟️", "Vagas para o Próximo Ano",
             "Situação das vagas de cada turma para o próximo ano letivo",
             CORES["acento"], self.rel_vagas_proximo_ano),

            ("🖨️", "Declaração de Matrícula",
             "Declaração individual para um aluno",
             CORES["primaria_clara"], self.rel_declaracao),

            ("📁", "Relatório Geral do Sistema",
             "Resumo completo: alunos, professores, turmas e frequência",
             "#7e3af2", self.rel_geral),

            ("🥗", "Relatório de Alergias",
             "Lista alunos com alergias alimentares para a cozinha",
             CORES["perigo"], self.rel_alergias),
            ("🗄", "Arquivo Morto — Resumo",
             "Lista todos os registros arquivados",
             CORES["dourado"], self.rel_arquivo_morto),
        ]

        for i, (icon, titulo, desc, cor, cmd) in enumerate(relatorios):
            card = ctk.CTkFrame(grid, fg_color=CORES["card"], corner_radius=12)
            card.grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="nsew")

            ctk.CTkLabel(card, text=icon, font=fonte(32)).pack(pady=(18, 4))
            ctk.CTkLabel(card, text=titulo, font=fonte(13, "bold"),
                         text_color=CORES["texto"], wraplength=210).pack(padx=10)
            ctk.CTkLabel(card, text=desc, font=fonte(10),
                         text_color=CORES["subtexto"], wraplength=210).pack(padx=15, pady=4)

            # Três botões: Exibir | PDF | Imprimir
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(pady=(6, 18))

            ctk.CTkButton(btn_row, text="👁 Exibir",
                          fg_color=cor,
                          text_color=CORES["texto_claro"] if cor != CORES["dourado"] else CORES["primaria"],
                          font=fonte(11, "bold"),
                          command=lambda c=cmd: c("exibir"), width=80).pack(side="left", padx=3)

            ctk.CTkButton(btn_row, text="📄 PDF",
                          fg_color=CORES["primaria_clara"],
                          text_color=CORES["texto_claro"], font=fonte(10),
                          command=lambda c=cmd: c("pdf"), width=60).pack(side="left", padx=3)

            ctk.CTkButton(btn_row, text="🖨",
                          fg_color=CORES["borda"],
                          text_color=CORES["texto"], font=fonte(10),
                          command=lambda c=cmd: c("print"), width=40).pack(side="left", padx=3)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _exibir_ou_exportar(self, titulo, blocos, nome_arq, modo):
        if modo == "exibir":
            JanelaExibir(self, titulo, blocos)
        elif modo == "pdf":
            pdf_utils.salvar_pdf_como(titulo, blocos, nome_arq, parent=self)
        else:
            pdf_utils.imprimir_pdf(titulo, blocos, nome_arq, parent=self)

    def _selecionar_turma(self, callback):
        conn = get_connection()
        turmas = conn.execute(
            "SELECT id, nome_completo, turno FROM turmas WHERE ativo=1 ORDER BY nome_completo"
        ).fetchall()
        conn.close()
        if not turmas:
            messagebox.showwarning("Atenção", "Nenhuma turma cadastrada.")
            return
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Selecionar Turma")
        win.geometry("340x180")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])
        ctk.CTkLabel(win, text="Selecione a turma:", font=fonte(13),
                     text_color=CORES["subtexto"]).pack(pady=(20, 5))
        d = {f"{t['nome_completo']} ({t['turno']})": t["id"] for t in turmas}
        var = ctk.StringVar(value=list(d.keys())[0])
        ctk.CTkOptionMenu(win, values=list(d.keys()), variable=var, width=280).pack(pady=8)
        ctk.CTkButton(win, text="✔ Confirmar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      command=lambda: [win.destroy(),
                                       callback(d[var.get()], var.get().split(" (")[0])]
                      ).pack(pady=8)

    # ── Relatórios ────────────────────────────────────────────────────────────
    def rel_tamanhos(self, modo="exibir"):
        def gerar(turma_id, turma_nome):
            conn = get_connection()
            res = conn.execute("""
                SELECT a.nome, r.calcado, r.calca_saia, r.camiseta, r.blusa, r.peso, r.altura
                FROM alunos a LEFT JOIN registro_tamanhos r ON r.aluno_id = a.id
                WHERE a.turma_id=? AND a.ativo=1 AND a.arquivado=0 ORDER BY a.nome
            """, (turma_id,)).fetchall()
            conn.close()
            linhas = [["Aluno", "Calçado", "Calça/Saia", "Camiseta", "Blusa", "Peso", "Altura"]]
            for r in res:
                linhas.append([r["nome"], r["calcado"] or "-", r["calca_saia"] or "-",
                               r["camiseta"] or "-", r["blusa"] or "-", r["peso"] or "-", r["altura"] or "-"])
            blocos = [("titulo", f"Registro de Tamanhos — {turma_nome}"), ("tabela", linhas)]
            self._exibir_ou_exportar(
                f"Tamanhos — {turma_nome}", blocos,
                f"Tamanhos_{turma_nome.replace(' ', '_')}.pdf", modo)
        self._selecionar_turma(gerar)

    def rel_lista_alunos(self, modo="exibir"):
        def gerar(turma_id, turma_nome):
            conn = get_connection()
            alunos = conn.execute("""
                SELECT cgm, nome, data_nascimento, sexo, responsavel, telefone_responsavel
                FROM alunos WHERE (turma_id=? OR turma_contraturno_id=?) AND ativo=1 AND arquivado=0 ORDER BY nome
            """, (turma_id, turma_id)).fetchall()
            conn.close()
            from tema import data_bd_para_tela
            linhas = [["Nº", "CGM", "Nome", "Nasc.", "Sexo", "Responsável", "Telefone"]]
            for i, a in enumerate(alunos, 1):
                linhas.append([str(i), a["cgm"] or "-", a["nome"],
                               data_bd_para_tela(a["data_nascimento"]) or "-",
                               a["sexo"] or "-",
                               a["responsavel"] or "-",
                               a["telefone_responsavel"] or "-"])
            blocos = [
                ("titulo", f"Turma: {turma_nome}  |  Data: {date.today().strftime('%d/%m/%Y')}"),
                ("tabela", linhas),
                ("texto",  f"Total: {len(alunos)} alunos"),
            ]
            self._exibir_ou_exportar(
                f"Lista de Alunos — {turma_nome}", blocos,
                f"Lista_Alunos_{turma_nome.replace(' ', '_')}.pdf", modo)
        self._selecionar_turma(gerar)

    def rel_historico_retiradas_estoque(self, modo="exibir"):
        from datetime import date, timedelta
        from tema import mascara_data, data_tela_para_bd, vincular_mascara

        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Movimentações de Estoque - Período")
        win.geometry("380x300")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])

        topo = ctk.CTkFrame(win, fg_color=CORES["primaria"], corner_radius=0, height=50)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="📦 Entradas e Saídas de Material", font=fonte(13, "bold"),
                     text_color=CORES["dourado"]).pack(padx=15, pady=12)

        corpo = ctk.CTkFrame(win, fg_color=CORES["fundo"])
        corpo.pack(fill="both", expand=True, padx=25, pady=15)

        hoje = date.today()
        inicio_padrao = (hoje - timedelta(days=180)).strftime("%d/%m/%Y")

        ctk.CTkLabel(corpo, text="Data de Início", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).pack(anchor="w", pady=(6, 0))
        e_inicio = ctk.CTkEntry(corpo, width=160, placeholder_text="DD/MM/AAAA")
        e_inicio.insert(0, inicio_padrao)
        vincular_mascara(e_inicio, mascara_data)
        e_inicio.pack(anchor="w")

        ctk.CTkLabel(corpo, text="Data Final", font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).pack(anchor="w", pady=(10, 0))
        e_fim = ctk.CTkEntry(corpo, width=160, placeholder_text="DD/MM/AAAA")
        e_fim.insert(0, hoje.strftime("%d/%m/%Y"))
        vincular_mascara(e_fim, mascara_data)
        e_fim.pack(anchor="w")

        def gerar():
            texto_inicio = e_inicio.get().strip()
            texto_fim = e_fim.get().strip()
            data_ini = data_tela_para_bd(texto_inicio)
            data_fim = data_tela_para_bd(texto_fim)
            if not data_ini or not data_fim:
                messagebox.showerror("Erro", "Preencha as duas datas corretamente.", parent=win)
                return
            win.destroy()

            conn = get_connection()
            movs = conn.execute("""
                SELECT m.data, m.tipo, i.nome as item_nome, m.quantidade, m.observacao
                FROM estoque_movimentacoes m LEFT JOIN estoque_itens i ON i.id = m.item_id
                WHERE m.data >= ? AND m.data <= ? ORDER BY m.data DESC
            """, (data_ini, data_fim)).fetchall()
            conn.close()

            from tema import data_bd_para_tela
            linhas = [["Data", "Tipo", "Item", "Quantidade", "Motivo/Observação"]]
            entradas = saidas = 0
            for r in movs:
                tipo_txt = "Entrada" if r["tipo"] == "entrada" else "Saída"
                if r["tipo"] == "entrada":
                    entradas += 1
                else:
                    saidas += 1
                linhas.append([data_bd_para_tela(r["data"]) or r["data"], tipo_txt,
                               r["item_nome"] or "-", str(r["quantidade"]), r["observacao"] or "-"])

            periodo_txt = f"{texto_inicio} a {texto_fim}"
            blocos = [("titulo", f"Movimentações de Estoque — {periodo_txt}"),
                      ("tabela", linhas),
                      ("texto", f"Total: {entradas} entrada(s) e {saidas} saída(s)")]
            self._exibir_ou_exportar("Movimentações de Estoque", blocos,
                                     "Movimentacoes_Estoque.pdf", modo)

        ctk.CTkButton(corpo, text="📄 Gerar Relatório", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=gerar, width=200, height=38).pack(pady=20)

    def rel_fila_espera(self, modo="exibir"):
        from modules.matriculas_shared import ORDEM_SERIES
        conn = get_connection()
        registros = conn.execute(
            "SELECT * FROM fila_espera WHERE excluido IS NULL OR excluido = 0 ORDER BY serie, data_cadastro"
        ).fetchall()
        conn.close()
        linhas = [["Nome", "Nasc.", "Série", "Turno Pref.", "Responsável", "Telefone", "CGM"]]
        por_serie = {}
        for r in registros:
            por_serie.setdefault(r["serie"], []).append(r)
        for serie in ORDEM_SERIES:
            for r in por_serie.get(serie, []):
                linhas.append([r["nome"], r["data_nascimento"] or "-", r["serie"] or "-",
                               r["turno_preferencia"] or "-", r["responsavel"] or "-",
                               r["telefone"] or "-", r["cgm"] or "-"])
        blocos = [("titulo", f"Data: {date.today().strftime('%d/%m/%Y')}"),
                  ("tabela", linhas), ("texto", f"Total: {len(registros)} na fila de espera")]
        self._exibir_ou_exportar("Fila de Espera", blocos, "Fila_de_Espera.pdf", modo)

    def rel_curso_informatica(self, modo="exibir"):
        conn = get_connection()
        registros = conn.execute("""
            SELECT c.nome_aluno, c.serie_turma, d.nome as disciplina_nome,
                   c.dia_semana, c.periodo, c.horario, c.observacao
            FROM curso_informatica c LEFT JOIN disciplinas d ON d.id = c.disciplina_id
            WHERE c.excluido IS NULL OR c.excluido = 0
            ORDER BY c.dia_semana, c.horario, c.nome_aluno
        """).fetchall()
        conn.close()
        linhas = [["Aluno", "Série/Turma", "Disciplina", "Dia", "Período", "Horário", "Observação"]]
        for r in registros:
            linhas.append([r["nome_aluno"], r["serie_turma"] or "-", r["disciplina_nome"] or "-",
                           r["dia_semana"] or "-", r["periodo"] or "-", r["horario"] or "-",
                           r["observacao"] or "-"])
        blocos = [("titulo", f"Data: {date.today().strftime('%d/%m/%Y')}"),
                  ("tabela", linhas), ("texto", f"Total: {len(registros)} matriculado(s)")]
        self._exibir_ou_exportar("Curso de Informática", blocos, "Curso_de_Informatica.pdf", modo)

    def rel_vagas_proximo_ano(self, modo="exibir"):
        from modules.matriculas_shared import listar_turmas_ordenadas, vagas_padrao_para
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

        linhas = [["Turma", "Vagas Totais", "Preenchidas", "Restantes", "Pendentes"]]
        for turma in turmas:
            total = vagas_config.get(turma["id"]) or vagas_padrao_para(turma["nome_completo"])
            preenchidas = cont_por_turma.get(turma["id"], {}).get("matriculado", 0)
            pendentes = cont_por_turma.get(turma["id"], {}).get("pendente", 0)
            linhas.append([f"{turma['nome_completo']} ({turma['turno']})", str(total),
                           str(preenchidas), str(total - preenchidas), str(pendentes)])
        blocos = [("titulo", f"Data: {date.today().strftime('%d/%m/%Y')}"), ("tabela", linhas)]
        self._exibir_ou_exportar("Vagas para o Próximo Ano Letivo", blocos, "Vagas_Proximo_Ano.pdf", modo)

    def rel_lista_professores(self, modo="exibir"):
        conn = get_connection()
        profs = conn.execute("""SELECT nome, cargo, cpf, telefone1, disciplinas, situacao_funcional
            FROM professores WHERE ativo=1 AND arquivado=0 ORDER BY nome""").fetchall()
        conn.close()
        linhas = [["Nome", "Cargo", "CPF", "Telefone", "Disciplinas", "Situação"]]
        for p in profs:
            linhas.append([p["nome"], p["cargo"] or "-", p["cpf"] or "-",
                           p["telefone1"] or "-", p["disciplinas"] or "-",
                           p["situacao_funcional"] or "-"])
        blocos = [("titulo", f"Data: {date.today().strftime('%d/%m/%Y')}"),
                  ("tabela", linhas), ("texto", f"Total: {len(profs)} professores")]
        self._exibir_ou_exportar("Lista de Professores", blocos, "Lista_Professores.pdf", modo)

    def rel_lista_funcionarios(self, modo="exibir"):
        conn = get_connection()
        funcs = conn.execute("""SELECT nome, cargo, cpf, telefone1, situacao_funcional
            FROM funcionarios WHERE ativo=1 AND arquivado=0 ORDER BY nome""").fetchall()
        conn.close()
        linhas = [["Nome", "Cargo", "CPF", "Telefone", "Situação"]]
        for f in funcs:
            linhas.append([f["nome"], f["cargo"] or "-", f["cpf"] or "-",
                           f["telefone1"] or "-", f["situacao_funcional"] or "-"])
        blocos = [("titulo", f"Data: {date.today().strftime('%d/%m/%Y')}"),
                  ("tabela", linhas), ("texto", f"Total: {len(funcs)} funcionários")]
        self._exibir_ou_exportar("Lista de Funcionários", blocos, "Lista_Funcionarios.pdf", modo)

    def rel_boletim_geral(self, modo="exibir"):
        def gerar(turma_id, turma_nome):
            conn = get_connection()
            alunos = conn.execute(
                "SELECT id, nome, cgm FROM alunos WHERE (turma_id=? OR turma_contraturno_id=?) AND ativo=1 AND arquivado=0 ORDER BY nome",
                (turma_id, turma_id)).fetchall()
            discs  = conn.execute(
                "SELECT id, nome FROM disciplinas WHERE turma_id=? AND (excluido IS NULL OR excluido=0) ORDER BY nome",
                (turma_id,)).fetchall()
            blocos = [("titulo", f"Turma: {turma_nome}  |  {date.today().strftime('%d/%m/%Y')}")]
            for aluno in alunos:
                linhas = [["Disciplina", "B1", "B2", "B3", "B4", "Total Anual", "Situação"]]
                for d in discs:
                    notas = {n["bimestre"]: n["total_bimestral"] for n in conn.execute(
                        "SELECT bimestre, total_bimestral FROM notas WHERE aluno_id=? AND disciplina_id=?",
                        (aluno["id"], d["id"])).fetchall()}
                    bims = [str(notas.get(b, "-")) for b in range(1, 5)]
                    vals = [notas[b] for b in range(1, 5) if b in notas]
                    ta   = round(sum(vals), 1) if vals else "-"
                    sit  = ("Aprovado" if isinstance(ta, float) and ta >= 24 else
                            "Reprovado" if isinstance(ta, float) else "—")
                    linhas.append([d["nome"]] + bims + [str(ta), sit])
                blocos.append(("titulo", f"{aluno['nome']}  |  CGM: {aluno['cgm'] or '-'}"))
                blocos.append(("tabela", linhas))
                blocos.append(("espaco", 0.3))
            conn.close()
            self._exibir_ou_exportar(
                f"Boletim Geral — {turma_nome}", blocos,
                f"Boletim_{turma_nome.replace(' ', '_')}.pdf", modo)
        self._selecionar_turma(gerar)

    def rel_frequencia(self, modo="exibir"):
        def gerar(turma_id, turma_nome):
            conn = get_connection()
            res = conn.execute("""
                SELECT a.nome, COUNT(f.id) total, SUM(f.presente) pres,
                       SUM(CASE WHEN f.presente=0 AND f.justificada=0 THEN 1 ELSE 0 END) faltas,
                       ROUND(SUM(f.presente)*100.0/NULLIF(COUNT(f.id),0),1) pct
                FROM alunos a LEFT JOIN frequencia f ON f.aluno_id=a.id
                WHERE (a.turma_id=? OR a.turma_contraturno_id=?) AND a.ativo=1 AND a.arquivado=0 GROUP BY a.id ORDER BY a.nome
            """, (turma_id, turma_id)).fetchall()
            conn.close()
            linhas = [["Nome", "Total Aulas", "Presentes", "Faltas", "% Freq."]]
            for r in res:
                pct = r["pct"] or 0
                linhas.append([r["nome"], str(r["total"] or 0),
                               str(r["pres"] or 0), str(r["faltas"] or 0),
                               f"{pct}%" + (" ⚠" if pct < 75 else "")])
            blocos = [("titulo", f"Turma: {turma_nome}  |  {date.today().strftime('%d/%m/%Y')}"),
                      ("tabela", linhas), ("texto", "⚠ = frequência abaixo de 75%")]
            self._exibir_ou_exportar(
                f"Frequência — {turma_nome}", blocos,
                f"Frequencia_{turma_nome.replace(' ', '_')}.pdf", modo)
        self._selecionar_turma(gerar)

    def rel_baixa_frequencia(self, modo="exibir"):
        conn = get_connection()
        res = conn.execute("""
            SELECT a.nome, a.cgm, t.nome_completo turma, a.responsavel, a.telefone_responsavel,
                   ROUND(SUM(f.presente)*100.0/NULLIF(COUNT(f.id),0),1) pct
            FROM alunos a JOIN turmas t ON a.turma_id=t.id
            LEFT JOIN frequencia f ON f.aluno_id=a.id
            WHERE a.ativo=1 AND a.arquivado=0 GROUP BY a.id
            HAVING pct < 75 OR pct IS NULL ORDER BY pct
        """).fetchall()
        conn.close()
        linhas = [["Nome", "CGM", "Turma", "Freq.", "Responsável", "Telefone"]]
        for r in res:
            linhas.append([r["nome"], r["cgm"] or "-", r["turma"],
                           f"{r['pct'] or 0}%", r["responsavel"] or "-",
                           r["telefone_responsavel"] or "-"])
        blocos = [("titulo", f"Data: {date.today().strftime('%d/%m/%Y')}"),
                  ("tabela", linhas),
                  ("texto", f"Total: {len(res)} aluno(s) com frequência < 75%")]
        self._exibir_ou_exportar("Alunos com Baixa Frequência", blocos, "Baixa_Frequencia.pdf", modo)

    def rel_desempenho(self, modo="exibir"):
        def gerar(turma_id, turma_nome):
            conn = get_connection()
            res = conn.execute("""
                SELECT d.nome, ROUND(AVG(n.total_bimestral),1) media,
                       SUM(CASE WHEN n.total_bimestral>=6 THEN 1 ELSE 0 END) aprov,
                       SUM(CASE WHEN n.total_bimestral<6  THEN 1 ELSE 0 END) reprov
                FROM disciplinas d LEFT JOIN notas n ON n.disciplina_id=d.id
                WHERE d.turma_id=? GROUP BY d.id ORDER BY d.nome
            """, (turma_id,)).fetchall()
            conn.close()
            linhas = [["Disciplina", "Média Geral", "Aprovados", "Reprovados"]]
            for r in res:
                linhas.append([r["nome"], str(r["media"] or "-"),
                               str(r["aprov"] or 0), str(r["reprov"] or 0)])
            blocos = [("titulo", f"Turma: {turma_nome}  |  {date.today().strftime('%d/%m/%Y')}"),
                      ("tabela", linhas)]
            self._exibir_ou_exportar(
                f"Desempenho — {turma_nome}", blocos,
                f"Desempenho_{turma_nome.replace(' ', '_')}.pdf", modo)
        self._selecionar_turma(gerar)

    def rel_turmas_sexo(self, modo="exibir"):
        conn = get_connection()
        res = conn.execute("""
            SELECT t.nome_completo, t.turno, p.nome professor,
                   COUNT(a.id) total,
                   SUM(CASE WHEN a.sexo='Masculino' THEN 1 ELSE 0 END) meninos,
                   SUM(CASE WHEN a.sexo='Feminino'  THEN 1 ELSE 0 END) meninas
            FROM turmas t
            LEFT JOIN alunos a ON a.turma_id=t.id AND a.ativo=1 AND a.arquivado=0
            LEFT JOIN professores p ON t.professor_id=p.id
            WHERE t.ativo=1 GROUP BY t.id ORDER BY t.nome_completo
        """).fetchall()
        conn.close()
        linhas = [["Turma", "Turno", "Professor", "Total", "Meninos", "Meninas"]]
        tg = mg = fg = 0
        for r in res:
            linhas.append([r["nome_completo"], r["turno"], r["professor"] or "—",
                           str(r["total"]), str(r["meninos"] or 0), str(r["meninas"] or 0)])
            tg += r["total"]; mg += r["meninos"] or 0; fg += r["meninas"] or 0
        linhas.append(["TOTAL GERAL", "", "", str(tg), str(mg), str(fg)])
        blocos = [("titulo", f"Data: {date.today().strftime('%d/%m/%Y')}"), ("tabela", linhas)]
        self._exibir_ou_exportar("Alunos por Turma e Sexo", blocos, "Turmas_Sexo.pdf", modo)

    def rel_grade(self, modo="exibir"):
        from tema import DIAS_SEMANA
        from modules.turmas import horarios_por_turno
        def gerar(turma_id, turma_nome):
            conn = get_connection()
            turma = conn.execute("SELECT * FROM turmas WHERE id=?", (turma_id,)).fetchone()
            rows  = conn.execute("""
                SELECT h.dia_semana, h.horario_inicio, h.horario_fim,
                       d.nome disciplina, p.nome professor
                FROM horarios h JOIN disciplinas d ON h.disciplina_id=d.id
                LEFT JOIN professores p ON d.professor_id=p.id
                WHERE h.turma_id=? ORDER BY h.dia_semana, h.horario_inicio
            """, (turma_id,)).fetchall()
            conn.close()
            from collections import defaultdict
            por_dia = defaultdict(list)
            for r in rows: por_dia[r["dia_semana"]].append(r)
            slots  = horarios_por_turno(turma["turno"])
            cab    = ["Aula / Horário"] + DIAS_SEMANA
            linhas = [cab]
            for i, (nome_slot, ini, fim) in enumerate(slots):
                linha = [f"{nome_slot}\n{ini}–{fim}"]
                for dia in DIAS_SEMANA:
                    aulas = por_dia.get(dia, [])
                    if i < len(aulas):
                        a = aulas[i]
                        linha.append(f"{a['disciplina']}\n{a['professor'] or '-'}")
                    else:
                        linha.append("—")
                linhas.append(linha)
            blocos = [
                ("titulo", f"Turma: {turma_nome}  |  Turno: {turma['turno']}"),
                ("tabela", linhas)]
            self._exibir_ou_exportar(
                f"Grade Curricular — {turma_nome}", blocos,
                f"Grade_{turma_nome.replace(' ', '_')}.pdf", modo)
        self._selecionar_turma(gerar)

    def rel_declaracao(self, modo="exibir"):
        conn = get_connection()
        alunos = conn.execute("""SELECT a.id, a.nome, a.cgm, a.data_matricula,
            t.nome_completo turma, t.serie, t.turno
            FROM alunos a LEFT JOIN turmas t ON a.turma_id=t.id
            WHERE a.ativo=1 AND a.arquivado=0 ORDER BY a.nome""").fetchall()
        conn.close()
        if not alunos:
            messagebox.showwarning("Atenção", "Nenhum aluno cadastrado.")
            return
        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title("Declaração de Matrícula")
        win.geometry("380x200")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])
        ctk.CTkLabel(win, text="Selecione o aluno:", font=fonte(13),
                     text_color=CORES["subtexto"]).pack(pady=15)
        d = {f"{a['nome']} (CGM: {a['cgm'] or '-'})": a for a in alunos}
        var = ctk.StringVar(value=list(d.keys())[0])
        ctk.CTkOptionMenu(win, values=list(d.keys()), variable=var, width=320).pack()
        def gerar():
            aluno = d[var.get()]
            from tema import data_bd_para_tela
            texto = (f"Declaramos que {aluno['nome'].upper()} encontra-se regularmente "
                     f"matriculado(a) nesta instituição de ensino, conforme dados abaixo.")
            blocos = [
                ("titulo", "DECLARAÇÃO DE MATRÍCULA"),
                ("texto",  texto), ("espaco", 0.5),
                ("tabela", [["Campo", "Informação"],
                            ["CGM",   aluno["cgm"] or "-"],
                            ["Turma", aluno["turma"] or "-"],
                            ["Série", aluno["serie"] or "-"],
                            ["Turno", aluno["turno"] or "-"],
                            ["Data de Matrícula", data_bd_para_tela(aluno["data_matricula"]) or "-"]]),
                ("espaco", 1.0),
                ("texto",  f"Local e data: ________________________, {date.today().strftime('%d/%m/%Y')}"),
                ("espaco", 1.5),
                ("texto",  "_________________________________\nAssinatura e Carimbo da Secretaria"),
            ]
            win.destroy()
            self._exibir_ou_exportar(
                f"Declaração — {aluno['nome']}", blocos,
                f"Declaracao_{aluno['nome'].replace(' ', '_')}.pdf", modo)
        ctk.CTkButton(win, text="Gerar", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      command=gerar).pack(pady=15)

    def rel_geral(self, modo="exibir"):
        conn = get_connection()
        ta = conn.execute("SELECT COUNT(*) FROM alunos WHERE ativo=1 AND arquivado=0").fetchone()[0]
        tm = conn.execute("SELECT COUNT(*) FROM alunos WHERE ativo=1 AND arquivado=0 AND sexo='Masculino'").fetchone()[0]
        tf = conn.execute("SELECT COUNT(*) FROM alunos WHERE ativo=1 AND arquivado=0 AND sexo='Feminino'").fetchone()[0]
        tp = conn.execute("SELECT COUNT(*) FROM professores WHERE ativo=1 AND arquivado=0").fetchone()[0]
        tfu= conn.execute("SELECT COUNT(*) FROM funcionarios WHERE ativo=1 AND arquivado=0").fetchone()[0]
        tped = conn.execute("SELECT COUNT(*) FROM pedagogas WHERE ativo=1 AND arquivado=0").fetchone()[0]
        tsec = conn.execute("SELECT COUNT(*) FROM secretarios WHERE ativo=1 AND arquivado=0").fetchone()[0]
        tdir = conn.execute("SELECT COUNT(*) FROM diretores WHERE ativo=1 AND arquivado=0").fetchone()[0]
        tt = conn.execute("SELECT COUNT(*) FROM turmas WHERE ativo=1").fetchone()[0]
        bx = conn.execute("""SELECT COUNT(*) FROM (
            SELECT a.id, ROUND(SUM(f.presente)*100.0/NULLIF(COUNT(f.id),0),1) pct
            FROM alunos a LEFT JOIN frequencia f ON f.aluno_id=a.id
            WHERE a.ativo=1 AND a.arquivado=0 GROUP BY a.id HAVING pct < 75)""").fetchone()[0]

        # Atividades extracurriculares
        try:
            t_fila = conn.execute("SELECT COUNT(*) FROM fila_espera WHERE excluido IS NULL OR excluido=0").fetchone()[0]
        except Exception:
            t_fila = 0
        try:
            t_info = conn.execute("SELECT COUNT(*) FROM curso_informatica WHERE excluido IS NULL OR excluido=0").fetchone()[0]
        except Exception:
            t_info = 0
        try:
            t_fanfarra = conn.execute("SELECT COUNT(*) FROM fanfarra_membros WHERE categoria='FANFARRA'").fetchone()[0]
            t_baliza = conn.execute("SELECT COUNT(*) FROM fanfarra_membros WHERE categoria='BALIZA'").fetchone()[0]
        except Exception:
            t_fanfarra = t_baliza = 0
        try:
            t_xadrez = conn.execute("SELECT COUNT(*) FROM xadrez_membros").fetchone()[0]
        except Exception:
            t_xadrez = 0

        # Estoque abaixo do mínimo
        try:
            itens_baixo = conn.execute("""SELECT nome, quantidade, estoque_minimo FROM estoque_itens
                WHERE (excluido IS NULL OR excluido=0) AND quantidade < estoque_minimo
                ORDER BY nome""").fetchall()
        except Exception:
            itens_baixo = []

        conn.close()
        blocos = [
            ("titulo", f"Data de geração: {date.today().strftime('%d/%m/%Y')}"),
            ("titulo", "Resumo de Alunos"),
            ("tabela", [["Indicador", "Qtd."],
                        ["Alunos ativos", str(ta)], ["Meninos", str(tm)],
                        ["Meninas", str(tf)], ["Baixa frequência (<75%)", str(bx)],
                        ["Fila de espera", str(t_fila)]]),
            ("titulo", "Equipe Escolar"),
            ("tabela", [["Categoria", "Ativos"],
                        ["Professores", str(tp)], ["Funcionários", str(tfu)],
                        ["Pedagogas", str(tped)], ["Secretários(as)", str(tsec)],
                        ["Diretores(as)", str(tdir)], ["Turmas ativas", str(tt)]]),
            ("titulo", "Atividades Extracurriculares"),
            ("tabela", [["Atividade", "Alunos"],
                        ["Curso de Informática", str(t_info)],
                        ["Fanfarra", str(t_fanfarra)],
                        ["Baliza", str(t_baliza)],
                        ["Xadrez", str(t_xadrez)]]),
        ]

        if itens_baixo:
            tabela_estoque = [["Item", "Quantidade Atual", "Estoque Mínimo"]]
            for it in itens_baixo:
                tabela_estoque.append([it["nome"], str(it["quantidade"]), str(it["estoque_minimo"])])
            blocos.append(("titulo", f"⚠ Itens Abaixo do Estoque Mínimo ({len(itens_baixo)})"))
            blocos.append(("tabela", tabela_estoque))
        else:
            blocos.append(("titulo", "Estoque"))
            blocos.append(("texto", "Nenhum item abaixo do estoque mínimo no momento."))

        self._exibir_ou_exportar("Relatório Geral do Sistema", blocos, "Relatorio_Geral.pdf", modo)

    def rel_arquivo_morto(self, modo="exibir"):
        conn = get_connection()
        aa = conn.execute("SELECT nome, data_arquivamento FROM alunos WHERE arquivado=1 ORDER BY nome").fetchall()
        ap = conn.execute("SELECT nome, data_arquivamento FROM professores WHERE arquivado=1 ORDER BY nome").fetchall()
        af = conn.execute("SELECT nome, data_arquivamento FROM funcionarios WHERE arquivado=1 ORDER BY nome").fetchall()
        conn.close()
        from tema import data_bd_para_tela
        blocos = [("titulo", f"Data: {date.today().strftime('%d/%m/%Y')}")]
        for titulo, lista in [("Alunos", aa), ("Professores", ap), ("Funcionários", af)]:
            linhas = [["Nome", "Arquivado em"]]
            for r in lista:
                linhas.append([r["nome"], data_bd_para_tela(r["data_arquivamento"]) or "-"])
            blocos.append(("titulo", f"{titulo} ({len(lista)} registro(s))"))
            blocos.append(("tabela", linhas))
        self._exibir_ou_exportar("Arquivo Morto — Resumo", blocos, "Arquivo_Morto.pdf", modo)
    
    
    def rel_alergias(self, modo="exibir"):
        conn = get_connection()
        # Busca alunos que:
        # 1. Tenham 'Sim' no campo alergico (caixa de seleção)
        # 2. OU tenham qualquer texto preenchido na descrição da alergia
        res = conn.execute("""
            SELECT a.nome, t.nome_completo as turma, a.alergia_descricao, a.alergico
            FROM alunos a
            LEFT JOIN turmas t ON a.turma_id = t.id
            WHERE (a.alergico = 'Sim' OR (a.alergia_descricao IS NOT NULL AND a.alergia_descricao != ''))
              AND a.ativo = 1 AND a.arquivado = 0
            ORDER BY t.nome_completo, a.nome
        """).fetchall()
        conn.close()

        linhas = [["Aluno", "Turma", "Descrição da Alergia"]]
        for r in res:
            # Se a descrição estiver vazia mas marcou 'Sim', coloca um aviso
            desc = r["alergia_descricao"]
            if (not desc or desc.strip() == "") and r["alergico"] == "Sim":
                desc = "(Marcado como Sim, mas sem detalhes)"
            elif not desc:
                desc = "Não informada"
                
            linhas.append([
                r["nome"], 
                r["turma"] or "Sem Turma", 
                desc
            ])

        from datetime import date
        blocos = [
            ("titulo", "RELATÓRIO DE ALERGIA ALIMENTAR - COZINHA"),
            ("titulo", f"Data de Emissão: {date.today().strftime('%d/%m/%Y')}"),
            ("espaco", 0.5),
            ("tabela", linhas),
            ("espaco", 1.0),
            ("texto", f"Total de alunos listados: {len(res)}"),
            ("espaco", 0.5),
            ("texto", "Atenção Equipe da Cozinha: Favor verificar os detalhes de cada restrição acima.")
        ]
        
        self._exibir_ou_exportar(
            "Relatorio_Alergias_Cozinha", blocos, 
            "Relatorio_Alergias.pdf", modo
        )
