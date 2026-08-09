import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import unicodedata
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import SUPABASE_URL, SUPABASE_KEY, supabase_configurado
from logger_config import get_logger

logger = get_logger(__name__)

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(page_title="João - Secretário Escolar - Gestão", page_icon="🏫", layout="wide", initial_sidebar_state="expanded")

# =========================================================
# ESTILO — TEMA ESCURO
# =========================================================
st.markdown("""
    <style>
    /* Fundo geral escuro */
    .stApp {
        background: linear-gradient(180deg, #0b0f2b 0%, #10163a 100%);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e27 0%, #0d1230 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] * { color: #d7dcf5 !important; }

    h1, h2, h3, h4, h5, p, span, label, .stMarkdown { color: #e8eaf6; }

    /* Esconde header/footer padrão do streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ---------- CABEÇALHO ---------- */
    .header-card {
        background: linear-gradient(135deg, #1a2151 0%, #12183a 100%);
        border-radius: 18px;
        padding: 22px 28px;
        display: flex;
        align-items: center;
        gap: 20px;
        border: 1px solid rgba(255,255,255,0.07);
        margin-bottom: 24px;
    }
    .logo-circle {
        width: 64px; height: 64px;
        border-radius: 16px;
        background: linear-gradient(135deg, #2e3a8c, #4a5fd6);
        display: flex; align-items: center; justify-content: center;
        font-size: 32px;
        flex-shrink: 0;
        box-shadow: 0 4px 14px rgba(74,95,214,0.4);
    }
    .badge {
        display: inline-block;
        background: rgba(255,196,0,0.15);
        color: #ffc400 !important;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1px;
        margin-right: 6px;
    }
    .badge-blue {
        display: inline-block;
        background: rgba(90,120,255,0.15);
        color: #7f9dff !important;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .school-name { font-size: 24px; font-weight: 800; color: #ffffff !important; margin: 4px 0; }

    /* ---------- CARDS DE MÉTRICA ---------- */
    .metric-card {
        background: linear-gradient(135deg, #1a2151 0%, #141a3d 100%);
        border-radius: 16px;
        padding: 18px 20px;
        border: 1px solid rgba(255,255,255,0.06);
        height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-icon {
        width: 38px; height: 38px;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 18px;
        margin-bottom: 10px;
    }
    .metric-val { font-size: 30px; font-weight: 800; color: #ffffff !important; line-height: 1; }
    .metric-label { font-size: 11px; color: #9aa4c7 !important; font-weight: 700; letter-spacing: 0.6px; margin-top: 6px; text-transform: uppercase; }
    .metric-sub { font-size: 11px; color: #6c7aa8 !important; margin-top: 3px; }

    .icon-blue    { background: rgba(90,120,255,0.18); }
    .icon-cyan    { background: rgba(0,210,211,0.18); }
    .icon-pink    { background: rgba(255,92,168,0.18); }
    .icon-green   { background: rgba(46,213,115,0.18); }
    .icon-red     { background: rgba(255,71,87,0.18); }
    .icon-purple  { background: rgba(163,102,255,0.18); }
    .icon-yellow  { background: rgba(255,196,0,0.18); }
    .icon-orange  { background: rgba(255,140,66,0.18); }

    /* ---------- SEÇÕES ---------- */
    .section-title {
        font-size: 16px; font-weight: 800; color: #ffffff !important;
        border-left: 4px solid #4a5fd6; padding-left: 10px; margin: 10px 0 14px 0;
    }
    .panel {
        background: linear-gradient(135deg, #1a2151 0%, #141a3d 100%);
        border-radius: 16px;
        padding: 18px 20px;
        border: 1px solid rgba(255,255,255,0.06);
    }

    /* ---------- EXPANDER (ALUNOS) ---------- */
    .stExpander {
        background: linear-gradient(135deg, #1a2151 0%, #141a3d 100%) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        margin-bottom: 8px;
    }
    .stExpander p, .stExpander span, .stExpander label, .stExpander div, .stExpander b, .stExpander li {
        color: #e8eaf6 !important;
    }
    .stExpander summary { font-weight: 800 !important; color: #ffffff !important; }

    /* Inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #141a3d !important;
        color: #e8eaf6 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* Botões */
    .stButton button, .stLinkButton a {
        border-radius: 10px !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# CONEXÃO SUPABASE (credenciais lidas de .env via config.py)
# =========================================================
if not supabase_configurado():
    st.error("Credenciais do Supabase não configuradas. Verifique o arquivo .env.")
    st.stop()

@st.cache_data(ttl=10)
def fetch(table):
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}",
                          headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
                          timeout=15)
        return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
    except requests.exceptions.RequestException as e:
        logger.error("Erro ao buscar tabela %s do Supabase: %s", table, e)
        return pd.DataFrame()

df_alunos = fetch("alunos")
df_turmas = fetch("turmas")
df_escola = fetch("dados_escola")
df_professores = fetch("professores")
df_funcionarios = fetch("funcionarios")
df_diretores = fetch("diretores")
df_secretarios = fetch("secretarios")

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def conta_positivo(df, col):
    """Conta quantos registros têm valor 'preenchido/positivo' em uma coluna de texto."""
    if df.empty or col not in df.columns:
        return 0
    serie = df[col].astype(str).str.strip().str.lower()
    negativos = ['', 'nan', 'none', 'não', 'nao', '0', 'não possui', 'nao possui',
                 'nenhuma', 'nenhum', 'n/a', 'na', '-']
    return int((~serie.isin(negativos)).sum())

def classificar_sexo(valor):
    """Normaliza valores variados de sexo/gênero em 'M' ou 'F'."""
    v = str(valor).strip().upper()
    if v in ['M', 'MASC', 'MASCULINO', '1']:
        return 'M'
    if v in ['F', 'FEM', 'FEMININO', '2']:
        return 'F'
    return None

WHATSAPP_ICON_SVG = ('<svg viewBox="0 0 32 32" width="26" height="26" xmlns="http://www.w3.org/2000/svg">'
                      '<circle cx="16" cy="16" r="16" fill="#25D366"/>'
                      '<path fill="#fff" d="M23.6 8.4c-2-2-4.7-3.1-7.6-3.1-5.9 0-10.7 4.8-10.7 10.7 0 1.9.5 3.7 1.4 5.3'
                      'L5 27l5.9-1.5c1.5.8 3.2 1.2 4.9 1.2h0c5.9 0 10.7-4.8 10.7-10.7 0-2.9-1.1-5.6-3.1-7.6zM16 24.8'
                      'c-1.5 0-3-.4-4.3-1.2l-.3-.2-3.5.9.9-3.4-.2-.3c-.9-1.4-1.3-3-1.3-4.6 0-4.8 3.9-8.7 8.7-8.7'
                      '2.3 0 4.5.9 6.1 2.6 1.6 1.6 2.6 3.8 2.6 6.1 0 4.8-3.9 8.7-8.7 8.7zm4.8-6.5c-.3-.1-1.6-.8-1.8-.9'
                      'c-.2-.1-.4-.1-.6.1-.2.3-.7.9-.8 1-.1.2-.3.2-.6.1-.3-.1-1.2-.4-2.2-1.4-.8-.7-1.4-1.6-1.5-1.9'
                      'c-.2-.3 0-.4.1-.6.1-.1.3-.3.4-.5.1-.2.2-.3.3-.5.1-.2 0-.4 0-.5C14 12.9 13.5 11.7 13.3 11.2'
                      'c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5.1-.7.3-.2.3-1 .9-1 2.3 0 1.3.9 2.6 1.1 2.8.1.2 1.9 2.9 4.6 4.1'
                      'c.6.3 1.1.4 1.5.6.6.2 1.2.2 1.6.1.5-.1 1.6-.6 1.8-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3z"/></svg>')

def link_whatsapp(numero, titulo):
    """Gera um link clicável apenas com o ícone do WhatsApp (sem texto)."""
    clean = "".join(filter(str.isdigit, str(numero)))
    if len(clean) < 8:
        return ""
    return (f'<a href="https://wa.me/55{clean}" target="_blank" title="WhatsApp {titulo}" '
            f'style="display:inline-block;margin-right:8px;text-decoration:none;vertical-align:middle;">'
            f'{WHATSAPP_ICON_SVG}</a>')

def chave_alfabetica(serie):
    """Chave de ordenação que ignora acentos e caixa (A-Z correto em português)."""
    return serie.astype(str).apply(
        lambda s: unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode().upper()
    )

def classificar_situacao_funcional(valor):
    """Agrupa a coluna situacao_funcional em PSS / Concursado / Terceirizado / Outros."""
    v = str(valor).strip().upper()
    if 'PSS' in v:
        return 'PSS'
    if 'CONCURS' in v or 'EFETIV' in v:
        return 'Concursado'
    if 'TERCEIR' in v:
        return 'Terceirizado'
    if v in ['', 'NAN', 'NONE', '-']:
        return None
    return 'Outros'

def encontrar_coluna_sexo(df):
    for candidato in ['sexo', 'genero', 'gênero', 'sex']:
        if candidato in df.columns:
            return candidato
    return None

def obter_responsavel(df):
    """Pega o nome do responsável ativo em tabelas como diretores/secretarios,
    detectando automaticamente a coluna de nome (nome, nome_completo, etc.)."""
    if df.empty:
        return None
    dtemp = df.copy()
    if 'ativo' in dtemp.columns:
        ativos = dtemp[dtemp['ativo'].astype(str).isin(['1', 'True', '1.0'])]
        if not ativos.empty:
            dtemp = ativos
    col_nome = None
    for candidato in ['nome', 'nome_completo', 'nome_diretor', 'nome_secretario']:
        if candidato in dtemp.columns:
            col_nome = candidato
            break
    if col_nome is None:
        return None
    return str(dtemp.iloc[0][col_nome])

def calcular_vagas_seed(row):
    """Regra SEED-PR de máximo de alunos por turma."""
    serie = str(row.get('serie', '')).upper()
    nome = str(row.get('nome_completo', '')).upper()
    texto = f"{serie} {nome}"
    texto_norm = (texto.replace('Ç', 'C').replace('Ã', 'A').replace('Á', 'A')
                        .replace('É', 'E').replace('Í', 'I').replace('Ó', 'O'))

    # Reforço escolar e Sala de Recursos Multifuncional
    if 'REFORCO' in texto_norm or 'MULTIFUNCIONAL' in texto_norm or 'SALA DE RECURSOS' in texto_norm:
        return 4
    # Educação Infantil 4 e 5 anos
    if "INFANTIL 4" in serie or "INFANTIL 5" in serie:
        return 20
    # 4º e 5º ano
    if any(x in serie for x in ["4º", "5º", "4O", "5O"]):
        return 30
    # 1º ao 3º ano
    if any(x in serie for x in ["1º", "2º", "3º", "1O", "2O", "3O"]):
        return 25
    return 30

def renderizar_pagina_equipe(df, label_cadastro, icone="👤"):
    """Renderiza cartão de total, gráfico de situação funcional e tabela (com telefone/WhatsApp),
    reaproveitado tanto para Professores quanto para Funcionários."""
    if df.empty:
        st.info(f"Nenhum registro encontrado em '{label_cadastro}'.")
        return

    metric_card(icone, "icon-orange", len(df), label_cadastro)
    st.write("")

    if 'situacao_funcional' in df.columns:
        st.markdown('<div class="section-title">📊 Situação Funcional</div>', unsafe_allow_html=True)
        categorias = df['situacao_funcional'].apply(classificar_situacao_funcional)
        contagem = categorias.value_counts()
        ordem = ['PSS', 'Concursado', 'Terceirizado'] + (['Outros'] if 'Outros' in contagem.index else [])
        contagem = contagem.reindex(ordem).fillna(0).astype(int)
        df_sit = pd.DataFrame({'Situação': contagem.index, 'Quantidade': contagem.values})
        cores = {'PSS': '#ffc400', 'Concursado': '#5a78ff', 'Terceirizado': '#a366ff', 'Outros': '#6c7aa8'}
        fig = px.bar(df_sit, x='Situação', y='Quantidade', text='Quantidade', color='Situação',
                     color_discrete_map=cores)
        fig.update_traces(textposition='outside', textfont_color='#e8eaf6', textfont_size=14)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8eaf6", showlegend=False, xaxis_title="", yaxis_title="",
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)"), margin=dict(t=30, b=10, l=10, r=10)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Atualiza automaticamente com base na coluna 'situacao_funcional' de cada registro.")
        st.write("")

    df_ordenado = df.copy()
    if 'nome' in df_ordenado.columns:
        df_ordenado['_ordem'] = chave_alfabetica(df_ordenado['nome'])
        df_ordenado = df_ordenado.sort_values('_ordem')

    cols = [c for c in ['nome', 'cargo', 'situacao_funcional'] if c in df_ordenado.columns]
    column_config = {}

    def montar_link_wa(v):
        clean = "".join(filter(str.isdigit, str(v)))
        return f"https://wa.me/55{clean}" if len(clean) >= 8 else None

    campos_telefone = [c for c in ['telefone', 'telefone1', 'telefone2'] if c in df_ordenado.columns
                       and df_ordenado[c].apply(montar_link_wa).notna().any()]
    for i, campo in enumerate(campos_telefone, start=1):
        nome_link = 'whatsapp' if len(campos_telefone) == 1 else f'whatsapp{i}'
        label = "WhatsApp" if len(campos_telefone) == 1 else f"WhatsApp {i}"
        df_ordenado[nome_link] = df_ordenado[campo].apply(montar_link_wa)
        cols.append(nome_link)
        column_config[nome_link] = st.column_config.LinkColumn(label, display_text="📲 Abrir")

    st.dataframe(df_ordenado[cols], use_container_width=True, hide_index=True, column_config=column_config)

def metric_card(icon, icon_class, valor, label, sub=""):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon {icon_class}">{icon}</div>
            <div class="metric-val">{valor}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-sub">{sub}</div>
        </div>
    """, unsafe_allow_html=True)

# =========================================================
# PROCESSAMENTO DE DADOS
# =========================================================
if not df_alunos.empty:
    df_ativos = df_alunos[df_alunos['ativo'].astype(str).isin(['1', 'True', '1.0'])].copy()
    total_alunos = len(df_ativos)
    col_sexo = encontrar_coluna_sexo(df_ativos)
    if col_sexo:
        df_ativos['sexo_classificado'] = df_ativos[col_sexo].apply(classificar_sexo)
        meninos = int((df_ativos['sexo_classificado'] == 'M').sum())
        meninas = int((df_ativos['sexo_classificado'] == 'F').sum())
    else:
        meninos = meninas = 0
else:
    df_ativos = pd.DataFrame()
    total_alunos = meninos = meninas = 0

if not df_turmas.empty:
    if not df_ativos.empty and 'turma_id' in df_ativos.columns:
        df_ativos['turma_id_str'] = df_ativos['turma_id'].astype(str).str.replace(r'\.0$', '', regex=True)
        contagem = df_ativos.groupby('turma_id_str').size().reset_index(name='Matriculados')
        df_turmas['id_str'] = df_turmas['id'].astype(str)
        df_turmas = pd.merge(df_turmas, contagem, left_on='id_str', right_on='turma_id_str', how='left').fillna(0)
    else:
        df_turmas['id_str'] = df_turmas['id'].astype(str) if 'id' in df_turmas.columns else df_turmas.index.astype(str)
        df_turmas['Matriculados'] = 0

    df_turmas['Vagas Máx'] = df_turmas.apply(calcular_vagas_seed, axis=1) if 'serie' in df_turmas.columns else 30
    df_turmas['Disponível'] = df_turmas['Vagas Máx'] - df_turmas['Matriculados']

qtd_professores = len(df_professores) if not df_professores.empty else 0
qtd_turmas = len(df_turmas) if not df_turmas.empty else 0

# Gênero por turma (para o gráfico de barras)
genero_turma = pd.DataFrame()
if not df_turmas.empty and not df_ativos.empty and 'turma_id_str' in df_ativos.columns:
    df_temp = pd.merge(df_ativos, df_turmas[['id_str', 'nome_completo']],
                        left_on='turma_id_str', right_on='id_str', how='left')
    df_temp = df_temp[df_temp['sexo_classificado'].isin(['M', 'F'])]
    if not df_temp.empty:
        genero_turma = df_temp.groupby(['nome_completo', 'sexo_classificado']).size().unstack(fill_value=0)
        for c in ['M', 'F']:
            if c not in genero_turma.columns:
                genero_turma[c] = 0
        genero_turma = genero_turma.rename(columns={'M': 'Meninos', 'F': 'Meninas'})
        genero_turma = genero_turma.reset_index().sort_values('nome_completo')

# =========================================================
# CABEÇALHO
# =========================================================
nome_escola = "Escola Municipal"
if not df_escola.empty:
    nome_escola = df_escola.iloc[0].get('nome_escola', nome_escola)

# Tenta usar a logo de verdade no círculo do cabeçalho; se não achar o
# arquivo, cai de volta pro emoji genérico, sem quebrar a página.
import base64
_logo_html = '🏫'
try:
    with open("assets/logo.png", "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode("ascii")
    _logo_html = f'<img src="data:image/png;base64,{_logo_b64}" style="width:100%;height:100%;object-fit:contain;border-radius:16px;">'
except Exception:
    pass

st.markdown(f"""
    <div class="header-card">
        <div class="logo-circle">{_logo_html}</div>
        <div>
            <span class="badge">ESCOLAGEST • V16</span>
            <span class="badge-blue">PAINEL DE GESTÃO ESCOLAR</span>
            <div class="school-name">{nome_escola}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# NAVEGAÇÃO
# =========================================================
try:
    st.sidebar.image("assets/logo.png", use_container_width=True)
except Exception:
    pass
st.sidebar.markdown("### 🛡️ João - Secretário Escolar - Gestão")
menu = st.sidebar.radio("Menu Principal", [
    "📊 Dashboard", "👥 Alunos", "🏫 Turmas & Vagas", "👨‍🏫 Professores", "🧑‍💼 Funcionários", "🏢 Dados da Escola", "☎️ Contato, Vendas e Suporte"
], label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption(f"Atualizado {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.button("🔄 Atualizar Dados", on_click=st.cache_data.clear, use_container_width=True)

# =========================================================
# 1. DASHBOARD
# =========================================================
if menu == "📊 Dashboard":
    st.markdown('<div class="section-title">📊 Painel de Controle</div>', unsafe_allow_html=True)
    st.caption("Visão geral da escola em tempo real")

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("🎓", "icon-blue", total_alunos, "Alunos Ativos", f"{qtd_turmas} turmas")
    with c2: metric_card("👦", "icon-cyan", meninos,
                          "Meninos", f"{round((meninos/total_alunos)*100,1) if total_alunos else 0}%")
    with c3: metric_card("👧", "icon-pink", meninas,
                          "Meninas", f"{round((meninas/total_alunos)*100,1) if total_alunos else 0}%")
    with c4: metric_card("👨‍🏫", "icon-orange", qtd_professores, "Professores", "Corpo docente")

    st.write("")

    st.write("")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown('<div class="section-title">⚖️ Balanço de Gênero</div>', unsafe_allow_html=True)
        if total_alunos > 0:
            df_g = pd.DataFrame({"Gênero": ["Meninos", "Meninas"], "Qtd": [meninos, meninas]})
            fig = px.pie(df_g, values="Qtd", names="Gênero", hole=0.6,
                         color_discrete_sequence=["#5a78ff", "#ff5ca8"])
            fig.update_traces(textfont_color="white", textfont_size=14)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e8eaf6", showlegend=True, legend=dict(orientation="h", y=-0.1),
                margin=dict(t=10, b=10, l=10, r=10),
                annotations=[dict(text=str(total_alunos), x=0.5, y=0.5, font_size=28,
                                   font_color="#ffffff", showarrow=False)]
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de alunos para exibir.")

    with g2:
        st.markdown('<div class="section-title">📶 Meninos x Meninas por Turma</div>', unsafe_allow_html=True)
        if not genero_turma.empty:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(y=genero_turma['nome_completo'], x=genero_turma['Meninos'],
                                   name='Meninos', orientation='h', marker_color='#5a78ff',
                                   text=genero_turma['Meninos'], textposition='inside',
                                   textfont=dict(color='white', size=12)))
            fig2.add_trace(go.Bar(y=genero_turma['nome_completo'], x=genero_turma['Meninas'],
                                   name='Meninas', orientation='h', marker_color='#ff5ca8',
                                   text=genero_turma['Meninas'], textposition='inside',
                                   textfont=dict(color='white', size=12)))
            fig2.update_layout(
                barmode='stack',
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e8eaf6",
                legend=dict(orientation="h", y=-0.15),
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sem dados suficientes de turma para exibir o gráfico.")

# =========================================================
# 2. ALUNOS
# =========================================================
elif menu == "👥 Alunos":
    st.markdown('<div class="section-title">👥 Consulta de Alunos</div>', unsafe_allow_html=True)
    if not df_ativos.empty:
        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            busca = st.text_input("🔍 Buscar por nome...")
        with col_b2:
            lista_t = ["TODAS"] + sorted(df_turmas['nome_completo'].astype(str).unique().tolist()) if not df_turmas.empty else ["TODAS"]
            filtro_t = st.selectbox("📂 Por Turma", lista_t)

        df_f = pd.merge(df_ativos, df_turmas[['id_str', 'nome_completo']],
                         left_on='turma_id_str', right_on='id_str', how='left') if not df_turmas.empty else df_ativos
        if busca:
            df_f = df_f[df_f['nome'].str.contains(busca, case=False, na=False)]
        if filtro_t != "TODAS":
            df_f = df_f[df_f['nome_completo'] == filtro_t]

        st.caption(f"{len(df_f)} aluno(s) encontrado(s)")

        for _, a in df_f.sort_values('nome').iterrows():
            with st.expander(f"👤 {str(a['nome']).upper()} — {a.get('nome_completo', 'S/T')}"):
                drive = str(a.get('pasta_documentos', '')).strip()
                if drive and drive.lower() != 'nan':
                    st.link_button("📂 ABRIR GOOGLE DRIVE", drive, type="primary")

                st.write("---")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("**📄 IDENTIFICAÇÃO**")
                    st.write(f"Nascimento: {a.get('data_nascimento','-')}")
                    st.write(f"CPF: {a.get('cpf','-')}")
                    st.write(f"RG: {a.get('rg','-')}")
                    st.write(f"NIS: {a.get('nis','-')}")
                with c2:
                    st.markdown("**👨‍👩‍👦 FAMÍLIA**")
                    st.write(f"Mãe: {a.get('nome_mae','-')}")
                    st.write(f"Pai: {a.get('nome_pai','-')}")
                    campos_contato = [
                        ('telefone1', 'Responsável'),
                        ('telefone2', 'Responsável'),
                        ('telefone_responsavel', 'Responsável'),
                        ('telefone_mae', 'Mãe'),
                        ('telefone_pai', 'Pai'),
                    ]
                    links_html = ""
                    for campo, titulo in campos_contato:
                        val = str(a.get(campo, '')).replace('nan', '').strip()
                        if len(val) > 7:
                            links_html += link_whatsapp(val, titulo)
                    if links_html:
                        st.markdown(links_html, unsafe_allow_html=True)
                with c3:
                    st.markdown("**🏥 SAÚDE & OBS**")
                    st.write(f"Alergia: {a.get('alergico','-')}")
                    st.write(f"Restrição: {a.get('restricao_alimentar','-')}")
                    st.write(f"Observação: {a.get('observacoes','-')}")
    else:
        st.info("Nenhum aluno ativo encontrado.")

# =========================================================
# 3. TURMAS & VAGAS
# =========================================================
elif menu == "🏫 Turmas & Vagas":
    st.markdown('<div class="section-title">🏫 Gestão de Vagas</div>', unsafe_allow_html=True)
    if not df_turmas.empty:
        t1, t2 = st.columns(2)
        with t1: metric_card("🏫", "icon-blue", qtd_turmas, "Turmas Ativas")
        with t2: metric_card("🟢", "icon-green", int(df_turmas['Disponível'].sum()), "Vagas Disponíveis")
        st.write("")
        st.dataframe(
            df_turmas[['nome_completo', 'serie', 'turno', 'Matriculados', 'Vagas Máx', 'Disponível']].sort_values('serie'),
            hide_index=True, use_container_width=True
        )
    else:
        st.info("Nenhuma turma cadastrada.")

# =========================================================
# 4. PROFESSORES
# =========================================================
elif menu == "👨‍🏫 Professores":
    st.markdown('<div class="section-title">👨‍🏫 Corpo Docente</div>', unsafe_allow_html=True)
    renderizar_pagina_equipe(df_professores, "Professores Cadastrados", "👨‍🏫")

# =========================================================
# 4b. FUNCIONÁRIOS
# =========================================================
elif menu == "🧑‍💼 Funcionários":
    st.markdown('<div class="section-title">🧑‍💼 Funcionários</div>', unsafe_allow_html=True)
    if df_funcionarios.empty:
        st.warning(
            "A tabela **funcionarios** ainda não existe (ou está vazia) no Supabase. "
            "Assim que ela for criada e alimentada, essa aba vai preencher sozinha, "
            "igual à aba Professores."
        )
    else:
        renderizar_pagina_equipe(df_funcionarios, "Funcionários Cadastrados", "🧑‍💼")

# =========================================================
# 5. DADOS DA ESCOLA
# =========================================================
elif menu == "🏢 Dados da Escola":
    st.markdown('<div class="section-title">🏢 Dados da Escola</div>', unsafe_allow_html=True)
    if not df_escola.empty:
        d = df_escola.iloc[0].to_dict()

        def campo_valido(v):
            return v is not None and str(v).strip() != '' and str(v).strip().lower() != 'nan'

        st.markdown(f"<div class='school-name'>{d.get('nome_escola', 'Escola')}</div>", unsafe_allow_html=True)
        st.write("")

        nome_diretor = obter_responsavel(df_diretores)
        nome_secretario = obter_responsavel(df_secretarios)
        if nome_diretor or nome_secretario:
            cd1, cd2 = st.columns(2)
            with cd1:
                metric_card("🧑‍💼", "icon-blue", nome_diretor or "-", "Diretor(a)")
            with cd2:
                metric_card("🗂️", "icon-cyan", nome_secretario or "-", "Secretário(a)")
            st.write("")

        # Agrupamento por prefixo/palavra-chave do nome da coluna.
        # Qualquer campo que não se encaixe em nenhum grupo cai em "Outras Informações",
        # então NADA da tabela fica de fora, mesmo que o Supabase tenha mais colunas que isso.
        grupos = {
            "📍 Identificação": ["nome_escola", "inep", "cnpj", "codigo", "mantenedora", "dependencia"],
            "📫 Endereço & Contato": ["rua", "numero", "bairro", "cep", "municipio", "uf",
                                       "telefone", "celular", "email", "site"],
            "🏗️ Estrutura Física": ["num_salas", "salas", "biblioteca", "laboratorio", "quadra",
                                     "refeitorio", "cozinha", "acessibilidade", "internet"],
            "👤 Direção & Equipe": ["diretor", "diretora", "pedagogo", "pedagoga", "secretario", "secretaria"],
            "📜 Resoluções & Pareceres": ["resolucao", "parecer", "ato", "portaria", "autorizacao"],
        }

        usados = set()
        for titulo, palavras_chave in grupos.items():
            campos_do_grupo = [k for k in d.keys()
                                if any(p in k.lower() for p in palavras_chave) and campo_valido(d[k])]
            if not campos_do_grupo:
                continue
            usados.update(campos_do_grupo)
            st.markdown(f'<div class="section-title">{titulo}</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            cols = st.columns(2)
            for i, k in enumerate(campos_do_grupo):
                with cols[i % 2]:
                    st.write(f"**{k.upper().replace('_', ' ')}:** {d[k]}")
            st.markdown('</div>', unsafe_allow_html=True)
            st.write("")

        # Qualquer coluna que não caiu em nenhum grupo acima — exceto campos
        # binários/sensíveis (base64 de arquivos, chave de API), que nunca
        # devem ser jogados na tela como texto cru.
        CAMPOS_OCULTOS = ["base64", "api_key", "apikey", "senha", "password", "token"]
        restantes = [k for k in d.keys()
                     if k not in usados and k != 'id' and campo_valido(d[k])
                     and not any(oculto in k.lower() for oculto in CAMPOS_OCULTOS)]
        if restantes:
            st.markdown('<div class="section-title">📋 Outras Informações</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            cols = st.columns(2)
            for i, k in enumerate(restantes):
                with cols[i % 2]:
                    st.write(f"**{k.upper().replace('_', ' ')}:** {d[k]}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Dados da escola não cadastrados.")

elif menu == "☎️ Contato, Vendas e Suporte":
    st.markdown('<div class="section-title">☎️ Contato, Vendas e Suporte</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel" style="text-align:center; padding:30px;">', unsafe_allow_html=True)
    try:
        st.image("assets/logo.png", width=110)
    except Exception:
        st.markdown("### 🏫")
    st.markdown(f"""
        <div class="school-name" style="margin-top:10px;">{nome_escola}</div>
        <div style="font-weight:600; color:#6c7aa8; margin-bottom:15px;">João - Secretário Escolar — Painel de Gestão</div>
        <p style="max-width:600px; margin:0 auto 20px auto; color:#444;">
            Sistema de gestão escolar desenvolvido sob medida, cobrindo cadastro de alunos e equipe,
            turmas e horários, notas e frequência, documentos oficiais, controle de materiais e
            patrimônio, comunicação com a comunidade escolar e muito mais.
        </p>
        <div style="font-weight:700; color:#2e3a8c; margin-bottom:8px;">☎️ Contato, Vendas e Suporte</div>
        <div>✉️ joao.secretarioescolar@gmail.com</div>
        <div>📱 (43) 99908-9871 &nbsp;•&nbsp; (43) 99936-1415</div>
        <div style="margin-top:20px; font-size:12px; color:#888;">
            Desenvolvido por João Paulo A. Guaita &nbsp;•&nbsp; Licença de uso cedida gratuitamente
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# RODAPÉ (aparece em todas as abas)
# =========================================================
st.markdown("""
    <div style="text-align:center; padding: 30px 0 10px 0; color:#6c7aa8; font-size:12px; letter-spacing:0.5px;">
        Sistema Desenvolvido por João Paulo A. Guaita
    </div>
""", unsafe_allow_html=True)
