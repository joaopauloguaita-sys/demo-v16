from fpdf import FPDF
import os
import sys
import subprocess
from datetime import datetime
from database.db import get_connection

class PDFGenerator(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.dados_escola = self._carregar_dados_escola()

    def _carregar_dados_escola(self):
        try:
            conn = get_connection()
            d = dict(conn.execute("SELECT * FROM dados_escola LIMIT 1").fetchone() or {})
            conn.close()
            return d
        except:
            return {}

    def header(self):
        if hasattr(self, 'pular_header') and self.pular_header:
            return

        if getattr(sys, 'frozen', False):
            raiz = os.path.dirname(sys.executable)
        else:
            raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        logo_path = os.path.join(raiz, "assets", "logo.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(raiz, "assets", "logo.jpg")

        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 20)
        
        d = self.dados_escola
        self.set_font("helvetica", 'B', 11)
        nome_esc = (d.get('nome_escola') or 'ESCOLA MUNICIPAL TRÁ LÁ LÁ').upper()
        self.set_xy(35, 10)
        self.cell(0, 5, nome_esc, ln=True)
        
        self.set_font("helvetica", size=8)
        self.set_x(35)
        
        # Montar endereço amigável
        rua = d.get('rua') or ''
        num = d.get('numero') or ''
        bairro = d.get('bairro') or ''
        mun = d.get('municipio') or 'Distrito de São José'
        tel = d.get('telefone') or d.get('telefone1') or '(43) 3441-1155'
        
        partes_end = []
        if rua: partes_end.append(f"{rua}")
        if num: partes_end.append(f"{num}")
        if bairro: partes_end.append(f"{bairro}")
        if mun: partes_end.append(f"{mun}")
        
        end_str = " - ".join(partes_end) if partes_end else "Endereço não cadastrado"
        
        self.cell(0, 4, f"{end_str} - Tel: {tel}", ln=True)
        
        self.set_x(35)
        email = d.get('email') or 'escola.lorenzette@gmail.com'
        inep = d.get('inep') or '41012345'
        self.cell(0, 4, f"E-mail: {email} | INEP: {inep}", ln=True)
        
        self.ln(10)
        self.line(10, 32, 200, 32)
        self.ln(5)

def gerar_pdf_bilhetes(dados):
    try:
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=False)
        total = dados['total']
        paginas = (total + 3) // 4
        if getattr(sys, 'frozen', False): raiz = os.path.dirname(sys.executable)
        else: raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(raiz, "assets", "logo.png")
        if not os.path.exists(logo_path): logo_path = os.path.join(raiz, "assets", "logo.jpg")

        count = 0
        for p in range(paginas):
            pdf.add_page()
            quadrantes = [(0, 0), (105, 0), (0, 148.5), (105, 148.5)]
            for q_x, q_y in quadrantes:
                if count >= total: break
                pdf.rect(q_x + 2.5, q_y + 2.5, 100, 143.5)
                m_x, m_y = q_x + 5, q_y + 5
                if os.path.exists(logo_path): pdf.image(logo_path, m_x, m_y, 10)
                pdf.set_font("helvetica", 'B', 7)
                pdf.set_xy(m_x + 12, m_y + 2)
                pdf.cell(83, 4, "ESCOLA MUNICIPAL TRÁ LÁ LÁ", ln=True, align='L')
                pdf.set_font("helvetica", 'B', 9)
                pdf.set_xy(q_x + 5, q_y + 15)
                assunto = str(dados.get('assunto', 'BILHETE')).upper()
                pdf.cell(95, 6, assunto, ln=True, align='C')
                pdf.set_font("helvetica", size=8)
                pdf.set_xy(q_x + 7.5, q_y + 25)
                pdf.multi_cell(90, 4, str(dados.get('mensagem', '')))
                
                atual_y = pdf.get_y() + 4
                
                if dados.get('autorizacao'):
                    pdf.set_font("helvetica", 'I', 8)
                    pdf.set_xy(q_x + 7.5, atual_y)
                    texto_aut = "Eu, ____________________________________________________, responsável pelo(a) estudante ____________________________________________________, autorizo sua participação."
                    pdf.multi_cell(90, 4.5, texto_aut)
                    atual_y = pdf.get_y() + 4
                
                # Assinatura do Responsável (se marcado)
                if dados.get('assinatura'):
                    pdf.set_font("helvetica", size=7)
                    pdf.set_xy(q_x + 7.5, atual_y + 2)
                    pdf.cell(90, 4, "Assinatura do Responsável: __________________________________________", ln=True)
                    atual_y = pdf.get_y() + 2
                
                # Assinatura Automática (Quem assina) - Fixa no fundo do bilhete, sem sobrepor
                pdf.set_font("helvetica", 'B', 7)
                # Posiciona 10mm antes do fim do quadrante (q_y + 148.5)
                pdf.set_xy(q_x + 5, q_y + 138)
                assinante = str(dados.get('assinante', 'Equipe Diretiva'))
                pdf.cell(95, 4, f"Atenciosamente, {assinante}", align='C')
                
                count += 1
        _salvar_e_abrir(pdf, "Bilhetes")
        return True, "OK"
    except Exception as e: return False, str(e)

def gerar_pdf_ata(titulo, conteudo):
    try:
        pdf = PDFGenerator()
        pdf.add_page()
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, titulo, ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("helvetica", size=11)
        pdf.multi_cell(0, 7, conteudo)
        _salvar_e_abrir(pdf, "Ata")
        return True, "OK"
    except Exception as e: return False, str(e)

def gerar_pdf_oficio(titulo, conteudo):
    try:
        pdf = PDFGenerator()
        pdf.add_page()
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, titulo, ln=True, align='L')
        pdf.ln(5)
        pdf.set_font("helvetica", size=11)
        pdf.multi_cell(0, 7, conteudo)
        _salvar_e_abrir(pdf, "Oficio")
        return True, "OK"
    except Exception as e: return False, str(e)

def _salvar_e_abrir(pdf, prefixo):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.exists(desktop):
        desktop = os.path.join(os.path.expanduser("~"), "Área de Trabalho")
        if not os.path.exists(desktop): desktop = os.getcwd()
    filename = f"{prefixo}_{datetime.now().strftime('%H%M%S')}.pdf"
    filepath = os.path.join(desktop, filename)
    pdf.output(filepath)
    if os.name == 'nt': os.startfile(filepath)
    else: subprocess.call(['open', filepath])

def gerar_pdf_documento(tipo, titulo, conteudo):
    if tipo == "ata": return gerar_pdf_ata(titulo, conteudo)
    else: return gerar_pdf_oficio(titulo, conteudo)
