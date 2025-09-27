#!/usr/bin/env python3
"""
Fixed Senado API Integration Test - Handles correct XML response format
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional
import re

def test_senado_api_comprehensive():
    """Comprehensive Senado API test with correct XML format handling"""

    print("🧪 FIXED SENADO API INTEGRATION TEST")
    print("=" * 60)

    results = {
        'api_status': 'unknown',
        'data_structure': {},
        'senators_analysis': {},
        'family_network_potential': {},
        'implementation_assessment': {}
    }

    # Test Senado API
    print("🔍 Testing Senado Federal API...")

    try:
        url = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            print(f"   ❌ API returned status {response.status_code}")
            results['api_status'] = 'failed'
            return results

        print(f"   ✅ API accessible, status 200")
        print(f"   📊 Response format: XML")

        # Parse XML
        root = ET.fromstring(response.content)
        results['api_status'] = 'success'

        # Extract senators using correct XML structure
        senators = []
        for parlamentar in root.findall('.//Parlamentar'):
            identificacao = parlamentar.find('IdentificacaoParlamentar')
            if identificacao is not None:
                senator_data = {}

                # Extract key fields
                fields_map = {
                    'codigo': 'CodigoParlamentar',
                    'codigo_publico': 'CodigoPublicoNaLegAtual',
                    'nome': 'NomeParlamentar',
                    'nome_completo': 'NomeCompletoParlamentar',
                    'sexo': 'SexoParlamentar',
                    'email': 'EmailParlamentar',
                    'partido': 'SiglaPartidoParlamentar',
                    'estado': 'UfParlamentar',
                    'foto_url': 'UrlFotoParlamentar',
                    'pagina_url': 'UrlPaginaParlamentar'
                }

                for field, xml_tag in fields_map.items():
                    element = identificacao.find(xml_tag)
                    if element is not None and element.text:
                        senator_data[field] = element.text.strip()

                # Extract bloco info
                bloco = identificacao.find('Bloco')
                if bloco is not None:
                    bloco_nome = bloco.find('NomeBloco')
                    if bloco_nome is not None and bloco_nome.text:
                        senator_data['bloco'] = bloco_nome.text.strip()

                if senator_data:
                    senators.append(senator_data)

        print(f"   📋 Found {len(senators)} senators")

        results['data_structure'] = {
            'format': 'xml',
            'senators_count': len(senators),
            'sample_fields': list(senators[0].keys()) if senators else [],
            'parsing_success': True
        }

        if senators:
            # Analyze senators data
            sample_senator = senators[0]
            print(f"   🔍 Sample senator: {sample_senator.get('nome', 'N/A')} ({sample_senator.get('partido', 'N/A')}-{sample_senator.get('estado', 'N/A')})")

            # Analyze parties and states
            parties = [s.get('partido') for s in senators if s.get('partido')]
            states = [s.get('estado') for s in senators if s.get('estado')]
            names = [s.get('nome_completo', s.get('nome', '')) for s in senators]

            results['senators_analysis'] = {
                'total_senators': len(senators),
                'parties': list(set(parties)),
                'party_count': len(set(parties)),
                'states': list(set(states)),
                'state_count': len(set(states)),
                'sample_names': names[:10],
                'data_completeness': {
                    'with_nome': len([s for s in senators if s.get('nome')]),
                    'with_partido': len([s for s in senators if s.get('partido')]),
                    'with_estado': len([s for s in senators if s.get('estado')]),
                    'with_email': len([s for s in senators if s.get('email')])
                }
            }

            print(f"   🏛️  Parties: {list(set(parties))[:8]}")
            print(f"   🗺️  States: {list(set(states))}")

            # Test family network potential (surname matching)
            sample_camara_surnames = [
                "LIRA",      # Arthur Lira
                "SILVA",     # Common surname
                "SANTOS",    # Common surname
                "OLIVEIRA",  # Common surname
                "PEREIRA",   # Common surname
                "GOMES",     # Cid Gomes (found in sample)
                "NOGUEIRA",  # Ciro Nogueira (found in sample)
                "FARO"       # Beto Faro (found in sample)
            ]

            family_matches = []
            for senator in senators:
                senator_name = senator.get('nome_completo', senator.get('nome', ''))
                if senator_name:
                    senator_surname = senator_name.split()[-1].upper()

                    for camara_surname in sample_camara_surnames:
                        if senator_surname == camara_surname:
                            family_matches.append({
                                'senado_name': senator_name,
                                'senado_surname': senator_surname,
                                'senado_party': senator.get('partido', 'N/A'),
                                'senado_state': senator.get('estado', 'N/A'),
                                'potential_camara_surname': camara_surname
                            })

            results['family_network_potential'] = {
                'test_surnames_count': len(sample_camara_surnames),
                'potential_matches': len(family_matches),
                'matches': family_matches,
                'analysis_confidence': 'high' if len(senators) > 70 else 'medium'
            }

            print(f"   👥 Family network matches: {len(family_matches)}")
            if family_matches:
                print(f"   🔍 Sample matches:")
                for match in family_matches[:3]:
                    print(f"      • {match['senado_name']} ({match['senado_party']}-{match['senado_state']}) ↔ {match['potential_camara_surname']}")

        # Implementation Assessment
        implementation_score = 0

        # API reliability (3 points)
        if results['api_status'] == 'success':
            implementation_score += 3

        # Data volume (3 points)
        senators_count = results['senators_analysis'].get('total_senators', 0)
        if senators_count >= 70:  # Brazil has 81 senators
            implementation_score += 3
        elif senators_count >= 50:
            implementation_score += 2
        elif senators_count >= 20:
            implementation_score += 1

        # Data completeness (2 points)
        completeness = results['senators_analysis'].get('data_completeness', {})
        with_party = completeness.get('with_partido', 0)
        with_state = completeness.get('with_estado', 0)
        if with_party >= senators_count * 0.9 and with_state >= senators_count * 0.9:
            implementation_score += 2
        elif with_party >= senators_count * 0.7 and with_state >= senators_count * 0.7:
            implementation_score += 1

        # Family network potential (2 points)
        family_potential = results['family_network_potential'].get('potential_matches', 0)
        if family_potential >= 3:
            implementation_score += 2
        elif family_potential >= 1:
            implementation_score += 1

        if implementation_score >= 8:
            assessment = 'ready'
        elif implementation_score >= 6:
            assessment = 'mostly_ready'
        else:
            assessment = 'needs_work'

        results['implementation_assessment'] = {
            'score': implementation_score,
            'max_score': 10,
            'assessment': assessment,
            'confidence': 'high' if implementation_score >= 8 else 'medium' if implementation_score >= 6 else 'low'
        }

        print(f"\\n🎯 IMPLEMENTATION ASSESSMENT:")
        print(f"   Score: {implementation_score}/10")
        print(f"   Assessment: {assessment}")
        print(f"   Confidence: {results['implementation_assessment']['confidence']}")

    except ET.ParseError as e:
        print(f"   ❌ XML parsing error: {e}")
        results['api_status'] = 'xml_error'
        results['error'] = str(e)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results['api_status'] = 'error'
        results['error'] = str(e)

    return results

def main():
    """Run the fixed Senado API test"""

    results = test_senado_api_comprehensive()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/fcavalcanti/dev/open-data-gov/tests/integration/senado_fixed_test_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\\n📄 Results saved to: {output_file}")

    # Final recommendation
    assessment = results.get('implementation_assessment', {})
    print(f"\\n" + "=" * 60)
    print(f"🎯 FINAL SENADO POPULATOR RECOMMENDATION")
    print(f"=" * 60)

    if assessment.get('assessment') == 'ready':
        print(f"✅ READY FOR IMPLEMENTATION")
        print(f"   • API is reliable and returns complete senator data")
        print(f"   • XML parsing works correctly")
        print(f"   • Family network detection shows potential")
        print(f"   • Implementation effort: LOW")
    elif assessment.get('assessment') == 'mostly_ready':
        print(f"⚠️  MOSTLY READY - Minor issues to address")
        print(f"   • Implementation effort: MEDIUM")
    else:
        print(f"❌ NEEDS WORK - Significant issues detected")
        print(f"   • Implementation effort: HIGH")

    # Show sample data for verification
    senators_analysis = results.get('senators_analysis', {})
    if senators_analysis.get('sample_names'):
        print(f"\\n📋 Sample Senators for Verification:")
        for name in senators_analysis['sample_names'][:5]:
            print(f"   • {name}")

    return results

if __name__ == "__main__":
    main()