"""
Painel: Dashboard Geral.
Mostra números combinados de todas as escolas cadastradas, mais uma
tabela de comparação escola por escola.
"""
import streamlit as st
import pandas as pd
from secretaria_modules.dados_escolas import carregar_tabela_combinada, listar_escolas, filtrar_ativos


def _metric(valor, rotulo):
    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-valor">{valor}</div>
            <div class="metric-label">{rotulo}</div>
        </div>
    """, unsafe_allow_html=True)


def render():
    st.markdown('<div class="titulo-secao">📊 Dashboard Geral — Todas as Escolas</div>', unsafe_allow_html=True)

    escolas = listar_escolas()
    if not escolas:
        st.warning("Nenhuma escola cadastrada ainda nos Secrets do app. "
                   "Cadastre cada escola no formato [escola_1], [escola_2], etc.")
        return

    df_alunos, escolas_com_erro = carregar_tabela_combinada("alunos", "id,nome,sexo,ativo,arquivado")
    df_professores, _ = carregar_tabela_combinada("professores", "id,ativo,arquivado")
    df_turmas, _ = carregar_tabela_combinada("turmas", "id,ativo")

    if not df_alunos.empty:
        df_alunos = filtrar_ativos(df_alunos)

    total_alunos = len(df_alunos)
    total_professores = len(df_professores) if not df_professores.empty else 0
    total_turmas = len(df_turmas) if not df_turmas.empty else 0
    total_escolas = len(escolas)

    st.markdown('<div class="painel">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric(total_escolas, "Escolas conectadas")
    with c2: _metric(total_alunos, "Alunos ativos (total)")
    with c3: _metric(total_professores, "Professores (total)")
    with c4: _metric(total_turmas, "Turmas ativas (total)")
    st.markdown('</div>', unsafe_allow_html=True)

    if escolas_com_erro:
        st.warning(f"⚠️ Não consegui buscar dados de: {', '.join(escolas_com_erro)} "
                   "(pode estar temporariamente fora do ar)")

    st.markdown('<div class="painel">', unsafe_allow_html=True)
    st.markdown('<div class="titulo-secao" style="font-size:16px;">📋 Comparativo por Escola</div>',
               unsafe_allow_html=True)
    if not df_alunos.empty:
        resumo = df_alunos.groupby("escola").size().reset_index(name="Alunos Ativos")
        if not df_professores.empty:
            prof_por_escola = df_professores.groupby("escola").size().reset_index(name="Professores")
            resumo = resumo.merge(prof_por_escola, on="escola", how="left")
        if not df_turmas.empty:
            turmas_por_escola = df_turmas.groupby("escola").size().reset_index(name="Turmas")
            resumo = resumo.merge(turmas_por_escola, on="escola", how="left")
        resumo = resumo.fillna(0)
        st.dataframe(resumo, use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há dados de alunos para exibir.")
    st.markdown('</div>', unsafe_allow_html=True)
