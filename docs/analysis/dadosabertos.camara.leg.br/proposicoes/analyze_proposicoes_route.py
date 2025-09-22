#!/usr/bin/env python3
"""
PROPOSICOES Route Analysis
Systematic testing of /proposicoes endpoint and all sub-routes
"""
import requests
import json
import time

base_url = 'https://dadosabertos.camara.leg.br/api/v2/'

def get_sample_proposicao_id():
    """Get a real proposição ID to test sub-routes"""
    print('=== GETTING SAMPLE PROPOSICAO ID ===')

    try:
        response = requests.get(f'{base_url}proposicoes?itens=1', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'dados' in data and data['dados']:
                proposicao_id = data['dados'][0]['id']
                proposicao_name = data['dados'][0].get('siglaTipo', '') + ' ' + str(data['dados'][0].get('numero', ''))
                print(f'Sample Proposição ID: {proposicao_id} ({proposicao_name})')
                return proposicao_id
    except Exception as e:
        print(f'Error getting sample ID: {e}')

    # Fallback to a known ID
    return 2366805

def test_main_proposicoes_route():
    """Test main /proposicoes endpoint with different parameters"""
    print('=== PROPOSICOES MAIN ROUTE ANALYSIS ===')
    print()

    test_cases = [
        {
            'name': 'proposicoes_basic',
            'params': {'itens': 3},
            'description': 'Basic propositions list'
        },
        {
            'name': 'proposicoes_by_year',
            'params': {'ano': 2024, 'itens': 3},
            'description': 'Propositions by year'
        },
        {
            'name': 'proposicoes_by_type',
            'params': {'siglaTipo': 'PL', 'itens': 3},
            'description': 'Propositions by type (PL)'
        },
        {
            'name': 'proposicoes_by_author',
            'params': {'autor': 'Arthur Lira', 'itens': 3},
            'description': 'Propositions by author name'
        },
        {
            'name': 'proposicoes_by_tema',
            'params': {'codTema': '40', 'itens': 3},
            'description': 'Propositions by theme'
        },
        {
            'name': 'proposicoes_by_keywords',
            'params': {'palavraChave': 'corrupção', 'itens': 3},
            'description': 'Propositions by keywords'
        },
        {
            'name': 'proposicoes_by_situation',
            'params': {'codSituacao': '100', 'itens': 3},
            'description': 'Propositions by situation'
        },
        {
            'name': 'proposicoes_order_by_date',
            'params': {'ordenarPor': 'dataApresentacao', 'ordem': 'desc', 'itens': 3},
            'description': 'Propositions ordered by date'
        }
    ]

    for test in test_cases:
        print(f'## {test["name"].upper()}')
        print(f'Description: {test["description"]}')

        try:
            response = requests.get(f'{base_url}proposicoes', params=test['params'], timeout=15)

            if response.status_code == 200:
                data = response.json()
                if 'dados' in data and data['dados']:
                    print(f'✅ WORKING - {len(data["dados"])} results')

                    # Show sample data
                    sample = data['dados'][0]
                    if 'siglaTipo' in sample and 'numero' in sample:
                        print(f'   Sample: {sample["siglaTipo"]} {sample["numero"]} - {sample.get("ementa", "")[:50]}...')
                else:
                    print('✅ WORKING - No results')
            else:
                print(f'❌ ERROR {response.status_code}: {response.text[:100]}')

        except Exception as e:
            print(f'❌ EXCEPTION: {e}')

        print()
        time.sleep(1)

def test_proposicoes_sub_routes(proposicao_id):
    """Test all sub-routes for a specific proposição"""
    print(f'=== PROPOSICOES SUB-ROUTES ANALYSIS ===')
    print(f'Testing with Proposição ID: {proposicao_id}')
    print()

    # All sub-routes from Swagger documentation
    sub_routes = {
        'proposicao_detail': {
            'url': f'{base_url}proposicoes/{proposicao_id}',
            'description': 'Detailed proposition information'
        },
        'proposicao_autores': {
            'url': f'{base_url}proposicoes/{proposicao_id}/autores',
            'description': 'Proposition authors/entities'
        },
        'proposicao_relacionadas': {
            'url': f'{base_url}proposicoes/{proposicao_id}/relacionadas',
            'description': 'Related propositions'
        },
        'proposicao_temas': {
            'url': f'{base_url}proposicoes/{proposicao_id}/temas',
            'description': 'Proposition thematic areas'
        },
        'proposicao_tramitacoes': {
            'url': f'{base_url}proposicoes/{proposicao_id}/tramitacoes',
            'description': 'Proposition processing history'
        },
        'proposicao_votacoes': {
            'url': f'{base_url}proposicoes/{proposicao_id}/votacoes',
            'description': 'Votes on specific proposition'
        }
    ]

    for route_name, route_info in sub_routes.items():
        print(f'## {route_name.upper()}')
        print(f'Description: {route_info["description"]}')
        print(f'URL: {route_info["url"]}')

        try:
            response = requests.get(route_info['url'], timeout=15)

            if response.status_code == 200:
                data = response.json()
                print('Status: ✅ WORKING')

                if 'dados' in data:
                    dados = data['dados']

                    if isinstance(dados, list):
                        print(f'Response: List with {len(dados)} items')
                        if dados and isinstance(dados[0], dict):
                            keys = list(dados[0].keys())[:4]
                            print(f'Sample fields: {", ".join(keys)}...')
                    else:
                        print('Response: Single object')
                        if isinstance(dados, dict):
                            keys = list(dados.keys())[:6]
                            print(f'Fields: {", ".join(keys)}...')

            else:
                print(f'Status: ❌ ERROR {response.status_code}')
                if response.text:
                    print(f'Error: {response.text[:100]}')

        except Exception as e:
            print(f'Status: ❌ EXCEPTION: {e}')

        print()
        print('-' * 40)
        print()

def test_advanced_proposicoes_features():
    """Test advanced features and complex queries"""
    print('=== ADVANCED PROPOSICOES FEATURES ===')
    print()

    advanced_tests = [
        {
            'name': 'multiple_types',
            'params': {'siglaTipo': 'PL,PEC', 'ano': 2024, 'itens': 3},
            'description': 'Multiple proposition types'
        },
        {
            'name': 'date_range',
            'params': {'dataInicio': '2024-01-01', 'dataFim': '2024-12-31', 'itens': 3},
            'description': 'Date range filter'
        },
        {
            'name': 'complex_author_search',
            'params': {'autor': 'Lira', 'siglaTipo': 'PL', 'ano': 2024, 'itens': 3},
            'description': 'Complex author + type + year search'
        }
    ]

    for test in advanced_tests:
        print(f'## {test["name"].upper()}')
        print(f'Description: {test["description"]}')

        try:
            response = requests.get(f'{base_url}proposicoes', params=test['params'], timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'dados' in data:
                    print(f'✅ WORKING - {len(data["dados"])} results')
                else:
                    print('✅ WORKING - No data structure')
            else:
                print(f'❌ ERROR {response.status_code}: {response.text[:100]}')

        except Exception as e:
            print(f'❌ EXCEPTION: {e}')

        print()

if __name__ == "__main__":
    # Get a real proposição ID first
    proposicao_id = get_sample_proposicao_id()
    print()

    # Test main route
    test_main_proposicoes_route()

    # Test sub-routes with real ID
    test_proposicoes_sub_routes(proposicao_id)

    # Test advanced features
    test_advanced_proposicoes_features()