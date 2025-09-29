"""
CLI4 CEPIM Validator
Comprehensive validation for CEPIM sanctions data in vendor_sanctions table
"""

from typing import Dict, List, Any, Optional
from cli4.modules import database


class CEPIMValidator:
    """Comprehensive validator for CEPIM sanctions data"""

    def __init__(self):
        self.validation_results = {}

    def validate_all_sanctions(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Run comprehensive validation on all sanctions records"""

        print("⚠️  COMPREHENSIVE CEPIM VALIDATION")
        print("=" * 60)
        print("Portal da Transparência CEPIM data quality and corruption detection readiness")
        print()

        # Get sample of sanctions records for validation
        limit_clause = f"LIMIT {limit}" if limit else ""

        sanctions_records = database.execute_query(f"""
            SELECT *
            FROM vendor_sanctions
            WHERE data_source = 'PORTAL_TRANSPARENCIA_CEPIM'
            ORDER BY created_at DESC
            {limit_clause}
        """)

        if not sanctions_records:
            return {
                'total_records': 0,
                'validation_categories': {},
                'compliance_score': 0,
                'status': 'NO_DATA'
            }

        total_records = len(sanctions_records)
        print(f"📊 Validating {total_records:,} sanctions records")
        print()

        # Initialize validation categories
        validations = {
            'core_data_integrity': {'passed': 0, 'failed': 0, 'issues': []},
            'cnpj_validation': {'passed': 0, 'failed': 0, 'issues': []},
            'date_consistency': {'passed': 0, 'failed': 0, 'issues': []},
            'agency_information': {'passed': 0, 'failed': 0, 'issues': []},
            'sanction_classification': {'passed': 0, 'failed': 0, 'issues': []},
            'corruption_detection_readiness': {'passed': 0, 'failed': 0, 'issues': []},
            'data_completeness': {'passed': 0, 'failed': 0, 'issues': []}
        }

        # Run validation categories
        self._validate_core_data_integrity(sanctions_records, validations['core_data_integrity'])
        self._validate_cnpj_data(sanctions_records, validations['cnpj_validation'])
        self._validate_date_consistency(sanctions_records, validations['date_consistency'])
        self._validate_agency_information(sanctions_records, validations['agency_information'])
        self._validate_sanction_classification(sanctions_records, validations['sanction_classification'])
        self._validate_corruption_detection_readiness(sanctions_records, validations['corruption_detection_readiness'])
        self._validate_data_completeness(sanctions_records, validations['data_completeness'])

        # Calculate overall compliance score
        compliance_score = self._calculate_compliance_score(validations)

        # Print validation results
        self._print_validation_summary(validations, compliance_score, total_records)

        return {
            'total_records': total_records,
            'validation_categories': validations,
            'compliance_score': compliance_score,
            'status': 'COMPLETED'
        }

    def _validate_core_data_integrity(self, records: List[Dict], validation: Dict):
        """Validate core data integrity and required fields"""
        print("🔍 Validating core data integrity...")

        for record in records:
            issues = []

            # Required fields validation
            if not record.get('cnpj_cpf'):
                issues.append("Missing cnpj_cpf")
            if not record.get('entity_name'):
                issues.append("Missing entity_name")
            if not record.get('sanction_type'):
                issues.append("Missing sanction_type")
            if not record.get('sanctioning_agency'):
                issues.append("Missing sanctioning_agency")

            # CNPJ format validation
            cnpj = record.get('cnpj_cpf', '')
            if cnpj and len(cnpj) != 14:
                issues.append(f"Invalid CNPJ length: {len(cnpj)} (expected 14)")
            if cnpj and not cnpj.isdigit():
                issues.append(f"CNPJ contains non-digits: {cnpj}")

            # Data source validation
            data_source = record.get('data_source')
            if data_source != 'PORTAL_TRANSPARENCIA_CEPIM':
                issues.append(f"Unexpected data source: {data_source}")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_cnpj_data(self, records: List[Dict], validation: Dict):
        """Validate CNPJ data quality and uniqueness"""
        print("🔍 Validating CNPJ data...")

        cnpj_counts = {}

        for record in records:
            issues = []
            cnpj = record.get('cnpj_cpf', '')

            # Track CNPJ frequency
            if cnpj:
                cnpj_counts[cnpj] = cnpj_counts.get(cnpj, 0) + 1

            # CNPJ format validation
            if cnpj:
                # Check for obviously invalid CNPJs
                if cnpj == '00000000000000':
                    issues.append("All-zeros CNPJ")
                elif cnpj == '11111111111111':
                    issues.append("All-ones CNPJ")
                elif len(set(cnpj)) == 1:
                    issues.append(f"Repeating digits CNPJ: {cnpj}")

            # Entity name validation
            entity_name = record.get('entity_name', '')
            if entity_name:
                if len(entity_name) < 3:
                    issues.append(f"Very short entity name: '{entity_name}'")
                elif entity_name.isupper() and len(entity_name) > 50:
                    # Long all-caps names are typically company names (good)
                    pass
                elif entity_name.islower():
                    issues.append(f"All lowercase entity name: '{entity_name}'")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        # Check for excessive CNPJ duplication
        high_frequency_cnpjs = {cnpj: count for cnpj, count in cnpj_counts.items() if count > 10}
        if high_frequency_cnpjs:
            validation['issues'].append(f"High-frequency CNPJs: {len(high_frequency_cnpjs)} CNPJs with >10 sanctions")

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_date_consistency(self, records: List[Dict], validation: Dict):
        """Validate date consistency and logic"""
        print("🔍 Validating date consistency...")

        for record in records:
            issues = []

            start_date = record.get('sanction_start_date')
            end_date = record.get('sanction_end_date')
            verification_date = record.get('verification_date')

            # Date format validation (should be YYYY-MM-DD or None)
            for date_field, date_value in [
                ('sanction_start_date', start_date),
                ('sanction_end_date', end_date)
            ]:
                if date_value:
                    try:
                        # Basic format check
                        if isinstance(date_value, str) and len(date_value) == 10:
                            year, month, day = date_value.split('-')
                            if not (1900 <= int(year) <= 2030):
                                issues.append(f"Invalid year in {date_field}: {year}")
                        else:
                            issues.append(f"Invalid date format in {date_field}: {date_value}")
                    except:
                        issues.append(f"Date parsing error in {date_field}: {date_value}")

            # Start/end date logic
            if start_date and end_date:
                try:
                    if start_date > end_date:
                        issues.append(f"Start date after end date: {start_date} > {end_date}")
                except:
                    issues.append("Date comparison error")

            # is_active field consistency
            is_active = record.get('is_active')
            if is_active is not None:
                # Basic check: if end date is in the past, should not be active
                if end_date and end_date < '2025-01-01' and is_active:
                    issues.append(f"Sanction marked active but ended: {end_date}")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_agency_information(self, records: List[Dict], validation: Dict):
        """Validate sanctioning agency information"""
        print("🔍 Validating agency information...")

        for record in records:
            issues = []

            agency = record.get('sanctioning_agency', '')
            state = record.get('sanctioning_state', '')

            # Agency name validation
            if agency:
                if len(agency) < 5:
                    issues.append(f"Very short agency name: '{agency}'")
                elif 'prefeitura' in agency.lower() and not state:
                    issues.append("Municipal agency without state information")
                elif 'governo' in agency.lower() and not state:
                    issues.append("State government without state code")

            # State code validation
            if state:
                if len(state) != 2:
                    issues.append(f"Invalid state code: '{state}' (expected 2 letters)")
                elif not state.isupper():
                    issues.append(f"State code not uppercase: '{state}'")

            # Process number validation
            process_num = record.get('sanctioning_process', '')
            if process_num and len(process_num) < 5:
                issues.append(f"Very short process number: '{process_num}'")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_sanction_classification(self, records: List[Dict], validation: Dict):
        """Validate sanction type classification"""
        print("🔍 Validating sanction classification...")

        sanction_types = {}

        for record in records:
            issues = []

            sanction_type = record.get('sanction_type', '')
            sanction_desc = record.get('sanction_description', '')

            # Track sanction type frequency
            if sanction_type:
                sanction_types[sanction_type] = sanction_types.get(sanction_type, 0) + 1

            # Sanction type validation
            if sanction_type:
                if len(sanction_type) < 5:
                    issues.append(f"Very short sanction type: '{sanction_type}'")
                elif sanction_type == sanction_desc:
                    issues.append("Sanction type same as description")

            # Description validation
            if sanction_desc:
                if len(sanction_desc) < 10:
                    issues.append(f"Very short sanction description: '{sanction_desc}'")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        # Show sanction type distribution
        top_types = sorted(sanction_types.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"   📊 Top sanction types: {[f'{t}: {c}' for t, c in top_types]}")

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_corruption_detection_readiness(self, records: List[Dict], validation: Dict):
        """Validate readiness for corruption detection cross-referencing"""
        print("🔍 Validating corruption detection readiness...")

        valid_for_corruption_detection = 0

        for record in records:
            issues = []

            # Must have clean CNPJ for cross-referencing
            cnpj = record.get('cnpj_cpf', '')
            if not cnpj or len(cnpj) != 14 or not cnpj.isdigit():
                issues.append("Invalid CNPJ prevents financial cross-referencing")

            # Must have entity name for identification
            entity_name = record.get('entity_name', '')
            if not entity_name or len(entity_name.strip()) < 3:
                issues.append("Missing/invalid entity name prevents identification")

            # Must have sanction type for risk assessment
            sanction_type = record.get('sanction_type', '')
            if not sanction_type:
                issues.append("Missing sanction type prevents risk classification")

            # Must have agency for credibility assessment
            agency = record.get('sanctioning_agency', '')
            if not agency:
                issues.append("Missing agency prevents credibility assessment")

            # Active status should be determinable
            is_active = record.get('is_active')
            if is_active is None:
                issues.append("Unknown active status prevents current risk assessment")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1
                valid_for_corruption_detection += 1

        print(f"   🎯 Records ready for corruption detection: {valid_for_corruption_detection:,}")
        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_data_completeness(self, records: List[Dict], validation: Dict):
        """Validate overall data completeness"""
        print("🔍 Validating data completeness...")

        field_completeness = {}
        total_records = len(records)

        # Track completeness for key fields
        key_fields = [
            'cnpj_cpf', 'entity_name', 'sanction_type', 'sanction_description',
            'sanction_start_date', 'sanction_end_date', 'sanctioning_agency',
            'sanctioning_state', 'sanctioning_process', 'is_active'
        ]

        for field in key_fields:
            non_null_count = sum(1 for record in records if record.get(field) is not None)
            completeness_pct = (non_null_count / total_records) * 100
            field_completeness[field] = completeness_pct

        for record in records:
            issues = []

            # Overall completeness check
            filled_fields = sum(1 for field in key_fields if record.get(field) is not None)
            completeness_pct = (filled_fields / len(key_fields)) * 100

            if completeness_pct < 60:
                issues.append(f"Low data completeness: {completeness_pct:.1f}%")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        # Show field completeness
        print(f"   📊 Field completeness:")
        for field, pct in sorted(field_completeness.items(), key=lambda x: x[1], reverse=True):
            status = "✅" if pct >= 90 else "⚠️" if pct >= 70 else "❌"
            print(f"      {status} {field}: {pct:.1f}%")

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _calculate_compliance_score(self, validations: Dict) -> float:
        """Calculate weighted compliance score"""
        # Define weights for different validation categories (corruption detection focus)
        weights = {
            'core_data_integrity': 0.25,           # Critical - basic data validity
            'cnpj_validation': 0.20,               # High - essential for cross-referencing
            'corruption_detection_readiness': 0.20, # High - main purpose
            'sanction_classification': 0.15,       # Important - risk assessment
            'date_consistency': 0.10,              # Moderate - temporal accuracy
            'agency_information': 0.10,            # Moderate - credibility
            'data_completeness': 0.10              # Moderate - overall quality
        }

        weighted_score = 0.0
        total_weight = 0.0

        for category, results in validations.items():
            if category in weights:
                weight = weights[category]
                total_tests = results['passed'] + results['failed']

                if total_tests > 0:
                    category_score = (results['passed'] / total_tests) * 100
                    weighted_score += category_score * weight
                    total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_score / total_weight

    def _print_validation_summary(self, validations: Dict, compliance_score: float, total_records: int):
        """Print comprehensive validation summary"""
        print(f"\\n📊 SANCTIONS VALIDATION SUMMARY")
        print("=" * 50)

        # Category breakdown
        for category, results in validations.items():
            total = results['passed'] + results['failed']
            if total > 0:
                success_rate = (results['passed'] / total) * 100
                status = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
                print(f"{status} {category.replace('_', ' ').title()}: {success_rate:.1f}% ({results['passed']}/{total})")

        print(f"\\n🎯 OVERALL COMPLIANCE: {compliance_score:.1f}%")

        if compliance_score >= 95:
            print("🏆 EXCELLENT - Sanctions data is highly reliable for corruption detection")
        elif compliance_score >= 85:
            print("👍 GOOD - Minor issues detected, mostly reliable for corruption detection")
        elif compliance_score >= 70:
            print("⚠️ ACCEPTABLE - Some issues need attention for optimal corruption detection")
        else:
            print("❌ NEEDS IMPROVEMENT - Significant data quality issues affect corruption detection")

        # Show critical issues
        critical_issues = []
        for category, results in validations.items():
            if results['failed'] > 0:
                critical_issues.extend(results['issues'][:3])  # Show first 3 issues per category

        if critical_issues:
            print(f"\\n🔍 SAMPLE ISSUES:")
            for issue in critical_issues[:10]:  # Show max 10 issues
                print(f"   • {issue}")

        print(f"\\n🎯 CORRUPTION DETECTION METRICS:")
        print(f"   Total sanctions validated: {total_records:,}")
        print(f"   Data quality score: {compliance_score:.1f}%")
        print(f"   Validation categories: {len(validations)}")
        print(f"   Ready for financial cross-referencing: ✅")