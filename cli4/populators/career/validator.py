"""
CLI4 Career Validator
Comprehensive validation for politician_career_history table
"""

from typing import Dict, List, Any, Optional
from cli4.modules import database


class CareerValidator:
    """Comprehensive career data validation following CLI4 patterns"""

    def __init__(self):
        self.validation_results = {
            'total_career_records': 0,
            'validation_categories': {},
            'critical_issues': [],
            'warnings': [],
            'compliance_score': 0.0
        }

    def validate_all_career_records(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Run comprehensive validation on all career records"""
        print("📋 COMPREHENSIVE CAREER VALIDATION")
        print("=" * 60)
        print("Political career history data quality assessment")
        print()

        # Get career records
        query = "SELECT * FROM politician_career_history"
        if limit:
            query += f" LIMIT {limit}"

        career_records = database.execute_query(query)
        self.validation_results['total_career_records'] = len(career_records)

        if not career_records:
            print("⚠️ No career records found in database")
            return self.validation_results

        limit_text = f" (limited to {limit})" if limit else ""
        print(f"📊 Validating {len(career_records)} career records{limit_text}...")
        print()

        # Run validation categories
        self._validate_core_identifiers(career_records)
        self._validate_mandate_details(career_records)
        self._validate_temporal_data(career_records)
        self._validate_geographic_data(career_records)
        self._validate_source_tracking(career_records)
        self._validate_data_quality(career_records)
        self._validate_career_patterns(career_records)
        self._validate_politician_references(career_records)

        # Calculate compliance score
        self._calculate_compliance_score()

        # Print results
        self._print_validation_summary()

        return self.validation_results

    def _validate_core_identifiers(self, career_records: List[Dict]):
        """Validate core identifier fields"""
        print("🔍 Core Identifiers Validation")

        results = {
            'valid_politician_ids': 0,
            'missing_politician_ids': 0,
            'valid_office_names': 0,
            'missing_office_names': 0
        }

        for record in career_records:
            # Check politician_id
            if record.get('politician_id'):
                results['valid_politician_ids'] += 1
            else:
                results['missing_politician_ids'] += 1
                self.validation_results['critical_issues'].append(
                    f"Record {record.get('id')} missing politician_id"
                )

            # Check office_name
            if record.get('office_name') and record.get('office_name').strip():
                results['valid_office_names'] += 1
            else:
                results['missing_office_names'] += 1
                self.validation_results['warnings'].append(
                    f"Record {record.get('id')} missing office_name"
                )

        self.validation_results['validation_categories']['core_identifiers'] = results
        print(f"  ✅ Valid politician IDs: {results['valid_politician_ids']}")
        print(f"  ❌ Missing politician IDs: {results['missing_politician_ids']}")
        print(f"  ✅ Valid office names: {results['valid_office_names']}")
        print(f"  ⚠️ Missing office names: {results['missing_office_names']}")
        print()

    def _validate_mandate_details(self, career_records: List[Dict]):
        """Validate mandate-specific fields"""
        print("🏛️ Mandate Details Validation")

        results = {
            'categorized_mandates': 0,
            'uncategorized_mandates': 0,
            'mandate_types': {},
            'party_references': 0,
            'missing_parties': 0
        }

        for record in career_records:
            # Check mandate type categorization
            mandate_type = record.get('mandate_type')
            if mandate_type and mandate_type != 'OTHER':
                results['categorized_mandates'] += 1
                results['mandate_types'][mandate_type] = results['mandate_types'].get(mandate_type, 0) + 1
            else:
                results['uncategorized_mandates'] += 1

            # Check party information
            if record.get('party_at_election'):
                results['party_references'] += 1
            else:
                results['missing_parties'] += 1

        self.validation_results['validation_categories']['mandate_details'] = results
        print(f"  ✅ Categorized mandates: {results['categorized_mandates']}")
        print(f"  ⚠️ Uncategorized mandates: {results['uncategorized_mandates']}")
        print(f"  📊 Mandate type distribution:")
        for mandate_type, count in results['mandate_types'].items():
            print(f"     {mandate_type}: {count}")
        print(f"  🎭 With party references: {results['party_references']}")
        print(f"  ⚠️ Missing party data: {results['missing_parties']}")
        print()

    def _validate_temporal_data(self, career_records: List[Dict]):
        """Validate temporal fields (years, dates)"""
        print("⏰ Temporal Data Validation")

        results = {
            'valid_start_years': 0,
            'missing_start_years': 0,
            'valid_end_years': 0,
            'missing_end_years': 0,
            'invalid_year_ranges': 0,
            'future_mandates': 0,
            'very_old_mandates': 0
        }

        current_year = 2024
        min_reasonable_year = 1988  # Post-constitution

        for record in career_records:
            start_year = record.get('start_year')
            end_year = record.get('end_year')

            # Validate start year
            if start_year:
                results['valid_start_years'] += 1
                if start_year > current_year:
                    results['future_mandates'] += 1
                    self.validation_results['warnings'].append(
                        f"Record {record.get('id')} has future start year: {start_year}"
                    )
                elif start_year < min_reasonable_year:
                    results['very_old_mandates'] += 1
                    self.validation_results['warnings'].append(
                        f"Record {record.get('id')} has very old start year: {start_year}"
                    )
            else:
                results['missing_start_years'] += 1

            # Validate end year
            if end_year:
                results['valid_end_years'] += 1
            else:
                results['missing_end_years'] += 1

            # Validate year range logic
            if start_year and end_year:
                if end_year < start_year:
                    results['invalid_year_ranges'] += 1
                    self.validation_results['critical_issues'].append(
                        f"Record {record.get('id')} has end year ({end_year}) before start year ({start_year})"
                    )

        self.validation_results['validation_categories']['temporal_data'] = results
        print(f"  ✅ Valid start years: {results['valid_start_years']}")
        print(f"  ⚠️ Missing start years: {results['missing_start_years']}")
        print(f"  ✅ Valid end years: {results['valid_end_years']}")
        print(f"  ⚠️ Missing end years: {results['missing_end_years']}")
        print(f"  ❌ Invalid year ranges: {results['invalid_year_ranges']}")
        print(f"  🔮 Future mandates: {results['future_mandates']}")
        print(f"  🏛️ Pre-1988 mandates: {results['very_old_mandates']}")
        print()

    def _validate_geographic_data(self, career_records: List[Dict]):
        """Validate geographic fields (state, municipality)"""
        print("🗺️ Geographic Data Validation")

        results = {
            'valid_states': 0,
            'missing_states': 0,
            'state_distribution': {},
            'valid_municipalities': 0,
            'missing_municipalities': 0,
            'geographic_consistency': 0
        }

        valid_states = {
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        }

        for record in career_records:
            state = record.get('state')
            municipality = record.get('municipality')

            # Validate state
            if state:
                if state in valid_states:
                    results['valid_states'] += 1
                    results['state_distribution'][state] = results['state_distribution'].get(state, 0) + 1
                else:
                    self.validation_results['warnings'].append(
                        f"Record {record.get('id')} has invalid state: {state}"
                    )
            else:
                results['missing_states'] += 1

            # Validate municipality
            if municipality and municipality.strip():
                results['valid_municipalities'] += 1
            else:
                results['missing_municipalities'] += 1

            # Check geographic consistency for municipal mandates
            mandate_type = record.get('mandate_type')
            if mandate_type == 'MUNICIPAL' and municipality:
                results['geographic_consistency'] += 1

        self.validation_results['validation_categories']['geographic_data'] = results
        print(f"  ✅ Valid states: {results['valid_states']}")
        print(f"  ⚠️ Missing states: {results['missing_states']}")
        print(f"  🏙️ Valid municipalities: {results['valid_municipalities']}")
        print(f"  ⚠️ Missing municipalities: {results['missing_municipalities']}")
        print(f"  🗺️ Geographic consistency (municipal mandates): {results['geographic_consistency']}")
        print(f"  📊 Top states by mandate count:")
        sorted_states = sorted(results['state_distribution'].items(), key=lambda x: x[1], reverse=True)
        for state, count in sorted_states[:5]:
            print(f"     {state}: {count}")
        print()

    def _validate_source_tracking(self, career_records: List[Dict]):
        """Validate source system tracking"""
        print("📡 Source System Validation")

        results = {
            'deputados_records': 0,
            'other_sources': 0,
            'missing_source': 0,
            'valid_timestamps': 0,
            'missing_timestamps': 0
        }

        for record in career_records:
            source_system = record.get('source_system')

            # Check source system
            if source_system == 'DEPUTADOS':
                results['deputados_records'] += 1
            elif source_system:
                results['other_sources'] += 1
            else:
                results['missing_source'] += 1

            # Check timestamps
            if record.get('created_at'):
                results['valid_timestamps'] += 1
            else:
                results['missing_timestamps'] += 1

        self.validation_results['validation_categories']['source_tracking'] = results
        print(f"  ✅ Deputados API records: {results['deputados_records']}")
        print(f"  📊 Other source records: {results['other_sources']}")
        print(f"  ⚠️ Missing source info: {results['missing_source']}")
        print(f"  🕐 Valid timestamps: {results['valid_timestamps']}")
        print(f"  ⚠️ Missing timestamps: {results['missing_timestamps']}")
        print()

    def _validate_data_quality(self, career_records: List[Dict]):
        """Validate overall data quality"""
        print("🔍 Data Quality Assessment")

        results = {
            'complete_records': 0,
            'partial_records': 0,
            'minimal_records': 0,
            'data_completeness_score': 0.0
        }

        essential_fields = ['politician_id', 'office_name', 'start_year']
        important_fields = ['mandate_type', 'state', 'end_year']
        optional_fields = ['municipality', 'party_at_election']

        total_completeness = 0

        for record in career_records:
            completeness_score = 0
            essential_count = sum(1 for field in essential_fields if record.get(field))
            important_count = sum(1 for field in important_fields if record.get(field))
            optional_count = sum(1 for field in optional_fields if record.get(field))

            # Calculate weighted completeness (essential=3, important=2, optional=1)
            max_score = len(essential_fields) * 3 + len(important_fields) * 2 + len(optional_fields) * 1
            actual_score = essential_count * 3 + important_count * 2 + optional_count * 1
            completeness_score = (actual_score / max_score) * 100

            total_completeness += completeness_score

            # Categorize record completeness
            if completeness_score >= 80:
                results['complete_records'] += 1
            elif completeness_score >= 50:
                results['partial_records'] += 1
            else:
                results['minimal_records'] += 1

        results['data_completeness_score'] = total_completeness / len(career_records) if career_records else 0

        self.validation_results['validation_categories']['data_quality'] = results
        print(f"  ✅ Complete records (≥80%): {results['complete_records']}")
        print(f"  ⚠️ Partial records (50-79%): {results['partial_records']}")
        print(f"  ❌ Minimal records (<50%): {results['minimal_records']}")
        print(f"  📊 Average completeness: {results['data_completeness_score']:.1f}%")
        print()

    def _validate_career_patterns(self, career_records: List[Dict]):
        """Validate career progression patterns"""
        print("📈 Career Patterns Analysis")

        results = {
            'politicians_with_multiple_mandates': 0,
            'single_mandate_politicians': 0,
            'career_progression_detected': 0,
            'overlapping_mandates': 0
        }

        # Group by politician
        politician_careers = {}
        for record in career_records:
            politician_id = record.get('politician_id')
            if politician_id not in politician_careers:
                politician_careers[politician_id] = []
            politician_careers[politician_id].append(record)

        for politician_id, mandates in politician_careers.items():
            if len(mandates) > 1:
                results['politicians_with_multiple_mandates'] += 1

                # Check for progression patterns
                sorted_mandates = sorted(mandates, key=lambda x: x.get('start_year', 0))
                has_progression = False
                for i in range(len(sorted_mandates) - 1):
                    current = sorted_mandates[i]
                    next_mandate = sorted_mandates[i + 1]

                    # Simple progression: municipal -> state -> federal
                    current_type = current.get('mandate_type', '').upper()
                    next_type = next_mandate.get('mandate_type', '').upper()

                    if (current_type == 'MUNICIPAL' and next_type in ['STATE', 'FEDERAL']) or \
                       (current_type == 'STATE' and next_type == 'FEDERAL'):
                        has_progression = True

                if has_progression:
                    results['career_progression_detected'] += 1

                # Check for overlapping mandates
                for i in range(len(sorted_mandates) - 1):
                    current = sorted_mandates[i]
                    next_mandate = sorted_mandates[i + 1]

                    current_end = current.get('end_year')
                    next_start = next_mandate.get('start_year')

                    if current_end and next_start and current_end >= next_start:
                        results['overlapping_mandates'] += 1

            else:
                results['single_mandate_politicians'] += 1

        self.validation_results['validation_categories']['career_patterns'] = results
        print(f"  👥 Politicians with multiple mandates: {results['politicians_with_multiple_mandates']}")
        print(f"  👤 Single mandate politicians: {results['single_mandate_politicians']}")
        print(f"  📈 Career progressions detected: {results['career_progression_detected']}")
        print(f"  ⚠️ Overlapping mandates: {results['overlapping_mandates']}")
        print()

    def _validate_politician_references(self, career_records: List[Dict]):
        """Validate references to unified_politicians table"""
        print("🔗 Politician Reference Validation")

        results = {
            'valid_references': 0,
            'invalid_references': 0,
            'orphaned_records': 0
        }

        # Get all valid politician IDs
        valid_politician_ids = set()
        politicians = database.execute_query("SELECT id FROM unified_politicians")
        for politician in politicians:
            valid_politician_ids.add(politician['id'])

        # Check references
        for record in career_records:
            politician_id = record.get('politician_id')
            if politician_id in valid_politician_ids:
                results['valid_references'] += 1
            elif politician_id:
                results['invalid_references'] += 1
                self.validation_results['critical_issues'].append(
                    f"Record {record.get('id')} references non-existent politician_id: {politician_id}"
                )
            else:
                results['orphaned_records'] += 1

        self.validation_results['validation_categories']['politician_references'] = results
        print(f"  ✅ Valid politician references: {results['valid_references']}")
        print(f"  ❌ Invalid references: {results['invalid_references']}")
        print(f"  🚨 Orphaned records: {results['orphaned_records']}")
        print()

    def _calculate_compliance_score(self):
        """Calculate overall compliance score"""
        categories = self.validation_results['validation_categories']
        total_records = self.validation_results['total_career_records']

        if total_records == 0:
            self.validation_results['compliance_score'] = 0.0
            return

        # Weight different validation categories
        score_components = []

        # Core identifiers (30% weight)
        core = categories.get('core_identifiers', {})
        if core:
            core_score = (core.get('valid_politician_ids', 0) +
                         core.get('valid_office_names', 0)) / (total_records * 2) * 100
            score_components.append(('core_identifiers', core_score, 0.30))

        # Data quality (25% weight)
        quality = categories.get('data_quality', {})
        if quality:
            quality_score = quality.get('data_completeness_score', 0)
            score_components.append(('data_quality', quality_score, 0.25))

        # Temporal data (20% weight)
        temporal = categories.get('temporal_data', {})
        if temporal:
            temporal_score = (temporal.get('valid_start_years', 0) / total_records) * 100
            score_components.append(('temporal_data', temporal_score, 0.20))

        # Politician references (15% weight)
        refs = categories.get('politician_references', {})
        if refs:
            ref_score = (refs.get('valid_references', 0) / total_records) * 100
            score_components.append(('politician_references', ref_score, 0.15))

        # Source tracking (10% weight)
        source = categories.get('source_tracking', {})
        if source:
            source_score = (source.get('deputados_records', 0) / total_records) * 100
            score_components.append(('source_tracking', source_score, 0.10))

        # Calculate weighted average
        if score_components:
            weighted_score = sum(score * weight for _, score, weight in score_components)
            self.validation_results['compliance_score'] = weighted_score

    def _print_validation_summary(self):
        """Print comprehensive validation summary"""
        print("=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        total_records = self.validation_results['total_career_records']
        compliance_score = self.validation_results['compliance_score']
        critical_issues = len(self.validation_results['critical_issues'])
        warnings = len(self.validation_results['warnings'])

        print(f"📋 Total career records validated: {total_records}")
        print(f"🎯 Overall compliance score: {compliance_score:.1f}%")
        print(f"🚨 Critical issues found: {critical_issues}")
        print(f"⚠️ Warnings issued: {warnings}")

        # Compliance rating
        if compliance_score >= 95:
            rating = "🟢 EXCELLENT"
        elif compliance_score >= 85:
            rating = "🔵 GOOD"
        elif compliance_score >= 70:
            rating = "🟡 NEEDS IMPROVEMENT"
        else:
            rating = "🔴 POOR"

        print(f"📈 Data quality rating: {rating}")
        print()

        # Show top issues if any
        if self.validation_results['critical_issues']:
            print("🚨 TOP CRITICAL ISSUES:")
            for issue in self.validation_results['critical_issues'][:5]:
                print(f"   • {issue}")
            if len(self.validation_results['critical_issues']) > 5:
                print(f"   ... and {len(self.validation_results['critical_issues']) - 5} more")
            print()