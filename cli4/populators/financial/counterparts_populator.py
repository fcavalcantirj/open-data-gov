"""
CLI4 Financial Counterparts Populator
Phase 2a: Build vendor/donor registry from Deputados + TSE
"""

from typing import Dict, List, Set, Tuple
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from src.clients.tse_client import TSEClient


class CLI4CounterpartsPopulator:
    """Populate financial_counterparts table with vendor/donor registry"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.tse_client = TSEClient()

    def populate(self, politician_ids: List[int] = None, start_year: int = None,
                end_year: int = None) -> int:
        """Populate financial counterparts table"""

        print("💰 FINANCIAL COUNTERPARTS POPULATION")
        print("=" * 50)
        print("Phase 2a: Building vendor/donor registry")
        print()

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = database.execute_query(
                "SELECT id, deputy_id, cpf, nome_civil FROM unified_politicians"
            )

        print(f"📋 Processing {len(politicians)} politicians")

        # Set date range
        if not start_year:
            start_year = 2019
        if not end_year:
            end_year = 2024

        print(f"📅 Date range: {start_year} - {end_year}")
        print()

        all_counterparts = set()

        # PHASE 1: Extract from Deputados expenses (proven method)
        print("🏛️ Extracting from Deputados expenses...")
        for i, politician in enumerate(politicians, 1):
            print(f"  [{i}/{len(politicians)}] Deputy {politician['deputy_id']}")

            deputados_counterparts = self._extract_deputados_counterparts(
                politician['deputy_id'], start_year, end_year
            )
            all_counterparts.update(deputados_counterparts)

        print(f"  ✅ Found {len(all_counterparts)} unique counterparts from Deputados")

        # PHASE 2: Extract from TSE campaign finance (SPACE ENGINEER FIX)
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
        query = f"SELECT id, deputy_id, cpf, nome_civil FROM unified_politicians WHERE id IN ({placeholders})"
        return database.execute_query(query, tuple(politician_ids))

    def _extract_deputados_counterparts(self, deputy_id: int, start_year: int,
                                      end_year: int) -> Set[Tuple[str, str, str]]:
        """Extract counterparts from Deputados expenses API"""
        counterparts = set()

        for year in range(start_year, end_year + 1):
            try:
                # Fetch expenses for the year
                expenses_url = f"/deputados/{deputy_id}/despesas"
                params = {'ano': year, 'itens': 100, 'ordem': 'ASC', 'ordenarPor': 'dataDocumento'}

                response_time = 0
                success = False

                try:
                    import requests
                    import time
                    start_time = time.time()

                    response = requests.get(
                        f"https://dadosabertos.camara.leg.br/api/v2{expenses_url}",
                        params=params,
                        timeout=30
                    )
                    response_time = time.time() - start_time

                    if response.status_code == 200:
                        data = response.json()
                        expenses = data.get('dados', [])
                        success = True

                        # Extract counterparts
                        for expense in expenses:
                            cnpj_cpf = expense.get('cnpjCpfFornecedor', '').strip()
                            name = expense.get('nomeFornecedor', '').strip()

                            if cnpj_cpf and name:
                                # Clean CNPJ/CPF (remove formatting)
                                cnpj_cpf_clean = ''.join(filter(str.isdigit, cnpj_cpf))
                                if len(cnpj_cpf_clean) in [11, 14]:  # Valid CPF or CNPJ
                                    counterparts.add((cnpj_cpf_clean, name, 'DEPUTADOS_VENDOR'))

                        self.logger.log_api_call('camara', expenses_url, 'success', response_time)

                    else:
                        self.logger.log_api_call('camara', expenses_url, 'error', response_time)

                except Exception as e:
                    self.logger.log_api_call('camara', expenses_url, 'error', response_time)

                # Rate limiting
                self.rate_limiter.wait_if_needed('camara')

            except Exception as e:
                print(f"    ⚠️ Error fetching {year} expenses: {e}")
                continue

        return counterparts

    def _extract_tse_counterparts(self, politicians: List[Dict], start_year: int,
                                 end_year: int) -> Set[Tuple[str, str, str]]:
        """Extract counterparts from TSE campaign finance - SPACE ENGINEER PRECISION FIX"""
        print("\n🗳️ Extracting from TSE campaign finance...")
        print("🚀 MEMORY-EFFICIENT: Processing one politician at a time")

        counterparts = set()

        # Calculate campaign years
        campaign_years = self._calculate_campaign_years(start_year, end_year)
        tse_data_types = ['receitas', 'despesas_contratadas']  # Only types with donor/vendor data

        print(f"  📅 Campaign years: {campaign_years}")
        print(f"  📊 TSE data types: {tse_data_types}")
        print(f"  👥 Processing {len(politicians)} politicians individually...")

        total_counterparts = 0

        for i, politician in enumerate(politicians, 1):
            politician_cpf = politician.get('cpf')
            if not politician_cpf:
                continue

            print(f"\n    👤 [{i}/{len(politicians)}] {politician.get('nome_civil', 'Unknown')[:30]}...")
            print(f"       CPF: {politician_cpf}")

            politician_counterparts = 0

            for year in campaign_years:
                for data_type in tse_data_types:
                    try:
                        print(f"         🔍 {year} {data_type}...")

                        # PRECISION: Use proven streaming method (same as records_populator)
                        finance_data = self.tse_client.get_finance_data_streaming(
                            year, data_type, politician_cpf
                        )

                        if finance_data:
                            type_counterparts = 0
                            for record in finance_data:
                                # Extract counterpart information
                                cnpj_cpf = (record.get('nr_cpf_cnpj_doador') or
                                          record.get('cnpj_cpf_doador') or
                                          record.get('NR_CPF_CNPJ_DOADOR'))

                                name = (record.get('nm_doador') or
                                       record.get('nome_doador') or
                                       record.get('NM_DOADOR'))

                                if cnpj_cpf and name:
                                    # Clean CNPJ/CPF
                                    cnpj_cpf_clean = ''.join(filter(str.isdigit, str(cnpj_cpf)))
                                    if len(cnpj_cpf_clean) in [11, 14]:
                                        counterparts.add((cnpj_cpf_clean, name.strip(), 'TSE_DONOR'))
                                        type_counterparts += 1

                            if type_counterparts > 0:
                                print(f"           ✅ {type_counterparts} counterparts")
                                politician_counterparts += type_counterparts

                        # Rate limiting between API calls
                        self.rate_limiter.wait_if_needed('tse')

                    except Exception as e:
                        print(f"           ⚠️ Error: {e}")
                        continue

            if politician_counterparts > 0:
                print(f"       ✅ Total: {politician_counterparts} counterparts")
                total_counterparts += politician_counterparts
            else:
                print(f"       ⚪ No TSE counterparts found")

        print(f"\n  🎯 TSE EXTRACTION COMPLETE")
        print(f"     Total TSE counterparts: {total_counterparts}")
        print(f"     Unique counterparts: {len(counterparts)}")

        return counterparts

    def _calculate_campaign_years(self, start_year: int, end_year: int) -> List[int]:
        """Calculate campaign finance years around elections"""
        election_years = [2018, 2022]  # Major federal elections
        campaign_years = []

        for election_year in election_years:
            if start_year <= election_year <= end_year:
                campaign_years.append(election_year)
                # Add pre-campaign year
                if start_year <= election_year - 1 <= end_year:
                    campaign_years.append(election_year - 1)

        return sorted(list(set(campaign_years)))

    def _bulk_insert_counterparts(self, counterparts: Set[Tuple[str, str, str]]) -> int:
        """Bulk insert counterparts into database"""
        if not counterparts:
            return 0

        # Convert to dict to deduplicate by CNPJ/CPF (keep latest name)
        counterparts_dict = {}
        for cnpj_cpf, name, source in counterparts:
            counterparts_dict[cnpj_cpf] = (name, source)

        # Convert to list for batch processing
        counterparts_list = [(cnpj_cpf, name, source) for cnpj_cpf, (name, source) in counterparts_dict.items()]
        batch_size = 100

        total_inserted = 0
        for i in range(0, len(counterparts_list), batch_size):
            batch = counterparts_list[i:i + batch_size]

            # Prepare batch values
            values = []
            for cnpj_cpf, name, source in batch:
                # Determine entity type
                entity_type = 'COMPANY' if len(cnpj_cpf) == 14 else 'INDIVIDUAL'

                # Normalize name
                normalized_name = name.upper().strip()

                values.append((cnpj_cpf, name, normalized_name, entity_type, source))

            # Bulk insert with conflict resolution
            if values:
                placeholders = ','.join(['(%s,%s,%s,%s,%s)'] * len(values))
                flat_values = [item for sublist in values for item in sublist]

                query = f"""
                    INSERT INTO financial_counterparts
                    (cnpj_cpf, name, normalized_name, entity_type, source_system)
                    VALUES {placeholders}
                    ON CONFLICT (cnpj_cpf) DO UPDATE SET
                        name = EXCLUDED.name,
                        normalized_name = EXCLUDED.normalized_name,
                        source_system = EXCLUDED.source_system,
                        updated_at = CURRENT_TIMESTAMP
                """

                try:
                    # Use execute_update for INSERT operations
                    affected_rows = database.execute_update(query, flat_values)
                    total_inserted += len(values)
                    print(f"    ✅ Processed batch {i//batch_size + 1}: {len(values)} records")

                except Exception as e:
                    print(f"    ❌ Batch insert error: {e}")
                    print(f"      Trying individual inserts...")
                    # Try one by one to identify problematic records
                    for cnpj_cpf, name, normalized_name, entity_type, source in values:
                        try:
                            single_query = """
                                INSERT INTO financial_counterparts
                                (cnpj_cpf, name, normalized_name, entity_type, source_system)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (cnpj_cpf) DO UPDATE SET
                                    name = EXCLUDED.name,
                                    normalized_name = EXCLUDED.normalized_name,
                                    source_system = EXCLUDED.source_system,
                                    updated_at = CURRENT_TIMESTAMP
                            """
                            database.execute_update(single_query, (cnpj_cpf, name, normalized_name, entity_type, source))
                            total_inserted += 1
                        except Exception as single_error:
                            print(f"      ❌ Failed to insert {cnpj_cpf}: {single_error}")

        return total_inserted