"""
CLI4 Professional Validator
Comprehensive validation for politician_professional_background table
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from cli4.modules import database


class ProfessionalValidator:
    """Comprehensive validator for professional background records"""

    def __init__(self):
        self.validation_categories = [
            'core_identifiers',
            'profession_details',
            'entity_information',
            'temporal_data',
            'data_quality',
            'career_analysis',
            'professional_distribution',
            'politician_references'
        ]

    def validate_all_professional_records(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Run comprehensive validation on all professional records"""
        print("🔍 COMPREHENSIVE PROFESSIONAL BACKGROUND VALIDATION")
        print("Following CLI4 validation standards with 8-category analysis")
        print("=" * 60)

        # Get professional records to validate
        limit_clause = f"LIMIT {limit}" if limit else ""
        professional_records = database.execute_query(f"""
            SELECT
                pb.*,
                p.nome_civil,
                p.deputy_id,
                p.cpf
            FROM politician_professional_background pb
            JOIN unified_politicians p ON pb.politician_id = p.id
            ORDER BY pb.id
            {limit_clause}
        """)

        if not professional_records:
            print("❌ No professional records found for validation")
            return {'error': 'No records found'}

        total_records = len(professional_records)
        print(f"📊 Validating {total_records:,} professional records")
        print()

        # Initialize validation results
        validation_results = {
            'total_records': total_records,
            'validation_categories': {},
            'summary': {},
            'compliance_score': 0,
            'recommendations': []
        }

        # Run validation categories
        self._validate_core_identifiers(professional_records, validation_results)
        self._validate_profession_details(professional_records, validation_results)
        self._validate_entity_information(professional_records, validation_results)
        self._validate_temporal_data(professional_records, validation_results)
        self._validate_data_quality(professional_records, validation_results)
        self._validate_career_analysis(professional_records, validation_results)
        self._validate_professional_distribution(professional_records, validation_results)
        self._validate_politician_references(professional_records, validation_results)

        # Calculate overall compliance score
        self._calculate_compliance_score(validation_results)

        # Generate recommendations
        self._generate_recommendations(validation_results)

        # Print summary
        self._print_validation_summary(validation_results)

        return validation_results

    def _validate_core_identifiers(self, records: List[Dict], results: Dict[str, Any]):
        """Validate core identification fields"""
        print("1. 🔑 Core Identifiers Validation")

        issues = {
            'missing_politician_id': 0,
            'missing_profession_type': 0,
            'invalid_profession_type': 0,
            'missing_profession_name': 0,
            'total_records': len(records)
        }

        valid_profession_types = {'PROFESSION', 'OCCUPATION'}

        for record in records:
            if not record.get('politician_id'):
                issues['missing_politician_id'] += 1

            prof_type = record.get('profession_type')
            if not prof_type:
                issues['missing_profession_type'] += 1
            elif prof_type not in valid_profession_types:
                issues['invalid_profession_type'] += 1

            if not record.get('profession_name'):
                issues['missing_profession_name'] += 1

        # Calculate compliance
        total_validations = issues['total_records'] * 3  # 3 core fields
        total_issues = (issues['missing_politician_id'] +
                       issues['missing_profession_type'] +
                       issues['invalid_profession_type'] +
                       issues['missing_profession_name'])

        compliance = ((total_validations - total_issues) / total_validations) * 100 if total_validations > 0 else 0

        results['validation_categories']['core_identifiers'] = {
            'compliance_percentage': compliance,
            'issues': issues,
            'status': 'PASS' if compliance >= 95 else 'FAIL'
        }

        print(f"   ✅ Core identifier compliance: {compliance:.1f}%")
        if issues['missing_politician_id'] > 0:
            print(f"   ⚠️  Missing politician_id: {issues['missing_politician_id']:,}")
        if issues['missing_profession_type'] > 0:
            print(f"   ⚠️  Missing profession_type: {issues['missing_profession_type']:,}")
        if issues['invalid_profession_type'] > 0:
            print(f"   ⚠️  Invalid profession_type: {issues['invalid_profession_type']:,}")
        if issues['missing_profession_name'] > 0:
            print(f"   ⚠️  Missing profession_name: {issues['missing_profession_name']:,}")

    def _validate_profession_details(self, records: List[Dict], results: Dict[str, Any]):
        """Validate profession-specific fields"""
        print("\n2. 💼 Profession Details Validation")

        issues = {
            'profession_records': 0,
            'missing_profession_code': 0,
            'occupation_records': 0,
            'missing_professional_title': 0,
            'total_records': len(records)
        }

        for record in records:
            prof_type = record.get('profession_type')

            if prof_type == 'PROFESSION':
                issues['profession_records'] += 1
                if not record.get('profession_code'):
                    issues['missing_profession_code'] += 1

            elif prof_type == 'OCCUPATION':
                issues['occupation_records'] += 1
                if not record.get('professional_title'):
                    issues['missing_professional_title'] += 1

        # Calculate compliance
        prof_compliance = 100
        if issues['profession_records'] > 0:
            prof_compliance = ((issues['profession_records'] - issues['missing_profession_code']) /
                             issues['profession_records']) * 100

        occ_compliance = 100
        if issues['occupation_records'] > 0:
            occ_compliance = ((issues['occupation_records'] - issues['missing_professional_title']) /
                            issues['occupation_records']) * 100

        overall_compliance = (prof_compliance + occ_compliance) / 2

        results['validation_categories']['profession_details'] = {
            'compliance_percentage': overall_compliance,
            'issues': issues,
            'status': 'PASS' if overall_compliance >= 80 else 'FAIL'
        }

        print(f"   📊 Profession records: {issues['profession_records']:,}")
        print(f"   📊 Occupation records: {issues['occupation_records']:,}")
        print(f"   ✅ Profession details compliance: {overall_compliance:.1f}%")
        if issues['missing_profession_code'] > 0:
            print(f"   ⚠️  Missing profession codes: {issues['missing_profession_code']:,}")
        if issues['missing_professional_title'] > 0:
            print(f"   ⚠️  Missing professional titles: {issues['missing_professional_title']:,}")

    def _validate_entity_information(self, records: List[Dict], results: Dict[str, Any]):
        """Validate entity/organization information"""
        print("\n3. 🏢 Entity Information Validation")

        issues = {
            'with_entity_name': 0,
            'with_entity_state': 0,
            'with_entity_country': 0,
            'normalized_entities': 0,
            'potential_duplicates': 0,
            'total_records': len(records)
        }

        entity_names = {}

        for record in records:
            if record.get('entity_name'):
                issues['with_entity_name'] += 1

                # Track potential duplicates
                entity_name = record['entity_name'].lower().strip()
                if entity_name in entity_names:
                    issues['potential_duplicates'] += 1
                else:
                    entity_names[entity_name] = 1

                # Check if normalized (no trailing punctuation)
                if not record['entity_name'].endswith(('.', 'LTDA.', 'S.A.')):
                    issues['normalized_entities'] += 1

            if record.get('entity_state'):
                issues['with_entity_state'] += 1

            if record.get('entity_country'):
                issues['with_entity_country'] += 1

        # Entity data completion rate
        entity_completion = (issues['with_entity_name'] / issues['total_records']) * 100 if issues['total_records'] > 0 else 0

        # Entity normalization rate
        entity_normalization = (issues['normalized_entities'] / issues['with_entity_name']) * 100 if issues['with_entity_name'] > 0 else 100

        overall_compliance = (entity_completion * 0.7 + entity_normalization * 0.3)

        results['validation_categories']['entity_information'] = {
            'compliance_percentage': overall_compliance,
            'issues': issues,
            'status': 'PASS' if overall_compliance >= 70 else 'FAIL'
        }

        print(f"   📊 Records with entity names: {issues['with_entity_name']:,} ({entity_completion:.1f}%)")
        print(f"   📊 Records with entity states: {issues['with_entity_state']:,}")
        print(f"   📊 Records with entity countries: {issues['with_entity_country']:,}")
        print(f"   ✅ Entity information compliance: {overall_compliance:.1f}%")
        if issues['potential_duplicates'] > 0:
            print(f"   ⚠️  Potential duplicate entities: {issues['potential_duplicates']:,}")

    def _validate_temporal_data(self, records: List[Dict], results: Dict[str, Any]):
        """Validate temporal/date information"""
        print("\n4. ⏰ Temporal Data Validation")

        current_year = datetime.now().year

        issues = {
            'with_year_start': 0,
            'with_year_end': 0,
            'historical_records': 0,
            'future_years': 0,
            'invalid_ranges': 0,
            'current_positions': 0,
            'total_records': len(records)
        }

        for record in records:
            year_start = record.get('year_start')
            year_end = record.get('year_end')
            is_current = record.get('is_current', False)

            if year_start:
                issues['with_year_start'] += 1

                # Check for historical records (before 1950)
                if year_start < 1950:
                    issues['historical_records'] += 1

                # Check for future years
                if year_start > current_year:
                    issues['future_years'] += 1

            if year_end:
                issues['with_year_end'] += 1

                # Check for invalid ranges
                if year_start and year_end and year_end < year_start:
                    issues['invalid_ranges'] += 1

            if is_current:
                issues['current_positions'] += 1

        # Temporal data completion rate
        temporal_completion = (issues['with_year_start'] / issues['total_records']) * 100 if issues['total_records'] > 0 else 0

        # Temporal data validity rate
        total_checks = issues['with_year_start']
        invalid_data = issues['future_years'] + issues['invalid_ranges']
        temporal_validity = ((total_checks - invalid_data) / total_checks) * 100 if total_checks > 0 else 100

        overall_compliance = (temporal_completion * 0.6 + temporal_validity * 0.4)

        results['validation_categories']['temporal_data'] = {
            'compliance_percentage': overall_compliance,
            'issues': issues,
            'status': 'PASS' if overall_compliance >= 80 else 'FAIL'
        }

        print(f"   📊 Records with start years: {issues['with_year_start']:,} ({temporal_completion:.1f}%)")
        print(f"   📊 Records with end years: {issues['with_year_end']:,}")
        print(f"   📊 Current positions: {issues['current_positions']:,}")
        print(f"   📊 Historical records (pre-1950): {issues['historical_records']:,}")
        print(f"   ✅ Temporal data compliance: {overall_compliance:.1f}%")
        if issues['future_years'] > 0:
            print(f"   ⚠️  Future years detected: {issues['future_years']:,}")
        if issues['invalid_ranges'] > 0:
            print(f"   ⚠️  Invalid year ranges: {issues['invalid_ranges']:,}")

    def _validate_data_quality(self, records: List[Dict], results: Dict[str, Any]):
        """Validate overall data quality"""
        print("\n5. 📊 Data Quality Validation")

        issues = {
            'complete_records': 0,
            'truncated_names': 0,
            'normalized_text': 0,
            'empty_strings': 0,
            'total_records': len(records)
        }

        for record in records:
            # Check for complete records (has profession_name and either profession_code or entity info)
            prof_type = record.get('profession_type')
            profession_name = record.get('profession_name')
            profession_code = record.get('profession_code')
            entity_name = record.get('entity_name')

            if profession_name:
                if prof_type == 'PROFESSION' and profession_code:
                    issues['complete_records'] += 1
                elif prof_type == 'OCCUPATION' and (entity_name or record.get('year_start')):
                    issues['complete_records'] += 1

            # Check for truncated names (ending with ...)
            if profession_name and profession_name.endswith('...'):
                issues['truncated_names'] += 1

            # Check for normalized text (no extra spaces, proper case)
            text_fields = ['profession_name', 'entity_name', 'professional_title']
            normalized_count = 0
            total_text_fields = 0

            for field in text_fields:
                value = record.get(field)
                if value:
                    total_text_fields += 1
                    if value.strip() == value and not value.isupper() and not value.islower():
                        normalized_count += 1

            if total_text_fields > 0 and normalized_count == total_text_fields:
                issues['normalized_text'] += 1

            # Check for empty strings
            for field, value in record.items():
                if isinstance(value, str) and value == '':
                    issues['empty_strings'] += 1
                    break

        # Calculate compliance
        completeness = (issues['complete_records'] / issues['total_records']) * 100 if issues['total_records'] > 0 else 0
        normalization = (issues['normalized_text'] / issues['total_records']) * 100 if issues['total_records'] > 0 else 0

        overall_compliance = (completeness * 0.7 + normalization * 0.3)

        results['validation_categories']['data_quality'] = {
            'compliance_percentage': overall_compliance,
            'issues': issues,
            'status': 'PASS' if overall_compliance >= 85 else 'FAIL'
        }

        print(f"   📊 Complete records: {issues['complete_records']:,} ({completeness:.1f}%)")
        print(f"   📊 Normalized text: {issues['normalized_text']:,} ({normalization:.1f}%)")
        print(f"   ✅ Data quality compliance: {overall_compliance:.1f}%")
        if issues['truncated_names'] > 0:
            print(f"   ⚠️  Truncated profession names: {issues['truncated_names']:,}")
        if issues['empty_strings'] > 0:
            print(f"   ⚠️  Records with empty strings: {issues['empty_strings']:,}")

    def _validate_career_analysis(self, records: List[Dict], results: Dict[str, Any]):
        """Validate career progression and analysis"""
        print("\n6. 📈 Career Analysis Validation")

        # Group records by politician
        politicians = {}
        for record in records:
            politician_id = record['politician_id']
            if politician_id not in politicians:
                politicians[politician_id] = []
            politicians[politician_id].append(record)

        issues = {
            'politicians_with_careers': len(politicians),
            'multi_profession_politicians': 0,
            'career_progressions': 0,
            'sector_diversity': 0,
            'long_careers': 0,
            'total_records': len(records)
        }

        for politician_id, politician_records in politicians.items():
            # Check for multiple professions/occupations
            if len(politician_records) > 1:
                issues['multi_profession_politicians'] += 1

            # Check for career progression (chronological order)
            sorted_records = sorted([r for r in politician_records if r.get('year_start')],
                                  key=lambda x: x['year_start'])
            if len(sorted_records) > 1:
                issues['career_progressions'] += 1

            # Check for sector diversity (public vs private, different entities)
            entities = set()
            for record in politician_records:
                entity = record.get('entity_name')
                if entity:
                    entities.add(entity.lower())

            if len(entities) > 1:
                issues['sector_diversity'] += 1

            # Check for long careers (span > 10 years)
            years = [r.get('year_start') for r in politician_records if r.get('year_start')]
            if len(years) > 1 and max(years) - min(years) > 10:
                issues['long_careers'] += 1

        # Calculate career analysis metrics
        multi_profession_rate = (issues['multi_profession_politicians'] / issues['politicians_with_careers']) * 100 if issues['politicians_with_careers'] > 0 else 0
        progression_rate = (issues['career_progressions'] / issues['politicians_with_careers']) * 100 if issues['politicians_with_careers'] > 0 else 0

        overall_compliance = (multi_profession_rate * 0.4 + progression_rate * 0.3 +
                            (issues['sector_diversity'] / issues['politicians_with_careers'] * 100 * 0.3)) if issues['politicians_with_careers'] > 0 else 0

        results['validation_categories']['career_analysis'] = {
            'compliance_percentage': overall_compliance,
            'issues': issues,
            'status': 'PASS' if overall_compliance >= 60 else 'FAIL'
        }

        print(f"   📊 Politicians with career data: {issues['politicians_with_careers']:,}")
        print(f"   📊 Multi-profession politicians: {issues['multi_profession_politicians']:,} ({multi_profession_rate:.1f}%)")
        print(f"   📊 Career progressions tracked: {issues['career_progressions']:,} ({progression_rate:.1f}%)")
        print(f"   📊 Sector diversity: {issues['sector_diversity']:,}")
        print(f"   📊 Long careers (>10 years): {issues['long_careers']:,}")
        print(f"   ✅ Career analysis compliance: {overall_compliance:.1f}%")

    def _validate_professional_distribution(self, records: List[Dict], results: Dict[str, Any]):
        """Validate professional background distribution"""
        print("\n7. 📊 Professional Distribution Validation")

        issues = {
            'profession_types': {},
            'top_professions': {},
            'top_entities': {},
            'geographic_distribution': {},
            'total_records': len(records)
        }

        # Analyze profession types
        for record in records:
            prof_type = record.get('profession_type', 'Unknown')
            issues['profession_types'][prof_type] = issues['profession_types'].get(prof_type, 0) + 1

            # Track top professions
            prof_name = record.get('profession_name', 'Unknown')
            issues['top_professions'][prof_name] = issues['top_professions'].get(prof_name, 0) + 1

            # Track top entities
            entity_name = record.get('entity_name')
            if entity_name:
                issues['top_entities'][entity_name] = issues['top_entities'].get(entity_name, 0) + 1

            # Geographic distribution
            entity_state = record.get('entity_state')
            if entity_state:
                issues['geographic_distribution'][entity_state] = issues['geographic_distribution'].get(entity_state, 0) + 1

        # Calculate distribution balance
        profession_balance = len(issues['profession_types'])
        entity_diversity = len(issues['top_entities'])
        geographic_coverage = len(issues['geographic_distribution'])

        # Professional diversity score
        diversity_score = min(100, (profession_balance * 20 + entity_diversity * 0.5 + geographic_coverage * 3))

        results['validation_categories']['professional_distribution'] = {
            'compliance_percentage': diversity_score,
            'issues': issues,
            'status': 'PASS' if diversity_score >= 70 else 'FAIL'
        }

        print(f"   📊 Profession types: {dict(list(issues['profession_types'].items())[:3])}")
        print(f"   📊 Top professions: {dict(list(sorted(issues['top_professions'].items(), key=lambda x: x[1], reverse=True)[:3]))}")
        if issues['top_entities']:
            print(f"   📊 Top entities: {dict(list(sorted(issues['top_entities'].items(), key=lambda x: x[1], reverse=True)[:3]))}")
        print(f"   📊 Geographic coverage: {len(issues['geographic_distribution'])} states")
        print(f"   ✅ Professional distribution compliance: {diversity_score:.1f}%")

    def _validate_politician_references(self, records: List[Dict], results: Dict[str, Any]):
        """Validate politician reference integrity"""
        print("\n8. 👥 Politician References Validation")

        issues = {
            'valid_politician_refs': 0,
            'missing_politician_refs': 0,
            'orphaned_records': 0,
            'politicians_with_data': 0,
            'total_records': len(records)
        }

        # Check politician references
        politician_ids = set()
        for record in records:
            politician_id = record.get('politician_id')
            if politician_id and record.get('nome_civil'):  # Has valid join with politicians table
                issues['valid_politician_refs'] += 1
                politician_ids.add(politician_id)
            else:
                issues['missing_politician_refs'] += 1
                if politician_id:
                    issues['orphaned_records'] += 1

        issues['politicians_with_data'] = len(politician_ids)

        # Calculate reference integrity
        ref_integrity = (issues['valid_politician_refs'] / issues['total_records']) * 100 if issues['total_records'] > 0 else 0

        results['validation_categories']['politician_references'] = {
            'compliance_percentage': ref_integrity,
            'issues': issues,
            'status': 'PASS' if ref_integrity >= 98 else 'FAIL'
        }

        print(f"   📊 Valid politician references: {issues['valid_politician_refs']:,} ({ref_integrity:.1f}%)")
        print(f"   📊 Unique politicians with data: {issues['politicians_with_data']:,}")
        print(f"   ✅ Reference integrity compliance: {ref_integrity:.1f}%")
        if issues['orphaned_records'] > 0:
            print(f"   ⚠️  Orphaned records: {issues['orphaned_records']:,}")

    def _calculate_compliance_score(self, results: Dict[str, Any]):
        """Calculate weighted overall compliance score"""
        weights = {
            'core_identifiers': 0.20,
            'profession_details': 0.15,
            'entity_information': 0.15,
            'temporal_data': 0.15,
            'data_quality': 0.15,
            'career_analysis': 0.10,
            'professional_distribution': 0.05,
            'politician_references': 0.05
        }

        total_score = 0
        total_weight = 0

        for category, weight in weights.items():
            if category in results['validation_categories']:
                score = results['validation_categories'][category]['compliance_percentage']
                total_score += score * weight
                total_weight += weight

        results['compliance_score'] = total_score / total_weight if total_weight > 0 else 0

    def _generate_recommendations(self, results: Dict[str, Any]):
        """Generate actionable recommendations based on validation results"""
        recommendations = []

        for category, data in results['validation_categories'].items():
            if data['status'] == 'FAIL':
                if category == 'core_identifiers':
                    recommendations.append("🔑 Fix missing core identifiers (politician_id, profession_type, profession_name)")
                elif category == 'profession_details':
                    recommendations.append("💼 Improve profession code coverage and professional title completeness")
                elif category == 'entity_information':
                    recommendations.append("🏢 Enhance entity name normalization and geographic information")
                elif category == 'temporal_data':
                    recommendations.append("⏰ Validate year ranges and fix future/invalid dates")
                elif category == 'data_quality':
                    recommendations.append("📊 Improve text normalization and reduce empty strings")
                elif category == 'career_analysis':
                    recommendations.append("📈 Enhance career progression tracking and chronological ordering")
                elif category == 'professional_distribution':
                    recommendations.append("📊 Improve professional diversity and geographic coverage")
                elif category == 'politician_references':
                    recommendations.append("👥 Fix orphaned records and politician reference integrity")

        results['recommendations'] = recommendations

    def _print_validation_summary(self, results: Dict[str, Any]):
        """Print comprehensive validation summary"""
        print("\n" + "=" * 60)
        print("📊 PROFESSIONAL VALIDATION SUMMARY")
        print("=" * 60)

        compliance_score = results['compliance_score']
        print(f"🎯 Overall Compliance Score: {compliance_score:.1f}%")

        if compliance_score >= 90:
            print("🏆 EXCELLENT - Professional data meets high quality standards")
        elif compliance_score >= 80:
            print("✅ GOOD - Professional data quality is acceptable with minor issues")
        elif compliance_score >= 70:
            print("⚠️ MODERATE - Professional data needs improvement")
        else:
            print("❌ POOR - Professional data requires significant attention")

        # Category breakdown
        print(f"\n📋 Category Performance:")
        for category, data in results['validation_categories'].items():
            status_icon = "✅" if data['status'] == 'PASS' else "❌"
            print(f"   {status_icon} {category.replace('_', ' ').title()}: {data['compliance_percentage']:.1f}%")

        # Recommendations
        if results['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in results['recommendations'][:5]:  # Top 5 recommendations
                print(f"   {rec}")

        print(f"\n📊 Total Records Validated: {results['total_records']:,}")
        print("=" * 60)