"""
Professional Populator Module
Populates the politician_professional_background table
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


class ProfessionalPopulator:
    """Populates professional background from professions and occupations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.deputados_client = DeputadosClient()

    def populate(self, politician_ids: Optional[List[int]] = None) -> None:
        """Populate professional background table"""
        print("🎓 PROFESSIONAL BACKGROUND POPULATION")
        print("=" * 50)

        enhanced_logger.log_processing("professional_population", "session", "started",
                                      {"politician_ids": politician_ids})

        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = self.db.get_politicians_for_processing(active_only=False)

        print(f"Processing {len(politicians)} politicians")

        professional_records = []
        processed = 0

        for politician in politicians:
            try:
                politician_id = politician['id']
                deputy_id = politician['deputy_id']

                if not deputy_id:
                    enhanced_logger.log_processing("politician", politician_id, "warning",
                                                  {"reason": "no_deputy_id", "name": politician['nome_civil']})
                    continue

                print(f"\n👨‍💼 Processing professional background for {politician['nome_civil']}")
                print(f"        DEBUG: Deputy ID: {deputy_id}")

                # Get professions
                print(f"        DEBUG: Fetching professions...")
                api_start = time.time()
                professions = self.deputados_client.get_deputy_professions(deputy_id)
                api_time = time.time() - api_start
                enhanced_logger.log_api_call("DEPUTADOS", f"professions/{deputy_id}", "success", api_time,
                                            {"deputy_id": deputy_id, "records_received": len(professions)})
                print(f"        DEBUG: Received {len(professions)} professions")
                for profession in professions:
                    print(f"        DEBUG: Profession: {profession}")
                    record = {
                        'politician_id': politician_id,
                        'profession_type': 'PROFESSION',
                        'profession_code': int(profession.get('codTipoProfissao')) if profession.get('codTipoProfissao') else None,
                        'profession_name': profession.get('titulo'),
                        'source_system': 'DEPUTADOS',
                        'created_at': datetime.now().isoformat()
                    }
                    professional_records.append(record)

                # Get occupations
                print(f"        DEBUG: Fetching occupations...")
                api_start = time.time()
                occupations = self.deputados_client.get_deputy_occupations(deputy_id)
                api_time = time.time() - api_start
                enhanced_logger.log_api_call("DEPUTADOS", f"occupations/{deputy_id}", "success", api_time,
                                            {"deputy_id": deputy_id, "records_received": len(occupations)})
                print(f"        DEBUG: Received {len(occupations)} occupations")
                for occupation in occupations:
                    print(f"        DEBUG: Occupation: {occupation}")
                    record = {
                        'politician_id': politician_id,
                        'profession_type': 'OCCUPATION',
                        'profession_name': occupation.get('titulo'),
                        'entity_name': occupation.get('entidade'),
                        'year_start': int(occupation.get('anoInicio')) if occupation.get('anoInicio') else None,
                        'year_end': int(occupation.get('anoFim')) if occupation.get('anoFim') else None,
                        'entity_state': occupation.get('entidadeUf'),
                        'entity_country': occupation.get('entidadePais'),
                        'source_system': 'DEPUTADOS',
                        'created_at': datetime.now().isoformat()
                    }
                    professional_records.append(record)

                processed += 1
                enhanced_logger.log_processing("politician_professional", politician_id, "success",
                                              {"professions_count": len(professions), "occupations_count": len(occupations),
                                               "name": politician['nome_civil']})
                print(f"  ✅ Added {len(professions)} professions, {len(occupations)} occupations")

            except Exception as e:
                enhanced_logger.log_processing("politician_professional", politician_id, "error",
                                              {"error": str(e), "name": politician.get('nome_civil', 'Unknown')})
                print(f"  ❌ Error processing politician {politician_id}: {e}")
                import traceback
                print(f"      DEBUG: Traceback: {traceback.format_exc()}")

        # Bulk insert
        if professional_records:
            self.db.bulk_insert_records('politician_professional_background', professional_records)
            enhanced_logger.log_processing("bulk_insert", "politician_professional_background", "success",
                                          {"records_inserted": len(professional_records)})

        print(f"\n✅ Inserted {len(professional_records)} professional records")
        enhanced_logger.save_session_metrics()

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict[str, Any]]:
        """Get specific politicians by IDs"""
        placeholders = ', '.join(['?' for _ in politician_ids])
        query = f"SELECT id, deputy_id, nome_civil FROM unified_politicians WHERE id IN ({placeholders})"
        results = self.db.execute_query(query, tuple(politician_ids))
        return [dict(row) for row in results]