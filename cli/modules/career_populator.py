"""
Career Populator Module
Populates the politician_career_history table from external mandates
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


class CareerPopulator:
    """Populates career history from external mandates"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.deputados_client = DeputadosClient()

    def populate(self, politician_ids: Optional[List[int]] = None) -> None:
        """Populate career history table"""
        print("📋 CAREER HISTORY POPULATION")
        print("=" * 50)

        enhanced_logger.log_processing("career_population", "session", "started",
                                      {"politician_ids": politician_ids})

        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = self.db.get_politicians_for_processing(active_only=False)

        print(f"Processing {len(politicians)} politicians")

        career_records = []
        processed = 0

        for politician in politicians:
            try:
                politician_id = politician['id']
                deputy_id = politician['deputy_id']

                if not deputy_id:
                    enhanced_logger.log_processing("politician", politician_id, "warning",
                                                  {"reason": "no_deputy_id", "name": politician['nome_civil']})
                    continue

                print(f"\n📝 Processing career for {politician['nome_civil']}")

                # Get external mandates
                api_start = time.time()
                mandates = self.deputados_client.get_deputy_external_mandates(deputy_id)
                api_time = time.time() - api_start
                enhanced_logger.log_api_call("DEPUTADOS", f"external_mandates/{deputy_id}", "success", api_time,
                                            {"deputy_id": deputy_id, "records_received": len(mandates)})

                for mandate in mandates:
                    career_record = {
                        'politician_id': politician_id,
                        'office_name': mandate.get('cargo'),
                        'state': mandate.get('siglaUf'),
                        'municipality': mandate.get('municipio'),
                        'start_year': int(mandate.get('anoInicio')) if mandate.get('anoInicio') else None,
                        'end_year': int(mandate.get('anoFim')) if mandate.get('anoFim') else None,
                        'party_at_election': mandate.get('siglaPartidoEleicao'),
                        'source_system': 'DEPUTADOS',
                        'created_at': datetime.now().isoformat()
                    }
                    career_records.append(career_record)

                processed += 1
                enhanced_logger.log_processing("politician_career", politician_id, "success",
                                              {"career_records": len(mandates), "name": politician['nome_civil']})
                print(f"  ✅ Added {len(mandates)} career records")

            except Exception as e:
                enhanced_logger.log_processing("politician_career", politician_id, "error",
                                              {"error": str(e), "name": politician.get('nome_civil', 'Unknown')})
                print(f"  ❌ Error processing politician {politician_id}: {e}")

        # Bulk insert
        if career_records:
            self.db.bulk_insert_records('politician_career_history', career_records)
            enhanced_logger.log_processing("bulk_insert", "politician_career_history", "success",
                                          {"records_inserted": len(career_records)})

        print(f"\n✅ Inserted {len(career_records)} career records")
        enhanced_logger.save_session_metrics()

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict[str, Any]]:
        """Get specific politicians by IDs"""
        placeholders = ', '.join(['?' for _ in politician_ids])
        query = f"SELECT id, deputy_id, nome_civil FROM unified_politicians WHERE id IN ({placeholders})"
        results = self.db.execute_query(query, tuple(politician_ids))
        return [dict(row) for row in results]