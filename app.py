import streamlit as st
import requests
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import SUPABASE_URL, SUPABASE_KEY, supabase_configurado

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="João - Secretário Escolar - Inspetores", page_icon="🛡️", layout="wide")

# --- LOGO ---
try:
    st.sidebar.image("assets/logo.png", use_container_width=True)
except:
    pass

# --- SOBRE ---
with st.sidebar.expander("☎️ Contato, Vendas e Suporte"):
    st.markdown("""
**João - Secretário Escolar**

Sistema de gestão escolar com painel de acompanhamento em tempo real
pra equipe de inspetores/portaria.

📞 **Contato, Vendas e Suporte**
✉️ joao.secretarioescolar@gmail.com
📱 (43) 99908-9871 • (43) 99936-1415

*Desenvolvido por João Paulo A. Guaita*
""")

# --- DESIGN (CSS) ---
st.markdown("""
    <style>
    .student-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        border-left: 6px solid #0B2E78;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CREDENCIAIS (lidas de .env via config.py) ---
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

@st.cache_data(ttl=5)
def carregar_dados():
    try:
        # 1. Puxa Alunos
        res_a = requests.get(f"{SUPABASE_URL}/rest/v1/alunos?select=*", headers=HEADERS, timeout=15)
        df_a = pd.DataFrame(res_a.json())
        
        # 2. Puxa Turmas
        res_t = requests.get(f"{SUPABASE_URL}/rest/v1/turmas?select=*", headers=HEADERS, timeout=15)
        df_t = pd.DataFrame(res_t.json())
        
        if df_a.empty:
            return pd.DataFrame(), pd.DataFrame()
            
        # Filtro de Arquivo Morto (usando coluna 'ativo' ou 'status' se disponível)
        if 'status' in df_a.columns:
            # Filtra apenas quem não está no Arquivo Morto
            df_a = df_a[~df_a['status'].str.contains('Arquivo Morto', case=False, na=False)]
            
        return df_a, df_t
    except requests.exceptions.RequestException:
        return pd.DataFrame(), pd.DataFrame()

st.title("🛡️ Inspetores Trá Lá Lá")

if not supabase_configurado():
    st.error("Credenciais do Supabase não configuradas. Verifique o arquivo .env.")
    st.stop()

df_alunos, df_turmas = carregar_dados()

if not df_alunos.empty:
    # --- MAPEAMENTO DAS TURMAS (O PULHO DO GATO) ---
    # Na sua tabela de turmas, o nome correto está na coluna 'nome_completo'
    if not df_turmas.empty:
        # Criamos um dicionário que liga o ID da turma ao Nome Completo dela
        mapa_turmas = dict(zip(df_turmas['id'].astype(str), df_turmas['nome_completo']))

        # Agora aplicamos esse nome aos alunos usando a coluna 'turma_id'
        # (remove o ".0" que o Pandas adiciona quando a coluna tem algum
        # aluno sem turma misturado com números, senão "38" vira "38.0"
        # e nunca bate com o id da tabela de turmas)
        turma_id_limpo = df_alunos['turma_id'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        df_alunos['turma_nome_exibicao'] = turma_id_limpo.map(mapa_turmas).fillna("Sem Turma")
    else:
        df_alunos['turma_nome_exibicao'] = "Sem Turma"

    # --- BARRA LATERAL ---
    opcoes_turma = sorted(df_alunos['turma_nome_exibicao'].unique())
    turma_sel = st.sidebar.radio("🏫 Escolha a Turma", opcoes_turma)
    
    # --- FILTRO DE BUSCA ---
    busca = st.text_input("🔍 Buscar Aluno", placeholder="Digite o nome do aluno...")
    
    # Filtra os alunos pela turma selecionada
    df_f = df_alunos[df_alunos['turma_nome_exibicao'] == turma_sel].copy()
    
    # Filtra pela busca de nome
    if busca:
        df_f = df_f[df_f['nome'].str.contains(busca, case=False, na=False)]
    
    # Ordena por nome de A a Z
    df_f = df_f.sort_values('nome')
    
    st.write(f"### {turma_sel} ({len(df_f)} alunos)")
    
    # --- LISTAGEM DE ALUNOS ---
    for _, aluno in df_f.iterrows():
        st.markdown('<div class="student-card">', unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            st.subheader(f"👤 {aluno.get('nome', 'Sem Nome')}")
            # WhatsApp
            w_cols = st.columns(3)
            for i, (lab, field) in enumerate([("Mãe", "telefone_mae"), ("Pai", "telefone_pai"), ("Resp", "telefone_responsavel")]):
                n = str(aluno.get(field) or "").strip()
                if n and n.lower() not in ['none', 'nan', '']:
                    n_limpo = "".join(filter(str.isdigit, n))
                    if len(n_limpo) <= 11: n_limpo = "55" + n_limpo
                    with w_cols[i]: st.link_button(f"💬 {lab}", f"https://wa.me/{n_limpo}")
        with c2:
            # Pega a autorização de saída
            aut = str(aluno.get('saida_autorizada', '')).lower()
            if "pode sair" in aut: 
                st.success("✅ PODE SAIR")
            elif "van" in aut: 
                st.warning("🟡 VAN")
            else: 
                st.error("🚫 NÃO SAI")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Sincronizando dados... Verifique a conexão do computador.")

if st.sidebar.button("🔄 Atualizar Lista"):
    st.cache_data.clear()
    st.rerun()
