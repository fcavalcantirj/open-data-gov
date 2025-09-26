"""
CLI4 Events Validator
Comprehensive validation for politician_events table
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date
from cli4.modules import database


class EventsValidator:
    """Comprehensive validator for parliamentary events data"""

    def __init__(self):
        self.validation_results = {}

    def validate_all_events(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform comprehensive validation of all events data

        Args:
            limit: Maximum number of records to validate (None for all)

        Returns:
            Comprehensive validation results
        """
        print("🔍 COMPREHENSIVE EVENTS VALIDATION")
        print("Validating politician_events with parliamentary activity analysis")
        print("=" * 70)

        # Get events data for validation
        events_data = self._get_events_sample(limit)

        if not events_data:
            return {
                'total_records': 0,
                'validation_categories': {},
                'compliance_score': 0.0,
                'issues_found': ['No events data found for validation']
            }

        print(f"📊 Validating {len(events_data)} events records...")
        print()

        # Comprehensive validation categories
        validation_categories = {
            'core_identifiers': self._validate_core_identifiers(events_data),
            'event_details': self._validate_event_details(events_data),
            'temporal_data': self._validate_temporal_data(events_data),
            'location_information': self._validate_location_information(events_data),
            'data_quality': self._validate_data_quality(events_data),
            'activity_analysis': self._validate_activity_analysis(events_data),
            'event_categorization': self._validate_event_categorization(events_data),
            'politician_correlation': self._validate_politician_correlation(events_data)
        }

        # Calculate weighted compliance score
        compliance_score = self._calculate_compliance_score(validation_categories)

        # Aggregate all issues
        all_issues = []
        for category_results in validation_categories.values():
            all_issues.extend(category_results.get('issues', []))

        results = {
            'total_records': len(events_data),
            'validation_categories': validation_categories,
            'compliance_score': compliance_score,
            'issues_found': all_issues,
            'validation_summary': self._generate_validation_summary(validation_categories)
        }

        self._print_validation_results(results)
        return results

    def _get_events_sample(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get events sample for validation"""
        query = """
            SELECT
                pe.*,
                up.nome_civil,
                up.deputy_id,
                up.cpf,
                up.first_election_year,
                up.last_election_year
            FROM politician_events pe
            JOIN unified_politicians up ON pe.politician_id = up.id
            ORDER BY pe.created_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        return database.execute_query(query)

    def _validate_core_identifiers(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Validate core identifier fields"""
        issues = []
        valid_records = 0

        for event in events_data:
            record_valid = True

            # Check essential identifiers
            if not event.get('politician_id'):
                issues.append(f"Event {event.get('id', 'unknown')}: Missing politician_id")
                record_valid = False

            if not event.get('event_id'):
                issues.append(f"Event {event.get('id', 'unknown')}: Missing event_id")
                record_valid = False

            # Validate politician correlation
            if not event.get('nome_civil'):
                issues.append(f"Event {event.get('id', 'unknown')}: Missing politician correlation")
                record_valid = False

            if record_valid:
                valid_records += 1

        compliance_rate = (valid_records / len(events_data)) * 100 if events_data else 0

        return {
            'category': 'Core Identifiers',
            'compliance_rate': compliance_rate,
            'valid_records': valid_records,
            'total_records': len(events_data),
            'issues': issues[:10],  # Limit to first 10 issues
            'critical': compliance_rate < 95
        }

    def _validate_event_details(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Validate event details and descriptions"""
        issues = []
        valid_records = 0

        event_type_stats = {}
        status_stats = {}

        for event in events_data:
            record_valid = True

            # Check event type
            event_type = event.get('event_type')
            if not event_type:
                issues.append(f"Event {event.get('event_id', 'unknown')}: Missing event_type")
                record_valid = False
            else:
                event_type_stats[event_type] = event_type_stats.get(event_type, 0) + 1

            # Check event description
            description = event.get('event_description')
            if not description or len(description.strip()) < 10:
                issues.append(f"Event {event.get('event_id', 'unknown')}: Insufficient event description")
                record_valid = False

            # Check event status
            status = event.get('event_status')
            if status:
                status_stats[status] = status_stats.get(status, 0) + 1

            if record_valid:
                valid_records += 1

        compliance_rate = (valid_records / len(events_data)) * 100 if events_data else 0

        return {
            'category': 'Event Details',
            'compliance_rate': compliance_rate,
            'valid_records': valid_records,
            'total_records': len(events_data),
            'event_types_found': len(event_type_stats),
            'status_distribution': status_stats,
            'issues': issues[:10],
            'critical': compliance_rate < 80
        }

    def _validate_temporal_data(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Validate temporal consistency and date logic"""
        issues = []
        valid_records = 0

        duration_stats = {'with_duration': 0, 'calculated_duration': 0, 'missing_times': 0}

        for event in events_data:
            record_valid = True

            start_datetime = event.get('start_datetime')
            end_datetime = event.get('end_datetime')
            duration_minutes = event.get('duration_minutes')

            # Validate datetime formats
            if start_datetime:
                try:
                    start_dt = datetime.fromisoformat(str(start_datetime))
                    # Check if start time is reasonable (not too far in past/future)
                    years_diff = abs((datetime.now() - start_dt).days / 365.25)
                    if years_diff > 10:
                        issues.append(f"Event {event.get('event_id')}: Start time too far from current date")
                        record_valid = False
                except Exception:
                    issues.append(f"Event {event.get('event_id')}: Invalid start_datetime format")
                    record_valid = False
            else:
                duration_stats['missing_times'] += 1

            if end_datetime:
                try:
                    end_dt = datetime.fromisoformat(str(end_datetime))
                    if start_datetime:
                        start_dt = datetime.fromisoformat(str(start_datetime))
                        if end_dt <= start_dt:
                            issues.append(f"Event {event.get('event_id')}: End time before start time")
                            record_valid = False
                        else:
                            # Validate duration calculation
                            calculated_duration = int((end_dt - start_dt).total_seconds() / 60)
                            if duration_minutes and abs(calculated_duration - duration_minutes) > 5:
                                issues.append(f"Event {event.get('event_id')}: Duration mismatch (stored: {duration_minutes}, calculated: {calculated_duration})")
                            duration_stats['calculated_duration'] += 1
                except Exception:
                    issues.append(f"Event {event.get('event_id')}: Invalid end_datetime format")
                    record_valid = False

            if duration_minutes:
                duration_stats['with_duration'] += 1
                # Sanity check duration (reasonable range: 15 minutes to 12 hours)
                if not (15 <= duration_minutes <= 720):
                    issues.append(f"Event {event.get('event_id')}: Unusual duration ({duration_minutes} minutes)")

            if record_valid:
                valid_records += 1

        compliance_rate = (valid_records / len(events_data)) * 100 if events_data else 0

        return {
            'category': 'Temporal Data',
            'compliance_rate': compliance_rate,
            'valid_records': valid_records,
            'total_records': len(events_data),
            'duration_stats': duration_stats,
            'issues': issues[:10],
            'critical': compliance_rate < 85
        }

    def _validate_location_information(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Validate location and venue information"""
        issues = []
        valid_records = 0

        location_stats = {
            'with_building': 0,
            'with_room': 0,
            'with_floor': 0,
            'external_locations': 0,
            'complete_location': 0
        }

        for event in events_data:
            record_valid = True

            building = event.get('location_building')
            room = event.get('location_room')
            floor = event.get('location_floor')
            external = event.get('location_external')

            if building:
                location_stats['with_building'] += 1
            if room:
                location_stats['with_room'] += 1
            if floor:
                location_stats['with_floor'] += 1
            if external:
                location_stats['external_locations'] += 1

            # Check if we have some location information
            has_location = building or room or floor or external
            if not has_location:
                issues.append(f"Event {event.get('event_id')}: No location information available")
            else:
                if building and room:
                    location_stats['complete_location'] += 1
                valid_records += 1

        compliance_rate = (valid_records / len(events_data)) * 100 if events_data else 0

        return {
            'category': 'Location Information',
            'compliance_rate': compliance_rate,
            'valid_records': valid_records,
            'total_records': len(events_data),
            'location_stats': location_stats,
            'issues': issues[:10],
            'critical': False  # Location is not critical for events
        }

    def _validate_data_quality(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Validate overall data quality and completeness"""
        issues = []
        valid_records = 0

        quality_metrics = {
            'with_registration_url': 0,
            'with_document_url': 0,
            'attendance_confirmed': 0,
            'complete_records': 0
        }

        for event in events_data:
            record_valid = True
            completeness_score = 0

            # Count available fields for completeness
            if event.get('event_type'):
                completeness_score += 1
            if event.get('event_description') and len(event.get('event_description', '').strip()) > 20:
                completeness_score += 1
            if event.get('start_datetime'):
                completeness_score += 1
            if event.get('end_datetime'):
                completeness_score += 1
            if event.get('duration_minutes'):
                completeness_score += 1
            if event.get('event_status'):
                completeness_score += 1

            # Track optional fields
            if event.get('registration_url'):
                quality_metrics['with_registration_url'] += 1
                completeness_score += 1
            if event.get('document_url'):
                quality_metrics['with_document_url'] += 1
                completeness_score += 1
            if event.get('attendance_confirmed'):
                quality_metrics['attendance_confirmed'] += 1
                completeness_score += 1

            # A complete record should have at least 6/9 key fields
            if completeness_score >= 6:
                quality_metrics['complete_records'] += 1
                valid_records += 1
            else:
                issues.append(f"Event {event.get('event_id')}: Incomplete record (score: {completeness_score}/9)")

        compliance_rate = (valid_records / len(events_data)) * 100 if events_data else 0

        return {
            'category': 'Data Quality',
            'compliance_rate': compliance_rate,
            'valid_records': valid_records,
            'total_records': len(events_data),
            'quality_metrics': quality_metrics,
            'issues': issues[:10],
            'critical': compliance_rate < 70
        }

    def _validate_activity_analysis(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Validate parliamentary activity patterns and analysis"""
        issues = []

        # Group by politician for activity analysis
        politician_events = {}
        for event in events_data:
            politician_id = event.get('politician_id')
            if politician_id:
                if politician_id not in politician_events:
                    politician_events[politician_id] = []
                politician_events[politician_id].append(event)

        activity_metrics = {
            'politicians_with_events': len(politician_events),
            'avg_events_per_politician': 0,
            'high_activity_politicians': 0,
            'low_activity_politicians': 0
        }

        if politician_events:
            total_events = sum(len(events) for events in politician_events.values())
            activity_metrics['avg_events_per_politician'] = total_events / len(politician_events)

            for politician_id, events in politician_events.items():
                event_count = len(events)
                if event_count > 20:  # High activity
                    activity_metrics['high_activity_politicians'] += 1
                elif event_count < 3:  # Low activity
                    activity_metrics['low_activity_politicians'] += 1
                    issues.append(f"Politician {politician_id}: Very low event activity ({event_count} events)")

        # Additional activity pattern analysis
        total_politicians = len(set(event.get('politician_id') for event in events_data if event.get('politician_id')))
        coverage_rate = (len(politician_events) / total_politicians * 100) if total_politicians > 0 else 0

        return {
            'category': 'Activity Analysis',
            'compliance_rate': coverage_rate,
            'valid_records': len(politician_events),
            'total_records': total_politicians,
            'activity_metrics': activity_metrics,
            'issues': issues[:10],
            'critical': coverage_rate < 50
        }

    def _validate_event_categorization(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Validate event categorization and type distribution"""
        issues = []

        categorization_stats = {}
        type_distribution = {}

        for event in events_data:
            event_type = event.get('event_type')
            if event_type:
                type_distribution[event_type] = type_distribution.get(event_type, 0) + 1

                # Simulate categorization logic
                category = self._categorize_event_type(event_type)
                categorization_stats[category] = categorization_stats.get(category, 0) + 1

        # Check for reasonable distribution
        total_categorized = sum(categorization_stats.values())
        if total_categorized < len(events_data) * 0.8:
            issues.append(f"Low categorization success rate: {total_categorized}/{len(events_data)}")

        # Check if we have diverse event types
        if len(type_distribution) < 3:
            issues.append(f"Limited event type diversity: only {len(type_distribution)} distinct types")

        compliance_rate = (total_categorized / len(events_data) * 100) if events_data else 0

        return {
            'category': 'Event Categorization',
            'compliance_rate': compliance_rate,
            'valid_records': total_categorized,
            'total_records': len(events_data),
            'categorization_stats': categorization_stats,
            'type_distribution': dict(list(type_distribution.items())[:10]),  # Top 10 types
            'issues': issues,
            'critical': False
        }

    def _validate_politician_correlation(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Validate correlation with politician data"""
        issues = []
        valid_records = 0

        correlation_stats = {
            'with_deputy_id': 0,
            'with_cpf': 0,
            'with_election_years': 0,
            'temporal_consistency': 0
        }

        for event in events_data:
            record_valid = True

            # Check politician correlation fields
            if event.get('deputy_id'):
                correlation_stats['with_deputy_id'] += 1
            else:
                issues.append(f"Event {event.get('event_id')}: Missing deputy_id correlation")
                record_valid = False

            if event.get('cpf'):
                correlation_stats['with_cpf'] += 1

            # Check temporal consistency with politician career
            start_datetime = event.get('start_datetime')
            first_election_year = event.get('first_election_year')

            if start_datetime and first_election_year:
                correlation_stats['with_election_years'] += 1
                try:
                    event_year = datetime.fromisoformat(str(start_datetime)).year
                    if event_year < first_election_year:
                        issues.append(f"Event {event.get('event_id')}: Event date before politician's first election")
                    else:
                        correlation_stats['temporal_consistency'] += 1
                except Exception:
                    pass

            if record_valid:
                valid_records += 1

        compliance_rate = (valid_records / len(events_data)) * 100 if events_data else 0

        return {
            'category': 'Politician Correlation',
            'compliance_rate': compliance_rate,
            'valid_records': valid_records,
            'total_records': len(events_data),
            'correlation_stats': correlation_stats,
            'issues': issues[:10],
            'critical': compliance_rate < 90
        }

    def _categorize_event_type(self, event_type: str) -> str:
        """Categorize event type for validation"""
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

    def _calculate_compliance_score(self, validation_categories: Dict[str, Dict]) -> float:
        """Calculate weighted compliance score"""
        # Define weights for different validation categories
        weights = {
            'core_identifiers': 0.20,      # Critical
            'event_details': 0.15,         # Important
            'temporal_data': 0.15,         # Important
            'location_information': 0.10,   # Moderate
            'data_quality': 0.15,          # Important
            'activity_analysis': 0.10,     # Moderate
            'event_categorization': 0.05,  # Low
            'politician_correlation': 0.10  # Moderate
        }

        weighted_score = 0.0
        total_weight = 0.0

        for category, results in validation_categories.items():
            if category in weights:
                weight = weights[category]
                compliance_rate = results.get('compliance_rate', 0)
                weighted_score += compliance_rate * weight
                total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _generate_validation_summary(self, validation_categories: Dict[str, Dict]) -> str:
        """Generate human-readable validation summary"""
        critical_issues = []
        warnings = []

        for category, results in validation_categories.items():
            if results.get('critical', False):
                critical_issues.append(f"{results['category']}: {results['compliance_rate']:.1f}%")
            elif results['compliance_rate'] < 85:
                warnings.append(f"{results['category']}: {results['compliance_rate']:.1f}%")

        summary_parts = []
        if critical_issues:
            summary_parts.append(f"Critical issues: {', '.join(critical_issues)}")
        if warnings:
            summary_parts.append(f"Warnings: {', '.join(warnings)}")
        if not critical_issues and not warnings:
            summary_parts.append("All validation categories passed")

        return "; ".join(summary_parts)

    def _print_validation_results(self, results: Dict[str, Any]) -> None:
        """Print formatted validation results"""
        print(f"📊 VALIDATION RESULTS SUMMARY")
        print("=" * 50)
        print(f"Total Records Validated: {results['total_records']:,}")
        print(f"Overall Compliance Score: {results['compliance_score']:.1f}%")
        print()

        # Print category results
        for category, category_results in results['validation_categories'].items():
            status = "✅" if not category_results.get('critical', False) else "⚠️"
            print(f"{status} {category_results['category']}: {category_results['compliance_rate']:.1f}%")
            if category_results.get('issues'):
                for issue in category_results['issues'][:3]:  # Show top 3 issues
                    print(f"   • {issue}")
                if len(category_results['issues']) > 3:
                    print(f"   • ... and {len(category_results['issues']) - 3} more issues")
            print()

        # Print summary
        print(f"Summary: {results['validation_summary']}")
        print("=" * 50)