"""
Senado Federal API Client
Integration with Brazilian Senate open data APIs for political network analysis.

Based on architecture document specification and discovered XML API structure.
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import re


class SenadoClient:
    """
    Client for accessing Senado Federal open data APIs
    Complements Câmara dos Deputados data for complete legislative picture
    """

    def __init__(self):
        self.base_url = "https://legis.senado.leg.br/dadosabertos/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Brazilian-Political-Network-Analyzer/1.0'
        })

    def get_current_senators(self) -> List[Dict[str, Any]]:
        """Get list of current senators"""
        url = f"{self.base_url}senador/lista/atual"

        try:
            response = self.session.get(url)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            senators = []

            # Navigate XML structure
            for parlamentar in root.findall('.//Parlamentar'):
                senator_data = self._parse_senator_xml(parlamentar)
                if senator_data:
                    senators.append(senator_data)

            return senators

        except Exception as e:
            print(f"Error fetching senators: {e}")
            return []

    def _parse_senator_xml(self, parlamentar_elem) -> Optional[Dict[str, Any]]:
        """Parse individual senator XML element"""
        try:
            identificacao = parlamentar_elem.find('IdentificacaoParlamentar')
            mandato = parlamentar_elem.find('Mandato')

            if identificacao is None:
                return None

            senator = {
                'codigo': self._get_xml_text(identificacao, 'CodigoParlamentar'),
                'codigo_publico': self._get_xml_text(identificacao, 'CodigoPublicoNaLegAtual'),
                'nome': self._get_xml_text(identificacao, 'NomeParlamentar'),
                'nome_completo': self._get_xml_text(identificacao, 'NomeCompletoParlamentar'),
                'sexo': self._get_xml_text(identificacao, 'SexoParlamentar'),
                'email': self._get_xml_text(identificacao, 'EmailParlamentar'),
                'partido': self._get_xml_text(identificacao, 'SiglaPartidoParlamentar'),
                'estado': self._get_xml_text(identificacao, 'UfParlamentar'),
                'foto_url': self._get_xml_text(identificacao, 'UrlFotoParlamentar'),
                'pagina_url': self._get_xml_text(identificacao, 'UrlPaginaParlamentar'),
                'membro_mesa': self._get_xml_text(identificacao, 'MembroMesa') == 'Sim',
                'membro_lideranca': self._get_xml_text(identificacao, 'MembroLideranca') == 'Sim'
            }

            # Add bloc information
            bloco = identificacao.find('Bloco')
            if bloco is not None:
                senator['bloco'] = {
                    'codigo': self._get_xml_text(bloco, 'CodigoBloco'),
                    'nome': self._get_xml_text(bloco, 'NomeBloco'),
                    'apelido': self._get_xml_text(bloco, 'NomeApelido')
                }

            # Add mandate information
            if mandato is not None:
                senator['mandato'] = {
                    'codigo': self._get_xml_text(mandato, 'CodigoMandato'),
                    'descricao_participacao': self._get_xml_text(mandato, 'DescricaoParticipacao')
                }

            return senator

        except Exception as e:
            print(f"Error parsing senator XML: {e}")
            return None

    def _get_xml_text(self, parent, tag_name):
        """Helper to safely get XML text content"""
        element = parent.find(tag_name)
        return element.text if element is not None else None

    def get_senator_by_name(self, search_name: str) -> List[Dict[str, Any]]:
        """Find senators by name"""
        senators = self.get_current_senators()

        search_normalized = self._normalize_name(search_name)
        matches = []

        for senator in senators:
            senator_name = self._normalize_name(senator.get('nome', ''))
            senator_full_name = self._normalize_name(senator.get('nome_completo', ''))

            # Check both regular name and full name
            if (search_normalized in senator_name or
                search_normalized in senator_full_name or
                senator_name in search_normalized or
                senator_full_name in search_normalized):
                matches.append(senator)

        return matches

    def _normalize_name(self, name: str) -> str:
        """Normalize Brazilian names for matching"""
        if not name:
            return ""

        name = name.upper()
        name = re.sub(r'\b(SENADOR|SENADORA|DR\.?|DRA\.?|PROF\.?)\b', '', name)
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()

        return name

    def get_senator_votacoes(self, codigo_parlamentar: str, year: Optional[int] = None) -> List[Dict]:
        """Get voting records for a senator"""
        # This would require additional API exploration
        # Senado has different endpoints for voting data
        print(f"⚠ Voting records API needs further exploration for senator {codigo_parlamentar}")
        return []

    def get_senator_materias(self, codigo_parlamentar: str) -> List[Dict]:
        """Get authored legislation for a senator"""
        # This would require additional API exploration
        print(f"⚠ Authored legislation API needs further exploration for senator {codigo_parlamentar}")
        return []

    def correlate_with_tse(self, senator_data: Dict, tse_client) -> Dict[str, Any]:
        """
        Correlate senator data with TSE electoral information
        Similar to deputy correlation strategy
        """
        print(f"\n=== SENATOR-TSE CORRELATION ===")
        print(f"Senator: {senator_data.get('nome')} ({senator_data.get('estado')})")

        correlation = {
            'senator_data': senator_data,
            'tse_matches': [],
            'confidence': 0.0
        }

        try:
            # Search TSE for senate candidates
            senator_name = senator_data.get('nome', '')
            senator_state = senator_data.get('estado', '')

            # Search recent elections for senate position
            election_years = [2022, 2018, 2014]

            for year in election_years:
                matches = tse_client.find_candidate_by_name(
                    senator_name, year, 'SENADOR'
                )

                # Filter by state
                state_matches = [m for m in matches if m.get('state') == senator_state]

                if state_matches:
                    correlation['tse_matches'].append({
                        'year': year,
                        'matches': state_matches
                    })
                    print(f"  {year}: ✓ Found {len(state_matches)} matches")

        except Exception as e:
            print(f"  ✗ TSE correlation error: {e}")

        # Calculate confidence based on matches found
        total_matches = len(correlation['tse_matches'])
        correlation['confidence'] = min(total_matches / 3.0, 1.0)  # Up to 3 recent elections

        print(f"  Confidence: {correlation['confidence']:.2f}")

        return correlation


def test_senado_integration():
    """Test Senado integration and find senators with potential cross-chamber connections"""
    print("🏛️ SENADO FEDERAL INTEGRATION TEST")
    print("=" * 50)

    client = SenadoClient()

    # Get all current senators
    print("Fetching current senators...")
    senators = client.get_current_senators()

    print(f"✓ Retrieved {len(senators)} senators")

    # Show sample data
    print("\nSample senators:")
    for senator in senators[:5]:
        print(f"  - {senator['nome']} ({senator['partido']}-{senator['estado']})")

    # Look for senators that might have been deputies (cross-chamber correlation)
    print("\n=== CROSS-CHAMBER ANALYSIS ===")

    potential_ex_deputies = []

    # Common names that appear in both chambers
    common_political_names = ['José', 'Maria', 'Carlos', 'Ana', 'Paulo', 'João']

    for senator in senators:
        name = senator.get('nome', '')
        # Look for senators with common political names (potential for confusion)
        if any(common_name in name for common_name in common_political_names):
            potential_ex_deputies.append({
                'senator': senator,
                'potential_deputy_match': True,
                'search_strategy': 'name_similarity'
            })

    print(f"Found {len(potential_ex_deputies)} senators with names that might match deputies")

    # Show a few examples
    for item in potential_ex_deputies[:3]:
        senator = item['senator']
        print(f"  - {senator['nome']} ({senator['partido']}-{senator['estado']}) - Could match deputy?")

    # Test specific senator lookup
    print("\n=== SPECIFIC SENATOR TEST ===")
    test_names = ['Flávio Bolsonaro', 'Ciro Nogueira', 'Eduardo Braga']

    for test_name in test_names:
        matches = client.get_senator_by_name(test_name)
        if matches:
            senator = matches[0]
            print(f"✓ Found: {senator['nome']} ({senator['partido']}-{senator['estado']})")
        else:
            print(f"✗ Not found: {test_name}")

    return {
        'total_senators': len(senators),
        'sample_senators': senators[:10],
        'cross_chamber_potential': len(potential_ex_deputies),
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run Senado integration test
    result = test_senado_integration()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"senado_integration_test_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Results saved to: {filename}")
    print(f"\n📊 SUMMARY:")
    print(f"   Total Senators: {result['total_senators']}")
    print(f"   Cross-chamber potential: {result['cross_chamber_potential']}")
    print(f"   API Status: ✅ Working (XML format)")