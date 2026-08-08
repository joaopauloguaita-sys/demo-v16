import os, sys
from tkinter import filedialog, messagebox
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

try:
    from docxtpl import DocxTemplate
    DOCXTPL_AVAILABLE = True
except ImportError:
    DOCXTPL_AVAILABLE = False

MESES_PT = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
            'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']

def _buscar_autoridades():
    from database.db import get_connection
    conn = get_connection()
    try:
        d = conn.execute('SELECT nome FROM diretores WHERE ativo=1 LIMIT 1').fetchone()
        s = conn.execute('SELECT nome FROM secretarios WHERE ativo=1 LIMIT 1').fetchone()
        return {'diretor': d[0] if d else '', 'secretario': s[0] if s else ''}
    except: return {'diretor': '', 'secretario': ''}
    finally: conn.close()

def _buscar_municipio():
    from database.db import get_connection
    conn = get_connection()
    try:
        e = conn.execute('SELECT municipio FROM dados_escola LIMIT 1').fetchone()
        return (e[0] or 'Município') if e else 'Município'
    except: return 'Município'
    finally: conn.close()

def gerar_documento_word(tipo, dados_aluno, parent=None):
    if not DOCXTPL_AVAILABLE:
        messagebox.showerror('Erro', 'Biblioteca docxtpl não encontrada.', parent=parent)
        return

    modelos = {
        'matricula': 'REQUERIMENTO_MATRICULA_2025.docx',
        'renovacao': 'REQUERIMENTO_DE_RENOVACAO_MATRICULA_2025.docx',
        'saude': 'FICHA_DE_SAUDE_2025.docx',
        'autorizacao_imagem': 'TERMO_USO_IMAGEM_2026.docx',
        'vaga': 'declaração_de_vaga.docx',
        'saida': 'AUTORIZAÇÃO_PARA_SAIDA_SOZINHO.docx',
        'autorizacao_fanfarra': 'AUTORIZAÇÃO_FANFARRA_BALIZA.docx',
        'certificado_fanfarra': 'CERTIFICADO DE PARTICIPAÇÃO.docx',
        'certificado_conclusao': 'CERTIFICADO DE CONCLUSÃO.docx',
        'autorizacao_xadrez': 'AUTORIZAÇÃO_XADREZ.docx',
        'comparecimento': 'declaracao_de_comparecimento.docx',
    }
    
    arq = modelos.get(tipo)
    caminhos = [os.path.join(BASE_DIR, arq), os.path.join(ROOT_DIR, arq), os.path.join(os.getcwd(), arq)]
    cam_final = next((c for c in caminhos if os.path.exists(c)), None)
    
    if not cam_final:
        messagebox.showerror('Erro', f"Modelo '{arq}' não encontrado.", parent=parent)
        return

    try:
        doc = DocxTemplate(cam_final)
        aut = _buscar_autoridades()
        municipio = _buscar_municipio()
        agora = datetime.now()
        mes_extenso = MESES_PT[agora.month - 1].capitalize()
        local_data = f"{municipio}, {agora.day} de {mes_extenso} de {agora.year}"
        
        # Pega a lista (seja qual for o nome que veio da aba)
        lista_dados = dados_aluno.get('alunos', dados_aluno.get('membros', []))

        # --- DICIONÁRIO TOTAL DE TAGS ---
        ctx = {k: (v or '') for k, v in dados_aluno.items()}
        ctx.update({
            # Identificação
            'nome': dados_aluno.get('nome', dados_aluno.get('aluno', '')),
            'aluno': dados_aluno.get('aluno', dados_aluno.get('nome', '')),
            'cgm': dados_aluno.get('cgm', ''),
            'cpf': dados_aluno.get('cpf', ''),
            'rg': dados_aluno.get('rg', ''),
            'data_nasc': dados_aluno.get('data_nascimento', dados_aluno.get('data_nasc', '')),
            'certidao': dados_aluno.get('certidao_nascimento', ''),
            'responsavel': dados_aluno.get('responsavel', ''),
            
            # Turmas
            'turma': dados_aluno.get('turma_var', dados_aluno.get('turma', '')),
            'turma_var': dados_aluno.get('turma_var', dados_aluno.get('turma', '')),
            'turno': dados_aluno.get('turno', ''),
            
            # Autoridades e Escola
            'diretor': aut['diretor'], 
            'diretora': aut['diretor'], 
            'secretario': aut['secretario'], 
            'escola': dados_aluno.get('_escola', 'Escola Municipal'),
            'cnpj_escola': dados_aluno.get('_cnpj_escola', ''),
            'mantenedora': dados_aluno.get('_mantenedora', ''),
            
            # Localização e Datas
            'local_data': local_data,
            'dia': str(agora.day).zfill(2),
            'mes_extenso': mes_extenso,
            'ano': str(agora.year),
            
            # Específicos
            'como_vai': dados_aluno.get('como_vai', ''),
            'obs': dados_aluno.get('obs', ''),
            'geo_tipo': dados_aluno.get('tipo_ident_geo', ''),
            'geo_num': dados_aluno.get('numero_ident_geo', ''),
            'cor_raca': dados_aluno.get('cor_raca', ''),
            'professor': dados_aluno.get('professor', ''),
            'hora_inicio': dados_aluno.get('hora_inicio', ''),
            'hora_fim': dados_aluno.get('hora_fim', ''),

            # DUPLICIDADE DE SEGURANÇA PARA O LOOP (Resolve o Word em Branco)
            'alunos': lista_dados,
            'membros': lista_dados
        })

        doc.render(ctx)
        sugestao = f"Documento_{agora.strftime('%H%M%S')}.docx"
        salv = filedialog.asksaveasfilename(defaultextension='.docx', initialfile=sugestao, parent=parent)
        if salv:
            doc.save(salv)
            if sys.platform.startswith('win'): os.startfile(salv)
            
    except Exception as e: 
        messagebox.showerror('Erro', f'Falha ao gerar Word: {str(e)}', parent=parent)

def salvar_requerimento(tipo, dados_aluno, nome_escola, parent=None):
    dados_aluno['_escola'] = nome_escola
    gerar_documento_word(tipo, dados_aluno, parent=parent)