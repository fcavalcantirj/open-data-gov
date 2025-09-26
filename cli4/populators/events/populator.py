"""
CLI4 Events Populator
Populate politician_events table with Deputados parliamentary activity data
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker
from src.clients.deputados_client import DeputadosClient


class EventsPopulator:
    """Populate events table with Deputados parliamentary activity data"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.deputados_client = DeputadosClient()

    def populate(self, politician_ids: Optional[List[int]] = None,
                 days_back: int = 365) -> int:
        """Main population method"""

        print("🏛️ PARLIAMENTARY EVENTS POPULATION")
        print("=" * 60)
        print("Deputados parliamentary activity with session analysis")
        print()

        # Check dependencies
        DependencyChecker.print_dependency_warning(
            required_steps=["politicians"],
            current_step="PARLIAMENTARY EVENTS POPULATION"
        )

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            # Get politicians with deputy_id for API correlation
            politicians = database.execute_query("""
                SELECT id, deputy_id, nome_civil, first_election_year, last_election_year
                FROM unified_politicians
                WHERE deputy_id IS NOT NULL
            """)

        if not politicians:
            print("⚠️ No politicians with deputy_id found for events correlation")
            return 0

        print(f"👥 Processing {len(politicians)} politicians with deputy data")
        print(f"📅 Date range: Up to {days_back} days back (smart calculation per politician)")
        print()

        total_records = 0
        processed_politicians = 0

        for politician in politicians:
            try:
                deputy_id = politician['deputy_id']
                politician_id = politician['id']
                nome_civil = politician['nome_civil']

                print(f"  🔄 Processing {nome_civil} (deputy_id: {deputy_id})")

                # Calculate smart date range for this politician
                start_date, end_date = self._calculate_event_date_range(
                    politician, days_back
                )

                print(f"    📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

                # Fetch events data with rate limiting
                events = self._fetch_events(deputy_id, start_date, end_date)

                if not events:
                    print(f"    ⚠️ No events found")
                    continue

                # Build event records
                event_records = []
                for event in events:
                    record = self._build_event_record(politician_id, event)
                    if record:
                        event_records.append(record)

                # Insert records
                if event_records:
                    inserted = self._insert_event_records(event_records)
                    total_records += inserted
                    print(f"    ✅ {inserted} event records inserted (from {len(events)} events)")

                    # Show event category breakdown
                    self._show_event_breakdown(event_records)
                else:
                    print(f"    ⚠️ No valid event records to insert")

                processed_politicians += 1

                self.logger.log_processing(
                    'events', str(politician_id), 'success',
                    {'events_found': len(events), 'records_inserted': len(event_records)}
                )

            except Exception as e:
                print(f"    ❌ Error processing {politician.get('nome_civil', 'Unknown')}: {e}")
                self.logger.log_processing(
                    'events', str(politician.get('id', 'unknown')), 'error',
                    {'error': str(e)}
                )
                continue

        print(f"\n✅ Events population completed")
        print(f"📊 {total_records} event records inserted")
        print(f"👥 {processed_politicians}/{len(politicians)} politicians processed")

        return total_records

    def _calculate_event_date_range(self, politician: dict, days_back: int) -> Tuple[datetime, datetime]:
        """Calculate career-adaptive date range for events based on politician's timeline"""
        end_date = datetime.now()

        # Get politician's career timeline
        first_election_year = politician.get('first_election_year')
        last_election_year = politician.get('last_election_year')

        if first_election_year:
            career_start = datetime(first_election_year, 1, 1)
            career_years = end_date.year - first_election_year + 1

            # Career-adaptive strategy: go back 1-2 years from earliest significant period
            if career_years <= 3:
                # New politicians: capture their entire career + 1 year before (if reasonable)
                lookback_start = datetime(max(first_election_year - 1, 2010), 1, 1)
                print(f"    💡 New politician ({career_years}y): from {lookback_start.year} (career + 1y buffer)")

            elif career_years <= 8:
                # Mid-career: capture career + 2 years before for context
                lookback_start = datetime(max(first_election_year - 2, 2010), 1, 1)
                print(f"    💡 Mid-career ({career_years}y): from {lookback_start.year} (career + 2y buffer)")

            else:
                # Veterans: focus on recent 3-4 years of activity but include some career context
                recent_years = min(4, career_years // 2)  # Dynamic recent period
                recent_start = datetime(max(end_date.year - recent_years, first_election_year), 1, 1)
                print(f"    💡 Veteran ({career_years}y): recent {recent_years}y activity from {recent_start.year}")
                lookback_start = recent_start

            start_date = lookback_start

        else:
            # No career data - use standard lookback with reasonable minimum
            standard_start = end_date - timedelta(days=days_back)
            # Don't go back before 2010 (reasonable parliamentary activity baseline)
            start_date = max(standard_start, datetime(2010, 1, 1))
            print(f"    💡 Standard {days_back}d range from {start_date.strftime('%Y')} (no career data)")

        return start_date, end_date

    def _fetch_events(self, deputy_id: int, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch events data with rate limiting"""
        wait_time = self.rate_limiter.wait_if_needed('deputados')

        try:
            start_time = time.time()
            events = self.deputados_client.get_deputy_events(
                deputy_id,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            api_time = time.time() - start_time

            self.logger.log_api_call('deputados', f'events/{deputy_id}', 'success', api_time)
            return events
        except Exception as e:
            self.logger.log_api_call('deputados', f'events/{deputy_id}', 'error', 0)
            print(f"      ❌ Events fetch failed: {e}")
            return []

    def _build_event_record(self, politician_id: int, event: Dict) -> Optional[Dict]:
        """Build event record from API data"""
        try:
            # Calculate duration from start/end times
            duration_minutes = self._calculate_duration(
                event.get('dataHoraInicio', ''),
                event.get('dataHoraFim', '')
            )

            # Extract location information
            local_camara = event.get('localCamara', {}) or {}

            # Build record following database schema
            record = {
                'politician_id': politician_id,
                'event_id': self._normalize_text(str(event.get('id', '')), 50),
                'event_type': self._normalize_text(event.get('descricaoTipo', ''), 100),
                'event_description': self._normalize_text(event.get('descricao', ''), 5000),
                'start_datetime': self._parse_datetime(event.get('dataHoraInicio')),
                'end_datetime': self._parse_datetime(event.get('dataHoraFim')),
                'duration_minutes': duration_minutes,
                'location_building': self._normalize_text(local_camara.get('predio', ''), 255),
                'location_room': self._normalize_text(local_camara.get('sala', ''), 255),
                'location_floor': self._normalize_text(local_camara.get('andar', ''), 100),
                'location_external': self._normalize_text(event.get('localExterno', ''), 255),
                'registration_url': self._normalize_text(event.get('urlRegistro', ''), 500),
                'document_url': None,  # Not available in API
                'event_status': self._normalize_text(event.get('situacao', ''), 50),
                'attendance_confirmed': False,  # Default, can be enhanced later
                'event_category': self._categorize_event(event.get('descricaoTipo', ''))
            }

            # Only return record if we have essential data
            if record['event_id'] and record['event_type']:
                return record

            return None

        except Exception as e:
            print(f"        ⚠️ Error building event record: {e}")
            return None

    def _calculate_duration(self, start_time: str, end_time: str) -> Optional[int]:
        """Calculate duration in minutes from start/end times"""
        if not start_time or not end_time:
            return None

        try:
            start_dt = datetime.fromisoformat(start_time.replace('T', ' ').replace('Z', ''))
            end_dt = datetime.fromisoformat(end_time.replace('T', ' ').replace('Z', ''))
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

            # Sanity check: duration should be positive and reasonable (< 24 hours)
            if 0 < duration_minutes < 1440:
                return duration_minutes

        except Exception:
            pass

        return None

    def _parse_datetime(self, datetime_str: str) -> Optional[str]:
        """Parse datetime string for database storage"""
        if not datetime_str:
            return None

        try:
            # Handle various datetime formats from API
            # Format: "2025-09-17T10:00" or "2025-09-17T10:00:00"
            clean_datetime = datetime_str.replace('T', ' ').replace('Z', '')

            # Validate datetime format
            datetime.fromisoformat(clean_datetime)
            return clean_datetime

        except Exception:
            return None

    def _categorize_event(self, event_type: str) -> str:
        """Categorize events by type and importance"""
        if not event_type:
            return 'OTHER'

        event_type_lower = event_type.lower()

        if 'sessão' in event_type_lower:
            return 'SESSION'
        elif 'comissão' in event_type_lower or 'comitê' in event_type_lower:
            return 'COMMITTEE'
        elif 'audiência' in event_type_lower:
            return 'HEARING'
        elif 'reunião' in event_type_lower:
            return 'MEETING'
        elif 'conferência' in event_type_lower or 'seminário' in event_type_lower:
            return 'CONFERENCE'
        else:
            return 'OTHER'

    def _normalize_text(self, text: str, max_length: int) -> Optional[str]:
        """Normalize and truncate text fields"""
        if not text or not text.strip():
            return None

        # Clean and normalize
        text = text.strip()

        # Smart truncation with word boundaries
        if len(text) <= max_length:
            return text

        # Reserve space for ellipsis
        truncate_length = max_length - 3

        # Try to break at word boundary if possible (within last 20 chars)
        if truncate_length > 20:
            last_space = text.rfind(' ', max(0, truncate_length - 20), truncate_length)
            if last_space > truncate_length - 20:
                truncate_length = last_space

        return text[:truncate_length] + '...'

    def _show_event_breakdown(self, event_records: List[Dict]) -> None:
        """Show breakdown of events by category"""
        category_counts = {}
        for record in event_records:
            category = record.get('event_category', 'OTHER')
            category_counts[category] = category_counts.get(category, 0) + 1

        breakdown_parts = []
        for category, count in sorted(category_counts.items()):
            breakdown_parts.append(f"{count} {category.lower()}")

        print(f"      📊 Breakdown: {', '.join(breakdown_parts)}")

    def _insert_event_records(self, records: List[Dict]) -> int:
        """Insert event records into database with conflict resolution"""
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
                    # Skip fields that don't exist in database schema
                    if field not in ['event_category']:  # event_category is for analytics only
                        if value is not None:
                            fields.append(field)
                            placeholders.append('%s')
                            values.append(value)

                # Use ON CONFLICT DO NOTHING (based on unique constraint)
                sql = f"""
                    INSERT INTO politician_events ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (politician_id, event_id) DO NOTHING
                    RETURNING id
                """

                result = database.execute_query(sql, tuple(values))
                if result:  # Record was inserted
                    inserted_count += 1

            except Exception as e:
                print(f"      ⚠️ Database insert error: {e}")

                # Enhanced error logging
                if hasattr(self, 'logger'):
                    self.logger.log_processing(
                        'events_insertion',
                        f"politician_{record.get('politician_id', 'unknown')}",
                        'error',
                        {
                            'error': str(e),
                            'event_type': record.get('event_type'),
                            'event_id': record.get('event_id')
                        }
                    )
                continue

        return inserted_count

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs with deputy_id data"""
        if not politician_ids:
            return []

        placeholders = ', '.join(['%s'] * len(politician_ids))
        query = f"""
            SELECT id, deputy_id, nome_civil, first_election_year, last_election_year
            FROM unified_politicians
            WHERE id IN ({placeholders}) AND deputy_id IS NOT NULL
        """

        return database.execute_query(query, tuple(politician_ids))