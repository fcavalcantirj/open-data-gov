"""
CLI4 Career Populator
Populate politician_career_history table with external mandates from Deputados API
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker
from src.clients.deputados_client import DeputadosClient


class CareerPopulator:
    """Populate politician career history table with external mandates"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.deputados_client = DeputadosClient()

    def populate(self, politician_ids: Optional[List[int]] = None) -> int:
        """Main population method"""

        print("📋 POLITICIAN CAREER HISTORY POPULATION")
        print("=" * 60)
        print("External mandates and political career tracking")
        print()

        # Check dependencies
        DependencyChecker.print_dependency_warning(
            required_steps=["politicians"],
            current_step="CAREER HISTORY POPULATION"
        )

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = database.execute_query(
                "SELECT id, deputy_id, cpf, nome_civil FROM unified_politicians WHERE deputy_id IS NOT NULL"
            )

        print(f"👥 Processing {len(politicians)} politicians with deputy_id")
        print()

        total_records = 0
        processed_politicians = 0

        for politician in politicians:
            try:
                print(f"🏛️ [{processed_politicians + 1}/{len(politicians)}] Processing {politician['nome_civil']}")

                politician_career_records = []

                # Fetch external mandates
                if politician['deputy_id']:
                    mandates = self._fetch_external_mandates(politician['deputy_id'])
                    politician_career_records.extend(
                        self._build_career_records(politician['id'], mandates)
                    )

                # Insert records immediately (memory-efficient)
                if politician_career_records:
                    inserted = self._insert_career_records(politician_career_records)
                    total_records += inserted
                    print(f"  ✅ Inserted {inserted} career records")
                else:
                    print(f"  ⚠️ No external mandates found")

                processed_politicians += 1

                self.logger.log_processing(
                    'career', str(politician['id']), 'success',
                    {'career_records_found': len(politician_career_records)}
                )

            except Exception as e:
                print(f"  ❌ Error: {e}")
                self.logger.log_processing(
                    'career', str(politician['id']), 'error',
                    {'error': str(e)}
                )
                continue

        print(f"\n✅ Career population completed")
        print(f"📊 {total_records} career records inserted")
        print(f"👥 {processed_politicians}/{len(politicians)} politicians processed")

        return total_records

    def _fetch_external_mandates(self, deputy_id: int) -> List[Dict]:
        """Fetch external mandates with rate limiting"""
        wait_time = self.rate_limiter.wait_if_needed('camara')

        try:
            start_time = time.time()
            mandates = self.deputados_client.get_deputy_external_mandates(deputy_id)
            api_time = time.time() - start_time

            self.logger.log_api_call('camara', f'mandatosExternos/{deputy_id}', 'success', api_time)
            print(f"    📋 Found {len(mandates)} external mandates")
            return mandates
        except Exception as e:
            self.logger.log_api_call('camara', f'mandatosExternos/{deputy_id}', 'error', 0)
            print(f"    ❌ External mandates fetch failed: {e}")
            return []

    def _build_career_records(self, politician_id: int, mandates: List[Dict]) -> List[Dict]:
        """Build career records from external mandates"""
        records = []

        for mandate in mandates:
            # Calculate mandate type based on office name
            office_name = mandate.get('cargo', '')
            mandate_type = self._categorize_mandate_type(office_name)

            # Build approximate dates from years
            start_date = self._build_approximate_date(mandate.get('anoInicio'), is_start=True)
            end_date = self._build_approximate_date(mandate.get('anoFim'), is_start=False)

            record = {
                'politician_id': politician_id,
                'mandate_type': mandate_type,
                'office_name': office_name,
                'entity_name': mandate.get('municipio'),  # Municipality for local mandates
                'state': mandate.get('siglaUf'),
                'municipality': mandate.get('municipio'),
                'start_year': self._parse_year(mandate.get('anoInicio')),
                'end_year': self._parse_year(mandate.get('anoFim')),
                'start_date': start_date,
                'end_date': end_date,
                'party_at_election': mandate.get('siglaPartidoEleicao'),
                'source_system': 'DEPUTADOS',
                'created_at': datetime.now()
            }
            records.append(record)

        return records

    def _categorize_mandate_type(self, office_name: str) -> str:
        """Categorize mandate type based on office name"""
        if not office_name:
            return 'OTHER'

        office_lower = office_name.lower()

        # Municipal mandates
        if any(term in office_lower for term in ['prefeito', 'vereador']):
            return 'MUNICIPAL'

        # State mandates
        elif any(term in office_lower for term in ['deputado estadual', 'governador', 'vice-governador']):
            return 'STATE'

        # Federal mandates
        elif any(term in office_lower for term in ['deputado federal', 'senador', 'presidente', 'ministro']):
            return 'FEDERAL'

        # Default
        else:
            return 'OTHER'

    def _build_approximate_date(self, year_str: str, is_start: bool) -> Optional[str]:
        """Build approximate date from year string"""
        if not year_str:
            return None

        try:
            year = int(year_str)
            if is_start:
                return f"{year}-01-01"  # Start of year
            else:
                return f"{year}-12-31"  # End of year
        except (ValueError, TypeError):
            return None

    def _parse_year(self, year_str: str) -> Optional[int]:
        """Parse year from string"""
        if not year_str:
            return None

        try:
            return int(year_str)
        except (ValueError, TypeError):
            return None

    def _insert_career_records(self, records: List[Dict]) -> int:
        """Insert career records into database"""
        if not records:
            return 0

        inserted_count = 0

        for record in records:
            try:
                # Build INSERT query for each record
                fields = []
                values = []
                placeholders = []

                for field, value in record.items():
                    if value is not None:
                        fields.append(field)
                        placeholders.append('%s')
                        values.append(value)

                sql = f"""
                    INSERT INTO politician_career_history ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (politician_id, office_name, start_year, state, municipality) DO NOTHING
                """

                result = database.execute_update(sql, tuple(values))
                if result > 0:
                    inserted_count += 1

            except Exception as e:
                print(f"    ⚠️ Database insert error for record: {e}")

                # Enhanced error logging
                if hasattr(self, 'logger'):
                    self.logger.log_processing(
                        'career_insertion',
                        f"politician_{record.get('politician_id', 'unknown')}",
                        'error',
                        {
                            'error': str(e),
                            'office_name': record.get('office_name'),
                            'start_year': record.get('start_year')
                        }
                    )
                continue

        return inserted_count

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs"""
        if not politician_ids:
            return []

        placeholders = ', '.join(['%s'] * len(politician_ids))
        query = f"""
            SELECT id, deputy_id, cpf, nome_civil
            FROM unified_politicians
            WHERE id IN ({placeholders})
            AND deputy_id IS NOT NULL
        """

        return database.execute_query(query, tuple(politician_ids))