"""
CLI4 Assets Populator
Populate politician_assets table with individual TSE asset declarations
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker
from src.clients.tse_client import TSEClient


class AssetsPopulator:
    """Populate politician assets table with individual TSE asset declarations"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None,
                election_years: Optional[List[int]] = None,
                force_refresh: bool = False) -> int:
        """Main population method"""

        print("🏛️ INDIVIDUAL ASSET DECLARATIONS POPULATION")
        print("=" * 60)
        print("TSE candidate asset declarations with detailed asset tracking")
        print()

        # Check dependencies
        DependencyChecker.print_dependency_warning(
            required_steps=["politicians"],
            current_step="ASSET DECLARATIONS POPULATION"
        )

        # Set default election years for asset data
        if election_years is None:
            election_years = [2018, 2020, 2022, 2024]

        print(f"🗳️ Processing election years: {', '.join(map(str, election_years))}")

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            # Get politicians with SQ_CANDIDATO data for correlation
            politicians = database.execute_query("""
                SELECT id, cpf, nome_civil, sq_candidato_current
                FROM unified_politicians
                WHERE sq_candidato_current IS NOT NULL
            """)

        if not politicians:
            print("⚠️ No politicians with SQ_CANDIDATO data found for asset correlation")
            return 0

        print(f"👥 Processing {len(politicians)} politicians with electoral data")
        print()

        total_records = 0
        processed_politicians = 0

        # Process each election year
        for year in election_years:
            print(f"\n🗳️ Processing {year} asset declarations...")

            # Get TSE asset data for this year (cached by TSE client)
            year_assets = self._fetch_tse_assets(year)
            if not year_assets:
                print(f"  ⚠️ No asset data available for {year}")
                continue

            print(f"  📊 Found {len(year_assets)} total assets in {year}")

            # Create SQ_CANDIDATO → assets mapping for efficiency
            assets_by_sq = {}
            for asset in year_assets:
                sq_candidato = asset.get('SQ_CANDIDATO')
                if sq_candidato:
                    if sq_candidato not in assets_by_sq:
                        assets_by_sq[sq_candidato] = []
                    assets_by_sq[sq_candidato].append(asset)

            print(f"  📋 Organized assets for {len(assets_by_sq)} unique candidates")

            # Process politicians for this year
            year_records = 0
            for politician in politicians:
                try:
                    # Use the current SQ_CANDIDATO for all years
                    # Note: This assumes politician maintains same SQ_CANDIDATO across years
                    sq_candidato = politician.get('sq_candidato_current')

                    if not sq_candidato:
                        continue  # Skip politicians without SQ_CANDIDATO data

                    sq_candidato_str = str(sq_candidato)
                    politician_assets = assets_by_sq.get(sq_candidato_str, [])

                    if politician_assets:
                        # Build asset records for this politician
                        asset_records = self._build_asset_records(
                            politician['id'], politician_assets, year
                        )

                        # Insert records immediately (memory-efficient)
                        if asset_records:
                            inserted = self._insert_asset_records(asset_records, force_refresh)
                            year_records += inserted

                            if inserted > 0:
                                print(f"    ✅ {politician['nome_civil']}: {inserted} assets inserted")
                            elif not force_refresh:
                                print(f"    ⏭️ {politician['nome_civil']}: {len(asset_records)} assets already exist")

                    self.logger.log_processing(
                        'assets', str(politician['id']), 'success',
                        {'assets_found': len(politician_assets), 'year': year}
                    )

                except Exception as e:
                    print(f"    ❌ Error processing {politician['nome_civil']}: {e}")
                    self.logger.log_processing(
                        'assets', str(politician['id']), 'error',
                        {'error': str(e), 'year': year}
                    )
                    continue

            print(f"  📊 Year {year}: {year_records} asset records inserted")
            total_records += year_records

        processed_politicians = len([p for p in politicians
                                   if p.get('sq_candidato_current')])

        print(f"\n✅ Asset population completed")
        print(f"📊 {total_records} asset records inserted")
        print(f"👥 {processed_politicians}/{len(politicians)} politicians had correlatable data")
        print(f"🗳️ Years processed: {', '.join(map(str, election_years))}")

        return total_records

    def _fetch_tse_assets(self, year: int) -> List[Dict]:
        """Fetch TSE asset data with rate limiting"""
        wait_time = self.rate_limiter.wait_if_needed('tse')

        try:
            start_time = time.time()
            assets = self.tse_client.get_asset_data(year)
            api_time = time.time() - start_time

            self.logger.log_api_call('tse', f'assets/{year}', 'success', api_time)
            print(f"    ✅ TSE asset data fetched: {len(assets)} records ({api_time:.1f}s)")
            return assets
        except Exception as e:
            self.logger.log_api_call('tse', f'assets/{year}', 'error', 0)
            print(f"    ❌ TSE asset fetch failed: {e}")
            return []

    def _build_asset_records(self, politician_id: int, assets: List[Dict], year: int) -> List[Dict]:
        """Build asset records from TSE data"""
        records = []

        for asset in assets:
            # Parse Brazilian currency format
            declared_value = self._parse_brazilian_currency(asset.get('VR_BEM_CANDIDATO', '0,00'))

            # Parse dates
            last_update_date = self._parse_brazilian_date(asset.get('DT_ULT_ATUAL_BEM_CANDIDATO'))
            data_generation_date = self._parse_brazilian_date(asset.get('DT_GERACAO'))

            # Build record following database schema (no source_system field)
            record = {
                'politician_id': politician_id,
                'asset_sequence': self._parse_int(asset.get('NR_ORDEM_BEM_CANDIDATO')),
                'asset_type_code': self._parse_int(asset.get('CD_TIPO_BEM_CANDIDATO')),
                'asset_type_description': self._smart_truncate(asset.get('DS_TIPO_BEM_CANDIDATO', ''), 100),
                'asset_description': self._smart_truncate(asset.get('DS_BEM_CANDIDATO', ''), 5000),
                'declared_value': declared_value,
                'currency': 'BRL',
                'declaration_year': year,
                'election_year': year,
                'last_update_date': last_update_date,
                'data_generation_date': data_generation_date
            }

            # Only add records with valid asset sequence and value
            if record['asset_sequence'] is not None and declared_value > 0:
                records.append(record)

        return records

    def _parse_brazilian_currency(self, value_str: str) -> float:
        """Parse Brazilian currency format: 1.234.567,89 → 1234567.89"""
        if not value_str or value_str.strip() == '':
            return 0.0

        try:
            # Remove thousands separators and replace decimal comma
            clean_value = value_str.replace('.', '').replace(',', '.')
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0

    def _parse_brazilian_date(self, date_str: str) -> Optional[str]:
        """Parse Brazilian date format: DD/MM/YYYY → YYYY-MM-DD"""
        if not date_str:
            return None

        try:
            # Handle DD/MM/YYYY format
            if '/' in date_str:
                day, month, year = date_str.split('/')
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            return None
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value) -> Optional[int]:
        """Safely parse integer values"""
        if value is None or value == '':
            return None

        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Smart truncation that preserves meaningful content"""
        if not text:
            return ''

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

    def _insert_asset_records(self, records: List[Dict], force_refresh: bool = False) -> int:
        """Insert asset records into database with conflict resolution"""
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

                if force_refresh:
                    # Use UPSERT for force refresh
                    sql = f"""
                        INSERT INTO politician_assets ({', '.join(fields)})
                        VALUES ({', '.join(placeholders)})
                        ON CONFLICT (politician_id, declaration_year, asset_sequence)
                        DO UPDATE SET
                            declared_value = EXCLUDED.declared_value,
                            asset_description = EXCLUDED.asset_description,
                            last_update_date = EXCLUDED.last_update_date,
                            data_generation_date = EXCLUDED.data_generation_date
                    """
                else:
                    # Skip duplicates
                    sql = f"""
                        INSERT INTO politician_assets ({', '.join(fields)})
                        VALUES ({', '.join(placeholders)})
                        ON CONFLICT (politician_id, declaration_year, asset_sequence) DO NOTHING
                    """

                result = database.execute_update(sql, tuple(values))
                if result > 0:
                    inserted_count += 1

            except Exception as e:
                print(f"      ⚠️ Database insert error: {e}")

                # Enhanced error logging
                if hasattr(self, 'logger'):
                    self.logger.log_processing(
                        'asset_insertion',
                        f"politician_{record.get('politician_id', 'unknown')}",
                        'error',
                        {
                            'error': str(e),
                            'asset_sequence': record.get('asset_sequence'),
                            'declared_value': record.get('declared_value')
                        }
                    )
                continue

        return inserted_count

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs with SQ_CANDIDATO data"""
        if not politician_ids:
            return []

        placeholders = ', '.join(['%s'] * len(politician_ids))
        query = f"""
            SELECT id, cpf, nome_civil, sq_candidato_current
            FROM unified_politicians
            WHERE id IN ({placeholders})
        """

        return database.execute_query(query, tuple(politician_ids))