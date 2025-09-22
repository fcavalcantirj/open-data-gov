"""
DataJud API Client
Integration with Brazilian National Judicial Database for political network analysis.

Based on CNJ DataJud public API documentation.
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


class DataJudClient:
    """
    Client for accessing CNJ DataJud public API
    Searches judicial processes for political network correlation
    """

    def __init__(self):
        self.base_url = "https://api-publica.datajud.cnj.jus.br/"

        # Public API Key from CNJ documentation
        self.api_key = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'APIKey {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Brazilian-Political-Network-Analyzer/1.0'
        })

    def search_processes_by_name(self, person_name: str, limit: int = 100) -> Dict[str, Any]:
        """
        Search judicial processes by person name
        """
        # Normalize name for search
        search_name = self._normalize_name_for_search(person_name)

        print(f"🔍 DATAJUD SEARCH: {search_name}")

        # DataJud typically uses Elasticsearch-style queries
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "nomePartes": search_name
                            }
                        }
                    ]
                }
            },
            "size": limit,
            "sort": [
                {
                    "dataAjuizamento": {
                        "order": "desc"
                    }
                }
            ]
        }

        try:
            # Try different possible endpoints
            endpoints = [
                "processos/_search",
                "search/processos",
                "_search",
                "api/processos/search"
            ]

            for endpoint in endpoints:
                url = f"{self.base_url}{endpoint}"
                print(f"Trying endpoint: {endpoint}")

                try:
                    response = self.session.post(url, json=query, timeout=30)

                    if response.status_code == 200:
                        print(f"✓ Success with endpoint: {endpoint}")
                        return response.json()
                    elif response.status_code == 404:
                        print(f"  404 - Endpoint not found: {endpoint}")
                        continue
                    else:
                        print(f"  {response.status_code} - {endpoint}")
                        continue

                except requests.exceptions.RequestException as e:
                    print(f"  Error with {endpoint}: {e}")
                    continue

            # If POST doesn't work, try GET with query parameters
            for endpoint in ["processos", "search"]:
                url = f"{self.base_url}{endpoint}"
                params = {
                    'nomePartes': search_name,
                    'size': limit
                }

                try:
                    response = self.session.get(url, params=params, timeout=30)

                    if response.status_code == 200:
                        print(f"✓ Success with GET {endpoint}")
                        return response.json()
                    else:
                        print(f"  GET {response.status_code} - {endpoint}")

                except requests.exceptions.RequestException as e:
                    print(f"  GET Error with {endpoint}: {e}")
                    continue

            print("❌ No working endpoints found")
            return {"error": "No accessible endpoints found"}

        except Exception as e:
            print(f"❌ DataJud search error: {e}")
            return {"error": str(e)}

    def search_processes_by_cpf(self, cpf: str, limit: int = 100) -> Dict[str, Any]:
        """
        Search judicial processes by CPF
        """
        cpf_clean = re.sub(r'[^\d]', '', cpf)

        print(f"🔍 DATAJUD CPF SEARCH: {cpf_clean}")

        query = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "cpfPartes": cpf_clean
                            }
                        },
                        {
                            "match": {
                                "documentoPartes": cpf_clean
                            }
                        }
                    ]
                }
            },
            "size": limit
        }

        # Similar endpoint testing as name search
        try:
            endpoints = ["processos/_search", "search/processos", "_search"]

            for endpoint in endpoints:
                url = f"{self.base_url}{endpoint}"

                try:
                    response = self.session.post(url, json=query, timeout=30)

                    if response.status_code == 200:
                        return response.json()

                except requests.exceptions.RequestException:
                    continue

            return {"error": "No accessible CPF search endpoints"}

        except Exception as e:
            return {"error": str(e)}

    def _normalize_name_for_search(self, name: str) -> str:
        """
        Normalize name for judicial search
        """
        if not name:
            return ""

        # Convert to uppercase (common in judicial systems)
        name = name.upper()

        # Remove titles
        name = re.sub(r'\b(DEPUTADO|DEPUTADA|SENADOR|SENADORA|DR\.?|DRA\.?)\b', '', name)

        # Remove special characters but keep spaces
        name = re.sub(r'[^\w\s]', '', name)

        # Normalize whitespace
        name = re.sub(r'\s+', ' ', name).strip()

        return name

    def analyze_politician_judicial_exposure(self, politician_data: Dict) -> Dict[str, Any]:
        """
        Complete judicial exposure analysis for a politician
        """
        print(f"\n⚖️ JUDICIAL EXPOSURE ANALYSIS")
        print(f"Politician: {politician_data.get('name', 'Unknown')}")
        print("-" * 50)

        analysis = {
            'politician': politician_data,
            'name_search_results': {},
            'cpf_search_results': {},
            'total_processes': 0,
            'risk_indicators': [],
            'judicial_exposure_score': 0.0,
            'timestamp': datetime.now().isoformat()
        }

        # Search by name
        politician_name = politician_data.get('name', '')
        if politician_name:
            name_results = self.search_processes_by_name(politician_name)
            analysis['name_search_results'] = name_results

            if 'hits' in name_results and 'total' in name_results['hits']:
                name_count = name_results['hits']['total']
                if isinstance(name_count, dict):
                    name_count = name_count.get('value', 0)
                analysis['total_processes'] += name_count
                print(f"  Name search: {name_count} processes")

        # Search by CPF (if available)
        politician_cpf = politician_data.get('cpf')
        if politician_cpf:
            cpf_results = self.search_processes_by_cpf(politician_cpf)
            analysis['cpf_search_results'] = cpf_results

            if 'hits' in cpf_results and 'total' in cpf_results['hits']:
                cpf_count = cpf_results['hits']['total']
                if isinstance(cpf_count, dict):
                    cpf_count = cpf_count.get('value', 0)
                analysis['total_processes'] += cpf_count
                print(f"  CPF search: {cpf_count} processes")

        # Risk assessment
        if analysis['total_processes'] > 0:
            analysis['risk_indicators'].append("Has judicial processes")

            if analysis['total_processes'] > 5:
                analysis['risk_indicators'].append("High litigation volume")
                analysis['judicial_exposure_score'] = 0.8
            elif analysis['total_processes'] > 1:
                analysis['risk_indicators'].append("Multiple processes")
                analysis['judicial_exposure_score'] = 0.5
            else:
                analysis['judicial_exposure_score'] = 0.2

        print(f"\n📊 JUDICIAL ANALYSIS:")
        print(f"   Total processes: {analysis['total_processes']}")
        print(f"   Exposure score: {analysis['judicial_exposure_score']:.2f}")
        print(f"   Risk indicators: {len(analysis['risk_indicators'])}")

        return analysis

    def test_api_connectivity(self) -> Dict[str, Any]:
        """
        Test DataJud API connectivity and available endpoints
        """
        print("🔌 DATAJUD API CONNECTIVITY TEST")
        print("=" * 40)

        test_results = {
            'api_key_valid': False,
            'accessible_endpoints': [],
            'error_responses': [],
            'base_url': self.base_url
        }

        # Test different base endpoints
        test_endpoints = [
            "",  # Root
            "health",
            "status",
            "_cluster/health",
            "processos",
            "_search"
        ]

        for endpoint in test_endpoints:
            url = f"{self.base_url}{endpoint}"

            try:
                response = self.session.get(url, timeout=10)

                if response.status_code in [200, 201]:
                    test_results['accessible_endpoints'].append({
                        'endpoint': endpoint,
                        'status': response.status_code,
                        'response_size': len(response.content)
                    })
                    print(f"✓ {endpoint or 'root'}: {response.status_code}")

                    if endpoint == "":
                        test_results['api_key_valid'] = True

                elif response.status_code == 401:
                    test_results['error_responses'].append({
                        'endpoint': endpoint,
                        'status': 401,
                        'message': 'Authentication required'
                    })
                    print(f"🔐 {endpoint or 'root'}: 401 - Auth required")

                else:
                    test_results['error_responses'].append({
                        'endpoint': endpoint,
                        'status': response.status_code
                    })
                    print(f"⚠ {endpoint or 'root'}: {response.status_code}")

            except Exception as e:
                test_results['error_responses'].append({
                    'endpoint': endpoint,
                    'error': str(e)
                })
                print(f"❌ {endpoint or 'root'}: {e}")

        print(f"\n📊 TEST SUMMARY:")
        print(f"   Accessible endpoints: {len(test_results['accessible_endpoints'])}")
        print(f"   Error responses: {len(test_results['error_responses'])}")
        print(f"   API key valid: {test_results['api_key_valid']}")

        return test_results


def test_datajud_integration():
    """
    Test DataJud integration with Arthur Lira data
    """
    print("⚖️ DATAJUD INTEGRATION TEST")
    print("=" * 50)

    client = DataJudClient()

    # First test connectivity
    connectivity = client.test_api_connectivity()

    # Test with Arthur Lira data
    arthur_lira_data = {
        'name': 'Arthur Lira',
        'cpf': '67821090425',  # From TSE integration
        'party': 'PP',
        'state': 'AL'
    }

    # Analyze judicial exposure
    judicial_analysis = client.analyze_politician_judicial_exposure(arthur_lira_data)

    return {
        'connectivity_test': connectivity,
        'judicial_analysis': judicial_analysis,
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run DataJud integration test
    result = test_datajud_integration()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"datajud_integration_test_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Results saved to: {filename}")

    # Summary
    connectivity = result.get('connectivity_test', {})
    judicial = result.get('judicial_analysis', {})

    print(f"\n📈 FINAL SUMMARY:")
    print(f"   API accessible: {len(connectivity.get('accessible_endpoints', []))} endpoints")
    print(f"   Judicial processes: {judicial.get('total_processes', 0)}")
    print(f"   Exposure score: {judicial.get('judicial_exposure_score', 0):.2f}")
    print(f"   API Status: {'✅ Working' if connectivity.get('api_key_valid') else '❌ Needs investigation'}")