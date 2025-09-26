"""
CLI4 Electoral Records Populator
Populate unified_electoral_records table with TSE electoral outcome data
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker
from src.clients.tse_client import TSEClient


class ElectoralRecordsPopulator:
    """Populate unified_electoral_records table with TSE electoral outcome data"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None,
                 election_years: Optional[List[int]] = None) -> int:
        """Populate unified electoral records table"""

        print("🗳️ UNIFIED ELECTORAL RECORDS POPULATION")
        print("=" * 60)
        print("Electoral outcome data from TSE with win/loss tracking")
        print()

        # Check dependencies
        DependencyChecker.print_dependency_warning(
            required_steps=["politicians"],
            current_step="ELECTORAL RECORDS POPULATION"
        )

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = database.execute_query(
                "SELECT id, cpf, nome_civil FROM unified_politicians WHERE cpf IS NOT NULL"
            )

        print(f"👥 Processing {len(politicians)} politicians with CPF")

        # Set election years to process
        if not election_years:
            election_years = [2018, 2020, 2022]  # Default recent elections

        print(f"🗳️ Election years: {', '.join(map(str, election_years))}")
        print()

        total_records = 0
        processed_politicians = 0
        skipped_politicians = 0

        for i, politician in enumerate(politicians, 1):
            print(f"\n👤 [{i}/{len(politicians)}] Processing: {politician['nome_civil'][:40]}")
            print(f"   CPF: {politician['cpf']} | ID: {politician['id']}")

            try:
                # Check if already processed
                existing_count = self._count_existing_records(politician['id'])
                if existing_count > 0:
                    print(f"   ⏭️ Skipping - already has {existing_count} electoral records")
                    skipped_politicians += 1
                    continue

                # Process all election years for this politician
                all_records = []
                for year in election_years:
                    print(f"   📊 Processing {year} electoral data...")
                    year_records = self._process_election_year(politician, year)
                    all_records.extend(year_records)
                    print(f"      Found {len(year_records)} records for {year}")

                    # Rate limiting between years
                    self.rate_limiter.wait_if_needed('default')

                # Bulk insert all electoral records
                if all_records:
                    inserted = self._bulk_insert_records(all_records)
                    total_records += inserted
                    processed_politicians += 1
                    print(f"   ✅ Inserted {inserted} electoral records")

                    self.logger.log_processing(
                        'electoral_records', str(politician['id']), 'success',
                        {'records_count': inserted, 'years_processed': len(election_years)}
                    )
                else:
                    print(f"   ⚠️ No electoral records found")

            except Exception as e:
                print(f"   ❌ Error processing politician {politician['id']}: {e}")
                self.logger.log_processing(
                    'electoral_records', str(politician['id']), 'error',
                    {'error': str(e)}
                )
                continue

        print(f"\n✅ ELECTORAL RECORDS POPULATION COMPLETED")
        print(f"   Total records: {total_records}")
        print(f"   Politicians processed: {processed_politicians}")
        print(f"   Politicians skipped: {skipped_politicians}")
        print(f"   Election years: {', '.join(map(str, election_years))}")

        return total_records

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs"""
        placeholders = ','.join(['%s'] * len(politician_ids))
        query = f"SELECT id, cpf, nome_civil FROM unified_politicians WHERE id IN ({placeholders}) AND cpf IS NOT NULL"
        return database.execute_query(query, tuple(politician_ids))

    def _count_existing_records(self, politician_id: int) -> int:
        """Count existing electoral records for a politician"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM unified_electoral_records WHERE politician_id = %s",
            (politician_id,)
        )
        return result[0]['count'] if result else 0

    def _process_election_year(self, politician: Dict, year: int) -> List[Dict]:
        """Process electoral data for a specific year using proven TSE structure"""
        records = []

        try:
            politician_cpf = politician['cpf']
            politician_name = politician['nome_civil']
            print(f"      🔍 Searching TSE {year} for CPF {politician_cpf} ({politician_name[:30]}...)")

            # Use the proven approach: download candidate data and filter by CPF
            # This is more reliable than name search which might miss variations
            candidates = self.tse_client.get_candidate_data(year=year)

            if not candidates:
                print(f"      ⚠️ No candidate data available for {year}")
                return records

            # Find candidacies by CPF (proven field: NR_CPF_CANDIDATO)
            matched_candidacies = []
            for candidate in candidates:
                candidate_cpf = candidate.get('NR_CPF_CANDIDATO') or candidate.get('nr_cpf_candidato')
                if candidate_cpf == politician_cpf:
                    matched_candidacies.append(candidate)

            print(f"      ✅ Found {len(matched_candidacies)} candidacies for CPF {politician_cpf}")

            # Convert each candidacy using proven TSE field structure
            for candidacy in matched_candidacies:
                record = self._convert_tse_candidacy_to_record(politician['id'], candidacy, year)
                if record:
                    records.append(record)
                    # Try both original TSE fields and normalized fields
                    outcome = candidacy.get('ds_situacao_candidatura') or candidacy.get('status', 'Unknown')
                    office = candidacy.get('ds_cargo') or candidacy.get('position', 'Unknown')
                    print(f"        📊 {office}: {outcome}")

        except Exception as e:
            print(f"      ❌ Error processing {year}: {e}")
            import traceback
            traceback.print_exc()

        return records

    def _convert_tse_candidacy_to_record(self, politician_id: int, candidacy: Dict, year: int) -> Optional[Dict]:
        """Convert TSE candidacy to electoral record using PROVEN field structure"""
        try:
            # Parse dates using proven TSE format
            election_date = None
            data_generation_date = None

            if candidacy.get('DT_ELEICAO'):
                try:
                    election_date = datetime.strptime(candidacy['DT_ELEICAO'], '%d/%m/%Y').date()
                except (ValueError, TypeError):
                    pass

            if candidacy.get('DT_GERACAO'):
                try:
                    data_generation_date = datetime.strptime(candidacy['DT_GERACAO'], '%d/%m/%Y').date()
                except (ValueError, TypeError):
                    pass

            # Build electoral record using PROVEN TSE field mappings
            record = {
                'politician_id': politician_id,
                'source_system': 'TSE',
                'source_record_id': candidacy.get('SQ_CANDIDATO'),
                'source_url': None,

                # Election context (PROVEN FIELDS)
                'election_year': year,
                'election_type': candidacy.get('NM_TIPO_ELEICAO'),
                'election_date': election_date,
                'election_round': candidacy.get('nr_turno', 1),
                'election_code': candidacy.get('cd_eleicao'),

                # Candidate information - use lowercase (normalized by TSE client)
                'candidate_name': candidacy.get('nm_candidato') or candidacy.get('name') or 'NOME NAO DISPONIVEL',
                'ballot_name': candidacy.get('nm_urna_candidato') or candidacy.get('ballot_name'),
                'social_name': candidacy.get('nm_social_candidato'),
                'candidate_number': candidacy.get('nr_candidato') or candidacy.get('electoral_number'),
                'cpf_candidate': candidacy.get('nr_cpf_candidato') or candidacy.get('cpf'),
                'voter_registration': candidacy.get('NR_TITULO_ELEITORAL_CANDIDATO'),

                # Position and party (PROVEN FIELDS)
                'position_code': candidacy.get('cd_cargo'),
                'position_description': candidacy.get('ds_cargo') or candidacy.get('position'),
                'party_number': candidacy.get('nr_partido'),
                'party_abbreviation': candidacy.get('sg_partido') or candidacy.get('party'),
                'party_name': candidacy.get('nm_partido') or candidacy.get('party_name'),

                # Coalition/Federation (PROVEN FIELDS)
                'coalition_name': candidacy.get('NM_COLIGACAO'),
                'coalition_composition': candidacy.get('DS_COMPOSICAO_COLIGACAO'),
                'federation_name': candidacy.get('NM_FEDERACAO'),
                'federation_number': candidacy.get('NR_FEDERACAO'),

                # Electoral outcome (PROVEN FIELDS - CRITICAL!)
                'candidacy_status_code': candidacy.get('CD_SITUACAO_CANDIDATURA') or candidacy.get('cd_situacao_candidatura'),
                'candidacy_status_description': candidacy.get('DS_SITUACAO_CANDIDATURA') or candidacy.get('ds_situacao_candidatura') or candidacy.get('status') or 'SITUACAO NAO DISPONIVEL',
                'final_result_code': candidacy.get('CD_SIT_TOT_TURNO') or candidacy.get('cd_sit_tot_turno'),
                'electoral_outcome': candidacy.get('DS_SIT_TOT_TURNO') or candidacy.get('ds_sit_tot_turno') or candidacy.get('electoral_outcome') or 'RESULTADO NAO DISPONIVEL',

                # Geographic (PROVEN FIELDS)
                'state': candidacy.get('SG_UF'),
                'electoral_unit': candidacy.get('SG_UE'),
                'electoral_unit_name': candidacy.get('NM_UE'),

                # Demographics (PROVEN FIELDS)
                'gender_code': candidacy.get('CD_GENERO'),
                'gender_description': candidacy.get('DS_GENERO'),
                'birth_date': candidacy.get('DT_NASCIMENTO'),
                'education_code': candidacy.get('CD_GRAU_INSTRUCAO'),
                'education_description': candidacy.get('DS_GRAU_INSTRUCAO'),
                'occupation_code': candidacy.get('CD_OCUPACAO'),
                'occupation_description': candidacy.get('DS_OCUPACAO'),

                # System metadata
                'data_generation_date': data_generation_date,
                'data_generation_time': candidacy.get('HH_GERACAO'),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            return record

        except Exception as e:
            print(f"    ❌ Error converting candidacy: {e}")
            return None

    def _convert_candidacy_to_record(self, politician_id: int, candidacy: Dict, year: int) -> Optional[Dict]:
        """Convert TSE candidacy data to database record format"""
        try:
            # Parse TSE dates if available
            election_date = None
            data_generation_date = None
            data_generation_time = None

            if candidacy.get('dt_eleicao'):
                try:
                    election_date = datetime.strptime(candidacy['dt_eleicao'], '%d/%m/%Y').date()
                except (ValueError, TypeError):
                    pass

            if candidacy.get('dt_geracao'):
                try:
                    data_generation_date = datetime.strptime(candidacy['dt_geracao'], '%d/%m/%Y').date()
                except (ValueError, TypeError):
                    pass

            if candidacy.get('hh_geracao'):
                try:
                    data_generation_time = datetime.strptime(candidacy['hh_geracao'], '%H:%M:%S').time()
                except (ValueError, TypeError):
                    pass

            # Build the electoral record
            record = {
                'politician_id': politician_id,
                'source_system': 'TSE',
                'source_record_id': candidacy.get('candidate_id') or candidacy.get('sq_candidato'),
                'source_url': None,  # Will be filled if available

                # Election context
                'election_year': year,
                'election_type': candidacy.get('nm_tipo_eleicao'),
                'election_date': election_date,
                'election_round': candidacy.get('nr_turno', 1),
                'election_code': candidacy.get('cd_eleicao'),

                # Candidate information (fallback for lowercase fields)
                'candidate_name': candidacy.get('name') or candidacy.get('nm_candidato') or candidacy.get('NM_CANDIDATO'),
                'ballot_name': candidacy.get('ballot_name') or candidacy.get('nm_urna_candidato'),
                'social_name': candidacy.get('nm_social_candidato'),
                'candidate_number': candidacy.get('electoral_number') or candidacy.get('nr_candidato'),
                'cpf_candidate': candidacy.get('cpf') or candidacy.get('nr_cpf_candidato'),
                'voter_registration': candidacy.get('nr_titulo_eleitoral_candidato'),

                # Position and party
                'position_code': candidacy.get('cd_cargo'),
                'position_description': candidacy.get('position') or candidacy.get('ds_cargo'),
                'party_number': candidacy.get('nr_partido'),
                'party_code': candidacy.get('party') or candidacy.get('sg_partido'),
                'party_name': candidacy.get('party_name') or candidacy.get('nm_partido'),

                # Coalition/federation
                'coalition_name': candidacy.get('coalition') or candidacy.get('nm_coligacao'),
                'coalition_composition': candidacy.get('ds_composicao_coligacao'),
                'federation_number': candidacy.get('nr_federacao'),
                'federation_code': candidacy.get('sg_federacao'),
                'federation_composition': candidacy.get('ds_composicao_federacao'),

                # Electoral outcomes (KEY FIELDS)
                'candidacy_status_code': candidacy.get('cd_situacao_candidatura'),
                'candidacy_status': candidacy.get('status') or candidacy.get('ds_situacao_candidatura'),
                'electoral_outcome_code': candidacy.get('electoral_outcome_code') or candidacy.get('cd_sit_tot_turno'),
                'electoral_outcome': candidacy.get('electoral_outcome') or candidacy.get('ds_sit_tot_turno'),
                'votes_received': candidacy.get('votes_received_int', 0),

                # Geographic context
                'electoral_unit_code': candidacy.get('electoral_unit_code') or candidacy.get('sg_ue'),
                'electoral_unit_name': candidacy.get('electoral_unit') or candidacy.get('nm_ue'),
                'state_code': candidacy.get('state') or candidacy.get('sg_uf'),

                # Demographics from TSE
                'birth_date': None,  # Would need parsing from dt_nascimento
                'birth_state': candidacy.get('sg_uf_nascimento'),
                'gender_code': candidacy.get('cd_genero'),
                'gender_description': candidacy.get('ds_genero'),
                'education_code': candidacy.get('cd_grau_instrucao'),
                'education_description': candidacy.get('ds_grau_instrucao'),
                'marital_status_code': candidacy.get('cd_estado_civil'),
                'marital_status': candidacy.get('ds_estado_civil'),
                'race_color_code': candidacy.get('cd_cor_raca'),
                'race_color': candidacy.get('ds_cor_raca'),
                'occupation_code': candidacy.get('cd_ocupacao'),
                'occupation_description': candidacy.get('ds_ocupacao'),

                # Derived analysis fields (calculated by TSE client)
                'was_elected': candidacy.get('was_elected', False),
                'election_status_category': candidacy.get('election_status_category'),

                # Metadata
                'data_generation_date': data_generation_date,
                'data_generation_time': data_generation_time
            }

            return record

        except Exception as e:
            print(f"        ❌ Error converting candidacy: {e}")
            return None

    def _bulk_insert_records(self, records: List[Dict]) -> int:
        """Bulk insert electoral records into database"""
        if not records:
            return 0

        # Define the field order for insertion (matching database schema)
        field_order = [
            'politician_id', 'source_system', 'source_record_id', 'source_url',
            'election_year', 'election_type', 'election_date', 'election_round', 'election_code',
            'candidate_name', 'ballot_name', 'social_name', 'candidate_number', 'cpf_candidate', 'voter_registration',
            'position_code', 'position_description', 'party_number', 'party_code', 'party_name',
            'coalition_name', 'coalition_composition', 'federation_number', 'federation_code', 'federation_composition',
            'candidacy_status_code', 'candidacy_status', 'electoral_outcome_code', 'electoral_outcome', 'votes_received',
            'electoral_unit_code', 'electoral_unit_name', 'state_code',
            'birth_date', 'birth_state', 'gender_code', 'gender_description',
            'education_code', 'education_description', 'marital_status_code', 'marital_status',
            'race_color_code', 'race_color', 'occupation_code', 'occupation_description',
            'was_elected', 'election_status_category',
            'data_generation_date', 'data_generation_time'
        ]

        # Build SQL
        columns = ', '.join(field_order)
        placeholders = ', '.join(['%s'] * len(field_order))
        sql = f"""
            INSERT INTO unified_electoral_records ({columns})
            VALUES ({placeholders})
            ON CONFLICT (politician_id, election_year, position_code, election_round) DO NOTHING
            RETURNING id
        """

        # Prepare values
        values = []
        for record in records:
            row = tuple(record.get(field) for field in field_order)
            values.append(row)

        try:
            # Debug: Check the first record structure
            if values:
                print(f"      🔍 First record has {len(values[0])} fields, SQL expects {sql.count('%s')}")
                print(f"      🔍 Sample values: {values[0][:5]}...")

            results = database.execute_batch_returning(sql, values)
            return len(results)
        except Exception as e:
            print(f"      ❌ Bulk insert error: {e}")
            return 0