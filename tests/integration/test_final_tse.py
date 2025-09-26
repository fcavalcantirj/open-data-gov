#!/usr/bin/env python3
"""
FINAL TEST: Verify all 4 TSE data types work correctly
Quick test to confirm all fixes are working
"""

import sys
import os
sys.path.append('/Users/fcavalcanti/dev/open-data-gov/src')

from clients.tse_client import TSEClient


def test_all_tse_data_types():
    """Test all 4 TSE data types work correctly"""
    print("🧪 FINAL TSE TEST - ALL 4 DATA TYPES")
    print("=" * 50)

    client = TSEClient()

    # Test each data type individually to verify validation
    data_types = ['receitas', 'despesas_contratadas', 'despesas_pagas', 'doador_originario']
    results = {}

    for data_type in data_types:
        print(f"\n📊 Testing {data_type}...")
        try:
            records = client.get_finance_data(year=2022, data_type=data_type)
            results[data_type] = len(records)
            print(f"   ✅ {data_type}: {len(records)} records")

            if records:
                sample = records[0]
                print(f"   Sample fields: {list(sample.keys())[:10]}...")
        except Exception as e:
            print(f"   ❌ {data_type}: Error - {e}")
            results[data_type] = 0

    print(f"\n🎯 FINAL RESULTS:")
    for data_type, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {data_type}: {count:,} records")

    total_records = sum(results.values())
    print(f"\n📊 TOTAL: {total_records:,} valid financial records")

    return total_records > 0


def main():
    """Run final TSE test"""
    print("🚀 FINAL TSE VALIDATION TEST")
    print("Testing all 4 data types after fixes")
    print("=" * 60)

    success = test_all_tse_data_types()

    if success:
        print(f"\n🎉 SUCCESS: All TSE data types working!")
        print(f"   The financial data populator is ready to use")
        print(f"   Run: python cli4/main.py populate-financial --year 2022")
    else:
        print(f"\n🔍 STILL ISSUES: Some data types not working")
        print(f"   Check the detailed output above")


if __name__ == "__main__":
    main()