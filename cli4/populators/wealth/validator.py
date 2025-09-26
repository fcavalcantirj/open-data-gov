"""
CLI4 Wealth Validator
Comprehensive validation for unified_wealth_tracking table
"""

from typing import Dict, List, Any, Optional
from cli4.modules import database


class CLI4WealthValidator:
    """Comprehensive validator for wealth tracking data"""

    def __init__(self):
        self.validation_results = {}

    def validate_all_wealth(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Run comprehensive validation on all wealth tracking records"""

        print("🔍 COMPREHENSIVE WEALTH TRACKING VALIDATION")
        print("=" * 60)
        print("Validating wealth progression, asset categories, and data quality")
        print()

        # Get sample of wealth records for validation
        limit_clause = f"LIMIT {limit}" if limit else ""

        wealth_records = database.execute_query(f"""
            SELECT wt.*, p.nome_civil, p.cpf
            FROM unified_wealth_tracking wt
            LEFT JOIN unified_politicians p ON wt.politician_id = p.id
            ORDER BY wt.politician_id, wt.year
            {limit_clause}
        """)

        if not wealth_records:
            return {
                'total_records': 0,
                'validation_categories': {},
                'compliance_score': 0,
                'status': 'NO_DATA'
            }

        total_records = len(wealth_records)
        print(f"📊 Validating {total_records:,} wealth tracking records")
        print()

        # Initialize validation categories
        validations = {
            'core_data_integrity': {'passed': 0, 'failed': 0, 'issues': []},
            'wealth_calculations': {'passed': 0, 'failed': 0, 'issues': []},
            'asset_categorization': {'passed': 0, 'failed': 0, 'issues': []},
            'temporal_consistency': {'passed': 0, 'failed': 0, 'issues': []},
            'progression_logic': {'passed': 0, 'failed': 0, 'issues': []},
            'data_quality': {'passed': 0, 'failed': 0, 'issues': []},
            'politician_correlation': {'passed': 0, 'failed': 0, 'issues': []}
        }

        # Group records by politician for progression analysis
        politicians_data = {}
        for record in wealth_records:
            politician_id = record['politician_id']
            if politician_id not in politicians_data:
                politicians_data[politician_id] = []
            politicians_data[politician_id].append(record)

        # Sort each politician's records by year
        for politician_id in politicians_data:
            politicians_data[politician_id].sort(key=lambda x: x['year'])

        # Run validation categories
        self._validate_core_data_integrity(wealth_records, validations['core_data_integrity'])
        self._validate_wealth_calculations(wealth_records, validations['wealth_calculations'])
        self._validate_asset_categorization(wealth_records, validations['asset_categorization'])
        self._validate_temporal_consistency(politicians_data, validations['temporal_consistency'])
        self._validate_progression_logic(politicians_data, validations['progression_logic'])
        self._validate_data_quality(wealth_records, validations['data_quality'])
        self._validate_politician_correlation(wealth_records, validations['politician_correlation'])

        # Calculate overall compliance score
        compliance_score = self._calculate_compliance_score(validations)

        # Print validation results
        self._print_validation_summary(validations, compliance_score, total_records)

        return {
            'total_records': total_records,
            'politicians_analyzed': len(politicians_data),
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
            if not record.get('politician_id'):
                issues.append("Missing politician_id")
            if not record.get('year'):
                issues.append("Missing year")
            if record.get('total_declared_wealth') is None:
                issues.append("Missing total_declared_wealth")
            if record.get('number_of_assets') is None:
                issues.append("Missing number_of_assets")

            # Year validity
            year = record.get('year')
            if year and (year < 2000 or year > 2030):
                issues.append(f"Invalid year: {year}")

            # Wealth value validity
            wealth = record.get('total_declared_wealth')
            if wealth is not None and wealth < 0:
                issues.append(f"Negative wealth: {wealth}")

            # Asset count validity
            asset_count = record.get('number_of_assets')
            if asset_count is not None and asset_count < 0:
                issues.append(f"Negative asset count: {asset_count}")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_wealth_calculations(self, records: List[Dict], validation: Dict):
        """Validate wealth calculation accuracy"""
        print("🔍 Validating wealth calculations...")

        for record in records:
            issues = []

            # Category totals should sum to approximately total wealth
            category_sum = (
                (record.get('real_estate_value') or 0) +
                (record.get('vehicles_value') or 0) +
                (record.get('investments_value') or 0) +
                (record.get('business_value') or 0) +
                (record.get('cash_deposits_value') or 0) +
                (record.get('other_assets_value') or 0)
            )

            total_wealth = record.get('total_declared_wealth') or 0

            # Allow for small rounding differences
            if abs(category_sum - total_wealth) > 0.01:
                issues.append(f"Category sum ({category_sum}) != Total wealth ({total_wealth})")

            # Individual category validations
            for category in ['real_estate_value', 'vehicles_value', 'investments_value',
                           'business_value', 'cash_deposits_value', 'other_assets_value']:
                value = record.get(category)
                if value is not None and value < 0:
                    issues.append(f"Negative {category}: {value}")

            # Wealth-to-asset ratio reasonableness
            asset_count = record.get('number_of_assets') or 0
            if asset_count > 0 and total_wealth > 0:
                avg_asset_value = total_wealth / asset_count
                if avg_asset_value < 1:  # Less than R$1 per asset seems unreasonable
                    issues.append(f"Unreasonable avg asset value: R${avg_asset_value:.2f}")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_asset_categorization(self, records: List[Dict], validation: Dict):
        """Validate asset categorization logic"""
        print("🔍 Validating asset categorization...")

        for record in records:
            issues = []

            total_wealth = record.get('total_declared_wealth') or 0
            asset_count = record.get('number_of_assets') or 0

            # If there are assets, at least one category should have value
            if asset_count > 0 and total_wealth > 0:
                has_category_value = any([
                    record.get('real_estate_value', 0) > 0,
                    record.get('vehicles_value', 0) > 0,
                    record.get('investments_value', 0) > 0,
                    record.get('business_value', 0) > 0,
                    record.get('cash_deposits_value', 0) > 0,
                    record.get('other_assets_value', 0) > 0
                ])

                if not has_category_value:
                    issues.append("Assets exist but no category has value")

            # No assets should mean no category values (unless rounding)
            if asset_count == 0:
                category_values = [
                    record.get('real_estate_value', 0),
                    record.get('vehicles_value', 0),
                    record.get('investments_value', 0),
                    record.get('business_value', 0),
                    record.get('cash_deposits_value', 0),
                    record.get('other_assets_value', 0)
                ]

                if any(value > 0.01 for value in category_values):
                    issues.append("No assets but category values exist")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_temporal_consistency(self, politicians_data: Dict, validation: Dict):
        """Validate temporal consistency in wealth records"""
        print("🔍 Validating temporal consistency...")

        for politician_id, records in politicians_data.items():
            if len(records) <= 1:
                validation['passed'] += 1
                continue

            issues = []

            # Check year ordering
            years = [record['year'] for record in records]
            if years != sorted(years):
                issues.append(f"Years not in order: {years}")

            # Check for year gaps consistency
            for i in range(1, len(records)):
                current_record = records[i]
                previous_record = records[i-1]

                expected_gap = current_record['year'] - previous_record['year']
                recorded_gap = current_record.get('years_between_declarations')

                if recorded_gap is not None and recorded_gap != expected_gap:
                    issues.append(f"Incorrect year gap: expected {expected_gap}, got {recorded_gap}")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Politician {politician_id}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_progression_logic(self, politicians_data: Dict, validation: Dict):
        """Validate wealth progression logic"""
        print("🔍 Validating wealth progression logic...")

        for politician_id, records in politicians_data.items():
            if len(records) <= 1:
                validation['passed'] += 1
                continue

            issues = []

            for i in range(1, len(records)):
                current_record = records[i]
                previous_record = records[i-1]

                # Check previous year reference
                if current_record.get('previous_year') != previous_record['year']:
                    issues.append(f"Incorrect previous_year reference")

                # Check previous wealth reference
                current_prev_wealth = current_record.get('previous_total_wealth')
                actual_prev_wealth = previous_record.get('total_declared_wealth')

                if (current_prev_wealth is not None and actual_prev_wealth is not None and
                    abs(current_prev_wealth - actual_prev_wealth) > 0.01):
                    issues.append(f"Incorrect previous_total_wealth reference")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Politician {politician_id}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_data_quality(self, records: List[Dict], validation: Dict):
        """Validate overall data quality"""
        print("🔍 Validating data quality...")

        for record in records:
            issues = []

            # Check for reasonable wealth values (not too extreme)
            wealth = record.get('total_declared_wealth', 0)
            if wealth > 1000000000:  # Over R$1 billion seems extreme
                issues.append(f"Extremely high wealth: R${wealth:,.2f}")

            # Check reference date validity
            ref_date = record.get('reference_date')
            year = record.get('year')
            if ref_date and year:
                ref_year = ref_date.year if hasattr(ref_date, 'year') else None
                if ref_year and abs(ref_year - year) > 1:
                    issues.append(f"Reference date year ({ref_year}) doesn't match record year ({year})")

            # Check verification source
            verification_source = record.get('verification_source')
            if not verification_source:
                issues.append("Missing verification_source")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _validate_politician_correlation(self, records: List[Dict], validation: Dict):
        """Validate politician correlation integrity"""
        print("🔍 Validating politician correlation...")

        for record in records:
            issues = []

            # Check if politician exists and has required data
            if not record.get('nome_civil'):
                issues.append("Missing politician name correlation")

            if not record.get('cpf'):
                issues.append("Missing politician CPF correlation")

            # Check politician_id validity
            politician_id = record.get('politician_id')
            if not politician_id:
                issues.append("Missing politician_id")
            elif politician_id <= 0:
                issues.append(f"Invalid politician_id: {politician_id}")

            if issues:
                validation['failed'] += 1
                validation['issues'].extend([
                    f"Record ID {record.get('id', 'unknown')}: {issue}" for issue in issues
                ])
            else:
                validation['passed'] += 1

        print(f"   ✅ Passed: {validation['passed']}, ❌ Failed: {validation['failed']}")

    def _calculate_compliance_score(self, validations: Dict) -> float:
        """Calculate overall compliance score"""
        total_passed = sum(v['passed'] for v in validations.values())
        total_failed = sum(v['failed'] for v in validations.values())
        total_tests = total_passed + total_failed

        if total_tests == 0:
            return 0.0

        return (total_passed / total_tests) * 100

    def _print_validation_summary(self, validations: Dict, compliance_score: float, total_records: int):
        """Print comprehensive validation summary"""
        print(f"\n📊 WEALTH VALIDATION SUMMARY")
        print("=" * 50)

        # Category breakdown
        for category, results in validations.items():
            total = results['passed'] + results['failed']
            if total > 0:
                success_rate = (results['passed'] / total) * 100
                status = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
                print(f"{status} {category.replace('_', ' ').title()}: {success_rate:.1f}% ({results['passed']}/{total})")

        print(f"\n🎯 OVERALL COMPLIANCE: {compliance_score:.1f}%")

        if compliance_score >= 95:
            print("🏆 EXCELLENT - Wealth data is highly reliable")
        elif compliance_score >= 85:
            print("👍 GOOD - Minor issues detected, mostly reliable")
        elif compliance_score >= 70:
            print("⚠️ ACCEPTABLE - Some issues need attention")
        else:
            print("❌ NEEDS IMPROVEMENT - Significant data quality issues")

        # Show critical issues
        critical_issues = []
        for category, results in validations.items():
            if results['failed'] > 0:
                critical_issues.extend(results['issues'][:3])  # Show first 3 issues per category

        if critical_issues:
            print(f"\n🔍 SAMPLE ISSUES:")
            for issue in critical_issues[:10]:  # Show max 10 issues
                print(f"   • {issue}")

        print(f"\n📈 WEALTH TRACKING METRICS:")
        print(f"   Total records validated: {total_records:,}")
        print(f"   Data integrity score: {compliance_score:.1f}%")
        print(f"   Validation categories: {len(validations)}")