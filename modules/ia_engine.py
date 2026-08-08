import os
import sqlite3
from groq import Groq
from database.db import get_connection

def redigir_documento(tipo, dados):
    """
    Usa a Groq IA (alternativa ao Gemini) para redigir documentos.
    """
    conn = get_connection()
    try:
        conf = conn.execute("SELECT gemini_api_key FROM dados_escola LIMIT 1").fetchone()
        if not conf or not conf['gemini_api_key']:
            return "Erro: Chave API não encontrada nos Dados da Escola."
        
        # A chave da Groq começa com 'gsk_'
        api_key = "".join(conf['gemini_api_key'].split())
        
        if not api_key.startswith("gsk_"):
            return "Erro: A chave atual não parece ser uma chave da Groq (deve começar com 'gsk_')."

        client = Groq(api_key=api_key)

        if tipo == 'ata':
            prompt = f"""
            Você é um secretário escolar formal. Escreva uma ATA DE REUNIÃO para a escola Lorenzette.
            Pauta: {dados.get('pauta')}
            Data: {dados.get('data')} às {dados.get('hora')}
            Local: {dados.get('local')}
            Participantes: {dados.get('participantes')}
            
            Instruções:
            - Use linguagem formal e técnica.
            - Comece com 'Aos {dados.get('data')}, às {dados.get('hora')} horas...'
            - Retorne apenas o texto da ata.
            """
        else:
            prompt = f"""
            Você é um secretário escolar formal. Escreva um OFÍCIO para a escola Lorenzette.
            Destinatário: {dados.get('destinatario')}
            Assunto: {dados.get('assunto')}
            
            Instruções:
            - Use o padrão oficial de ofícios.
            - Retorne apenas o texto do corpo do ofício.
            """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        return f"Erro na Groq IA: {str(e)}"
    finally:
        conn.close()
