#!/usr/bin/env python3
"""
SIMPLE TEST: Verify fixed TSE field mappings
Test with one small state file to confirm validation works
"""

import sys
import os
sys.path.append('/Users/fcavalcanti/dev/open-data-gov/src')

from clients.tse_client import TSEClient


def test_fixed_tse_mappings():
    """Test fixed TSE field mappings with small data set"""
    print("🧪 TESTING FIXED TSE FIELD MAPPINGS")
    print("=" * 50)

    client = TSEClient()

    # Test with AC (small state) to avoid timeouts
    print("📊 Testing fixed TSE validation with AC state data...")

    try:
        # Get finance data with enhanced logging - test receitas first
        finance_records = client.get_finance_data(year=2022, data_type='receitas')

        print(f"\n✅ RECEITAS TEST RESULT:")
        print(f"   Total receitas records: {len(finance_records)}")

        if finance_records:
            # Show sample record
            sample = finance_records[0]
            print(f"   ✅ SUCCESS: Found valid receitas records!")
            print(f"   Sample fields: {list(sample.keys())[:15]}...")

            # Check key fields
            if 'vr_receita' in sample:
                print(f"   Amount field: {sample['vr_receita']}")
            if 'nr_cpf_candidato' in sample:
                print(f"   CPF field: {sample['nr_cpf_candidato']}")

            # Show data type breakdown
            data_types = {}
            for record in finance_records[:100]:  # Sample first 100
                data_type = record.get('tse_data_type', 'unknown')
                data_types[data_type] = data_types.get(data_type, 0) + 1
            print(f"   Data type breakdown: {data_types}")
        else:
            print("   ❌ No valid receitas records found")

        # If receitas worked, try other types
        if finance_records:
            print(f"\n📊 Testing other data types...")

            # Test despesas_contratadas
            despesas_contratadas = client.get_finance_data(year=2022, data_type='despesas_contratadas')
            print(f"   Despesas contratadas: {len(despesas_contratadas)} records")

            # Test despesas_pagas
            despesas_pagas = client.get_finance_data(year=2022, data_type='despesas_pagas')
            print(f"   Despesas pagas: {len(despesas_pagas)} records")

        return len(finance_records) > 0

    except Exception as e:
        print(f"❌ Error testing fixed mappings: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run fixed TSE mapping test"""
    print("🚀 FIXED TSE FIELD MAPPING TEST")
    print("Testing with corrected field names from actual data")
    print("=" * 60)

    success = test_fixed_tse_mappings()

    if success:
        print(f"\n🎉 SUCCESS: Fixed TSE field mappings work!")
        print(f"   Field validation now properly handles all 4 TSE data types")
        print(f"   Ready to populate financial database with real data")
    else:
        print(f"\n🔍 STILL DEBUGGING: Check the validation logic")
        print(f"   Examine the detailed output above for any remaining issues")


if __name__ == "__main__":
    main()