"""
CLI4 Electoral Validator
Validate unified_electoral_records table for data quality and completeness
"""

from typing import Dict, List, Any
from cli4.modules import database


class ElectoralRecordsValidator:
    """Comprehensive electoral data validation"""

    def __init__(self):
        self.validation_results = {
            'electoral_records': {},
            'outcome_analysis': {},
            'referential_integrity': {},
            'data_quality': {},
            'summary': {},
            'compliance_score': 0.0
        }

    def validate_all_electoral(self) -> Dict[str, Any]:
        """Run comprehensive validation on electoral records table"""
        print("🔍 COMPREHENSIVE ELECTORAL VALIDATION")
        print("=" * 60)
        print("Validating unified_electoral_records table")
        print("=" * 60)

        # Validate basic table structure
        self._validate_electoral_records()

        # Validate electoral outcomes
        self._validate_electoral_outcomes()

        # Validate referential integrity
        self._validate_referential_integrity()

        # Analyze data quality
        self._analyze_data_quality()

        # Calculate compliance score
        self._calculate_compliance_score()

        # Print results
        self._print_validation_summary()

        return self.validation_results

    def _validate_electoral_records(self):
        """Validate unified_electoral_records table structure and completeness"""
        print("📊 Validating unified_electoral_records table...")

        # Get electoral records data
        records = database.execute_query("SELECT * FROM unified_electoral_records")

        if not records:
            self.validation_results['electoral_records'] = {
                'total_records': 0,
                'issues': ['❌ No electoral records found in database'],
                'completion_rate': 0
            }
            return

        issues = []
        total_records = len(records)

        # Check REQUIRED fields
        missing_politician_id = [r for r in records if not r.get('politician_id')]
        missing_election_year = [r for r in records if not r.get('election_year')]
        missing_candidate_name = [r for r in records if not r.get('candidate_name')]
        missing_electoral_outcome = [r for r in records if not r.get('electoral_outcome')]

        # Check IMPORTANT fields for analysis
        missing_cpf_candidate = [r for r in records if not r.get('cpf_candidate')]
        missing_position_description = [r for r in records if not r.get('position_description')]
        missing_party_code = [r for r in records if not r.get('party_code')]
        missing_state_code = [r for r in records if not r.get('state_code')]

        # Check DERIVED analysis fields
        missing_was_elected = [r for r in records if r.get('was_elected') is None]
        missing_status_category = [r for r in records if not r.get('election_status_category')]

        # Report issues
        if missing_politician_id:
            issues.append(f"❌ {len(missing_politician_id)} records missing politician_id")

        if missing_election_year:
            issues.append(f"❌ {len(missing_election_year)} records missing election_year")

        if missing_candidate_name:
            issues.append(f"❌ {len(missing_candidate_name)} records missing candidate_name")

        if missing_electoral_outcome:
            issues.append(f"❌ {len(missing_electoral_outcome)} records missing electoral_outcome")

        if missing_cpf_candidate:
            issues.append(f"⚠️ {len(missing_cpf_candidate)} records missing cpf_candidate")

        if missing_position_description:
            issues.append(f"⚠️ {len(missing_position_description)} records missing position_description")

        if missing_party_code:
            issues.append(f"⚠️ {len(missing_party_code)} records missing party_code")

        if missing_state_code:
            issues.append(f"⚠️ {len(missing_state_code)} records missing state_code")

        if missing_was_elected:
            issues.append(f"⚠️ {len(missing_was_elected)} records missing was_elected analysis")

        if missing_status_category:
            issues.append(f"⚠️ {len(missing_status_category)} records missing election_status_category")

        # Calculate completion rate based on critical fields
        critical_fields_complete = total_records - max(
            len(missing_politician_id),
            len(missing_election_year),
            len(missing_candidate_name),
            len(missing_electoral_outcome)
        )
        completion_rate = (critical_fields_complete / total_records) * 100 if total_records > 0 else 0

        self.validation_results['electoral_records'] = {
            'total_records': total_records,
            'issues': issues,
            'completion_rate': completion_rate,
            'critical_fields_complete': critical_fields_complete,
            'analysis_fields_complete': total_records - len(missing_was_elected)
        }

        print(f"  📋 Total records: {total_records}")
        print(f"  ✅ Completion rate: {completion_rate:.1f}%")
        for issue in issues:
            print(f"  {issue}")

    def _validate_electoral_outcomes(self):
        """Validate electoral outcomes data and derived analysis"""
        print("\n🗳️ Validating electoral outcomes...")

        # Get outcome distribution
        outcome_query = """
            SELECT
                electoral_outcome,
                was_elected,
                election_status_category,
                COUNT(*) as count
            FROM unified_electoral_records
            GROUP BY electoral_outcome, was_elected, election_status_category
            ORDER BY count DESC
        """
        outcomes = database.execute_query(outcome_query)

        if not outcomes:
            self.validation_results['outcome_analysis'] = {
                'total_outcomes': 0,
                'issues': ['❌ No electoral outcomes found']
            }
            return

        issues = []
        total_outcomes = sum(o['count'] for o in outcomes)

        # Analyze outcome categories
        elected_count = sum(o['count'] for o in outcomes if o.get('was_elected'))
        not_elected_count = sum(o['count'] for o in outcomes if not o.get('was_elected'))
        unknown_election_status = sum(o['count'] for o in outcomes if o.get('was_elected') is None)

        # Check for inconsistencies
        inconsistent_outcomes = []
        for outcome in outcomes:
            outcome_text = outcome.get('electoral_outcome', '').upper()
            was_elected = outcome.get('was_elected')
            category = outcome.get('election_status_category')

            # Check for logical inconsistencies
            if 'ELEITO' in outcome_text and 'NÃO ELEITO' not in outcome_text:
                if not was_elected:
                    inconsistent_outcomes.append(f"'{outcome_text}' marked as not elected")
            elif 'NÃO ELEITO' in outcome_text:
                if was_elected:
                    inconsistent_outcomes.append(f"'{outcome_text}' marked as elected")

        if inconsistent_outcomes:
            issues.extend([f"❌ Inconsistent outcome: {inc}" for inc in inconsistent_outcomes[:5]])

        if unknown_election_status > 0:
            issues.append(f"⚠️ {unknown_election_status} records with unknown election status")

        # Calculate election success rate
        success_rate = (elected_count / total_outcomes) * 100 if total_outcomes > 0 else 0

        self.validation_results['outcome_analysis'] = {
            'total_outcomes': total_outcomes,
            'elected_count': elected_count,
            'not_elected_count': not_elected_count,
            'success_rate': success_rate,
            'outcome_categories': len(set(o.get('election_status_category') for o in outcomes if o.get('election_status_category'))),
            'issues': issues
        }

        print(f"  📊 Total outcomes: {total_outcomes}")
        print(f"  ✅ Elected: {elected_count} ({success_rate:.1f}%)")
        print(f"  ❌ Not elected: {not_elected_count}")
        print(f"  📂 Outcome categories: {self.validation_results['outcome_analysis']['outcome_categories']}")
        for issue in issues:
            print(f"  {issue}")

    def _validate_referential_integrity(self):
        """Validate referential integrity with unified_politicians table"""
        print("\n🔗 Validating referential integrity...")

        # Check orphaned electoral records
        orphaned_query = """
            SELECT COUNT(*) as orphaned_count
            FROM unified_electoral_records er
            LEFT JOIN unified_politicians p ON er.politician_id = p.id
            WHERE p.id IS NULL
        """
        orphaned_result = database.execute_query(orphaned_query)
        orphaned_count = orphaned_result[0]['orphaned_count'] if orphaned_result else 0

        # Check politicians with electoral records
        politicians_with_records_query = """
            SELECT COUNT(DISTINCT er.politician_id) as politicians_with_records
            FROM unified_electoral_records er
        """
        politicians_result = database.execute_query(politicians_with_records_query)
        politicians_with_records = politicians_result[0]['politicians_with_records'] if politicians_result else 0

        # Check total politicians
        total_politicians_query = "SELECT COUNT(*) as total FROM unified_politicians"
        total_result = database.execute_query(total_politicians_query)
        total_politicians = total_result[0]['total'] if total_result else 0

        # Calculate coverage
        coverage_rate = (politicians_with_records / total_politicians) * 100 if total_politicians > 0 else 0

        issues = []
        if orphaned_count > 0:
            issues.append(f"❌ {orphaned_count} orphaned electoral records (invalid politician_id)")

        if coverage_rate < 50:
            issues.append(f"⚠️ Low coverage: only {coverage_rate:.1f}% of politicians have electoral records")

        self.validation_results['referential_integrity'] = {
            'orphaned_records': orphaned_count,
            'politicians_with_records': politicians_with_records,
            'total_politicians': total_politicians,
            'coverage_rate': coverage_rate,
            'issues': issues
        }

        print(f"  🏛️ Politicians with electoral records: {politicians_with_records}/{total_politicians} ({coverage_rate:.1f}%)")
        print(f"  🔗 Orphaned records: {orphaned_count}")
        for issue in issues:
            print(f"  {issue}")

    def _analyze_data_quality(self):
        """Analyze overall data quality metrics"""
        print("\n📈 Analyzing data quality...")

        # Election year distribution
        year_query = """
            SELECT election_year, COUNT(*) as count
            FROM unified_electoral_records
            GROUP BY election_year
            ORDER BY election_year DESC
        """
        years = database.execute_query(year_query)

        # Position distribution
        position_query = """
            SELECT position_description, COUNT(*) as count
            FROM unified_electoral_records
            WHERE position_description IS NOT NULL
            GROUP BY position_description
            ORDER BY count DESC
            LIMIT 10
        """
        positions = database.execute_query(position_query)

        # Party distribution
        party_query = """
            SELECT party_code, COUNT(*) as count
            FROM unified_electoral_records
            WHERE party_code IS NOT NULL
            GROUP BY party_code
            ORDER BY count DESC
            LIMIT 10
        """
        parties = database.execute_query(party_query)

        issues = []

        # Check year coverage
        expected_years = [2018, 2020, 2022]
        found_years = [y['election_year'] for y in years if y['election_year']]
        missing_years = [y for y in expected_years if y not in found_years]

        if missing_years:
            issues.append(f"⚠️ Missing data for years: {missing_years}")

        # Check for reasonable data distribution
        if len(positions) < 5:
            issues.append("⚠️ Limited position diversity in electoral records")

        if len(parties) < 10:
            issues.append("⚠️ Limited party diversity in electoral records")

        self.validation_results['data_quality'] = {
            'election_years': len(years),
            'year_distribution': years,
            'position_types': len(positions),
            'party_diversity': len(parties),
            'missing_years': missing_years,
            'issues': issues
        }

        print(f"  📅 Election years covered: {len(years)}")
        print(f"  🏛️ Position types: {len(positions)}")
        print(f"  🎯 Party diversity: {len(parties)}")
        for issue in issues:
            print(f"  {issue}")

    def _calculate_compliance_score(self):
        """Calculate overall compliance score"""
        # Scoring components
        structure_score = min(self.validation_results['electoral_records'].get('completion_rate', 0), 100) / 100
        outcome_score = 1.0 if len(self.validation_results['outcome_analysis'].get('issues', [])) == 0 else 0.8
        integrity_score = 1.0 if self.validation_results['referential_integrity'].get('orphaned_records', 0) == 0 else 0.7
        quality_score = max(0.5, 1.0 - (len(self.validation_results['data_quality'].get('issues', [])) * 0.1))

        # Weighted average
        compliance_score = (
            structure_score * 0.4 +
            outcome_score * 0.3 +
            integrity_score * 0.2 +
            quality_score * 0.1
        ) * 100

        self.validation_results['compliance_score'] = compliance_score

        # Overall grade
        if compliance_score >= 90:
            grade = "A - EXCELLENT"
        elif compliance_score >= 80:
            grade = "B - GOOD"
        elif compliance_score >= 70:
            grade = "C - ACCEPTABLE"
        elif compliance_score >= 60:
            grade = "D - NEEDS IMPROVEMENT"
        else:
            grade = "F - CRITICAL ISSUES"

        self.validation_results['summary'] = {
            'grade': grade,
            'compliance_score': compliance_score,
            'total_issues': sum(len(section.get('issues', [])) for section in [
                self.validation_results['electoral_records'],
                self.validation_results['outcome_analysis'],
                self.validation_results['referential_integrity'],
                self.validation_results['data_quality']
            ])
        }

    def _print_validation_summary(self):
        """Print comprehensive validation summary"""
        print("\n" + "=" * 60)
        print("📋 ELECTORAL VALIDATION SUMMARY")
        print("=" * 60)

        summary = self.validation_results['summary']
        print(f"🎯 Overall Grade: {summary['grade']}")
        print(f"📊 Compliance Score: {summary['compliance_score']:.1f}%")
        print(f"⚠️ Total Issues: {summary['total_issues']}")

        # Detailed breakdown
        print(f"\n📊 DETAILED BREAKDOWN:")
        print(f"   Electoral Records: {self.validation_results['electoral_records'].get('total_records', 0)} records")
        print(f"   Completion Rate: {self.validation_results['electoral_records'].get('completion_rate', 0):.1f}%")
        print(f"   Electoral Outcomes: {self.validation_results['outcome_analysis'].get('total_outcomes', 0)} analyzed")
        print(f"   Success Rate: {self.validation_results['outcome_analysis'].get('success_rate', 0):.1f}%")
        print(f"   Politician Coverage: {self.validation_results['referential_integrity'].get('coverage_rate', 0):.1f}%")
        print(f"   Election Years: {self.validation_results['data_quality'].get('election_years', 0)}")

        print(f"\n✅ ELECTORAL VALIDATION COMPLETED")
        return self.validation_results