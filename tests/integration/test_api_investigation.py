#!/usr/bin/env python3
"""
DEEP API INVESTIGATION: Portal da Transparência CEIS
Investigate if we're really getting only 15 records total
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def deep_api_investigation():
    """Deep investigation of the CEIS API"""

    api_key = os.getenv('PORTAL_TRANSPARENCIA_API_KEY')
    session = requests.Session()
    session.headers.update({
        'chave-api-dados': api_key,
        'User-Agent': 'CLI4-API-Investigation/1.0'
    })

    base_url = "https://api.portaldatransparencia.gov.br/api-de-dados/"

    print("🔍 DEEP API INVESTIGATION")
    print("=" * 60)

    # Test 1: Multiple pages without any filters
    print("Test 1: Checking multiple pages to find total records")
    for page in range(1, 11):  # Check first 10 pages
        url = f"{base_url}ceis"
        response = session.get(url, params={'pagina': page})

        if response.status_code != 200:
            print(f"   Page {page}: HTTP {response.status_code}")
            break

        data = response.json()

        if not data or len(data) == 0:
            print(f"   Page {page}: Empty (end of data)")
            break

        print(f"   Page {page}: {len(data)} records")

        # Show first record ID from each page to see if they're different
        if data:
            first_id = data[0].get('id', 'no_id')
            last_id = data[-1].get('id', 'no_id')
            print(f"      First ID: {first_id}, Last ID: {last_id}")

    print(f"\nTest 2: Check response headers for pagination info")
    response = session.get(f"{base_url}ceis", params={'pagina': 1})
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")

    # Look for pagination headers
    for header in ['X-Total-Count', 'X-Total-Pages', 'Link', 'Content-Range']:
        if header in response.headers:
            print(f"   {header}: {response.headers[header]}")

    print(f"\nTest 3: Try different API endpoints")

    # Test different endpoints that might have sanctions
    endpoints = [
        'ceis',  # Current one we're using
        'empresas-sancionadas',  # Alternative name
        'sancoes',  # Another possibility
        'cnep',  # Nepotism register (different)
    ]

    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = session.get(url, params={'pagina': 1})
            print(f"   /{endpoint}: HTTP {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"      Records: {len(data) if isinstance(data, list) else 'not_list'}")
                if data and isinstance(data, list) and len(data) > 0:
                    # Show field structure
                    sample = data[0]
                    print(f"      Sample fields: {list(sample.keys())[:8]}")
            elif response.status_code == 404:
                print(f"      Not found")
            else:
                print(f"      Error: {response.text[:100]}")

        except Exception as e:
            print(f"   /{endpoint}: Exception - {e}")

    print(f"\nTest 4: Check official API documentation")

    # Test if there are any query parameters that affect results
    test_params = [
        {'pagina': 1},
        {'pagina': 1, 'tamanhoPagina': 50},  # Try larger page size
        {'pagina': 1, 'ordenacao': 'id'},
        {'pagina': 1, 'formato': 'json'},
    ]

    for params in test_params:
        try:
            response = session.get(f"{base_url}ceis", params=params)
            data = response.json() if response.status_code == 200 else None
            count = len(data) if isinstance(data, list) else 'error'
            print(f"   Params {params}: {count} records")
        except Exception as e:
            print(f"   Params {params}: Exception - {e}")

    print(f"\nTest 5: Compare with known working example")

    # Test a definitely working endpoint for comparison
    try:
        # Try servidores (public servants) which should have many records
        response = session.get(f"{base_url}servidores", params={'pagina': 1})
        if response.status_code == 200:
            data = response.json()
            print(f"   /servidores: {len(data) if isinstance(data, list) else 'not_list'} records")
            print(f"      Working endpoint confirmed")
        else:
            print(f"   /servidores: HTTP {response.status_code}")
    except Exception as e:
        print(f"   /servidores: Exception - {e}")

if __name__ == "__main__":
    deep_api_investigation()