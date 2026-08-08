import sqlite3
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import get_logger

logger = get_logger(__name__)

# Regex para validar nomes de tabelas/colunas usados em f-strings de SQL.
# Permite letras, dígitos e underscores desde que não comece com dígito.
_NOME_VALIDO_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def nome_seguro(nome):
    """Retorna True se o nome é um identificador SQL seguro."""
    return isinstance(nome, str) and bool(_NOME_VALIDO_RE.match(nome))


def get_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    possiveis = [
        os.path.join(base_dir, 'database.db'),
        os.path.join(base_dir, 'database', 'database.db'),
        'database.db'
    ]
    for path in possiveis:
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alunos'")
                if cursor.fetchone():
                    conn.row_factory = sqlite3.Row
                    cursor.execute("PRAGMA foreign_keys = ON")
                    return conn
                conn.close()
            except Exception as e:
                logger.error("Erro ao abrir banco em %s: %s", path, e)
    db_path = os.path.join(base_dir, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
    except Exception as e:
        logger.error("Erro ao habilitar foreign_keys: %s", e)
    return conn

def inicializar_banco():
    migrar_banco()

def migrar_banco():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Garantir tabelas
        cursor.execute("CREATE TABLE IF NOT EXISTS turmas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS dados_escola (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_escola TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS atas (id INTEGER PRIMARY KEY AUTOINCREMENT, numero INTEGER, ano INTEGER, data TEXT, hora TEXT, local TEXT, pauta TEXT, participantes TEXT, redacao TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS oficios (id INTEGER PRIMARY KEY AUTOINCREMENT, numero INTEGER, ano INTEGER, data TEXT, destinatario TEXT, cargo_destinatario TEXT, orgao_destinatario TEXT, assunto TEXT, forma_tratamento TEXT, redacao TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS bilhetes (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, assunto TEXT, mensagem TEXT, assinante TEXT, autorizacao INTEGER, assinatura INTEGER)")
        cursor.execute("CREATE TABLE IF NOT EXISTS galeria_fotos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cargo TEXT, periodo TEXT, arquivo TEXT, foto_base64 TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS log_acessos (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_nome TEXT, usuario_login TEXT, data_hora TEXT, acao TEXT DEFAULT 'login')")
        # Limpeza automática: apaga registros de acesso/atividade com mais de 12 meses
        cursor.execute("DELETE FROM log_acessos WHERE data_hora < date('now', '-45 days')")
        cursor.execute("""CREATE TABLE IF NOT EXISTS registro_tamanhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER UNIQUE REFERENCES alunos(id) ON DELETE CASCADE,
            calcado TEXT, calca_saia TEXT, camiseta TEXT, blusa TEXT,
            peso TEXT, altura TEXT
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS estoque_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, quantidade INTEGER DEFAULT 0, estoque_minimo INTEGER DEFAULT 0,
            unidade TEXT, categoria TEXT, observacao TEXT,
            excluido INTEGER DEFAULT 0
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS estoque_pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT, itens_json TEXT,
            excluido INTEGER DEFAULT 0
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS estoque_movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER REFERENCES estoque_itens(id) ON DELETE CASCADE,
            tipo TEXT, quantidade INTEGER, data TEXT, observacao TEXT,
            excluido INTEGER DEFAULT 0
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS matriculas_proximo_ano (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER UNIQUE REFERENCES alunos(id) ON DELETE CASCADE,
            turma_destino_id INTEGER REFERENCES turmas(id) ON DELETE SET NULL,
            status TEXT DEFAULT 'pendente', observacao TEXT, excluido INTEGER DEFAULT 0
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS vagas_ano_letivo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turma_id INTEGER UNIQUE REFERENCES turmas(id) ON DELETE CASCADE,
            vagas_totais INTEGER
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS fila_espera (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT, nome TEXT, data_nascimento TEXT, serie TEXT,
            turno_preferencia TEXT, responsavel TEXT, telefone TEXT, data_cadastro TEXT,
            excluido INTEGER DEFAULT 0
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS curso_informatica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_aluno TEXT, serie_turma TEXT,
            disciplina_id INTEGER REFERENCES disciplinas(id) ON DELETE SET NULL,
            dia_semana TEXT, periodo TEXT, horario TEXT, observacao TEXT,
            excluido INTEGER DEFAULT 0
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS turmas_proximo_ano (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serie TEXT, letra TEXT, turno TEXT, nome_completo TEXT, excluido INTEGER DEFAULT 0
        )""")

        # 1.1 Índices para acelerar as consultas mais comuns (idempotente)
        indices = [
            ("idx_alunos_turma_id", "alunos", "turma_id"),
            ("idx_alunos_ativo", "alunos", "ativo"),
            ("idx_alunos_arquivado", "alunos", "arquivado"),
            ("idx_alunos_cgm", "alunos", "cgm"),
            ("idx_frequencia_aluno", "frequencia", "aluno_id"),
            ("idx_frequencia_disciplina", "frequencia", "disciplina_id"),
            ("idx_notas_aluno", "notas", "aluno_id"),
            ("idx_notas_disciplina", "notas", "disciplina_id"),
            ("idx_usuarios_ativo", "usuarios", "ativo"),
            ("idx_turmas_ativo", "turmas", "ativo"),
            ("idx_turmas_professor", "turmas", "professor_id"),
            ("idx_estoque_mov_item", "estoque_movimentacoes", "item_id"),
            ("idx_matriculas_prox_aluno", "matriculas_proximo_ano", "aluno_id"),
            ("idx_vagas_turma", "vagas_ano_letivo", "turma_id"),
        ]
        for nome_idx, tabela, coluna in indices:
            if nome_seguro(nome_idx) and nome_seguro(tabela) and nome_seguro(coluna):
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {nome_idx} ON {tabela}({coluna})")
            else:
                logger.warning("Índice ignorado por nome inválido: %s %s(%s)", nome_idx, tabela, coluna)

        # NOTA SOBRE FOREIGN KEYS: tabelas legadas já criadas sem FK não são
        # recriadas automaticamente para evitar perda/corrupção de dados. As
        # FKs acima só serão aplicadas em bancos novos. A validação é ativada
        # via PRAGMA foreign_keys = ON em get_connection().
        # Na primeira vez, copia as turmas de hoje como ponto de partida pro
        # próximo ano (preservando o MESMO id, pra qualquer matrícula/vaga
        # já cadastrada continuar apontando pro lugar certo). Depois disso,
        # o secretário ajusta livremente na tela "Configurar Turmas".
        ja_tem = cursor.execute("SELECT COUNT(*) FROM turmas_proximo_ano").fetchone()[0]
        if ja_tem == 0:
            turmas_atuais = cursor.execute(
                "SELECT id, nome_completo, turno FROM turmas WHERE ativo=1 AND (tipo IS NULL OR tipo != 'contraturno')"
            ).fetchall()
            for t in turmas_atuais:
                partes = t[1].rsplit(" ", 1)
                serie, letra = (partes[0], partes[1]) if len(partes) == 2 else (t[1], "")
                cursor.execute(
                    "INSERT INTO turmas_proximo_ano (id, serie, letra, turno, nome_completo) VALUES (?,?,?,?,?)",
                    (t[0], serie, letra, t[2], t[1]))

        # 2. Migrações de Colunas
        migracoes = {
            "dados_escola": ["cnpj", "mantenedora", "gemini_api_key", "inep", "endereco", "telefone", "email", "bairro", "rua", "numero", "complemento", "municipio", "cep", "uf", "telefone1", "telefone2", "num_salas", "link_documentacao", "gestao_usuarios_login", "gestao_usuarios_senha", "calendario_base64", "bim1_inicio", "bim1_fim", "bim2_inicio", "bim2_fim", "bim3_inicio", "bim3_fim", "bim4_inicio", "bim4_fim"],
            "turmas": ["nome_completo", "turno", "tipo", "ativo", "professor_id"],
            "professores": ["matricula"],
            "funcionarios": ["matricula"],
            "pedagogas": ["matricula"],
            "log_acessos": ["acao"],
            "matriculas_proximo_ano": ["excluido"],
            "fila_espera": ["excluido"],
            "curso_informatica": ["excluido"],
            "turmas_proximo_ano": ["excluido"],
            "bilhetes": ["excluido"],
            "oficios": ["excluido"],
            "atas": ["excluido"],
            "usuarios": ["excluido"],
            "disciplinas": ["excluido"],
            "galeria_fotos": ["excluido"],
            "estoque_itens": ["excluido"],
            "atestados": ["excluido"],
            "frequencia": ["excluido"],
            "ocorrencias": ["excluido"],
            "secretarios": ["matricula"],
            "diretores": ["matricula"],
            "alunos": [
                "saida_autorizada",
                "cgm", "data_nascimento", "sexo", "cpf", "rg",
                "certidao_nascimento", "municipio_nascimento", "uf_nascimento",
                "nome_mae", "cpf_mae", "telefone_mae",
                "nome_pai", "cpf_pai", "telefone_pai",
                "responsavel", "telefone_responsavel", "email",
                "endereco", "bairro", "cidade", "cep",
                "tipo_ident_geo", "numero_ident_geo",
                "participa_programas_sociais", "qtd_pessoas_residencia",
                "tipos_deficiencia", "necessidades_especiais",
                "turma_id", "turma_contraturno_id", "pasta_documentos", 
                "data_matricula", "observacoes", "alergico", "alergia_descricao",
                "ativo", "arquivado", "data_arquivamento"
            ]
        }
        
        # Inserir resoluções (1-16) se não existirem
        for i in range(1, 17):
            migracoes["dados_escola"].append(f"resolucao_{i}")

        for tabela, colunas in migracoes.items():
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabela,))
            if not cursor.fetchone():
                continue  # tabela ainda não existe neste banco, pula sem travar as outras
            try:
                cursor.execute(f"PRAGMA table_info({tabela})")
                existentes = [row[1] for row in cursor.fetchall()]
            except Exception as e:
                logger.error("Não foi possível ler table_info de %s: %s", tabela, e)
                continue
            for col in colunas:
                if not nome_seguro(col):
                    logger.warning("Nome de coluna inválido ignorado: %s.%s", tabela, col)
                    continue
                if col not in existentes:
                    # Booleanos novos sempre como INTEGER DEFAULT 0;
                    # colunas legadas em TEXT permanecem compatíveis.
                    tipo = "INTEGER DEFAULT 0" if col in ("ativo", "arquivado", "excluido") else "TEXT"
                    try:
                        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {col} {tipo}")
                    except Exception as e:
                        logger.error("Falha ao adicionar coluna %s em %s: %s", col, tabela, e)

        # 3. Ajustes de consistência
        cursor.execute("PRAGMA table_info(turmas)")
        cols_turmas = [row[1] for row in cursor.fetchall()]
        if "nome" in cols_turmas and "nome_completo" in cols_turmas:
            cursor.execute("UPDATE turmas SET nome_completo = nome WHERE nome_completo IS NULL OR nome_completo = ''")
        if "ativo" in cols_turmas:
            cursor.execute("UPDATE turmas SET ativo = 1 WHERE ativo IS NULL")
            
        cursor.execute("PRAGMA table_info(alunos)")
        cols_alunos = [row[1] for row in cursor.fetchall()]
        if "ativo" in cols_alunos:
            cursor.execute("UPDATE alunos SET ativo = 1 WHERE ativo IS NULL")
        if "arquivado" in cols_alunos:
            cursor.execute("UPDATE alunos SET arquivado = 0 WHERE arquivado IS NULL")

        conn.commit()
        conn.close()
    except Exception as e:
        logger.exception("Erro na migração: %s", e)

if __name__ == "__main__":
    migrar_banco()
