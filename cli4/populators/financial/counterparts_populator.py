"""
CLI4 Financial Counterparts Populator
Populate financial_counterparts table (Phase 2a)
"""

import requests
import time
from typing import Dict, List, Set, Tuple, Optional
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from src.clients.tse_client import TSEClient


class CLI4CounterpartsPopulator:
    """Populate financial_counterparts table with vendors and donors"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.camara_base = "https://dadosabertos.camara.leg.br/api/v2"
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None,
                 start_year: Optional[int] = None,
                 end_year: Optional[int] = None) -> int:
        """Populate financial counterparts table"""

        print("💰 FINANCIAL COUNTERPARTS POPULATION")
        print("=" * 50)
        print("Phase 2a: Building vendor/donor registry")
        print()

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = database.execute_query("SELECT id, deputy_id FROM unified_politicians")

        print(f"📋 Processing {len(politicians)} politicians")

        # Set date range
        if not start_year:
            start_year = 2019  # Default: last 5 years
        if not end_year:
            end_year = 2024

        print(f"📅 Date range: {start_year} - {end_year}")
        print()

        # Collect all unique counterparts
        all_counterparts: Set[Tuple[str, str, str]] = set()

        # PHASE 1: Extract from Deputados expenses
        print("🏛️ Extracting from Deputados expenses...")
        for i, politician in enumerate(politicians, 1):
            print(f"  [{i}/{len(politicians)}] Deputy {politician['deputy_id']}")

            deputados_counterparts = self._extract_deputados_counterparts(
                politician['deputy_id'], start_year, end_year
            )
            all_counterparts.update(deputados_counterparts)

        print(f"  ✅ Found {len(all_counterparts)} unique counterparts from Deputados")

        # PHASE 2: Extract from TSE campaign finance
        print("\n🗳️ Extracting from TSE campaign finance...")
        tse_counterparts = self._extract_tse_counterparts(
            politicians, start_year, end_year
        )
        all_counterparts.update(tse_counterparts)

        print(f"  ✅ Total unique counterparts: {len(all_counterparts)}")

        # PHASE 3: Bulk insert counterparts
        print(f"\n💾 Inserting {len(all_counterparts)} counterparts...")
        inserted_count = self._bulk_insert_counterparts(all_counterparts)

        print(f"✅ Financial counterparts population completed: {inserted_count} records")
        return inserted_count

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs"""
        placeholders = ','.join(['%s'] * len(politician_ids))
        query = f"SELECT id, deputy_id FROM unified_politicians WHERE id IN ({placeholders})"
        return database.execute_query(query, tuple(politician_ids))

    def _extract_deputados_counterparts(self, deputy_id: int, start_year: int,
                                       end_year: int) -> Set[Tuple[str, str, str]]:
        """Extract counterparts from Deputados expenses"""
        counterparts = set()

        for year in range(start_year, end_year + 1):
            wait_time = self.rate_limiter.wait_if_needed('camara')

            start_time = time.time()
            url = f"{self.camara_base}/deputados/{deputy_id}/despesas"
            params = {'ano': year, 'ordem': 'ASC', 'ordenarPor': 'mes'}

            try:
                response = requests.get(url, params=params, timeout=30)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    self.logger.log_api_call('camara', f'/deputados/{deputy_id}/despesas', 'success', response_time)

                    data = response.json()
                    expenses = data.get('dados', [])

                    for expense in expenses:
                        cnpj_cpf = expense.get('cnpjCpfFornecedor')
                        name = expense.get('nomeFornecedor')

                        if cnpj_cpf and name:
                            # Clean CNPJ/CPF (remove formatting)
                            cnpj_cpf_clean = ''.join(filter(str.isdigit, cnpj_cpf))
                            if len(cnpj_cpf_clean) in [11, 14]:  # Valid CPF or CNPJ length
                                counterparts.add((cnpj_cpf_clean, name.strip(), 'DEPUTADOS_VENDOR'))

                else:
                    self.logger.log_api_call('camara', f'/deputados/{deputy_id}/despesas', 'error', response_time)

            except Exception as e:
                print(f"    ⚠️ Error fetching {year} expenses: {e}")
                continue

        return counterparts

    def _extract_tse_counterparts(self, politicians: List[Dict], start_year: int,
                                 end_year: int) -> Set[Tuple[str, str, str]]:
        """Extract counterparts from TSE campaign finance"""
        counterparts = set()

        # Get CPFs from politicians for TSE correlation
        politician_cpfs = set()
        for politician in politicians:
            cpf_result = database.execute_query(
                "SELECT cpf FROM unified_politicians WHERE id = %s",
                (politician['id'],)
            )
            if cpf_result and cpf_result[0]['cpf']:
                politician_cpfs.add(cpf_result[0]['cpf'])

        print(f"  🔍 Searching TSE finance data for {len(politician_cpfs)} politicians")

        # Search TSE finance years
        for year in range(start_year, end_year + 1):
            try:
                print(f"    → Processing TSE {year}...")

                # Get TSE finance data for the year
                finance_data = self.tse_client.get_finance_data(year)

                if finance_data:
                    year_counterparts = 0
                    for record in finance_data:
                        # Check if this record relates to our politicians
                        candidate_cpf = record.get('nr_cpf_candidato') or record.get('cpf_candidato')
                        if candidate_cpf in politician_cpfs:

                            cnpj_cpf = record.get('nr_cpf_cnpj_doador') or record.get('cnpj_cpf_doador')
                            name = record.get('nm_doador') or record.get('nome_doador')

                            if cnpj_cpf and name:
                                # Clean CNPJ/CPF
                                cnpj_cpf_clean = ''.join(filter(str.isdigit, cnpj_cpf))
                                if len(cnpj_cpf_clean) in [11, 14]:
                                    counterparts.add((cnpj_cpf_clean, name.strip(), 'TSE_DONOR'))
                                    year_counterparts += 1

                    print(f"      ✅ Found {year_counterparts} counterparts in {year}")
                else:
                    print(f"      ❌ No TSE finance data for {year}")

            except Exception as e:
                print(f"    ⚠️ Error processing TSE {year}: {e}")
                continue

        return counterparts

    def _bulk_insert_counterparts(self, counterparts: Set[Tuple[str, str, str]]) -> int:
        """Bulk insert counterparts with conflict resolution"""

        if not counterparts:
            return 0

        # Prepare batch data
        batch_data = []
        for cnpj_cpf, name, source_type in counterparts:
            record = {
                'cnpj_cpf': cnpj_cpf,
                'name': name,
                'normalized_name': self._normalize_name(name),
                'entity_type': self._classify_entity_type(cnpj_cpf),
                'cnpj_validated': False,
                'sanctions_checked': False
            }
            batch_data.append(record)

        # Batch insert with ON CONFLICT handling
        inserted_count = 0
        batch_size = 100

        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i:i + batch_size]

            try:
                # Build bulk insert query
                fields = batch[0].keys()
                placeholders = ', '.join(['%s'] * len(fields))
                fields_str = ', '.join(fields)

                query = f"""
                    INSERT INTO financial_counterparts ({fields_str})
                    VALUES ({placeholders})
                    ON CONFLICT (cnpj_cpf) DO UPDATE SET
                        name = EXCLUDED.name,
                        normalized_name = EXCLUDED.normalized_name,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """

                # Prepare values
                values = []
                for record in batch:
                    values.append(tuple(record[field] for field in fields))

                # Execute batch
                results = database.execute_batch_returning(query, values)
                inserted_count += len(results)

                print(f"    ✅ Processed batch {i//batch_size + 1}: {len(results)} records")

            except Exception as e:
                print(f"    ❌ Error in batch {i//batch_size + 1}: {e}")
                continue

        return inserted_count

    def _normalize_name(self, name: str) -> str:
        """Normalize name for matching"""
        if not name:
            return ''

        import unicodedata
        normalized = unicodedata.normalize('NFD', name)
        ascii_name = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return ascii_name.upper().strip()

    def _classify_entity_type(self, cnpj_cpf: str) -> str:
        """Classify entity type based on identifier length"""
        if len(cnpj_cpf) == 14:
            return 'COMPANY'
        elif len(cnpj_cpf) == 11:
            return 'INDIVIDUAL'
        else:
            return 'UNKNOWN'