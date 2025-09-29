"""
CLI4 CEPIM Populator
Populate vendor_sanctions table with Portal da Transparência CEPIM data
Essential for corruption detection through vendor cross-referencing
"""

import time
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker
from src.clients.portal_transparencia_client import PortalTransparenciaClient


class CEPIMPopulator:
    """Populate vendor sanctions table with Portal da Transparência CEPIM data"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.portal_client = PortalTransparenciaClient()

    def populate(self, max_pages: Optional[int] = None,
                 update_existing: bool = False) -> int:
        """Main population method - fetches all sanctions from Portal da Transparência"""

        print("⚠️  CEPIM SANCTIONS POPULATION")
        print("=" * 60)
        print("Portal da Transparência CEPIM sanctions for corruption detection")
        print()

        # Check dependencies - sanctions are independent but useful for cross-referencing
        DependencyChecker.print_dependency_warning(
            required_steps=[],  # No dependencies - sanctions are standalone
            current_step="CEPIM POPULATION"
        )

        print("🎯 APPROACH: Complete sanctions database for fast local lookups")
        print("   • Fetch ALL sanctions via pagination (API CNPJ filter is broken)")
        print("   • Store in local database with proper indexing")
        print("   • Enable fast cross-referencing with financial records")
        print()

        if not max_pages:
            max_pages = 1000  # Reasonable default to prevent infinite loops
            print(f"📄 Max pages limit: {max_pages} (prevent runaway)")

        # Track progress
        total_records = 0
        total_pages_processed = 0
        current_page = 1
        consecutive_empty_pages = 0
        max_consecutive_empty = 5

        print(f"🚀 Starting sanctions population...")
        start_time = time.time()

        while current_page <= max_pages and consecutive_empty_pages < max_consecutive_empty:
            try:
                print(f"📄 Processing page {current_page}...")

                # Rate limiting
                wait_time = self.rate_limiter.wait_if_needed('portal_transparencia')
                if wait_time > 0:
                    print(f"   ⏰ Rate limiting: waited {wait_time:.1f}s")

                # Fetch page
                api_start = time.time()
                sanctions_page = self._fetch_sanctions_page(current_page)
                api_time = time.time() - api_start

                if not sanctions_page or len(sanctions_page) == 0:
                    consecutive_empty_pages += 1
                    print(f"   ⚠️ Empty page {current_page} ({consecutive_empty_pages}/{max_consecutive_empty})")

                    if consecutive_empty_pages >= max_consecutive_empty:
                        print(f"   🛑 Stopping: {max_consecutive_empty} consecutive empty pages")
                        break

                    current_page += 1
                    continue

                # Reset empty page counter
                consecutive_empty_pages = 0

                print(f"   📋 Found {len(sanctions_page)} sanctions")

                # Process and insert sanctions
                processed_records = self._process_sanctions_page(
                    sanctions_page, current_page, update_existing
                )

                total_records += processed_records
                total_pages_processed += 1

                self.logger.log_api_call(
                    'portal_transparencia',
                    f'cepim/page/{current_page}',
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

                current_page += 1

            except Exception as e:
                print(f"   ❌ Error processing page {current_page}: {e}")
                self.logger.log_api_call(
                    'portal_transparencia',
                    f'cepim/page/{current_page}',
                    'error',
                    0
                )

                # Continue to next page after error
                current_page += 1
                continue

        # Final summary
        elapsed_time = time.time() - start_time
        print(f"\\n✅ CEPIM population completed")
        print(f"📊 {total_records} sanctions records processed")
        print(f"📄 {total_pages_processed} pages processed successfully")
        print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
        print(f"⚡ Average: {total_records/elapsed_time:.1f} records/second")

        # Show corruption detection readiness
        print(f"\\n🎯 CORRUPTION DETECTION READINESS:")
        self._show_sanctions_summary()

        return total_records

    def _fetch_sanctions_page(self, page: int) -> List[Dict]:
        """Fetch a single page of sanctions from Portal da Transparência"""
        try:
            # Use the existing client method but bypass CNPJ filtering
            # since we discovered the API ignores CNPJ filters anyway
            response = self.portal_client.session.get(
                f"{self.portal_client.base_url}cepim",
                params={'pagina': page},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data if isinstance(data, list) else []

        except Exception as e:
            print(f"      ❌ API fetch error: {e}")
            raise

    def _process_sanctions_page(self, sanctions: List[Dict], page_number: int,
                               update_existing: bool) -> int:
        """Process a page of sanctions and insert into database"""
        processed_count = 0

        for sanction in sanctions:
            try:
                record = self._build_sanction_record(sanction)
                if record:
                    inserted = self._insert_sanction_record(record, update_existing)
                    if inserted:
                        processed_count += 1

            except Exception as e:
                print(f"      ⚠️ Error processing sanction {sanction.get('id', 'unknown')}: {e}")
                continue

        print(f"   ✅ Page {page_number}: {processed_count}/{len(sanctions)} sanctions processed")
        return processed_count

    def _build_sanction_record(self, cepim: Dict) -> Optional[Dict]:
        """Build CEPIM sanction record from API data following our database schema"""
        try:
            # Extract CEPIM-specific entity info
            pessoa_juridica = cepim.get('pessoaJuridica', {})
            orgao_superior = cepim.get('orgaoSuperior', {})
            convenio = cepim.get('convenio', {})

            # Get CNPJ from pessoaJuridica (CEPIM structure)
            cnpj_raw = pessoa_juridica.get('cnpjFormatado', '')
            if not cnpj_raw:
                return None  # Skip records without CNPJ

            # Clean CNPJ (remove formatting)
            cnpj_clean = re.sub(r'[^\d]', '', cnpj_raw)
            if len(cnpj_clean) != 14:
                return None  # Skip invalid CNPJs

            # CEPIM doesn't have start/end dates like CEIS, only dataReferencia
            # We'll use dataReferencia as the sanction date
            data_referencia = self._parse_date(cepim.get('dataReferencia'))

            # Extract penalty amount from convenio if available
            penalty_amount = None
            if convenio and convenio.get('valorGlobal'):
                penalty_amount = float(convenio.get('valorGlobal', 0))

            # Get entity name from multiple possible sources
            entity_name = (
                pessoa_juridica.get('razaoSocialReceita') or
                pessoa_juridica.get('nome') or
                'Unknown'
            )

            record = {
                'cnpj_cpf': cnpj_clean,
                'entity_name': self._normalize_text(entity_name, 500),
                'sanction_type': 'CEPIM - Empresa Punida',
                'sanction_description': self._normalize_text(
                    cepim.get('motivo', ''), 2000
                ),
                'sanction_start_date': data_referencia,  # Using dataReferencia
                'sanction_end_date': None,  # CEPIM doesn't have end dates
                'sanctioning_agency': self._normalize_text(
                    orgao_superior.get('nome', 'Unknown'), 255
                ),
                'sanctioning_state': '',  # CEPIM doesn't have state info
                'sanctioning_process': '',  # CEPIM doesn't have process numbers
                'penalty_amount': penalty_amount,
                'is_active': True,  # CEPIM records are generally considered active
                'data_source': 'PORTAL_TRANSPARENCIA_CEPIM',
                'api_reference_id': str(cepim.get('id', '')),
                'verification_date': datetime.now()
            }

            return record

        except Exception as e:
            print(f"        ⚠️ Error building CEPIM record: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse Brazilian date format to database-compatible format"""
        if not date_str or date_str.strip() == '' or 'Sem informação' in date_str:
            return None

        try:
            # Handle format: "14/02/2025"
            if '/' in date_str and len(date_str) == 10:
                day, month, year = date_str.split('/')
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            return None
        except Exception:
            return None

    def _is_sanction_active(self, start_date: Optional[str], end_date: Optional[str]) -> bool:
        """Determine if sanction is currently active"""
        if not start_date:
            return False

        try:
            today = datetime.now().date()
            start = datetime.fromisoformat(start_date).date()

            # If no end date, assume active if start date is in the past
            if not end_date:
                return start <= today

            end = datetime.fromisoformat(end_date).date()
            return start <= today <= end

        except Exception:
            return False  # Conservative default

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

    def _insert_sanction_record(self, record: Dict, update_existing: bool) -> bool:
        """Insert sanction record with conflict resolution"""
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
                               if field not in ['cnpj_cpf', 'sanction_type', 'sanction_start_date', 'sanctioning_agency']]

                sql = f"""
                    INSERT INTO vendor_sanctions ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (cnpj_cpf, sanction_type, sanction_start_date, sanctioning_agency)
                    DO UPDATE SET {', '.join(update_fields)}
                    RETURNING id
                """
            else:
                # ON CONFLICT DO NOTHING (faster for initial population)
                sql = f"""
                    INSERT INTO vendor_sanctions ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (cnpj_cpf, sanction_type, sanction_start_date, sanctioning_agency)
                    DO NOTHING
                    RETURNING id
                """

            result = database.execute_query(sql, tuple(values))
            return bool(result)  # True if record was inserted

        except Exception as e:
            print(f"        ⚠️ Database insert error: {e}")
            return False

    def _show_sanctions_summary(self):
        """Show summary of sanctions data for corruption detection readiness"""
        try:
            # Get basic stats
            total_sanctions = database.execute_query(
                "SELECT COUNT(*) as count FROM vendor_sanctions"
            )[0]['count']

            active_sanctions = database.execute_query(
                "SELECT COUNT(*) as count FROM vendor_sanctions WHERE is_active = true"
            )[0]['count']

            unique_entities = database.execute_query(
                "SELECT COUNT(DISTINCT cnpj_cpf) as count FROM vendor_sanctions"
            )[0]['count']

            # Get top sanctioning agencies
            top_agencies = database.execute_query("""
                SELECT sanctioning_agency, COUNT(*) as sanction_count
                FROM vendor_sanctions
                WHERE sanctioning_agency IS NOT NULL
                GROUP BY sanctioning_agency
                ORDER BY sanction_count DESC
                LIMIT 5
            """)

            print(f"   📊 Total sanctions: {total_sanctions:,}")
            print(f"   🔴 Active sanctions: {active_sanctions:,}")
            print(f"   🏢 Unique sanctioned entities: {unique_entities:,}")
            print(f"   📈 Active rate: {(active_sanctions/total_sanctions)*100:.1f}%")

            print(f"\\n   🏛️  Top sanctioning agencies:")
            for agency in top_agencies:
                print(f"      • {agency['sanctioning_agency']}: {agency['sanction_count']:,}")

            # Cross-reference readiness
            print(f"\\n   🎯 Cross-reference capability:")
            print(f"      ✅ {unique_entities:,} entities available for vendor matching")
            print(f"      ✅ Fast CNPJ lookups via database index")
            print(f"      ✅ Ready for financial records correlation")

        except Exception as e:
            print(f"   ⚠️ Error generating summary: {e}")


def main():
    """Standalone test of sanctions populator"""
    print("🧪 TESTING SANCTIONS POPULATOR")
    print("=" * 50)

    from cli4.modules.logger import CLI4Logger
    from cli4.modules.rate_limiter import CLI4RateLimiter

    logger = CLI4Logger()
    rate_limiter = CLI4RateLimiter()

    populator = CEPIMPopulator(logger, rate_limiter)

    # Test with limited pages
    result = populator.populate(max_pages=3, update_existing=False)
    print(f"\\n🎯 Test completed: {result} records processed")


if __name__ == "__main__":
    main()