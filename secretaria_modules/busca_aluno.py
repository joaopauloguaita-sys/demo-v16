"""
Painel: Buscar Aluno.
A Secretaria digita um nome (ou parte dele) e o sistema procura em TODAS
as escolas cadastradas de uma vez — não precisa saber de qual escola é
o aluno. Ao encontrar, mostra a ficha completa (só leitura), com os
campos preenchidos, e os links de WhatsApp/pasta do Drive clicáveis.
"""
import streamlit as st
from secretaria_modules.dados_escolas import carregar_tabela_combinada, link_whatsapp

CAMPOS_OCULTOS = ["base64", "api_key", "apikey", "senha", "password", "token", "id", "escola"]

RENOMEAR = {
    "nome": "Nome", "cgm": "CGM", "data_nascimento": "Data de Nascimento",
    "sexo": "Sexo", "cor_raca": "Cor/Raça", "cpf": "CPF", "rg": "RG",
    "certidao_nascimento": "Certidão de Nascimento",
    "municipio_nascimento": "Município de Nascimento", "uf_nascimento": "UF de Nascimento",
    "nome_mae": "Nome da Mãe", "cpf_mae": "CPF da Mãe", "telefone_mae": "Telefone da Mãe",
    "nome_pai": "Nome do Pai", "cpf_pai": "CPF do Pai", "telefone_pai": "Telefone do Pai",
    "responsavel": "Responsável", "telefone_responsavel": "Telefone do Responsável",
    "endereco": "Endereço", "bairro": "Bairro", "cidade": "Cidade", "cep": "CEP",
    "email": "E-mail", "alergico": "Possui Alergia?", "alergia_descricao": "Descrição da Alergia",
    "tipos_deficiencia": "Tipo de Deficiência", "necessidades_especiais": "Necessidades Especiais",
    "observacoes": "Observações", "saida_autorizada": "Autorização de Saída",
    "pasta_documentos": "Pasta de Documentos",
}


def _ficha_completa(aluno):
    st.markdown('<div class="painel">', unsafe_allow_html=True)
    st.markdown(f'<div class="titulo-secao" style="font-size:18px;">👤 {aluno.get("nome", "-")} '
               f'<span style="font-size:13px; color:#9aa3c0;">({aluno.get("escola", "")})</span></div>',
               unsafe_allow_html=True)

    tel_resp = aluno.get("telefone_responsavel")
    tel_mae = aluno.get("telefone_mae")
    tel_pai = aluno.get("telefone_pai")
    pasta = aluno.get("pasta_documentos")

    linha_links = st.columns(4)
    if pasta and str(pasta).strip() and str(pasta).lower() != "nan":
        with linha_links[0]:
            st.link_button("📁 Abrir Pasta (Drive)", pasta, use_container_width=True)
    if tel_resp and link_whatsapp(tel_resp):
        with linha_links[1]:
            st.link_button("💬 WhatsApp Responsável", link_whatsapp(tel_resp), use_container_width=True)
    if tel_mae and link_whatsapp(tel_mae):
        with linha_links[2]:
            st.link_button("💬 WhatsApp Mãe", link_whatsapp(tel_mae), use_container_width=True)
    if tel_pai and link_whatsapp(tel_pai):
        with linha_links[3]:
            st.link_button("💬 WhatsApp Pai", link_whatsapp(tel_pai), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(2)
    i = 0
    for chave, valor in aluno.items():
        if any(o in chave.lower() for o in CAMPOS_OCULTOS):
            continue
        if valor is None or str(valor).strip() in ("", "nan", "None"):
            continue
        rotulo = RENOMEAR.get(chave, chave.replace("_", " ").title())
        with cols[i % 2]:
            st.write(f"**{rotulo}:** {valor}")
        i += 1
    st.markdown('</div>', unsafe_allow_html=True)


def render():
    st.markdown('<div class="titulo-secao">🔍 Buscar Aluno</div>', unsafe_allow_html=True)

    st.markdown('<div class="painel">', unsafe_allow_html=True)
    col_busca, col_botao = st.columns([4, 1])
    with col_busca:
        termo = st.text_input("Nome do aluno", label_visibility="collapsed",
                              placeholder="Digite o nome do aluno...")
    with col_botao:
        buscar = st.button("🔍 Buscar", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not buscar and not termo:
        return
    if not termo.strip():
        st.warning("Digite um nome pra buscar.")
        return

    df_alunos, _ = carregar_tabela_combinada("alunos", "*")
    if df_alunos.empty:
        st.info("Nenhum dado de aluno disponível no momento.")
        return

    termo_norm = termo.strip().lower()
    encontrados = df_alunos[df_alunos["nome"].astype(str).str.lower().str.contains(termo_norm, na=False)]

    if encontrados.empty:
        st.warning(f"Nenhum aluno encontrado com o nome '{termo}'.")
        return

    st.markdown(f"**{len(encontrados)} aluno(s) encontrado(s):**")
    for _, aluno in encontrados.iterrows():
        rotulo = f"{aluno.get('nome', '-')} — {aluno.get('escola', '')}"
        if st.button(rotulo, key=f"btn_{aluno.get('escola','')}_{aluno.get('id','')}"):
            st.session_state["aluno_selecionado"] = aluno.to_dict()

    if "aluno_selecionado" in st.session_state:
        st.markdown("---")
        _ficha_completa(st.session_state["aluno_selecionado"])
