#!/usr/bin/env python3
"""
TOTAL SCOPE TEST: Find the actual size of the sanctions database
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def find_total_scope():
    """Use binary search to find the last page with data"""

    api_key = os.getenv('PORTAL_TRANSPARENCIA_API_KEY')
    session = requests.Session()
    session.headers.update({
        'chave-api-dados': api_key,
        'User-Agent': 'CLI4-Scope-Test/1.0'
    })

    base_url = "https://api.portaldatransparencia.gov.br/api-de-dados/"

    print("🔍 FINDING TOTAL SCOPE OF SANCTIONS DATABASE")
    print("=" * 60)

    def has_data(page_num):
        """Check if a page has data"""
        try:
            response = session.get(f"{base_url}ceis", params={'pagina': page_num}, timeout=10)
            if response.status_code != 200:
                return False
            data = response.json()
            return isinstance(data, list) and len(data) > 0
        except:
            return False

    # Binary search to find last page
    print("🔍 Using binary search to find last page with data...")

    low = 1
    high = 10000  # Start with reasonable upper bound

    # First, find an upper bound where we know there's no data
    print("   Finding upper bound...")
    test_pages = [100, 500, 1000, 2000, 5000, 10000]

    for test_page in test_pages:
        print(f"   Testing page {test_page}...")
        if has_data(test_page):
            print(f"      ✅ Page {test_page} has data")
            low = test_page
        else:
            print(f"      ❌ Page {test_page} is empty")
            high = test_page
            break

    # Binary search between low and high
    print(f"   Binary search between {low} and {high}...")

    last_page_with_data = low

    while low <= high:
        mid = (low + high) // 2
        print(f"   Testing page {mid}...")

        if has_data(mid):
            print(f"      ✅ Page {mid} has data")
            last_page_with_data = mid
            low = mid + 1
        else:
            print(f"      ❌ Page {mid} is empty")
            high = mid - 1

    print(f"\n🎯 RESULT:")
    print(f"   Last page with data: {last_page_with_data}")
    print(f"   Estimated total records: {last_page_with_data * 15:,}")
    print(f"   Data collection time estimate: {(last_page_with_data * 2)/60:.1f} minutes")

    return last_page_with_data

if __name__ == "__main__":
    find_total_scope()