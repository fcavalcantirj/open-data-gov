# COMPLETE SQL SCHEMA - TSE ELECTORAL DATA LAKE

## CORE TSE TABLES (FROM TSE API)

### Primary Candidate Records
```sql
CREATE TABLE tse_candidates (
    -- Primary identifiers
    sq_candidato BIGINT PRIMARY KEY,
    deputy_id INTEGER REFERENCES deputies(id), -- Link to deputados data

    -- Generation metadata
    dt_geracao DATE,
    hh_geracao TIME,

    -- Election context
    ano_eleicao INTEGER NOT NULL,
    cd_tipo_eleicao INTEGER,
    nm_tipo_eleicao VARCHAR(100),
    nr_turno INTEGER,
    cd_eleicao INTEGER,
    ds_eleicao VARCHAR(255),
    dt_eleicao DATE,
    tp_abrangencia CHAR(1),

    -- Geographic context
    sg_uf CHAR(2) NOT NULL,
    sg_ue VARCHAR(10),
    nm_ue VARCHAR(255),

    -- Position details
    cd_cargo INTEGER,
    ds_cargo VARCHAR(100),

    -- Core identity (CRITICAL FOR CORRELATION)
    nr_candidato VARCHAR(10), -- Electoral number (MISSING from deputados)
    nm_candidato VARCHAR(255) NOT NULL,
    nm_urna_candidato VARCHAR(100),
    nm_social_candidato VARCHAR(255),
    nr_cpf_candidato CHAR(11), -- Primary correlation key
    ds_email VARCHAR(255),

    -- Electoral registration
    nr_titulo_eleitoral_candidato VARCHAR(12),

    -- Candidacy status
    cd_situacao_candidatura INTEGER,
    ds_situacao_candidatura VARCHAR(100),

    -- Party affiliation
    tp_agremiacao VARCHAR(50),
    nr_partido INTEGER,
    sg_partido VARCHAR(10),
    nm_partido VARCHAR(255),

    -- Federation (modern alliance structure)
    nr_federacao INTEGER,
    nm_federacao VARCHAR(255),
    sg_federacao VARCHAR(10),
    ds_composicao_federacao TEXT,

    -- Coalition
    sq_coligacao INTEGER,
    nm_coligacao VARCHAR(255),
    ds_composicao_coligacao TEXT,

    -- Personal information
    sg_uf_nascimento CHAR(2),
    dt_nascimento DATE,
    cd_genero INTEGER,
    ds_genero VARCHAR(20),
    cd_grau_instrucao INTEGER,
    ds_grau_instrucao VARCHAR(100),
    cd_estado_civil INTEGER,
    ds_estado_civil VARCHAR(50),
    cd_cor_raca INTEGER,
    ds_cor_raca VARCHAR(50),
    cd_ocupacao INTEGER,
    ds_ocupacao VARCHAR(255),

    -- Final election status
    cd_sit_tot_turno INTEGER,
    ds_sit_tot_turno VARCHAR(100),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for correlation
    INDEX idx_cpf (nr_cpf_candidato),
    INDEX idx_electoral_number (nr_candidato),
    INDEX idx_name (nm_candidato),
    INDEX idx_year_state (ano_eleicao, sg_uf),
    INDEX idx_party_year (sg_partido, ano_eleicao),
    INDEX idx_deputy_link (deputy_id),

    -- Unique constraint for candidate per election
    UNIQUE KEY uk_candidate_election (nr_cpf_candidato, ano_eleicao, cd_cargo, nr_turno)
);
```

### Asset Declarations
```sql
CREATE TABLE tse_assets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sq_candidato BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Generation metadata
    dt_geracao DATE,
    hh_geracao TIME,

    -- Election context
    ano_eleicao INTEGER NOT NULL,
    cd_tipo_eleicao INTEGER,
    nm_tipo_eleicao VARCHAR(100),
    cd_eleicao INTEGER,
    ds_eleicao VARCHAR(255),
    dt_eleicao DATE,

    -- Geographic context
    sg_uf CHAR(2),
    sg_ue VARCHAR(10),
    nm_ue VARCHAR(255),

    -- Asset details
    nr_ordem_bem_candidato INTEGER,
    cd_tipo_bem_candidato INTEGER,
    ds_tipo_bem_candidato VARCHAR(100),
    ds_bem_candidato TEXT,
    vr_bem_candidato DECIMAL(15,2),

    -- Update tracking
    dt_ult_atual_bem_candidato DATE,
    hh_ult_atual_bem_candidato TIME,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for analysis
    INDEX idx_candidate_year (sq_candidato, ano_eleicao),
    INDEX idx_asset_type (cd_tipo_bem_candidato),
    INDEX idx_asset_value (vr_bem_candidato),
    INDEX idx_year_value (ano_eleicao, vr_bem_candidato)
);
```

### Campaign Finance Data
```sql
CREATE TABLE tse_campaign_finance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sq_candidato BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Transaction details
    ano_eleicao INTEGER NOT NULL,
    tipo_transacao VARCHAR(100), -- 'RECEITA' or 'DESPESA'

    -- Donor/Creditor information
    cnpj_cpf_doador VARCHAR(14),
    nome_doador VARCHAR(255),

    -- Financial details
    valor_transacao DECIMAL(15,2),
    data_transacao DATE,
    descricao_transacao TEXT,

    -- Transaction category
    codigo_especie INTEGER,
    descricao_especie VARCHAR(255),

    -- Geographic context
    sg_uf_doador CHAR(2),
    nm_municipio_doador VARCHAR(255),

    -- Document references
    numero_documento VARCHAR(100),
    tipo_documento VARCHAR(100),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for correlation
    INDEX idx_candidate_finance (sq_candidato, ano_eleicao),
    INDEX idx_cnpj_doador (cnpj_cpf_doador),
    INDEX idx_valor_data (valor_transacao, data_transacao),
    INDEX idx_year_type (ano_eleicao, tipo_transacao)
);
```

### Election Results
```sql
CREATE TABLE tse_election_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sq_candidato BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Election context
    ano_eleicao INTEGER NOT NULL,
    nr_turno INTEGER,
    cd_eleicao INTEGER,

    -- Geographic breakdown
    sg_uf CHAR(2),
    cd_municipio INTEGER,
    nm_municipio VARCHAR(255),
    nr_zona INTEGER,
    nr_secao INTEGER,

    -- Vote counts
    qt_votos_nominais INTEGER,
    qt_votos_legenda INTEGER,
    qt_votos_totais INTEGER,

    -- Position in results
    nr_colocacao INTEGER,
    st_voto_valido BOOLEAN,

    -- Percentages
    perc_votos_validos DECIMAL(8,4),
    perc_votos_nominais DECIMAL(8,4),

    -- Final result
    st_eleito BOOLEAN,
    ds_situacao_candidato VARCHAR(100),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for analysis
    INDEX idx_candidate_results (sq_candidato, ano_eleicao),
    INDEX idx_geographic (sg_uf, cd_municipio, nr_zona),
    INDEX idx_performance (qt_votos_totais, nr_colocacao),
    INDEX idx_elected (st_eleito, ano_eleicao)
);
```

### Coalition Networks
```sql
CREATE TABLE tse_coalitions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- Coalition identity
    sq_coligacao INTEGER,
    nm_coligacao VARCHAR(255),
    ds_composicao_coligacao TEXT,

    -- Election context
    ano_eleicao INTEGER NOT NULL,
    sg_uf CHAR(2),
    cd_cargo INTEGER,

    -- Member parties
    partidos_membros JSON, -- Array of party codes and names

    -- Performance metrics
    total_candidatos INTEGER,
    total_votos INTEGER,
    candidatos_eleitos INTEGER,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_coalition_election (sq_coligacao, ano_eleicao),
    INDEX idx_state_year (sg_uf, ano_eleicao),
    INDEX idx_performance (total_votos, candidatos_eleitos)
);
```

### Party Federation Data
```sql
CREATE TABLE tse_federations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- Federation identity
    nr_federacao INTEGER,
    nm_federacao VARCHAR(255),
    sg_federacao VARCHAR(10),
    ds_composicao_federacao TEXT,

    -- Election context
    ano_eleicao INTEGER NOT NULL,
    sg_uf CHAR(2),

    -- Member parties
    partidos_federados JSON, -- Array of federated parties

    -- Registration details
    dt_registro DATE,
    dt_dissolucao DATE,

    -- Performance
    total_candidatos INTEGER,
    total_votos INTEGER,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_federation_year (nr_federacao, ano_eleicao),
    INDEX idx_active_federations (dt_registro, dt_dissolucao)
);
```

---

## ENRICHMENT TABLES (FROM EXTERNAL SOURCES)

### Voter Registration Data
```sql
CREATE TABLE tse_voter_registry (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- Voter identification
    nr_titulo_eleitoral VARCHAR(12) UNIQUE,
    cpf_eleitor CHAR(11),
    nm_eleitor VARCHAR(255),

    -- Registration details
    sg_uf_domicilio CHAR(2),
    cd_municipio_domicilio INTEGER,
    nm_municipio_domicilio VARCHAR(255),
    nr_zona_eleitoral INTEGER,
    nr_secao_eleitoral INTEGER,

    -- Status
    cd_situacao_eleitor INTEGER,
    ds_situacao_eleitor VARCHAR(100),
    dt_ultima_atualizacao DATE,

    -- Demographics
    dt_nascimento DATE,
    cd_genero INTEGER,
    cd_grau_instrucao INTEGER,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_cpf_eleitor (cpf_eleitor),
    INDEX idx_titulo (nr_titulo_eleitoral),
    INDEX idx_domicilio (sg_uf_domicilio, cd_municipio_domicilio),
    INDEX idx_zona_secao (nr_zona_eleitoral, nr_secao_eleitoral)
);
```

### Candidate Criminal Records
```sql
CREATE TABLE tse_criminal_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sq_candidato BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Criminal record details (NEED - Police databases)
    tipo_certidao VARCHAR(100),
    orgao_emissor VARCHAR(255),
    dt_emissao DATE,
    dt_validade DATE,

    -- Record content
    possui_antecedentes BOOLEAN,
    detalhes_antecedentes TEXT,
    processos_pendentes INTEGER,

    -- Geographic jurisdiction
    sg_uf_jurisdicao CHAR(2),

    -- Verification
    hash_documento VARCHAR(255),
    verificado BOOLEAN DEFAULT FALSE,
    dt_verificacao DATE,

    INDEX idx_candidate_records (sq_candidato),
    INDEX idx_antecedentes (possui_antecedentes)
);
```

### Property and Asset Verification
```sql
CREATE TABLE tse_asset_verification (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asset_id BIGINT REFERENCES tse_assets(id),
    sq_candidato BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Property details (NEED - Property registries)
    numero_registro_imovel VARCHAR(100),
    cartorio_registro VARCHAR(255),
    endereco_completo TEXT,
    area_imovel DECIMAL(10,2),
    valor_venal DECIMAL(15,2),
    valor_mercado DECIMAL(15,2),

    -- Vehicle details (NEED - DETRAN)
    placa_veiculo VARCHAR(10),
    chassi_veiculo VARCHAR(50),
    modelo_veiculo VARCHAR(100),
    ano_fabricacao INTEGER,
    valor_fipe DECIMAL(12,2),

    -- Financial assets (NEED - CVM, BACEN)
    instituicao_financeira VARCHAR(255),
    tipo_investimento VARCHAR(100),
    valor_atual DECIMAL(15,2),
    data_avaliacao DATE,

    -- Verification status
    status_verificacao VARCHAR(50),
    dt_verificacao DATE,
    fonte_verificacao VARCHAR(100),

    INDEX idx_candidate_verification (sq_candidato),
    INDEX idx_asset_link (asset_id),
    INDEX idx_property_value (valor_mercado),
    INDEX idx_verification_status (status_verificacao)
);
```

---

## CORRELATION TABLES (CROSS-SYSTEM INTEGRATION)

### TSE-Deputados Correlation
```sql
CREATE TABLE tse_deputados_correlation (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- Keys
    deputy_id INTEGER REFERENCES deputies(id),
    sq_candidato BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Correlation metadata
    cpf_match BOOLEAN DEFAULT FALSE,
    name_match_score DECIMAL(3,2), -- 0.00 to 1.00
    party_consistent BOOLEAN DEFAULT FALSE,
    state_consistent BOOLEAN DEFAULT FALSE,

    -- Timeline correlation
    eleicao_ano INTEGER,
    mandate_start DATE,
    mandate_end DATE,

    -- Validation flags
    electoral_number_filled BOOLEAN DEFAULT FALSE,
    asset_progression_linked BOOLEAN DEFAULT FALSE,
    campaign_finance_linked BOOLEAN DEFAULT FALSE,

    -- Confidence scoring
    correlation_confidence DECIMAL(3,2), -- Overall match confidence
    validation_status VARCHAR(50),
    dt_last_validation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    UNIQUE KEY uk_deputy_candidate (deputy_id, sq_candidato),
    INDEX idx_correlation_confidence (correlation_confidence),
    INDEX idx_validation_status (validation_status)
);
```

### Campaign Finance Risk Matrix
```sql
CREATE TABLE tse_finance_risk_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sq_candidato BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Risk calculations
    total_receitas DECIMAL(15,2),
    total_despesas DECIMAL(15,2),
    numero_doadores INTEGER,
    numero_cnpjs_doadores INTEGER,

    -- Sanction correlations
    doadores_sancionados INTEGER,
    valor_doadores_sancionados DECIMAL(15,2),
    percentual_risco DECIMAL(5,2),

    -- Vendor correlations (with deputados expenses)
    cnpjs_fornecedores_comum INTEGER,
    valor_fornecedores_comum DECIMAL(15,2),

    -- Risk flags
    risco_alto BOOLEAN DEFAULT FALSE,
    risco_medio BOOLEAN DEFAULT FALSE,
    requer_investigacao BOOLEAN DEFAULT FALSE,

    -- Analysis metadata
    dt_analise TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    algoritmo_versao VARCHAR(20),

    INDEX idx_candidate_risk (sq_candidato),
    INDEX idx_risk_level (risco_alto, risco_medio),
    INDEX idx_investigation_flag (requer_investigacao)
);
```

### Electoral Performance Analysis
```sql
CREATE TABLE tse_performance_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sq_candidato BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Electoral strength
    ano_eleicao INTEGER,
    total_votos INTEGER,
    posicao_ranking INTEGER,
    percentual_votos DECIMAL(8,4),

    -- Geographic performance
    municipios_votacao INTEGER,
    zonas_votacao INTEGER,
    concentracao_geografica DECIMAL(5,2), -- % votes in top municipality

    -- Comparative analysis
    media_votos_cargo DECIMAL(12,2),
    percentil_performance INTEGER, -- 1-100

    -- Trend analysis
    crescimento_vs_eleicao_anterior DECIMAL(8,4),
    estabilidade_eleitoral DECIMAL(3,2), -- consistency score

    -- Network influence
    votos_coligacao INTEGER,
    contribuicao_coligacao DECIMAL(5,2), -- % of coalition votes

    -- Metadata
    dt_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_candidate_performance (sq_candidato, ano_eleicao),
    INDEX idx_vote_ranking (total_votos, posicao_ranking),
    INDEX idx_percentile (percentil_performance)
);
```

---

## ADVANCED ANALYSIS TABLES

### Wealth Progression Tracking
```sql
CREATE TABLE tse_wealth_progression (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sq_candidato BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Wealth timeline
    ano_referencia INTEGER,
    valor_total_bens DECIMAL(15,2),
    numero_bens INTEGER,

    -- Asset categories
    valor_imoveis DECIMAL(15,2),
    valor_veiculos DECIMAL(15,2),
    valor_investimentos DECIMAL(15,2),
    valor_outros DECIMAL(15,2),

    -- Growth analysis
    crescimento_absoluto DECIMAL(15,2),
    crescimento_percentual DECIMAL(8,4),
    crescimento_anualizado DECIMAL(8,4),

    -- Risk indicators
    crescimento_suspeito BOOLEAN DEFAULT FALSE,
    justificativa_crescimento TEXT,
    fonte_renda_declarada VARCHAR(255),

    -- Comparative metrics
    media_crescimento_cargo DECIMAL(8,4),
    percentil_riqueza INTEGER,

    -- Metadata
    dt_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_candidate_wealth (sq_candidato, ano_referencia),
    INDEX idx_growth_analysis (crescimento_percentual, crescimento_suspeito),
    INDEX idx_wealth_percentile (percentil_riqueza)
);
```

### Political Network Analysis
```sql
CREATE TABLE tse_political_networks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- Network nodes
    sq_candidato_origem BIGINT REFERENCES tse_candidates(sq_candidato),
    sq_candidato_destino BIGINT REFERENCES tse_candidates(sq_candidato),

    -- Connection types
    tipo_conexao VARCHAR(100), -- 'COLIGACAO', 'FEDERACAO', 'PARTIDO', 'FINANCIADOR'
    ano_eleicao INTEGER,
    intensidade_conexao DECIMAL(3,2), -- 0.00 to 1.00

    -- Connection details
    descricao_conexao TEXT,
    valor_conexao DECIMAL(15,2), -- when financial
    duracao_conexao INTEGER, -- in years

    -- Network metrics
    centralidade_origem DECIMAL(8,6),
    centralidade_destino DECIMAL(8,6),
    clustering_coefficient DECIMAL(8,6),

    -- Metadata
    dt_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_network_origin (sq_candidato_origem, ano_eleicao),
    INDEX idx_network_destination (sq_candidato_destino, tipo_conexao),
    INDEX idx_connection_strength (intensidade_conexao, valor_conexao)
);
```

---

## PERFORMANCE INDEXES AND VIEWS

### Critical Performance Indexes
```sql
-- Core correlation indexes
CREATE INDEX idx_tse_cpf_year ON tse_candidates(nr_cpf_candidato, ano_eleicao);
CREATE INDEX idx_tse_electoral_number ON tse_candidates(nr_candidato) WHERE nr_candidato IS NOT NULL;
CREATE INDEX idx_tse_name_fuzzy ON tse_candidates(nm_candidato(50), sg_uf, ano_eleicao);

-- Financial analysis indexes
CREATE INDEX idx_assets_progression ON tse_assets(sq_candidato, ano_eleicao, vr_bem_candidato);
CREATE INDEX idx_finance_cnpj ON tse_campaign_finance(cnpj_cpf_doador, valor_transacao);
CREATE INDEX idx_wealth_growth ON tse_wealth_progression(crescimento_percentual, crescimento_suspeito);

-- Performance analysis indexes
CREATE INDEX idx_electoral_performance ON tse_election_results(sq_candidato, qt_votos_totais, st_eleito);
CREATE INDEX idx_coalition_analysis ON tse_coalitions(ano_eleicao, sg_uf, total_votos);

-- Cross-system correlation indexes
CREATE INDEX idx_correlation_lookup ON tse_deputados_correlation(deputy_id, correlation_confidence);
CREATE INDEX idx_risk_assessment ON tse_finance_risk_analysis(sq_candidato, percentual_risco);
```

### Essential Analysis Views
```sql
-- Complete candidate profile with correlation
CREATE VIEW tse_complete_candidate_profile AS
SELECT
    tc.sq_candidato,
    tc.nr_cpf_candidato,
    tc.nr_candidato as electoral_number,
    tc.nm_candidato,
    tc.ano_eleicao,
    tc.sg_partido,
    tc.sg_uf,
    tdc.deputy_id,
    tdc.correlation_confidence,
    wp.valor_total_bens,
    wp.crescimento_percentual,
    fra.percentual_risco,
    pm.percentil_performance
FROM tse_candidates tc
LEFT JOIN tse_deputados_correlation tdc ON tc.sq_candidato = tdc.sq_candidato
LEFT JOIN tse_wealth_progression wp ON tc.sq_candidato = wp.sq_candidato
LEFT JOIN tse_finance_risk_analysis fra ON tc.sq_candidato = fra.sq_candidato
LEFT JOIN tse_performance_metrics pm ON tc.sq_candidato = pm.sq_candidato;

-- Wealth progression red flags
CREATE VIEW tse_wealth_red_flags AS
SELECT
    tc.nr_cpf_candidato,
    tc.nm_candidato,
    wp.ano_referencia,
    wp.valor_total_bens,
    wp.crescimento_percentual,
    wp.crescimento_suspeito,
    fra.percentual_risco
FROM tse_candidates tc
JOIN tse_wealth_progression wp ON tc.sq_candidato = wp.sq_candidato
LEFT JOIN tse_finance_risk_analysis fra ON tc.sq_candidato = fra.sq_candidato
WHERE wp.crescimento_suspeito = TRUE
   OR wp.crescimento_percentual > 100.0
   OR fra.percentual_risco > 50.0;

-- Campaign finance networks
CREATE VIEW tse_campaign_finance_networks AS
SELECT
    tc.nr_cpf_candidato,
    tc.nm_candidato,
    tc.ano_eleicao,
    COUNT(tcf.cnpj_cpf_doador) as total_doadores,
    SUM(tcf.valor_transacao) as total_doacoes,
    COUNT(CASE WHEN s.id IS NOT NULL THEN 1 END) as doadores_sancionados,
    fra.percentual_risco
FROM tse_candidates tc
LEFT JOIN tse_campaign_finance tcf ON tc.sq_candidato = tcf.sq_candidato
LEFT JOIN sanctions_data s ON tcf.cnpj_cpf_doador = s.cnpj
LEFT JOIN tse_finance_risk_analysis fra ON tc.sq_candidato = fra.sq_candidato
GROUP BY tc.sq_candidato, tc.nr_cpf_candidato, tc.nm_candidato, tc.ano_eleicao, fra.percentual_risco;

-- Electoral performance timeline
CREATE VIEW tse_electoral_timeline AS
SELECT
    tc.nr_cpf_candidato,
    tc.nm_candidato,
    tc.ano_eleicao,
    tc.sg_partido,
    ter.qt_votos_totais,
    ter.st_eleito,
    pm.percentil_performance,
    LAG(ter.qt_votos_totais) OVER (
        PARTITION BY tc.nr_cpf_candidato
        ORDER BY tc.ano_eleicao
    ) as votos_eleicao_anterior
FROM tse_candidates tc
LEFT JOIN tse_election_results ter ON tc.sq_candidato = ter.sq_candidato
LEFT JOIN tse_performance_metrics pm ON tc.sq_candidato = pm.sq_candidato
ORDER BY tc.nr_cpf_candidato, tc.ano_eleicao;
```

---

## DATA INTEGRATION PROCEDURES

### TSE-Deputados Correlation Procedure
```sql
DELIMITER //
CREATE PROCEDURE CorrelateTSEDeputados()
BEGIN
    -- Clear existing correlations
    DELETE FROM tse_deputados_correlation;

    -- Perfect CPF matches
    INSERT INTO tse_deputados_correlation (
        deputy_id, sq_candidato, cpf_match, name_match_score,
        party_consistent, state_consistent, correlation_confidence
    )
    SELECT
        d.id,
        tc.sq_candidato,
        TRUE as cpf_match,
        CASE
            WHEN UPPER(d.nome_civil) = UPPER(tc.nm_candidato) THEN 1.00
            ELSE 0.80
        END as name_match_score,
        CASE WHEN d.sigla_partido = tc.sg_partido THEN TRUE ELSE FALSE END,
        CASE WHEN d.sigla_uf = tc.sg_uf THEN TRUE ELSE FALSE END,
        0.95 as correlation_confidence
    FROM deputies d
    JOIN tse_candidates tc ON d.cpf = tc.nr_cpf_candidato
    WHERE tc.ds_cargo = 'DEPUTADO FEDERAL'
    AND tc.ano_eleicao >= 2010;

    -- Update electoral numbers in deputados table
    UPDATE deputies d
    JOIN tse_deputados_correlation tdc ON d.id = tdc.deputy_id
    JOIN tse_candidates tc ON tdc.sq_candidato = tc.sq_candidato
    SET d.numero_eleitoral = tc.nr_candidato
    WHERE tdc.correlation_confidence >= 0.90
    AND tc.ano_eleicao = (
        SELECT MAX(ano_eleicao)
        FROM tse_candidates tc2
        WHERE tc2.sq_candidato = tc.sq_candidato
    );
END //
DELIMITER ;
```

This comprehensive SQL schema provides the complete foundation for storing and analyzing all TSE electoral data with full cross-system correlation capabilities.