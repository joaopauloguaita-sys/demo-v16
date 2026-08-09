"""
Fonte central de dados do app da Secretaria de Educação.

Cada escola tem seu PRÓPRIO Supabase (mesmo esquema de tabelas do sistema
"João - Secretário Escolar"). Esse arquivo:

  1) Lê a lista de escolas cadastradas (nome + credenciais) dos Secrets
     do Streamlit Cloud.
  2) Sabe buscar uma tabela (ex: "alunos") de TODAS as escolas de uma vez,
     em paralelo, e devolver tudo já combinado num único DataFrame, com
     uma coluna "escola" dizendo de onde veio cada linha.
  3) Também sabe buscar dados de UMA escola só (pro painel Escola por
     Escola, que mostra cada uma separadamente).

Pra adicionar/remover uma escola: só mexe nos Secrets, não precisa
mexer em nenhum código.
"""
import concurrent.futures
import streamlit as st
import pandas as pd
import requests


def listar_escolas():
    """
    Lê a lista de escolas dos Secrets. Espera um formato assim no
    secrets.toml do Streamlit Cloud:

        [escola_1]
        nome = "Escola Municipal Trá Lá Lá"
        url = "https://xxxxx.supabase.co"
        key = "chave-anon-aqui"

        [escola_2]
        nome = "Escola Municipal Outra"
        url = "https://yyyyy.supabase.co"
        key = "chave-anon-aqui"

    (repete um bloco [escola_N] pra cada escola — N não precisa ser
    sequencial nem ter limite)
    """
    escolas = []
    for chave in st.secrets.keys():
        if chave.startswith("escola_"):
            bloco = st.secrets[chave]
            if "url" in bloco and "key" in bloco:
                escolas.append({
                    "id": chave,
                    "nome": bloco.get("nome", chave),
                    "url": bloco["url"],
                    "key": bloco["key"],
                })
    return escolas


def _buscar_tabela_uma_escola(escola, tabela, select="*"):
    """Busca uma tabela de UMA escola só. Nunca derruba o app inteiro se
    uma escola estiver fora do ar — só devolve vazio pra ela."""
    try:
        headers = {"apikey": escola["key"], "Authorization": f"Bearer {escola['key']}"}
        resp = requests.get(f"{escola['url']}/rest/v1/{tabela}?select={select}",
                             headers=headers, timeout=15)
        dados = resp.json()
        if not isinstance(dados, list):
            return escola["nome"], pd.DataFrame()
        df = pd.DataFrame(dados)
        df["escola"] = escola["nome"]
        return escola["nome"], df
    except Exception:
        return escola["nome"], pd.DataFrame()


@st.cache_data(ttl=120)
def carregar_tabela_combinada(tabela, select="*"):
    """
    Busca a mesma tabela em TODAS as escolas cadastradas, em paralelo, e
    devolve tudo junto num DataFrame só (com a coluna "escola" marcando
    a origem de cada linha). Escolas fora do ar simplesmente não entram,
    sem travar as outras.
    """
    escolas = listar_escolas()
    if not escolas:
        return pd.DataFrame(), []

    resultados = []
    escolas_com_erro = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        tarefas = {executor.submit(_buscar_tabela_uma_escola, e, tabela, select): e for e in escolas}
        for tarefa in concurrent.futures.as_completed(tarefas):
            nome, df = tarefa.result()
            if df.empty:
                escolas_com_erro.append(nome)
            else:
                resultados.append(df)

    if not resultados:
        return pd.DataFrame(), escolas_com_erro
    return pd.concat(resultados, ignore_index=True), escolas_com_erro


@st.cache_data(ttl=120)
def buscar_tabela_de_uma_escola(escola_id, tabela, select="*"):
    """Busca uma tabela de UMA escola específica (identificada pelo id,
    tipo 'escola_1'). Usado pelo painel Escola por Escola, onde cada aba
    mostra só os dados daquela escola."""
    escolas = {e["id"]: e for e in listar_escolas()}
    escola = escolas.get(escola_id)
    if not escola:
        return pd.DataFrame()
    _, df = _buscar_tabela_uma_escola(escola, tabela, select)
    return df


def link_whatsapp(telefone):
    """Monta o link do WhatsApp a partir de um telefone salvo no banco."""
    if not telefone:
        return None
    numeros = "".join(c for c in str(telefone) if c.isdigit())
    if not numeros:
        return None
    if len(numeros) <= 11:
        numeros = "55" + numeros
    return f"https://wa.me/{numeros}"


def _verdadeiro(serie):
    """Reconhece 'verdadeiro' em qualquer formato que o banco possa mandar
    (1, 1.0, True, true, t, yes, sim...), pra nunca deixar passar um
    arquivado por engano só por causa do formato do dado."""
    return serie.astype(str).str.strip().str.lower().isin(["1", "1.0", "true", "t", "yes", "sim"])


def filtrar_ativos(df):
    """Filtra só os registros ativos e NÃO arquivados. Se as colunas
    'ativo'/'arquivado' não existirem, não filtra por elas (assume que
    já vieram só os que interessam)."""
    if df.empty:
        return df
    filtro = pd.Series(True, index=df.index)
    if "ativo" in df.columns:
        filtro &= _verdadeiro(df["ativo"])
    if "arquivado" in df.columns:
        filtro &= ~_verdadeiro(df["arquivado"])
    return df[filtro]
