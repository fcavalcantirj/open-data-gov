#!/usr/bin/env python3
"""
Drop and Recreate All Tables with Proper Unique Constraints
Complete reset for testing duplicate prevention
"""

import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def recreate_all_tables():
    """Drop all tables and recreate with proper constraints"""

    postgres_url = os.getenv('POSTGRES_POOL_URL')
    if not postgres_url:
        raise Exception("POSTGRES_POOL_URL environment variable not set")

    print(f"🐘 Connecting to PostgreSQL database...")
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()

    print("⚠️  DROPPING ALL TABLES...")

    # Drop all tables in correct order (dependencies first)
    drop_tables = [
        "DROP TABLE IF EXISTS party_memberships CASCADE",
        "DROP TABLE IF EXISTS politician_assets CASCADE",
        "DROP TABLE IF EXISTS politician_professional_background CASCADE",
        "DROP TABLE IF EXISTS politician_events CASCADE",
        "DROP TABLE IF EXISTS politician_career_history CASCADE",
        "DROP TABLE IF EXISTS unified_wealth_tracking CASCADE",
        "DROP TABLE IF EXISTS unified_political_networks CASCADE",
        "DROP TABLE IF EXISTS unified_electoral_records CASCADE",
        "DROP TABLE IF EXISTS unified_financial_records CASCADE",
        "DROP TABLE IF EXISTS vendor_sanctions CASCADE",
        "DROP TABLE IF EXISTS tcu_disqualifications CASCADE",
        "DROP TABLE IF EXISTS senado_politicians CASCADE",
        "DROP TABLE IF EXISTS political_parties CASCADE",
        "DROP TABLE IF EXISTS financial_counterparts CASCADE",
        "DROP TABLE IF EXISTS unified_politicians CASCADE"
    ]

    for drop_sql in drop_tables:
        cursor.execute(drop_sql)
        table_name = drop_sql.split("IF EXISTS ")[1].split(" ")[0]
        print(f"  🗑️  Dropped {table_name}")

    print("\n✅ All tables dropped successfully!")
    print("\nRecreating tables with proper constraints...")

    # Table 1: Unified Politicians
    cursor.execute("""
    CREATE TABLE unified_politicians (
        id SERIAL PRIMARY KEY,

        -- UNIVERSAL IDENTIFIERS
        cpf CHAR(11) UNIQUE NOT NULL,
        nome_civil VARCHAR(255) NOT NULL,
        nome_completo_normalizado VARCHAR(255),

        -- SOURCE SYSTEM LINKS
        deputy_id INTEGER UNIQUE, -- UNIQUE constraint for deputy_id
        sq_candidato_current BIGINT,
        deputy_active BOOLEAN DEFAULT FALSE,

        -- DEPUTADOS CORE IDENTITY DATA
        nome_eleitoral VARCHAR(255),
        url_foto VARCHAR(255),
        data_falecimento DATE,

        -- TSE CORE IDENTITY DATA
        electoral_number VARCHAR(20),
        nr_titulo_eleitoral VARCHAR(12),
        nome_urna_candidato VARCHAR(100),
        nome_social_candidato VARCHAR(255),

        -- CURRENT POLITICAL STATUS
        current_party VARCHAR(20),
        current_state VARCHAR(10),
        current_legislature INTEGER,
        situacao VARCHAR(100),
        condicao_eleitoral VARCHAR(100),

        -- TSE POLITICAL DETAILS
        nr_partido INTEGER,
        nm_partido VARCHAR(255),
        nr_federacao INTEGER,
        sg_federacao VARCHAR(20),
        current_position VARCHAR(100),

        -- TSE ELECTORAL STATUS
        cd_situacao_candidatura INTEGER,
        ds_situacao_candidatura VARCHAR(100),
        cd_sit_tot_turno INTEGER,
        ds_sit_tot_turno VARCHAR(100),

        -- DEMOGRAPHICS
        birth_date DATE,
        birth_state VARCHAR(10),
        birth_municipality VARCHAR(255),
        gender VARCHAR(20),
        gender_code INTEGER,
        education_level VARCHAR(100),
        education_code INTEGER,
        occupation VARCHAR(255),
        occupation_code INTEGER,
        marital_status VARCHAR(50),
        marital_status_code INTEGER,
        race_color VARCHAR(50),
        race_color_code INTEGER,

        -- GEOGRAPHIC DETAILS
        sg_ue VARCHAR(20),
        nm_ue VARCHAR(255),

        -- CONTACT INFORMATION
        email VARCHAR(255),
        phone VARCHAR(50),
        website VARCHAR(255),
        social_networks JSONB,

        -- OFFICE DETAILS
        office_building VARCHAR(100),
        office_room VARCHAR(50),
        office_floor VARCHAR(50),
        office_phone VARCHAR(50),
        office_email VARCHAR(255),

        -- CAREER TIMELINE
        first_election_year INTEGER,
        last_election_year INTEGER,
        total_elections INTEGER,
        first_mandate_year INTEGER,

        -- ENHANCED AGGREGATE METRICS (calculated fields)
        number_of_elections INTEGER DEFAULT 0,
        electoral_success_rate DECIMAL(5,2) DEFAULT 0.0,
        total_financial_transactions INTEGER DEFAULT 0,
        total_financial_amount DECIMAL(15,2) DEFAULT 0.0,
        financial_counterparts_count INTEGER DEFAULT 0,
        first_transaction_date DATE,
        last_transaction_date DATE,

        -- CORRUPTION DETECTION METRICS
        tcu_disqualifications_total INTEGER DEFAULT 0,
        tcu_disqualifications_active INTEGER DEFAULT 0,
        tcu_first_disqualification DATE,
        tcu_latest_disqualification DATE,
        sanctioned_vendors_count INTEGER DEFAULT 0,
        sanctioned_vendors_total_sanctions INTEGER DEFAULT 0,
        sanctioned_vendors_amount DECIMAL(15,2) DEFAULT 0.0,
        corruption_risk_score DECIMAL(5,2) DEFAULT 0.0,

        -- FAMILY NETWORK ANALYSIS
        family_senators_count INTEGER DEFAULT 0,
        family_deputies_count INTEGER DEFAULT 0,
        family_parties_senado TEXT,
        family_parties_camara TEXT,
        political_network_types INTEGER DEFAULT 0,
        total_political_networks INTEGER DEFAULT 0,
        leadership_positions_count INTEGER DEFAULT 0,

        -- CAREER PROGRESSION METRICS
        career_unique_offices INTEGER DEFAULT 0,
        career_total_mandates INTEGER DEFAULT 0,
        career_start_year INTEGER,
        career_latest_year INTEGER,
        career_span_years INTEGER DEFAULT 0,
        career_states_served INTEGER DEFAULT 0,
        professional_background_types INTEGER DEFAULT 0,
        professional_background_total INTEGER DEFAULT 0,
        professional_background_list TEXT,
        parliamentary_events_total INTEGER DEFAULT 0,
        parliamentary_event_types INTEGER DEFAULT 0,
        parliamentary_attendance_rate DECIMAL(5,2) DEFAULT 0.0,

        -- WEALTH PROGRESSION METRICS
        wealth_declarations_count INTEGER DEFAULT 0,
        wealth_first_year INTEGER,
        wealth_latest_year INTEGER,
        wealth_lowest_declared DECIMAL(15,2),
        wealth_highest_declared DECIMAL(15,2),
        wealth_average_declared DECIMAL(15,2),
        wealth_total_growth DECIMAL(15,2) DEFAULT 0.0,
        asset_types_diversity INTEGER DEFAULT 0,
        total_individual_assets INTEGER DEFAULT 0,
        total_individual_asset_value DECIMAL(15,2) DEFAULT 0.0,
        average_individual_asset_value DECIMAL(15,2) DEFAULT 0.0,

        -- DATA VALIDATION FLAGS
        cpf_validated BOOLEAN DEFAULT FALSE,
        tse_linked BOOLEAN DEFAULT FALSE,
        last_updated_date DATE,

        -- METADATA
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✓ Created unified_politicians table")

    # Table 2: Financial Counterparts
    cursor.execute("""
    CREATE TABLE financial_counterparts (
        id SERIAL PRIMARY KEY,

        -- IDENTITY
        cnpj_cpf VARCHAR(14) UNIQUE NOT NULL,  -- UNIQUE constraint
        name VARCHAR(255) NOT NULL,
        normalized_name VARCHAR(255),
        entity_type VARCHAR(20) NOT NULL,
        source_system VARCHAR(20),

        -- COMPANY DETAILS
        trade_name VARCHAR(255),
        business_sector VARCHAR(100),
        company_size VARCHAR(20),
        registration_status VARCHAR(50),

        -- GEOGRAPHIC INFORMATION
        state VARCHAR(10),
        municipality VARCHAR(255),

        -- TRANSACTION SUMMARY
        total_transaction_amount DECIMAL(15,2) DEFAULT 0,
        transaction_count INTEGER DEFAULT 0,
        politician_count INTEGER DEFAULT 0,
        first_transaction_date DATE,
        last_transaction_date DATE,

        -- EXTERNAL VALIDATION FLAGS
        cnpj_validated BOOLEAN DEFAULT FALSE,
        sanctions_checked BOOLEAN DEFAULT FALSE,
        last_validation DATE,

        -- METADATA
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✓ Created financial_counterparts table")

    # Table 3: Unified Financial Records with UNIQUE constraint
    cursor.execute("""
    CREATE TABLE unified_financial_records (
        id SERIAL PRIMARY KEY,
        politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,

        -- SOURCE IDENTIFICATION
        source_system VARCHAR(20) NOT NULL,
        source_record_id VARCHAR(50),
        source_url VARCHAR(500),

        -- TRANSACTION CLASSIFICATION
        transaction_type VARCHAR(50) NOT NULL,
        transaction_category VARCHAR(255),

        -- FINANCIAL DETAILS
        amount DECIMAL(15,2) NOT NULL,
        amount_net DECIMAL(15,2),
        amount_rejected DECIMAL(15,2) DEFAULT 0,
        original_amount DECIMAL(15,2),

        -- TEMPORAL DETAILS
        transaction_date DATE NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER,

        -- COUNTERPART INFORMATION
        counterpart_name VARCHAR(255),
        counterpart_cnpj_cpf VARCHAR(14),
        counterpart_type VARCHAR(50),
        counterpart_cnae VARCHAR(20),
        counterpart_business_type VARCHAR(100),

        -- GEOGRAPHIC CONTEXT
        state VARCHAR(10),
        municipality VARCHAR(255),

        -- DOCUMENT REFERENCES
        document_number VARCHAR(100),
        document_code INTEGER,
        document_type VARCHAR(100),
        document_type_code INTEGER,
        document_url VARCHAR(500),

        -- PROCESSING DETAILS
        lote_code INTEGER,
        installment INTEGER,
        reimbursement_number VARCHAR(100),

        -- ELECTION CONTEXT
        election_year INTEGER,
        election_round INTEGER,
        election_date DATE,

        -- VALIDATION FLAGS
        cnpj_validated BOOLEAN DEFAULT FALSE,
        sanctions_checked BOOLEAN DEFAULT FALSE,
        external_validation_date DATE,

        -- METADATA
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        -- UNIQUE CONSTRAINT to prevent duplicates
        CONSTRAINT unique_financial_record UNIQUE (source_system, source_record_id)
    )
    """)
    print("✓ Created unified_financial_records table with unique constraint")

    # Table 4: Unified Electoral Records (NEW - Electoral Outcome Data)
    cursor.execute("""
    CREATE TABLE unified_electoral_records (
        id SERIAL PRIMARY KEY,
        politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,

        -- SOURCE IDENTIFICATION
        source_system VARCHAR(20) NOT NULL DEFAULT 'TSE',
        source_record_id VARCHAR(50),
        source_url VARCHAR(500),

        -- ELECTION CONTEXT
        election_year INTEGER NOT NULL,
        election_type VARCHAR(50),
        election_date DATE,
        election_round INTEGER DEFAULT 1,
        election_code VARCHAR(20),

        -- CANDIDATE INFORMATION
        candidate_name VARCHAR(255) NOT NULL,
        ballot_name VARCHAR(100),
        social_name VARCHAR(255),
        candidate_number VARCHAR(10),
        cpf_candidate VARCHAR(11),
        voter_registration VARCHAR(12),

        -- POSITION AND PARTY
        position_code INTEGER,
        position_description VARCHAR(100),
        party_number INTEGER,
        party_code VARCHAR(10),
        party_name VARCHAR(255),

        -- COALITION/FEDERATION
        coalition_name VARCHAR(255),
        coalition_composition TEXT,
        federation_number INTEGER,
        federation_code VARCHAR(20),
        federation_composition TEXT,

        -- ELECTORAL OUTCOMES (Key Fields for Analysis)
        candidacy_status_code INTEGER,
        candidacy_status VARCHAR(100),
        electoral_outcome_code INTEGER,
        electoral_outcome VARCHAR(100) NOT NULL,
        votes_received INTEGER DEFAULT 0,

        -- GEOGRAPHIC CONTEXT
        electoral_unit_code VARCHAR(20),
        electoral_unit_name VARCHAR(255),
        state_code VARCHAR(10),

        -- CANDIDATE DEMOGRAPHICS
        birth_date DATE,
        birth_state VARCHAR(10),
        gender_code INTEGER,
        gender_description VARCHAR(20),
        education_code INTEGER,
        education_description VARCHAR(100),
        marital_status_code INTEGER,
        marital_status VARCHAR(50),
        race_color_code INTEGER,
        race_color VARCHAR(50),
        occupation_code INTEGER,
        occupation_description VARCHAR(255),

        -- DERIVED ANALYSIS FIELDS
        was_elected BOOLEAN DEFAULT FALSE,
        election_status_category VARCHAR(30),

        -- METADATA
        data_generation_date DATE,
        data_generation_time TIME,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        -- UNIQUE CONSTRAINT to prevent duplicates
        CONSTRAINT unique_electoral_record UNIQUE (politician_id, election_year, position_code, election_round)
    )
    """)
    print("✓ Created unified_electoral_records table with unique constraint")

    # Continue with remaining tables...
    remaining_tables = [
        ('unified_political_networks', '''
        CREATE TABLE unified_political_networks (
            id SERIAL PRIMARY KEY,
            politician_id INTEGER NOT NULL REFERENCES unified_politicians(id) ON DELETE CASCADE,
            network_type VARCHAR(50) NOT NULL,
            network_id VARCHAR(50) NOT NULL,
            network_name VARCHAR(255) NOT NULL,
            role VARCHAR(100),
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_network_member UNIQUE (politician_id, network_type, network_id)
        )
        '''),
        ('unified_wealth_tracking', '''
        CREATE TABLE unified_wealth_tracking (
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_wealth_year UNIQUE (politician_id, year)
        )
        '''),
        ('politician_career_history', '''
        CREATE TABLE politician_career_history (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_mandate UNIQUE (politician_id, office_name, start_year, state, municipality)
        )
        '''),
        ('politician_events', '''
        CREATE TABLE politician_events (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_event UNIQUE (politician_id, event_id)
        )
        '''),
        ('politician_assets', '''
        CREATE TABLE politician_assets (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_asset UNIQUE (politician_id, declaration_year, asset_sequence)
        )
        '''),
        ('politician_professional_background', '''
        CREATE TABLE politician_professional_background (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_profession UNIQUE (politician_id, profession_type, profession_name, year_start)
        )
        '''),
        ('vendor_sanctions', '''
        CREATE TABLE vendor_sanctions (
            id SERIAL PRIMARY KEY,
            cnpj_cpf VARCHAR(14) NOT NULL,
            entity_name VARCHAR(500),
            sanction_type VARCHAR(100),
            sanction_description TEXT,
            sanction_start_date DATE,
            sanction_end_date DATE,
            sanctioning_agency VARCHAR(255),
            sanctioning_state VARCHAR(10),
            sanctioning_process VARCHAR(100),
            penalty_amount DECIMAL(15,2),
            is_active BOOLEAN DEFAULT TRUE,
            data_source VARCHAR(50) DEFAULT 'PORTAL_TRANSPARENCIA',
            api_reference_id VARCHAR(100),
            verification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_sanction UNIQUE (cnpj_cpf, sanction_type, sanction_start_date, sanctioning_agency)
        )
        '''),
        ('tcu_disqualifications', '''
        CREATE TABLE tcu_disqualifications (
            id SERIAL PRIMARY KEY,
            cpf VARCHAR(11) NOT NULL,
            nome VARCHAR(255),
            processo VARCHAR(50),
            deliberacao VARCHAR(50),
            data_transito_julgado DATE,
            data_final DATE,
            data_acordao DATE,
            uf VARCHAR(10),
            municipio VARCHAR(255),
            data_source VARCHAR(50) DEFAULT 'TCU',
            api_reference_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_tcu_disqualification UNIQUE (cpf, processo, deliberacao)
        )
        '''),
        ('senado_politicians', '''
        CREATE TABLE senado_politicians (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(10),
            codigo_publico VARCHAR(10),
            nome VARCHAR(255),
            nome_completo VARCHAR(255),
            sexo VARCHAR(20),
            partido VARCHAR(20),
            estado VARCHAR(10),
            email VARCHAR(255),
            foto_url VARCHAR(500),
            pagina_url VARCHAR(500),
            bloco VARCHAR(255),
            data_source VARCHAR(50) DEFAULT 'SENADO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_senado_politician UNIQUE (codigo)
        )
        '''),
        ('political_parties', '''
        CREATE TABLE political_parties (
            id INTEGER PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            sigla VARCHAR(20) NOT NULL,
            numero_eleitoral INTEGER,
            status VARCHAR(50) DEFAULT 'Ativo',
            lider_atual VARCHAR(255),
            lider_id INTEGER,
            lider_estado VARCHAR(10),
            lider_legislatura INTEGER,
            total_membros INTEGER DEFAULT 0,
            total_efetivos INTEGER DEFAULT 0,
            legislatura_id INTEGER,
            logo_url VARCHAR(500),
            uri_membros VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_party_legislature UNIQUE (id, legislatura_id)
        )
        '''),
        ('party_memberships', '''
        CREATE TABLE party_memberships (
            id SERIAL PRIMARY KEY,
            party_id INTEGER NOT NULL,
            deputy_id INTEGER NOT NULL,
            deputy_name VARCHAR(255),
            legislatura_id INTEGER,
            status VARCHAR(50) DEFAULT 'Ativo',
            data_inicio DATE,
            data_fim DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (party_id) REFERENCES political_parties(id),
            FOREIGN KEY (deputy_id) REFERENCES unified_politicians(deputy_id),
            CONSTRAINT unique_party_membership UNIQUE (party_id, deputy_id, legislatura_id)
        )
        ''')
    ]

    for table_name, create_sql in remaining_tables:
        cursor.execute(create_sql)
        print(f"✓ Created {table_name} table with unique constraint")

    # Create performance indexes
    print("\nCreating performance indexes...")
    indexes = [
        "CREATE INDEX idx_politicians_cpf ON unified_politicians(cpf)",
        "CREATE INDEX idx_politicians_deputy_active ON unified_politicians(deputy_active)",
        "CREATE INDEX idx_financial_politician_year ON unified_financial_records(politician_id, year)",
        "CREATE INDEX idx_financial_counterpart_cnpj ON unified_financial_records(counterpart_cnpj_cpf)",
        "CREATE INDEX idx_counterparts_cnpj ON financial_counterparts(cnpj_cpf)",
        "CREATE INDEX idx_networks_politician ON unified_political_networks(politician_id, network_type)",
        "CREATE INDEX idx_wealth_politician_year ON unified_wealth_tracking(politician_id, year)",
        "CREATE INDEX idx_career_politician ON politician_career_history(politician_id)",
        "CREATE INDEX idx_events_politician ON politician_events(politician_id)",
        "CREATE INDEX idx_assets_politician_year ON politician_assets(politician_id, declaration_year)",
        "CREATE INDEX idx_professional_politician ON politician_professional_background(politician_id)",
        "CREATE INDEX idx_sanctions_cnpj ON vendor_sanctions(cnpj_cpf)",
        "CREATE INDEX idx_sanctions_active ON vendor_sanctions(is_active)",
        "CREATE INDEX idx_tcu_cpf ON tcu_disqualifications(cpf)",
        "CREATE INDEX idx_tcu_data_final ON tcu_disqualifications(data_final)",
        "CREATE INDEX idx_tcu_uf ON tcu_disqualifications(uf)",
        "CREATE INDEX idx_senado_codigo ON senado_politicians(codigo)",
        "CREATE INDEX idx_senado_nome ON senado_politicians(nome_completo)",
        "CREATE INDEX idx_senado_partido_estado ON senado_politicians(partido, estado)",
        "CREATE INDEX idx_parties_sigla ON political_parties(sigla)",
        "CREATE INDEX idx_parties_legislatura ON political_parties(legislatura_id)",
        "CREATE INDEX idx_party_memberships_party ON party_memberships(party_id)",
        "CREATE INDEX idx_party_memberships_deputy ON party_memberships(deputy_id)",
        "CREATE INDEX idx_party_memberships_legislatura ON party_memberships(legislatura_id)",
        # Enhanced field indexes
        "CREATE INDEX idx_politicians_corruption_risk ON unified_politicians(corruption_risk_score)",
        "CREATE INDEX idx_politicians_tcu_disqualifications ON unified_politicians(tcu_disqualifications_total)",
        "CREATE INDEX idx_politicians_sanctioned_vendors ON unified_politicians(sanctioned_vendors_count)",
        "CREATE INDEX idx_politicians_family_network ON unified_politicians(family_senators_count, family_deputies_count)",
        "CREATE INDEX idx_politicians_career_span ON unified_politicians(career_span_years)",
        "CREATE INDEX idx_politicians_wealth_growth ON unified_politicians(wealth_total_growth)",
        "CREATE INDEX idx_politicians_electoral_success ON unified_politicians(electoral_success_rate)",
        "CREATE INDEX idx_politicians_corruption_composite ON unified_politicians(corruption_risk_score, tcu_disqualifications_total, sanctioned_vendors_count)",
        "CREATE INDEX idx_politicians_family_network_composite ON unified_politicians(family_senators_count, family_deputies_count, total_political_networks)"
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    print("✓ Created all performance indexes")

    # Add enhanced validation constraints
    print("\nAdding enhanced validation constraints...")
    enhanced_constraints_sql = """
    ALTER TABLE unified_politicians
    ADD CONSTRAINT check_corruption_risk_range CHECK (corruption_risk_score >= 0 AND corruption_risk_score <= 100),
    ADD CONSTRAINT check_electoral_success_range CHECK (electoral_success_rate >= 0 AND electoral_success_rate <= 100),
    ADD CONSTRAINT check_attendance_range CHECK (parliamentary_attendance_rate >= 0 AND parliamentary_attendance_rate <= 100),
    ADD CONSTRAINT check_non_negative_counts CHECK (
        tcu_disqualifications_total >= 0 AND
        sanctioned_vendors_count >= 0 AND
        family_senators_count >= 0 AND
        family_deputies_count >= 0 AND
        career_unique_offices >= 0 AND
        wealth_declarations_count >= 0
    );
    """

    cursor.execute(enhanced_constraints_sql)
    print("✓ Applied enhanced validation constraints")

    # Commit changes and close connection
    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n🎯 SUCCESS: All tables recreated with proper unique constraints!")
    print("\n📊 Tables created with UNIQUE constraints:")
    print("1. ✅ unified_politicians - UNIQUE on (cpf, deputy_id)")
    print("2. ✅ financial_counterparts - UNIQUE on (cnpj_cpf)")
    print("3. ✅ unified_financial_records - UNIQUE on (source_system, source_record_id)")
    print("4. ✅ unified_political_networks - UNIQUE on (politician_id, network_type, network_id)")
    print("5. ✅ unified_wealth_tracking - UNIQUE on (politician_id, year)")
    print("6. ✅ politician_career_history - UNIQUE on (politician_id, office_name, start_year, state, municipality)")
    print("7. ✅ politician_events - UNIQUE on (politician_id, event_id)")
    print("8. ✅ politician_assets - UNIQUE on (politician_id, declaration_year, asset_sequence)")
    print("9. ✅ politician_professional_background - UNIQUE on (politician_id, profession_type, profession_name, year_start)")
    print("10. ✅ vendor_sanctions - UNIQUE on (cnpj_cpf, sanction_type, sanction_start_date, sanctioning_agency)")
    print("11. ✅ tcu_disqualifications - UNIQUE on (cpf, processo, deliberacao)")
    print("12. ✅ senado_politicians - UNIQUE on (codigo)")
    print("13. ✅ political_parties - UNIQUE on (id, legislatura_id)")
    print("14. ✅ party_memberships - UNIQUE on (party_id, deputy_id, legislatura_id)")
    print("\n🚀 ENHANCED FEATURES READY:")
    print("✅ Corruption Detection: TCU disqualifications + vendor sanctions correlation")
    print("✅ Family Networks: Cross-chamber surname analysis (Senate + Chamber)")
    print("✅ Career Analytics: 35+ aggregate fields for comprehensive profiling")
    print("✅ Enhanced Post-Processing: Ready for python cli4/main.py post-process --enhanced")

    print("\n🧪 READY FOR TESTING!")
    print("Run these commands twice to test duplicate prevention:")
    print("1. python cli4/main.py populate --limit 10")
    print("2. python cli4/main.py populate-financial --limit 10")
    print("\n✅ The second run should UPDATE records, not create duplicates!")

if __name__ == "__main__":
    recreate_all_tables()