"""
Asset Populator Module
Populates the politician_assets table from individual TSE asset declarations
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

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


class AssetPopulator:
    """Populates individual assets from TSE declarations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None) -> None:
        """Populate individual assets table"""
        print("🏠 INDIVIDUAL ASSETS POPULATION")
        print("=" * 50)

        enhanced_logger.log_processing("asset_population", "session", "started",
                                      {"politician_ids": politician_ids})

        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = self.db.get_politicians_for_processing(active_only=False)

        print(f"Processing {len(politicians)} politicians")

        asset_records = []
        processed = 0

        for politician in politicians:
            try:
                politician_id = politician['id']
                cpf = politician['cpf']
                sq_candidato = politician['sq_candidato_current']

                if not sq_candidato:
                    print(f"\n⚠️ No SQ_CANDIDATO for {politician['nome_civil']}, skipping")
                    enhanced_logger.log_processing("politician", politician_id, "warning",
                                                  {"reason": "no_sq_candidato", "name": politician['nome_civil']})
                    continue

                print(f"\n🏘️ Processing assets for {politician['nome_civil']}")
                print(f"        DEBUG: Using SQ_CANDIDATO: {sq_candidato}")

                # Get individual asset records
                assets = self._get_individual_assets(sq_candidato)

                for asset in assets:
                    # Truncate long descriptions to avoid VARCHAR constraint errors
                    type_desc = asset.get('DS_TIPO_BEM_CANDIDATO')
                    if type_desc and len(type_desc) > 100:
                        enhanced_logger.log_data_issue("varchar_truncation",
                                                      f"Asset type description truncated from {len(type_desc)} chars",
                                                      type_desc)
                        type_desc = type_desc[:97] + '...'

                    asset_record = {
                        'politician_id': politician_id,
                        'asset_sequence': int(asset.get('NR_ORDEM_BEM_CANDIDATO', 0)) if asset.get('NR_ORDEM_BEM_CANDIDATO') else None,
                        'asset_type_code': int(asset.get('CD_TIPO_BEM_CANDIDATO', 0)) if asset.get('CD_TIPO_BEM_CANDIDATO') else None,
                        'asset_type_description': type_desc,
                        'asset_description': asset.get('DS_BEM_CANDIDATO'),
                        'declared_value': self._parse_currency_value(asset.get('VR_BEM_CANDIDATO', '0')),
                        'declaration_year': int(asset.get('ANO_ELEICAO', 0)) if asset.get('ANO_ELEICAO') else None,
                        'election_year': int(asset.get('ANO_ELEICAO', 0)) if asset.get('ANO_ELEICAO') else None,
                        'last_update_date': self._parse_date(asset.get('DT_ULT_ATUAL_BEM_CANDIDATO')),
                        'data_generation_date': self._parse_date(asset.get('DT_GERACAO')),
                        'created_at': datetime.now().isoformat()
                    }
                    asset_records.append(asset_record)

                processed += 1
                print(f"  ✅ Added {len(assets)} individual assets")
                enhanced_logger.log_processing("politician_assets", politician_id, "success",
                                              {"assets_count": len(assets), "name": politician['nome_civil']})

            except Exception as e:
                print(f"  ❌ Error processing politician {politician_id}: {e}")
                enhanced_logger.log_processing("politician_assets", politician_id, "error",
                                              {"error": str(e), "name": politician.get('nome_civil', 'Unknown')})

        # Bulk insert
        if asset_records:
            self.db.bulk_insert_records('politician_assets', asset_records)
            enhanced_logger.log_processing("bulk_insert", "politician_assets", "success",
                                          {"records_inserted": len(asset_records)})

        print(f"\n✅ Inserted {len(asset_records)} asset records")
        enhanced_logger.save_session_metrics()

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict[str, Any]]:
        """Get specific politicians by IDs"""
        placeholders = ', '.join(['?' for _ in politician_ids])
        query = f"SELECT id, cpf, sq_candidato_current, nome_civil FROM unified_politicians WHERE id IN ({placeholders})"
        results = self.db.execute_query(query, tuple(politician_ids))
        return [dict(row) for row in results]

    def _get_individual_assets(self, sq_candidato: str) -> List[Dict[str, Any]]:
        """Get individual TSE asset records for politician using SQ_CANDIDATO"""
        all_assets = []

        try:
            # Get asset data for recent years
            for year in [2022, 2024]:
                try:
                    print(f"      → Searching {year} asset data...")
                    print(f"        DEBUG: Requesting asset data for year {year}")
                    api_start = time.time()
                    year_assets = self.tse_client.get_asset_data(year)
                    api_time = time.time() - api_start
                    enhanced_logger.log_api_call("TSE", f"assets/{year}", "success", api_time,
                                                {"year": year, "records_received": len(year_assets)})
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
                    print(f"      ⚠️ Error getting {year} asset data: {e}")
                    import traceback
                    print(f"        DEBUG: Traceback: {traceback.format_exc()}")
                    enhanced_logger.log_api_call("TSE", f"assets/{year}", "error", 0,
                                                {"year": year, "error": str(e)})
                    continue

        except Exception as e:
            print(f"    ⚠️ Error in TSE individual asset collection: {e}")
            import traceback
            print(f"      DEBUG: Traceback: {traceback.format_exc()}")

        print(f"    ✓ Collected {len(all_assets)} individual assets")
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

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string - handles both Brazilian DD/MM/YYYY and ISO YYYY-MM-DD formats"""
        if not date_str:
            return None
        try:
            # Try Brazilian format first (DD/MM/YYYY)
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return dt.date().isoformat()
        except:
            try:
                # Fallback to ISO format (YYYY-MM-DD)
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.date().isoformat()
            except:
                return None