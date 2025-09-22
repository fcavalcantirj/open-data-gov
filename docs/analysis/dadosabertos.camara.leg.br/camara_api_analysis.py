#!/usr/bin/env python3
import requests
import json

base_url = 'https://dadosabertos.camara.leg.br/api/v2/'

# Test deputy ID 160541 (Arthur Lira) on all possible routes
deputy_id = 160541

# All known Câmara API routes
routes = {
    'deputados': {
        'base': 'deputados',
        'description': 'List all deputies',
        'test_url': f'{base_url}deputados?itens=5'
    },
    'deputado_detail': {
        'base': f'deputados/{deputy_id}',
        'description': 'Specific deputy details',
        'test_url': f'{base_url}deputados/{deputy_id}'
    },
    'deputado_despesas': {
        'base': f'deputados/{deputy_id}/despesas',
        'description': 'Deputy expenses (CEAP)',
        'test_url': f'{base_url}deputados/{deputy_id}/despesas?ano=2024&itens=3'
    },
    'deputado_discursos': {
        'base': f'deputados/{deputy_id}/discursos',
        'description': 'Deputy speeches',
        'test_url': f'{base_url}deputados/{deputy_id}/discursos?itens=3'
    },
    'deputado_eventos': {
        'base': f'deputados/{deputy_id}/eventos',
        'description': 'Deputy events/activities',
        'test_url': f'{base_url}deputados/{deputy_id}/eventos?itens=3'
    },
    'deputado_ocupacoes': {
        'base': f'deputados/{deputy_id}/ocupacoes',
        'description': 'Deputy occupations/professions',
        'test_url': f'{base_url}deputados/{deputy_id}/ocupacoes'
    },
    'deputado_orgaos': {
        'base': f'deputados/{deputy_id}/orgaos',
        'description': 'Deputy committee memberships',
        'test_url': f'{base_url}deputados/{deputy_id}/orgaos'
    },
    'deputado_proposicoes': {
        'base': f'deputados/{deputy_id}/proposicoes',
        'description': 'Deputy legislative proposals',
        'test_url': f'{base_url}deputados/{deputy_id}/proposicoes?itens=3'
    },
    'deputado_votacoes': {
        'base': f'deputados/{deputy_id}/votacoes',
        'description': 'Deputy voting records',
        'test_url': f'{base_url}deputados/{deputy_id}/votacoes?itens=3'
    },
    'deputado_frentes': {
        'base': f'deputados/{deputy_id}/frentes',
        'description': 'Deputy parliamentary fronts',
        'test_url': f'{base_url}deputados/{deputy_id}/frentes'
    },
    'partidos': {
        'base': 'partidos',
        'description': 'Political parties',
        'test_url': f'{base_url}partidos?itens=5'
    },
    'proposicoes': {
        'base': 'proposicoes',
        'description': 'Legislative proposals',
        'test_url': f'{base_url}proposicoes?ano=2024&itens=3'
    },
    'votacoes': {
        'base': 'votacoes',
        'description': 'Voting sessions',
        'test_url': f'{base_url}votacoes?ano=2024&itens=3'
    },
    'orgaos': {
        'base': 'orgaos',
        'description': 'Parliamentary committees and organs',
        'test_url': f'{base_url}orgaos?itens=5'
    },
    'eventos': {
        'base': 'eventos',
        'description': 'Parliamentary events',
        'test_url': f'{base_url}eventos?itens=3'
    },
    'legislaturas': {
        'base': 'legislaturas',
        'description': 'Legislative periods',
        'test_url': f'{base_url}legislaturas'
    },
    'blocos': {
        'base': 'blocos',
        'description': 'Parliamentary blocs',
        'test_url': f'{base_url}blocos'
    },
    'frentes': {
        'base': 'frentes',
        'description': 'Parliamentary fronts',
        'test_url': f'{base_url}frentes?itens=3'
    }
}

print('# CÂMARA DOS DEPUTADOS API - COMPLETE ROUTE ANALYSIS')
print('=' * 60)
print(f'Testing with Deputy ID: {deputy_id} (Arthur Lira)')
print(f'Base URL: {base_url}')
print()

for route_name, route_info in routes.items():
    print(f'## {route_name.upper().replace("_", " ")}')
    print(f'**Route:** {route_info["base"]}')
    print(f'**Description:** {route_info["description"]}')
    print(f'**Test URL:** {route_info["test_url"]}')

    try:
        response = requests.get(route_info['test_url'], timeout=10)

        if response.status_code == 200:
            data = response.json()
            print('**Status:** ✅ Working')

            if 'dados' in data:
                dados = data['dados']
                if isinstance(dados, list):
                    print(f'**Response:** List with {len(dados)} items')
                    if dados and isinstance(dados[0], dict):
                        sample_keys = list(dados[0].keys())[:8]
                        keys_str = ', '.join(sample_keys)
                        print(f'**Sample Keys:** {keys_str}...')
                elif isinstance(dados, dict):
                    print('**Response:** Single object')
                    sample_keys = list(dados.keys())[:8]
                    keys_str = ', '.join(sample_keys)
                    print(f'**Keys:** {keys_str}...')
                else:
                    print(f'**Response:** {type(dados)}')
            else:
                print(f'**Response:** {type(data)}')
                if isinstance(data, dict):
                    sample_keys = list(data.keys())[:5]
                    keys_str = ', '.join(sample_keys)
                    print(f'**Keys:** {keys_str}...')
        else:
            print(f'**Status:** ❌ Error {response.status_code}')
            if response.status_code != 404:
                print(f'**Error Details:** {response.text[:100]}')

    except Exception as e:
        print(f'**Status:** ❌ Error: {e}')

    print()