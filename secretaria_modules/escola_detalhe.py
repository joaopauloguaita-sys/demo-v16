"""
Painel: Escola por Escola.
Uma aba pra cada escola (até 10, hoje) — mostra os dados daquela escola
específica: sub-dashboard e botões pra ver Alunos com Necessidades
Especiais, Professores, Gestão e Equipe (Diretor/Pedagogas/Secretário/
Funcionários) e Dados da Escola.

Pra aumentar de 10 pra mais escolas: só muda o número MAX_ESCOLAS aqui
embaixo — o resto se ajusta sozinho.
"""
import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF
from secretaria_modules.dados_escolas import listar_escolas, buscar_tabela_de_uma_escola, link_whatsapp

MAX_ESCOLAS = 10


def _texto_pdf(txt):
    """Garante que acentos não quebrem o PDF (fonte padrão só suporta latin-1)."""
    return str(txt).encode("latin-1", "replace").decode("latin-1")


def _gerar_pdf_tabela(titulo, nome_escola, cabecalhos, linhas):
    """Monta um PDF simples de tabela, pronto pra imprimir."""
    paisagem = len(cabecalhos) > 4
    pdf = FPDF(orientation="L" if paisagem else "P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 9, _texto_pdf(titulo), ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, _texto_pdf(nome_escola), ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Gerado em {date.today().strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(4)

    largura_pagina = pdf.w - 20
    largura_col = largura_pagina / len(cabecalhos)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(30, 40, 90)
    pdf.set_text_color(255, 255, 255)
    for c in cabecalhos:
        pdf.cell(largura_col, 8, _texto_pdf(c), border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    for i, linha in enumerate(linhas):
        pdf.set_fill_color(240, 240, 248) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        for valor in linha:
            pdf.cell(largura_col, 7, _texto_pdf(valor), border=1, fill=True)
        pdf.ln()

    return bytes(pdf.output())


def _metric(valor, rotulo):
    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-valor">{valor}</div>
            <div class="metric-label">{rotulo}</div>
        </div>
    """, unsafe_allow_html=True)


def _tabela_com_links(df, colunas_map, col_pasta=None, col_whatsapp=None):
    """Mostra um DataFrame como tabela, com colunas de pasta/whatsapp
    viram links clicáveis de verdade."""
    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    df = df.rename(columns=colunas_map)
    config = {}
    if col_pasta and colunas_map.get(col_pasta, col_pasta) in df.columns:
        config[colunas_map.get(col_pasta, col_pasta)] = st.column_config.LinkColumn(
            "Pasta (Drive)", display_text="📁 Abrir")
    if col_whatsapp and colunas_map.get(col_whatsapp, col_whatsapp) in df.columns:
        config[colunas_map.get(col_whatsapp, col_whatsapp)] = st.column_config.LinkColumn(
            "WhatsApp", display_text="💬 Abrir")

    st.dataframe(df, use_container_width=True, hide_index=True, column_config=config)


def _sub_dashboard(escola_id):
    df_alunos = buscar_tabela_de_uma_escola(escola_id, "alunos",
        "id,nome,sexo,ativo,arquivado,turma_id,data_nascimento,pasta_documentos,"
        "telefone_responsavel,tipos_deficiencia,necessidades_especiais")
    df_professores = buscar_tabela_de_uma_escola(escola_id, "professores", "id,ativo,arquivado")
    df_funcionarios = buscar_tabela_de_uma_escola(escola_id, "funcionarios", "id,ativo,arquivado")
    df_turmas = buscar_tabela_de_uma_escola(escola_id, "turmas", "id,ativo")
    df_diretores = buscar_tabela_de_uma_escola(escola_id, "diretores", "id,nome,ativo,arquivado")
    df_pedagogas = buscar_tabela_de_uma_escola(escola_id, "pedagogas", "id,nome,ativo,arquivado")

    if not df_alunos.empty:
        df_alunos_ativos = df_alunos[
            (df_alunos["ativo"].astype(str).isin(["1", "True", "1.0"])) &
            (~df_alunos["arquivado"].astype(str).isin(["1", "True", "1.0"]))]
    else:
        df_alunos_ativos = df_alunos

    meninos = len(df_alunos_ativos[df_alunos_ativos.get("sexo", "") == "Masculino"]) if not df_alunos_ativos.empty else 0
    meninas = len(df_alunos_ativos[df_alunos_ativos.get("sexo", "") == "Feminino"]) if not df_alunos_ativos.empty else 0

    def _ativos(df):
        if df.empty:
            return df
        return df[(df["ativo"].astype(str).isin(["1", "True", "1.0"])) &
                  (~df.get("arquivado", pd.Series(dtype=str)).astype(str).isin(["1", "True", "1.0"]))]

    n_professores = len(_ativos(df_professores))
    n_funcionarios = len(_ativos(df_funcionarios))
    n_turmas = len(df_turmas[df_turmas["ativo"].astype(str).isin(["1", "True", "1.0"])]) if not df_turmas.empty else 0

    try:
        n_informatica = len(buscar_tabela_de_uma_escola(escola_id, "curso_informatica", "id"))
    except Exception:
        n_informatica = 0
    try:
        n_xadrez = len(buscar_tabela_de_uma_escola(escola_id, "xadrez_membros", "id"))
    except Exception:
        n_xadrez = 0
    try:
        n_fila = len(buscar_tabela_de_uma_escola(escola_id, "fila_espera", "id"))
    except Exception:
        n_fila = 0

    nomes_diretores = ", ".join(_ativos(df_diretores)["nome"].tolist()) if not df_diretores.empty else "—"
    nomes_pedagogas = ", ".join(_ativos(df_pedagogas)["nome"].tolist()) if not df_pedagogas.empty else "—"

    st.markdown('<div class="painel">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1: _metric(len(df_alunos_ativos), "Alunos ativos")
    with c2: _metric(meninos, "Meninos")
    with c3: _metric(meninas, "Meninas")
    c4, c5, c6 = st.columns(3, gap="medium")
    with c4: _metric(n_turmas, "Turmas")
    with c5: _metric(n_professores, "Professores")
    with c6: _metric(n_funcionarios, "Funcionários")
    c7, c8, c9 = st.columns(3, gap="medium")
    with c7: _metric(n_informatica, "Alunos — Informática")
    with c8: _metric(n_xadrez, "Alunos — Xadrez")
    with c9: _metric(n_fila, "Fila de Espera")
    st.markdown(f"""
        <div style="margin-top:15px; color:#c9cfe8;">
            <b>👤 Diretor(a):</b> {nomes_diretores} &nbsp;&nbsp;&nbsp;
            <b>📘 Pedagogas:</b> {nomes_pedagogas}
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    return df_alunos


def _botao_necessidades_especiais(escola_id, df_alunos):
    with st.expander("🧩 Alunos com Necessidades Especiais"):
        if df_alunos.empty:
            st.info("Nenhum aluno encontrado.")
            return

        def _coluna_texto(df, nome):
            if nome in df.columns:
                return df[nome].fillna("").astype(str).str.strip()
            return pd.Series([""] * len(df), index=df.index)

        col_def = _coluna_texto(df_alunos, "tipos_deficiencia")
        col_nec = _coluna_texto(df_alunos, "necessidades_especiais")
        alvo = df_alunos[(col_def != "") | (col_nec != "")].copy()
        if alvo.empty:
            st.info("Nenhum aluno com necessidades especiais registradas.")
            return

        df_turmas = buscar_tabela_de_uma_escola(escola_id, "turmas", "id,nome_completo")
        if not df_turmas.empty:
            mapa = dict(zip(df_turmas["id"].astype(str), df_turmas["nome_completo"]))
            alvo["turma_id_str"] = alvo["turma_id"].astype(str).str.replace(r"\.0$", "", regex=True)
            alvo["Turma"] = alvo["turma_id_str"].map(mapa).fillna("—")
        else:
            alvo["Turma"] = "—"

        alvo["WhatsApp"] = alvo["telefone_responsavel"].apply(link_whatsapp)
        tabela = alvo[["nome", "Turma", "data_nascimento", "pasta_documentos", "WhatsApp"]]
        _tabela_com_links(
            tabela,
            colunas_map={"nome": "Nome", "data_nascimento": "Nascimento", "pasta_documentos": "Pasta"},
            col_pasta="pasta_documentos", col_whatsapp="WhatsApp")


def _botao_professores(escola_id):
    with st.expander("👨‍🏫 Professores"):
        df = buscar_tabela_de_uma_escola(escola_id, "professores",
            "id,nome,cargo,situacao_funcional,telefone1,pasta_documentos,ativo,arquivado")
        if df.empty:
            st.info("Nenhum professor encontrado.")
            return
        df = df[(df["ativo"].astype(str).isin(["1", "True", "1.0"])) &
               (~df["arquivado"].astype(str).isin(["1", "True", "1.0"]))]
        tabela = df[["nome", "cargo", "situacao_funcional", "telefone1", "pasta_documentos"]]
        _tabela_com_links(
            tabela,
            colunas_map={"nome": "Nome", "cargo": "Cargo", "situacao_funcional": "Situação Funcional",
                        "telefone1": "Telefone", "pasta_documentos": "Pasta"},
            col_pasta="pasta_documentos")


def _botao_gestao_equipe(escola_id):
    with st.expander("🏫 Gestão e Equipe (Diretor(a) / Pedagogas / Secretário(a) / Funcionários)"):
        categorias = [
            ("diretores", "🏛 Diretor(a)"),
            ("pedagogas", "📘 Pedagogas"),
            ("secretarios", "🗂️ Secretário(a)"),
            ("funcionarios", "🧑‍💼 Funcionários"),
        ]
        for tabela_nome, titulo in categorias:
            st.markdown(f"**{titulo}**")
            df = buscar_tabela_de_uma_escola(escola_id, tabela_nome,
                "id,nome,cargo,situacao_funcional,telefone1,pasta_documentos,ativo,arquivado")
            if df.empty:
                st.caption("Nenhum registro.")
                continue
            df = df[(df["ativo"].astype(str).isin(["1", "True", "1.0"])) &
                   (~df["arquivado"].astype(str).isin(["1", "True", "1.0"]))]
            tabela = df[["nome", "cargo", "situacao_funcional", "telefone1", "pasta_documentos"]]
            _tabela_com_links(
                tabela,
                colunas_map={"nome": "Nome", "cargo": "Cargo", "situacao_funcional": "Situação Funcional",
                            "telefone1": "Telefone", "pasta_documentos": "Pasta"},
                col_pasta="pasta_documentos")


def _botao_estoque_baixo(escola_id, nome_escola):
    with st.expander("📦 Materiais Abaixo do Estoque Mínimo"):
        df = buscar_tabela_de_uma_escola(escola_id, "estoque_itens",
            "nome,quantidade,estoque_minimo,unidade,excluido")
        if df.empty:
            st.info("Nenhum item de estoque cadastrado.")
            return
        if "excluido" in df.columns:
            df = df[~df["excluido"].astype(str).isin(["1", "True", "1.0"])]
        df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)
        df["estoque_minimo"] = pd.to_numeric(df["estoque_minimo"], errors="coerce").fillna(0)
        baixo = df[df["quantidade"] < df["estoque_minimo"]].copy()
        if baixo.empty:
            st.success("Nenhum item abaixo do estoque mínimo no momento. ✅")
            return
        baixo["Falta"] = (baixo["estoque_minimo"] - baixo["quantidade"]).astype(int)
        tabela = baixo.rename(columns={
            "nome": "Item", "quantidade": "Estoque Atual",
            "estoque_minimo": "Estoque Mínimo", "unidade": "Unidade"})
        st.dataframe(tabela[["Item", "Estoque Atual", "Estoque Mínimo", "Falta", "Unidade"]],
                     use_container_width=True, hide_index=True)

        linhas_pdf = [[r["Item"], r["Estoque Atual"], r["Estoque Mínimo"], r["Falta"], r["Unidade"]]
                     for _, r in tabela.iterrows()]
        pdf_bytes = _gerar_pdf_tabela("Materiais Abaixo do Estoque Mínimo", nome_escola,
                                      ["Item", "Estoque Atual", "Estoque Mínimo", "Falta", "Unidade"], linhas_pdf)
        st.download_button("📄 Gerar PDF pra Imprimir", data=pdf_bytes,
                           file_name=f"estoque_baixo_{escola_id}.pdf", mime="application/pdf",
                           key=f"pdf_estoque_{escola_id}")


def _botao_medidas(escola_id, nome_escola):
    with st.expander("📏 Medidas Individuais dos Alunos"):
        df_med = buscar_tabela_de_uma_escola(escola_id, "registro_tamanhos",
            "aluno_id,calcado,calca_saia,camiseta,blusa")
        if df_med.empty:
            st.info("Nenhuma medida cadastrada ainda.")
            return
        df_alunos = buscar_tabela_de_uma_escola(escola_id, "alunos", "id,nome,turma_id,ativo,arquivado")
        df_turmas = buscar_tabela_de_uma_escola(escola_id, "turmas", "id,nome_completo")

        df_alunos = df_alunos[(df_alunos["ativo"].astype(str).isin(["1", "True", "1.0"])) &
                              (~df_alunos["arquivado"].astype(str).isin(["1", "True", "1.0"]))]

        combinado = df_med.merge(df_alunos, left_on="aluno_id", right_on="id", how="inner")
        if not df_turmas.empty:
            mapa = dict(zip(df_turmas["id"].astype(str), df_turmas["nome_completo"]))
            combinado["turma_id_str"] = combinado["turma_id"].astype(str).str.replace(r"\.0$", "", regex=True)
            combinado["Turma"] = combinado["turma_id_str"].map(mapa).fillna("Sem Turma")
        else:
            combinado["Turma"] = "Sem Turma"

        combinado = combinado.sort_values(["Turma", "nome"])
        tabela = combinado.rename(columns={
            "nome": "Nome", "calcado": "Calçado", "calca_saia": "Calça/Saia",
            "camiseta": "Camiseta", "blusa": "Blusa"})
        colunas_finais = ["Turma", "Nome", "Calçado", "Calça/Saia", "Camiseta", "Blusa"]
        st.dataframe(tabela[colunas_finais], use_container_width=True, hide_index=True)

        linhas_pdf = [[r[c] for c in colunas_finais] for _, r in tabela.iterrows()]
        pdf_bytes = _gerar_pdf_tabela("Medidas Individuais dos Alunos", nome_escola, colunas_finais, linhas_pdf)
        st.download_button("📄 Gerar PDF pra Imprimir", data=pdf_bytes,
                           file_name=f"medidas_{escola_id}.pdf", mime="application/pdf",
                           key=f"pdf_medidas_{escola_id}")


def _botao_dados_escola(escola_id):
    with st.expander("🏢 Dados da Escola"):
        df = buscar_tabela_de_uma_escola(escola_id, "dados_escola", "*")
        if df.empty:
            st.info("Dados da escola não cadastrados.")
            return
        d = df.iloc[0].to_dict()
        OCULTOS = ["base64", "api_key", "apikey", "senha", "password", "token", "id"]
        cols = st.columns(2)
        i = 0
        for k, v in d.items():
            if any(o in k.lower() for o in OCULTOS):
                continue
            if v is None or str(v).strip() in ("", "nan", "None"):
                continue
            with cols[i % 2]:
                st.write(f"**{k.upper().replace('_', ' ')}:** {v}")
            i += 1


def render():
    st.markdown('<div class="titulo-secao">🏫 Escola por Escola</div>', unsafe_allow_html=True)

    escolas_conectadas = {e["id"]: e for e in listar_escolas()}

    rotulos = []
    ids_em_ordem = []
    for i in range(1, MAX_ESCOLAS + 1):
        escola_id = f"escola_{i}"
        if escola_id in escolas_conectadas:
            rotulos.append(escolas_conectadas[escola_id]["nome"])
        else:
            rotulos.append(f"Escola {i} — não conectada")
        ids_em_ordem.append(escola_id)

    abas = st.tabs(rotulos)
    for aba, escola_id, rotulo in zip(abas, ids_em_ordem, rotulos):
        with aba:
            if escola_id not in escolas_conectadas:
                st.info("Essa escola ainda não foi conectada. Cadastre as credenciais dela "
                       f"nos Secrets do app, no bloco [{escola_id}].")
                continue
            df_alunos = _sub_dashboard(escola_id)
            _botao_necessidades_especiais(escola_id, df_alunos)
            _botao_professores(escola_id)
            _botao_gestao_equipe(escola_id)
            _botao_estoque_baixo(escola_id, rotulo)
            _botao_medidas(escola_id, rotulo)
            _botao_dados_escola(escola_id)
