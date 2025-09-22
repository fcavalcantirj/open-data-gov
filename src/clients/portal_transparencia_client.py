"""
Portal da Transparência API Client
Integration with Brazilian Government Transparency Portal for contract analysis.

Cross-references politician expense CNPJs with government contracts and sanctions.
"""

import requests
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re


class PortalTransparenciaClient:
    """
    Client for accessing Portal da Transparência APIs
    Enables correlation of politician expenses with government contracts
    """

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.portaldatransparencia.gov.br/api-de-dados/"

        # Load API key from environment or parameter
        if api_key:
            self.api_key = api_key
        else:
            # Try to load from .env file
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('PORTAL_TRANSPARENCIA_API_KEY='):
                            self.api_key = line.split('=')[1].strip()
                            break
                    else:
                        raise ValueError("API key not found in .env file")
            except FileNotFoundError:
                raise ValueError("No API key provided and .env file not found")

        self.session = requests.Session()
        self.session.headers.update({
            'chave-api-dados': self.api_key,
            'User-Agent': 'Brazilian-Political-Network-Analyzer/1.0'
        })

    def get_sanctioned_companies(self, cnpj: Optional[str] = None, page: int = 1) -> Dict[str, Any]:
        """
        Get sanctioned companies (CEIS - Cadastro de Empresas Inidôneas e Suspensas)
        """
        url = f"{self.base_url}ceis"
        params = {'pagina': page}

        if cnpj:
            # Clean CNPJ
            cnpj_clean = re.sub(r'[^\d]', '', cnpj)
            params['cnpjSancionado'] = cnpj_clean

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching sanctioned companies: {e}")
            return {}

    def get_government_contracts(self, cnpj: Optional[str] = None, year: Optional[int] = None, page: int = 1) -> Dict[str, Any]:
        """
        Get government contracts by CNPJ
        """
        url = f"{self.base_url}contratos"
        params = {'pagina': page}

        if cnpj:
            cnpj_clean = re.sub(r'[^\d]', '', cnpj)
            params['cnpjContratada'] = cnpj_clean

        if year:
            params['anoAssinatura'] = year

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching contracts: {e}")
            return {}

    def get_public_servants(self, name: Optional[str] = None, cpf: Optional[str] = None, page: int = 1) -> Dict[str, Any]:
        """
        Get public servants information
        """
        url = f"{self.base_url}servidores"
        params = {'pagina': page}

        if name:
            params['nome'] = name

        if cpf:
            cpf_clean = re.sub(r'[^\d]', '', cpf)
            params['cpf'] = cpf_clean

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching public servants: {e}")
            return {}

    def get_nepotism_register(self, cpf: Optional[str] = None, page: int = 1) -> Dict[str, Any]:
        """
        Get nepotism register information
        """
        url = f"{self.base_url}cnep"
        params = {'pagina': page}

        if cpf:
            cpf_clean = re.sub(r'[^\d]', '', cpf)
            params['cpf'] = cpf_clean

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching nepotism register: {e}")
            return {}

    def analyze_politician_vendor_network(self, vendor_cnpjs: List[str], politician_name: str = "Unknown") -> Dict[str, Any]:
        """
        Analyze a politician's vendor network against government transparency data
        Core function for implementing the correlation strategy
        """
        print(f"\n💼 VENDOR NETWORK ANALYSIS")
        print(f"Politician: {politician_name}")
        print(f"Analyzing {len(vendor_cnpjs)} vendor CNPJs...")
        print("-" * 50)

        analysis = {
            'politician': politician_name,
            'total_vendors': len(vendor_cnpjs),
            'sanctioned_vendors': [],
            'government_contractors': [],
            'contract_patterns': {},
            'risk_assessment': 'LOW',
            'timestamp': datetime.now().isoformat()
        }

        # Check each CNPJ against sanctions and contracts
        for i, cnpj in enumerate(vendor_cnpjs):
            print(f"Checking CNPJ {i+1}/{len(vendor_cnpjs)}: {cnpj}")

            # Check sanctions
            try:
                sanctions = self.get_sanctioned_companies(cnpj)
                if sanctions and len(sanctions) > 0:
                    analysis['sanctioned_vendors'].append({
                        'cnpj': cnpj,
                        'sanctions': sanctions
                    })
                    print(f"  ⚠ SANCTIONED: Found {len(sanctions)} sanctions")
                else:
                    print(f"  ✓ Clean: No sanctions")
            except Exception as e:
                print(f"  ✗ Error checking sanctions: {e}")

            # Check government contracts
            try:
                current_year = datetime.now().year
                contracts_data = self.get_government_contracts(cnpj, current_year)

                if contracts_data and len(contracts_data) > 0:
                    analysis['government_contractors'].append({
                        'cnpj': cnpj,
                        'contracts': contracts_data
                    })
                    print(f"  💰 CONTRACTOR: Found {len(contracts_data)} contracts")
                else:
                    print(f"  ○ No current contracts")
            except Exception as e:
                print(f"  ✗ Error checking contracts: {e}")

        # Risk assessment
        sanctioned_count = len(analysis['sanctioned_vendors'])
        contractor_count = len(analysis['government_contractors'])

        if sanctioned_count > 0:
            analysis['risk_assessment'] = 'HIGH'
        elif contractor_count > len(vendor_cnpjs) * 0.3:  # >30% are contractors
            analysis['risk_assessment'] = 'MEDIUM'
        else:
            analysis['risk_assessment'] = 'LOW'

        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"   Sanctioned vendors: {sanctioned_count}")
        print(f"   Government contractors: {contractor_count}")
        print(f"   Risk assessment: {analysis['risk_assessment']}")

        return analysis

    def cross_reference_politician(self, politician_data: Dict, vendor_cnpjs: List[str]) -> Dict[str, Any]:
        """
        Complete cross-reference of politician against transparency databases
        """
        print(f"\n🔍 COMPLETE TRANSPARENCY CROSS-REFERENCE")
        print(f"Politician: {politician_data.get('name', 'Unknown')}")

        cross_ref = {
            'politician_data': politician_data,
            'vendor_analysis': {},
            'cpf_checks': {},
            'servant_records': {},
            'nepotism_records': {},
            'overall_transparency_score': 0.0
        }

        # Vendor network analysis
        cross_ref['vendor_analysis'] = self.analyze_politician_vendor_network(
            vendor_cnpjs,
            politician_data.get('name', 'Unknown')
        )

        # CPF-based checks (if available)
        politician_cpf = politician_data.get('cpf')
        if politician_cpf:
            print(f"\n👤 CPF-BASED CHECKS: {politician_cpf}")

            # Check if politician appears in public servant database
            try:
                servant_data = self.get_public_servants(cpf=politician_cpf)
                cross_ref['servant_records'] = servant_data
                print(f"  ✓ Public servant records: {len(servant_data) if servant_data else 0}")
            except Exception as e:
                print(f"  ✗ Error checking servant records: {e}")

            # Check nepotism register
            try:
                nepotism_data = self.get_nepotism_register(cpf=politician_cpf)
                cross_ref['nepotism_records'] = nepotism_data
                print(f"  ✓ Nepotism records: {len(nepotism_data) if nepotism_data else 0}")
            except Exception as e:
                print(f"  ✗ Error checking nepotism: {e}")

        # Calculate transparency score
        transparency_factors = []

        # Vendor network factor
        vendor_risk = cross_ref['vendor_analysis'].get('risk_assessment', 'LOW')
        if vendor_risk == 'LOW':
            transparency_factors.append(0.4)
        elif vendor_risk == 'MEDIUM':
            transparency_factors.append(0.2)
        else:  # HIGH
            transparency_factors.append(0.0)

        # Additional factors based on records found
        if not cross_ref.get('nepotism_records'):
            transparency_factors.append(0.3)

        if cross_ref.get('servant_records'):
            transparency_factors.append(0.3)  # Transparency if appearing in servant DB

        cross_ref['overall_transparency_score'] = sum(transparency_factors)

        print(f"\n📊 TRANSPARENCY SCORE: {cross_ref['overall_transparency_score']:.2f}")

        return cross_ref


def test_portal_transparencia_integration():
    """
    Test Portal da Transparência integration with Arthur Lira's vendor network
    """
    print("💼 PORTAL DA TRANSPARÊNCIA INTEGRATION TEST")
    print("=" * 60)

    try:
        client = PortalTransparenciaClient()
        print("✅ API client initialized successfully")

        # Test with Arthur Lira data (using saved results)
        arthur_lira_data = {
            'name': 'Arthur Lira',
            'cpf': '67821090425',  # From TSE integration
            'party': 'PP',
            'state': 'AL'
        }

        # Sample CNPJs from Arthur Lira's expenses (from previous discovery)
        sample_cnpjs = [
            '29032820000147',
            '04735992000156',
            '05459764000163',
            '48949641000113',
            '08886885000180'
        ]

        print(f"Testing with {len(sample_cnpjs)} sample CNPJs from Arthur Lira's expenses")

        # Run complete cross-reference
        cross_ref_result = client.cross_reference_politician(arthur_lira_data, sample_cnpjs)

        return cross_ref_result

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return {'error': str(e)}


if __name__ == "__main__":
    # Run Portal da Transparência integration test
    result = test_portal_transparencia_integration()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"portal_transparencia_test_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Results saved to: {filename}")

    if 'error' not in result:
        vendor_analysis = result.get('vendor_analysis', {})
        print(f"\n📈 FINAL SUMMARY:")
        print(f"   Politician: {result['politician_data']['name']}")
        print(f"   Vendors analyzed: {vendor_analysis.get('total_vendors', 0)}")
        print(f"   Sanctioned vendors: {len(vendor_analysis.get('sanctioned_vendors', []))}")
        print(f"   Government contractors: {len(vendor_analysis.get('government_contractors', []))}")
        print(f"   Risk assessment: {vendor_analysis.get('risk_assessment', 'UNKNOWN')}")
        print(f"   Transparency score: {result.get('overall_transparency_score', 0):.2f}")