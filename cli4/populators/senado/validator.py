"""
CLI4 Senado Politicians Validator
Validates senado_politicians table data quality and completeness
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from cli4.modules import database
from cli4.modules.logger import CLI4Logger


class SenadoValidator:
    """Validate Senado politicians data quality and integrity"""

    def __init__(self, logger: CLI4Logger):
        self.logger = logger

    def validate_all_senado(self, limit: Optional[int] = None) -> Dict:
        """
        Comprehensive validation of Senado politicians data
        Returns validation results with scoring
        """
        print("🏛️  SENADO POLITICIANS VALIDATION")
        print("=" * 60)
        print("Validating Senate Federal politicians data quality")
        print()

        validation_results = {
            'data_completeness': {},
            'data_quality': {},
            'party_validation': {},
            'state_validation': {},
            'duplicate_analysis': {},
            'family_network_readiness': {},
            'compliance_score': 0.0
        }

        # Run all validation checks
        validation_results['data_completeness'] = self._validate_data_completeness()
        validation_results['data_quality'] = self._validate_data_quality()
        validation_results['party_validation'] = self._validate_party_data()
        validation_results['state_validation'] = self._validate_state_data()
        validation_results['duplicate_analysis'] = self._analyze_duplicates()
        validation_results['family_network_readiness'] = self._validate_family_network_readiness()

        # Calculate overall compliance score
        validation_results['compliance_score'] = self._calculate_compliance_score(validation_results)

        self._print_validation_summary(validation_results)

        return validation_results

    def _validate_data_completeness(self) -> Dict:
        """Validate data completeness across all fields"""
        print("📊 Validating data completeness...")

        try:
            # Get total record count
            total_count = database.execute_query(
                "SELECT COUNT(*) as count FROM senado_politicians"
            )[0]['count']

            if total_count == 0:
                print("   ⚠️ No Senado politician records found")
                return {'error': 'No records found', 'score': 0.0}

            # Check field completeness
            completeness_query = """
                SELECT
                    COUNT(*) as total_records,
                    COUNT(codigo) as records_with_codigo,
                    COUNT(codigo_publico) as records_with_codigo_publico,
                    COUNT(nome) as records_with_nome,
                    COUNT(nome_completo) as records_with_nome_completo,
                    COUNT(sexo) as records_with_sexo,
                    COUNT(partido) as records_with_partido,
                    COUNT(estado) as records_with_estado,
                    COUNT(email) as records_with_email,
                    COUNT(foto_url) as records_with_foto_url,
                    COUNT(pagina_url) as records_with_pagina_url,
                    COUNT(bloco) as records_with_bloco
                FROM senado_politicians
            """

            completeness_data = database.execute_query(completeness_query)[0]

            # Calculate completion rates
            completion_rates = {}
            for field in ['codigo', 'codigo_publico', 'nome', 'nome_completo', 'sexo',
                         'partido', 'estado', 'email', 'foto_url', 'pagina_url', 'bloco']:
                field_key = f'records_with_{field}'
                if field_key in completeness_data:
                    rate = (completeness_data[field_key] / total_count) * 100
                    completion_rates[field] = rate

            # Calculate completeness score (codigo, nome, partido, estado are critical)
            critical_fields = ['codigo', 'nome', 'partido', 'estado']
            important_fields = ['nome_completo', 'sexo']
            optional_fields = ['codigo_publico', 'email', 'foto_url', 'pagina_url', 'bloco']

            score = 0.0
            # Critical fields: 60% weight
            for field in critical_fields:
                if field in completion_rates:
                    score += (completion_rates[field] / 100) * (60 / len(critical_fields))

            # Important fields: 30% weight
            for field in important_fields:
                if field in completion_rates:
                    score += (completion_rates[field] / 100) * (30 / len(important_fields))

            # Optional fields: 10% weight
            for field in optional_fields:
                if field in completion_rates:
                    score += (completion_rates[field] / 100) * (10 / len(optional_fields))

            print(f"   📊 Total senators: {total_count:,}")
            print(f"   📈 Critical field completeness:")
            for field in critical_fields:
                if field in completion_rates:
                    rate = completion_rates[field]
                    status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                    print(f"      {status} {field}: {rate:.1f}%")

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
            # Check for malformed or suspicious data
            quality_query = """
                SELECT
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN LENGTH(nome) < 3 THEN 1 END) as short_names,
                    COUNT(CASE WHEN nome ~ '^[A-ZÁÊÔÇ\\s]+$' THEN 1 END) as valid_name_format,
                    COUNT(CASE WHEN email LIKE '%@%.%' THEN 1 END) as valid_emails,
                    COUNT(CASE WHEN LENGTH(partido) BETWEEN 2 AND 20 THEN 1 END) as valid_parties,
                    COUNT(CASE WHEN LENGTH(estado) = 2 THEN 1 END) as valid_states,
                    COUNT(CASE WHEN foto_url LIKE 'http%' THEN 1 END) as valid_foto_urls,
                    COUNT(CASE WHEN pagina_url LIKE 'http%' THEN 1 END) as valid_pagina_urls
                FROM senado_politicians
                WHERE codigo IS NOT NULL
            """

            quality_data = database.execute_query(quality_query)[0]
            total = quality_data['total_records']

            if total == 0:
                return {'error': 'No records to validate', 'score': 0.0}

            # Calculate quality metrics
            quality_metrics = {
                'valid_names': (quality_data['valid_name_format'] / total) * 100,
                'no_short_names': ((total - quality_data['short_names']) / total) * 100,
                'valid_emails': (quality_data['valid_emails'] / max(1, quality_data.get('valid_emails', 0) + (total - quality_data.get('valid_emails', 0)))) * 100,
                'valid_parties': (quality_data['valid_parties'] / total) * 100,
                'valid_states': (quality_data['valid_states'] / total) * 100,
                'valid_foto_urls': (quality_data['valid_foto_urls'] / max(1, quality_data.get('valid_foto_urls', 0) + (total - quality_data.get('valid_foto_urls', 0)))) * 100,
                'valid_pagina_urls': (quality_data['valid_pagina_urls'] / max(1, quality_data.get('valid_pagina_urls', 0) + (total - quality_data.get('valid_pagina_urls', 0)))) * 100
            }

            # Calculate quality score
            score = (
                quality_metrics['valid_names'] * 0.25 +
                quality_metrics['no_short_names'] * 0.20 +
                quality_metrics['valid_parties'] * 0.20 +
                quality_metrics['valid_states'] * 0.20 +
                quality_metrics['valid_emails'] * 0.15
            ) / 100

            print(f"   📈 Data quality metrics:")
            print(f"      ✅ Valid name formats: {quality_metrics['valid_names']:.1f}%")
            print(f"      ✅ No suspiciously short names: {quality_metrics['no_short_names']:.1f}%")
            print(f"      ✅ Valid party codes: {quality_metrics['valid_parties']:.1f}%")
            print(f"      ✅ Valid state codes: {quality_metrics['valid_states']:.1f}%")

            return {
                'quality_metrics': quality_metrics,
                'score': score * 100
            }

        except Exception as e:
            print(f"   ❌ Error validating data quality: {e}")
            return {'error': str(e), 'score': 0.0}

    def _validate_party_data(self) -> Dict:
        """Validate party distribution and consistency"""
        print("🏛️  Validating party data...")

        try:
            # Party distribution analysis
            party_query = """
                SELECT
                    partido,
                    COUNT(*) as senator_count,
                    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
                FROM senado_politicians
                WHERE partido IS NOT NULL
                GROUP BY partido
                ORDER BY senator_count DESC
            """

            party_data = database.execute_query(party_query)

            # Validate party codes (should be standard Brazilian party abbreviations)
            valid_parties = [
                'PT', 'PSB', 'MDB', 'PSD', 'PP', 'PDT', 'PSDB', 'PL', 'REPUBLICANOS',
                'UNIÃO', 'PODEMOS', 'PSL', 'PTB', 'PCdoB', 'CIDADANIA', 'NOVO',
                'PV', 'REDE', 'SOLIDARIEDADE', 'PROS', 'AVANTE', 'PATRIOTA'
            ]

            invalid_parties = [p for p in party_data if p['partido'] not in valid_parties]
            valid_party_rate = ((len(party_data) - len(invalid_parties)) / max(1, len(party_data))) * 100

            # Check for reasonable distribution (no party should have > 50% of senators)
            max_party_percentage = max([p['percentage'] for p in party_data]) if party_data else 0
            distribution_score = 100 if max_party_percentage <= 50 else max(0, 100 - (max_party_percentage - 50) * 2)

            score = (valid_party_rate * 0.7 + distribution_score * 0.3)

            print(f"   📊 Party analysis:")
            print(f"      • Total parties: {len(party_data)}")
            print(f"      • Valid party codes: {valid_party_rate:.1f}%")
            print(f"      • Max party concentration: {max_party_percentage:.1f}%")

            if party_data:
                print(f"   🏛️  Top parties:")
                for party in party_data[:5]:
                    print(f"      • {party['partido']}: {party['senator_count']} ({party['percentage']:.1f}%)")

            return {
                'party_distribution': party_data,
                'valid_party_rate': valid_party_rate,
                'max_concentration': max_party_percentage,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error validating party data: {e}")
            return {'error': str(e), 'score': 0.0}

    def _validate_state_data(self) -> Dict:
        """Validate state distribution"""
        print("🗺️  Validating state data...")

        try:
            # State distribution analysis
            state_query = """
                SELECT
                    estado,
                    COUNT(*) as senator_count
                FROM senado_politicians
                WHERE estado IS NOT NULL
                GROUP BY estado
                ORDER BY senator_count DESC
            """

            state_data = database.execute_query(state_query)

            # Brazil has 26 states + DF = 27 electoral units, each should have 3 senators = 81 total
            expected_states = 27
            expected_total_senators = 81

            # Validate state codes (should be 2-letter Brazilian state codes)
            valid_states = [
                'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
                'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
                'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
            ]

            invalid_states = [s for s in state_data if s['estado'] not in valid_states]
            valid_state_rate = ((len(state_data) - len(invalid_states)) / max(1, len(state_data))) * 100

            # Check if each state has approximately 3 senators
            total_senators = sum([s['senator_count'] for s in state_data])
            avg_senators_per_state = total_senators / len(state_data) if state_data else 0
            distribution_score = max(0, 100 - abs(avg_senators_per_state - 3) * 20)

            score = (valid_state_rate * 0.6 + distribution_score * 0.4)

            print(f"   📊 State analysis:")
            print(f"      • Total states represented: {len(state_data)}/{expected_states}")
            print(f"      • Valid state codes: {valid_state_rate:.1f}%")
            print(f"      • Total senators: {total_senators}")
            print(f"      • Average senators per state: {avg_senators_per_state:.1f}")

            return {
                'state_distribution': state_data,
                'valid_state_rate': valid_state_rate,
                'states_represented': len(state_data),
                'total_senators': total_senators,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error validating state data: {e}")
            return {'error': str(e), 'score': 0.0}

    def _analyze_duplicates(self) -> Dict:
        """Analyze potential duplicates"""
        print("🔍 Analyzing duplicate records...")

        try:
            # Check for duplicate codes (primary concern)
            duplicate_codes_query = """
                SELECT codigo, COUNT(*) as count
                FROM senado_politicians
                WHERE codigo IS NOT NULL
                GROUP BY codigo
                HAVING COUNT(*) > 1
            """

            duplicate_codes = database.execute_query(duplicate_codes_query)

            # Check for similar names (potential duplicates)
            similar_names_query = """
                SELECT nome_completo, COUNT(*) as count
                FROM senado_politicians
                WHERE nome_completo IS NOT NULL
                GROUP BY nome_completo
                HAVING COUNT(*) > 1
            """

            similar_names = database.execute_query(similar_names_query)

            # Calculate duplicate rate
            total_records = database.execute_query("SELECT COUNT(*) as count FROM senado_politicians")[0]['count']

            duplicate_rate = (len(duplicate_codes) / max(1, total_records)) * 100
            score = max(0, 100 - duplicate_rate * 10)  # Heavy penalty for duplicates

            print(f"   📊 Duplicate analysis:")
            print(f"      • Duplicate codes: {len(duplicate_codes)}")
            print(f"      • Similar names: {len(similar_names)}")
            print(f"      • Duplicate rate: {duplicate_rate:.2f}%")

            if duplicate_codes:
                print(f"   ⚠️  Found duplicate codes:")
                for dup in duplicate_codes[:5]:
                    print(f"      • Code {dup['codigo']}: {dup['count']} records")

            return {
                'duplicate_codes': len(duplicate_codes),
                'similar_names': len(similar_names),
                'duplicate_rate': duplicate_rate,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error analyzing duplicates: {e}")
            return {'error': str(e), 'score': 0.0}

    def _validate_family_network_readiness(self) -> Dict:
        """Validate readiness for family network detection"""
        print("👨‍👩‍👧‍👦 Validating family network detection readiness...")

        try:
            # Extract surnames from names for family network analysis
            surname_query = """
                SELECT
                    nome_completo,
                    partido,
                    estado,
                    UPPER(TRIM(SPLIT_PART(nome_completo, ' ', -1))) as surname
                FROM senado_politicians
                WHERE nome_completo IS NOT NULL
                AND LENGTH(nome_completo) > 5
            """

            try:
                surname_data = database.execute_query(surname_query)
            except:
                # Fallback for PostgreSQL without SPLIT_PART
                surname_fallback_query = """
                    SELECT
                        nome_completo,
                        partido,
                        estado,
                        UPPER(TRIM(REGEXP_REPLACE(nome_completo, '.* ', ''))) as surname
                    FROM senado_politicians
                    WHERE nome_completo IS NOT NULL
                    AND LENGTH(nome_completo) > 5
                """
                surname_data = database.execute_query(surname_fallback_query)

            # Count surname frequency
            surname_counts = {}
            for record in surname_data:
                surname = record['surname']
                if len(surname) >= 3:  # Only meaningful surnames
                    surname_counts[surname] = surname_counts.get(surname, 0) + 1

            # Identify potential family networks (same surname, different first names)
            potential_families = {k: v for k, v in surname_counts.items() if v > 1}

            # Calculate readiness score
            total_senators = len(surname_data)
            senators_with_extractable_surnames = len([s for s in surname_data if len(s['surname']) >= 3])

            readiness_rate = (senators_with_extractable_surnames / max(1, total_senators)) * 100
            score = readiness_rate

            print(f"   📊 Family network readiness:")
            print(f"      • Senators with extractable surnames: {senators_with_extractable_surnames}/{total_senators}")
            print(f"      • Surname extraction rate: {readiness_rate:.1f}%")
            print(f"      • Potential family clusters: {len(potential_families)}")

            if potential_families:
                print(f"   👨‍👩‍👧‍👦 Top potential family surnames:")
                sorted_families = sorted(potential_families.items(), key=lambda x: x[1], reverse=True)
                for surname, count in sorted_families[:5]:
                    print(f"      • {surname}: {count} senators")

            return {
                'extractable_surnames': senators_with_extractable_surnames,
                'total_analyzed': total_senators,
                'readiness_rate': readiness_rate,
                'potential_families': len(potential_families),
                'family_clusters': potential_families,
                'score': score
            }

        except Exception as e:
            print(f"   ❌ Error validating family network readiness: {e}")
            return {'error': str(e), 'score': 0.0}

    def _calculate_compliance_score(self, validations: Dict) -> float:
        """Calculate overall compliance score from all validations"""
        try:
            weights = {
                'data_completeness': 0.30,
                'data_quality': 0.25,
                'party_validation': 0.15,
                'state_validation': 0.15,
                'duplicate_analysis': 0.10,
                'family_network_readiness': 0.05
            }

            total_score = 0.0
            total_weight = 0.0

            for category, weight in weights.items():
                if category in validations and 'score' in validations[category]:
                    score = validations[category]['score']
                    if isinstance(score, (int, float)) and score >= 0:
                        total_score += score * weight
                        total_weight += weight

            return total_score / total_weight if total_weight > 0 else 0.0

        except Exception as e:
            print(f"   ❌ Error calculating compliance score: {e}")
            return 0.0

    def _print_validation_summary(self, validation_results: Dict):
        """Print comprehensive validation summary"""
        print(f"\n📋 SENADO VALIDATION SUMMARY")
        print("=" * 60)

        score = validation_results.get('compliance_score', 0)
        print(f"🎯 Overall Compliance Score: {score:.1f}/100")

        # Determine status
        if score >= 90:
            status = "🏆 EXCELLENT"
            status_desc = "Ready for family network analysis"
        elif score >= 70:
            status = "👍 GOOD"
            status_desc = "Minor issues, suitable for analysis"
        elif score >= 50:
            status = "⚠️  FAIR"
            status_desc = "Needs improvement before analysis"
        else:
            status = "❌ POOR"
            status_desc = "Significant data quality issues"

        print(f"📊 Status: {status}")
        print(f"💡 Assessment: {status_desc}")
        print()

        # Print category scores
        categories = [
            ('data_completeness', 'Data Completeness', '📊'),
            ('data_quality', 'Data Quality', '🔍'),
            ('party_validation', 'Party Validation', '🏛️'),
            ('state_validation', 'State Validation', '🗺️'),
            ('duplicate_analysis', 'Duplicate Analysis', '🔍'),
            ('family_network_readiness', 'Family Network Readiness', '👨‍👩‍👧‍👦')
        ]

        for category, name, emoji in categories:
            if category in validation_results and 'score' in validation_results[category]:
                cat_score = validation_results[category]['score']
                print(f"{emoji} {name}: {cat_score:.1f}/100")

        print(f"\n✅ Senado validation completed")


def main():
    """Standalone test of Senado validator"""
    print("🧪 TESTING SENADO VALIDATOR")
    print("=" * 50)

    from cli4.modules.logger import CLI4Logger

    logger = CLI4Logger()
    validator = SenadoValidator(logger)

    # Test validation
    result = validator.validate_all_senado()
    print(f"\n🎯 Validation completed with score: {result.get('compliance_score', 0):.1f}/100")


if __name__ == "__main__":
    main()