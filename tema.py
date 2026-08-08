"""
Tema visual João - Secretário Escolar — versão aprovada pela Diretora.
Paleta: azul marinho + azul claro brilhante + dourado.
Alto contraste: fundo azul → fonte branca | fundo claro → fonte azul marinho.
"""
import customtkinter as ctk
import webbrowser
import re
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logger_config import get_logger

logger = get_logger(__name__)

# ===================== PALETA DE CORES =====================
CORES = {
    # Azuis principais
    "primaria":        "#0a2463",   # azul marinho profundo (fundo sidebar, cabeçalhos)
    "primaria_clara":  "#1e4db7",   # azul médio vibrante (botões secundários)
    "secundaria":      "#1565c0",   # azul royal (destaques)
    "acento":          "#1976d2",   # azul claro brilhante (botões principais)
    "acento_hover":    "#1565c0",   # azul um pouco mais escuro no hover

    # Dourado — detalhes e títulos
    "dourado":         "#f5a623",   # dourado brilhante
    "dourado_hover":   "#e09612",   # dourado mais escuro no hover
    "dourado_escuro":  "#c47d0e",   # dourado para texto sobre fundo claro

    # Ação / estado
    "sucesso":         "#1565c0",   # azul para aprovado
    "sucesso_hover":   "#1e4db7",
    "perigo":          "#c62828",   # vermelho escuro para erros/excluir
    "perigo_hover":    "#b71c1c",
    "aviso":           "#f5a623",

    # Fundos
    "fundo":           "#e8edf5",   # azul muito claro (quase branco azulado) — fundo geral
    "card":            "#ffffff",   # branco puro — cartões e painéis
    "card_claro":      "#f0f4fb",   # azul claríssimo — linhas alternadas
    "sidebar":         "#0a2463",   # azul marinho — sidebar
    "sidebar_hover":   "#1e4db7",   # azul médio — hover na sidebar
    "sidebar_ativo":   "#f5a623",   # dourado — item ativo na sidebar

    # Textos — ALTO CONTRASTE
    "texto":           "#0a2463",   # azul marinho — texto sobre fundo claro/branco
    "texto_escuro":    "#0a2463",   # azul marinho — para tabelas
    "texto_claro":     "#ffffff",   # branco — texto sobre fundo azul escuro
    "texto_card":      "#0a2463",   # azul marinho — texto dentro de cards brancos
    "subtexto":        "#1e4db7",   # azul médio — labels e textos secundários
    "subtexto_claro":  "#b3c6e7",   # azul claro — texto sutil sobre fundo escuro

    # Bordas
    "borda":           "#90b0d8",   # azul médio claro

    # Notas
    "nota_aprovado":   "#0a2463",   # azul marinho — nota aprovada
    "nota_reprovado":  "#c62828",   # vermelho escuro — nota reprovada

    # Turmas nas tabelas
    "turma_texto":     "#1565c0",   # azul royal visível sobre fundo branco
}

FONTE_PADRAO = "Segoe UI"
MEDIA_APROVACAO_BIMESTRAL = 6.0
MEDIA_APROVACAO_FINAL     = 24.0


def aplicar_tema():
    ctk.set_appearance_mode("light")   # Modo claro — melhor para ambientes iluminados
    ctk.set_default_color_theme("blue")
    try:
        ctk.deactivate_automatic_dpi_awareness()
    except Exception as e:
        logger.warning("deactivate_automatic_dpi_awareness não disponível: %s", e)
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)


def fonte(tamanho=11, peso="normal"):
    return ctk.CTkFont(family=FONTE_PADRAO, size=tamanho, weight=peso)


def maximizar(janela):
    janela.update_idletasks()
    w = janela.winfo_screenwidth()
    h = janela.winfo_screenheight()
    # Primeiro garante posição e tamanho corretos de forma explícita (0,0 até o
    # tamanho da tela) - isso sozinho já evita a janela abrir deslocada.
    janela.geometry(f"{w}x{h}+0+0")
    janela.update_idletasks()
    # Depois tenta o modo "maximizado" nativo do Windows por cima (fica com a
    # aparência de janela maximizada de verdade, com os botões certos)
    try:
        janela.state("zoomed")
    except Exception as e:
        logger.warning("state('zoomed') não disponível: %s", e)
        try:
            janela.attributes("-zoomed", True)
        except Exception as e2:
            logger.warning("attributes('-zoomed') também não disponível: %s", e2)


def abrir_link(url):
    if url and url.strip():
        webbrowser.open(url.strip())


def abrir_whatsapp(numero):
    """
    Abre o WhatsApp Web com o número já preenchido.
    Limpa o número (remove formatação) e monta o link wa.me.
    Funciona com WhatsApp Web ou WhatsApp Desktop — o que estiver instalado abre automaticamente.
    """
    if not numero:
        return
    # Remove tudo que não for dígito
    import re as _re
    digitos = _re.sub(r"\D", "", str(numero))
    if not digitos:
        return
    # Adicionar DDI do Brasil se não tiver (55)
    if len(digitos) == 10 or len(digitos) == 11:
        digitos = "55" + digitos
    url = f"https://wa.me/{digitos}"
    webbrowser.open(url)


# ===================== MÁSCARAS =====================

def mascara_cpf(texto):
    nums = re.sub(r"\D", "", texto)[:11]
    if len(nums) <= 3:   return nums
    if len(nums) <= 6:   return f"{nums[:3]}.{nums[3:]}"
    if len(nums) <= 9:   return f"{nums[:3]}.{nums[3:6]}.{nums[6:]}"
    return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"

def mascara_cep(texto):
    nums = re.sub(r"\D", "", texto)[:8]
    if len(nums) <= 5: return nums
    return f"{nums[:5]}-{nums[5:]}"

def mascara_telefone(texto):
    nums = re.sub(r"\D", "", texto)[:11]
    if len(nums) <= 2:  return f"({nums}"
    if len(nums) <= 6:  return f"({nums[:2]}) {nums[2:]}"
    if len(nums) <= 10: return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"

def mascara_data(texto):
    nums = re.sub(r"\D", "", texto)[:8]
    if len(nums) <= 2:  return nums
    if len(nums) <= 4:  return f"{nums[:2]}/{nums[2:]}"
    return f"{nums[:2]}/{nums[2:4]}/{nums[4:]}"

def mascara_nis(texto):
    nums = re.sub(r"\D", "", texto)[:11]
    if len(nums) <= 3:  return nums
    if len(nums) <= 8:  return f"{nums[:3]}.{nums[3:]}"
    if len(nums) <= 10: return f"{nums[:3]}.{nums[3:8]}.{nums[8:]}"
    return f"{nums[:3]}.{nums[3:8]}.{nums[8:10]}-{nums[10:]}"

def mascara_cgm(texto):
    return re.sub(r"\D", "", texto)[:10]

def mascara_nota(texto):
    limpo = re.sub(r"[^0-9.]", "", texto)
    partes = limpo.split(".")
    if len(partes) > 2:
        limpo = partes[0] + "." + partes[1]
    if "." in limpo:
        inteiro, decimal = limpo.split(".", 1)
        limpo = f"{inteiro[:2]}.{decimal[:1]}"
    else:
        limpo = limpo[:2]
    return limpo

def mascara_portaria(texto):
    nums = re.sub(r"\D", "", texto)[:7]
    if len(nums) <= 3: return nums
    return f"{nums[:3]}/{nums[3:]}"

def mascara_certidao(texto):
    nums = re.sub(r"\D", "", texto)[:32]
    partes = [6, 2, 2, 4, 1, 5, 3, 7, 2]
    out, i = [], 0
    for tam in partes:
        bloco = nums[i:i+tam]
        if not bloco: break
        out.append(bloco)
        i += tam
    seps = [" ", " ", " ", " ", " ", " ", " ", "-"]
    resultado = ""
    for idx, bloco in enumerate(out):
        resultado += bloco
        if idx < len(out) - 1 and idx < len(seps):
            resultado += seps[idx]
    return resultado

def mascara_inep(texto):
    return re.sub(r"\D", "", texto)[:8]

def mascara_resolucao(texto):
    return re.sub(r"[^0-9\-]", "", texto)[:12]

def mascara_geo(texto):
    return re.sub(r"[^0-9\-]", "", texto)[:12]

def data_bd_para_tela(texto):
    if not texto: return ""
    texto = str(texto).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", texto):
        a, m, d = texto.split("-")
        return f"{d}/{m}/{a}"
    return texto

def data_tela_para_bd(texto):
    if not texto: return ""
    texto = str(texto).strip()
    if re.match(r"^\d{2}/\d{2}/\d{4}$", texto):
        d, m, a = texto.split("/")
        return f"{a}-{m}-{d}"
    return texto

def vincular_mascara(entry, funcao_mascara):
    def on_key(event):
        val = entry.get()
        novo = funcao_mascara(val)
        if novo != val:
            entry.delete(0, "end")
            entry.insert(0, novo)
    entry.bind("<KeyRelease>", on_key)


def bimestre_atual():
    """Calcula em qual bimestre estamos hoje, com base nas datas cadastradas
    em Dados da Escola. Retorna 1 se não houver datas cadastradas ainda."""
    from datetime import date
    try:
        from database.db import get_connection
        conn = get_connection()
        row = conn.execute(
            "SELECT bim1_inicio, bim1_fim, bim2_inicio, bim2_fim, "
            "bim3_inicio, bim3_fim, bim4_inicio, bim4_fim FROM dados_escola LIMIT 1"
        ).fetchone()
        conn.close()
        if not row:
            return 1
        hoje = date.today().isoformat()
        for n in range(1, 5):
            ini = row[f"bim{n}_inicio"]
            fim = row[f"bim{n}_fim"]
            if ini and fim and ini <= hoje <= fim:
                return n
        for n in (4, 3, 2, 1):
            ini = row[f"bim{n}_inicio"]
            if ini and ini <= hoje:
                return n
        return 1
    except Exception:
        return 1


_UNIDADES = ["", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove"]
_DEZ_A_DEZENOVE = ["dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis",
                    "dezessete", "dezoito", "dezenove"]
_DEZENAS = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
_CENTENAS = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos",
             "seiscentos", "setecentos", "oitocentos", "novecentos"]


def _grupo_extenso(n):
    if n == 0:
        return ""
    if n == 100:
        return "cem"
    c, resto = divmod(n, 100)
    partes = []
    if c:
        partes.append(_CENTENAS[c])
    if resto:
        if resto < 10:
            partes.append(_UNIDADES[resto])
        elif resto < 20:
            partes.append(_DEZ_A_DEZENOVE[resto - 10])
        else:
            d, u = divmod(resto, 10)
            partes.append(_DEZENAS[d] + (f" e {_UNIDADES[u]}" if u else ""))
    return " e ".join(partes) if c and resto else partes[0] if partes else ""


def numero_por_extenso(n):
    """Converte um número inteiro (0 a 999.999) em texto por extenso, em português."""
    try:
        n = int(n)
    except Exception:
        return ""
    if n == 0:
        return "zero"
    if n < 0:
        return "menos " + numero_por_extenso(-n)
    milhar, resto = divmod(n, 1000)
    partes = []
    if milhar:
        partes.append("mil" if milhar == 1 else _grupo_extenso(milhar) + " mil")
    if resto:
        partes.append(_grupo_extenso(resto))
    return " e ".join(partes) if milhar and resto and (resto < 100 or resto % 100 == 0) else " ".join(partes)


# ===================== LISTAS =====================

ESTADOS_UF = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
              "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC",
              "SP","SE","TO"]
COR_RACA_OPCOES       = ["Branca","Preta","Parda","Amarela","Indígena","Não declarada"]
ESTADO_CIVIL_OPCOES   = ["Solteiro(a)","Casado(a)","Divorciado(a)","Viúvo(a)","União Estável","Separado(a)"]
SITUACAO_FUNCIONAL_OPCOES = ["Concursado","PSS","Terceirizado","CLT"]

TIPOS_DEFICIENCIA = [
    "Altas habilidades/Superdotação","Atraso no Desenvolvimento Neuropsicomotor",
    "Baixa visão","Cegueira","Deficiência auditiva","Deficiência física",
    "Deficiência intelectual","Deficiência múltipla","Distúrbios de aprendizagem",
    "Surdez","Surdocegueira","Transtorno do Espectro Autista","Transtornos Mentais",
    "Visão Monocular",
]
NECESSIDADES_ESPECIAIS = [
    "Faz uso de cadeira de rodas","Faz uso de muletas ou bengalas entre outros",
    "Livros ampliados","Reglete, sorobã ou material em braille","Carteiras adaptadas",
    "Computadores adaptados","Materiais de Comunicação alternativo e ampliado",
    "Intérprete de LIBRAS","Atendente","Professor de apoio permanente",
    "Auxílio ledor","Auxílio transcrição","Guia-intérprete","Leitura labial",
    "Nenhum","Prova Ampliada (fonte 18)","CD com áudio para deficiente visual",
    "Prova de Língua Portuguesa como 2ª língua para surdos e deficientes auditivos",
    "Prova em vídeo Libras","Tradutor-Intérprete de Libras",
    "Prova superampliada (fonte 24)","Tempo adicional","Prova em Braille",
    "Material em Braille",
]
SERIES_REGULARES = ["Infantil 4","Infantil 5","1º Ano","2º Ano","3º Ano","4º Ano","5º Ano"]
TURNOS      = ["Manhã","Tarde","Integral","Horário Diferenciado"]
DIAS_SEMANA = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira"]
