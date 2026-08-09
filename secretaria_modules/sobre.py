"""
Painel: Contato, Vendas e Suporte.
"""
import streamlit as st


def render():
    st.markdown('<div class="titulo-secao">☎️ Contato, Vendas e Suporte</div>', unsafe_allow_html=True)
    st.markdown('<div class="painel" style="text-align:center; padding:35px;">', unsafe_allow_html=True)
    try:
        st.image("assets/logo.png", width=110)
    except Exception:
        st.markdown("### 🏫")
    st.markdown("""
        <div style="font-size:20px; font-weight:800; color:#d6b64d; margin-top:10px;">
            João - Secretário Escolar
        </div>
        <div style="font-weight:600; color:#9aa3c0; margin-bottom:15px;">
            Painel da Secretaria de Educação
        </div>
        <p style="max-width:600px; margin:0 auto 20px auto; color:#c9cfe8;">
            Visão consolidada de todas as escolas do município que usam o sistema
            "João - Secretário Escolar" — alunos, equipe, turmas e muito mais,
            tudo num só lugar.
        </p>
        <div style="font-weight:700; color:#d6b64d; margin-bottom:8px;">☎️ Contato, Vendas e Suporte</div>
        <div>✉️ joao.secretarioescolar@gmail.com</div>
        <div>📱 (43) 99908-9871 &nbsp;•&nbsp; (43) 99936-1415</div>
        <div style="margin-top:20px; font-size:12px; color:#6c7aa8;">
            Desenvolvido por João Paulo A. Guaita &nbsp;•&nbsp; Licença de uso cedida gratuitamente
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
