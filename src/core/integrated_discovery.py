"""
Integrated Discovery: Câmara + TSE
Implementation of the full correlation strategy from brazilian-political-data-architecture-v0.md

This integrates Câmara dos Deputados data with TSE electoral data for complete deputy mapping.
"""

import requests
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ..clients.tse_client import TSEClient


def discover_deputy_complete_universe(deputy_name_or_id: str) -> Dict[str, Any]:
    """
    Complete deputy discovery across Câmara and TSE systems
    Implementation of the correlation strategy from the architecture document
    """

    print(f"🇧🇷 COMPLETE DEPUTY UNIVERSE DISCOVERY")
    print("=" * 60)
    print(f"Target: {deputy_name_or_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    result = {
        'target': deputy_name_or_id,
        'discovery_timestamp': datetime.now().isoformat(),
        'camara_data': {},
        'tse_data': {},
        'correlation': {},
        'networks': {},
        'confidence_score': 0.0
    }

    # === PHASE 1: CÂMARA DOS DEPUTADOS ===
    print("\n🏛️ PHASE 1: CÂMARA DOS DEPUTADOS")
    print("-" * 40)

    try:
        # Search for deputy
        if deputy_name_or_id.isdigit():
            camara_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputy_name_or_id}"
            response = requests.get(camara_url)
        else:
            camara_url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
            response = requests.get(camara_url, params={"nome": deputy_name_or_id})

        response.raise_for_status()
        camara_response = response.json()

        # Handle different response formats
        if 'dados' in camara_response:
            if isinstance(camara_response['dados'], list) and camara_response['dados']:
                deputy_data = camara_response['dados'][0]
            else:
                deputy_data = camara_response['dados']
        else:
            deputy_data = camara_response

        deputy_id = deputy_data['id']
        deputy_name = deputy_data['nome']
        deputy_state = deputy_data.get('siglaUf')
        deputy_party = deputy_data.get('siglaPartido')

        print(f"✓ Deputy Found: {deputy_name}")
        print(f"  ID: {deputy_id}")
        print(f"  Party: {deputy_party}")
        print(f"  State: {deputy_state}")
        print(f"  CPF: {deputy_data.get('cpf', 'Not disclosed')}")

        # Store Câmara data
        result['camara_data'] = {
            'id': deputy_id,
            'name': deputy_name,
            'party': deputy_party,
            'state': deputy_state,
            'cpf': deputy_data.get('cpf'),
            'full_data': deputy_data
        }

        # Get expenses (financial network)
        print(f"\n💰 Financial Network Discovery")
        expenses_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputy_id}/despesas"
        current_year = datetime.now().year

        all_expenses = []
        vendor_cnpjs = set()

        for year in [current_year, current_year - 1]:
            try:
                params = {"ano": year, "itens": 100}
                response = requests.get(expenses_url, params=params)
                response.raise_for_status()

                year_expenses = response.json().get('dados', [])
                all_expenses.extend(year_expenses)

                # Extract CNPJs
                for expense in year_expenses:
                    cnpj_fields = ['cnpjCpfFornecedor', 'cnpj', 'fornecedor_cnpj']
                    for field in cnpj_fields:
                        if field in expense and expense[field]:
                            cnpj = re.sub(r'[^\d]', '', str(expense[field]))
                            if len(cnpj) == 14:
                                vendor_cnpjs.add(cnpj)

            except Exception as e:
                print(f"  ⚠ Error fetching {year} expenses: {e}")

        print(f"  ✓ Expenses: {len(all_expenses)} records")
        print(f"  ✓ Vendor CNPJs: {len(vendor_cnpjs)} unique")

        result['networks']['vendor_cnpjs'] = list(vendor_cnpjs)

        # Get propositions
        print(f"\n📋 Legislative Activity")
        try:
            props_url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
            params = {
                "idDeputadoAutor": deputy_id,
                "dataInicio": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                "itens": 20
            }
            response = requests.get(props_url, params=params)
            response.raise_for_status()

            propositions = response.json().get('dados', [])
            print(f"  ✓ Propositions: {len(propositions)} in last year")

            result['camara_data']['propositions_count'] = len(propositions)
            result['camara_data']['recent_propositions'] = propositions[:5]  # Store sample

        except Exception as e:
            print(f"  ⚠ Error fetching propositions: {e}")

    except Exception as e:
        print(f"❌ Câmara discovery failed: {e}")
        return {'error': f"Câmara discovery failed: {e}"}

    # === PHASE 2: TSE ELECTORAL DATA ===
    print(f"\n🗳️ PHASE 2: TSE ELECTORAL DATA")
    print("-" * 40)

    try:
        tse_client = TSEClient()

        # Get electoral history
        electoral_history = tse_client.get_deputy_electoral_history(deputy_name, deputy_state)

        result['tse_data'] = electoral_history

        # Extract key TSE insights
        tse_elections = electoral_history.get('elections', {})
        print(f"  ✓ Electoral history: {len(tse_elections)} elections found")

        # Get most recent election data
        if tse_elections:
            latest_year = max(tse_elections.keys())
            latest_election = tse_elections[latest_year]

            tse_cpf = latest_election.get('cpf')
            tse_electoral_number = latest_election.get('electoral_number')

            print(f"  ✓ Latest election ({latest_year}):")
            print(f"    Electoral #: {tse_electoral_number}")
            print(f"    CPF: {tse_cpf}")
            print(f"    Confidence: {electoral_history.get('correlation_confidence', 0):.2f}")

        else:
            print(f"  ❌ No electoral data found")

    except Exception as e:
        print(f"⚠ TSE discovery error: {e}")
        result['tse_data'] = {'error': str(e)}

    # === PHASE 3: DATA CORRELATION ===
    print(f"\n🔗 PHASE 3: DATA CORRELATION")
    print("-" * 40)

    correlation = {
        'name_match': False,
        'state_match': False,
        'cpf_match': False,
        'party_consistency': False,
        'temporal_consistency': False
    }

    confidence_factors = []

    # Name correlation
    camara_name = result['camara_data'].get('name', '').upper()
    tse_data = result.get('tse_data', {})

    if tse_data and 'elections' in tse_data:
        latest_elections = list(tse_data['elections'].values())
        if latest_elections:
            latest_tse = latest_elections[0]
            tse_name = latest_tse.get('candidate_data', {}).get('name', '').upper()

            # Name similarity check
            if tse_name and camara_name:
                # Simple check: both names contain key parts
                camara_words = set(camara_name.split())
                tse_words = set(tse_name.split())
                common_words = camara_words.intersection(tse_words)

                if len(common_words) >= 2:  # At least 2 words in common
                    correlation['name_match'] = True
                    confidence_factors.append(0.3)
                    print(f"  ✓ Name correlation: {len(common_words)} words match")

            # State correlation
            camara_state = result['camara_data'].get('state')
            tse_state = latest_tse.get('candidate_data', {}).get('state')

            if camara_state and tse_state and camara_state == tse_state:
                correlation['state_match'] = True
                confidence_factors.append(0.2)
                print(f"  ✓ State match: {camara_state}")

            # CPF correlation (if available)
            camara_cpf = result['camara_data'].get('cpf')
            tse_cpf = latest_tse.get('cpf')

            if camara_cpf and tse_cpf:
                camara_cpf_clean = re.sub(r'[^\d]', '', camara_cpf)
                tse_cpf_clean = re.sub(r'[^\d]', '', tse_cpf)

                if camara_cpf_clean == tse_cpf_clean:
                    correlation['cpf_match'] = True
                    confidence_factors.append(0.4)
                    print(f"  ✓ CPF match: {tse_cpf_clean}")
                else:
                    print(f"  ⚠ CPF mismatch: Câmara={camara_cpf_clean}, TSE={tse_cpf_clean}")

            # Party consistency check
            camara_party = result['camara_data'].get('party')
            recent_tse_parties = set()

            for election_data in tse_data['elections'].values():
                party = election_data.get('party')
                if party:
                    recent_tse_parties.add(party)

            if camara_party in recent_tse_parties:
                correlation['party_consistency'] = True
                confidence_factors.append(0.1)
                print(f"  ✓ Party consistency: {camara_party}")

    # Calculate overall confidence
    overall_confidence = sum(confidence_factors)
    result['confidence_score'] = min(overall_confidence, 1.0)
    result['correlation'] = correlation

    print(f"\n📊 CORRELATION SUMMARY")
    print(f"  Overall Confidence: {result['confidence_score']:.2f}")
    print(f"  Name Match: {correlation['name_match']}")
    print(f"  State Match: {correlation['state_match']}")
    print(f"  CPF Match: {correlation['cpf_match']}")
    print(f"  Party Consistency: {correlation['party_consistency']}")

    # === PHASE 4: NETWORK MAPPING ===
    print(f"\n🕸️ PHASE 4: NETWORK MAPPING")
    print("-" * 40)

    # Entity relationships identified
    entity_map = {
        'politician': {
            'camara_id': result['camara_data'].get('id'),
            'tse_electoral_numbers': [],
            'name_variations': [result['camara_data'].get('name')]
        },
        'financial_entities': len(result['networks'].get('vendor_cnpjs', [])),
        'electoral_cycles': len(tse_data.get('elections', {})),
        'total_relationships': 0
    }

    # Add TSE electoral numbers
    if tse_data and 'elections' in tse_data:
        for election in tse_data['elections'].values():
            electoral_num = election.get('electoral_number')
            if electoral_num:
                entity_map['politician']['tse_electoral_numbers'].append(electoral_num)

    entity_map['total_relationships'] = (
        entity_map['financial_entities'] +
        entity_map['electoral_cycles'] +
        len(entity_map['politician']['tse_electoral_numbers'])
    )

    result['entity_map'] = entity_map

    print(f"  ✓ Entity mapping complete")
    print(f"    Financial entities: {entity_map['financial_entities']}")
    print(f"    Electoral cycles: {entity_map['electoral_cycles']}")
    print(f"    Total relationships: {entity_map['total_relationships']}")

    print(f"\n✅ DISCOVERY COMPLETE")
    print(f"   Confidence Score: {result['confidence_score']:.2f}")
    print(f"   Data Sources: Câmara + TSE")
    print(f"   Entity Relationships: {entity_map['total_relationships']}")

    return result


def test_integrated_discovery():
    """Test integrated discovery with Arthur Lira"""
    print("🔍 INTEGRATED DISCOVERY TEST")
    print("=" * 50)

    # Test with Arthur Lira (as specified in architecture)
    result = discover_deputy_complete_universe("Arthur Lira")

    return result


if __name__ == "__main__":
    # Run the integrated test
    result = test_integrated_discovery()

    # Save comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"integrated_discovery_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Complete results saved to: {filename}")

    # Print summary
    if 'confidence_score' in result:
        print(f"\n📈 FINAL SUMMARY:")
        print(f"   Target: {result.get('target')}")
        print(f"   Confidence: {result['confidence_score']:.2f}")
        print(f"   Financial Network: {len(result.get('networks', {}).get('vendor_cnpjs', []))} CNPJs")
        print(f"   Electoral History: {len(result.get('tse_data', {}).get('elections', {}))} elections")
        print(f"   Total Relationships: {result.get('entity_map', {}).get('total_relationships', 0)}")