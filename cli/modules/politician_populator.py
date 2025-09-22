"""
Politician Populator Module
Populates the unified_politicians table (foundation table)
Implements the strategy from DATA_POPULATION_GUIDE.md Phase 1
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import re
import time
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.clients.deputados_client import DeputadosClient
from src.clients.tse_client import TSEClient
from cli.modules.database_manager import DatabaseManager

# Import enhanced logger
try:
    from cli.modules.enhanced_logger import enhanced_logger
except:
    # Fallback if enhanced logger not available
    class DummyLogger:
        def log_processing(self, *args, **kwargs): pass
        def log_api_call(self, *args, **kwargs): pass
        def log_data_issue(self, *args, **kwargs): pass
        def save_session_metrics(self): pass
    enhanced_logger = DummyLogger()


class PoliticianPopulator:
    """
    Populates the unified_politicians table with complete field mapping
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.deputados_client = DeputadosClient()
        self.tse_client = TSEClient()

    def populate(self, limit: Optional[int] = None,
                start_id: Optional[int] = None,
                active_only: bool = True) -> List[int]:
        """
        Populate unified_politicians table

        Args:
            limit: Maximum number of politicians to process
            start_id: Start from specific deputy ID
            active_only: Only process active deputies

        Returns:
            List of created politician IDs
        """
        print("👥 POLITICIAN POPULATION WORKFLOW")
        print("=" * 50)
        print("Following DATA_POPULATION_GUIDE.md Phase 1 strategy")

        enhanced_logger.log_processing("politician_population", "session", "started",
                                      {"limit": limit, "start_id": start_id, "active_only": active_only})
        print(f"Active only: {active_only}")
        if limit:
            print(f"Limit: {limit}")
        if start_id:
            print(f"Starting from ID: {start_id}")
        print()

        # Phase 1: Get all current deputies from Deputados API
        print("📋 PHASE 1: Discovering deputies from Câmara API")
        api_start = time.time()
        deputies_list = self.deputados_client.get_all_deputies(active_only=active_only)
        api_time = time.time() - api_start
        enhanced_logger.log_api_call("Deputados", "get_all_deputies", "success", api_time,
                                   {"active_only": active_only, "count": len(deputies_list)})
        print(f"Found {len(deputies_list)} deputies")

        if limit:
            deputies_list = deputies_list[:limit]
            print(f"Limited to {len(deputies_list)} deputies")

        if start_id:
            deputies_list = [d for d in deputies_list if d['id'] >= start_id]
            print(f"Filtered to {len(deputies_list)} deputies from ID {start_id}")

        created_politician_ids = []
        processed = 0
        skipped = 0
        errors = 0

        for deputy in deputies_list:
            try:
                deputy_id = deputy['id']
                print(f"\n👤 Processing deputy {deputy_id}: {deputy['nome']}")

                # Check if already exists
                existing_id = self._check_existing_politician(deputy_id)
                if existing_id:
                    print(f"  ⏭️ Already exists as politician {existing_id}")
                    enhanced_logger.log_processing("politician", deputy_id, "warning",
                                                  {"reason": "already_exists", "existing_id": existing_id})
                    created_politician_ids.append(existing_id)
                    skipped += 1
                    continue

                # Phase 2: Get detailed deputy profile
                print("  📊 Fetching detailed profile...")
                politician_record = self._build_politician_record(deputy_id)

                if politician_record:
                    # Phase 4: Insert into database
                    politician_id = self._insert_politician(politician_record)
                    if politician_id:
                        created_politician_ids.append(politician_id)
                        processed += 1
                        print(f"  ✅ Created politician {politician_id}")
                        enhanced_logger.log_processing("politician", deputy_id, "success",
                                                      {"politician_id": politician_id, "name": deputy['nome']})
                    else:
                        errors += 1
                        print(f"  ❌ Failed to insert politician")
                        enhanced_logger.log_processing("politician", deputy_id, "error",
                                                      {"reason": "insert_failed", "name": deputy['nome']})
                else:
                    errors += 1
                    print(f"  ❌ Failed to build politician record")
                    enhanced_logger.log_processing("politician", deputy_id, "error",
                                                  {"reason": "build_record_failed", "name": deputy['nome']})

                # Rate limiting: small delay between politicians to avoid API bans
                if processed % 10 == 0 and processed > 0:
                    print(f"  ⏸️ Rate limiting: processed {processed}, pausing 2 seconds...")
                    time.sleep(2)
                else:
                    time.sleep(0.5)  # Small delay between each politician

            except Exception as e:
                errors += 1
                print(f"  ❌ Error processing deputy {deputy_id}: {e}")
                enhanced_logger.log_processing("politician", deputy_id, "error",
                                              {"reason": "exception", "error": str(e)})
                continue

        # Summary
        print("\n" + "=" * 50)
        print("📊 POLITICIAN POPULATION SUMMARY")
        print(f"Processed: {processed}")
        print(f"Skipped (existing): {skipped}")
        print(f"Errors: {errors}")
        print(f"Total politicians in database: {len(created_politician_ids)}")
        print("=" * 50)

        enhanced_logger.log_processing("politician_population", "session", "completed",
                                      {"processed": processed, "skipped": skipped, "errors": errors,
                                       "total_created": len(created_politician_ids)})
        enhanced_logger.save_session_metrics()
        return created_politician_ids

    def _check_existing_politician(self, deputy_id: int) -> Optional[int]:
        """Check if politician already exists by deputy_id"""
        query = "SELECT id FROM unified_politicians WHERE deputy_id = ?"
        result = self.db.execute_query(query, (deputy_id,))
        return result[0]['id'] if result else None

    def _build_politician_record(self, deputy_id: int) -> Optional[Dict[str, Any]]:
        """
        Build complete politician record from deputados and TSE data
        Implements Phase 2-3 from DATA_POPULATION_GUIDE.md
        """
        try:
            # Phase 2: Detailed deputy data
            deputy_detail = self.deputados_client.get_deputy_details(deputy_id)
            if not deputy_detail:
                print("    ❌ No deputy details found")
                return None

            deputy_status = deputy_detail.get('ultimoStatus', {})
            cpf = deputy_detail.get('cpf')

            print(f"    ✓ Deputy details: {deputy_detail.get('nomeCivil')}")
            print(f"    ✓ CPF: {cpf}")

            # Phase 3: TSE correlation (multiple elections)
            tse_records = []
            most_recent_tse = None

            if cpf and self.deputados_client.validate_cpf(cpf):
                print("    🔍 Searching TSE records by CPF...")
                tse_records = self._find_tse_candidate_by_cpf(cpf)
                if tse_records:
                    most_recent_tse = self._get_most_recent_election(tse_records)
                    print(f"    ✓ Found {len(tse_records)} TSE records")
                    if most_recent_tse:
                        print(f"    ✓ Most recent election: {most_recent_tse.get('ano_eleicao')}")
                else:
                    print("    ⚠️ No TSE records found")
            else:
                print("    ⚠️ Invalid or missing CPF, skipping TSE correlation")

            # Phase 4: Field mapping
            politician_record = self._map_politician_fields(
                deputy_detail, deputy_status, most_recent_tse, tse_records
            )

            return politician_record

        except Exception as e:
            print(f"    ❌ Error building politician record: {e}")
            return None

    def _find_tse_candidate_by_cpf(self, cpf: str) -> List[Dict[str, Any]]:
        """Find TSE candidate records by CPF across multiple elections"""
        try:
            # Get available election years from packages
            packages = self.tse_client.get_packages()
            candidate_packages = [p for p in packages if 'candidatos-' in p and p.split('-')[-1].isdigit()]

            # Focus on most recent election years for efficiency
            recent_years = []
            for package in candidate_packages:
                year = int(package.split('-')[-1])
                if year >= 2020:  # Only last 2 election cycles for speed
                    recent_years.append(year)

            recent_years = sorted(set(recent_years), reverse=True)
            print(f"      → Searching {len(recent_years)} election years: {recent_years}")

            all_records = []

            for year in recent_years:
                try:
                    print(f"        → Searching {year}...")

                    # Use the TSE client's get_candidate_data method
                    candidates = self.tse_client.get_candidate_data(year)

                    if candidates:
                        matching_records = [
                            candidate for candidate in candidates
                            if candidate.get('nr_cpf_candidato') == cpf or candidate.get('cpf') == cpf
                        ]

                        if matching_records:
                            print(f"          ✓ Found {len(matching_records)} records in {year}")
                            # Year info is already in election_year field from TSE client
                            all_records.extend(matching_records)
                        else:
                            print(f"          - No matches in {year}")
                    else:
                        print(f"          - No data available for {year}")

                except Exception as e:
                    print(f"        ⚠️ Error searching {year}: {e}")
                    continue

            print(f"      ✓ Total TSE records found: {len(all_records)}")
            return all_records

        except Exception as e:
            print(f"    ❌ Error in TSE search: {e}")
            return []

    def _get_most_recent_election(self, tse_records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the most recent TSE election record"""
        if not tse_records:
            return None

        # Sort by election year descending
        sorted_records = sorted(
            tse_records,
            key=lambda x: int(x.get('ano_eleicao', 0)),
            reverse=True
        )

        return sorted_records[0]

    def _map_politician_fields(self, deputy_detail: Dict[str, Any],
                             deputy_status: Dict[str, Any],
                             most_recent_tse: Optional[Dict[str, Any]],
                             all_tse_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map all fields from deputados and TSE to unified_politicians schema
        Complete 100% field mapping as specified in UNIFIED_SQL_SCHEMA_FINAL.sql
        """
        # Universal identifiers
        cpf = deputy_detail.get('cpf')
        nome_civil = deputy_detail.get('nomeCivil', '')

        record = {
            # UNIVERSAL IDENTIFIERS
            'cpf': cpf,
            'nome_civil': nome_civil,
            'nome_completo_normalizado': self.deputados_client.normalize_name(nome_civil),

            # SOURCE SYSTEM LINKS
            'deputy_id': deputy_detail.get('id'),
            'sq_candidato_current': most_recent_tse.get('sq_candidato') if most_recent_tse else None,
            'deputy_active': deputy_status.get('situacao') == 'Exercício',

            # DEPUTADOS CORE IDENTITY DATA
            'nome_eleitoral': deputy_status.get('nomeEleitoral'),
            'url_foto': deputy_status.get('urlFoto'),
            'data_falecimento': self._parse_date(deputy_detail.get('dataFalecimento')),

            # TSE CORE IDENTITY DATA
            'electoral_number': most_recent_tse.get('nr_candidato') if most_recent_tse else None,
            'nr_titulo_eleitoral': most_recent_tse.get('nr_titulo_eleitoral_candidato') if most_recent_tse else None,
            'nome_urna_candidato': most_recent_tse.get('nm_urna_candidato') if most_recent_tse else None,
            'nome_social_candidato': most_recent_tse.get('nm_social_candidato') if most_recent_tse else None,

            # CURRENT POLITICAL STATUS (Deputados Primary)
            'current_party': deputy_status.get('siglaPartido'),
            'current_state': deputy_status.get('siglaUf'),
            'current_legislature': deputy_status.get('idLegislatura'),
            'situacao': deputy_status.get('situacao'),
            'condicao_eleitoral': deputy_status.get('condicaoEleitoral'),

            # TSE POLITICAL DETAILS
            'nr_partido': int(most_recent_tse.get('nr_partido', 0)) if most_recent_tse and most_recent_tse.get('nr_partido') else None,
            'nm_partido': most_recent_tse.get('nm_partido') if most_recent_tse else None,
            'nr_federacao': int(most_recent_tse.get('nr_federacao', 0)) if most_recent_tse and most_recent_tse.get('nr_federacao') else None,
            'sg_federacao': most_recent_tse.get('sg_federacao') if most_recent_tse else None,
            'current_position': most_recent_tse.get('ds_cargo') if most_recent_tse else None,

            # TSE ELECTORAL STATUS
            'cd_situacao_candidatura': int(most_recent_tse.get('cd_situacao_candidatura', 0)) if most_recent_tse and most_recent_tse.get('cd_situacao_candidatura') else None,
            'ds_situacao_candidatura': most_recent_tse.get('ds_situacao_candidatura') if most_recent_tse else None,
            'cd_sit_tot_turno': int(most_recent_tse.get('cd_sit_tot_turno', 0)) if most_recent_tse and most_recent_tse.get('cd_sit_tot_turno') else None,
            'ds_sit_tot_turno': most_recent_tse.get('ds_sit_tot_turno') if most_recent_tse else None,

            # DEMOGRAPHICS
            'birth_date': self._parse_date(deputy_detail.get('dataNascimento')) or self._parse_date(most_recent_tse.get('dt_nascimento')) if most_recent_tse else None,
            'birth_state': deputy_detail.get('ufNascimento') or (most_recent_tse.get('sg_uf_nascimento') if most_recent_tse else None),
            'birth_municipality': deputy_detail.get('municipioNascimento'),

            'gender': deputy_detail.get('sexo') or (most_recent_tse.get('ds_genero') if most_recent_tse else None),
            'gender_code': int(most_recent_tse.get('cd_genero', 0)) if most_recent_tse and most_recent_tse.get('cd_genero') else None,

            'education_level': deputy_detail.get('escolaridade') or (most_recent_tse.get('ds_grau_instrucao') if most_recent_tse else None),
            'education_code': int(most_recent_tse.get('cd_grau_instrucao', 0)) if most_recent_tse and most_recent_tse.get('cd_grau_instrucao') else None,

            'occupation': most_recent_tse.get('ds_ocupacao') if most_recent_tse else None,
            'occupation_code': int(most_recent_tse.get('cd_ocupacao', 0)) if most_recent_tse and most_recent_tse.get('cd_ocupacao') else None,

            'marital_status': most_recent_tse.get('ds_estado_civil') if most_recent_tse else None,
            'marital_status_code': int(most_recent_tse.get('cd_estado_civil', 0)) if most_recent_tse and most_recent_tse.get('cd_estado_civil') else None,

            'race_color': most_recent_tse.get('ds_cor_raca') if most_recent_tse else None,
            'race_color_code': int(most_recent_tse.get('cd_cor_raca', 0)) if most_recent_tse and most_recent_tse.get('cd_cor_raca') else None,

            # GEOGRAPHIC DETAILS
            'sg_ue': most_recent_tse.get('sg_ue') if most_recent_tse else None,
            'nm_ue': most_recent_tse.get('nm_ue') if most_recent_tse else None,

            # CONTACT INFORMATION
            'email': deputy_status.get('email') or deputy_detail.get('email') or (most_recent_tse.get('ds_email') if most_recent_tse else None),
            'phone': deputy_status.get('gabinete', {}).get('telefone'),
            'website': deputy_detail.get('urlWebsite'),
            'social_networks': json.dumps(deputy_detail.get('redeSocial', [])) if deputy_detail.get('redeSocial') else None,

            # OFFICE DETAILS
            'office_building': deputy_status.get('gabinete', {}).get('predio'),
            'office_room': deputy_status.get('gabinete', {}).get('sala'),
            'office_floor': deputy_status.get('gabinete', {}).get('andar'),
            'office_phone': deputy_status.get('gabinete', {}).get('telefone'),
            'office_email': deputy_status.get('gabinete', {}).get('email'),

            # CAREER TIMELINE (Basic aggregation)
            'first_election_year': min(int(r.get('ano_eleicao', 9999)) for r in all_tse_records) if all_tse_records else None,
            'last_election_year': max(int(r.get('ano_eleicao', 0)) for r in all_tse_records) if all_tse_records else None,
            'total_elections': len(all_tse_records),
            'first_mandate_year': min(int(r.get('ano_eleicao', 0)) for r in all_tse_records if r.get('ano_eleicao')) if all_tse_records else None,

            # DATA VALIDATION FLAGS
            'cpf_validated': bool(cpf and self.deputados_client.validate_cpf(cpf)),
            'tse_linked': bool(most_recent_tse),
            'last_updated_date': date.today().isoformat(),

            # METADATA
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        return record

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None

        try:
            # Handle various date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def _insert_politician(self, record: Dict[str, Any]) -> Optional[int]:
        """Insert politician record into database"""
        try:
            # Use the database manager's bulk_insert_records method
            result = self.db.bulk_insert_records('unified_politicians', [record])

            if result > 0:
                # For PostgreSQL, we need to get the ID differently
                if self.db.db_type == 'postgresql':
                    # Get the most recently inserted politician
                    query = "SELECT id FROM unified_politicians WHERE cpf = ? ORDER BY id DESC LIMIT 1"
                    result = self.db.execute_query(query, (record['cpf'],))
                    return result[0]['id'] if result else None
                else:
                    # For SQLite, we could use lastrowid, but this is more consistent
                    query = "SELECT id FROM unified_politicians WHERE cpf = ? ORDER BY id DESC LIMIT 1"
                    result = self.db.execute_query(query, (record['cpf'],))
                    return result[0]['id'] if result else None

            return None

        except Exception as e:
            print(f"    ❌ Database insert error: {e}")
            return None