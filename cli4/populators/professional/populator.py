"""
CLI4 Professional Populator
Populate politician_professional_background table with Deputados professional data
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker
from src.clients.deputados_client import DeputadosClient


class ProfessionalPopulator:
    """Populate professional background table with Deputados professional data"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.deputados_client = DeputadosClient()

    def populate(self, politician_ids: Optional[List[int]] = None) -> int:
        """Main population method"""

        print("💼 PROFESSIONAL BACKGROUND POPULATION")
        print("=" * 60)
        print("Deputados professional background with career analysis")
        print()

        # Check dependencies
        DependencyChecker.print_dependency_warning(
            required_steps=["politicians"],
            current_step="PROFESSIONAL BACKGROUND POPULATION"
        )

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            # Get politicians with deputy_id for API correlation
            politicians = database.execute_query("""
                SELECT id, deputy_id, nome_civil
                FROM unified_politicians
                WHERE deputy_id IS NOT NULL
            """)

        if not politicians:
            print("⚠️ No politicians with deputy_id found for professional correlation")
            return 0

        print(f"👥 Processing {len(politicians)} politicians with deputy data")
        print()

        total_records = 0
        processed_politicians = 0

        for politician in politicians:
            try:
                deputy_id = politician['deputy_id']
                politician_id = politician['id']
                nome_civil = politician['nome_civil']

                print(f"  🔄 Processing {nome_civil} (deputy_id: {deputy_id})")

                # Fetch professional data with rate limiting
                professions = self._fetch_professions(deputy_id)
                occupations = self._fetch_occupations(deputy_id)

                if not professions and not occupations:
                    print(f"    ⚠️ No professional data found")
                    continue

                # Build professional records
                professional_records = []

                # Process professions
                for profession in professions:
                    record = self._build_profession_record(politician_id, profession)
                    if record:
                        professional_records.append(record)

                # Process occupations
                for occupation in occupations:
                    record = self._build_occupation_record(politician_id, occupation)
                    if record:
                        professional_records.append(record)

                # Insert records
                if professional_records:
                    inserted = self._insert_professional_records(professional_records)
                    total_records += inserted
                    print(f"    ✅ {inserted} professional records inserted ({len(professions)} prof, {len(occupations)} occ)")
                else:
                    print(f"    ⚠️ No valid professional records to insert")

                processed_politicians += 1

                self.logger.log_processing(
                    'professional', str(politician_id), 'success',
                    {'professions_found': len(professions), 'occupations_found': len(occupations)}
                )

            except Exception as e:
                print(f"    ❌ Error processing {politician.get('nome_civil', 'Unknown')}: {e}")
                self.logger.log_processing(
                    'professional', str(politician.get('id', 'unknown')), 'error',
                    {'error': str(e)}
                )
                continue

        print(f"\n✅ Professional population completed")
        print(f"📊 {total_records} professional records inserted")
        print(f"👥 {processed_politicians}/{len(politicians)} politicians processed")

        return total_records

    def _fetch_professions(self, deputy_id: int) -> List[Dict]:
        """Fetch profession data with rate limiting"""
        wait_time = self.rate_limiter.wait_if_needed('deputados')

        try:
            start_time = time.time()
            professions = self.deputados_client.get_deputy_professions(deputy_id)
            api_time = time.time() - start_time

            self.logger.log_api_call('deputados', f'professions/{deputy_id}', 'success', api_time)
            return professions
        except Exception as e:
            self.logger.log_api_call('deputados', f'professions/{deputy_id}', 'error', 0)
            print(f"      ❌ Professions fetch failed: {e}")
            return []

    def _fetch_occupations(self, deputy_id: int) -> List[Dict]:
        """Fetch occupation data with rate limiting"""
        wait_time = self.rate_limiter.wait_if_needed('deputados')

        try:
            start_time = time.time()
            occupations = self.deputados_client.get_deputy_occupations(deputy_id)
            api_time = time.time() - start_time

            self.logger.log_api_call('deputados', f'occupations/{deputy_id}', 'success', api_time)
            return occupations
        except Exception as e:
            self.logger.log_api_call('deputados', f'occupations/{deputy_id}', 'error', 0)
            print(f"      ❌ Occupations fetch failed: {e}")
            return []

    def _build_profession_record(self, politician_id: int, profession: Dict) -> Optional[Dict]:
        """Build profession record from API data"""
        try:
            # Parse year from dataHora (format: "2018-08-14T16:36")
            year_start = None
            data_hora = profession.get('dataHora', '')
            if data_hora:
                try:
                    year_start = int(data_hora.split('-')[0])
                except:
                    pass

            # Build record following database schema
            record = {
                'politician_id': politician_id,
                'profession_type': 'PROFESSION',
                'profession_code': self._parse_int(profession.get('codTipoProfissao')),
                'profession_name': self._normalize_text(profession.get('titulo', ''), 255),
                'entity_name': None,
                'start_date': None,
                'end_date': None,
                'year_start': year_start,
                'year_end': None,
                'professional_title': None,
                'professional_registry': None,
                'entity_state': None,
                'entity_country': None,
                'is_current': False
            }

            # Only return record if we have essential data
            if record['profession_name']:
                return record

            return None

        except Exception as e:
            print(f"        ⚠️ Error building profession record: {e}")
            return None

    def _build_occupation_record(self, politician_id: int, occupation: Dict) -> Optional[Dict]:
        """Build occupation record from API data"""
        try:
            # Build record following database schema
            record = {
                'politician_id': politician_id,
                'profession_type': 'OCCUPATION',
                'profession_code': None,
                'profession_name': self._normalize_text(occupation.get('titulo', ''), 255),
                'entity_name': self._normalize_entity_name(occupation.get('entidade')),
                'start_date': None,
                'end_date': None,
                'year_start': self._parse_int(occupation.get('anoInicio')),
                'year_end': self._parse_int(occupation.get('anoFim')),
                'professional_title': self._normalize_text(occupation.get('titulo', ''), 255),
                'professional_registry': None,
                'entity_state': self._normalize_text(occupation.get('entidadeUF', ''), 10),
                'entity_country': self._normalize_text(occupation.get('entidadePais', ''), 100),
                'is_current': occupation.get('anoFim') is None
            }

            # Only return record if we have essential data
            if record['profession_name']:
                return record

            return None

        except Exception as e:
            print(f"        ⚠️ Error building occupation record: {e}")
            return None

    def _normalize_text(self, text: str, max_length: int) -> Optional[str]:
        """Normalize and truncate text fields"""
        if not text or not text.strip():
            return None

        # Clean and normalize
        text = text.strip()

        # Smart truncation with word boundaries
        if len(text) <= max_length:
            return text

        # Reserve space for ellipsis
        truncate_length = max_length - 3

        # Try to break at word boundary if possible (within last 20 chars)
        if truncate_length > 20:
            last_space = text.rfind(' ', max(0, truncate_length - 20), truncate_length)
            if last_space > truncate_length - 20:
                truncate_length = last_space

        return text[:truncate_length] + '...'

    def _normalize_entity_name(self, entity_name: str) -> Optional[str]:
        """Normalize entity/company names"""
        if not entity_name or not entity_name.strip():
            return None

        # Basic normalization
        normalized = entity_name.strip()

        # Remove common noise words/patterns
        noise_patterns = ['LTDA.', 'S.A.', 'S/A', 'LTDA', 'ME.', 'EPP.']
        for pattern in noise_patterns:
            if normalized.upper().endswith(pattern):
                normalized = normalized[:-len(pattern)].strip()
                break

        return self._normalize_text(normalized, 255)

    def _parse_int(self, value) -> Optional[int]:
        """Safely parse integer values"""
        if value is None or value == '':
            return None

        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _insert_professional_records(self, records: List[Dict]) -> int:
        """Insert professional records into database with conflict resolution"""
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

                # Use ON CONFLICT DO NOTHING (based on unique constraint)
                sql = f"""
                    INSERT INTO politician_professional_background ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (politician_id, profession_type, profession_name, year_start) DO NOTHING
                    RETURNING id
                """

                result = database.execute_query(sql, tuple(values))
                if result:  # Record was inserted
                    inserted_count += 1

            except Exception as e:
                print(f"      ⚠️ Database insert error: {e}")

                # Enhanced error logging
                if hasattr(self, 'logger'):
                    self.logger.log_processing(
                        'professional_insertion',
                        f"politician_{record.get('politician_id', 'unknown')}",
                        'error',
                        {
                            'error': str(e),
                            'profession_type': record.get('profession_type'),
                            'profession_name': record.get('profession_name')
                        }
                    )
                continue

        return inserted_count

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs with deputy_id data"""
        if not politician_ids:
            return []

        placeholders = ', '.join(['%s'] * len(politician_ids))
        query = f"""
            SELECT id, deputy_id, nome_civil
            FROM unified_politicians
            WHERE id IN ({placeholders}) AND deputy_id IS NOT NULL
        """

        return database.execute_query(query, tuple(politician_ids))