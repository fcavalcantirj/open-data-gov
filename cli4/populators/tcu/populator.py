"""
CLI4 TCU Disqualifications Populator
Populate tcu_disqualifications table with TCU Federal Audit Court data
Essential for corruption detection through CPF cross-referencing
"""

import time
import re
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker


class TCUPopulator:
    """Populate TCU disqualifications table with Federal Audit Court data"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.base_url = "https://contas.tcu.gov.br/ords/condenacao/consulta/inabilitados"

    def populate(self, max_pages: Optional[int] = None,
                 update_existing: bool = False) -> int:
        """Main population method - fetches all TCU disqualifications"""

        print("⚖️  TCU DISQUALIFICATIONS POPULATION")
        print("=" * 60)
        print("Federal Audit Court disqualifications for corruption detection")
        print()

        # Check dependencies - TCU data is independent but critical for cross-referencing
        DependencyChecker.print_dependency_warning(
            required_steps=[],  # No dependencies - TCU data is standalone
            current_step="TCU DISQUALIFICATIONS POPULATION"
        )

        print("🎯 APPROACH: Complete TCU disqualifications database for CPF cross-reference")
        print("   • Fetch ALL disqualifications via pagination")
        print("   • Clean and validate CPF formats for matching")
        print("   • Store in local database with proper indexing")
        print("   • Enable fast cross-referencing with politician CPFs")
        print()

        if not max_pages:
            max_pages = 100  # Reasonable default based on API testing
            print(f"📄 Max pages limit: {max_pages} (prevent runaway)")

        # Track progress
        total_records = 0
        total_pages_processed = 0
        current_offset = 0
        page_size = 25  # TCU API default page size
        has_more = True

        print(f"🚀 Starting TCU disqualifications population...")
        start_time = time.time()

        while has_more and total_pages_processed < max_pages:
            try:
                current_page = total_pages_processed + 1
                print(f"📄 Processing page {current_page} (offset: {current_offset})...")

                # Rate limiting
                wait_time = self.rate_limiter.wait_if_needed('tcu')
                if wait_time > 0:
                    print(f"   ⏰ Rate limiting: waited {wait_time:.1f}s")

                # Fetch page
                api_start = time.time()
                tcu_page, has_more = self._fetch_tcu_page(current_offset)
                api_time = time.time() - api_start

                if not tcu_page:
                    print(f"   ⚠️ Empty page at offset {current_offset}")
                    break

                print(f"   📋 Found {len(tcu_page)} disqualification records")

                # Process and insert records
                processed_records = self._process_tcu_page(
                    tcu_page, current_page, update_existing
                )

                total_records += processed_records
                total_pages_processed += 1

                self.logger.log_api_call(
                    'tcu',
                    f'disqualifications/offset/{current_offset}',
                    'success',
                    api_time
                )

                # Progress update every 10 pages
                if current_page % 10 == 0:
                    elapsed = time.time() - start_time
                    avg_time_per_page = elapsed / current_page
                    estimated_total_time = avg_time_per_page * max_pages
                    print(f"   📊 Progress: {current_page}/{max_pages} pages, "
                          f"{total_records} records, "
                          f"ETA: {(estimated_total_time - elapsed)/60:.1f}min")

                # Update offset for next page
                current_offset += page_size

            except Exception as e:
                print(f"   ❌ Error processing page {current_page}: {e}")
                self.logger.log_api_call(
                    'tcu',
                    f'disqualifications/offset/{current_offset}',
                    'error',
                    0
                )

                # Continue to next page after error
                current_offset += page_size
                continue

        # Final summary
        elapsed_time = time.time() - start_time
        print(f"\n✅ TCU disqualifications population completed")
        print(f"📊 {total_records} disqualification records processed")
        print(f"📄 {total_pages_processed} pages processed successfully")
        print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
        if total_records > 0:
            print(f"⚡ Average: {total_records/elapsed_time:.1f} records/second")

        # Show corruption detection readiness
        print(f"\n🎯 CORRUPTION DETECTION READINESS:")
        self._show_tcu_summary()

        return total_records

    def _fetch_tcu_page(self, offset: int) -> Tuple[List[Dict], bool]:
        """Fetch a single page of TCU disqualifications"""
        try:
            params = {'offset': offset}
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # TCU API returns {"items": [...], "hasMore": boolean}
            if 'items' not in data:
                print(f"      ❌ Unexpected API response format: {list(data.keys())}")
                return [], False

            items = data.get('items', [])
            has_more = data.get('hasMore', False)

            return items, has_more

        except Exception as e:
            print(f"      ❌ API fetch error: {e}")
            raise

    def _process_tcu_page(self, disqualifications: List[Dict], page_number: int,
                          update_existing: bool) -> int:
        """Process a page of TCU disqualifications and insert into database"""
        processed_count = 0

        for disqualification in disqualifications:
            try:
                record = self._build_tcu_record(disqualification)
                if record:
                    inserted = self._insert_tcu_record(record, update_existing)
                    if inserted:
                        processed_count += 1

            except Exception as e:
                nome = disqualification.get('nome', 'unknown')
                print(f"      ⚠️ Error processing {nome}: {e}")
                continue

        print(f"   ✅ Page {page_number}: {processed_count}/{len(disqualifications)} records processed")
        return processed_count

    def _build_tcu_record(self, disqualification: Dict) -> Optional[Dict]:
        """Build TCU disqualification record from API data following database schema"""
        try:
            # Extract and clean CPF
            cpf_raw = disqualification.get('cpf', '')
            if not cpf_raw:
                return None  # Skip records without CPF

            cpf_clean = self._clean_cpf(cpf_raw)
            if not cpf_clean or len(cpf_clean) != 11:
                return None  # Skip invalid CPFs

            # Parse dates
            data_transito = self._parse_date(disqualification.get('data_transito_julgado'))
            data_final = self._parse_date(disqualification.get('data_final'))
            data_acordao = self._parse_date(disqualification.get('data_acordao'))

            record = {
                'cpf': cpf_clean,
                'nome': self._normalize_text(disqualification.get('nome'), 255),
                'processo': self._normalize_text(disqualification.get('processo'), 50),
                'deliberacao': self._normalize_text(disqualification.get('deliberacao'), 50),
                'data_transito_julgado': data_transito,
                'data_final': data_final,
                'data_acordao': data_acordao,
                'uf': self._normalize_text(disqualification.get('uf'), 10),
                'municipio': self._normalize_text(disqualification.get('municipio'), 255),
                'data_source': 'TCU',
                'api_reference_id': str(disqualification.get('processo', '')),
            }

            return record

        except Exception as e:
            print(f"        ⚠️ Error building TCU record: {e}")
            return None

    def _clean_cpf(self, cpf_raw: str) -> Optional[str]:
        """Clean CPF format - remove dots, dashes, spaces"""
        if not cpf_raw:
            return None

        # Remove all non-digit characters
        cpf_clean = re.sub(r'[^0-9]', '', str(cpf_raw))

        # Validate length
        if len(cpf_clean) != 11:
            return None

        # Basic CPF validation (all same digits check)
        if cpf_clean == cpf_clean[0] * 11:
            return None

        return cpf_clean

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date from TCU API format to database-compatible format"""
        if not date_str or date_str.strip() == '':
            return None

        try:
            # Handle ISO format with timezone: "2022-07-16T03:00:00Z"
            if 'T' in date_str:
                # Parse ISO format and extract date part
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.date().isoformat()

            # Handle simple date format: "2022-07-16"
            if len(date_str) == 10 and '-' in date_str:
                return date_str

            return None

        except Exception:
            return None

    def _normalize_text(self, text: str, max_length: int) -> Optional[str]:
        """Normalize and truncate text fields"""
        if not text or not text.strip():
            return None

        # Clean and normalize
        text = text.strip()

        # Smart truncation
        if len(text) <= max_length:
            return text

        # Reserve space for ellipsis
        truncate_length = max_length - 3

        # Try to break at word boundary
        if truncate_length > 20:
            last_space = text.rfind(' ', max(0, truncate_length - 20), truncate_length)
            if last_space > truncate_length - 20:
                truncate_length = last_space

        return text[:truncate_length] + '...'

    def _insert_tcu_record(self, record: Dict, update_existing: bool) -> bool:
        """Insert TCU record with conflict resolution"""
        try:
            # Build INSERT query
            fields = []
            values = []
            placeholders = []

            for field, value in record.items():
                if value is not None:
                    fields.append(field)
                    placeholders.append('%s')
                    values.append(value)

            if update_existing:
                # ON CONFLICT UPDATE approach
                update_fields = [f"{field} = EXCLUDED.{field}" for field in fields
                               if field not in ['cpf', 'processo', 'deliberacao']]

                sql = f"""
                    INSERT INTO tcu_disqualifications ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (cpf, processo, deliberacao)
                    DO UPDATE SET {', '.join(update_fields)}
                    RETURNING id
                """
            else:
                # ON CONFLICT DO NOTHING (faster for initial population)
                sql = f"""
                    INSERT INTO tcu_disqualifications ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (cpf, processo, deliberacao)
                    DO NOTHING
                    RETURNING id
                """

            result = database.execute_query(sql, tuple(values))
            return bool(result)  # True if record was inserted

        except Exception as e:
            print(f"        ⚠️ Database insert error: {e}")
            return False

    def _show_tcu_summary(self):
        """Show summary of TCU data for corruption detection readiness"""
        try:
            # Get basic stats
            total_disqualifications = database.execute_query(
                "SELECT COUNT(*) as count FROM tcu_disqualifications"
            )[0]['count']

            active_disqualifications = database.execute_query(
                "SELECT COUNT(*) as count FROM tcu_disqualifications "
                "WHERE data_final IS NULL OR data_final > CURRENT_DATE"
            )[0]['count']

            unique_cpfs = database.execute_query(
                "SELECT COUNT(DISTINCT cpf) as count FROM tcu_disqualifications"
            )[0]['count']

            # Get top states with disqualifications
            top_states = database.execute_query("""
                SELECT uf, COUNT(*) as disqualification_count
                FROM tcu_disqualifications
                WHERE uf IS NOT NULL
                GROUP BY uf
                ORDER BY disqualification_count DESC
                LIMIT 5
            """)

            print(f"   📊 Total disqualifications: {total_disqualifications:,}")
            print(f"   🔴 Active disqualifications: {active_disqualifications:,}")
            print(f"   👥 Unique disqualified CPFs: {unique_cpfs:,}")
            if total_disqualifications > 0:
                active_rate = (active_disqualifications/total_disqualifications)*100
                print(f"   📈 Active rate: {active_rate:.1f}%")

            if top_states:
                print(f"\n   🗺️  Top states with disqualifications:")
                for state in top_states:
                    uf = state['uf']
                    count = state['disqualification_count']
                    print(f"      • {uf}: {count:,}")

            # Cross-reference readiness
            print(f"\n   🎯 Cross-reference capability:")
            print(f"      ✅ {unique_cpfs:,} CPFs available for politician matching")
            print(f"      ✅ Fast CPF lookups via database index")
            print(f"      ✅ Ready for corruption detection via CPF correlation")

        except Exception as e:
            print(f"   ⚠️ Error generating summary: {e}")


def main():
    """Standalone test of TCU populator"""
    print("🧪 TESTING TCU POPULATOR")
    print("=" * 50)

    from cli4.modules.logger import CLI4Logger
    from cli4.modules.rate_limiter import CLI4RateLimiter

    logger = CLI4Logger()
    rate_limiter = CLI4RateLimiter()

    populator = TCUPopulator(logger, rate_limiter)

    # Test with limited pages
    result = populator.populate(max_pages=3, update_existing=False)
    print(f"\n🎯 Test completed: {result} records processed")


if __name__ == "__main__":
    main()