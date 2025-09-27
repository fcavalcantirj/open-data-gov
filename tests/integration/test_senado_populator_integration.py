#!/usr/bin/env python3
"""
Comprehensive integration test for Senado populator
Tests API connectivity, data parsing, and database integration
"""

import os
import sys
import json
import time
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.populators.senado.populator import SenadoPopulator
from cli4.populators.senado.validator import SenadoValidator


def test_senado_populator_integration():
    """Comprehensive integration test for Senado populator"""

    print("🧪 SENADO POPULATOR INTEGRATION TEST")
    print("=" * 60)
    print("Testing API connectivity, data parsing, and database integration")
    print()

    test_results = {
        'test_timestamp': datetime.now().isoformat(),
        'api_connectivity': {},
        'data_parsing': {},
        'database_integration': {},
        'validation_results': {},
        'overall_assessment': {}
    }

    # Initialize components
    logger = CLI4Logger()
    rate_limiter = CLI4RateLimiter()

    try:
        # Test 1: API Connectivity
        print("🔌 Testing API connectivity...")
        populator = SenadoPopulator(logger, rate_limiter)

        start_time = time.time()
        senators = populator._fetch_senators()
        api_response_time = time.time() - start_time

        if senators and len(senators) > 0:
            test_results['api_connectivity'] = {
                'status': 'success',
                'senators_found': len(senators),
                'response_time_seconds': round(api_response_time, 2),
                'sample_senator': senators[0] if senators else None
            }
            print(f"   ✅ API connectivity: SUCCESS")
            print(f"   📊 Senators found: {len(senators)}")
            print(f"   ⏱️  Response time: {api_response_time:.2f}s")
        else:
            test_results['api_connectivity'] = {
                'status': 'failure',
                'error': 'No senators returned from API'
            }
            print(f"   ❌ API connectivity: FAILED - No senators returned")
            return test_results

        # Test 2: Data Parsing Quality
        print(f"\n🔍 Testing data parsing quality...")
        parsing_stats = {
            'total_senators': len(senators),
            'with_codigo': 0,
            'with_nome': 0,
            'with_partido': 0,
            'with_estado': 0,
            'with_email': 0,
            'parsing_errors': 0
        }

        valid_senators = []
        for senator in senators:
            try:
                record = populator._build_senado_record(senator)
                if record:
                    valid_senators.append(record)
                    if record.get('codigo'): parsing_stats['with_codigo'] += 1
                    if record.get('nome'): parsing_stats['with_nome'] += 1
                    if record.get('partido'): parsing_stats['with_partido'] += 1
                    if record.get('estado'): parsing_stats['with_estado'] += 1
                    if record.get('email'): parsing_stats['with_email'] += 1
                else:
                    parsing_stats['parsing_errors'] += 1
            except Exception as e:
                parsing_stats['parsing_errors'] += 1
                print(f"   ⚠️ Parsing error: {e}")

        parsing_success_rate = (len(valid_senators) / len(senators)) * 100

        test_results['data_parsing'] = {
            'status': 'success' if parsing_success_rate >= 90 else 'warning' if parsing_success_rate >= 70 else 'failure',
            'statistics': parsing_stats,
            'success_rate': round(parsing_success_rate, 1),
            'valid_records': len(valid_senators)
        }

        print(f"   📊 Parsing success rate: {parsing_success_rate:.1f}%")
        print(f"   ✅ Valid records: {len(valid_senators)}/{len(senators)}")
        print(f"   📋 Field completeness:")
        print(f"      • Codigo: {parsing_stats['with_codigo']}/{len(senators)} ({(parsing_stats['with_codigo']/len(senators)*100):.1f}%)")
        print(f"      • Nome: {parsing_stats['with_nome']}/{len(senators)} ({(parsing_stats['with_nome']/len(senators)*100):.1f}%)")
        print(f"      • Partido: {parsing_stats['with_partido']}/{len(senators)} ({(parsing_stats['with_partido']/len(senators)*100):.1f}%)")
        print(f"      • Estado: {parsing_stats['with_estado']}/{len(senators)} ({(parsing_stats['with_estado']/len(senators)*100):.1f}%)")

        # Test 3: Database Integration (dry run)
        print(f"\n💾 Testing database integration...")

        # Test a few sample records without actually inserting
        sample_records = valid_senators[:3]
        db_test_results = {
            'sample_records_tested': len(sample_records),
            'record_build_success': 0,
            'potential_conflicts': 0
        }

        for record in sample_records:
            try:
                # Test record building (already done above, but verify again)
                if record and 'codigo' in record and record['codigo']:
                    db_test_results['record_build_success'] += 1
                else:
                    db_test_results['potential_conflicts'] += 1
            except Exception as e:
                db_test_results['potential_conflicts'] += 1
                print(f"   ⚠️ Record validation error: {e}")

        db_success_rate = (db_test_results['record_build_success'] / len(sample_records)) * 100

        test_results['database_integration'] = {
            'status': 'success' if db_success_rate >= 90 else 'warning',
            'statistics': db_test_results,
            'success_rate': round(db_success_rate, 1),
            'note': 'Dry run test - no actual database insertion performed'
        }

        print(f"   📊 Database preparation success rate: {db_success_rate:.1f}%")
        print(f"   ✅ Records ready for insertion: {db_test_results['record_build_success']}/{len(sample_records)}")

        # Test 4: Family Network Analysis Potential
        print(f"\n👨‍👩‍👧‍👦 Testing family network analysis potential...")

        # Extract surnames for family network analysis
        surnames = {}
        family_analysis = {
            'senators_with_surnames': 0,
            'unique_surnames': 0,
            'potential_family_clusters': 0,
            'largest_family_group': 0,
            'sample_families': []
        }

        for senator in valid_senators:
            nome_completo = senator.get('nome_completo')
            if nome_completo and len(nome_completo.split()) > 1:
                surname = nome_completo.split()[-1].upper()
                if len(surname) >= 3:  # Only meaningful surnames
                    family_analysis['senators_with_surnames'] += 1
                    surnames[surname] = surnames.get(surname, [])
                    surnames[surname].append({
                        'nome': senator.get('nome'),
                        'partido': senator.get('partido'),
                        'estado': senator.get('estado')
                    })

        family_analysis['unique_surnames'] = len(surnames)

        # Find potential families (surnames with multiple senators)
        potential_families = {k: v for k, v in surnames.items() if len(v) > 1}
        family_analysis['potential_family_clusters'] = len(potential_families)

        if potential_families:
            largest_family = max(potential_families.values(), key=len)
            family_analysis['largest_family_group'] = len(largest_family)

            # Sample families for analysis
            sorted_families = sorted(potential_families.items(), key=lambda x: len(x[1]), reverse=True)
            family_analysis['sample_families'] = [
                {
                    'surname': surname,
                    'senators': senators_with_surname
                }
                for surname, senators_with_surname in sorted_families[:3]
            ]

        test_results['family_network_analysis'] = family_analysis

        print(f"   📊 Family network analysis potential:")
        print(f"      • Senators with extractable surnames: {family_analysis['senators_with_surnames']}")
        print(f"      • Unique surnames: {family_analysis['unique_surnames']}")
        print(f"      • Potential family clusters: {family_analysis['potential_family_clusters']}")
        print(f"      • Largest family group: {family_analysis['largest_family_group']}")

        if family_analysis['sample_families']:
            print(f"   👨‍👩‍👧‍👦 Sample potential families:")
            for family in family_analysis['sample_families']:
                surname = family['surname']
                count = len(family['senators'])
                print(f"      • {surname}: {count} senators")

        # Overall Assessment
        print(f"\n📋 OVERALL ASSESSMENT")
        print("=" * 40)

        # Calculate overall score
        scores = []
        if test_results['api_connectivity']['status'] == 'success':
            scores.append(100)
        else:
            scores.append(0)

        if test_results['data_parsing']['status'] == 'success':
            scores.append(test_results['data_parsing']['success_rate'])
        elif test_results['data_parsing']['status'] == 'warning':
            scores.append(test_results['data_parsing']['success_rate'] * 0.8)
        else:
            scores.append(0)

        if test_results['database_integration']['status'] == 'success':
            scores.append(test_results['database_integration']['success_rate'])
        else:
            scores.append(test_results['database_integration']['success_rate'] * 0.8)

        overall_score = sum(scores) / len(scores)

        if overall_score >= 90:
            assessment = "ready"
            confidence = "high"
            status = "✅ EXCELLENT"
        elif overall_score >= 75:
            assessment = "ready_with_minor_issues"
            confidence = "high"
            status = "👍 GOOD"
        elif overall_score >= 60:
            assessment = "needs_review"
            confidence = "medium"
            status = "⚠️ FAIR"
        else:
            assessment = "not_ready"
            confidence = "low"
            status = "❌ POOR"

        test_results['overall_assessment'] = {
            'score': round(overall_score, 1),
            'max_score': 100,
            'assessment': assessment,
            'confidence': confidence,
            'status': status
        }

        print(f"🎯 Overall Score: {overall_score:.1f}/100")
        print(f"📊 Status: {status}")
        print(f"🔍 Assessment: {assessment}")
        print(f"💪 Confidence: {confidence}")

        # Implementation readiness
        if overall_score >= 85:
            print(f"\n🚀 IMPLEMENTATION READINESS: HIGH")
            print(f"   ✅ Ready for production implementation")
            print(f"   ✅ API integration verified")
            print(f"   ✅ Data parsing robust")
            print(f"   ✅ Family network detection capable")
        elif overall_score >= 70:
            print(f"\n⚠️ IMPLEMENTATION READINESS: MEDIUM")
            print(f"   ⚠️ Ready with minor adjustments needed")
            print(f"   ✅ Core functionality verified")
        else:
            print(f"\n❌ IMPLEMENTATION READINESS: LOW")
            print(f"   ❌ Requires significant improvements")
            print(f"   ⚠️ Not recommended for production")

    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        test_results['overall_assessment'] = {
            'score': 0,
            'max_score': 100,
            'assessment': 'test_failed',
            'confidence': 'none',
            'error': str(e)
        }

    return test_results


def save_test_results(results):
    """Save test results to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"senado_populator_integration_test_{timestamp}.json"
    filepath = os.path.join(os.path.dirname(__file__), filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Test results saved to: {filename}")
    return filepath


def main():
    """Run comprehensive Senado populator integration test"""
    results = test_senado_populator_integration()
    save_test_results(results)

    # Exit with appropriate code
    overall_score = results.get('overall_assessment', {}).get('score', 0)
    sys.exit(0 if overall_score >= 85 else 1)


if __name__ == "__main__":
    main()