"""
Módulo RAG do SofIA
Permite que o SofIA "leia" documentos (PDF, Word, TXT) fornecidos por você
e responda perguntas com base neles, em vez de depender só da memória
do modelo de IA.

Funciona 100% local e gratuito: os documentos e os embeddings ficam
salvos no seu computador; só o texto final da pergunta + trechos
relevantes é que vai para a API de IA.
"""

import os
import sys
import json
import numpy as np

# Evita um bug conhecido no Windows: sem "Modo de Desenvolvedor" ativado, a
# biblioteca do Hugging Face tenta criar links simbólicos ao baixar o modelo
# de IA e trava silenciosamente. Isso desativa esse comportamento.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
# Evita ficar travado pra sempre se a internet estiver lenta/bloqueada -
# desiste depois de alguns segundos com um erro claro, em vez de travar.
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "20")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "30")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.path.join(BASE_DIR, "dados_sofia")
ARQUIVO_INDICE = os.path.join(PASTA_DADOS, "indice.json")
NOME_MODELO_EMBEDDING = "all-MiniLM-L6-v2"

os.makedirs(PASTA_DADOS, exist_ok=True)

_modelo = None  # carregado sob demanda (lazy load), pois é pesado


def _obter_modelo():
    """Carrega o modelo de embeddings apenas quando necessário."""
    global _modelo
    if _modelo is None:
        try:
            from sentence_transformers import SentenceTransformer
            _modelo = SentenceTransformer(NOME_MODELO_EMBEDDING)
        except Exception as e:
            raise RuntimeError(
                "Não consegui baixar/carregar o modelo de IA da SofIA. "
                "Isso costuma ser falta de internet ou um firewall bloqueando "
                "o acesso a huggingface.co na primeira vez que um documento é "
                f"adicionado. Detalhe técnico: {e}"
            )
    return _modelo


# ============================================================
# EXTRAÇÃO DE TEXTO
# ============================================================

def extrair_texto(caminho_arquivo):
    ext = os.path.splitext(caminho_arquivo)[1].lower()

    if ext == ".txt":
        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif ext == ".pdf":
        from pypdf import PdfReader
        leitor = PdfReader(caminho_arquivo)
        return "\n".join(pagina.extract_text() or "" for pagina in leitor.pages)

    elif ext in (".docx",):
        import docx
        doc = docx.Document(caminho_arquivo)
        return "\n".join(p.text for p in doc.paragraphs)

    else:
        raise ValueError(f"Formato não suportado: {ext}")


def dividir_em_pedacos(texto, tamanho=800, sobreposicao=150):
    """Divide o texto em pedaços (chunks) menores, com sobreposição,
    para preservar contexto entre pedaços vizinhos."""
    texto = " ".join(texto.split())  # normaliza espaços
    pedacos = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + tamanho
        pedacos.append(texto[inicio:fim])
        inicio += tamanho - sobreposicao
    return [p for p in pedacos if p.strip()]


# ============================================================
# ÍNDICE (armazenamento local dos documentos + embeddings)
# ============================================================

def _carregar_indice():
    if os.path.exists(ARQUIVO_INDICE):
        with open(ARQUIVO_INDICE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"documentos": [], "pedacos": []}


def _salvar_indice(indice):
    with open(ARQUIVO_INDICE, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False)


def listar_documentos():
    indice = _carregar_indice()
    return indice["documentos"]


def adicionar_documento(caminho_arquivo, callback_status=None):
    """Extrai, divide em pedaços, gera embeddings e adiciona ao índice."""
    nome = os.path.basename(caminho_arquivo)

    if callback_status:
        callback_status(f"Lendo {nome}...")
    texto = extrair_texto(caminho_arquivo)

    if not texto.strip():
        raise ValueError("Não foi possível extrair texto deste arquivo.")

    if callback_status:
        callback_status(f"Dividindo {nome} em trechos...")
    pedacos_texto = dividir_em_pedacos(texto)

    if callback_status:
        if _modelo is None:
            callback_status(f"Preparando a IA pela primeira vez (baixando ~90MB, só acontece uma vez)...")
        else:
            callback_status(f"Gerando embeddings de {nome} (pode levar um instante)...")
    modelo = _obter_modelo()
    vetores = modelo.encode(pedacos_texto).tolist()

    indice = _carregar_indice()
    indice["documentos"].append(nome)
    for pedaco, vetor in zip(pedacos_texto, vetores):
        indice["pedacos"].append({
            "documento": nome,
            "texto": pedaco,
            "vetor": vetor,
        })
    _salvar_indice(indice)

    if callback_status:
        callback_status(f"{nome} adicionado com sucesso ({len(pedacos_texto)} trechos).")


def remover_documento(nome):
    indice = _carregar_indice()
    if nome in indice["documentos"]:
        indice["documentos"].remove(nome)
    indice["pedacos"] = [p for p in indice["pedacos"] if p["documento"] != nome]
    _salvar_indice(indice)


def total_documentos():
    return len(listar_documentos())


# ============================================================
# BUSCA POR RELEVÂNCIA (similaridade de cosseno)
# ============================================================

def buscar(pergunta, top_k=4, limiar_minimo=0.25):
    """Retorna os trechos mais relevantes para a pergunta, entre os
    documentos cadastrados. Retorna lista vazia se não houver documentos
    ou se nada for suficientemente relevante."""
    indice = _carregar_indice()
    if not indice["pedacos"]:
        return []

    modelo = _obter_modelo()
    vetor_pergunta = modelo.encode([pergunta])[0]

    vetores = np.array([p["vetor"] for p in indice["pedacos"]])
    normas = np.linalg.norm(vetores, axis=1) * np.linalg.norm(vetor_pergunta)
    normas[normas == 0] = 1e-10
    similaridades = (vetores @ vetor_pergunta) / normas

    indices_ordenados = np.argsort(-similaridades)[:top_k]

    resultados = []
    for i in indices_ordenados:
        if similaridades[i] >= limiar_minimo:
            resultados.append({
                "documento": indice["pedacos"][i]["documento"],
                "texto": indice["pedacos"][i]["texto"],
                "relevancia": float(similaridades[i]),
            })
    return resultados
