#!/usr/bin/env python3
"""
Comprehensive Senado API Integration Test
Tests all aspects needed for Senado politicians populator implementation
"""

import requests
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional
import re

class SenadoAPITester:
    """Comprehensive Senado API testing for populator implementation"""

    def __init__(self):
        self.base_url = "https://legis.senado.leg.br/dadosabertos/"
        self.endpoints = {
            'senators': 'senador/lista/atual',
            'senator_detail': 'senador/{codigo}',  # {codigo} will be replaced
        }
        self.test_results = {
            'api_connectivity': {},
            'data_structure': {},
            'data_volume': {},
            'data_quality': {},
            'family_network_potential': {},
            'implementation_readiness': {}
        }

    def test_api_connectivity(self) -> Dict:
        """Test Senado API endpoints for reliability"""
        print("🔗 Testing Senado API Connectivity...")

        connectivity_results = {}

        # Test senators list endpoint
        url = f"{self.base_url}{self.endpoints['senators']}"

        try:
            start_time = time.time()
            response = requests.get(url, timeout=30)
            response_time = time.time() - start_time

            connectivity_results['senators_list'] = {
                'url': url,
                'status_code': response.status_code,
                'response_time': response_time,
                'success': response.status_code == 200,
                'content_length': len(response.content) if response.status_code == 200 else 0,
                'content_type': response.headers.get('content-type', 'unknown')
            }

            if response.status_code == 200:
                print(f"   ✅ senators_list: {response.status_code} ({response_time:.2f}s)")
            else:
                print(f"   ❌ senators_list: {response.status_code}")

        except Exception as e:
            connectivity_results['senators_list'] = {
                'url': url,
                'error': str(e),
                'success': False
            }
            print(f"   ❌ senators_list: Error - {e}")

        self.test_results['api_connectivity'] = connectivity_results
        return connectivity_results

    def test_senators_data_structure(self) -> Dict:
        """Test Senado senators data structure for database compatibility"""
        print("📊 Testing Senado Senators Data Structure...")

        try:
            url = f"{self.base_url}{self.endpoints['senators']}"
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                return {'error': f'API returned status {response.status_code}'}

            # Parse XML response
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                return {'error': f'XML parsing failed: {e}'}

            structure_analysis = {
                'response_format': 'xml',
                'root_element': root.tag,
                'total_senators': 0,
                'sample_senator': {},
                'field_analysis': {},
                'name_analysis': {},
                'party_analysis': {},
                'state_analysis': {}
            }

            # Find senators in XML structure
            senators = []

            # Common XML structures for Senado API
            for senator_elem in root.findall('.//Senador') + root.findall('.//senador'):
                senator_data = {}
                for child in senator_elem:
                    # Handle both text content and attributes
                    if child.text and child.text.strip():
                        senator_data[child.tag] = child.text.strip()

                    # Also check attributes
                    for attr_name, attr_value in child.attrib.items():
                        senator_data[f"{child.tag}_{attr_name}"] = attr_value

                    # Handle nested elements
                    if len(child) > 0:
                        for nested in child:
                            if nested.text and nested.text.strip():
                                senator_data[f"{child.tag}_{nested.tag}"] = nested.text.strip()

                if senator_data:
                    senators.append(senator_data)

            # Alternative: check if it's a different structure
            if not senators:
                # Try alternative XML paths
                for elem in root.iter():
                    if elem.tag.lower() in ['senador', 'senator', 'parlamentar']:
                        senator_data = {}
                        for attr_name, attr_value in elem.attrib.items():
                            senator_data[attr_name] = attr_value
                        if elem.text and elem.text.strip():
                            senator_data['text_content'] = elem.text.strip()
                        if senator_data:
                            senators.append(senator_data)

            structure_analysis['total_senators'] = len(senators)

            if senators:
                sample_senator = senators[0]
                structure_analysis['sample_senator'] = sample_senator

                # Analyze field types and content
                for field, value in sample_senator.items():
                    structure_analysis['field_analysis'][field] = {
                        'type': type(value).__name__,
                        'sample_value': str(value)[:100] if value else None,
                        'is_null': value is None
                    }

                # Analyze names for family network potential
                names = []
                parties = []
                states = []

                for senator in senators[:20]:  # Sample first 20
                    # Extract name variants
                    name_fields = ['Nome', 'nome', 'NomeCompleto', 'nome_completo', 'NomeParlamentar', 'nome_parlamentar']
                    for field in name_fields:
                        if field in senator and senator[field]:
                            names.append(str(senator[field]))
                            break

                    # Extract party
                    party_fields = ['Partido', 'partido', 'SiglaPartido', 'sigla_partido']
                    for field in party_fields:
                        if field in senator and senator[field]:
                            parties.append(str(senator[field]))
                            break

                    # Extract state
                    state_fields = ['UF', 'uf', 'Estado', 'estado', 'SiglaUf', 'sigla_uf']
                    for field in state_fields:
                        if field in senator and senator[field]:
                            states.append(str(senator[field]))
                            break

                structure_analysis['name_analysis'] = {
                    'total_names': len(names),
                    'sample_names': names[:10],
                    'unique_names': len(set(names))
                }

                structure_analysis['party_analysis'] = {
                    'total_parties': len(set(parties)),
                    'parties': list(set(parties))[:10]
                }

                structure_analysis['state_analysis'] = {
                    'total_states': len(set(states)),
                    'states': list(set(states))
                }

                print(f"   📋 Found {len(senators)} senators")
                print(f"   🏛️  Sample fields: {list(sample_senator.keys())[:10]}")
                print(f"   🏛️  Parties: {list(set(parties))[:5]}")
                print(f"   🗺️  States: {list(set(states))[:10]}")

            else:
                print(f"   ⚠️  No senators found in XML structure")
                print(f"   🔍 Root element: {root.tag}")
                print(f"   🔍 Available elements: {[elem.tag for elem in root.iter()][:20]}")

            self.test_results['data_structure'] = structure_analysis
            return structure_analysis

        except Exception as e:
            error_result = {'error': str(e)}
            self.test_results['data_structure'] = error_result
            return error_result

    def test_family_network_potential(self) -> Dict:
        """Test potential for family network detection between Câmara and Senado"""
        print("👥 Testing Family Network Detection Potential...")

        try:
            # Sample politician surnames from Câmara (these should be from actual database)
            sample_camara_surnames = [
                "LIRA",      # Arthur Lira
                "SILVA",     # Common surname
                "SANTOS",    # Common surname
                "OLIVEIRA",  # Common surname
                "PEREIRA"    # Common surname
            ]

            url = f"{self.base_url}{self.endpoints['senators']}"
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                return {'error': f'API returned status {response.status_code}'}

            # Parse senators data (similar to previous function)
            root = ET.fromstring(response.content)
            senators = []

            for senator_elem in root.findall('.//Senador') + root.findall('.//senador'):
                senator_data = {}
                for child in senator_elem:
                    if child.text and child.text.strip():
                        senator_data[child.tag] = child.text.strip()
                if senator_data:
                    senators.append(senator_data)

            family_analysis = {
                'total_senators_checked': len(senators),
                'potential_family_matches': 0,
                'surname_matches': [],
                'analysis_confidence': 'unknown'
            }

            surname_matches = []

            for senator in senators:
                # Extract senator name
                senator_name = ""
                name_fields = ['Nome', 'nome', 'NomeCompleto', 'nome_completo']
                for field in name_fields:
                    if field in senator and senator[field]:
                        senator_name = str(senator[field])
                        break

                if senator_name:
                    # Extract surname (last name)
                    senator_surname = senator_name.split()[-1].upper() if senator_name else ""

                    # Check for matches with Câmara surnames
                    for camara_surname in sample_camara_surnames:
                        if senator_surname == camara_surname:
                            surname_matches.append({
                                'senado_name': senator_name,
                                'senado_surname': senator_surname,
                                'camara_surname': camara_surname,
                                'potential_family_connection': True
                            })

            family_analysis['potential_family_matches'] = len(surname_matches)
            family_analysis['surname_matches'] = surname_matches[:10]

            # Determine analysis confidence
            if len(senators) > 50:
                family_analysis['analysis_confidence'] = 'high'
            elif len(senators) > 20:
                family_analysis['analysis_confidence'] = 'medium'
            else:
                family_analysis['analysis_confidence'] = 'low'

            print(f"   📊 Senators analyzed: {len(senators)}")
            print(f"   👥 Potential family matches: {len(surname_matches)}")

            if surname_matches:
                print(f"   🔍 Sample matches:")
                for match in surname_matches[:3]:
                    print(f"      • {match['senado_name']} (Senado) ↔ {match['camara_surname']} (Câmara)")

            self.test_results['family_network_potential'] = family_analysis
            return family_analysis

        except Exception as e:
            error_result = {'error': str(e)}
            self.test_results['family_network_potential'] = error_result
            return error_result

    def generate_implementation_readiness_report(self) -> Dict:
        """Generate final implementation readiness assessment for Senado populator"""
        print("📋 Generating Senado Implementation Readiness Report...")

        readiness_report = {
            'overall_readiness': 'unknown',
            'api_reliability': 'unknown',
            'data_quality': 'unknown',
            'family_network_viability': 'unknown',
            'implementation_risks': [],
            'implementation_recommendations': [],
            'estimated_effort': 'unknown'
        }

        # Assess API reliability
        connectivity = self.test_results.get('api_connectivity', {})
        if connectivity.get('senators_list', {}).get('success', False):
            readiness_report['api_reliability'] = 'high'
        else:
            readiness_report['api_reliability'] = 'failed'

        # Assess data quality
        data_structure = self.test_results.get('data_structure', {})
        total_senators = data_structure.get('total_senators', 0)

        if total_senators >= 70:  # Brazil has 81 senators
            readiness_report['data_quality'] = 'high'
        elif total_senators >= 50:
            readiness_report['data_quality'] = 'medium'
        else:
            readiness_report['data_quality'] = 'low'

        # Assess family network viability
        family_potential = self.test_results.get('family_network_potential', {})
        confidence = family_potential.get('analysis_confidence', 'unknown')
        readiness_report['family_network_viability'] = confidence

        # Generate risks and recommendations
        if readiness_report['api_reliability'] == 'failed':
            readiness_report['implementation_risks'].append('API connectivity issues')

        if readiness_report['data_quality'] == 'low':
            readiness_report['implementation_risks'].append('Insufficient senator data volume')

        if data_structure.get('response_format') == 'xml':
            readiness_report['implementation_recommendations'].append('Implement XML parsing for senator data')

        # Overall readiness assessment
        high_scores = sum([1 for score in [readiness_report['api_reliability'], readiness_report['data_quality'], readiness_report['family_network_viability']] if score == 'high'])
        medium_scores = sum([1 for score in [readiness_report['api_reliability'], readiness_report['data_quality'], readiness_report['family_network_viability']] if score == 'medium'])

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
        """Run all Senado tests and generate final report"""
        print("🧪 COMPREHENSIVE SENADO API INTEGRATION TEST")
        print("=" * 60)

        # Run all test phases
        self.test_api_connectivity()
        print()

        self.test_senators_data_structure()
        print()

        self.test_family_network_potential()
        print()

        self.generate_implementation_readiness_report()
        print()

        return self.test_results

def main():
    """Run comprehensive Senado API integration test"""
    tester = SenadoAPITester()
    results = tester.run_comprehensive_test()

    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/fcavalcanti/dev/open-data-gov/tests/integration/senado_comprehensive_test_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"📄 Test results saved to: {output_file}")

    # Print final summary
    readiness = results.get('implementation_readiness', {})
    print("\n" + "=" * 60)
    print("🎯 FINAL SENADO IMPLEMENTATION ASSESSMENT")
    print("=" * 60)
    print(f"Overall Readiness: {readiness.get('overall_readiness', 'unknown')}")
    print(f"Estimated Effort: {readiness.get('estimated_effort', 'unknown')}")
    print(f"API Reliability: {readiness.get('api_reliability', 'unknown')}")
    print(f"Data Quality: {readiness.get('data_quality', 'unknown')}")
    print(f"Family Network Viability: {readiness.get('family_network_viability', 'unknown')}")

    if readiness.get('implementation_risks'):
        print(f"\nRisks Identified:")
        for risk in readiness['implementation_risks']:
            print(f"  ⚠️  {risk}")

    if readiness.get('implementation_recommendations'):
        print(f"\nRecommendations:")
        for rec in readiness['implementation_recommendations']:
            print(f"  💡 {rec}")

    return results

if __name__ == "__main__":
    main()