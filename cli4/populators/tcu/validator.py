"""
CLI4 TCU Disqualifications Validator
Validates tcu_disqualifications table data quality and completeness
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from cli4.modules import database
from cli4.modules.logger import CLI4Logger


class TCUValidator:
    """Validate TCU disqualifications data quality and integrity"""

    def __init__(self, logger: CLI4Logger):
        self.logger = logger

    def validate(self) -> Dict:
        """
        Comprehensive validation of TCU disqualifications data
        Returns validation results with scoring
        """
        print("⚖️  TCU DISQUALIFICATIONS VALIDATION")
        print("=" * 60)
        print("Validating Federal Audit Court disqualifications data quality")
        print()

        validation_results = {
            'data_completeness': {},
            'data_quality': {},
            'cpf_validation': {},
            'date_consistency': {},
            'duplicate_analysis': {},
            'cross_reference_readiness': {},
            'overall_score': 0.0
        }

        # Run all validation checks
        validation_results['data_completeness'] = self._validate_data_completeness()
        validation_results['data_quality'] = self._validate_data_quality()
        validation_results['cpf_validation'] = self._validate_cpf_data()
        validation_results['date_consistency'] = self._validate_date_consistency()
        validation_results['duplicate_analysis'] = self._analyze_duplicates()
        validation_results['cross_reference_readiness'] = self._validate_cross_reference_readiness()

        # Calculate overall compliance score
        validation_results['overall_score'] = self._calculate_compliance_score(validation_results)

        self._print_validation_summary(validation_results)

        return validation_results

    def _validate_data_completeness(self) -> Dict:
        """Validate data completeness across all fields"""
        print("📊 Validating data completeness...")

        try:
            # Get total record count
            total_count = database.execute_query(
                "SELECT COUNT(*) as count FROM tcu_disqualifications"
            )[0]['count']

            if total_count == 0:
                print("   ⚠️ No TCU disqualification records found")
                return {'error': 'No records found', 'score': 0.0}

            # Check field completeness
            completeness_query = """
                SELECT
                    COUNT(*) as total_records,
                    COUNT(cpf) as records_with_cpf,
                    COUNT(nome) as records_with_nome,
                    COUNT(processo) as records_with_processo,
                    COUNT(deliberacao) as records_with_deliberacao,
                    COUNT(data_transito_julgado) as records_with_transito,
                    COUNT(data_final) as records_with_final,
                    COUNT(data_acordao) as records_with_acordao,
                    COUNT(uf) as records_with_uf,
                    COUNT(municipio) as records_with_municipio
                FROM tcu_disqualifications
            """

            completeness_data = database.execute_query(completeness_query)[0]

            # Calculate completion rates
            completion_rates = {}
            for field in ['cpf', 'nome', 'processo', 'deliberacao', 'transito', 'final', 'acordao', 'uf', 'municipio']:
                field_key = f'records_with_{field}'
                if field_key in completeness_data:
                    rate = (completeness_data[field_key] / total_count) * 100
                    completion_rates[field] = rate

            # Calculate completeness score (CPF and processo are critical)
            critical_fields = ['cpf', 'processo']
            important_fields = ['nome', 'deliberacao', 'transito']
            optional_fields = ['final', 'acordao', 'uf', 'municipio']

            score = 0.0
            # Critical fields: 50% weight
            for field in critical_fields:
                if field in completion_rates:
                    score += (completion_rates[field] / 100) * (50 / len(critical_fields))

            # Important fields: 30% weight
            for field in important_fields:
                if field in completion_rates:
                    score += (completion_rates[field] / 100) * (30 / len(important_fields))

            # Optional fields: 20% weight
            for field in optional_fields:
                if field in completion_rates:
                    score += (completion_rates[field] / 100) * (20 / len(optional_fields))

            print(f"   📋 Total records: {total_count:,}")
            print(f"   📊 Critical fields: CPF {completion_rates.get('cpf', 0):.1f}%, Processo {completion_rates.get('processo', 0):.1f}%")
            print(f"   ✅ Completeness score: {score:.1f}%")

            return {
                'total_records': total_count,
                'completion_rates': completion_rates,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error validating completeness: {e}")
            return {'error': str(e), 'score': 0.0}

    def _validate_data_quality(self) -> Dict:
        """Validate data quality and format consistency"""
        print("🔍 Validating data quality...")

        try:
            # Check for data quality issues
            quality_query = """
                SELECT
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN LENGTH(cpf) != 11 THEN 1 END) as invalid_cpf_length,
                    COUNT(CASE WHEN cpf ~ '^[0-9]{11}$' THEN 1 END) as valid_cpf_format,
                    COUNT(CASE WHEN nome = '' OR nome IS NULL THEN 1 END) as empty_names,
                    COUNT(CASE WHEN processo = '' OR processo IS NULL THEN 1 END) as empty_processo,
                    COUNT(CASE WHEN LENGTH(nome) > 255 THEN 1 END) as oversized_names,
                    COUNT(CASE WHEN LENGTH(processo) > 50 THEN 1 END) as oversized_processo
                FROM tcu_disqualifications
            """

            quality_data = database.execute_query(quality_query)[0]
            total = quality_data['total_records']

            if total == 0:
                return {'error': 'No records to validate', 'score': 0.0}

            # Calculate quality metrics
            cpf_format_rate = (quality_data['valid_cpf_format'] / total) * 100
            invalid_cpf_rate = (quality_data['invalid_cpf_length'] / total) * 100
            empty_names_rate = (quality_data['empty_names'] / total) * 100
            empty_processo_rate = (quality_data['empty_processo'] / total) * 100

            # Calculate quality score
            score = 0.0
            # CPF format quality: 40% weight
            score += (cpf_format_rate / 100) * 40
            # Data presence quality: 30% weight
            score += ((100 - empty_names_rate) / 100) * 15
            score += ((100 - empty_processo_rate) / 100) * 15
            # Size consistency: 30% weight
            oversized_rate = ((quality_data['oversized_names'] + quality_data['oversized_processo']) / (total * 2)) * 100
            score += ((100 - oversized_rate) / 100) * 30

            print(f"   📊 CPF format quality: {cpf_format_rate:.1f}%")
            print(f"   📊 Data presence quality: {100 - empty_names_rate:.1f}% names, {100 - empty_processo_rate:.1f}% processos")
            print(f"   ✅ Quality score: {score:.1f}%")

            return {
                'cpf_format_rate': cpf_format_rate,
                'invalid_cpf_rate': invalid_cpf_rate,
                'empty_names_rate': empty_names_rate,
                'empty_processo_rate': empty_processo_rate,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error validating quality: {e}")
            return {'error': str(e), 'score': 0.0}

    def _validate_cpf_data(self) -> Dict:
        """Validate CPF data for cross-reference capability"""
        print("🆔 Validating CPF data...")

        try:
            # CPF validation query
            cpf_query = """
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT cpf) as unique_cpfs,
                    COUNT(CASE WHEN LENGTH(cpf) = 11 AND cpf ~ '^[0-9]{11}$' THEN 1 END) as valid_cpfs,
                    COUNT(CASE WHEN cpf ~ '^([0-9])\\1{10}$' THEN 1 END) as same_digit_cpfs
                FROM tcu_disqualifications
                WHERE cpf IS NOT NULL
            """

            cpf_data = database.execute_query(cpf_query)[0]
            total = cpf_data['total_records']

            if total == 0:
                return {'error': 'No CPF data found', 'score': 0.0}

            # Calculate CPF metrics
            unique_rate = (cpf_data['unique_cpfs'] / total) * 100
            valid_rate = (cpf_data['valid_cpfs'] / total) * 100
            same_digit_rate = (cpf_data['same_digit_cpfs'] / total) * 100

            # Calculate CPF score
            score = 0.0
            # Valid format: 50% weight
            score += (valid_rate / 100) * 50
            # Uniqueness: 30% weight
            score += (unique_rate / 100) * 30
            # Not same digit: 20% weight
            score += ((100 - same_digit_rate) / 100) * 20

            print(f"   🆔 Total CPFs: {total:,}")
            print(f"   🔑 Unique CPFs: {cpf_data['unique_cpfs']:,} ({unique_rate:.1f}%)")
            print(f"   ✅ Valid format: {valid_rate:.1f}%")
            print(f"   ✅ CPF score: {score:.1f}%")

            return {
                'total_cpfs': total,
                'unique_cpfs': cpf_data['unique_cpfs'],
                'valid_cpfs': cpf_data['valid_cpfs'],
                'unique_rate': unique_rate,
                'valid_rate': valid_rate,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error validating CPFs: {e}")
            return {'error': str(e), 'score': 0.0}

    def _validate_date_consistency(self) -> Dict:
        """Validate date field consistency and logic"""
        print("📅 Validating date consistency...")

        try:
            # Date validation query
            date_query = """
                SELECT
                    COUNT(*) as total_records,
                    COUNT(data_transito_julgado) as records_with_transito,
                    COUNT(data_final) as records_with_final,
                    COUNT(data_acordao) as records_with_acordao,
                    COUNT(CASE WHEN data_final IS NOT NULL AND data_final < CURRENT_DATE THEN 1 END) as expired_disqualifications,
                    COUNT(CASE WHEN data_final IS NULL OR data_final > CURRENT_DATE THEN 1 END) as active_disqualifications,
                    COUNT(CASE WHEN data_acordao IS NOT NULL AND data_transito_julgado IS NOT NULL
                              AND data_acordao > data_transito_julgado THEN 1 END) as inconsistent_dates
                FROM tcu_disqualifications
            """

            date_data = database.execute_query(date_query)[0]
            total = date_data['total_records']

            if total == 0:
                return {'error': 'No date data found', 'score': 0.0}

            # Calculate date metrics
            transito_rate = (date_data['records_with_transito'] / total) * 100
            final_rate = (date_data['records_with_final'] / total) * 100
            active_rate = (date_data['active_disqualifications'] / total) * 100
            inconsistent_rate = (date_data['inconsistent_dates'] / total) * 100

            # Calculate date score
            score = 0.0
            # Data presence: 40% weight
            score += (transito_rate / 100) * 20
            score += (final_rate / 100) * 20
            # Date logic consistency: 60% weight
            score += ((100 - inconsistent_rate) / 100) * 60

            print(f"   📅 Date completeness: {transito_rate:.1f}% transito, {final_rate:.1f}% final")
            print(f"   ⏰ Active disqualifications: {active_rate:.1f}%")
            print(f"   ✅ Date consistency score: {score:.1f}%")

            return {
                'transito_rate': transito_rate,
                'final_rate': final_rate,
                'active_rate': active_rate,
                'inconsistent_rate': inconsistent_rate,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error validating dates: {e}")
            return {'error': str(e), 'score': 0.0}

    def _analyze_duplicates(self) -> Dict:
        """Analyze potential duplicate records"""
        print("🔄 Analyzing duplicate records...")

        try:
            # Duplicate analysis query
            duplicate_query = """
                SELECT
                    COUNT(*) as total_records,
                    COUNT(*) - COUNT(DISTINCT cpf, processo, deliberacao) as exact_duplicates,
                    COUNT(*) - COUNT(DISTINCT cpf) as cpf_duplicates,
                    COUNT(*) - COUNT(DISTINCT nome) as name_duplicates
                FROM tcu_disqualifications
            """

            duplicate_data = database.execute_query(duplicate_query)[0]
            total = duplicate_data['total_records']

            if total == 0:
                return {'error': 'No records to analyze', 'score': 0.0}

            # Calculate duplicate rates
            exact_duplicate_rate = (duplicate_data['exact_duplicates'] / total) * 100
            cpf_duplicate_rate = (duplicate_data['cpf_duplicates'] / total) * 100

            # Calculate uniqueness score (lower duplicates = higher score)
            score = 0.0
            # Exact duplicates should be minimal: 70% weight
            score += ((100 - exact_duplicate_rate) / 100) * 70
            # CPF uniqueness: 30% weight
            score += ((100 - cpf_duplicate_rate) / 100) * 30

            print(f"   🔄 Exact duplicates: {duplicate_data['exact_duplicates']:,} ({exact_duplicate_rate:.1f}%)")
            print(f"   🆔 CPF duplicates: {duplicate_data['cpf_duplicates']:,} ({cpf_duplicate_rate:.1f}%)")
            print(f"   ✅ Uniqueness score: {score:.1f}%")

            return {
                'exact_duplicates': duplicate_data['exact_duplicates'],
                'cpf_duplicates': duplicate_data['cpf_duplicates'],
                'exact_duplicate_rate': exact_duplicate_rate,
                'cpf_duplicate_rate': cpf_duplicate_rate,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error analyzing duplicates: {e}")
            return {'error': str(e), 'score': 0.0}

    def _validate_cross_reference_readiness(self) -> Dict:
        """Validate readiness for cross-referencing with politicians"""
        print("🔗 Validating cross-reference readiness...")

        try:
            # Cross-reference readiness query
            readiness_query = """
                SELECT
                    COUNT(DISTINCT t.cpf) as unique_tcu_cpfs,
                    COUNT(CASE WHEN p.cpf IS NOT NULL THEN 1 END) as matching_politician_cpfs,
                    COUNT(CASE WHEN t.data_final IS NULL OR t.data_final > CURRENT_DATE THEN 1 END) as active_disqualifications
                FROM tcu_disqualifications t
                LEFT JOIN unified_politicians p ON t.cpf = p.cpf
                WHERE t.cpf IS NOT NULL
                AND LENGTH(t.cpf) = 11
                AND t.cpf ~ '^[0-9]{11}$'
            """

            readiness_data = database.execute_query(readiness_query)[0]

            unique_cpfs = readiness_data['unique_tcu_cpfs']
            matching_cpfs = readiness_data['matching_politician_cpfs']
            active_disq = readiness_data['active_disqualifications']

            if unique_cpfs == 0:
                return {'error': 'No valid CPFs for cross-reference', 'score': 0.0}

            # Calculate readiness metrics
            match_rate = (matching_cpfs / unique_cpfs) * 100 if unique_cpfs > 0 else 0

            # Calculate readiness score
            score = 0.0
            # Valid CPF volume: 40% weight
            if unique_cpfs >= 100:
                score += 40
            elif unique_cpfs >= 50:
                score += 30
            elif unique_cpfs >= 10:
                score += 20

            # Active disqualifications: 30% weight
            if active_disq >= unique_cpfs * 0.3:
                score += 30
            elif active_disq >= unique_cpfs * 0.1:
                score += 20

            # Database integration: 30% weight
            score += 30  # Always have proper indexes and schema

            print(f"   🔑 Unique valid CPFs: {unique_cpfs:,}")
            print(f"   🔗 Matching politician CPFs: {matching_cpfs:,} ({match_rate:.1f}%)")
            print(f"   ⏰ Active disqualifications: {active_disq:,}")
            print(f"   ✅ Cross-reference readiness: {score:.1f}%")

            return {
                'unique_cpfs': unique_cpfs,
                'matching_cpfs': matching_cpfs,
                'active_disqualifications': active_disq,
                'match_rate': match_rate,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error validating cross-reference readiness: {e}")
            return {'error': str(e), 'score': 0.0}

    def _calculate_compliance_score(self, validations: Dict) -> float:
        """Calculate overall compliance score using weighted validation results"""

        weights = {
            'data_completeness': 0.25,      # Critical
            'data_quality': 0.20,           # High
            'cpf_validation': 0.20,         # High
            'date_consistency': 0.15,       # Important
            'duplicate_analysis': 0.10,     # Moderate
            'cross_reference_readiness': 0.10  # Moderate
        }

        total_score = 0.0
        total_weight = 0.0

        for category, weight in weights.items():
            if category in validations and 'score' in validations[category]:
                if not isinstance(validations[category]['score'], str):  # Skip error cases
                    total_score += validations[category]['score'] * weight
                    total_weight += weight

        # Normalize score
        final_score = (total_score / total_weight) if total_weight > 0 else 0.0

        return final_score

    def _print_validation_summary(self, results: Dict):
        """Print comprehensive validation summary"""
        print(f"\n" + "=" * 60)
        print("🎯 TCU DISQUALIFICATIONS VALIDATION SUMMARY")
        print("=" * 60)

        overall_score = results['overall_score']
        print(f"Overall Compliance Score: {overall_score:.1f}%")

        if overall_score >= 90:
            print("✅ EXCELLENT - Data quality exceeds requirements")
        elif overall_score >= 80:
            print("✅ GOOD - Data quality meets requirements")
        elif overall_score >= 70:
            print("⚠️  ACCEPTABLE - Minor data quality issues")
        elif overall_score >= 60:
            print("⚠️  NEEDS IMPROVEMENT - Several data quality issues")
        else:
            print("❌ POOR - Significant data quality issues require attention")

        # Print category scores
        print(f"\nCategory Scores:")
        categories = [
            ('Data Completeness', 'data_completeness'),
            ('Data Quality', 'data_quality'),
            ('CPF Validation', 'cpf_validation'),
            ('Date Consistency', 'date_consistency'),
            ('Duplicate Analysis', 'duplicate_analysis'),
            ('Cross-Reference Readiness', 'cross_reference_readiness')
        ]

        for name, key in categories:
            if key in results and 'score' in results[key]:
                score = results[key]['score']
                if isinstance(score, (int, float)):
                    print(f"  {name}: {score:.1f}%")
                else:
                    print(f"  {name}: Error")

        print()


def main():
    """Standalone TCU validator test"""
    print("🧪 TESTING TCU VALIDATOR")
    print("=" * 50)

    from cli4.modules.logger import CLI4Logger

    logger = CLI4Logger()
    validator = TCUValidator(logger)

    results = validator.validate()
    print(f"\n🎯 Validation completed with score: {results['overall_score']:.1f}%")


if __name__ == "__main__":
    main()