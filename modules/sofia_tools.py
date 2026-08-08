"""
Ferramentas que a SofIA pode chamar pra consultar o banco de dados real do
sistema (telefones, RG, horário de aula agora, faltas de um aluno, etc.),
em vez de inventar ou dizer "não sei".

Tudo aqui é só LEITURA — nenhuma função escreve no banco.
"""
import os
import sys
import unicodedata
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import get_connection


def _normalizar(txt):
    """Remove acentos e ignora maiúscula/minúscula, pra comparar nomes de
    forma confiável (o SQLite não faz isso direito com 'LIKE' em texto
    acentuado, tipo 'Português' vs 'portugues'). Também ignora os símbolos
    de ordinal (º/ª) e espaços extras, pra '1 ano a' bater com '1º Ano A'."""
    if not txt:
        return ""
    sem_ordinal = str(txt).replace("º", "").replace("ª", "").replace("°", "")
    nfkd = unicodedata.normalize("NFKD", sem_ordinal)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(sem_acento.casefold().split())


def _contem(alvo, texto):
    """True se 'alvo' aparece dentro de 'texto', ignorando acento/caixa."""
    return _normalizar(alvo) in _normalizar(texto)


def _localizar_turma(termo):
    """Acha a turma pelo nome (aceitando variação de acento/caixa)."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, nome_completo FROM turmas WHERE ativo=1").fetchall()
        for r in rows:
            if _contem(termo, r["nome_completo"] or ""):
                return dict(r)
        return None
    finally:
        conn.close()


DIAS_SEMANA_PT = ["Segunda-feira", "Terça-feira", "Quarta-feira",
                   "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

TABELAS_PESSOAS = [
    ("alunos", "Aluno(a)", "nome"),
    ("professores", "Professor(a)", "nome"),
    ("funcionarios", "Funcionário(a)", "nome"),
    ("pedagogas", "Pedagoga", "nome"),
    ("secretarios", "Secretário(a)", "nome"),
    ("diretores", "Diretor(a)", "nome"),
]


def _colunas(tabela):
    conn = get_connection()
    try:
        return [c[1] for c in conn.execute(f"PRAGMA table_info({tabela})").fetchall()]
    finally:
        conn.close()


def _localizar_pessoas(nome):
    """Procura o nome em todas as tabelas de pessoas e retorna uma lista
    com tabela/id/nome/data_admissao de cada correspondência encontrada
    (pode haver mais de uma pessoa com nome parecido)."""
    resultados = []
    conn = get_connection()
    try:
        for tabela, categoria, _ in TABELAS_PESSOAS:
            cols = _colunas(tabela)
            sel_admissao = "data_admissao" if "data_admissao" in cols else "NULL as data_admissao"
            rows = conn.execute(
                f"SELECT id, nome, {sel_admissao} as data_admissao FROM {tabela}").fetchall()
            for r in rows:
                if _contem(nome, r["nome"] or ""):
                    resultados.append({
                        "tabela": tabela, "categoria": categoria, "id": r["id"],
                        "nome": r["nome"], "data_admissao": r["data_admissao"],
                    })
    finally:
        conn.close()
    return resultados


# ============================================================
# FERRAMENTA 1: buscar dados de uma pessoa (telefone, RG, CPF, cargo/turma)
# ============================================================

def buscar_pessoa(nome):
    """Procura por nome (parcial) em alunos, professores, funcionários,
    pedagogas, secretários e diretores. Retorna os dados de contato/
    identificação de cada pessoa encontrada."""
    resultados = []
    conn = get_connection()
    try:
        for tabela, categoria, col_nome in TABELAS_PESSOAS:
            cols = _colunas(tabela)
            campos_interesse = [c for c in
                ["nome", "cpf", "rg", "nome_mae", "cpf_mae", "telefone_mae",
                 "nome_pai", "cpf_pai", "telefone_pai",
                 "telefone1", "telefone_responsavel", "responsavel", "cargo",
                 "turma_id", "situacao_funcional",
                 "endereco", "rua", "numero", "complemento", "bairro",
                 "cidade", "municipio", "cep", "email"] if c in cols]
            sql = f"SELECT {', '.join(campos_interesse)} FROM {tabela} WHERE (arquivado=0 OR arquivado IS NULL)"
            rows = conn.execute(sql).fetchall()
            for r in rows:
                if not _contem(nome, r["nome"] or ""):
                    continue
                d = dict(r)
                d["_categoria"] = categoria
                if tabela == "alunos" and d.get("turma_id"):
                    turma = conn.execute("SELECT nome_completo FROM turmas WHERE id=?",
                                         (d["turma_id"],)).fetchone()
                    d["turma"] = turma["nome_completo"] if turma else None
                resultados.append(d)
    finally:
        conn.close()
    if not resultados:
        return {"encontrado": False, "mensagem": f"Não encontrei ninguém chamado '{nome}' cadastrado."}
    return {"encontrado": True, "pessoas": resultados}


# ============================================================
# FERRAMENTA 2: qual aula uma turma tem agora (dia da semana + horário atuais)
# ============================================================

def horario_atual(turma):
    """Descobre qual disciplina uma turma tem agora, com base no dia da
    semana e horário atuais do computador."""
    agora = datetime.now()
    dia_semana = DIAS_SEMANA_PT[agora.weekday()]
    hora_atual = agora.strftime("%H:%M")

    conn = get_connection()
    try:
        turma_row = _localizar_turma(turma)
        if not turma_row:
            return {"encontrado": False, "mensagem": f"Não encontrei a turma '{turma}'."}

        if dia_semana in ("Sábado", "Domingo"):
            return {"encontrado": True, "turma": turma_row["nome_completo"],
                    "dia": dia_semana, "mensagem": "Hoje é fim de semana, não tem aula."}

        aulas = conn.execute(
            "SELECT horario_inicio, horario_fim, disciplina_id FROM horarios "
            "WHERE turma_id=? AND dia_semana=? ORDER BY horario_inicio",
            (turma_row["id"], dia_semana)).fetchall()

        cols_disc = _colunas("disciplinas")
        for a in aulas:
            if a["horario_inicio"] <= hora_atual <= a["horario_fim"]:
                disc = conn.execute("SELECT * FROM disciplinas WHERE id=?",
                                    (a["disciplina_id"],)).fetchone()
                nome_disc = disc["nome"] if disc and "nome" in disc.keys() else "(vaga)"
                professor_nome = None
                if disc:
                    d_disc = dict(disc)
                    if "professor_id" in cols_disc and d_disc.get("professor_id"):
                        prof = conn.execute("SELECT nome FROM professores WHERE id=?",
                                            (d_disc["professor_id"],)).fetchone()
                        professor_nome = prof["nome"] if prof else None
                    elif "professor_nome" in d_disc:
                        professor_nome = d_disc.get("professor_nome")
                return {
                    "encontrado": True, "turma": turma_row["nome_completo"],
                    "dia": dia_semana, "horario": f"{a['horario_inicio']}–{a['horario_fim']}",
                    "disciplina_agora": nome_disc, "professor": professor_nome,
                }
        return {"encontrado": True, "turma": turma_row["nome_completo"], "dia": dia_semana,
                "mensagem": "Agora não é horário de nenhuma aula dessa turma (intervalo ou fora do período letivo)."}
    finally:
        conn.close()


# ============================================================
# FERRAMENTA: grade horária completa de uma turma (a semana toda, não só agora)
# ============================================================

def grade_horaria(turma, disciplina=None):
    """Retorna a grade de horários COMPLETA de uma turma (todos os dias da
    semana), opcionalmente filtrada por uma disciplina específica. Use isso
    (não horario_atual) quando for perguntado 'quais os horários de X' ou
    'que dias a turma tem aula de X' — coisas sobre a grade em geral, não
    sobre o exato momento presente."""
    conn = get_connection()
    try:
        turma_row = _localizar_turma(turma)
        if not turma_row:
            return {"encontrado": False, "mensagem": f"Não encontrei a turma '{turma}'."}

        sql = ("SELECT h.dia_semana, h.horario_inicio, h.horario_fim, d.nome as disciplina "
               "FROM horarios h LEFT JOIN disciplinas d ON d.id = h.disciplina_id "
               "WHERE h.turma_id=?")
        params = [turma_row["id"]]
        ordem_dias = {"Segunda-feira": 1, "Terça-feira": 2, "Quarta-feira": 3,
                      "Quinta-feira": 4, "Sexta-feira": 5}
        rows = conn.execute(sql, params).fetchall()
        aulas = [dict(r) for r in rows]
        if disciplina:
            aulas = [a for a in aulas if _contem(disciplina, a.get("disciplina") or "")]
        aulas = sorted(aulas, key=lambda r: (ordem_dias.get(r["dia_semana"], 9), r["horario_inicio"]))

        if not aulas:
            msg = f"Não encontrei aulas de '{disciplina}' na grade de {turma_row['nome_completo']}." if disciplina \
                  else f"Não encontrei nenhuma aula cadastrada pra {turma_row['nome_completo']}."
            return {"encontrado": True, "turma": turma_row["nome_completo"], "mensagem": msg}

        return {"encontrado": True, "turma": turma_row["nome_completo"],
                "disciplina_filtrada": disciplina, "aulas": aulas}
    finally:
        conn.close()


# ============================================================
# FERRAMENTA 3: faltas de um aluno (mês / bimestre / ano)
# ============================================================

def faltas_aluno(nome, periodo="mes"):
    """Conta as faltas de um aluno no mês atual, no bimestre atual ou no
    ano letivo inteiro. periodo deve ser 'mes', 'bimestre' ou 'ano'."""
    conn = get_connection()
    try:
        candidatos = conn.execute(
            "SELECT id, nome FROM alunos WHERE (arquivado=0 OR arquivado IS NULL)").fetchall()
        aluno = next((a for a in candidatos if _contem(nome, a["nome"] or "")), None)
        if not aluno:
            return {"encontrado": False, "mensagem": f"Não encontrei nenhum aluno chamado '{nome}'."}

        hoje = date.today()
        if periodo == "ano":
            data_ini, data_fim = date(hoje.year, 1, 1).isoformat(), date(hoje.year, 12, 31).isoformat()
        elif periodo == "bimestre":
            escola = conn.execute("SELECT * FROM dados_escola LIMIT 1").fetchone()
            data_ini, data_fim = None, None
            if escola:
                d_esc = dict(escola)
                for n in range(1, 5):
                    ini, fim = d_esc.get(f"bim{n}_inicio"), d_esc.get(f"bim{n}_fim")
                    if ini and fim and ini <= hoje.isoformat() <= fim:
                        data_ini, data_fim = ini, fim
                        break
            if not data_ini:
                # fallback: mês atual, se não achou as datas do bimestre configuradas
                data_ini = date(hoje.year, hoje.month, 1).isoformat()
                data_fim = hoje.isoformat()
        else:  # mes
            data_ini = date(hoje.year, hoje.month, 1).isoformat()
            data_fim = hoje.isoformat()

        total_faltas = conn.execute(
            "SELECT COUNT(*) FROM frequencia WHERE aluno_id=? AND presente=0 AND data BETWEEN ? AND ?",
            (aluno["id"], data_ini, data_fim)).fetchone()[0]
        total_aulas = conn.execute(
            "SELECT COUNT(*) FROM frequencia WHERE aluno_id=? AND data BETWEEN ? AND ?",
            (aluno["id"], data_ini, data_fim)).fetchone()[0]

        return {
            "encontrado": True, "aluno": aluno["nome"], "periodo": periodo,
            "de": data_ini, "ate": data_fim,
            "faltas": total_faltas, "aulas_registradas": total_aulas,
        }
    finally:
        conn.close()


# ============================================================
# FERRAMENTA 4: atestados (de uma pessoa, ou da escola inteira, num período)
# ============================================================

def contar_atestados(nome=None, data_inicio=None, data_fim=None, desde_admissao=False):
    """Conta e lista atestados/declarações de uma pessoa específica (aluno,
    professor, funcionário, pedagoga, secretário(a) ou diretor(a)) ou da
    escola inteira, dentro de um período. data_inicio/data_fim no formato
    AAAA-MM-DD. Se desde_admissao=True, usa a data de admissão da pessoa
    como início do período (ignora data_inicio nesse caso)."""
    conn = get_connection()
    try:
        pessoas_alvo = None
        if nome:
            pessoas_alvo = _localizar_pessoas(nome)
            if not pessoas_alvo:
                return {"encontrado": False, "mensagem": f"Não encontrei ninguém chamado '{nome}'."}
            if desde_admissao:
                admissoes = [p["data_admissao"] for p in pessoas_alvo if p.get("data_admissao")]
                if admissoes:
                    data_inicio = min(admissoes)

        sql = "SELECT entidade, entidade_id, tipo, data, duracao, unidade_duracao, observacao FROM atestados WHERE (excluido IS NULL OR excluido=0)"
        params = []
        if pessoas_alvo:
            pares = " OR ".join(["(entidade=? AND entidade_id=?)"] * len(pessoas_alvo))
            sql += f" AND ({pares})"
            for p in pessoas_alvo:
                params += [p["tabela"], p["id"]]
        if data_inicio:
            sql += " AND data >= ?"
            params.append(data_inicio)
        if data_fim:
            sql += " AND data <= ?"
            params.append(data_fim)
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

        return {
            "encontrado": True,
            "pessoa": pessoas_alvo[0]["nome"] if pessoas_alvo else "toda a escola",
            "periodo_de": data_inicio or "sem limite (todo o histórico)",
            "periodo_ate": data_fim or "hoje",
            "total_atestados": len(rows),
            "detalhes": rows[:30],
        }
    finally:
        conn.close()


# ============================================================
# FERRAMENTA 5: ocorrências (de uma pessoa, ou da escola inteira, num período)
# ============================================================

def listar_ocorrencias(nome=None, data_inicio=None, data_fim=None):
    """Lista ocorrências registradas de uma pessoa específica ou da escola
    inteira, dentro de um período. data_inicio/data_fim no formato AAAA-MM-DD."""
    conn = get_connection()
    try:
        pessoas_alvo = None
        if nome:
            pessoas_alvo = _localizar_pessoas(nome)
            if not pessoas_alvo:
                return {"encontrado": False, "mensagem": f"Não encontrei ninguém chamado '{nome}'."}

        sql = "SELECT entidade, entidade_id, data, descricao, registrado_por FROM ocorrencias WHERE (excluido IS NULL OR excluido=0)"
        params = []
        if pessoas_alvo:
            pares = " OR ".join(["(entidade=? AND entidade_id=?)"] * len(pessoas_alvo))
            sql += f" AND ({pares})"
            for p in pessoas_alvo:
                params += [p["tabela"], p["id"]]
        if data_inicio:
            sql += " AND data >= ?"
            params.append(data_inicio)
        if data_fim:
            sql += " AND data <= ?"
            params.append(data_fim)
        sql += " ORDER BY data DESC"
        rows = conn.execute(sql, params).fetchall()

        nomes_cache = {}
        detalhes = []
        for r in rows:
            chave = (r["entidade"], r["entidade_id"])
            if chave not in nomes_cache:
                try:
                    nm = conn.execute(f"SELECT nome FROM {r['entidade']} WHERE id=?",
                                      (r["entidade_id"],)).fetchone()
                    nomes_cache[chave] = nm["nome"] if nm else "?"
                except Exception:
                    nomes_cache[chave] = "?"
            d = dict(r)
            d["nome_pessoa"] = nomes_cache[chave]
            detalhes.append(d)

        return {
            "encontrado": True,
            "periodo_de": data_inicio or "sem limite (todo o histórico)",
            "periodo_ate": data_fim or "hoje",
            "total_ocorrencias": len(detalhes),
            "ocorrencias": detalhes[:30],
        }
    finally:
        conn.close()


# ============================================================
# FERRAMENTA 6: estatísticas gerais da escola (contagens de tudo)
# ============================================================

def estatisticas_gerais():
    """Retorna um panorama geral com as contagens de tudo que existe no
    sistema: alunos (total, meninos, meninas), professores, funcionários,
    pedagogas, secretários(as), diretores(as), turmas ativas, fila de
    espera, alunos na Informática/Fanfarra/Baliza/Xadrez, e itens do
    estoque abaixo do mínimo. Use isso pra QUALQUER pergunta do tipo
    'quantos/quantas X tem na escola'."""
    conn = get_connection()
    try:
        dados = {
            "alunos_ativos": conn.execute(
                "SELECT COUNT(*) FROM alunos WHERE ativo=1 AND (arquivado=0 OR arquivado IS NULL)").fetchone()[0],
            "meninos": conn.execute(
                "SELECT COUNT(*) FROM alunos WHERE ativo=1 AND (arquivado=0 OR arquivado IS NULL) AND sexo='Masculino'").fetchone()[0],
            "meninas": conn.execute(
                "SELECT COUNT(*) FROM alunos WHERE ativo=1 AND (arquivado=0 OR arquivado IS NULL) AND sexo='Feminino'").fetchone()[0],
            "professores": conn.execute(
                "SELECT COUNT(*) FROM professores WHERE ativo=1 AND (arquivado=0 OR arquivado IS NULL)").fetchone()[0],
            "funcionarios": conn.execute(
                "SELECT COUNT(*) FROM funcionarios WHERE ativo=1 AND (arquivado=0 OR arquivado IS NULL)").fetchone()[0],
            "pedagogas": conn.execute(
                "SELECT COUNT(*) FROM pedagogas WHERE ativo=1 AND (arquivado=0 OR arquivado IS NULL)").fetchone()[0],
            "secretarios": conn.execute(
                "SELECT COUNT(*) FROM secretarios WHERE ativo=1 AND (arquivado=0 OR arquivado IS NULL)").fetchone()[0],
            "diretores": conn.execute(
                "SELECT COUNT(*) FROM diretores WHERE ativo=1 AND (arquivado=0 OR arquivado IS NULL)").fetchone()[0],
            "turmas_ativas": conn.execute("SELECT COUNT(*) FROM turmas WHERE ativo=1").fetchone()[0],
        }
        for chave, tabela, condicao in [
            ("fila_espera", "fila_espera", "excluido IS NULL OR excluido=0"),
            ("curso_informatica", "curso_informatica", "excluido IS NULL OR excluido=0"),
            ("xadrez", "xadrez_membros", "1=1"),
        ]:
            try:
                dados[chave] = conn.execute(f"SELECT COUNT(*) FROM {tabela} WHERE {condicao}").fetchone()[0]
            except Exception:
                dados[chave] = None
        try:
            dados["fanfarra"] = conn.execute(
                "SELECT COUNT(*) FROM fanfarra_membros WHERE categoria='FANFARRA'").fetchone()[0]
            dados["baliza"] = conn.execute(
                "SELECT COUNT(*) FROM fanfarra_membros WHERE categoria='BALIZA'").fetchone()[0]
        except Exception:
            dados["fanfarra"] = dados["baliza"] = None
        try:
            itens_baixo = conn.execute(
                "SELECT nome, quantidade, estoque_minimo FROM estoque_itens "
                "WHERE (excluido IS NULL OR excluido=0) AND quantidade < estoque_minimo").fetchall()
            dados["itens_estoque_abaixo_minimo"] = [dict(i) for i in itens_baixo]
        except Exception:
            dados["itens_estoque_abaixo_minimo"] = []
        return dados
    finally:
        conn.close()


# ============================================================
# FERRAMENTA 7: listar nomes de quem participa de uma atividade
# ============================================================

def listar_participantes(atividade):
    """Lista os NOMES dos alunos inscritos numa atividade extracurricular
    específica: 'informatica', 'fanfarra', 'baliza', 'xadrez' ou
    'fila_espera'. Use isso sempre que for pedido os nomes/lista de quem
    está em alguma dessas atividades (estatisticas_gerais só dá o total,
    não os nomes)."""
    conn = get_connection()
    try:
        a = (atividade or "").strip().lower()
        if a in ("informatica", "informática", "curso_informatica", "curso de informática"):
            rows = conn.execute(
                "SELECT nome_aluno as nome, serie_turma, dia_semana, periodo, horario "
                "FROM curso_informatica WHERE excluido IS NULL OR excluido=0 ORDER BY nome_aluno"
            ).fetchall()
            return {"atividade": "Curso de Informática", "total": len(rows),
                    "participantes": [dict(r) for r in rows]}

        if a in ("fanfarra", "baliza"):
            categoria = "BALIZA" if a == "baliza" else "FANFARRA"
            rows = conn.execute(
                "SELECT al.nome FROM fanfarra_membros f JOIN alunos al ON al.id = f.aluno_id "
                "WHERE f.categoria=? ORDER BY al.nome", (categoria,)).fetchall()
            return {"atividade": categoria.title(), "total": len(rows),
                    "participantes": [r["nome"] for r in rows]}

        if a in ("xadrez", "aula de xadrez"):
            rows = conn.execute(
                "SELECT al.nome FROM xadrez_membros x JOIN alunos al ON al.id = x.aluno_id "
                "ORDER BY al.nome").fetchall()
            return {"atividade": "Xadrez", "total": len(rows),
                    "participantes": [r["nome"] for r in rows]}

        if a in ("fila_espera", "fila de espera", "fila"):
            rows = conn.execute(
                "SELECT nome, serie, turno_preferencia FROM fila_espera "
                "WHERE excluido IS NULL OR excluido=0 ORDER BY nome").fetchall()
            return {"atividade": "Fila de Espera", "total": len(rows),
                    "participantes": [dict(r) for r in rows]}

        return {"erro": f"Atividade '{atividade}' não reconhecida. "
                         "Use: informatica, fanfarra, baliza, xadrez ou fila_espera."}
    finally:
        conn.close()


# ============================================================
# FERRAMENTA 8: alunos alérgicos
# ============================================================

def listar_alunos_alergicos():
    """Lista os nomes dos alunos marcados como alérgicos, junto com a
    descrição da alergia de cada um e a turma."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT nome, alergia_descricao, turma_id FROM alunos "
            "WHERE alergico='Sim' AND ativo=1 AND (arquivado=0 OR arquivado IS NULL) "
            "ORDER BY nome").fetchall()
        alunos = []
        for r in rows:
            d = dict(r)
            turma = conn.execute("SELECT nome_completo FROM turmas WHERE id=?",
                                 (d["turma_id"],)).fetchone() if d.get("turma_id") else None
            d["turma"] = turma["nome_completo"] if turma else None
            del d["turma_id"]
            alunos.append(d)
        return {"total": len(alunos), "alunos": alunos}
    finally:
        conn.close()


# ============================================================
# FERRAMENTA 9: todos os alunos de uma turma (com contato dos responsáveis)
# ============================================================

def listar_alunos_da_turma(turma):
    """Lista TODOS os alunos matriculados numa turma específica, com nome,
    responsável e telefone de contato. Use isso pra 'quais alunos tem na
    turma X' ou 'telefone de todos os alunos do Y ano'."""
    conn = get_connection()
    try:
        turma_row = _localizar_turma(turma)
        if not turma_row:
            return {"encontrado": False, "mensagem": f"Não encontrei a turma '{turma}'."}
        rows = conn.execute(
            "SELECT nome, responsavel, telefone_responsavel, nome_mae, telefone_mae, "
            "nome_pai, telefone_pai FROM alunos WHERE turma_id=? AND ativo=1 "
            "AND (arquivado=0 OR arquivado IS NULL) ORDER BY nome",
            (turma_row["id"],)).fetchall()
        return {"encontrado": True, "turma": turma_row["nome_completo"],
                "total": len(rows), "alunos": [dict(r) for r in rows]}
    finally:
        conn.close()


# ============================================================
# Definições das ferramentas no formato que a API da Groq espera
# ============================================================

FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_pessoa",
            "description": "Busca telefone, CPF, RG, endereço, e-mail, cargo ou turma de um aluno, "
                            "professor, funcionário, pedagoga, secretário(a) ou diretor(a) pelo nome.",
            "parameters": {
                "type": "object",
                "properties": {"nome": {"type": "string", "description": "Nome (completo ou parcial) da pessoa"}},
                "required": ["nome"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "horario_atual",
            "description": "Descobre qual disciplina/aula uma turma está tendo NESTE EXATO MOMENTO, "
                            "com base no dia da semana e horário atuais. Só serve pra perguntas sobre "
                            "'agora'/'nesse momento'. Para perguntas sobre a grade de horários em geral "
                            "(ex: 'quais os horários de Geografia', 'que dias tem aula de X'), use "
                            "grade_horaria em vez desta.",
            "parameters": {
                "type": "object",
                "properties": {"turma": {"type": "string", "description": "Nome da turma, ex: '5º Ano A'"}},
                "required": ["turma"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grade_horaria",
            "description": "Retorna a grade de horários COMPLETA de uma turma (todos os dias da "
                            "semana), opcionalmente filtrada por disciplina. Use pra perguntas sobre "
                            "a grade em geral, tipo 'quais os horários de Geografia do 5º ano', "
                            "diferente de horario_atual (que é só sobre o momento presente).",
            "parameters": {
                "type": "object",
                "properties": {
                    "turma": {"type": "string", "description": "Nome da turma, ex: '5º Ano A'"},
                    "disciplina": {"type": "string", "description": "Nome da disciplina, opcional"},
                },
                "required": ["turma"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "faltas_aluno",
            "description": "Conta quantas faltas um aluno teve no mês atual, no bimestre atual "
                            "ou no ano letivo inteiro.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome do aluno"},
                    "periodo": {"type": "string", "enum": ["mes", "bimestre", "ano"],
                                "description": "Período a considerar"},
                },
                "required": ["nome", "periodo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "contar_atestados",
            "description": "Conta e lista os atestados/declarações de uma pessoa específica "
                            "(aluno, professor, funcionário, pedagoga, secretário(a) ou diretor(a)) "
                            "ou da escola inteira, dentro de um período. Use isso pra perguntas "
                            "tipo 'quantos atestados o professor X teve esse mês', 'quantos atestados "
                            "a escola teve desde tal data', ou 'atestados do professor Y desde que "
                            "ele começou a trabalhar'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string",
                             "description": "Nome da pessoa. Deixe vazio ou omita pra contar da escola inteira."},
                    "data_inicio": {"type": "string", "description": "Data inicial no formato AAAA-MM-DD"},
                    "data_fim": {"type": "string", "description": "Data final no formato AAAA-MM-DD"},
                    "desde_admissao": {"type": "boolean",
                                        "description": "Se true, conta desde a data em que a pessoa começou a trabalhar na escola"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_ocorrencias",
            "description": "Lista as ocorrências registradas de uma pessoa específica ou da "
                            "escola inteira, dentro de um período. Use pra perguntas tipo 'quais "
                            "ocorrências aconteceram esse ano' ou 'ocorrências do professor X'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string",
                             "description": "Nome da pessoa. Deixe vazio ou omita pra listar da escola inteira."},
                    "data_inicio": {"type": "string", "description": "Data inicial no formato AAAA-MM-DD"},
                    "data_fim": {"type": "string", "description": "Data final no formato AAAA-MM-DD"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estatisticas_gerais",
            "description": "Retorna as contagens gerais da escola: total de alunos (meninos/meninas), "
                            "professores, funcionários, pedagogas, secretários(as), diretores(as), "
                            "turmas ativas, fila de espera, Informática, Fanfarra, Baliza, Xadrez, e "
                            "itens do estoque abaixo do mínimo. Use SEMPRE que a pergunta for do tipo "
                            "'quantos/quantas X tem na escola' e não for sobre uma pessoa específica.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_participantes",
            "description": "Lista os NOMES dos alunos inscritos numa atividade extracurricular "
                            "('informatica', 'fanfarra', 'baliza', 'xadrez' ou 'fila_espera'). "
                            "Use isso (não a estatisticas_gerais) sempre que for pedido nomes ou "
                            "lista de quem participa de alguma dessas atividades.",
            "parameters": {
                "type": "object",
                "properties": {
                    "atividade": {"type": "string",
                                  "enum": ["informatica", "fanfarra", "baliza", "xadrez", "fila_espera"]},
                },
                "required": ["atividade"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_alunos_alergicos",
            "description": "Lista os alunos marcados como alérgicos, com a descrição da alergia "
                            "e a turma de cada um.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_alunos_da_turma",
            "description": "Lista TODOS os alunos de uma turma específica, com nome do "
                            "responsável e telefone de contato de cada um. Use pra perguntas "
                            "tipo 'quais alunos tem no 1º ano A' ou 'telefone de todos os alunos "
                            "do 5º ano'.",
            "parameters": {
                "type": "object",
                "properties": {"turma": {"type": "string", "description": "Nome da turma, ex: '1º Ano A'"}},
                "required": ["turma"],
            },
        },
    },
]

_DISPATCH = {
    "buscar_pessoa": lambda args: buscar_pessoa(args.get("nome", "")),
    "horario_atual": lambda args: horario_atual(args.get("turma", "")),
    "grade_horaria": lambda args: grade_horaria(args.get("turma", ""), args.get("disciplina") or None),
    "faltas_aluno": lambda args: faltas_aluno(args.get("nome", ""), args.get("periodo", "mes")),
    "contar_atestados": lambda args: contar_atestados(
        args.get("nome") or None, args.get("data_inicio") or None,
        args.get("data_fim") or None, args.get("desde_admissao", False)),
    "listar_ocorrencias": lambda args: listar_ocorrencias(
        args.get("nome") or None, args.get("data_inicio") or None, args.get("data_fim") or None),
    "estatisticas_gerais": lambda args: estatisticas_gerais(),
    "listar_participantes": lambda args: listar_participantes(args.get("atividade", "")),
    "listar_alunos_alergicos": lambda args: listar_alunos_alergicos(),
    "listar_alunos_da_turma": lambda args: listar_alunos_da_turma(args.get("turma", "")),
}


def executar_ferramenta(nome_funcao, argumentos: dict):
    """Executa a ferramenta pedida pela IA e retorna o resultado (dict)."""
    fn = _DISPATCH.get(nome_funcao)
    if not fn:
        return {"erro": f"Ferramenta desconhecida: {nome_funcao}"}
    try:
        return fn(argumentos)
    except Exception as e:
        return {"erro": str(e)}
