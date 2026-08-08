-- ============================================================
-- SQL COMPLETO - gerado automaticamente a partir do banco real
-- Cole tudo isso no SQL Editor do Supabase e clique em RUN.
-- Seguro rodar mais de uma vez (não apaga nenhum dado existente).
-- ============================================================

-- Tabela: alunos
CREATE TABLE IF NOT EXISTS "alunos" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "cgm" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "data_nascimento" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "sexo" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "cpf" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "rg" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "certidao_nascimento" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "municipio_nascimento" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "uf_nascimento" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "nome_mae" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "cpf_mae" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "telefone_mae" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "nome_pai" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "cpf_pai" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "telefone_pai" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "responsavel" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "telefone_responsavel" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "email" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "endereco" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "bairro" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "cidade" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "cep" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "tipo_ident_geo" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "numero_ident_geo" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "participa_programas_sociais" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "qtd_pessoas_residencia" BIGINT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "tipos_deficiencia" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "necessidades_especiais" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "turma_id" BIGINT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "pasta_documentos" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "ativo" BIGINT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "arquivado" BIGINT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "data_arquivamento" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "data_matricula" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "observacoes" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "turma_contraturno_id" BIGINT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "alergico" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "alergia_descricao" TEXT;
ALTER TABLE "alunos" ADD COLUMN IF NOT EXISTS "saida_autorizada" TEXT;
ALTER TABLE "alunos" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "alunos";
CREATE POLICY "acesso_total" ON "alunos" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: matriculas_contraturno
CREATE TABLE IF NOT EXISTS "matriculas_contraturno" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "matriculas_contraturno" ADD COLUMN IF NOT EXISTS "aluno_id" BIGINT;
ALTER TABLE "matriculas_contraturno" ADD COLUMN IF NOT EXISTS "turma_id" BIGINT;
ALTER TABLE "matriculas_contraturno" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "matriculas_contraturno";
CREATE POLICY "acesso_total" ON "matriculas_contraturno" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: turmas
CREATE TABLE IF NOT EXISTS "turmas" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "serie" TEXT;
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "letra" TEXT;
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "turno" TEXT;
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "nome_completo" TEXT;
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "ano_letivo" TEXT;
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "sala" TEXT;
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "capacidade" BIGINT;
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "professor_id" BIGINT;
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "tipo" TEXT;
ALTER TABLE "turmas" ADD COLUMN IF NOT EXISTS "ativo" BIGINT;
ALTER TABLE "turmas" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "turmas";
CREATE POLICY "acesso_total" ON "turmas" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: disciplinas
CREATE TABLE IF NOT EXISTS "disciplinas" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "disciplinas" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "disciplinas" ADD COLUMN IF NOT EXISTS "carga_horaria" BIGINT;
ALTER TABLE "disciplinas" ADD COLUMN IF NOT EXISTS "professor_id" BIGINT;
ALTER TABLE "disciplinas" ADD COLUMN IF NOT EXISTS "turma_id" BIGINT;
ALTER TABLE "disciplinas" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "disciplinas" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "disciplinas";
CREATE POLICY "acesso_total" ON "disciplinas" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: horarios
CREATE TABLE IF NOT EXISTS "horarios" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "horarios" ADD COLUMN IF NOT EXISTS "turma_id" BIGINT;
ALTER TABLE "horarios" ADD COLUMN IF NOT EXISTS "disciplina_id" BIGINT;
ALTER TABLE "horarios" ADD COLUMN IF NOT EXISTS "dia_semana" TEXT;
ALTER TABLE "horarios" ADD COLUMN IF NOT EXISTS "horario_inicio" TEXT;
ALTER TABLE "horarios" ADD COLUMN IF NOT EXISTS "horario_fim" TEXT;
ALTER TABLE "horarios" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "horarios";
CREATE POLICY "acesso_total" ON "horarios" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: notas
CREATE TABLE IF NOT EXISTS "notas" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "notas" ADD COLUMN IF NOT EXISTS "aluno_id" BIGINT;
ALTER TABLE "notas" ADD COLUMN IF NOT EXISTS "disciplina_id" BIGINT;
ALTER TABLE "notas" ADD COLUMN IF NOT EXISTS "bimestre" BIGINT;
ALTER TABLE "notas" ADD COLUMN IF NOT EXISTS "nota_1" DOUBLE PRECISION;
ALTER TABLE "notas" ADD COLUMN IF NOT EXISTS "nota_2" DOUBLE PRECISION;
ALTER TABLE "notas" ADD COLUMN IF NOT EXISTS "nota_recuperacao" DOUBLE PRECISION;
ALTER TABLE "notas" ADD COLUMN IF NOT EXISTS "total_bimestral" DOUBLE PRECISION;
ALTER TABLE "notas" ADD COLUMN IF NOT EXISTS "ano_letivo" TEXT;
ALTER TABLE "notas" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "notas";
CREATE POLICY "acesso_total" ON "notas" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: frequencia
CREATE TABLE IF NOT EXISTS "frequencia" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "frequencia" ADD COLUMN IF NOT EXISTS "aluno_id" BIGINT;
ALTER TABLE "frequencia" ADD COLUMN IF NOT EXISTS "disciplina_id" BIGINT;
ALTER TABLE "frequencia" ADD COLUMN IF NOT EXISTS "data" TEXT;
ALTER TABLE "frequencia" ADD COLUMN IF NOT EXISTS "presente" BIGINT;
ALTER TABLE "frequencia" ADD COLUMN IF NOT EXISTS "justificada" BIGINT;
ALTER TABLE "frequencia" ADD COLUMN IF NOT EXISTS "observacao" TEXT;
ALTER TABLE "frequencia" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "frequencia" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "frequencia";
CREATE POLICY "acesso_total" ON "frequencia" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: ocorrencias
CREATE TABLE IF NOT EXISTS "ocorrencias" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "ocorrencias" ADD COLUMN IF NOT EXISTS "entidade" TEXT;
ALTER TABLE "ocorrencias" ADD COLUMN IF NOT EXISTS "entidade_id" BIGINT;
ALTER TABLE "ocorrencias" ADD COLUMN IF NOT EXISTS "data" TEXT;
ALTER TABLE "ocorrencias" ADD COLUMN IF NOT EXISTS "descricao" TEXT;
ALTER TABLE "ocorrencias" ADD COLUMN IF NOT EXISTS "registrado_por" TEXT;
ALTER TABLE "ocorrencias" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "ocorrencias" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "ocorrencias";
CREATE POLICY "acesso_total" ON "ocorrencias" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: atestados
CREATE TABLE IF NOT EXISTS "atestados" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "atestados" ADD COLUMN IF NOT EXISTS "entidade" TEXT;
ALTER TABLE "atestados" ADD COLUMN IF NOT EXISTS "entidade_id" BIGINT;
ALTER TABLE "atestados" ADD COLUMN IF NOT EXISTS "tipo" TEXT;
ALTER TABLE "atestados" ADD COLUMN IF NOT EXISTS "data" TEXT;
ALTER TABLE "atestados" ADD COLUMN IF NOT EXISTS "duracao" TEXT;
ALTER TABLE "atestados" ADD COLUMN IF NOT EXISTS "unidade_duracao" TEXT;
ALTER TABLE "atestados" ADD COLUMN IF NOT EXISTS "observacao" TEXT;
ALTER TABLE "atestados" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "atestados" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "atestados";
CREATE POLICY "acesso_total" ON "atestados" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: dados_escola
CREATE TABLE IF NOT EXISTS "dados_escola" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "nome_escola" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "inep" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "rua" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "numero" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "complemento" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "municipio" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "cep" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "uf" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "telefone1" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "telefone2" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "num_salas" BIGINT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "link_documentacao" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_1" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_2" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_3" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_4" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_5" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_6" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_7" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_8" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_9" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_10" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_11" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_12" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_13" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_14" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_15" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "resolucao_16" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "gemini_api_key" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "cnpj" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "mantenedora" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "endereco" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "telefone" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "email" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "bairro" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "gestao_usuarios_login" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "gestao_usuarios_senha" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "calendario_base64" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "bim1_inicio" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "bim1_fim" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "bim2_inicio" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "bim2_fim" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "bim3_inicio" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "bim3_fim" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "bim4_inicio" TEXT;
ALTER TABLE "dados_escola" ADD COLUMN IF NOT EXISTS "bim4_fim" TEXT;
ALTER TABLE "dados_escola" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "dados_escola";
CREATE POLICY "acesso_total" ON "dados_escola" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: usuarios
CREATE TABLE IF NOT EXISTS "usuarios" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "usuarios" ADD COLUMN IF NOT EXISTS "login" TEXT;
ALTER TABLE "usuarios" ADD COLUMN IF NOT EXISTS "senha" TEXT;
ALTER TABLE "usuarios" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "usuarios" ADD COLUMN IF NOT EXISTS "perfil" TEXT;
ALTER TABLE "usuarios" ADD COLUMN IF NOT EXISTS "ativo" BIGINT;
ALTER TABLE "usuarios" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "usuarios" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "usuarios";
CREATE POLICY "acesso_total" ON "usuarios" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: professores
CREATE TABLE IF NOT EXISTS "professores" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "cargo" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "rua" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "numero" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "complemento" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "municipio" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "cep" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "uf" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "telefone1" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "telefone2" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "cpf" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "nis" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "cor_raca" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "nome_mae" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "estado_civil" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "instituicao_formacao" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "ano_formacao" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "pos_graduacao" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "outros_cursos" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "situacao_funcional" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "disciplinas" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "email" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "data_admissao" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "pasta_documentos" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "observacoes" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "ativo" BIGINT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "arquivado" BIGINT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "data_arquivamento" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "bairro" TEXT;
ALTER TABLE "professores" ADD COLUMN IF NOT EXISTS "matricula" TEXT;
ALTER TABLE "professores" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "professores";
CREATE POLICY "acesso_total" ON "professores" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: funcionarios
CREATE TABLE IF NOT EXISTS "funcionarios" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "cargo" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "rua" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "numero" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "complemento" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "municipio" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "cep" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "uf" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "telefone1" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "telefone2" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "cpf" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "nis" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "cor_raca" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "nome_mae" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "estado_civil" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "instituicao_formacao" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "ano_formacao" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "pos_graduacao" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "outros_cursos" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "situacao_funcional" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "disciplinas" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "email" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "data_admissao" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "pasta_documentos" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "observacoes" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "ativo" BIGINT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "arquivado" BIGINT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "data_arquivamento" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "bairro" TEXT;
ALTER TABLE "funcionarios" ADD COLUMN IF NOT EXISTS "matricula" TEXT;
ALTER TABLE "funcionarios" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "funcionarios";
CREATE POLICY "acesso_total" ON "funcionarios" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: pedagogas
CREATE TABLE IF NOT EXISTS "pedagogas" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "cargo" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "rua" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "numero" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "complemento" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "municipio" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "cep" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "uf" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "telefone1" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "telefone2" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "cpf" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "nis" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "cor_raca" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "nome_mae" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "estado_civil" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "instituicao_formacao" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "ano_formacao" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "pos_graduacao" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "outros_cursos" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "situacao_funcional" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "disciplinas" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "email" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "data_admissao" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "pasta_documentos" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "observacoes" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "ativo" BIGINT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "arquivado" BIGINT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "data_arquivamento" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "bairro" TEXT;
ALTER TABLE "pedagogas" ADD COLUMN IF NOT EXISTS "matricula" TEXT;
ALTER TABLE "pedagogas" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "pedagogas";
CREATE POLICY "acesso_total" ON "pedagogas" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: secretarios
CREATE TABLE IF NOT EXISTS "secretarios" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "cargo" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "rua" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "numero" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "complemento" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "municipio" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "cep" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "uf" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "telefone1" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "telefone2" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "cpf" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "nis" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "cor_raca" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "nome_mae" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "estado_civil" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "instituicao_formacao" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "ano_formacao" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "pos_graduacao" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "outros_cursos" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "situacao_funcional" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "disciplinas" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "email" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "data_admissao" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "pasta_documentos" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "observacoes" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "ativo" BIGINT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "arquivado" BIGINT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "data_arquivamento" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "bairro" TEXT;
ALTER TABLE "secretarios" ADD COLUMN IF NOT EXISTS "matricula" TEXT;
ALTER TABLE "secretarios" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "secretarios";
CREATE POLICY "acesso_total" ON "secretarios" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: diretores
CREATE TABLE IF NOT EXISTS "diretores" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "cargo" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "rua" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "numero" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "complemento" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "municipio" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "cep" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "uf" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "telefone1" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "telefone2" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "cpf" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "nis" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "cor_raca" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "nome_mae" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "estado_civil" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "instituicao_formacao" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "ano_formacao" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "pos_graduacao" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "outros_cursos" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "situacao_funcional" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "disciplinas" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "email" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "data_admissao" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "pasta_documentos" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "observacoes" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "ativo" BIGINT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "arquivado" BIGINT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "data_arquivamento" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "portaria_nomeacao" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "bairro" TEXT;
ALTER TABLE "diretores" ADD COLUMN IF NOT EXISTS "matricula" TEXT;
ALTER TABLE "diretores" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "diretores";
CREATE POLICY "acesso_total" ON "diretores" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: atas
CREATE TABLE IF NOT EXISTS "atas" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "numero" BIGINT;
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "ano" BIGINT;
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "data" TEXT;
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "hora" TEXT;
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "local" TEXT;
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "pauta" TEXT;
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "participantes" TEXT;
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "redacao" TEXT;
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "criado_em" TEXT;
ALTER TABLE "atas" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "atas" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "atas";
CREATE POLICY "acesso_total" ON "atas" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: oficios
CREATE TABLE IF NOT EXISTS "oficios" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "numero" BIGINT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "ano" BIGINT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "data" TEXT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "destinatario" TEXT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "cargo_destinatario" TEXT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "orgao_destinatario" TEXT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "assunto" TEXT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "forma_tratamento" TEXT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "redacao" TEXT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "criado_em" TEXT;
ALTER TABLE "oficios" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "oficios" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "oficios";
CREATE POLICY "acesso_total" ON "oficios" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: bilhetes
CREATE TABLE IF NOT EXISTS "bilhetes" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "bilhetes" ADD COLUMN IF NOT EXISTS "data" TEXT;
ALTER TABLE "bilhetes" ADD COLUMN IF NOT EXISTS "assunto" TEXT;
ALTER TABLE "bilhetes" ADD COLUMN IF NOT EXISTS "mensagem" TEXT;
ALTER TABLE "bilhetes" ADD COLUMN IF NOT EXISTS "assinante" TEXT;
ALTER TABLE "bilhetes" ADD COLUMN IF NOT EXISTS "autorizacao" BIGINT;
ALTER TABLE "bilhetes" ADD COLUMN IF NOT EXISTS "assinatura" BIGINT;
ALTER TABLE "bilhetes" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "bilhetes" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "bilhetes";
CREATE POLICY "acesso_total" ON "bilhetes" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: galeria_fotos
CREATE TABLE IF NOT EXISTS "galeria_fotos" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "galeria_fotos" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "galeria_fotos" ADD COLUMN IF NOT EXISTS "cargo" TEXT;
ALTER TABLE "galeria_fotos" ADD COLUMN IF NOT EXISTS "periodo" TEXT;
ALTER TABLE "galeria_fotos" ADD COLUMN IF NOT EXISTS "arquivo" TEXT;
ALTER TABLE "galeria_fotos" ADD COLUMN IF NOT EXISTS "foto_base64" TEXT;
ALTER TABLE "galeria_fotos" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "galeria_fotos" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "galeria_fotos";
CREATE POLICY "acesso_total" ON "galeria_fotos" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: log_acessos
CREATE TABLE IF NOT EXISTS "log_acessos" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "log_acessos" ADD COLUMN IF NOT EXISTS "usuario_nome" TEXT;
ALTER TABLE "log_acessos" ADD COLUMN IF NOT EXISTS "usuario_login" TEXT;
ALTER TABLE "log_acessos" ADD COLUMN IF NOT EXISTS "data_hora" TEXT;
ALTER TABLE "log_acessos" ADD COLUMN IF NOT EXISTS "acao" TEXT;
ALTER TABLE "log_acessos" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "log_acessos";
CREATE POLICY "acesso_total" ON "log_acessos" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: registro_tamanhos
CREATE TABLE IF NOT EXISTS "registro_tamanhos" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "registro_tamanhos" ADD COLUMN IF NOT EXISTS "aluno_id" BIGINT;
ALTER TABLE "registro_tamanhos" ADD COLUMN IF NOT EXISTS "calcado" TEXT;
ALTER TABLE "registro_tamanhos" ADD COLUMN IF NOT EXISTS "calca_saia" TEXT;
ALTER TABLE "registro_tamanhos" ADD COLUMN IF NOT EXISTS "camiseta" TEXT;
ALTER TABLE "registro_tamanhos" ADD COLUMN IF NOT EXISTS "blusa" TEXT;
ALTER TABLE "registro_tamanhos" ADD COLUMN IF NOT EXISTS "peso" TEXT;
ALTER TABLE "registro_tamanhos" ADD COLUMN IF NOT EXISTS "altura" TEXT;
ALTER TABLE "registro_tamanhos" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "registro_tamanhos";
CREATE POLICY "acesso_total" ON "registro_tamanhos" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: estoque_itens
CREATE TABLE IF NOT EXISTS "estoque_itens" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "estoque_itens" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "estoque_itens" ADD COLUMN IF NOT EXISTS "quantidade" BIGINT;
ALTER TABLE "estoque_itens" ADD COLUMN IF NOT EXISTS "estoque_minimo" BIGINT;
ALTER TABLE "estoque_itens" ADD COLUMN IF NOT EXISTS "unidade" TEXT;
ALTER TABLE "estoque_itens" ADD COLUMN IF NOT EXISTS "categoria" TEXT;
ALTER TABLE "estoque_itens" ADD COLUMN IF NOT EXISTS "observacao" TEXT;
ALTER TABLE "estoque_itens" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "estoque_itens" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "estoque_itens";
CREATE POLICY "acesso_total" ON "estoque_itens" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: estoque_pedidos
CREATE TABLE IF NOT EXISTS "estoque_pedidos" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "estoque_pedidos" ADD COLUMN IF NOT EXISTS "data" TEXT;
ALTER TABLE "estoque_pedidos" ADD COLUMN IF NOT EXISTS "itens_json" TEXT;
ALTER TABLE "estoque_pedidos" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "estoque_pedidos";
CREATE POLICY "acesso_total" ON "estoque_pedidos" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: estoque_movimentacoes
CREATE TABLE IF NOT EXISTS "estoque_movimentacoes" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "estoque_movimentacoes" ADD COLUMN IF NOT EXISTS "item_id" BIGINT;
ALTER TABLE "estoque_movimentacoes" ADD COLUMN IF NOT EXISTS "tipo" TEXT;
ALTER TABLE "estoque_movimentacoes" ADD COLUMN IF NOT EXISTS "quantidade" BIGINT;
ALTER TABLE "estoque_movimentacoes" ADD COLUMN IF NOT EXISTS "data" TEXT;
ALTER TABLE "estoque_movimentacoes" ADD COLUMN IF NOT EXISTS "observacao" TEXT;
ALTER TABLE "estoque_movimentacoes" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "estoque_movimentacoes";
CREATE POLICY "acesso_total" ON "estoque_movimentacoes" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: matriculas_proximo_ano
CREATE TABLE IF NOT EXISTS "matriculas_proximo_ano" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "matriculas_proximo_ano" ADD COLUMN IF NOT EXISTS "aluno_id" BIGINT;
ALTER TABLE "matriculas_proximo_ano" ADD COLUMN IF NOT EXISTS "turma_destino_id" BIGINT;
ALTER TABLE "matriculas_proximo_ano" ADD COLUMN IF NOT EXISTS "status" TEXT;
ALTER TABLE "matriculas_proximo_ano" ADD COLUMN IF NOT EXISTS "observacao" TEXT;
ALTER TABLE "matriculas_proximo_ano" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "matriculas_proximo_ano" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "matriculas_proximo_ano";
CREATE POLICY "acesso_total" ON "matriculas_proximo_ano" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: vagas_ano_letivo
CREATE TABLE IF NOT EXISTS "vagas_ano_letivo" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "vagas_ano_letivo" ADD COLUMN IF NOT EXISTS "turma_id" BIGINT;
ALTER TABLE "vagas_ano_letivo" ADD COLUMN IF NOT EXISTS "vagas_totais" BIGINT;
ALTER TABLE "vagas_ano_letivo" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "vagas_ano_letivo";
CREATE POLICY "acesso_total" ON "vagas_ano_letivo" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: fila_espera
CREATE TABLE IF NOT EXISTS "fila_espera" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "fila_espera" ADD COLUMN IF NOT EXISTS "cgm" TEXT;
ALTER TABLE "fila_espera" ADD COLUMN IF NOT EXISTS "nome" TEXT;
ALTER TABLE "fila_espera" ADD COLUMN IF NOT EXISTS "data_nascimento" TEXT;
ALTER TABLE "fila_espera" ADD COLUMN IF NOT EXISTS "serie" TEXT;
ALTER TABLE "fila_espera" ADD COLUMN IF NOT EXISTS "turno_preferencia" TEXT;
ALTER TABLE "fila_espera" ADD COLUMN IF NOT EXISTS "responsavel" TEXT;
ALTER TABLE "fila_espera" ADD COLUMN IF NOT EXISTS "telefone" TEXT;
ALTER TABLE "fila_espera" ADD COLUMN IF NOT EXISTS "data_cadastro" TEXT;
ALTER TABLE "fila_espera" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "fila_espera" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "fila_espera";
CREATE POLICY "acesso_total" ON "fila_espera" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: curso_informatica
CREATE TABLE IF NOT EXISTS "curso_informatica" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "curso_informatica" ADD COLUMN IF NOT EXISTS "nome_aluno" TEXT;
ALTER TABLE "curso_informatica" ADD COLUMN IF NOT EXISTS "serie_turma" TEXT;
ALTER TABLE "curso_informatica" ADD COLUMN IF NOT EXISTS "disciplina_id" BIGINT;
ALTER TABLE "curso_informatica" ADD COLUMN IF NOT EXISTS "dia_semana" TEXT;
ALTER TABLE "curso_informatica" ADD COLUMN IF NOT EXISTS "periodo" TEXT;
ALTER TABLE "curso_informatica" ADD COLUMN IF NOT EXISTS "horario" TEXT;
ALTER TABLE "curso_informatica" ADD COLUMN IF NOT EXISTS "observacao" TEXT;
ALTER TABLE "curso_informatica" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "curso_informatica" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "curso_informatica";
CREATE POLICY "acesso_total" ON "curso_informatica" FOR ALL USING (true) WITH CHECK (true);

-- Tabela: turmas_proximo_ano
CREATE TABLE IF NOT EXISTS "turmas_proximo_ano" ("id" BIGINT PRIMARY KEY);
ALTER TABLE "turmas_proximo_ano" ADD COLUMN IF NOT EXISTS "serie" TEXT;
ALTER TABLE "turmas_proximo_ano" ADD COLUMN IF NOT EXISTS "letra" TEXT;
ALTER TABLE "turmas_proximo_ano" ADD COLUMN IF NOT EXISTS "turno" TEXT;
ALTER TABLE "turmas_proximo_ano" ADD COLUMN IF NOT EXISTS "nome_completo" TEXT;
ALTER TABLE "turmas_proximo_ano" ADD COLUMN IF NOT EXISTS "excluido" TEXT;
ALTER TABLE "turmas_proximo_ano" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "acesso_total" ON "turmas_proximo_ano";
CREATE POLICY "acesso_total" ON "turmas_proximo_ano" FOR ALL USING (true) WITH CHECK (true);
