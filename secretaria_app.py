"""
Painel da Secretaria de Educação — visão combinada de todas as escolas
do município que usam o sistema "João - Secretário Escolar".

Cada painel (Dashboard, Turmas & Vagas, etc.) é um módulo independente
dentro de secretaria_modules/. Pra tirar um painel de circulação, comenta
a linha dele em MODULOS abaixo. Pra adicionar um novo, cria o arquivo
com uma função render() e registra uma linha nova aqui.
"""
import streamlit as st

st.set_page_config(page_title="Secretaria de Educação — Painel Geral",
                    page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

# =========================================================
# VISUAL (tema escuro nos painéis, barra lateral azul)
# =========================================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #16215c, #1f2f8c);
    }
    section[data-testid="stSidebar"] * { color: #e8ebff !important; }
    .painel {
        background-color: #171b26;
        border: 1px solid #262c3d;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
    }
    .titulo-secao {
        color: #d6b64d;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 14px;
    }
    .metric-box {
        background-color: #1c2233;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
    }
    .metric-valor { font-size: 32px; font-weight: 800; color: #ffffff; }
    .metric-label { font-size: 13px; color: #9aa3c0; margin-top: 4px; }
    h1, h2, h3, p, span, div { color: #e8ebff; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# REGISTRO DE MÓDULOS
# Pra tirar um painel: comenta (ou apaga) a linha dele aqui.
# Pra adicionar um novo: cria o arquivo em secretaria_modules/ com uma
# função render(), e acrescenta uma linha aqui.
# =========================================================
MODULOS = [
    ("📊 Dashboard Geral", "secretaria_modules.dashboard"),
    ("🏫 Escola por Escola", "secretaria_modules.escola_detalhe"),
    # ("📈 Notas & Frequência", "secretaria_modules.notas_frequencia"),
    ("☎️ Contato, Vendas e Suporte", "secretaria_modules.sobre"),
]

# =========================================================
# CABEÇALHO
# =========================================================
st.sidebar.markdown("## 🏛️ Secretaria de Educação")
st.sidebar.caption("Painel Geral — Visão de todas as escolas")
st.sidebar.markdown("---")

opcoes = [nome for nome, _ in MODULOS]
escolha = st.sidebar.radio("Painéis", opcoes, label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.button("🔄 Atualizar Dados", on_click=st.cache_data.clear, use_container_width=True)

# =========================================================
# CARREGA E RENDERIZA O MÓDULO ESCOLHIDO
# =========================================================
import importlib

modulo_path = dict(MODULOS)[escolha]
modulo = importlib.import_module(modulo_path)
modulo.render()

st.markdown("""
    <div style="text-align:center; padding: 25px 0 10px 0; color:#6c7aa8; font-size:12px;">
        Painel da Secretaria • João - Secretário Escolar
    </div>
""", unsafe_allow_html=True)
