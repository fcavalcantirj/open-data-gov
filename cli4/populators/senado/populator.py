"""
CLI4 Senado Politicians Populator
Populate senado_politicians table with Senate Federal data
Essential for family/business network detection through surname cross-referencing
"""

import time
import re
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker


class SenadoPopulator:
    """Populate Senado politicians table with Senate Federal data"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.base_url = "https://legis.senado.leg.br/dadosabertos/"

    def populate(self, update_existing: bool = False) -> int:
        """Main population method - fetches all current senators"""

        print("🏛️  SENADO POLITICIANS POPULATION")
        print("=" * 60)
        print("Senate Federal data for family/business network detection")
        print()

        # Check dependencies - Senado data is independent but enables cross-referencing
        DependencyChecker.print_dependency_warning(
            required_steps=[],  # No dependencies - Senado data is standalone
            current_step="SENADO POLITICIANS POPULATION"
        )

        print("🎯 APPROACH: Complete Senate registry for surname cross-reference")
        print("   • Fetch ALL current senators from XML API")
        print("   • Extract names, parties, states for family network detection")
        print("   • Store in local database with proper indexing")
        print("   • Enable fast surname cross-referencing with Câmara deputies")
        print()

        # Track progress
        total_records = 0
        start_time = time.time()

        print(f"🚀 Starting Senado politicians population...")

        try:
            # Rate limiting
            wait_time = self.rate_limiter.wait_if_needed('senado')
            if wait_time > 0:
                print(f"   ⏰ Rate limiting: waited {wait_time:.1f}s")

            # Fetch senators
            api_start = time.time()
            senators = self._fetch_senators()
            api_time = time.time() - api_start

            if not senators:
                print(f"   ⚠️ No senators found")
                return 0

            print(f"   📋 Found {len(senators)} senators")

            # Process and insert records
            processed_records = self._process_senators(senators, update_existing)
            total_records += processed_records

            self.logger.log_api_call(
                'senado',
                'senador/lista/atual',
                'success',
                api_time
            )

        except Exception as e:
            print(f"   ❌ Error processing senators: {e}")
            self.logger.log_api_call(
                'senado',
                'senador/lista/atual',
                'error',
                0
            )
            raise

        # Final summary
        elapsed_time = time.time() - start_time
        print(f"\n✅ Senado politicians population completed")
        print(f"📊 {total_records} senator records processed")
        print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
        if total_records > 0:
            print(f"⚡ Average: {total_records/elapsed_time:.1f} records/second")

        # Show family network readiness
        print(f"\n🎯 FAMILY NETWORK DETECTION READINESS:")
        self._show_senado_summary()

        return total_records

    def _fetch_senators(self) -> List[Dict]:
        """Fetch all current senators from Senado XML API"""
        try:
            url = f"{self.base_url}senador/lista/atual"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            senators = []

            # Navigate XML structure based on integration test results
            for parlamentar in root.findall('.//Parlamentar'):
                senator_data = self._parse_senator_xml(parlamentar)
                if senator_data:
                    senators.append(senator_data)

            return senators

        except Exception as e:
            print(f"      ❌ API fetch error: {e}")
            raise

    def _parse_senator_xml(self, parlamentar) -> Optional[Dict]:
        """Parse individual senator XML element"""
        try:
            identificacao = parlamentar.find('IdentificacaoParlamentar')
            if identificacao is None:
                return None

            # Extract fields based on verified XML structure
            fields_map = {
                'codigo': 'CodigoParlamentar',
                'codigo_publico': 'CodigoPublicoNaLegAtual',
                'nome': 'NomeParlamentar',
                'nome_completo': 'NomeCompletoParlamentar',
                'sexo': 'SexoParlamentar',
                'partido': 'SiglaPartidoParlamentar',
                'estado': 'UfParlamentar',
                'email': 'EmailParlamentar',
                'foto_url': 'UrlFotoParlamentar',
                'pagina_url': 'UrlPaginaParlamentar',
                'bloco': 'NomeBlocoParlamentar'
            }

            senator = {}
            for field, xml_field in fields_map.items():
                element = identificacao.find(xml_field)
                if element is not None and element.text:
                    senator[field] = element.text.strip()
                else:
                    senator[field] = None

            # Validate required fields
            if not senator.get('codigo') or not senator.get('nome'):
                return None

            return senator

        except Exception as e:
            print(f"        ⚠️ Error parsing senator XML: {e}")
            return None

    def _process_senators(self, senators: List[Dict], update_existing: bool) -> int:
        """Process senators and insert into database"""
        processed_count = 0

        for senator in senators:
            try:
                record = self._build_senado_record(senator)
                if record:
                    inserted = self._insert_senado_record(record, update_existing)
                    if inserted:
                        processed_count += 1

            except Exception as e:
                nome = senator.get('nome', 'unknown')
                print(f"      ⚠️ Error processing {nome}: {e}")
                continue

        print(f"   ✅ Processed: {processed_count}/{len(senators)} senator records")
        return processed_count

    def _build_senado_record(self, senator: Dict) -> Optional[Dict]:
        """Build Senado politician record following database schema"""
        try:
            record = {
                'codigo': senator.get('codigo'),
                'codigo_publico': senator.get('codigo_publico'),
                'nome': self._normalize_text(senator.get('nome'), 255),
                'nome_completo': self._normalize_text(senator.get('nome_completo'), 255),
                'sexo': self._normalize_text(senator.get('sexo'), 20),
                'partido': self._normalize_text(senator.get('partido'), 20),
                'estado': self._normalize_text(senator.get('estado'), 10),
                'email': self._normalize_text(senator.get('email'), 255),
                'foto_url': self._normalize_text(senator.get('foto_url'), 500),
                'pagina_url': self._normalize_text(senator.get('pagina_url'), 500),
                'bloco': self._normalize_text(senator.get('bloco'), 255),
                'data_source': 'SENADO'
            }

            return record

        except Exception as e:
            print(f"        ⚠️ Error building Senado record: {e}")
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

    def _insert_senado_record(self, record: Dict, update_existing: bool) -> bool:
        """Insert Senado record with conflict resolution"""
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
                               if field not in ['codigo']]

                sql = f"""
                    INSERT INTO senado_politicians ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (codigo)
                    DO UPDATE SET {', '.join(update_fields)}
                    RETURNING id
                """
            else:
                # ON CONFLICT DO NOTHING (faster for initial population)
                sql = f"""
                    INSERT INTO senado_politicians ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (codigo)
                    DO NOTHING
                    RETURNING id
                """

            result = database.execute_query(sql, tuple(values))
            return bool(result)  # True if record was inserted

        except Exception as e:
            print(f"        ⚠️ Database insert error: {e}")
            return False

    def _show_senado_summary(self):
        """Show summary of Senado data for family network detection readiness"""
        try:
            # Get basic stats
            total_senators = database.execute_query(
                "SELECT COUNT(*) as count FROM senado_politicians"
            )[0]['count']

            # Get party distribution
            party_stats = database.execute_query("""
                SELECT partido, COUNT(*) as senator_count
                FROM senado_politicians
                WHERE partido IS NOT NULL
                GROUP BY partido
                ORDER BY senator_count DESC
                LIMIT 5
            """)

            # Get state distribution
            state_stats = database.execute_query("""
                SELECT estado, COUNT(*) as senator_count
                FROM senado_politicians
                WHERE estado IS NOT NULL
                GROUP BY estado
                ORDER BY senator_count DESC
                LIMIT 5
            """)

            print(f"   📊 Total senators: {total_senators:,}")

            if party_stats:
                print(f"\n   🏛️  Top parties:")
                for party in party_stats:
                    partido = party['partido']
                    count = party['senator_count']
                    print(f"      • {partido}: {count:,}")

            if state_stats:
                print(f"\n   🗺️  Top states:")
                for state in state_stats:
                    estado = state['estado']
                    count = state['senator_count']
                    print(f"      • {estado}: {count:,}")

            # Family network capability
            print(f"\n   🎯 Family network detection capability:")
            print(f"      ✅ {total_senators:,} senators available for surname matching")
            print(f"      ✅ Fast name lookups via database index")
            print(f"      ✅ Ready for family network detection via surname correlation")
            print(f"      ✅ Party/state cross-reference for political family analysis")

        except Exception as e:
            print(f"   ⚠️ Error generating summary: {e}")


def main():
    """Standalone test of Senado populator"""
    print("🧪 TESTING SENADO POPULATOR")
    print("=" * 50)

    from cli4.modules.logger import CLI4Logger
    from cli4.modules.rate_limiter import CLI4RateLimiter

    logger = CLI4Logger()
    rate_limiter = CLI4RateLimiter()

    populator = SenadoPopulator(logger, rate_limiter)

    # Test population
    result = populator.populate(update_existing=False)
    print(f"\n🎯 Test completed: {result} records processed")


if __name__ == "__main__":
    main()