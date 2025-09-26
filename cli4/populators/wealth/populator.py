"""
CLI4 Wealth Populator
Populate unified_wealth_tracking table with TSE asset declarations and wealth progression analysis
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker
from src.clients.tse_client import TSEClient


class CLI4WealthPopulator:
    """Populate unified_wealth_tracking table with comprehensive wealth analysis"""

    # Asset categorization mapping based on TSE asset type codes
    ASSET_CATEGORIES = {
        'real_estate': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Real estate assets
        'vehicles': [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],  # Vehicles
        'investments': [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],  # Financial investments
        'business': [31, 32, 33, 34, 35, 36, 37, 38, 39, 40],  # Business interests
        'cash_deposits': [41, 42, 43, 44, 45, 46, 47, 48, 49, 50],  # Cash and deposits
        # All other codes fall into 'other' category
    }

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None,
                 election_years: Optional[List[int]] = None,
                 force_refresh: bool = False) -> int:
        """Main population method for wealth tracking"""

        print("💎 UNIFIED WEALTH TRACKING POPULATION")
        print("=" * 60)
        print("TSE asset declarations with wealth progression analysis")
        print()

        # Check dependencies - wealth optimization NEEDS post-processing!
        DependencyChecker.print_dependency_warning(
            required_steps=["politicians", "postprocess"],
            current_step="WEALTH TRACKING POPULATION (OPTIMIZED)"
        )

        # Additional specific warning about timeline fields
        print("⚠️ NOTE: Wealth populator uses first_election_year and last_election_year")
        print("⚠️       for optimized year selection. Without post-processing, it will")
        print("⚠️       fall back to default years and lose 25% efficiency gain!")
        print()

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = database.execute_query(
                "SELECT id, cpf, sq_candidato_current, nome_civil, first_election_year, last_election_year FROM unified_politicians WHERE cpf IS NOT NULL"
            )

        print(f"👥 Processing {len(politicians)} politicians with CPF")

        # Set election years to process (default: recent elections)
        if not election_years:
            election_years = [2018, 2020, 2022, 2024]

        print(f"📅 Election years: {', '.join(map(str, election_years))}")
        print()

        total_records = 0
        processed_politicians = 0

        for i, politician in enumerate(politicians, 1):
            print(f"\n💰 [{i}/{len(politicians)}] Processing: {politician['nome_civil'][:40]}")
            print(f"   ID: {politician['id']} | SQ_CANDIDATO: {politician.get('sq_candidato_current', 'None')}")

            try:
                # Check if already processed (skip if force_refresh is True)
                if not force_refresh:
                    existing_count = self._count_existing_records(politician['id'])
                    if existing_count > 0:
                        print(f"   ⏭️ Skipping - already has {existing_count} wealth records")
                        continue
                else:
                    print(f"   🔄 Force refresh enabled - processing anyway")

                # Process wealth data for this politician
                wealth_records = self._process_politician_wealth(politician, election_years)

                if wealth_records:
                    inserted = self._insert_wealth_records(wealth_records)
                    total_records += inserted
                    processed_politicians += 1
                    print(f"   ✅ Inserted {inserted} wealth tracking records")

                    self.logger.log_processing(
                        'wealth_tracking', str(politician['id']), 'success',
                        {'records_count': inserted, 'years_processed': len(wealth_records)}
                    )
                else:
                    print(f"   ⚪ No wealth data found")

            except Exception as e:
                print(f"   ❌ Error processing politician {politician['id']}: {e}")
                self.logger.log_processing(
                    'wealth_tracking', str(politician['id']), 'error',
                    {'error': str(e)}
                )
                continue

        print(f"\n✅ WEALTH TRACKING POPULATION COMPLETED")
        print(f"   Total records: {total_records}")
        print(f"   Politicians processed: {processed_politicians}")
        print(f"   Politicians with data: {processed_politicians}/{len(politicians)}")

        return total_records

    def _process_politician_wealth(self, politician: Dict, election_years: List[int]) -> List[Dict]:
        """Process wealth data for a single politician across all election years"""
        wealth_records = []
        cpf = politician['cpf']
        sq_candidato = politician.get('sq_candidato_current')

        if not sq_candidato:
            print(f"   ⚠️ No SQ_CANDIDATO for correlation, skipping")
            return []

        # Get dynamic years based on politician activity
        relevant_years = self._calculate_relevant_years(politician, election_years)
        print(f"   📊 Processing years: {relevant_years}")

        all_assets_by_year = {}

        # Collect assets for all relevant years
        for year in relevant_years:
            try:
                print(f"      🗳️ Fetching {year} asset data...")
                year_assets = self._get_politician_assets(sq_candidato, year)

                if year_assets:
                    all_assets_by_year[year] = year_assets
                    print(f"         ✓ Found {len(year_assets)} assets")
                else:
                    print(f"         ⚪ No assets found")

                # Rate limiting between years
                self.rate_limiter.wait_if_needed('tse')

            except Exception as e:
                print(f"         ❌ Error fetching {year} assets: {e}")
                continue

        # Process each year and calculate wealth progression
        previous_record = None

        for year in sorted(all_assets_by_year.keys()):
            assets = all_assets_by_year[year]

            wealth_record = self._build_wealth_record(
                politician['id'], year, assets, previous_record
            )

            if wealth_record:
                wealth_records.append(wealth_record)
                previous_record = wealth_record

        return wealth_records

    def _get_politician_assets(self, sq_candidato: str, year: int) -> List[Dict]:
        """Get assets for specific politician and year from TSE"""
        try:
            # Get all asset data for the year
            all_assets = self.tse_client.get_asset_data(year)

            # Filter for this politician's SQ_CANDIDATO
            politician_assets = []
            for asset in all_assets:
                if str(asset.get('SQ_CANDIDATO', '')) == str(sq_candidato):
                    politician_assets.append(asset)

            return politician_assets

        except Exception as e:
            print(f"         ⚠️ TSE asset fetch error: {e}")
            return []

    def _build_wealth_record(self, politician_id: int, year: int,
                           assets: List[Dict], previous_record: Optional[Dict]) -> Optional[Dict]:
        """Build comprehensive wealth record with categorization and progression analysis"""

        if not assets:
            return None

        # Calculate total wealth and asset categories
        total_wealth = Decimal('0.00')
        category_totals = {
            'real_estate_value': Decimal('0.00'),
            'vehicles_value': Decimal('0.00'),
            'investments_value': Decimal('0.00'),
            'business_value': Decimal('0.00'),
            'cash_deposits_value': Decimal('0.00'),
            'other_assets_value': Decimal('0.00')
        }

        # Process each asset
        for asset in assets:
            asset_value = self._parse_brazilian_currency(asset.get('VR_BEM_CANDIDATO', '0'))
            asset_type_code = asset.get('CD_TIPO_BEM_CANDIDATO')

            total_wealth += asset_value

            # Categorize asset
            category = self._categorize_asset(asset_type_code)
            category_field = f"{category}_value"
            if category_field in category_totals:
                category_totals[category_field] += asset_value

        # Get reference date from first asset (TSE election date)
        reference_date = None
        if assets:
            first_asset = assets[0]
            ano_eleicao = first_asset.get('ANO_ELEICAO')
            if ano_eleicao:
                # Use election year as reference (October 1st for general elections)
                reference_date = date(int(ano_eleicao), 10, 1)

        # Build base wealth record
        wealth_record = {
            'politician_id': politician_id,
            'year': year,
            'election_year': year,
            'reference_date': reference_date,
            'total_declared_wealth': float(total_wealth),
            'number_of_assets': len(assets),

            # Asset category totals
            'real_estate_value': float(category_totals['real_estate_value']),
            'vehicles_value': float(category_totals['vehicles_value']),
            'investments_value': float(category_totals['investments_value']),
            'business_value': float(category_totals['business_value']),
            'cash_deposits_value': float(category_totals['cash_deposits_value']),
            'other_assets_value': float(category_totals['other_assets_value']),

            # Default progression fields
            'previous_year': None,
            'previous_total_wealth': None,
            'years_between_declarations': None,

            # Validation flags
            'externally_verified': False,
            'verification_date': None,
            'verification_source': 'TSE_ASSET_DECLARATIONS'
        }

        # Calculate wealth progression if we have previous data
        if previous_record:
            progression = self._calculate_wealth_progression(wealth_record, previous_record)
            wealth_record.update(progression)

        return wealth_record

    def _parse_brazilian_currency(self, value_str: str) -> Decimal:
        """Parse Brazilian currency format with comprehensive error handling"""
        if not value_str:
            return Decimal('0.00')

        try:
            # Convert to string and clean
            clean_value = str(value_str).strip()

            # Handle empty or null values
            if not clean_value or clean_value.upper() in ['NULL', '#NULO#', 'N/A']:
                return Decimal('0.00')

            # Handle Brazilian formats:
            # 1.234.567,89 (thousands with dots, decimal with comma)
            # 1234567,89 (no thousands separator, decimal with comma)
            # 1234567.89 (no thousands separator, decimal with dot)

            # Remove any non-numeric characters except dots and commas
            import re
            clean_value = re.sub(r'[^\d.,]', '', clean_value)

            # Determine if comma is decimal separator or thousands separator
            if ',' in clean_value and '.' in clean_value:
                # Both present - assume Brazilian format (dots=thousands, comma=decimal)
                clean_value = clean_value.replace('.', '').replace(',', '.')
            elif ',' in clean_value:
                # Only comma - check if it's likely decimal separator
                comma_pos = clean_value.rfind(',')
                if len(clean_value) - comma_pos <= 3:  # 2 digits or less after comma = decimal
                    clean_value = clean_value.replace(',', '.')
                else:
                    # Likely thousands separator
                    clean_value = clean_value.replace(',', '')
            # If only dots, assume already correct format

            return Decimal(clean_value)

        except (InvalidOperation, ValueError, TypeError):
            print(f"         ⚠️ Currency parsing error for value: '{value_str}', using 0.00")
            return Decimal('0.00')

    def _categorize_asset(self, asset_type_code: Optional[int]) -> str:
        """Categorize asset based on TSE asset type code"""
        if not asset_type_code:
            return 'other'

        try:
            code = int(asset_type_code)

            for category, codes in self.ASSET_CATEGORIES.items():
                if code in codes:
                    return category

            return 'other'  # Default for unknown codes

        except (ValueError, TypeError):
            return 'other'

    def _calculate_wealth_progression(self, current_record: Dict, previous_record: Dict) -> Dict:
        """Calculate wealth progression between declarations"""
        current_wealth = Decimal(str(current_record['total_declared_wealth']))
        previous_wealth = Decimal(str(previous_record['total_declared_wealth']))
        current_year = current_record['year']
        previous_year = previous_record['year']
        years_diff = current_year - previous_year

        return {
            'previous_year': previous_year,
            'previous_total_wealth': float(previous_wealth),
            'years_between_declarations': years_diff
        }

    def _calculate_relevant_years(self, politician: Dict, election_years: List[int]) -> List[int]:
        """Calculate relevant election years based on politician timeline and TSE data availability"""

        # Known years with TSE data (skip 2020 - no candidate packages available)
        available_years = [2014, 2016, 2018, 2022, 2024]

        # Get politician timeline from database fields
        first_year = politician.get('first_election_year')
        last_year = politician.get('last_election_year')

        # Fallback strategy for politicians without timeline data
        if not first_year or not last_year:
            # Use safe recent years with known TSE data
            fallback_years = [year for year in [2018, 2022, 2024] if year in available_years]
            print(f"      ⚠️ No timeline data, using fallback: {fallback_years}")
            return fallback_years

        smart_years = set()

        # 1. Add years during active political career
        for year in available_years:
            if first_year <= year <= last_year:
                smart_years.add(year)

        # 2. Add pre-career baseline (2 years before first election for wealth baseline)
        prep_year = first_year - 2
        while prep_year >= 2014 and prep_year not in smart_years:
            if prep_year in available_years:
                smart_years.add(prep_year)
                break
            prep_year -= 2

        # 3. Add post-career analysis (2 years after for wealth retention tracking)
        post_year = last_year + 2
        while post_year <= 2024 and post_year not in smart_years:
            if post_year in available_years:
                smart_years.add(post_year)
                break
            post_year += 2

        # 4. Ensure we have at least one recent year for currently active politicians
        if last_year >= 2020:
            recent_years = [2024, 2022, 2018]
            for year in recent_years:
                if year in available_years and year not in smart_years:
                    smart_years.add(year)
                    break

        selected_years = sorted(list(smart_years))

        # Log the optimization decision
        original_count = len([y for y in election_years if y in available_years])
        optimized_count = len(selected_years)

        if optimized_count < original_count:
            print(f"      💰 Optimized: {optimized_count} years vs {original_count} default ({original_count - optimized_count} fewer API calls)")
        elif optimized_count > original_count:
            print(f"      📈 Enhanced coverage: {optimized_count} years vs {original_count} default (+{optimized_count - original_count} for completeness)")
        else:
            print(f"      ⚖️ Same {optimized_count} years but better targeted")

        return selected_years

    def _count_existing_records(self, politician_id: int) -> int:
        """Count existing wealth records for politician"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM unified_wealth_tracking WHERE politician_id = %s",
            (politician_id,)
        )
        return result[0]['count'] if result else 0

    def _insert_wealth_records(self, records: List[Dict]) -> int:
        """Insert wealth records into database with conflict handling"""
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
                    INSERT INTO unified_wealth_tracking ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (politician_id, year) DO UPDATE SET
                        total_declared_wealth = EXCLUDED.total_declared_wealth,
                        number_of_assets = EXCLUDED.number_of_assets,
                        real_estate_value = EXCLUDED.real_estate_value,
                        vehicles_value = EXCLUDED.vehicles_value,
                        investments_value = EXCLUDED.investments_value,
                        business_value = EXCLUDED.business_value,
                        cash_deposits_value = EXCLUDED.cash_deposits_value,
                        other_assets_value = EXCLUDED.other_assets_value,
                        updated_at = CURRENT_TIMESTAMP
                """

                result = database.execute_update(sql, tuple(values))
                if result > 0:
                    inserted_count += 1

            except Exception as e:
                print(f"      ⚠️ Database insert error for record: {e}")
                continue

        return inserted_count

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs"""
        if not politician_ids:
            return []

        placeholders = ', '.join(['%s'] * len(politician_ids))
        query = f"""
            SELECT id, cpf, sq_candidato_current, nome_civil, first_election_year, last_election_year
            FROM unified_politicians
            WHERE id IN ({placeholders}) AND cpf IS NOT NULL
        """

        return database.execute_query(query, tuple(politician_ids))