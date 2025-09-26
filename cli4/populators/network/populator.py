"""
CLI4 Network Populator
Populate unified_political_networks table with complete political network memberships
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker
from src.clients.deputados_client import DeputadosClient
from src.clients.tse_client import TSEClient


class NetworkPopulator:
    """Populate unified political networks table"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.deputados_client = DeputadosClient()
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None) -> int:
        """Main population method"""

        print("🤝 UNIFIED POLITICAL NETWORKS POPULATION")
        print("=" * 60)
        print("Committee, front, coalition, and federation memberships")
        print()

        # Check dependencies
        DependencyChecker.print_dependency_warning(
            required_steps=["politicians"],
            current_step="NETWORK RECORDS POPULATION"
        )

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = database.execute_query(
                "SELECT id, deputy_id, cpf, nome_civil, current_state FROM unified_politicians"
            )

        print(f"👥 Processing {len(politicians)} politicians")
        print()

        total_records = 0
        processed_politicians = 0

        for politician in politicians:
            try:
                print(f"🏛️ [{processed_politicians + 1}/{len(politicians)}] Processing {politician['nome_civil']}")

                politician_networks = []

                # 1. Fetch committees (if deputy)
                if politician['deputy_id']:
                    committees = self._fetch_committees(politician['deputy_id'])
                    politician_networks.extend(
                        self._build_committee_records(politician['id'], committees)
                    )

                # 2. Fetch parliamentary fronts (if deputy)
                if politician['deputy_id']:
                    fronts = self._fetch_parliamentary_fronts(politician['deputy_id'])
                    politician_networks.extend(
                        self._build_front_records(politician['id'], fronts)
                    )

                # 3. Fetch coalitions/federations from TSE
                if politician['cpf'] and politician['current_state']:
                    coalitions = self._fetch_tse_coalitions(politician['cpf'], politician['current_state'])
                    politician_networks.extend(
                        self._build_coalition_records(politician['id'], coalitions)
                    )

                # 4. Insert records immediately (memory-efficient)
                if politician_networks:
                    inserted = self._insert_network_records(politician_networks)
                    total_records += inserted
                    print(f"  ✅ Inserted {inserted} network records")
                else:
                    print(f"  ⚠️ No network memberships found")

                processed_politicians += 1

                self.logger.log_processing(
                    'network', str(politician['id']), 'success',
                    {'networks_found': len(politician_networks)}
                )

            except Exception as e:
                print(f"  ❌ Error: {e}")
                self.logger.log_processing(
                    'network', str(politician['id']), 'error',
                    {'error': str(e)}
                )
                continue

        print(f"\n✅ Network population completed")
        print(f"📊 {total_records} network records inserted")
        print(f"👥 {processed_politicians}/{len(politicians)} politicians processed")

        return total_records

    def _fetch_committees(self, deputy_id: int) -> List[Dict]:
        """Fetch committee memberships with rate limiting"""
        wait_time = self.rate_limiter.wait_if_needed('camara')

        try:
            start_time = time.time()
            committees = self.deputados_client.get_deputy_committees(deputy_id)
            api_time = time.time() - start_time

            self.logger.log_api_call('camara', f'committees/{deputy_id}', 'success', api_time)
            print(f"    📋 Found {len(committees)} committee memberships")
            return committees
        except Exception as e:
            self.logger.log_api_call('camara', f'committees/{deputy_id}', 'error', 0)
            print(f"    ❌ Committee fetch failed: {e}")
            return []

    def _fetch_parliamentary_fronts(self, deputy_id: int) -> List[Dict]:
        """Fetch parliamentary front memberships with rate limiting"""
        wait_time = self.rate_limiter.wait_if_needed('camara')

        try:
            start_time = time.time()
            fronts = self.deputados_client.get_deputy_fronts(deputy_id)
            api_time = time.time() - start_time

            self.logger.log_api_call('camara', f'fronts/{deputy_id}', 'success', api_time)
            print(f"    🏛️ Found {len(fronts)} parliamentary front memberships")
            return fronts
        except Exception as e:
            self.logger.log_api_call('camara', f'fronts/{deputy_id}', 'error', 0)
            print(f"    ❌ Parliamentary front fetch failed: {e}")
            return []

    def _fetch_tse_coalitions(self, cpf: str, state: str) -> List[Dict]:
        """Fetch TSE coalition/federation data"""
        wait_time = self.rate_limiter.wait_if_needed('tse')

        try:
            start_time = time.time()

            # Check recent elections (2018, 2020, 2022, 2024)
            election_years = [2024, 2022, 2020, 2018]
            coalitions = []

            for year in election_years:
                try:
                    # Get candidate data for politician's state
                    candidates = self.tse_client.get_candidate_data(year, state)

                    if candidates:
                        # Look for politician by CPF
                        matches = [c for c in candidates if c.get('nr_cpf_candidato') == cpf]

                        for match in matches:
                            # Check for federation data
                            if (match.get('nr_federacao') and
                                match.get('nr_federacao') != '-1' and
                                match.get('sg_federacao') and
                                match.get('sg_federacao').upper() != '#NULO'):

                                coalitions.append({
                                    'type': 'FEDERATION',
                                    'id': match.get('nr_federacao'),
                                    'name': match.get('sg_federacao'),
                                    'year': year,
                                    'party': match.get('sg_partido')
                                })

                except Exception:
                    # Skip individual years that fail
                    continue

            api_time = time.time() - start_time
            self.logger.log_api_call('tse', f'coalitions/{cpf}', 'success', api_time)
            print(f"    🗳️ Found {len(coalitions)} TSE coalition/federation records")
            return coalitions

        except Exception as e:
            print(f"    ❌ TSE coalition fetch failed: {e}")
            return []

    def _build_committee_records(self, politician_id: int, committees: List[Dict]) -> List[Dict]:
        """Build committee network records"""
        records = []

        for committee in committees:
            record = {
                'politician_id': politician_id,
                'network_type': 'COMMITTEE',
                'network_id': str(committee.get('idOrgao', '')),
                'network_name': committee.get('nomeOrgao', ''),
                'role': committee.get('titulo'),
                'start_date': self._parse_date(committee.get('dataInicio')),
                'end_date': self._parse_date(committee.get('dataFim')),
                'year': self._extract_year(committee.get('dataInicio')) or datetime.now().year,
                'source_system': 'DEPUTADOS'
            }
            records.append(record)

        return records

    def _build_front_records(self, politician_id: int, fronts: List[Dict]) -> List[Dict]:
        """Build parliamentary front network records"""
        records = []

        for front in fronts:
            record = {
                'politician_id': politician_id,
                'network_type': 'PARLIAMENTARY_FRONT',
                'network_id': str(front.get('id', '')),
                'network_name': front.get('titulo', ''),
                'role': None,  # Parliamentary fronts don't have specific roles
                'start_date': None,
                'end_date': None,
                'year': datetime.now().year,  # Use current year for fronts
                'legislature_id': front.get('idLegislatura'),
                'source_system': 'DEPUTADOS'
            }
            records.append(record)

        return records

    def _build_coalition_records(self, politician_id: int, coalitions: List[Dict]) -> List[Dict]:
        """Build coalition/federation network records"""
        records = []

        for coalition in coalitions:
            record = {
                'politician_id': politician_id,
                'network_type': coalition['type'],  # FEDERATION
                'network_id': str(coalition.get('id', '')),
                'network_name': coalition.get('name', ''),
                'role': None,  # TSE doesn't provide role info
                'start_date': None,
                'end_date': None,
                'year': coalition.get('year'),
                'election_year': coalition.get('year'),
                'source_system': 'TSE'
            }
            records.append(record)

        return records

    def _validate_field_lengths(self, record: Dict) -> Dict:
        """Validate and truncate fields that may exceed database limits"""
        # Field length limits based on updated schema
        field_limits = {
            'network_name': 500,
            'role': 400,
            'network_id': 50,
            'network_type': 50
        }

        validated_record = record.copy()

        for field, max_length in field_limits.items():
            if field in validated_record and validated_record[field]:
                value = str(validated_record[field])
                original_length = len(value)

                if original_length > max_length:
                    # LOUD WARNING for field truncation
                    print(f"    ⚠️⚠️⚠️ TRUNCATING {field.upper()}: {original_length} chars → {max_length} chars ⚠️⚠️⚠️")
                    print(f"       🔴 ORIGINAL FULL VALUE: {value}")
                    print(f"       ✂️  WILL BE TRUNCATED TO: {self._smart_truncate(value, max_length)}")
                    print(f"       📊 Politician ID: {record.get('politician_id', 'unknown')}")
                    print(f"       🏛️  Network Type: {record.get('network_type', 'unknown')}")
                    print()  # Empty line for visibility

                    # Log to structured logger with FULL original value
                    if hasattr(self, 'logger'):
                        self.logger.log_processing(
                            'network_field_truncation',
                            f"politician_{record.get('politician_id', 'unknown')}",
                            'warning',
                            {
                                'field': field,
                                'original_length': original_length,
                                'limit': max_length,
                                'full_original_value': value,  # FULL VALUE LOGGED
                                'truncated_value': self._smart_truncate(value, max_length),
                                'network_type': record.get('network_type'),
                                'politician_id': record.get('politician_id'),
                                'network_id': record.get('network_id')
                            }
                        )

                    # Smart truncation preserving meaningful content
                    validated_record[field] = self._smart_truncate(value, max_length)

        return validated_record

    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Smart truncation that preserves meaningful content"""
        if len(text) <= max_length:
            return text

        # Reserve 3 characters for ellipsis
        truncate_length = max_length - 3

        # Try to break at word boundary if possible (within last 20 chars)
        if truncate_length > 20:
            last_space = text.rfind(' ', max(0, truncate_length - 20), truncate_length)
            if last_space > truncate_length - 20:
                truncate_length = last_space

        return text[:truncate_length] + '...'

    def _insert_network_records(self, records: List[Dict]) -> int:
        """Insert network records into database with field validation"""
        if not records:
            return 0

        inserted_count = 0

        for record in records:
            try:
                # Validate and truncate fields before insertion
                validated_record = self._validate_field_lengths(record)

                # Build INSERT query for each record
                fields = []
                values = []
                placeholders = []

                for field, value in validated_record.items():
                    if value is not None:
                        fields.append(field)
                        placeholders.append('%s')
                        values.append(value)

                sql = f"""
                    INSERT INTO unified_political_networks ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (politician_id, network_type, network_id) DO NOTHING
                """

                result = database.execute_update(sql, tuple(values))
                if result > 0:
                    inserted_count += 1

            except Exception as e:
                print(f"    ⚠️ Database insert error for record: {e}")

                # Enhanced error logging with field details
                if hasattr(self, 'logger'):
                    self.logger.log_processing(
                        'network_insertion',
                        f"politician_{record.get('politician_id', 'unknown')}",
                        'error',
                        {
                            'error': str(e),
                            'network_type': record.get('network_type'),
                            'network_name_length': len(str(record.get('network_name', ''))),
                            'role_length': len(str(record.get('role', '') or ''))
                        }
                    )
                continue

        return inserted_count

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None

        try:
            # Handle various date formats
            if 'T' in date_str:
                date_part = date_str.split('T')[0]
            else:
                date_part = date_str

            # Validate format
            datetime.strptime(date_part, '%Y-%m-%d')
            return date_part
        except:
            return None

    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string"""
        if not date_str:
            return None

        try:
            if 'T' in date_str:
                date_part = date_str.split('T')[0]
            else:
                date_part = date_str
            return datetime.strptime(date_part, '%Y-%m-%d').year
        except:
            return None

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs"""
        if not politician_ids:
            return []

        placeholders = ', '.join(['%s'] * len(politician_ids))
        query = f"""
            SELECT id, deputy_id, cpf, nome_civil, current_state
            FROM unified_politicians
            WHERE id IN ({placeholders})
        """

        return database.execute_query(query, tuple(politician_ids))