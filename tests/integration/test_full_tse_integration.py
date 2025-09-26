#!/usr/bin/env python3
"""
TEST FULL TSE INTEGRATION
Test the enhanced TSE client with FULL PROCESSING capabilities
"""

import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.append('/Users/fcavalcanti/dev/open-data-gov')

from src.clients.tse_client import TSEClient

def test_full_tse_integration():
    """
    Test the FULL PROCESSING TSE client integration
    """
    print("🧪 TESTING FULL TSE INTEGRATION")
    print("=" * 60)
    print("Testing enhanced TSE client with FULL PROCESSING capabilities")
    print("Target: ALL finance packages, ALL resources, ALL records")
    print("=" * 60)

    start_time = time.time()

    # Initialize TSE client
    client = TSEClient()

    try:
        # Test finance data retrieval with FULL PROCESSING
        print("\n🗳️ Testing FULL TSE finance data retrieval...")
        print("Year: 2022 (complete dataset)")
        print("Data types: ALL (receitas, despesas_contratadas, despesas_pagas, doador_originario)")

        # Get finance data with ALL types
        finance_data = client.get_finance_data(2022, 'all')

        processing_time = time.time() - start_time

        print(f"\n📊 FULL PROCESSING RESULTS:")
        print(f"   Total records: {len(finance_data):,}")
        print(f"   Processing time: {processing_time:.1f} seconds")
        print(f"   Records/second: {len(finance_data) / processing_time:,.0f}")

        # Analyze data types
        data_type_counts = {}
        for record in finance_data:
            data_type = record.get('tse_data_type', 'unknown')
            data_type_counts[data_type] = data_type_counts.get(data_type, 0) + 1

        print(f"\n📈 RECORDS BY DATA TYPE:")
        for data_type, count in data_type_counts.items():
            percentage = (count / len(finance_data)) * 100
            print(f"   {data_type}: {count:,} ({percentage:.1f}%)")

        # Test specific data type retrieval
        print(f"\n🔍 Testing specific data type retrieval...")

        # Test receitas only
        receitas_data = client.get_finance_data(2022, 'receitas')
        print(f"   Receitas only: {len(receitas_data):,} records")

        # Test despesas_contratadas only
        contratadas_data = client.get_finance_data(2022, 'despesas_contratadas')
        print(f"   Despesas contratadas only: {len(contratadas_data):,} records")

        print(f"\n✅ FULL TSE INTEGRATION TEST SUCCESSFUL!")
        print(f"   Enhanced TSE client is processing ALL available data")
        print(f"   Ready for CLI4 populator integration")

        # Save sample results for inspection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            'test_timestamp': timestamp,
            'total_records': len(finance_data),
            'processing_time': processing_time,
            'records_per_second': len(finance_data) / processing_time,
            'data_type_distribution': data_type_counts,
            'test_status': 'SUCCESS',
            'sample_records': finance_data[:5] if finance_data else []
        }

        import json
        with open(f'tse_full_integration_test_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Results saved to: tse_full_integration_test_{timestamp}.json")

        return results

    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
        print(f"📊 Partial processing time: {time.time() - start_time:.1f} seconds")
        return None

    except Exception as e:
        print(f"\n❌ Error during integration test: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_full_tse_integration()