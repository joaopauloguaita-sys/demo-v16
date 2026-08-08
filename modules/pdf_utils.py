"""
Geração de PDF para o João - Secretário Escolar.
Colunas proporcionais ao conteúdo — sem desperdício de espaço.
"""
import os, sys, tempfile, subprocess
from datetime import date
from tkinter import filedialog, messagebox

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics

DESENVOLVEDOR = "Sistema desenvolvido por João Paulo A. Guaita  |  Licença cedida gratuitamente"


def _nome_escola_atual():
    """Busca o nome da escola direto do banco (Dados da Escola). Nunca fica
    preso a um texto fixo — muda sozinho se você trocar o cadastro."""
    try:
        from database.db import get_connection
        conn = get_connection()
        row = conn.execute("SELECT nome_escola FROM dados_escola LIMIT 1").fetchone()
        conn.close()
        if row and row["nome_escola"]:
            return row["nome_escola"]
    except Exception:
        pass
    return "Escola Municipal"
COR_PRIMARIA  = colors.HexColor("#0a2463")
COR_ACENTO    = colors.HexColor("#1976d2")
COR_DOURADO   = colors.HexColor("#f5a623")
COR_SUBTEXTO  = colors.HexColor("#1e4db7")
COR_CINZA     = colors.HexColor("#555555")

# Largura útil da página A4 em pontos
LARGURA_UTIL_A4        = A4[0] - 4 * cm          # ~503 pt
LARGURA_UTIL_A4_LAND   = A4[1] - 4 * cm          # ~714 pt


def _estilos():
    base = getSampleStyleSheet()
    return {
        "secao":  ParagraphStyle("secao",  parent=base["Heading2"], fontSize=11,
                                  textColor=COR_PRIMARIA, spaceBefore=8, spaceAfter=3),
        "normal": ParagraphStyle("normal", parent=base["Normal"],   fontSize=9, leading=13),
        "rodape": ParagraphStyle("rodape", parent=base["Normal"],   fontSize=7,
                                  alignment=TA_CENTER, textColor=COR_CINZA),
    }


def _char_width(texto, font_size=8):
    """Estima largura em pontos de um texto baseado nos caracteres."""
    return len(str(texto)) * font_size * 0.52


def _calcular_larguras(dados, largura_util):
    """
    Calcula larguras de coluna proporcionais ao conteúdo máximo de cada coluna.
    Garante que a soma nunca ultrapasse largura_util.
    """
    if not dados:
        return []
    n_cols = max(len(row) for row in dados)
    # Medir largura máxima de conteúdo por coluna (em pontos)
    maximos = [0] * n_cols
    for row in dados:
        for j, cell in enumerate(row):
            if j < n_cols:
                w = _char_width(str(cell) if cell is not None else "")
                # Cabeçalho recebe peso maior (bold)
                if row == dados[0]:
                    w *= 1.1
                maximos[j] = max(maximos[j], w)

    # Adicionar padding interno
    maximos = [m + 14 for m in maximos]  # 7pt de padding em cada lado

    total = sum(maximos)
    if total <= largura_util:
        # Esticar proporcionalmente para preencher a largura
        fator = largura_util / total
        return [m * fator for m in maximos]
    else:
        # Reduzir proporcionalmente para caber
        fator = largura_util / total
        return [m * fator for m in maximos]


def _on_page(canvas_obj, doc, titulo, nome_escola, orientacao="retrato"):
    canvas_obj.saveState()
    larg, alt = (A4[1], A4[0]) if orientacao == "paisagem" else A4

    # Cabeçalho
    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.setFillColor(COR_PRIMARIA)
    canvas_obj.drawCentredString(larg / 2, alt - 1.5 * cm, nome_escola)
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.setFillColor(COR_SUBTEXTO)
    canvas_obj.drawCentredString(larg / 2, alt - 2.0 * cm, titulo)
    canvas_obj.setStrokeColor(COR_DOURADO)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.line(2 * cm, alt - 2.35 * cm, larg - 2 * cm, alt - 2.35 * cm)

    # Rodapé
    canvas_obj.setStrokeColor(COR_CINZA)
    canvas_obj.setLineWidth(0.4)
    canvas_obj.line(2 * cm, 1.8 * cm, larg - 2 * cm, 1.8 * cm)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(COR_CINZA)
    canvas_obj.drawCentredString(larg / 2, 1.3 * cm, DESENVOLVEDOR)
    canvas_obj.drawRightString(larg - 2 * cm, 1.3 * cm,
                                f"Pág. {doc.page}  |  {date.today().strftime('%d/%m/%Y')}")
    canvas_obj.restoreState()


def _montar_tabela(dados, largura_util):
    """Monta um objeto Table do ReportLab com larguras proporcionais."""
    if not dados:
        return None

    col_widths = _calcular_larguras(dados, largura_util)

    # Converter células longas para Paragraph (permite quebra de linha)
    estilos = _estilos()
    dados_fmt = []
    for i, row in enumerate(dados):
        linha = []
        for j, cell in enumerate(row):
            txt = str(cell) if cell is not None else ""
            if i == 0:
                # Cabeçalho
                p = Paragraph(f"<b>{txt}</b>",
                              ParagraphStyle("hdr", fontSize=8, textColor=colors.white,
                                             leading=11, wordWrap='CJK'))
            else:
                p = Paragraph(txt,
                              ParagraphStyle("cel", fontSize=8, textColor=colors.HexColor("#111111"),
                                             leading=11, wordWrap='CJK'))
            linha.append(p)
        dados_fmt.append(linha)

    tabela = Table(dados_fmt, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    tabela.setStyle(TableStyle([
        # Cabeçalho
        ("BACKGROUND",    (0, 0), (-1, 0),  COR_PRIMARIA),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        # Linhas
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1),
         [colors.white, colors.HexColor("#eef2fb")]),
        # Grid
        ("GRID",          (0, 0), (-1, -1), 0.35, colors.HexColor("#c0c0c0")),
        # Padding
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tabela


def _precisa_paisagem(dados):
    """Usa paisagem se a tabela tiver 6 ou mais colunas."""
    if not dados:
        return False
    return max(len(row) for row in dados) >= 6


def gerar_pdf(titulo, blocos, nome_arquivo_sugerido,
              nome_escola=None, caminho_destino=None):
    """
    blocos: lista de tuplas:
      ("titulo",  "texto")
      ("texto",   "parágrafo")
      ("tabela",  [[linha1], [linha2], ...])
      ("espaco",  altura_cm)
    Retorna caminho do PDF.
    """
    if nome_escola is None:
        nome_escola = _nome_escola_atual()

    # Detectar se alguma tabela precisa de paisagem
    orientacao = "retrato"
    for bloco in blocos:
        if bloco[0] == "tabela" and _precisa_paisagem(bloco[1]):
            orientacao = "paisagem"
            break

    caminho = caminho_destino or os.path.join(tempfile.gettempdir(), nome_arquivo_sugerido)

    if orientacao == "paisagem":
        pagesize = landscape(A4)
        largura_util = LARGURA_UTIL_A4_LAND
        top_m = 3.0 * cm
    else:
        pagesize = A4
        largura_util = LARGURA_UTIL_A4
        top_m = 3.0 * cm

    doc = SimpleDocTemplate(
        caminho, pagesize=pagesize,
        topMargin=top_m, bottomMargin=2.2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm)

    estilos = _estilos()
    story   = []

    for bloco in blocos:
        tipo = bloco[0]
        if tipo == "titulo":
            story.append(Paragraph(str(bloco[1]), estilos["secao"]))

        elif tipo == "texto":
            for linha in str(bloco[1]).split("\n"):
                if linha.strip():
                    story.append(Paragraph(linha, estilos["normal"]))
                else:
                    story.append(Spacer(1, 0.3 * cm))

        elif tipo == "espaco":
            story.append(Spacer(1, float(bloco[1]) * cm))

        elif tipo == "tabela":
            dados = bloco[1]
            if not dados:
                continue
            # Tabela muito larga? Usar toda largura disponível
            larg = largura_util
            tab = _montar_tabela(dados, larg)
            if tab:
                story.append(tab)
                story.append(Spacer(1, 0.3 * cm))

    cb = lambda c, d: _on_page(c, d, titulo, nome_escola, orientacao)
    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    return caminho


def salvar_pdf_como(titulo, blocos, nome_arquivo_sugerido,
                    nome_escola=None, parent=None):
    caminho = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")],
        initialfile=nome_arquivo_sugerido,
        title="Salvar PDF como...")
    if not caminho:
        return None
    try:
        gerar_pdf(titulo, blocos, nome_arquivo_sugerido,
                  nome_escola=nome_escola, caminho_destino=caminho)
        messagebox.showinfo("PDF gerado", f"Arquivo salvo em:\n{caminho}", parent=parent)
        _abrir_arquivo(caminho)
        return caminho
    except Exception as e:
        messagebox.showerror("Erro ao gerar PDF", str(e), parent=parent)
        return None


def imprimir_pdf(titulo, blocos, nome_arquivo_sugerido,
                 nome_escola=None, parent=None):
    try:
        caminho = gerar_pdf(titulo, blocos, nome_arquivo_sugerido, nome_escola=nome_escola)
        if sys.platform.startswith("win"):
            os.startfile(caminho, "print")
        else:
            subprocess.run(["lpr", caminho])
        return caminho
    except Exception as e:
        messagebox.showerror("Erro ao imprimir", str(e), parent=parent)
        return None


def _abrir_arquivo(caminho):
    try:
        if sys.platform.startswith("win"):
            os.startfile(caminho)
        elif sys.platform == "darwin":
            subprocess.run(["open", caminho])
        else:
            subprocess.run(["xdg-open", caminho])
    except Exception:
        pass
