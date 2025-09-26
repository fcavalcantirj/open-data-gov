#!/usr/bin/env python3
"""
TARGETED TEST: Confirm CNPJ filtering behavior in Portal da Transparência API
"""

import requests
import json
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_cnpj_filtering():
    """Test if CNPJ filtering actually works"""

    api_key = os.getenv('PORTAL_TRANSPARENCIA_API_KEY')
    if not api_key:
        raise ValueError("PORTAL_TRANSPARENCIA_API_KEY not found")

    session = requests.Session()
    session.headers.update({
        'chave-api-dados': api_key,
        'User-Agent': 'CLI4-Sanctions-Targeted-Test/1.0'
    })

    base_url = "https://api.portaldatransparencia.gov.br/api-de-dados/"

    print("🎯 TESTING CNPJ FILTERING BEHAVIOR")
    print("=" * 60)

    # Test 1: No filter (baseline)
    print("Test 1: No CNPJ filter")
    url = f"{base_url}ceis"
    response = session.get(url, params={'pagina': 1})
    no_filter_data = response.json()
    print(f"   Results: {len(no_filter_data)}")
    if no_filter_data:
        first_cnpj = no_filter_data[0]['pessoa']['cnpjFormatado']
        print(f"   First CNPJ: {first_cnpj}")

    # Test 2: Specific CNPJ filter
    specific_cnpj = "24.418.900/0001-11"  # From the previous test results
    print(f"\nTest 2: Filter by specific CNPJ: {specific_cnpj}")
    clean_cnpj = re.sub(r'[^\d]', '', specific_cnpj)
    response = session.get(url, params={'cnpjSancionado': clean_cnpj, 'pagina': 1})
    filtered_data = response.json()
    print(f"   Results: {len(filtered_data)}")
    if filtered_data:
        filtered_cnpjs = [item['pessoa']['cnpjFormatado'] for item in filtered_data]
        unique_cnpjs = set(filtered_cnpjs)
        print(f"   Unique CNPJs: {len(unique_cnpjs)}")
        print(f"   CNPJs found: {list(unique_cnpjs)[:5]}")

        # Check if our target CNPJ is in results
        target_found = any(clean_cnpj in cnpj for cnpj in filtered_cnpjs)
        print(f"   Target CNPJ found: {target_found}")

    # Test 3: Non-existent CNPJ
    print(f"\nTest 3: Filter by non-existent CNPJ")
    fake_cnpj = "99999999999999"
    response = session.get(url, params={'cnpjSancionado': fake_cnpj, 'pagina': 1})
    fake_data = response.json()
    print(f"   Results: {len(fake_data)}")

    print(f"\n🔍 ANALYSIS:")
    print(f"   No filter returns: {len(no_filter_data)}")
    print(f"   Specific CNPJ returns: {len(filtered_data)}")
    print(f"   Fake CNPJ returns: {len(fake_data)}")

    if len(no_filter_data) == len(filtered_data) == len(fake_data):
        print(f"   ⚠️  API appears to ignore CNPJ filter (returns same count)")
        print(f"   💡 May need different API endpoint or parameter name")
    else:
        print(f"   ✅ CNPJ filtering works correctly")

if __name__ == "__main__":
    test_cnpj_filtering()