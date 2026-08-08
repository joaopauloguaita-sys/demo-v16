-- ============================================================
-- Script de correção do banco na nuvem (Supabase)
-- Cole tudo isso no SQL Editor do Supabase e clique em RUN.
-- É seguro rodar mais de uma vez (não apaga dados existentes).
-- ============================================================

-- Colunas usadas por Professores, Funcionários, Pedagogas,
-- Secretários e Diretores (mesma ficha para todos)
DO $$
DECLARE
  tabela TEXT;
  colunas TEXT[] := ARRAY[
    'nome','cargo','rua','numero','complemento','municipio','cep','uf',
    'telefone1','telefone2','cpf','nis','cor_raca','nome_mae','estado_civil',
    'instituicao_formacao','ano_formacao','pos_graduacao','outros_cursos',
    'situacao_funcional','disciplinas','email','data_admissao',
    'pasta_documentos','observacoes','ativo','arquivado','data_arquivamento',
    'bairro','telefone','matricula'
  ];
  coluna TEXT;
BEGIN
  FOREACH tabela IN ARRAY ARRAY['professores','funcionarios','pedagogas','secretarios','diretores']
  LOOP
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I (id BIGINT PRIMARY KEY)', tabela);
    FOREACH coluna IN ARRAY colunas
    LOOP
      EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS %I TEXT', tabela, coluna);
    END LOOP;
  END LOOP;

  -- Diretores também tem a portaria de nomeação
  EXECUTE 'ALTER TABLE diretores ADD COLUMN IF NOT EXISTS portaria_nomeacao TEXT';
END $$;

-- Tabela de atestados/declarações
CREATE TABLE IF NOT EXISTS atestados (id BIGINT PRIMARY KEY);
ALTER TABLE atestados ADD COLUMN IF NOT EXISTS entidade TEXT;
ALTER TABLE atestados ADD COLUMN IF NOT EXISTS entidade_id BIGINT;
ALTER TABLE atestados ADD COLUMN IF NOT EXISTS tipo TEXT;
ALTER TABLE atestados ADD COLUMN IF NOT EXISTS data TEXT;
ALTER TABLE atestados ADD COLUMN IF NOT EXISTS duracao TEXT;
ALTER TABLE atestados ADD COLUMN IF NOT EXISTS unidade_duracao TEXT;
ALTER TABLE atestados ADD COLUMN IF NOT EXISTS observacao TEXT;

-- Tabela da Galeria de Fotos (novidade)
CREATE TABLE IF NOT EXISTS galeria_fotos (id BIGINT PRIMARY KEY);
ALTER TABLE galeria_fotos ADD COLUMN IF NOT EXISTS nome TEXT;
ALTER TABLE galeria_fotos ADD COLUMN IF NOT EXISTS cargo TEXT;
ALTER TABLE galeria_fotos ADD COLUMN IF NOT EXISTS periodo TEXT;
ALTER TABLE galeria_fotos ADD COLUMN IF NOT EXISTS arquivo TEXT;
ALTER TABLE galeria_fotos ADD COLUMN IF NOT EXISTS foto_base64 TEXT;

-- Permitir que o app leia/grave nessas tabelas (Row Level Security)
ALTER TABLE pedagogas ENABLE ROW LEVEL SECURITY;
ALTER TABLE secretarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE diretores ENABLE ROW LEVEL SECURITY;
ALTER TABLE atestados ENABLE ROW LEVEL SECURITY;
ALTER TABLE galeria_fotos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "acesso_total" ON pedagogas;
CREATE POLICY "acesso_total" ON pedagogas FOR ALL USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "acesso_total" ON secretarios;
CREATE POLICY "acesso_total" ON secretarios FOR ALL USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "acesso_total" ON diretores;
CREATE POLICY "acesso_total" ON diretores FOR ALL USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "acesso_total" ON atestados;
CREATE POLICY "acesso_total" ON atestados FOR ALL USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "acesso_total" ON galeria_fotos;
CREATE POLICY "acesso_total" ON galeria_fotos FOR ALL USING (true) WITH CHECK (true);

-- Colunas novas em dados_escola (Base de Conhecimento / Gestão de Usuários / Calendário)
ALTER TABLE dados_escola ADD COLUMN IF NOT EXISTS gestao_usuarios_login TEXT;
ALTER TABLE dados_escola ADD COLUMN IF NOT EXISTS gestao_usuarios_senha TEXT;
ALTER TABLE dados_escola ADD COLUMN IF NOT EXISTS calendario_base64 TEXT;
