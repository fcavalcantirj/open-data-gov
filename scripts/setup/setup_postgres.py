#!/usr/bin/env python3
"""
PostgreSQL Setup Script for Brazilian Political Transparency Data Lake
Creates all 9 unified schema tables for complete data integration
"""

import psycopg2
import psycopg2.extras
import os
from datetime import datetime

def create_unified_postgres_database():
    """
    Create the complete unified political transparency database in PostgreSQL
    with all 9 tables from the validated schema.
    """

    postgres_url = os.getenv('POSTGRES_POOL_URL')
    if not postgres_url:
        raise Exception("POSTGRES_POOL_URL environment variable not set")

    print(f"🐘 Connecting to PostgreSQL database...")
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()

    print("Creating unified schema tables...")

    # Table 1: Unified Politicians (Core Entity) - PostgreSQL version
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unified_politicians (
        id SERIAL PRIMARY KEY,

        -- UNIVERSAL IDENTIFIERS (Perfect Correlation Keys)
        cpf CHAR(11) UNIQUE NOT NULL, -- Universal person identifier - from deputados.cpf ↔ tse_candidates.nr_cpf_candidato
        nome_civil VARCHAR(255) NOT NULL, -- Legal name - from deputados.nome_civil ↔ tse_candidates.nm_candidato
        nome_completo_normalizado VARCHAR(255), -- Normalized name for fuzzy matching - calculated field

        -- SOURCE SYSTEM LINKS
        deputy_id INTEGER, -- Link to deputados.id - when deputy_active=TRUE
        sq_candidato_current BIGINT, -- Most recent TSE candidate record - from tse_candidates.sq_candidato
        deputy_active BOOLEAN DEFAULT FALSE, -- Currently serving deputy - derived from deputados.situacao

        -- DEPUTADOS CORE IDENTITY DATA
        nome_eleitoral VARCHAR(255), -- Electoral name - from deputados.nome_eleitoral
        url_foto VARCHAR(255), -- Photo URL - from deputados.url_foto
        data_falecimento DATE, -- Death date - from deputados.data_falecimento

        -- TSE CORE IDENTITY DATA
        electoral_number VARCHAR(20), -- Electoral number - from tse_candidates.nr_candidato (FILLS DEPUTADOS GAP)
        nr_titulo_eleitoral VARCHAR(12), -- Voter registration - from tse_candidates.nr_titulo_eleitoral_candidato
        nome_urna_candidato VARCHAR(100), -- Ballot name - from tse_candidates.nm_urna_candidato
        nome_social_candidato VARCHAR(255), -- Social name - from tse_candidates.nm_social_candidato

        -- CURRENT POLITICAL STATUS (Deputados Primary)
        current_party VARCHAR(20), -- Current party abbreviation - from deputados.sigla_partido
        current_state VARCHAR(10), -- Current state - from deputados.sigla_uf
        current_legislature INTEGER, -- Current legislature - from deputados.id_legislatura
        situacao VARCHAR(100), -- Deputy status - from deputados.situacao
        condicao_eleitoral VARCHAR(100), -- Electoral condition - from deputados.condicao_eleitoral

        -- TSE POLITICAL DETAILS (Complete Set)
        nr_partido INTEGER, -- Party number - from tse_candidates.nr_partido
        nm_partido VARCHAR(255), -- Full party name - from tse_candidates.nm_partido
        nr_federacao INTEGER, -- Federation number - from tse_candidates.nr_federacao
        sg_federacao VARCHAR(20), -- Federation abbreviation - from tse_candidates.sg_federacao
        current_position VARCHAR(100), -- Current position - from tse_candidates.ds_cargo

        -- TSE ELECTORAL STATUS (Critical for Election Analysis)
        cd_situacao_candidatura INTEGER, -- Candidacy status code - from tse_candidates.cd_situacao_candidatura
        ds_situacao_candidatura VARCHAR(100), -- Candidacy status description - from tse_candidates.ds_situacao_candidatura
        cd_sit_tot_turno INTEGER, -- Final election result code - from tse_candidates.cd_sit_tot_turno
        ds_sit_tot_turno VARCHAR(100), -- Final election result description - from tse_candidates.ds_sit_tot_turno

        -- DEMOGRAPHICS (TSE Primary, Deputados Secondary)
        birth_date DATE, -- Birth date - from deputados.data_nascimento ↔ tse_candidates.dt_nascimento
        birth_state VARCHAR(10), -- Birth state - from deputados.uf_nascimento ↔ tse_candidates.sg_uf_nascimento
        birth_municipality VARCHAR(255), -- Birth municipality - from deputados.municipio_nascimento

        gender VARCHAR(20), -- Gender description - from deputados.sexo ↔ tse_candidates.ds_genero
        gender_code INTEGER, -- Gender code - from tse_candidates.cd_genero

        education_level VARCHAR(100), -- Education description - from deputados.escolaridade ↔ tse_candidates.ds_grau_instrucao
        education_code INTEGER, -- Education code - from tse_candidates.cd_grau_instrucao

        occupation VARCHAR(255), -- Occupation description - from tse_candidates.ds_ocupacao
        occupation_code INTEGER, -- Occupation code - from tse_candidates.cd_ocupacao

        marital_status VARCHAR(50), -- Marital status description - from tse_candidates.ds_estado_civil
        marital_status_code INTEGER, -- Marital status code - from tse_candidates.cd_estado_civil

        race_color VARCHAR(50), -- Race/color description - from tse_candidates.ds_cor_raca
        race_color_code INTEGER, -- Race/color code - from tse_candidates.cd_cor_raca

        -- GEOGRAPHIC DETAILS (Both Sources)
        sg_ue VARCHAR(20), -- Electoral unit code - from tse_candidates.sg_ue
        nm_ue VARCHAR(255), -- Electoral unit name - from tse_candidates.nm_ue

        -- CONTACT INFORMATION (Deputados Primary)
        email VARCHAR(255), -- Email address - from deputados.email ↔ tse_candidates.ds_email
        phone VARCHAR(50), -- Phone number - from deputados.gabinete_telefone
        website VARCHAR(255), -- Personal website - from deputados.url_website
        social_networks JSONB, -- Social media links - from deputados.redes_sociais

        -- OFFICE DETAILS (Deputados Only)
        office_building VARCHAR(100), -- Office building - from deputados.gabinete_predio
        office_room VARCHAR(50), -- Office room - from deputados.gabinete_sala
        office_floor VARCHAR(50), -- Office floor - from deputados.gabinete_andar
        office_phone VARCHAR(50), -- Office phone - from deputados.gabinete_telefone
        office_email VARCHAR(255), -- Office email - from deputados.gabinete_email

        -- CAREER TIMELINE (Calculated from Multiple Sources - Basic Aggregation Only)
        first_election_year INTEGER, -- First election participation - MIN(tse_candidates.ano_eleicao)
        last_election_year INTEGER, -- Most recent election - MAX(tse_candidates.ano_eleicao)
        total_elections INTEGER, -- Total elections participated - COUNT(tse_candidates)
        first_mandate_year INTEGER, -- First elected mandate - MIN(external_mandates.ano_inicio)

        -- DATA VALIDATION FLAGS (Basic Status Only)
        cpf_validated BOOLEAN DEFAULT FALSE, -- CPF cross-validated between systems
        tse_linked BOOLEAN DEFAULT FALSE, -- Has successful TSE correlation
        last_updated_date DATE, -- Last data update timestamp

        -- METADATA
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✓ Created unified_politicians table")

    # Table 2: Unified Financial Records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unified_financial_records (
        id SERIAL PRIMARY KEY,
        politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,

        -- SOURCE IDENTIFICATION
        source_system VARCHAR(20) NOT NULL, -- DEPUTADOS, TSE - source system identifier
        source_record_id VARCHAR(50), -- Original record ID
        source_url VARCHAR(500), -- Document URL

        -- TRANSACTION CLASSIFICATION
        transaction_type VARCHAR(50) NOT NULL, -- PARLIAMENTARY_EXPENSE, CAMPAIGN_DONATION, CAMPAIGN_EXPENSE_CONTRACTED, CAMPAIGN_EXPENSE_PAID, CAMPAIGN_DONATION_ORIGINAL
        transaction_category VARCHAR(255), -- Category description

        -- FINANCIAL DETAILS (Raw Values Only - No Calculations)
        amount DECIMAL(15,2) NOT NULL, -- Transaction amount
        amount_net DECIMAL(15,2), -- Net amount after deductions
        amount_rejected DECIMAL(15,2) DEFAULT 0, -- Rejected/returned amount
        original_amount DECIMAL(15,2), -- Original document amount

        -- TEMPORAL DETAILS
        transaction_date DATE NOT NULL, -- Transaction date
        year INTEGER NOT NULL, -- Transaction year
        month INTEGER, -- Transaction month

        -- COUNTERPART INFORMATION
        counterpart_name VARCHAR(255), -- Vendor/donor name
        counterpart_cnpj_cpf VARCHAR(14), -- CNPJ/CPF
        counterpart_type VARCHAR(50), -- VENDOR, DONOR, INDIVIDUAL, COMPANY
        counterpart_cnae VARCHAR(20), -- CNAE business classification code
        counterpart_business_type VARCHAR(100), -- Business type classification

        -- GEOGRAPHIC CONTEXT
        state VARCHAR(10), -- Transaction state
        municipality VARCHAR(255), -- Transaction municipality

        -- DOCUMENT REFERENCES
        document_number VARCHAR(100), -- Document number
        document_code INTEGER, -- Document code
        document_type VARCHAR(100), -- Document type
        document_type_code INTEGER, -- Document type code
        document_url VARCHAR(500), -- PDF/document link

        -- PROCESSING DETAILS
        lote_code INTEGER, -- Batch code
        installment INTEGER, -- Installment number
        reimbursement_number VARCHAR(100), -- Reimbursement number

        -- ELECTION CONTEXT
        election_year INTEGER, -- Related election year
        election_round INTEGER, -- Election round
        election_date DATE, -- Election date

        -- VALIDATION FLAGS
        cnpj_validated BOOLEAN DEFAULT FALSE, -- CNPJ format validated
        sanctions_checked BOOLEAN DEFAULT FALSE, -- External sanctions checked
        external_validation_date DATE, -- Last external validation check

        -- METADATA
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✓ Created unified_financial_records table")

    # Table 3: Financial Counterparts Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_counterparts (
        id SERIAL PRIMARY KEY,

        -- IDENTITY
        cnpj_cpf VARCHAR(14) UNIQUE NOT NULL, -- CNPJ or CPF identifier
        name VARCHAR(255) NOT NULL, -- Legal/trade name
        normalized_name VARCHAR(255), -- Normalized name for matching
        entity_type VARCHAR(20) NOT NULL, -- COMPANY, INDIVIDUAL, NGO, GOVERNMENT

        -- COMPANY DETAILS
        trade_name VARCHAR(255), -- Trade/fantasy name
        business_sector VARCHAR(100), -- Primary business sector
        company_size VARCHAR(20), -- MICRO, SMALL, MEDIUM, LARGE
        registration_status VARCHAR(50), -- Active, inactive, suspended

        -- GEOGRAPHIC INFORMATION
        state VARCHAR(10), -- Primary state
        municipality VARCHAR(255), -- Primary municipality

        -- TRANSACTION SUMMARY
        total_transaction_amount DECIMAL(15,2) DEFAULT 0, -- Total transaction volume
        transaction_count INTEGER DEFAULT 0, -- Number of transactions
        politician_count INTEGER DEFAULT 0, -- Number of politicians involved
        first_transaction_date DATE, -- First transaction date
        last_transaction_date DATE, -- Most recent transaction date

        -- EXTERNAL VALIDATION FLAGS
        cnpj_validated BOOLEAN DEFAULT FALSE, -- CNPJ validated
        sanctions_checked BOOLEAN DEFAULT FALSE, -- Sanctions checked
        last_validation DATE, -- Last validation date

        -- METADATA
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✓ Created financial_counterparts table")

    # Table 4: Unified Electoral Records (NEW - Electoral Outcome Data)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unified_electoral_records (
        id SERIAL PRIMARY KEY,
        politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,

        -- SOURCE IDENTIFICATION
        source_system VARCHAR(20) NOT NULL DEFAULT 'TSE', -- TSE (primary source for electoral data)
        source_record_id VARCHAR(50), -- Original TSE record ID (SQ_CANDIDATO)
        source_url VARCHAR(500), -- TSE data package URL

        -- ELECTION CONTEXT
        election_year INTEGER NOT NULL, -- Election year (2018, 2020, 2022, etc.)
        election_type VARCHAR(50), -- GERAL, SUPLEMENTAR, etc.
        election_date DATE, -- Election date
        election_round INTEGER DEFAULT 1, -- Election round (1 or 2)
        election_code VARCHAR(20), -- TSE election code (CD_ELEICAO)

        -- CANDIDATE INFORMATION
        candidate_name VARCHAR(255) NOT NULL, -- Full candidate name (NM_CANDIDATO)
        ballot_name VARCHAR(100), -- Ballot name (NM_URNA_CANDIDATO)
        social_name VARCHAR(255), -- Social name (NM_SOCIAL_CANDIDATO)
        candidate_number VARCHAR(10), -- Ballot number (NR_CANDIDATO)
        cpf_candidate VARCHAR(11), -- Candidate CPF (NR_CPF_CANDIDATO)
        voter_registration VARCHAR(12), -- Voter registration number (NR_TITULO_ELEITORAL_CANDIDATO)

        -- POSITION AND PARTY
        position_code INTEGER, -- Position code (CD_CARGO)
        position_description VARCHAR(100), -- Position description (DS_CARGO)
        party_number INTEGER, -- Party number (NR_PARTIDO)
        party_code VARCHAR(10), -- Party abbreviation (SG_PARTIDO)
        party_name VARCHAR(255), -- Full party name (NM_PARTIDO)

        -- COALITION/FEDERATION
        coalition_name VARCHAR(255), -- Coalition name (NM_COLIGACAO)
        coalition_composition TEXT, -- Coalition composition (DS_COMPOSICAO_COLIGACAO)
        federation_number INTEGER, -- Federation number (NR_FEDERACAO)
        federation_code VARCHAR(20), -- Federation abbreviation (SG_FEDERACAO)
        federation_composition TEXT, -- Federation composition (DS_COMPOSICAO_FEDERACAO)

        -- ELECTORAL OUTCOMES (Key Fields for Analysis)
        candidacy_status_code INTEGER, -- Candidacy status code (CD_SITUACAO_CANDIDATURA)
        candidacy_status VARCHAR(100), -- Candidacy status description (DS_SITUACAO_CANDIDATURA)
        electoral_outcome_code INTEGER, -- Final result code (CD_SIT_TOT_TURNO)
        electoral_outcome VARCHAR(100) NOT NULL, -- Final result description (DS_SIT_TOT_TURNO)
        votes_received INTEGER DEFAULT 0, -- Votes received (QT_VOTOS_NOMINAIS when available)

        -- GEOGRAPHIC CONTEXT
        electoral_unit_code VARCHAR(20), -- Electoral unit code (SG_UE)
        electoral_unit_name VARCHAR(255), -- Electoral unit name (NM_UE)
        state_code VARCHAR(10), -- State code (SG_UF)

        -- CANDIDATE DEMOGRAPHICS
        birth_date DATE, -- Birth date (DT_NASCIMENTO)
        birth_state VARCHAR(10), -- Birth state (SG_UF_NASCIMENTO)
        gender_code INTEGER, -- Gender code (CD_GENERO)
        gender_description VARCHAR(20), -- Gender description (DS_GENERO)
        education_code INTEGER, -- Education code (CD_GRAU_INSTRUCAO)
        education_description VARCHAR(100), -- Education description (DS_GRAU_INSTRUCAO)
        marital_status_code INTEGER, -- Marital status code (CD_ESTADO_CIVIL)
        marital_status VARCHAR(50), -- Marital status description (DS_ESTADO_CIVIL)
        race_color_code INTEGER, -- Race/color code (CD_COR_RACA)
        race_color VARCHAR(50), -- Race/color description (DS_COR_RACA)
        occupation_code INTEGER, -- Occupation code (CD_OCUPACAO)
        occupation_description VARCHAR(255), -- Occupation description (DS_OCUPACAO)

        -- DERIVED ANALYSIS FIELDS (Calculated from electoral_outcome)
        was_elected BOOLEAN DEFAULT FALSE, -- Calculated: true if any "ELEITO" variant
        election_status_category VARCHAR(30), -- Standardized category: ELECTED_DIRECT, NOT_ELECTED, SUBSTITUTE, etc.

        -- METADATA
        data_generation_date DATE, -- TSE data generation date (DT_GERACAO)
        data_generation_time TIME, -- TSE data generation time (HH_GERACAO)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        -- CONSTRAINTS AND INDEXES
        UNIQUE(politician_id, election_year, position_code, election_round)
    )
    """)
    print("✓ Created unified_electoral_records table")

    # Continue with remaining tables...
    remaining_tables = [
        ('unified_political_networks', '''
        CREATE TABLE IF NOT EXISTS unified_political_networks (
            id SERIAL PRIMARY KEY,
            politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,
            network_type VARCHAR(50) NOT NULL,
            network_id VARCHAR(50) NOT NULL,
            network_name VARCHAR(500) NOT NULL,
            role VARCHAR(400),
            role_code VARCHAR(20),
            is_leadership BOOLEAN DEFAULT FALSE,
            start_date DATE,
            end_date DATE,
            year INTEGER NOT NULL,
            legislature_id INTEGER,
            election_year INTEGER,
            source_system VARCHAR(20) NOT NULL,
            network_size INTEGER,
            network_description TEXT,
            coalition_composition TEXT,
            federation_composition TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''),
        ('unified_wealth_tracking', '''
        CREATE TABLE IF NOT EXISTS unified_wealth_tracking (
            id SERIAL PRIMARY KEY,
            politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,
            year INTEGER NOT NULL,
            election_year INTEGER,
            reference_date DATE,
            total_declared_wealth DECIMAL(15,2) NOT NULL,
            number_of_assets INTEGER DEFAULT 0,
            real_estate_value DECIMAL(15,2) DEFAULT 0,
            vehicles_value DECIMAL(15,2) DEFAULT 0,
            investments_value DECIMAL(15,2) DEFAULT 0,
            business_value DECIMAL(15,2) DEFAULT 0,
            cash_deposits_value DECIMAL(15,2) DEFAULT 0,
            other_assets_value DECIMAL(15,2) DEFAULT 0,
            previous_year INTEGER,
            previous_total_wealth DECIMAL(15,2),
            years_between_declarations INTEGER,
            externally_verified BOOLEAN DEFAULT FALSE,
            verification_date DATE,
            verification_source VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''),
        ('politician_career_history', '''
        CREATE TABLE IF NOT EXISTS politician_career_history (
            id SERIAL PRIMARY KEY,
            politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,
            mandate_type VARCHAR(50),
            office_name VARCHAR(255),
            entity_name VARCHAR(255),
            state VARCHAR(10),
            municipality VARCHAR(255),
            start_year INTEGER,
            end_year INTEGER,
            start_date DATE,
            end_date DATE,
            election_year INTEGER,
            party_at_election VARCHAR(20),
            mandate_status VARCHAR(100),
            mandate_outcome VARCHAR(100),
            source_system VARCHAR(20) DEFAULT 'DEPUTADOS',
            source_record_id VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''),
        ('politician_events', '''
        CREATE TABLE IF NOT EXISTS politician_events (
            id SERIAL PRIMARY KEY,
            politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,
            event_id VARCHAR(50),
            event_type VARCHAR(100),
            event_description TEXT,
            start_datetime TIMESTAMP,
            end_datetime TIMESTAMP,
            duration_minutes INTEGER,
            location_building VARCHAR(255),
            location_room VARCHAR(255),
            location_floor VARCHAR(100),
            location_external VARCHAR(255),
            registration_url VARCHAR(500),
            document_url VARCHAR(500),
            event_status VARCHAR(50),
            attendance_confirmed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''),
        ('politician_assets', '''
        CREATE TABLE IF NOT EXISTS politician_assets (
            id SERIAL PRIMARY KEY,
            politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,
            wealth_tracking_id INTEGER REFERENCES unified_wealth_tracking(id) ON DELETE CASCADE,
            asset_sequence INTEGER,
            asset_type_code INTEGER,
            asset_type_description VARCHAR(100),
            asset_description TEXT,
            declared_value DECIMAL(15,2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'BRL',
            declaration_year INTEGER NOT NULL,
            election_year INTEGER,
            last_update_date DATE,
            data_generation_date DATE,
            verified_value DECIMAL(15,2),
            verification_source VARCHAR(100),
            verification_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''),
        ('politician_professional_background', '''
        CREATE TABLE IF NOT EXISTS politician_professional_background (
            id SERIAL PRIMARY KEY,
            politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,
            profession_type VARCHAR(50),
            profession_code INTEGER,
            profession_name VARCHAR(255),
            entity_name VARCHAR(255),
            start_date DATE,
            end_date DATE,
            year_start INTEGER,
            year_end INTEGER,
            professional_title VARCHAR(255),
            professional_registry VARCHAR(100),
            entity_state VARCHAR(10),
            entity_country VARCHAR(100),
            is_current BOOLEAN DEFAULT FALSE,
            source_system VARCHAR(20) DEFAULT 'DEPUTADOS',
            source_record_id VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    ]

    for table_name, create_sql in remaining_tables:
        cursor.execute(create_sql)
        print(f"✓ Created {table_name} table")

    # Create indexes for performance optimization
    print("Creating performance indexes...")

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_politicians_cpf ON unified_politicians(cpf)",
        "CREATE INDEX IF NOT EXISTS idx_politicians_deputy_active ON unified_politicians(deputy_active)",
        "CREATE INDEX IF NOT EXISTS idx_financial_politician_year ON unified_financial_records(politician_id, year)",
        "CREATE INDEX IF NOT EXISTS idx_financial_counterpart_cnpj ON unified_financial_records(counterpart_cnpj_cpf)",
        "CREATE INDEX IF NOT EXISTS idx_counterparts_cnpj ON financial_counterparts(cnpj_cpf)",
        "CREATE INDEX IF NOT EXISTS idx_networks_politician ON unified_political_networks(politician_id, network_type)",
        "CREATE INDEX IF NOT EXISTS idx_wealth_politician_year ON unified_wealth_tracking(politician_id, year)",
        "CREATE INDEX IF NOT EXISTS idx_career_politician ON politician_career_history(politician_id)",
        "CREATE INDEX IF NOT EXISTS idx_events_politician ON politician_events(politician_id)",
        "CREATE INDEX IF NOT EXISTS idx_assets_politician_year ON politician_assets(politician_id, declaration_year)",
        "CREATE INDEX IF NOT EXISTS idx_professional_politician ON politician_professional_background(politician_id)"
    ]

    # Add unique constraints to prevent duplicates
    unique_constraints = [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_financial_records_unique ON unified_financial_records(source_system, source_record_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_political_networks_unique ON unified_political_networks(politician_id, network_type, network_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_career_history_unique ON politician_career_history(politician_id, office_name, start_year, state, municipality)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique ON politician_events(politician_id, event_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_assets_unique ON politician_assets(politician_id, declaration_year, asset_sequence)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_professional_unique ON politician_professional_background(politician_id, profession_type, profession_name, year_start)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_wealth_tracking_unique ON unified_wealth_tracking(politician_id, year)"
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    print("✓ Created performance indexes")

    # Create unique constraints
    print("Creating unique constraints to prevent duplicates...")
    for constraint_sql in unique_constraints:
        cursor.execute(constraint_sql)

    print("✓ Created unique constraints")

    # Commit changes and close connection
    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n🎯 SUCCESS: PostgreSQL database created with all 9 unified schema tables!")
    print("\nTables created:")
    print("1. ✅ unified_politicians (Core entity with 100% field mapping)")
    print("2. ✅ unified_financial_records (All transactions)")
    print("3. ✅ financial_counterparts (Vendor/donor registry)")
    print("4. ✅ unified_political_networks (Committees and coalitions)")
    print("5. ✅ unified_wealth_tracking (Asset summaries)")
    print("6. ✅ politician_career_history (External mandates)")
    print("7. ✅ politician_events (Parliamentary activity)")
    print("8. ✅ politician_assets (Individual TSE assets)")
    print("9. ✅ politician_professional_background (Professions and occupations)")
    print("\n📊 Database ready for data population following the DATA_POPULATION_GUIDE.md")

if __name__ == "__main__":
    create_unified_postgres_database()