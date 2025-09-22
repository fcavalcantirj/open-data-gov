#!/usr/bin/env python3
"""
DEPUTADOS Complete Route Testing
All routes from official Swagger documentation with proper parameters
"""
import requests
import json
import time
from datetime import datetime, timedelta

base_url = 'https://dadosabertos.camara.leg.br/api/v2/'
deputy_id = 160541  # Arthur Lira

def test_all_deputados_routes():
    """Test ALL deputados routes with proper parameters"""
    print('=== COMPLETE DEPUTADOS ROUTES TESTING ===')
    print(f'Deputy ID: {deputy_id}')
    print()

    # Calculate date range for historico route
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    routes = [
        {
            'name': 'deputados',
            'url': f'{base_url}deputados?itens=3',
            'description': 'List and search deputies'
        },
        {
            'name': 'deputados/{id}',
            'url': f'{base_url}deputados/{deputy_id}',
            'description': 'Deputy detailed information'
        },
        {
            'name': 'deputados/{id}/despesas',
            'url': f'{base_url}deputados/{deputy_id}/despesas?ano=2024&itens=3',
            'description': 'Parliamentary expenses (CEAP)'
        },
        {
            'name': 'deputados/{id}/discursos',
            'url': f'{base_url}deputados/{deputy_id}/discursos?itens=3',
            'description': 'Deputy speeches'
        },
        {
            'name': 'deputados/{id}/eventos',
            'url': f'{base_url}deputados/{deputy_id}/eventos?itens=3',
            'description': 'Event participation'
        },
        {
            'name': 'deputados/{id}/frentes',
            'url': f'{base_url}deputados/{deputy_id}/frentes',
            'description': 'Parliamentary fronts membership'
        },
        {
            'name': 'deputados/{id}/historico',
            'url': f'{base_url}deputados/{deputy_id}/historico?dataInicio={start_date}&dataFim={end_date}',
            'description': 'Parliamentary exercise changes (with date range)'
        },
        {
            'name': 'deputados/{id}/mandatosExternos',
            'url': f'{base_url}deputados/{deputy_id}/mandatosExternos',
            'description': 'External elective mandates'
        },
        {
            'name': 'deputados/{id}/ocupacoes',
            'url': f'{base_url}deputados/{deputy_id}/ocupacoes',
            'description': 'Employment and activities'
        },
        {
            'name': 'deputados/{id}/orgaos',
            'url': f'{base_url}deputados/{deputy_id}/orgaos',
            'description': 'Committee memberships'
        },
        {
            'name': 'deputados/{id}/profissoes',
            'url': f'{base_url}deputados/{deputy_id}/profissoes',
            'description': 'Declared professions'
        }
    ]

    results = []

    for route in routes:
        print(f'Testing: {route["name"]}')
        print(f'URL: {route["url"]}')

        try:
            response = requests.get(route['url'], timeout=20)

            if response.status_code == 200:
                data = response.json()

                # Count items
                item_count = 0
                if 'dados' in data:
                    if isinstance(data['dados'], list):
                        item_count = len(data['dados'])
                        print(f'✅ SUCCESS - {item_count} items')
                    else:
                        print('✅ SUCCESS - Single object')
                        item_count = 1
                else:
                    print('✅ SUCCESS - Direct response')

                results.append({
                    'route': route['name'],
                    'status': 'working',
                    'items': item_count
                })

            else:
                print(f'❌ ERROR {response.status_code}')
                results.append({
                    'route': route['name'],
                    'status': f'error_{response.status_code}',
                    'items': 0
                })

        except Exception as e:
            print(f'❌ EXCEPTION: {e}')
            results.append({
                'route': route['name'],
                'status': 'exception',
                'items': 0
            })

        print('-' * 50)
        time.sleep(1)

    print('\n=== SUMMARY ===')
    working = sum(1 for r in results if r['status'] == 'working')
    print(f'Working routes: {working}/{len(results)}')

    for r in results:
        status_icon = '✅' if r['status'] == 'working' else '❌'
        print(f'{status_icon} {r["route"]} - {r["status"]} ({r["items"]} items)')

if __name__ == '__main__':
    test_all_deputados_routes()