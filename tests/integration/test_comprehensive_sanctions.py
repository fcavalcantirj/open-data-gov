#!/usr/bin/env python3
"""
Test Comprehensive Sanctions Populator
Quick verification that the approach works with Portal da Transparência
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.clients.portal_transparencia_client import PortalTransparenciaClient


def test_all_endpoints():
    """Test all three sanctions endpoints with different parameters"""

    print("🧪 TESTING COMPREHENSIVE SANCTIONS APPROACH")
    print("=" * 60)

    client = PortalTransparenciaClient()

    endpoints = ['ceis', 'cepim', 'cnep']
    test_results = {}

    for endpoint in endpoints:
        print(f"\n📊 Testing {endpoint.upper()} endpoint:")
        print("-" * 40)

        test_results[endpoint] = {}

        # Test 1: Simple pagination
        try:
            response = client.session.get(
                f"{client.base_url}{endpoint}",
                params={'pagina': 1},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                test_results[endpoint]['pagination'] = len(data)
                print(f"  ✅ Pagination: {len(data)} records")

                # Show sample record structure
                sample = data[0]
                print(f"  📋 Sample fields: {list(sample.keys())[:5]}...")

                # Check for CNPJ/CPF fields
                cnpj_fields = [k for k in str(sample).lower() if 'cnpj' in k or 'cpf' in k]
                if cnpj_fields:
                    print(f"  🔑 ID fields found: {cnpj_fields[:3]}...")

            else:
                test_results[endpoint]['pagination'] = 0
                print(f"  ❌ Pagination: Empty response")

        except Exception as e:
            test_results[endpoint]['pagination'] = f"Error: {e}"
            print(f"  ❌ Pagination: Error - {e}")

        # Test 2: State parameter (Alagoas - Arthur Lira's state)
        try:
            response = client.session.get(
                f"{client.base_url}{endpoint}",
                params={'pagina': 1, 'ufSancionado': 'AL'},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                test_results[endpoint]['state_AL'] = len(data)
                print(f"  🌐 State AL: {len(data)} records")
            else:
                test_results[endpoint]['state_AL'] = 0
                print(f"  🌐 State AL: Empty")

        except Exception as e:
            test_results[endpoint]['state_AL'] = f"Error: {e}"
            print(f"  🌐 State AL: Error - {e}")

    # Summary
    print(f"\n🎯 TEST SUMMARY")
    print("=" * 30)

    total_records = 0
    working_endpoints = 0

    for endpoint, results in test_results.items():
        print(f"\n{endpoint.upper()}:")
        for test_type, result in results.items():
            if isinstance(result, int) and result > 0:
                print(f"  ✅ {test_type}: {result} records")
                total_records += result
                working_endpoints += 1
            elif isinstance(result, int):
                print(f"  ⚠️ {test_type}: {result} records")
            else:
                print(f"  ❌ {test_type}: {result}")

    print(f"\nWorking endpoint/parameter combinations: {working_endpoints}")
    print(f"Total sample records found: {total_records}")

    if working_endpoints >= 3:
        print("✅ COMPREHENSIVE APPROACH VIABLE - Multiple endpoints working")
        return True
    else:
        print("⚠️ LIMITED APPROACH - Some endpoints may have issues")
        return False


if __name__ == "__main__":
    success = test_all_endpoints()

    if success:
        print("\n🚀 Ready to run comprehensive sanctions population!")
        print("Command: python cli4/main.py populate-sanctions-comprehensive --max-pages 50")
    else:
        print("\n⚠️ May need parameter strategy adjustments")