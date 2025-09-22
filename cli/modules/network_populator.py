"""
Network Populator Module
Populates the unified_political_networks table
Implements committees, fronts, coalitions, and federations
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.clients.deputados_client import DeputadosClient
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


class NetworkPopulator:
    """Populates political networks from deputados and TSE data"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.deputados_client = DeputadosClient()
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None) -> None:
        """Populate political networks table"""
        print("🤝 POLITICAL NETWORKS POPULATION")
        print("=" * 50)

        enhanced_logger.log_processing("network_population", "session", "started",
                                      {"politician_ids": politician_ids})

        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = self.db.get_politicians_for_processing(active_only=True)

        print(f"Processing {len(politicians)} politicians")

        networks = []
        processed = 0

        for politician in politicians:
            try:
                politician_id = politician['id']
                deputy_id = politician['deputy_id']
                politician_networks = []

                print(f"\n🏛️ Processing networks for {politician['nome_civil']}")

                # Get committee memberships
                if deputy_id:
                    print(f"  📋 Fetching committees...")
                    api_start = time.time()
                    committees = self.deputados_client.get_deputy_committees(deputy_id)
                    api_time = time.time() - api_start
                    enhanced_logger.log_api_call("DEPUTADOS", f"committees/{deputy_id}", "success", api_time,
                                                {"deputy_id": deputy_id, "records_received": len(committees)})
                else:
                    committees = []
                for committee in committees:
                    network = {
                        'politician_id': politician_id,
                        'network_type': 'COMMITTEE',
                        'network_id': str(committee.get('id', '')),
                        'network_name': committee.get('nome', ''),
                        'role': committee.get('titulo'),
                        'start_date': self._parse_date(committee.get('dataInicio')),
                        'end_date': self._parse_date(committee.get('dataFim')),
                        'year': datetime.now().year,
                        'source_system': 'DEPUTADOS',
                        'created_at': datetime.now().isoformat()
                    }
                    politician_networks.append(network)

                # Get parliamentary fronts
                if deputy_id:
                    print(f"  🏛️ Fetching fronts...")
                    api_start = time.time()
                    fronts = self.deputados_client.get_deputy_fronts(deputy_id)
                    api_time = time.time() - api_start
                    enhanced_logger.log_api_call("DEPUTADOS", f"fronts/{deputy_id}", "success", api_time,
                                                {"deputy_id": deputy_id, "records_received": len(fronts)})
                else:
                    fronts = []
                for front in fronts:
                    network = {
                        'politician_id': politician_id,
                        'network_type': 'PARLIAMENTARY_FRONT',
                        'network_id': str(front.get('id', '')),
                        'network_name': front.get('titulo', ''),
                        'year': datetime.now().year,
                        'legislature_id': front.get('idLegislatura'),
                        'source_system': 'DEPUTADOS',
                        'created_at': datetime.now().isoformat()
                    }
                    politician_networks.append(network)

                # Insert networks for this politician immediately
                if politician_networks:
                    print(f"  💾 Inserting {len(politician_networks)} network records...")
                    self.db.bulk_insert_records('unified_political_networks', politician_networks)
                    enhanced_logger.log_processing("bulk_insert_politician", politician_id, "success",
                                                  {"records_inserted": len(politician_networks)})
                    networks.extend(politician_networks)

                processed += 1
                enhanced_logger.log_processing("politician_networks", politician_id, "success",
                                              {"committees_count": len(committees), "fronts_count": len(fronts),
                                               "name": politician['nome_civil']})
                print(f"  ✅ Added {len(committees)} committees, {len(fronts)} fronts")

            except Exception as e:
                enhanced_logger.log_processing("politician_networks", politician_id, "error",
                                              {"error": str(e), "name": politician.get('nome_civil', 'Unknown')})
                print(f"  ❌ Error processing politician {politician_id}: {e}")
                import traceback
                print(f"      DEBUG: Traceback: {traceback.format_exc()}")
                continue  # Continue to next politician even if one fails

        print(f"\n✅ Inserted {len(networks)} network records")
        enhanced_logger.save_session_metrics()

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict[str, Any]]:
        """Get specific politicians by IDs"""
        placeholders = ', '.join(['?' for _ in politician_ids])
        query = f"SELECT id, deputy_id, nome_civil FROM unified_politicians WHERE id IN ({placeholders})"
        results = self.db.execute_query(query, tuple(politician_ids))
        return [dict(row) for row in results]

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string"""
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.date().isoformat()
        except:
            return None