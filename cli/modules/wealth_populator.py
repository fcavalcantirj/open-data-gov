"""
Wealth Populator Module
Populates the unified_wealth_tracking table from TSE asset declarations
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.clients.tse_client import TSEClient
from cli.modules.database_manager import DatabaseManager

# Import enhanced logger
try:
    from cli.modules.enhanced_logger import enhanced_logger
except:
    # Fallback if enhanced logger not available
    class DummyLogger:
        def log_processing(self, *args, **kwargs): pass
        def log_api_call(self, *args, **kwargs): pass
        def log_data_issue(self, *args, **kwargs): pass
        def save_session_metrics(self): pass
    enhanced_logger = DummyLogger()


class WealthPopulator:
    """Populates wealth tracking from TSE asset declarations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None) -> None:
        """Populate wealth tracking table"""
        print("💎 WEALTH TRACKING POPULATION")
        print("=" * 50)

        enhanced_logger.log_processing("wealth_population", "session", "started",
                                      {"politician_ids": politician_ids})

        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = self.db.get_politicians_for_processing(active_only=False)

        print(f"Processing {len(politicians)} politicians")

        wealth_records = []
        processed = 0

        for politician in politicians:
            try:
                politician_id = politician['id']
                cpf = politician['cpf']
                sq_candidato = politician['sq_candidato_current']

                if not sq_candidato:
                    print(f"\n⚠️ No SQ_CANDIDATO for {politician['nome_civil']}, skipping")
                    continue

                print(f"\n💰 Processing wealth for {politician['nome_civil']}")
                print(f"        DEBUG: Using SQ_CANDIDATO: {sq_candidato}")

                # Get TSE asset data
                asset_data = self._get_tse_asset_data(sq_candidato)

                # Group by year and create wealth summary
                yearly_wealth = self._group_assets_by_year(asset_data)

                for year, assets in yearly_wealth.items():
                    wealth_record = {
                        'politician_id': politician_id,
                        'year': year,
                        'election_year': year,
                        'total_declared_wealth': sum(self._parse_currency_value(a.get('VR_BEM_CANDIDATO', '0')) for a in assets),
                        'number_of_assets': len(assets),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    wealth_records.append(wealth_record)

                processed += 1
                print(f"  ✅ Added {len(yearly_wealth)} wealth records")

            except Exception as e:
                print(f"  ❌ Error processing politician {politician_id}: {e}")

        # Bulk insert
        if wealth_records:
            self.db.bulk_insert_records('unified_wealth_tracking', wealth_records)

        print(f"\n✅ Inserted {len(wealth_records)} wealth records")
        enhanced_logger.save_session_metrics()

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict[str, Any]]:
        """Get specific politicians by IDs"""
        placeholders = ', '.join(['?' for _ in politician_ids])
        query = f"SELECT id, cpf, sq_candidato_current, nome_civil FROM unified_politicians WHERE id IN ({placeholders})"
        results = self.db.execute_query(query, tuple(politician_ids))
        return [dict(row) for row in results]

    def _get_tse_asset_data(self, sq_candidato: str) -> List[Dict[str, Any]]:
        """Get TSE asset declarations for politician using SQ_CANDIDATO"""
        all_assets = []

        try:
            # Get asset data for recent years
            for year in [2022, 2024]:
                try:
                    print(f"      → Searching {year} asset data...")
                    print(f"        DEBUG: Requesting asset data for year {year}")
                    year_assets = self.tse_client.get_asset_data(year)
                    print(f"        DEBUG: Received {len(year_assets)} total asset records")

                    # Debug SQ_CANDIDATO matching
                    print(f"        DEBUG: Looking for SQ_CANDIDATO {sq_candidato}")

                    # Filter for this politician's SQ_CANDIDATO
                    politician_assets = []
                    for row in year_assets:
                        asset_sq_candidato = row.get('SQ_CANDIDATO')
                        if asset_sq_candidato and str(asset_sq_candidato) == str(sq_candidato):
                            politician_assets.append(row)
                            print(f"        DEBUG: Found matching asset! SQ_CANDIDATO: {asset_sq_candidato}")

                    if politician_assets:
                        enhanced_logger.log_processing(f"asset_match_{year}", sq_candidato, "success",
                                                      {"matches_found": len(politician_assets), "year": year})
                    all_assets.extend(politician_assets)
                    print(f"        ✓ Found {len(politician_assets)} assets in {year}")

                except Exception as e:
                    enhanced_logger.log_api_call("TSE", f"assets/{year}", "error", 0,
                                                {"year": year, "error": str(e)})
                    print(f"      ⚠️ Error getting {year} asset data: {e}")
                    import traceback
                    print(f"        DEBUG: Traceback: {traceback.format_exc()}")
                    continue

        except Exception as e:
            print(f"    ⚠️ Error in TSE asset data collection: {e}")
            import traceback
            print(f"      DEBUG: Traceback: {traceback.format_exc()}")

        print(f"    ✓ Collected {len(all_assets)} TSE assets")
        return all_assets

    def _parse_currency_value(self, value_str: Optional[str]) -> float:
        """Parse Brazilian currency format (80000,00) to float"""
        if not value_str:
            return 0.0
        try:
            # Replace comma with dot for decimal point (Brazilian format)
            value_str = str(value_str).replace(',', '.')
            return float(value_str)
        except:
            return 0.0

    def _group_assets_by_year(self, assets: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """Group assets by election year"""
        yearly_assets = {}
        for asset in assets:
            year = int(asset.get('ANO_ELEICAO', 0))
            if year not in yearly_assets:
                yearly_assets[year] = []
            yearly_assets[year].append(asset)
        return yearly_assets