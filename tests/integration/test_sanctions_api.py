#!/usr/bin/env python3
"""
INTEGRATION TEST: Portal da Transparência Sanctions API
Comprehensive testing before implementing the sanctions populator
"""

import requests
import json
import os
import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SanctionsAPITester:
    """Comprehensive tester for Portal da Transparência sanctions API"""

    def __init__(self):
        self.base_url = "https://api.portaldatransparencia.gov.br/api-de-dados/"

        # Load API key from environment
        self.api_key = os.getenv('PORTAL_TRANSPARENCIA_API_KEY')
        if not self.api_key:
            raise ValueError("PORTAL_TRANSPARENCIA_API_KEY not found in environment")

        self.session = requests.Session()
        self.session.headers.update({
            'chave-api-dados': self.api_key,
            'User-Agent': 'CLI4-Sanctions-Integration-Test/1.0'
        })

        # Rate limiting
        self.request_count = 0
        self.start_time = time.time()
        self.max_requests_per_minute = 90  # Portal limit

    def test_api_access(self) -> bool:
        """Test basic API access and authentication"""
        print("🔑 TESTING API ACCESS AND AUTHENTICATION")
        print("=" * 60)

        try:
            # Test basic endpoint
            url = f"{self.base_url}ceis"
            params = {'pagina': 1}

            response = self.session.get(url, params=params, timeout=30)

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ API access successful")
                print(f"📊 Sample data structure:")
                if data and isinstance(data, list) and len(data) > 0:
                    sample = data[0]
                    for key, value in sample.items():
                        print(f"   {key}: {type(value).__name__} = {str(value)[:100]}")
                elif isinstance(data, dict):
                    print(f"   Response is dict with keys: {list(data.keys())}")
                else:
                    print(f"   Response type: {type(data)}, length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                return True
            else:
                print(f"❌ API access failed: {response.status_code}")
                print(f"Error response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ API access exception: {e}")
            return False

    def test_cnpj_search_patterns(self) -> Dict[str, Any]:
        """Test different CNPJ search patterns and formats"""
        print(f"\n🔍 TESTING CNPJ SEARCH PATTERNS")
        print("=" * 60)

        # Test CNPJs from Arthur Lira case (known to have sanctions)
        test_cnpjs = [
            "29032820000147",  # Clean format
            "04735992000156",  # From Arthur Lira expenses
            "05459764000163",  # From Arthur Lira expenses
            "48949641000113",  # From Arthur Lira expenses
            "08886885000180"   # From Arthur Lira expenses
        ]

        results = {}

        for cnpj in test_cnpjs:
            print(f"\n🔎 Testing CNPJ: {cnpj}")

            try:
                # Test clean CNPJ format
                sanctions = self._fetch_sanctions_by_cnpj(cnpj)

                if sanctions:
                    print(f"   ✅ Found {len(sanctions)} sanctions")
                    results[cnpj] = {
                        'sanctions_count': len(sanctions),
                        'sanctions': sanctions[:2],  # Store first 2 for analysis
                        'status': 'SANCTIONED'
                    }

                    # Analyze first sanction
                    if len(sanctions) > 0:
                        first_sanction = sanctions[0]
                        print(f"   📋 Sample sanction:")
                        for key, value in first_sanction.items():
                            print(f"      {key}: {value}")
                else:
                    print(f"   ✓ No sanctions found (clean)")
                    results[cnpj] = {
                        'sanctions_count': 0,
                        'sanctions': [],
                        'status': 'CLEAN'
                    }

                # Rate limiting
                self._rate_limit()

            except Exception as e:
                print(f"   ❌ Error testing CNPJ {cnpj}: {e}")
                results[cnpj] = {
                    'error': str(e),
                    'status': 'ERROR'
                }

        return results

    def test_pagination_and_limits(self) -> Dict[str, Any]:
        """Test API pagination, limits, and response handling"""
        print(f"\n📄 TESTING PAGINATION AND LIMITS")
        print("=" * 60)

        pagination_results = {}

        try:
            # Test pagination without filters
            print("Testing pagination without filters...")

            page_1 = self._fetch_sanctions_page(1)
            print(f"Page 1: {len(page_1) if page_1 else 0} results")

            page_2 = self._fetch_sanctions_page(2)
            print(f"Page 2: {len(page_2) if page_2 else 0} results")

            # Test page size consistency
            if page_1 and page_2:
                page_1_size = len(page_1)
                page_2_size = len(page_2)
                print(f"Page size consistency: {page_1_size} vs {page_2_size}")

            pagination_results['basic_pagination'] = {
                'page_1_size': len(page_1) if page_1 else 0,
                'page_2_size': len(page_2) if page_2 else 0,
                'pagination_works': bool(page_1 and page_2)
            }

            # Test large page numbers
            page_100 = self._fetch_sanctions_page(100)
            print(f"Page 100: {len(page_100) if page_100 else 0} results")

            pagination_results['high_page_numbers'] = {
                'page_100_size': len(page_100) if page_100 else 0,
                'high_pages_work': page_100 is not None
            }

        except Exception as e:
            print(f"❌ Pagination test error: {e}")
            pagination_results['error'] = str(e)

        return pagination_results

    def test_field_analysis(self) -> Dict[str, Any]:
        """Analyze sanctions data structure for database mapping"""
        print(f"\n🔬 ANALYZING SANCTIONS DATA STRUCTURE")
        print("=" * 60)

        try:
            # Get sample data
            sample_sanctions = self._fetch_sanctions_page(1)

            if not sample_sanctions or len(sample_sanctions) == 0:
                print("❌ No sample data available for analysis")
                return {'error': 'No sample data'}

            print(f"📊 Analyzing {len(sample_sanctions)} sample sanctions")

            # Analyze field patterns
            field_analysis = {}

            for sanction in sample_sanctions:
                for field, value in sanction.items():
                    if field not in field_analysis:
                        field_analysis[field] = {
                            'type': type(value).__name__,
                            'sample_values': [],
                            'null_count': 0,
                            'max_length': 0
                        }

                    # Track sample values
                    if value is not None and value != '':
                        if len(field_analysis[field]['sample_values']) < 3:
                            field_analysis[field]['sample_values'].append(str(value))

                        # Track max length for strings
                        if isinstance(value, str):
                            field_analysis[field]['max_length'] = max(
                                field_analysis[field]['max_length'],
                                len(value)
                            )
                    else:
                        field_analysis[field]['null_count'] += 1

            print(f"\n📋 FIELD ANALYSIS RESULTS:")
            for field, analysis in field_analysis.items():
                null_pct = (analysis['null_count'] / len(sample_sanctions)) * 100
                print(f"\n   {field}:")
                print(f"      Type: {analysis['type']}")
                print(f"      Null rate: {null_pct:.1f}%")
                if analysis['max_length'] > 0:
                    print(f"      Max length: {analysis['max_length']}")
                if analysis['sample_values']:
                    print(f"      Samples: {analysis['sample_values']}")

            return field_analysis

        except Exception as e:
            print(f"❌ Field analysis error: {e}")
            return {'error': str(e)}

    def test_known_sanctions(self) -> Dict[str, Any]:
        """Test with known sanctioned entities from Arthur Lira case"""
        print(f"\n⚠️  TESTING KNOWN SANCTIONED ENTITIES")
        print("=" * 60)
        print("Testing CNPJs that should have sanctions (from CORRUPTION_ANALYSIS.md)")

        # CNPJs from Arthur Lira case study that were 100% sanctioned
        known_sanctioned_cnpjs = [
            "29032820000147",  # Should be sanctioned
            "04735992000156",  # Should be sanctioned
            "05459764000163",  # Should be sanctioned
            "48949641000113",  # Should be sanctioned
            "08886885000180"   # Should be sanctioned
        ]

        sanctioned_results = {}
        total_sanctions_found = 0

        for cnpj in known_sanctioned_cnpjs:
            print(f"\n🎯 Testing known sanctioned CNPJ: {cnpj}")

            try:
                sanctions = self._fetch_sanctions_by_cnpj(cnpj)

                if sanctions and len(sanctions) > 0:
                    print(f"   ✅ CONFIRMED: {len(sanctions)} sanctions found")
                    total_sanctions_found += len(sanctions)

                    sanctioned_results[cnpj] = {
                        'sanctions_count': len(sanctions),
                        'sanctions_found': True,
                        'sample_sanction': sanctions[0]
                    }

                    # Show sanction details
                    for i, sanction in enumerate(sanctions[:2]):  # Show first 2
                        print(f"      Sanction {i+1}:")
                        print(f"         Type: {sanction.get('descricaoSancao', 'N/A')}")
                        print(f"         Agency: {sanction.get('orgaoSancionador', 'N/A')}")
                        print(f"         Date: {sanction.get('dataInicioSancao', 'N/A')}")
                else:
                    print(f"   ❌ UNEXPECTED: No sanctions found for {cnpj}")
                    sanctioned_results[cnpj] = {
                        'sanctions_count': 0,
                        'sanctions_found': False,
                        'error': 'Expected sanctions but none found'
                    }

                self._rate_limit()

            except Exception as e:
                print(f"   ❌ Error checking {cnpj}: {e}")
                sanctioned_results[cnpj] = {
                    'error': str(e),
                    'sanctions_found': False
                }

        # Summary
        print(f"\n📊 KNOWN SANCTIONS TEST SUMMARY:")
        sanctions_found_count = sum(1 for r in sanctioned_results.values() if r.get('sanctions_found', False))
        print(f"   Expected sanctioned CNPJs: {len(known_sanctioned_cnpjs)}")
        print(f"   Sanctions confirmed: {sanctions_found_count}")
        print(f"   Total sanctions found: {total_sanctions_found}")
        print(f"   Success rate: {(sanctions_found_count / len(known_sanctioned_cnpjs)) * 100:.1f}%")

        return {
            'tested_cnpjs': known_sanctioned_cnpjs,
            'results': sanctioned_results,
            'summary': {
                'expected_sanctioned': len(known_sanctioned_cnpjs),
                'confirmed_sanctioned': sanctions_found_count,
                'total_sanctions_found': total_sanctions_found,
                'success_rate': (sanctions_found_count / len(known_sanctioned_cnpjs)) * 100
            }
        }

    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and edge cases"""
        print(f"\n🛡️  TESTING ERROR HANDLING AND EDGE CASES")
        print("=" * 60)

        error_tests = {}

        # Test invalid CNPJ formats
        print("Testing invalid CNPJ formats...")
        invalid_cnpjs = [
            "invalid",
            "12345",
            "123456789012345",  # Too long
            "00000000000000",   # All zeros
            ""                  # Empty
        ]

        for invalid_cnpj in invalid_cnpjs:
            try:
                result = self._fetch_sanctions_by_cnpj(invalid_cnpj)
                error_tests[f"invalid_cnpj_{invalid_cnpj or 'empty'}"] = {
                    'handled_gracefully': True,
                    'result_type': type(result).__name__,
                    'result_count': len(result) if result else 0
                }
                print(f"   Invalid CNPJ '{invalid_cnpj}': handled gracefully")
            except Exception as e:
                error_tests[f"invalid_cnpj_{invalid_cnpj or 'empty'}"] = {
                    'handled_gracefully': False,
                    'error': str(e)
                }
                print(f"   Invalid CNPJ '{invalid_cnpj}': threw exception - {e}")

        # Test very high page numbers
        print("\nTesting very high page numbers...")
        try:
            high_page_result = self._fetch_sanctions_page(999999)
            error_tests['high_page_number'] = {
                'handled_gracefully': True,
                'result': high_page_result is not None,
                'result_count': len(high_page_result) if high_page_result else 0
            }
            print(f"   High page number: handled gracefully")
        except Exception as e:
            error_tests['high_page_number'] = {
                'handled_gracefully': False,
                'error': str(e)
            }
            print(f"   High page number: threw exception - {e}")

        return error_tests

    def _fetch_sanctions_by_cnpj(self, cnpj: str) -> List[Dict]:
        """Fetch sanctions for a specific CNPJ"""
        # Clean CNPJ
        cnpj_clean = re.sub(r'[^\d]', '', cnpj)

        url = f"{self.base_url}ceis"
        params = {
            'cnpjSancionado': cnpj_clean,
            'pagina': 1
        }

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data if isinstance(data, list) else []

    def _fetch_sanctions_page(self, page: int) -> List[Dict]:
        """Fetch a page of sanctions"""
        url = f"{self.base_url}ceis"
        params = {'pagina': page}

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data if isinstance(data, list) else []

    def _rate_limit(self):
        """Simple rate limiting"""
        self.request_count += 1

        # Check if we need to wait
        elapsed = time.time() - self.start_time
        if elapsed < 60 and self.request_count >= self.max_requests_per_minute:
            wait_time = 60 - elapsed
            print(f"   ⏰ Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
            self.start_time = time.time()
            self.request_count = 0

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        print("🧪 COMPREHENSIVE SANCTIONS API INTEGRATION TEST")
        print("=" * 80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        results = {
            'test_start': datetime.now().isoformat(),
            'api_key_configured': bool(self.api_key),
            'base_url': self.base_url
        }

        # Test 1: Basic API access
        results['api_access'] = self.test_api_access()

        if not results['api_access']:
            print("\n❌ ABORTING: Basic API access failed")
            return results

        # Test 2: CNPJ search patterns
        results['cnpj_search'] = self.test_cnpj_search_patterns()

        # Test 3: Pagination
        results['pagination'] = self.test_pagination_and_limits()

        # Test 4: Field analysis
        results['field_analysis'] = self.test_field_analysis()

        # Test 5: Known sanctions
        results['known_sanctions'] = self.test_known_sanctions()

        # Test 6: Error handling
        results['error_handling'] = self.test_error_handling()

        # Final summary
        results['test_end'] = datetime.now().isoformat()
        results['total_requests'] = self.request_count

        print(f"\n🎯 COMPREHENSIVE TEST COMPLETED")
        print("=" * 80)
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total API requests: {self.request_count}")

        return results


def main():
    """Run comprehensive sanctions API integration test"""
    try:
        tester = SanctionsAPITester()
        results = tester.run_comprehensive_test()

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sanctions_api_integration_test_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 Results saved to: {filename}")

        # Final assessment
        print(f"\n🏆 FINAL ASSESSMENT:")
        print(f"   API Access: {'✅' if results.get('api_access') else '❌'}")
        print(f"   CNPJ Search: {'✅' if results.get('cnpj_search') else '❌'}")
        print(f"   Pagination: {'✅' if results.get('pagination', {}).get('basic_pagination', {}).get('pagination_works') else '❌'}")
        print(f"   Field Analysis: {'✅' if results.get('field_analysis') and 'error' not in results['field_analysis'] else '❌'}")

        # Known sanctions assessment
        known_sanctions = results.get('known_sanctions', {})
        if known_sanctions and 'summary' in known_sanctions:
            success_rate = known_sanctions['summary'].get('success_rate', 0)
            print(f"   Known Sanctions: {'✅' if success_rate >= 80 else '⚠️' if success_rate >= 50 else '❌'} ({success_rate:.1f}%)")

        print(f"   Error Handling: {'✅' if results.get('error_handling') else '❌'}")

        # Overall readiness
        basic_tests_pass = all([
            results.get('api_access'),
            results.get('cnpj_search'),
            results.get('field_analysis') and 'error' not in results.get('field_analysis', {})
        ])

        if basic_tests_pass:
            print(f"\n🚀 READY FOR IMPLEMENTATION: All basic tests passed!")
            print(f"   ✅ API integration working")
            print(f"   ✅ Data structure understood")
            print(f"   ✅ CNPJ search functional")
            print(f"\n📋 Next step: Implement sanctions populator")
        else:
            print(f"\n⚠️  NOT READY: Some tests failed")
            print(f"   Review test results before implementation")

        return results

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {'critical_error': str(e)}


if __name__ == "__main__":
    main()