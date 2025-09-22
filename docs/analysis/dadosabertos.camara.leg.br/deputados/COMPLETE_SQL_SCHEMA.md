# COMPLETE SQL SCHEMA - POLITICAL TRANSPARENCY DATA LAKE

## CORE DEPUTY TABLES (FROM DEPUTADOS API)

### Primary Deputy Record
```sql
CREATE TABLE deputies (
    -- Primary identifiers
    id INTEGER PRIMARY KEY,
    uri VARCHAR(255),

    -- Personal identifiers (HAVE)
    cpf CHAR(11) UNIQUE NOT NULL,
    nome_civil VARCHAR(255) NOT NULL,
    nome_eleitoral VARCHAR(255),
    sexo CHAR(1),

    -- Birth information (HAVE)
    data_nascimento DATE,
    data_falecimento DATE,
    uf_nascimento CHAR(2),
    municipio_nascimento VARCHAR(255),

    -- Contact & Social (HAVE - often null)
    email VARCHAR(255),
    url_website VARCHAR(255),
    redes_sociais JSON,

    -- Education & Background (HAVE)
    escolaridade VARCHAR(255),

    -- Current status (HAVE)
    sigla_partido VARCHAR(10),
    sigla_uf CHAR(2),
    id_legislatura INTEGER,
    url_foto VARCHAR(255),
    situacao VARCHAR(100),
    condicao_eleitoral VARCHAR(100),

    -- Office details (HAVE)
    gabinete_nome VARCHAR(255),
    gabinete_predio VARCHAR(100),
    gabinete_sala VARCHAR(50),
    gabinete_andar VARCHAR(50),
    gabinete_telefone VARCHAR(50),
    gabinete_email VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Financial Records
```sql
CREATE TABLE deputy_expenses (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Temporal (HAVE)
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    data_documento DATE,

    -- Document details (HAVE)
    cod_documento INTEGER,
    tipo_documento VARCHAR(100),
    cod_tipo_documento INTEGER,
    num_documento VARCHAR(100),
    url_documento VARCHAR(500), -- PDF link

    -- Financial (HAVE)
    valor_documento DECIMAL(12,2),
    valor_liquido DECIMAL(12,2),
    valor_glosa DECIMAL(12,2),

    -- Vendor (HAVE)
    nome_fornecedor VARCHAR(255),
    cnpj_cpf_fornecedor VARCHAR(14), -- 14 for CNPJ, 11 for CPF

    -- Category (HAVE)
    tipo_despesa VARCHAR(255),

    -- Processing (HAVE)
    num_ressarcimento VARCHAR(100),
    cod_lote INTEGER,
    parcela INTEGER,

    -- Indexes
    INDEX idx_deputy_year (deputy_id, ano),
    INDEX idx_cnpj (cnpj_cpf_fornecedor),
    INDEX idx_value (valor_liquido),
    INDEX idx_date (data_documento)
);
```

### Political Career History
```sql
CREATE TABLE external_mandates (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Position details (HAVE)
    cargo VARCHAR(255),
    sigla_uf CHAR(2),
    municipio VARCHAR(255),

    -- Timeline (HAVE)
    ano_inicio INTEGER,
    ano_fim INTEGER,

    -- Party at election (HAVE)
    sigla_partido_eleicao VARCHAR(10),
    uri_partido_eleicao VARCHAR(255),

    INDEX idx_deputy_timeline (deputy_id, ano_inicio)
);
```

### Committee Memberships
```sql
CREATE TABLE deputy_committees (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Committee details (HAVE)
    id_orgao INTEGER,
    uri_orgao VARCHAR(255),
    sigla_orgao VARCHAR(50),
    nome_orgao TEXT,
    nome_publicacao VARCHAR(255),

    -- Role (HAVE)
    titulo VARCHAR(100), -- Presidente, Titular, Suplente, etc.
    cod_titulo VARCHAR(10),

    -- Timeline (HAVE)
    data_inicio TIMESTAMP,
    data_fim TIMESTAMP,

    INDEX idx_deputy_active (deputy_id, data_fim),
    INDEX idx_committee (id_orgao)
);
```

### Parliamentary Groups
```sql
CREATE TABLE deputy_fronts (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Front details (HAVE)
    id_frente INTEGER,
    uri_frente VARCHAR(255),
    titulo_frente TEXT,
    id_legislatura INTEGER,

    INDEX idx_deputy_fronts (deputy_id),
    INDEX idx_front_members (id_frente)
);
```

### Activities & Events
```sql
CREATE TABLE deputy_events (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Event details (HAVE)
    id_evento INTEGER,
    uri_evento VARCHAR(255),

    -- Timing (HAVE)
    data_hora_inicio TIMESTAMP,
    data_hora_fim TIMESTAMP,

    -- Event info (HAVE)
    situacao VARCHAR(100),
    descricao_tipo VARCHAR(255),
    descricao TEXT,

    -- Location (HAVE)
    local_externo VARCHAR(255),
    local_camara_nome VARCHAR(255),
    local_camara_predio VARCHAR(100),
    local_camara_sala VARCHAR(50),
    local_camara_andar VARCHAR(50),

    -- Media (HAVE)
    url_registro VARCHAR(500), -- YouTube/video link

    INDEX idx_deputy_events (deputy_id, data_hora_inicio)
);
```

### Speeches & Discourse
```sql
CREATE TABLE deputy_speeches (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Timing (HAVE when available)
    data_hora_inicio TIMESTAMP,
    data_hora_fim TIMESTAMP,

    -- Content (HAVE when available)
    tipo_discurso VARCHAR(100),
    transcricao TEXT,

    -- Media links (HAVE when available)
    url_texto VARCHAR(500),
    url_audio VARCHAR(500),
    url_video VARCHAR(500),

    -- Full text search
    FULLTEXT(transcricao),
    INDEX idx_deputy_speeches (deputy_id, data_hora_inicio)
);
```

### Professional Background
```sql
CREATE TABLE deputy_professions (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Registration (HAVE)
    data_hora TIMESTAMP,
    cod_tipo_profissao INTEGER,
    titulo VARCHAR(255),

    INDEX idx_deputy_profession (deputy_id)
);

CREATE TABLE deputy_occupations (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Employment details (HAVE but often null)
    titulo VARCHAR(255),
    entidade VARCHAR(255),
    entidade_uf CHAR(2),
    entidade_pais VARCHAR(100),
    ano_inicio INTEGER,
    ano_fim INTEGER,

    INDEX idx_deputy_employment (deputy_id)
);
```

### Status Changes
```sql
CREATE TABLE deputy_history (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Change details (HAVE)
    data_hora TIMESTAMP,
    id_situacao INTEGER,
    situacao VARCHAR(255),
    descricao TEXT,
    sigla_partido VARCHAR(10),
    sigla_uf CHAR(2),
    id_legislatura INTEGER,

    INDEX idx_deputy_changes (deputy_id, data_hora)
);
```

---

## ENRICHMENT TABLES (FROM EXTERNAL SOURCES)

### Electoral Data (TSE)
```sql
CREATE TABLE electoral_data (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Electoral identifiers (NEED - TSE)
    numero_eleitoral VARCHAR(20),
    titulo_eleitoral VARCHAR(20),
    zona_eleitoral VARCHAR(10),
    secao_eleitoral VARCHAR(10),

    -- Election details (NEED - TSE)
    ano_eleicao INTEGER,
    cargo_candidatura VARCHAR(100),
    numero_candidato VARCHAR(10),
    sigla_partido_candidatura VARCHAR(10),
    coligacao TEXT,

    -- Results (NEED - TSE)
    votos_recebidos INTEGER,
    situacao_candidatura VARCHAR(100),

    -- Campaign finance (NEED - TSE)
    receita_campanha DECIMAL(15,2),
    despesa_campanha DECIMAL(15,2),

    INDEX idx_electoral_year (ano_eleicao),
    INDEX idx_electoral_number (numero_eleitoral)
);
```

### Sanctions & Compliance (Portal Transparência)
```sql
CREATE TABLE sanctions_data (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Sanction details (NEED - Portal Transparência)
    tipo_sancao VARCHAR(255),
    orgao_sancionador VARCHAR(255),
    data_inicio_sancao DATE,
    data_fim_sancao DATE,
    valor_multa DECIMAL(15,2),
    motivo TEXT,
    processo_numero VARCHAR(100),

    -- Status (NEED)
    situacao_sancao VARCHAR(100),
    data_verificacao DATE,

    INDEX idx_sanctions_active (deputy_id, data_fim_sancao)
);

CREATE TABLE nepotism_registry (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Family member details (NEED - Portal Transparência)
    nome_parente VARCHAR(255),
    cpf_parente CHAR(11),
    grau_parentesco VARCHAR(100),
    cargo_parente VARCHAR(255),
    orgao_lotacao VARCHAR(255),
    salario DECIMAL(10,2),
    data_admissao DATE,
    data_exoneracao DATE,

    INDEX idx_nepotism_active (deputy_id, data_exoneracao)
);
```

### Audit Records (TCU)
```sql
CREATE TABLE audit_records (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- TCU process details (NEED - TCU)
    numero_processo VARCHAR(100),
    tipo_processo VARCHAR(100),
    data_autuacao DATE,
    relator VARCHAR(255),

    -- Decision (NEED - TCU)
    decisao TEXT,
    data_decisao DATE,
    valor_debito DECIMAL(15,2),
    valor_multa DECIMAL(15,2),

    -- Status (NEED - TCU)
    situacao_processo VARCHAR(100),

    INDEX idx_audit_process (numero_processo),
    INDEX idx_audit_deputy (deputy_id)
);
```

### Judicial Records (DataJud)
```sql
CREATE TABLE judicial_processes (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Process details (NEED - DataJud)
    numero_processo VARCHAR(100),
    classe_processual VARCHAR(255),
    assunto_principal TEXT,
    data_ajuizamento DATE,

    -- Court details (NEED - DataJud)
    tribunal VARCHAR(100),
    orgao_julgador VARCHAR(255),

    -- Parties (NEED - DataJud)
    polo_ativo TEXT,
    polo_passivo TEXT,

    -- Status (NEED - DataJud)
    situacao_processo VARCHAR(100),
    data_situacao DATE,

    INDEX idx_judicial_number (numero_processo),
    INDEX idx_judicial_deputy (deputy_id)
);
```

---

## PERSONAL INFORMATION TABLES (ADDITIONAL SOURCES)

### Personal Documents & Contacts
```sql
CREATE TABLE personal_documents (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Identity documents (NEED - Various sources)
    rg VARCHAR(20),
    rg_orgao_expedidor VARCHAR(50),
    rg_uf_expedicao CHAR(2),
    rg_data_expedicao DATE,

    -- Driver's license (NEED - DETRAN)
    cnh VARCHAR(20),
    cnh_categoria VARCHAR(10),
    cnh_data_vencimento DATE,

    -- Professional registrations (NEED - Professional councils)
    oab_numero VARCHAR(20),
    oab_uf CHAR(2),
    oab_situacao VARCHAR(50),

    crm_numero VARCHAR(20),
    crm_uf CHAR(2),
    crm_situacao VARCHAR(50),

    -- Other professional IDs
    crea_numero VARCHAR(20),
    crc_numero VARCHAR(20)
);

CREATE TABLE contact_information (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Phone numbers (NEED - Multiple sources)
    telefone_residencial VARCHAR(20),
    telefone_celular VARCHAR(20),
    telefone_comercial VARCHAR(20),
    whatsapp VARCHAR(20),

    -- Addresses (NEED - Electoral registry, Receita)
    endereco_residencial TEXT,
    endereco_cep_residencial CHAR(8),
    endereco_cidade_residencial VARCHAR(255),
    endereco_uf_residencial CHAR(2),

    endereco_comercial TEXT,
    endereco_cep_comercial CHAR(8),
    endereco_cidade_comercial VARCHAR(255),
    endereco_uf_comercial CHAR(2),

    -- Email addresses
    email_pessoal VARCHAR(255),
    email_comercial VARCHAR(255),
    email_campanha VARCHAR(255),

    -- Data quality
    data_verificacao DATE,
    fonte_informacao VARCHAR(100)
);
```

### Family & Relationships
```sql
CREATE TABLE family_data (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Marital status (NEED - Civil registry)
    estado_civil VARCHAR(50),
    nome_conjuge VARCHAR(255),
    cpf_conjuge CHAR(11),
    data_casamento DATE,

    -- Parents (NEED - Civil registry)
    nome_pai VARCHAR(255),
    cpf_pai CHAR(11),
    nome_mae VARCHAR(255),
    cpf_mae CHAR(11),

    -- Children (NEED - Civil registry)
    numero_filhos INTEGER,

    INDEX idx_family_spouse (cpf_conjuge),
    INDEX idx_family_parents (cpf_pai, cpf_mae)
);

CREATE TABLE family_members (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Family member details
    nome VARCHAR(255),
    cpf CHAR(11),
    grau_parentesco VARCHAR(100),
    data_nascimento DATE,

    -- Employment (for nepotism detection)
    empregado_publico BOOLEAN DEFAULT FALSE,
    cargo_publico VARCHAR(255),
    orgao_publico VARCHAR(255),

    INDEX idx_family_cpf (cpf)
);
```

### Financial Information
```sql
CREATE TABLE financial_data (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Bank accounts (NEED - Banking regulation)
    banco_codigo VARCHAR(10),
    banco_nome VARCHAR(255),
    agencia VARCHAR(10),
    conta VARCHAR(20),
    tipo_conta VARCHAR(50),

    -- Assets (NEED - TSE declarations, Receita)
    patrimonio_declarado DECIMAL(15,2),
    ano_declaracao INTEGER,

    -- Business ownership (NEED - Receita Federal)
    empresas_socias JSON, -- Array of CNPJs where deputy is partner

    -- Debts (NEED - SERASA/SPC)
    dividas_pendentes DECIMAL(15,2),
    restricoes_credito BOOLEAN DEFAULT FALSE,

    INDEX idx_financial_year (ano_declaracao)
);
```

### Business Relationships
```sql
CREATE TABLE business_network (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Company details (NEED - Receita Federal)
    cnpj CHAR(14),
    razao_social VARCHAR(255),
    nome_fantasia VARCHAR(255),

    -- Relationship (NEED - Receita Federal)
    tipo_participacao VARCHAR(100), -- Sócio, Administrador, etc.
    percentual_participacao DECIMAL(5,2),
    data_inicio_participacao DATE,
    data_fim_participacao DATE,

    -- Company status (NEED - Receita Federal)
    situacao_empresa VARCHAR(100),
    atividade_principal VARCHAR(255),

    INDEX idx_business_cnpj (cnpj),
    INDEX idx_business_deputy (deputy_id)
);
```

---

## VALIDATION & QUALITY TABLES

### Data Validation Status
```sql
CREATE TABLE validation_status (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Validation flags
    cpf_validado BOOLEAN DEFAULT FALSE,
    cpf_data_validacao DATE,

    cnpj_fornecedores_validados BOOLEAN DEFAULT FALSE,
    cnpj_data_validacao DATE,

    tse_match_confirmado BOOLEAN DEFAULT FALSE,
    tse_data_match DATE,

    portal_transparencia_checked BOOLEAN DEFAULT FALSE,
    portal_data_check DATE,

    tcu_records_checked BOOLEAN DEFAULT FALSE,
    tcu_data_check DATE,

    datajud_checked BOOLEAN DEFAULT FALSE,
    datajud_data_check DATE,

    -- Completeness scores
    dados_completos_percentual DECIMAL(5,2),
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_validation_deputy (deputy_id)
);
```

### Data Sources Log
```sql
CREATE TABLE data_sources_log (
    id SERIAL PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id),

    -- Source tracking
    fonte VARCHAR(100), -- 'DEPUTADOS_API', 'TSE', 'PORTAL_TRANSPARENCIA', etc.
    tabela_destino VARCHAR(100),
    campo VARCHAR(100),

    -- Operation details
    operacao VARCHAR(50), -- 'INSERT', 'UPDATE', 'ENRICH'
    valor_anterior TEXT,
    valor_novo TEXT,

    -- Metadata
    data_operacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_sistema VARCHAR(100),
    confiabilidade_score DECIMAL(3,2), -- 0.00 to 1.00

    INDEX idx_sources_deputy (deputy_id),
    INDEX idx_sources_date (data_operacao)
);
```

---

## PERFORMANCE INDEXES

### Primary Performance Indexes
```sql
-- Core lookup indexes
CREATE INDEX idx_deputies_cpf ON deputies(cpf);
CREATE INDEX idx_deputies_nome ON deputies(nome_civil);
CREATE INDEX idx_deputies_partido_uf ON deputies(sigla_partido, sigla_uf);

-- Financial analysis indexes
CREATE INDEX idx_expenses_timeline ON deputy_expenses(deputy_id, ano, mes);
CREATE INDEX idx_expenses_vendor ON deputy_expenses(cnpj_cpf_fornecedor, valor_liquido);
CREATE INDEX idx_expenses_category ON deputy_expenses(tipo_despesa, valor_liquido);

-- Activity analysis indexes
CREATE INDEX idx_events_activity ON deputy_events(deputy_id, data_hora_inicio);
CREATE INDEX idx_committees_active ON deputy_committees(deputy_id) WHERE data_fim IS NULL;

-- Cross-reference indexes
CREATE INDEX idx_electoral_match ON electoral_data(numero_eleitoral, ano_eleicao);
CREATE INDEX idx_sanctions_lookup ON sanctions_data(deputy_id) WHERE data_fim_sancao IS NULL;

-- Full-text search indexes
CREATE FULLTEXT INDEX idx_speeches_content ON deputy_speeches(transcricao);
CREATE FULLTEXT INDEX idx_sanctions_motivo ON sanctions_data(motivo);
```

---

## VIEWS FOR ANALYSIS

### Complete Deputy Profile
```sql
CREATE VIEW deputy_complete_profile AS
SELECT
    d.*,
    cd.telefone_celular,
    cd.endereco_residencial,
    fd.nome_conjuge,
    vd.dados_completos_percentual
FROM deputies d
LEFT JOIN contact_information cd ON d.id = cd.deputy_id
LEFT JOIN family_data fd ON d.id = fd.deputy_id
LEFT JOIN validation_status vd ON d.id = vd.deputy_id;
```

### Active Sanctions Summary
```sql
CREATE VIEW active_sanctions_summary AS
SELECT
    d.id,
    d.nome_civil,
    COUNT(s.id) as total_sanctions,
    SUM(s.valor_multa) as total_fines
FROM deputies d
LEFT JOIN sanctions_data s ON d.id = s.deputy_id
WHERE s.data_fim_sancao IS NULL OR s.data_fim_sancao > CURRENT_DATE
GROUP BY d.id, d.nome_civil;
```

This schema provides a complete foundation for storing and enriching all political transparency data across multiple sources.