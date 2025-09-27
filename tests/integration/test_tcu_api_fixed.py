#!/usr/bin/env python3
"""
Fixed TCU API Integration Test - Handles correct API response format
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import re

def test_tcu_api_comprehensive():
    """Comprehensive TCU API test with correct response format handling"""

    print("🧪 FIXED TCU API INTEGRATION TEST")
    print("=" * 60)

    results = {
        'api_status': 'unknown',
        'data_structure': {},
        'disqualifications_analysis': {},
        'cpf_cross_reference': {},
        'implementation_assessment': {}
    }

    # Test TCU Disqualifications API
    print("🔍 Testing TCU Disqualifications API...")

    try:
        url = "https://contas.tcu.gov.br/ords/condenacao/consulta/inabilitados"
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            print(f"   ❌ API returned status {response.status_code}")
            results['api_status'] = 'failed'
            return results

        data = response.json()
        results['api_status'] = 'success'

        print(f"   ✅ API accessible, status 200")
        print(f"   📊 Response structure: {type(data).__name__}")

        # Parse the correct structure
        if 'items' in data:
            items = data['items']
            has_more = data.get('hasMore', False)
            total_count = data.get('count', len(items))
            limit = data.get('limit', 25)
            offset = data.get('offset', 0)

            print(f"   📋 Found {len(items)} disqualification records")
            print(f"   📄 Pagination: limit={limit}, offset={offset}, hasMore={has_more}")

            results['data_structure'] = {
                'format': 'oracle_rest_api',
                'items_count': len(items),
                'has_pagination': has_more,
                'limit': limit,
                'offset': offset,
                'sample_fields': list(items[0].keys()) if items else []
            }

            # Analyze disqualifications data
            if items:
                sample_record = items[0]
                print(f"   🔍 Sample record fields: {list(sample_record.keys())}")

                # CPF Analysis
                cpf_analysis = {
                    'total_records': len(items),
                    'records_with_cpf': 0,
                    'valid_cpf_format': 0,
                    'cpf_samples': [],
                    'names_samples': []
                }

                for record in items[:10]:  # Analyze first 10 records
                    if 'cpf' in record and record['cpf']:
                        cpf_analysis['records_with_cpf'] += 1
                        cpf_raw = str(record['cpf'])
                        cpf_clean = re.sub(r'[^0-9]', '', cpf_raw)

                        if len(cpf_clean) == 11:
                            cpf_analysis['valid_cpf_format'] += 1

                        cpf_analysis['cpf_samples'].append({
                            'cpf_raw': cpf_raw,
                            'cpf_clean': cpf_clean,
                            'nome': record.get('nome', 'N/A'),
                            'processo': record.get('processo', 'N/A')
                        })

                        cpf_analysis['names_samples'].append(record.get('nome', 'N/A'))

                cpf_quality = cpf_analysis['valid_cpf_format'] / cpf_analysis['records_with_cpf'] if cpf_analysis['records_with_cpf'] > 0 else 0

                print(f"   📊 CPF Quality: {cpf_analysis['valid_cpf_format']}/{cpf_analysis['records_with_cpf']} ({cpf_quality:.1%} valid)")

                results['disqualifications_analysis'] = cpf_analysis

                # Show some sample names for manual verification
                print(f"   👥 Sample disqualified persons:")
                for sample in cpf_analysis['cpf_samples'][:5]:
                    print(f"      • {sample['nome']} (CPF: {sample['cpf_clean']}) - {sample['processo']}")

                # Test cross-reference potential with known politician CPFs
                test_cpfs = [
                    "67821090425",  # Arthur Lira
                    # Add more politician CPFs from database if available
                ]

                matches_found = []
                for record in items:
                    if 'cpf' in record and record['cpf']:
                        cpf_clean = re.sub(r'[^0-9]', '', str(record['cpf']))
                        if cpf_clean in test_cpfs:
                            matches_found.append({
                                'cpf': cpf_clean,
                                'nome': record.get('nome', 'N/A'),
                                'processo': record.get('processo', 'N/A'),
                                'data_final': record.get('data_final', 'N/A')
                            })

                results['cpf_cross_reference'] = {
                    'test_cpfs_checked': len(test_cpfs),
                    'matches_found': len(matches_found),
                    'match_details': matches_found
                }

                if matches_found:
                    print(f"   🚨 MATCHES FOUND: {len(matches_found)} politician(s) with TCU disqualifications!")
                    for match in matches_found:
                        print(f"      ⚠️  {match['nome']} (CPF: {match['cpf']}) - {match['processo']}")
                else:
                    print(f"   ✅ No matches found with test politician CPFs")

        # Implementation Assessment
        implementation_score = 0

        if results['api_status'] == 'success':
            implementation_score += 3

        if results['disqualifications_analysis'].get('valid_cpf_format', 0) > 0:
            implementation_score += 2

        if results['data_structure'].get('items_count', 0) > 10:
            implementation_score += 2

        if cpf_quality > 0.8:
            implementation_score += 3

        if implementation_score >= 8:
            assessment = 'ready'
        elif implementation_score >= 5:
            assessment = 'mostly_ready'
        else:
            assessment = 'needs_work'

        results['implementation_assessment'] = {
            'score': implementation_score,
            'max_score': 10,
            'assessment': assessment,
            'confidence': 'high' if implementation_score >= 8 else 'medium' if implementation_score >= 5 else 'low'
        }

        print(f"\\n🎯 IMPLEMENTATION ASSESSMENT:")
        print(f"   Score: {implementation_score}/10")
        print(f"   Assessment: {assessment}")
        print(f"   Confidence: {results['implementation_assessment']['confidence']}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        results['api_status'] = 'error'
        results['error'] = str(e)

    return results

def main():
    """Run the fixed TCU API test"""

    results = test_tcu_api_comprehensive()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/fcavalcanti/dev/open-data-gov/tests/integration/tcu_fixed_test_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\\n📄 Results saved to: {output_file}")

    # Final recommendation
    assessment = results.get('implementation_assessment', {})
    print(f"\\n" + "=" * 60)
    print(f"🎯 FINAL TCU POPULATOR RECOMMENDATION")
    print(f"=" * 60)

    if assessment.get('assessment') == 'ready':
        print(f"✅ READY FOR IMPLEMENTATION")
        print(f"   • API is reliable and returns structured data")
        print(f"   • CPF data quality is sufficient for cross-referencing")
        print(f"   • Pagination is available for complete data fetching")
        print(f"   • Implementation effort: LOW")
    elif assessment.get('assessment') == 'mostly_ready':
        print(f"⚠️  MOSTLY READY - Minor issues to address")
        print(f"   • Implementation effort: MEDIUM")
    else:
        print(f"❌ NEEDS WORK - Significant issues detected")
        print(f"   • Implementation effort: HIGH")

    return results

if __name__ == "__main__":
    main()