#!/usr/bin/env python3
import requests
import json

base_url = 'https://dadosabertos.camara.leg.br/api/v2/'
deputy_id = 160541

# Get full response schemas for working endpoints
working_endpoints = {
    'deputado_base': f'{base_url}deputados/{deputy_id}',
    'deputado_despesas': f'{base_url}deputados/{deputy_id}/despesas?ano=2024&itens=1',
    'deputado_eventos': f'{base_url}deputados/{deputy_id}/eventos?itens=1',
    'deputado_ocupacoes': f'{base_url}deputados/{deputy_id}/ocupacoes',
    'deputado_orgaos': f'{base_url}deputados/{deputy_id}/orgaos',
    'deputado_frentes': f'{base_url}deputados/{deputy_id}/frentes',
    'deputado_profissoes': f'{base_url}deputados/{deputy_id}/profissoes'
}

print('# CÂMARA API - DEPUTADO RESPONSE SCHEMAS')
print()

for endpoint_name, url in working_endpoints.items():
    print(f'## {endpoint_name.upper()} RESPONSE SCHEMA')
    print()

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Pretty print the JSON response
            print('```json')
            if 'dados' in data and data['dados']:
                # Show the actual data structure
                if isinstance(data['dados'], list) and data['dados']:
                    sample = data['dados'][0]
                    print(json.dumps(sample, indent=2, ensure_ascii=False))
                else:
                    print(json.dumps(data['dados'], indent=2, ensure_ascii=False))
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            print('```')

        else:
            print(f'Error {response.status_code}: {response.text[:100]}')

    except Exception as e:
        print(f'Error: {e}')

    print()
    print('---')
    print()