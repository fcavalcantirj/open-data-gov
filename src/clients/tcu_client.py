"""
TCU (Tribunal de Contas da União) API Client
Integration with Brazilian Federal Audit Court APIs for political network analysis.

Based on TCU open data and web services documentation.
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re


class TCUClient:
    """
    Client for accessing TCU (Federal Audit Court) APIs
    Provides audit data, sanctions, and investigation information
    """

    def __init__(self):
        self.base_url = "https://contas.tcu.gov.br/ords/"
        self.dados_abertos_url = "https://dados-abertos.apps.tcu.gov.br/api/"
        self.certidoes_url = "https://certidoes-apf.apps.tcu.gov.br/api/rest/publico/"

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Brazilian-Political-Network-Analyzer/1.0',
            'Accept': 'application/json'
        })

    def get_disqualified_persons(self, name: Optional[str] = None, cpf: Optional[str] = None) -> Dict[str, Any]:
        """
        Get disqualified persons from TCU database
        Key function for political network risk assessment
        """
        url = f"{self.base_url}condenacao/consulta/inabilitados"

        params = {}
        if name:
            params['nome'] = name.upper()
        if cpf:
            cpf_clean = re.sub(r'[^\d]', '', cpf)
            params['cpf'] = cpf_clean

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching disqualified persons: {e}")
            return {}

    def get_acordaos(self, search_term: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """
        Get TCU rulings (acordãos) - key audit decisions
        """
        url = f"{self.dados_abertos_url}acordao/recupera-acordaos"

        params = {
            'limit': limit
        }

        if search_term:
            params['termo'] = search_term

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching acordãos: {e}")
            return {}

    def get_congressional_requests(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get congressional requests to TCU
        Shows political pressure and investigation requests
        """
        url = f"{self.base_url}api/publica/scn/pedidos_congresso"

        params = {}
        if year:
            params['ano'] = year

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching congressional requests: {e}")
            return {}

    def get_company_certification(self, cnpj: str) -> Dict[str, Any]:
        """
        Get company certification and audit status
        Cross-references with vendor CNPJs from politician expenses
        """
        cnpj_clean = re.sub(r'[^\d]', '', cnpj)

        url = f"{self.certidoes_url}certidoes/{cnpj_clean}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching company certification for {cnpj}: {e}")
            return {}

    def analyze_politician_tcu_exposure(self, politician_data: Dict, vendor_cnpjs: List[str] = None) -> Dict[str, Any]:
        """
        Complete TCU exposure analysis for a politician
        Core function for audit risk assessment
        """
        print(f"\n🔍 TCU AUDIT EXPOSURE ANALYSIS")
        print(f"Politician: {politician_data.get('name', 'Unknown')}")
        print("-" * 50)

        analysis = {
            'politician': politician_data,
            'disqualification_check': {},
            'vendor_audit_status': [],
            'related_rulings': {},
            'congressional_mentions': {},
            'audit_risk_score': 0.0,
            'risk_factors': [],
            'timestamp': datetime.now().isoformat()
        }

        # Check if politician is disqualified
        politician_name = politician_data.get('name', '')
        politician_cpf = politician_data.get('cpf')

        if politician_name:
            print(f"🔍 Checking disqualifications for: {politician_name}")
            disqualified = self.get_disqualified_persons(name=politician_name)
            analysis['disqualification_check'] = disqualified

            if disqualified and 'items' in disqualified and disqualified['items']:
                analysis['risk_factors'].append('Found in TCU disqualification database')
                analysis['audit_risk_score'] += 0.8
                print(f"  ⚠️ FOUND: {len(disqualified['items'])} disqualification records")
            else:
                print(f"  ✓ Clean: No disqualifications found")

        # Check CPF-based disqualifications
        if politician_cpf:
            print(f"🔍 Checking CPF disqualifications: {politician_cpf}")
            cpf_disqualified = self.get_disqualified_persons(cpf=politician_cpf)

            if cpf_disqualified and 'items' in cpf_disqualified and cpf_disqualified['items']:
                analysis['risk_factors'].append('CPF found in disqualification database')
                analysis['audit_risk_score'] += 0.9
                print(f"  ⚠️ CPF MATCH: {len(cpf_disqualified['items'])} records")

        # Check vendor audit status
        if vendor_cnpjs:
            print(f"\n💼 Checking audit status for {len(vendor_cnpjs)} vendor CNPJs...")

            vendor_audit_issues = 0
            for cnpj in vendor_cnpjs[:10]:  # Limit to first 10 for testing
                try:
                    cert_status = self.get_company_certification(cnpj)

                    vendor_analysis = {
                        'cnpj': cnpj,
                        'certification_status': cert_status,
                        'has_issues': False
                    }

                    # Check for audit issues
                    if cert_status and 'status' in cert_status:
                        if cert_status['status'] in ['IRREGULAR', 'SUSPENDED', 'INELIGIBLE']:
                            vendor_analysis['has_issues'] = True
                            vendor_audit_issues += 1
                            print(f"  ⚠️ {cnpj}: {cert_status.get('status', 'UNKNOWN')}")
                        else:
                            print(f"  ✓ {cnpj}: Regular")

                    analysis['vendor_audit_status'].append(vendor_analysis)

                except Exception as e:
                    print(f"  ❌ {cnpj}: Error - {e}")

            if vendor_audit_issues > 0:
                vendor_risk_factor = vendor_audit_issues / len(vendor_cnpjs[:10])
                analysis['risk_factors'].append(f'{vendor_audit_issues} vendors with audit issues')
                analysis['audit_risk_score'] += vendor_risk_factor * 0.5

        # Search for related rulings
        if politician_name:
            print(f"\n📋 Searching TCU rulings mentioning: {politician_name}")
            rulings = self.get_acordaos(search_term=politician_name)
            analysis['related_rulings'] = rulings

            if rulings and 'items' in rulings and rulings['items']:
                analysis['risk_factors'].append(f'Mentioned in {len(rulings["items"])} TCU rulings')
                analysis['audit_risk_score'] += len(rulings['items']) * 0.1
                print(f"  📄 Found {len(rulings['items'])} rulings")
            else:
                print(f"  ○ No rulings found")

        # Check congressional investigation requests
        current_year = datetime.now().year
        print(f"\n🏛️ Checking congressional requests for {current_year}")
        congress_requests = self.get_congressional_requests(current_year)
        analysis['congressional_mentions'] = congress_requests

        # Final risk assessment
        analysis['audit_risk_score'] = min(analysis['audit_risk_score'], 1.0)

        if analysis['audit_risk_score'] > 0.7:
            risk_level = "HIGH"
        elif analysis['audit_risk_score'] > 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        print(f"\n📊 TCU AUDIT ANALYSIS:")
        print(f"   Risk factors: {len(analysis['risk_factors'])}")
        print(f"   Audit risk score: {analysis['audit_risk_score']:.2f}")
        print(f"   Risk level: {risk_level}")

        for factor in analysis['risk_factors']:
            print(f"   - {factor}")

        return analysis

    def test_tcu_connectivity(self) -> Dict[str, Any]:
        """
        Test TCU API connectivity and available services
        """
        print("🔌 TCU API CONNECTIVITY TEST")
        print("=" * 40)

        test_results = {
            'accessible_endpoints': [],
            'error_responses': [],
            'api_status': 'unknown'
        }

        # Test different endpoints
        test_endpoints = [
            {
                'name': 'Disqualified Persons',
                'url': f"{self.base_url}condenacao/consulta/inabilitados",
                'method': 'GET'
            },
            {
                'name': 'Acordãos',
                'url': f"{self.dados_abertos_url}acordao/recupera-acordaos",
                'method': 'GET'
            },
            {
                'name': 'Congressional Requests',
                'url': f"{self.base_url}api/publica/scn/pedidos_congresso",
                'method': 'GET'
            }
        ]

        for endpoint in test_endpoints:
            try:
                response = self.session.get(endpoint['url'], timeout=10)

                if response.status_code in [200, 201]:
                    test_results['accessible_endpoints'].append({
                        'name': endpoint['name'],
                        'url': endpoint['url'],
                        'status': response.status_code,
                        'response_size': len(response.content)
                    })
                    print(f"✓ {endpoint['name']}: {response.status_code}")

                else:
                    test_results['error_responses'].append({
                        'name': endpoint['name'],
                        'status': response.status_code,
                        'url': endpoint['url']
                    })
                    print(f"⚠ {endpoint['name']}: {response.status_code}")

            except Exception as e:
                test_results['error_responses'].append({
                    'name': endpoint['name'],
                    'error': str(e),
                    'url': endpoint['url']
                })
                print(f"❌ {endpoint['name']}: {e}")

        # Overall API status
        if len(test_results['accessible_endpoints']) >= 2:
            test_results['api_status'] = 'working'
        elif len(test_results['accessible_endpoints']) >= 1:
            test_results['api_status'] = 'partial'
        else:
            test_results['api_status'] = 'failed'

        print(f"\n📊 TEST SUMMARY:")
        print(f"   Working endpoints: {len(test_results['accessible_endpoints'])}")
        print(f"   Failed endpoints: {len(test_results['error_responses'])}")
        print(f"   Overall status: {test_results['api_status']}")

        return test_results


def test_tcu_integration():
    """
    Test TCU integration with Arthur Lira data
    """
    print("🔍 TCU INTEGRATION TEST")
    print("=" * 50)

    client = TCUClient()

    # Test connectivity first
    connectivity = client.test_tcu_connectivity()

    # Test with Arthur Lira data
    arthur_lira_data = {
        'name': 'Arthur Lira',
        'cpf': '67821090425',  # From TSE integration
        'party': 'PP',
        'state': 'AL'
    }

    # Sample vendor CNPJs from previous analysis
    vendor_cnpjs = [
        '29032820000147',
        '04735992000156',
        '05459764000163'
    ]

    # Analyze TCU exposure
    tcu_analysis = client.analyze_politician_tcu_exposure(arthur_lira_data, vendor_cnpjs)

    return {
        'connectivity_test': connectivity,
        'tcu_analysis': tcu_analysis,
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run TCU integration test
    result = test_tcu_integration()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tcu_integration_test_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Results saved to: {filename}")

    # Summary
    connectivity = result.get('connectivity_test', {})
    tcu = result.get('tcu_analysis', {})

    print(f"\n📈 FINAL SUMMARY:")
    print(f"   API Status: {connectivity.get('api_status', 'unknown').upper()}")
    print(f"   Working endpoints: {len(connectivity.get('accessible_endpoints', []))}")
    print(f"   Risk factors: {len(tcu.get('risk_factors', []))}")
    print(f"   Audit risk score: {tcu.get('audit_risk_score', 0):.2f}")
    print(f"   TCU Integration: {'✅ Working' if connectivity.get('api_status') == 'working' else '❌ Needs investigation'}")