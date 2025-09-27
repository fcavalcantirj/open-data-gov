#!/usr/bin/env python3
"""
Comprehensive TCU API Integration Test
Tests all aspects needed for TCU disqualifications populator implementation
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import re

class TCUAPITester:
    """Comprehensive TCU API testing for populator implementation"""

    def __init__(self):
        self.base_url = "https://contas.tcu.gov.br/ords/"
        self.endpoints = {
            'disqualifications': 'condenacao/consulta/inabilitados',
            'congress_requests': 'api/publica/scn/pedidos_congresso'
        }
        self.test_results = {
            'api_connectivity': {},
            'data_structure': {},
            'data_volume': {},
            'data_quality': {},
            'rate_limiting': {},
            'cpf_analysis': {},
            'implementation_readiness': {}
        }

    def test_api_connectivity(self) -> Dict:
        """Test all TCU API endpoints for reliability"""
        print("🔗 Testing TCU API Connectivity...")

        connectivity_results = {}

        for endpoint_name, endpoint_path in self.endpoints.items():
            url = f"{self.base_url}{endpoint_path}"

            try:
                start_time = time.time()
                response = requests.get(url, timeout=30)
                response_time = time.time() - start_time

                connectivity_results[endpoint_name] = {
                    'url': url,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200,
                    'content_length': len(response.content) if response.status_code == 200 else 0
                }

                if response.status_code == 200:
                    print(f"   ✅ {endpoint_name}: {response.status_code} ({response_time:.2f}s)")
                else:
                    print(f"   ❌ {endpoint_name}: {response.status_code}")

            except Exception as e:
                connectivity_results[endpoint_name] = {
                    'url': url,
                    'error': str(e),
                    'success': False
                }
                print(f"   ❌ {endpoint_name}: Error - {e}")

        self.test_results['api_connectivity'] = connectivity_results
        return connectivity_results

    def test_disqualifications_data_structure(self) -> Dict:
        """Test TCU disqualifications data structure for database compatibility"""
        print("📊 Testing TCU Disqualifications Data Structure...")

        try:
            url = f"{self.base_url}{self.endpoints['disqualifications']}"
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                return {'error': f'API returned status {response.status_code}'}

            data = response.json()

            # Analyze data structure
            structure_analysis = {
                'response_type': type(data).__name__,
                'total_records': len(data) if isinstance(data, list) else 0,
                'sample_record': None,
                'field_analysis': {},
                'cpf_format_analysis': {},
                'date_format_analysis': {}
            }

            if isinstance(data, list) and len(data) > 0:
                sample_record = data[0]
                structure_analysis['sample_record'] = sample_record

                # Analyze each field
                for field, value in sample_record.items():
                    structure_analysis['field_analysis'][field] = {
                        'type': type(value).__name__,
                        'sample_value': str(value)[:100] if value else None,
                        'is_null': value is None
                    }

                # Analyze CPF format across all records
                cpf_patterns = {}
                date_patterns = {}

                for record in data[:50]:  # Sample first 50 records
                    # CPF analysis
                    if 'cpf' in record and record['cpf']:
                        cpf = str(record['cpf'])
                        cpf_clean = re.sub(r'[^0-9]', '', cpf)
                        cpf_length = len(cpf_clean)

                        if cpf_length not in cpf_patterns:
                            cpf_patterns[cpf_length] = 0
                        cpf_patterns[cpf_length] += 1

                    # Date analysis
                    for field in ['data_transito_julgado', 'data_final', 'data_acordao']:
                        if field in record and record[field]:
                            date_str = str(record[field])
                            if date_str not in date_patterns:
                                date_patterns[date_str[:10]] = 0
                            date_patterns[date_str[:10]] += 1

                structure_analysis['cpf_format_analysis'] = cpf_patterns
                structure_analysis['date_format_analysis'] = dict(list(date_patterns.items())[:10])

                print(f"   📋 Found {len(data)} disqualification records")
                print(f"   📏 CPF lengths: {cpf_patterns}")
                print(f"   📅 Date formats sample: {list(date_patterns.keys())[:5]}")

            self.test_results['data_structure'] = structure_analysis
            return structure_analysis

        except Exception as e:
            error_result = {'error': str(e)}
            self.test_results['data_structure'] = error_result
            return error_result

    def test_data_volume_and_pagination(self) -> Dict:
        """Test data volume and pagination strategy"""
        print("📈 Testing TCU Data Volume and Pagination...")

        try:
            url = f"{self.base_url}{self.endpoints['disqualifications']}"
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                return {'error': f'API returned status {response.status_code}'}

            data = response.json()

            volume_analysis = {
                'total_records': len(data) if isinstance(data, list) else 0,
                'response_size_bytes': len(response.content),
                'estimated_full_size': len(response.content),
                'pagination_needed': False,
                'recommendation': 'single_request'
            }

            if isinstance(data, list):
                total_records = len(data)

                if total_records > 1000:
                    volume_analysis['pagination_needed'] = True
                    volume_analysis['recommendation'] = 'implement_pagination'
                elif total_records > 500:
                    volume_analysis['recommendation'] = 'monitor_size'
                else:
                    volume_analysis['recommendation'] = 'single_request_ok'

                print(f"   📊 Total records: {total_records}")
                print(f"   💾 Response size: {len(response.content):,} bytes")
                print(f"   🎯 Recommendation: {volume_analysis['recommendation']}")

            self.test_results['data_volume'] = volume_analysis
            return volume_analysis

        except Exception as e:
            error_result = {'error': str(e)}
            self.test_results['data_volume'] = error_result
            return error_result

    def test_cpf_cross_reference_potential(self) -> Dict:
        """Test CPF cross-reference potential with existing politicians"""
        print("🔍 Testing CPF Cross-Reference Potential...")

        try:
            # Sample politician CPFs for testing (these should be from actual database)
            sample_politician_cpfs = [
                "67821090425",  # Arthur Lira from previous tests
                "12345678901",  # Dummy for testing
                "98765432100"   # Dummy for testing
            ]

            url = f"{self.base_url}{self.endpoints['disqualifications']}"
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                return {'error': f'API returned status {response.status_code}'}

            data = response.json()

            cross_ref_analysis = {
                'tcu_records_checked': len(data) if isinstance(data, list) else 0,
                'cpf_format_issues': 0,
                'potential_matches': 0,
                'sample_matches': [],
                'implementation_confidence': 'unknown'
            }

            if isinstance(data, list):
                potential_matches = []
                cpf_issues = 0

                for record in data:
                    if 'cpf' in record and record['cpf']:
                        cpf = str(record['cpf'])
                        cpf_clean = re.sub(r'[^0-9]', '', cpf)

                        # Check CPF format
                        if len(cpf_clean) != 11:
                            cpf_issues += 1

                        # Check for matches with sample politicians
                        if cpf_clean in sample_politician_cpfs:
                            potential_matches.append({
                                'cpf': cpf_clean,
                                'nome': record.get('nome', 'N/A'),
                                'processo': record.get('processo', 'N/A')
                            })

                cross_ref_analysis['cpf_format_issues'] = cpf_issues
                cross_ref_analysis['potential_matches'] = len(potential_matches)
                cross_ref_analysis['sample_matches'] = potential_matches[:5]

                # Determine implementation confidence
                total_records = len(data)
                valid_cpfs = total_records - cpf_issues
                cpf_quality_rate = valid_cpfs / total_records if total_records > 0 else 0

                if cpf_quality_rate > 0.9:
                    cross_ref_analysis['implementation_confidence'] = 'high'
                elif cpf_quality_rate > 0.7:
                    cross_ref_analysis['implementation_confidence'] = 'medium'
                else:
                    cross_ref_analysis['implementation_confidence'] = 'low'

                print(f"   📊 TCU records: {total_records}")
                print(f"   ✅ Valid CPFs: {valid_cpfs} ({cpf_quality_rate:.1%})")
                print(f"   🎯 Confidence: {cross_ref_analysis['implementation_confidence']}")

                if potential_matches:
                    print(f"   🚨 Potential matches found: {len(potential_matches)}")
                    for match in potential_matches[:3]:
                        print(f"      • {match['nome']} (CPF: {match['cpf']}) - {match['processo']}")

            self.test_results['cpf_analysis'] = cross_ref_analysis
            return cross_ref_analysis

        except Exception as e:
            error_result = {'error': str(e)}
            self.test_results['cpf_analysis'] = error_result
            return error_result

    def test_rate_limiting_and_reliability(self) -> Dict:
        """Test API rate limiting and reliability for batch processing"""
        print("⏱️  Testing API Rate Limiting and Reliability...")

        rate_test_results = {
            'requests_tested': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0,
            'rate_limit_detected': False,
            'recommended_delay': 0
        }

        try:
            url = f"{self.base_url}{self.endpoints['disqualifications']}"
            response_times = []

            # Test 5 consecutive requests
            for i in range(5):
                start_time = time.time()
                response = requests.get(url, timeout=30)
                response_time = time.time() - start_time

                rate_test_results['requests_tested'] += 1

                if response.status_code == 200:
                    rate_test_results['successful_requests'] += 1
                    response_times.append(response_time)
                else:
                    rate_test_results['failed_requests'] += 1

                    if response.status_code == 429:  # Too Many Requests
                        rate_test_results['rate_limit_detected'] = True

                print(f"   Request {i+1}: {response.status_code} ({response_time:.2f}s)")

                # Small delay between requests
                time.sleep(0.5)

            if response_times:
                rate_test_results['average_response_time'] = sum(response_times) / len(response_times)

            # Recommendation based on results
            if rate_test_results['rate_limit_detected']:
                rate_test_results['recommended_delay'] = 2.0
            elif rate_test_results['average_response_time'] > 5.0:
                rate_test_results['recommended_delay'] = 1.0
            else:
                rate_test_results['recommended_delay'] = 0.5

            print(f"   📊 Success rate: {rate_test_results['successful_requests']}/{rate_test_results['requests_tested']}")
            print(f"   ⏱️  Avg response time: {rate_test_results['average_response_time']:.2f}s")
            print(f"   💤 Recommended delay: {rate_test_results['recommended_delay']}s")

            self.test_results['rate_limiting'] = rate_test_results
            return rate_test_results

        except Exception as e:
            rate_test_results['error'] = str(e)
            self.test_results['rate_limiting'] = rate_test_results
            return rate_test_results

    def generate_implementation_readiness_report(self) -> Dict:
        """Generate final implementation readiness assessment"""
        print("📋 Generating Implementation Readiness Report...")

        readiness_report = {
            'overall_readiness': 'unknown',
            'api_reliability': 'unknown',
            'data_quality': 'unknown',
            'cross_reference_viability': 'unknown',
            'implementation_risks': [],
            'implementation_recommendations': [],
            'estimated_effort': 'unknown'
        }

        # Assess API reliability
        connectivity = self.test_results.get('api_connectivity', {})
        rate_limiting = self.test_results.get('rate_limiting', {})

        if connectivity.get('disqualifications', {}).get('success', False):
            success_rate = rate_limiting.get('successful_requests', 0) / max(rate_limiting.get('requests_tested', 1), 1)
            if success_rate >= 0.8:
                readiness_report['api_reliability'] = 'high'
            elif success_rate >= 0.6:
                readiness_report['api_reliability'] = 'medium'
            else:
                readiness_report['api_reliability'] = 'low'
        else:
            readiness_report['api_reliability'] = 'failed'

        # Assess data quality
        cpf_analysis = self.test_results.get('cpf_analysis', {})
        readiness_report['data_quality'] = cpf_analysis.get('implementation_confidence', 'unknown')

        # Assess cross-reference viability
        data_volume = self.test_results.get('data_volume', {})
        total_records = data_volume.get('total_records', 0)

        if total_records > 100:
            readiness_report['cross_reference_viability'] = 'high'
        elif total_records > 10:
            readiness_report['cross_reference_viability'] = 'medium'
        else:
            readiness_report['cross_reference_viability'] = 'low'

        # Generate risks and recommendations
        if readiness_report['api_reliability'] == 'low':
            readiness_report['implementation_risks'].append('API reliability issues detected')

        if readiness_report['data_quality'] == 'low':
            readiness_report['implementation_risks'].append('CPF data quality concerns')

        if rate_limiting.get('rate_limit_detected', False):
            readiness_report['implementation_risks'].append('Rate limiting detected')
            readiness_report['implementation_recommendations'].append(f"Add {rate_limiting.get('recommended_delay', 1)}s delay between requests")

        # Overall readiness assessment
        high_scores = sum([1 for score in [readiness_report['api_reliability'], readiness_report['data_quality'], readiness_report['cross_reference_viability']] if score == 'high'])
        medium_scores = sum([1 for score in [readiness_report['api_reliability'], readiness_report['data_quality'], readiness_report['cross_reference_viability']] if score == 'medium'])

        if high_scores >= 2:
            readiness_report['overall_readiness'] = 'ready'
            readiness_report['estimated_effort'] = 'low'
        elif high_scores + medium_scores >= 2:
            readiness_report['overall_readiness'] = 'mostly_ready'
            readiness_report['estimated_effort'] = 'medium'
        else:
            readiness_report['overall_readiness'] = 'needs_work'
            readiness_report['estimated_effort'] = 'high'

        self.test_results['implementation_readiness'] = readiness_report

        print(f"   🎯 Overall Readiness: {readiness_report['overall_readiness']}")
        print(f"   🏗️  Estimated Effort: {readiness_report['estimated_effort']}")
        if readiness_report['implementation_risks']:
            print(f"   ⚠️  Risks: {len(readiness_report['implementation_risks'])} identified")

        return readiness_report

    def run_comprehensive_test(self) -> Dict:
        """Run all tests and generate final report"""
        print("🧪 COMPREHENSIVE TCU API INTEGRATION TEST")
        print("=" * 60)

        # Run all test phases
        self.test_api_connectivity()
        print()

        self.test_disqualifications_data_structure()
        print()

        self.test_data_volume_and_pagination()
        print()

        self.test_cpf_cross_reference_potential()
        print()

        self.test_rate_limiting_and_reliability()
        print()

        self.generate_implementation_readiness_report()
        print()

        return self.test_results

def main():
    """Run comprehensive TCU API integration test"""
    tester = TCUAPITester()
    results = tester.run_comprehensive_test()

    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/fcavalcanti/dev/open-data-gov/tests/integration/tcu_comprehensive_test_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"📄 Test results saved to: {output_file}")

    # Print final summary
    readiness = results.get('implementation_readiness', {})
    print("\n" + "=" * 60)
    print("🎯 FINAL IMPLEMENTATION ASSESSMENT")
    print("=" * 60)
    print(f"Overall Readiness: {readiness.get('overall_readiness', 'unknown')}")
    print(f"Estimated Effort: {readiness.get('estimated_effort', 'unknown')}")
    print(f"API Reliability: {readiness.get('api_reliability', 'unknown')}")
    print(f"Data Quality: {readiness.get('data_quality', 'unknown')}")
    print(f"Cross-Reference Viability: {readiness.get('cross_reference_viability', 'unknown')}")

    if readiness.get('implementation_risks'):
        print(f"\nRisks Identified:")
        for risk in readiness['implementation_risks']:
            print(f"  ⚠️  {risk}")

    if readiness.get('implementation_recommendations'):
        print(f"\nRecommendations:")
        for rec in readiness['implementation_recommendations']:
            print(f"  💡 {rec}")

if __name__ == "__main__":
    main()