"""
Event Populator Module
Populates the politician_events table from parliamentary activities
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
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


class EventPopulator:
    """Populates events from parliamentary activities"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.deputados_client = DeputadosClient()

    def populate(self, politician_ids: Optional[List[int]] = None, days_back: int = 365) -> None:
        """Populate events table"""
        print("📅 EVENTS POPULATION")
        print("=" * 50)

        enhanced_logger.log_processing("event_population", "session", "started",
                                      {"politician_ids": politician_ids, "days_back": days_back})

        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = self.db.get_politicians_for_processing(active_only=False)

        print(f"Processing {len(politicians)} politicians")
        print(f"Collecting events from last {days_back} days")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        print(f"Date range: {start_date_str} to {end_date_str}")

        event_records = []
        processed = 0
        errors = 0

        for politician in politicians:
            try:
                politician_id = politician['id']
                deputy_id = politician['deputy_id']

                if not deputy_id:
                    enhanced_logger.log_processing("politician", politician_id, "warning",
                                                  {"reason": "no_deputy_id", "name": politician['nome_civil']})
                    continue

                print(f"\n📅 Processing events for {politician['nome_civil']}")
                print(f"        DEBUG: Deputy ID: {deputy_id}")
                print(f"        DEBUG: Date range: {start_date_str} to {end_date_str}")

                # Get deputy events
                print(f"        DEBUG: Fetching events...")
                api_start = time.time()
                events = self.deputados_client.get_deputy_events(
                    deputy_id, start_date_str, end_date_str
                )
                api_time = time.time() - api_start
                enhanced_logger.log_api_call("DEPUTADOS", f"events/{deputy_id}", "success", api_time,
                                            {"deputy_id": deputy_id, "start_date": start_date_str,
                                             "end_date": end_date_str, "records_received": len(events)})
                print(f"        DEBUG: Received {len(events)} events")

                for i, event in enumerate(events):
                    if i < 3:  # Only log first 3 events to avoid spam
                        print(f"        DEBUG: Event {i+1}: {event}")
                    event_record = {
                        'politician_id': politician_id,
                        'event_id': str(event.get('id', '')),
                        'event_type': event.get('descricaoTipo'),
                        'event_description': event.get('descricao'),
                        'start_datetime': self._parse_datetime(event.get('dataHoraInicio')),
                        'end_datetime': self._parse_datetime(event.get('dataHoraFim')),
                        'duration_minutes': self._calculate_duration(event.get('dataHoraInicio'), event.get('dataHoraFim')),
                        'location_building': event.get('localCamara', {}).get('nome') if event.get('localCamara') else None,
                        'location_room': event.get('localCamara', {}).get('andar') if event.get('localCamara') else None,
                        'event_status': event.get('situacao'),
                        'created_at': datetime.now().isoformat()
                    }
                    event_records.append(event_record)

                processed += 1
                enhanced_logger.log_processing("politician_events", politician_id, "success",
                                              {"events_count": len(events), "name": politician['nome_civil']})
                print(f"  ✅ Added {len(events)} events")

            except Exception as e:
                errors += 1
                enhanced_logger.log_processing("politician_events", politician_id, "error",
                                              {"error": str(e), "name": politician.get('nome_civil', 'Unknown')})
                print(f"  ❌ Error processing politician {politician_id}: {e}")
                import traceback
                print(f"      DEBUG: Traceback: {traceback.format_exc()}")
                continue

        # Bulk insert
        if event_records:
            self.db.bulk_insert_records('politician_events', event_records)
            enhanced_logger.log_processing("bulk_insert", "politician_events", "success",
                                          {"records_inserted": len(event_records)})

        print(f"\n✅ Inserted {len(event_records)} event records")
        print(f"Processed: {processed}, Errors: {errors}")
        enhanced_logger.save_session_metrics()

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict[str, Any]]:
        """Get specific politicians by IDs"""
        placeholders = ', '.join(['?' for _ in politician_ids])
        query = f"SELECT id, deputy_id, nome_civil FROM unified_politicians WHERE id IN ({placeholders})"
        results = self.db.execute_query(query, tuple(politician_ids))
        return [dict(row) for row in results]

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None
        try:
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[str]:
        """Parse datetime string to ISO format"""
        if not date_str:
            return None
        try:
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def _calculate_duration(self, start_str: Optional[str], end_str: Optional[str]) -> Optional[int]:
        """Calculate duration in minutes between start and end times"""
        if not start_str or not end_str:
            return None
        try:
            start_dt = None
            end_dt = None

            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                if not start_dt:
                    try:
                        start_dt = datetime.strptime(start_str, fmt)
                    except ValueError:
                        continue
                if not end_dt:
                    try:
                        end_dt = datetime.strptime(end_str, fmt)
                    except ValueError:
                        continue

            if start_dt and end_dt:
                duration = end_dt - start_dt
                return int(duration.total_seconds() / 60)
            return None
        except Exception:
            return None