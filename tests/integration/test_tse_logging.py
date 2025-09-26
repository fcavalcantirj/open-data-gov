#!/usr/bin/env python3
"""
TEST SCRIPT: TSE Financial Data Logging
Test the enhanced TSE client with improved validation logging
"""

import sys
import os
sys.path.append('/Users/fcavalcanti/dev/open-data-gov/src')

from clients.tse_client import TSEClient


def test_tse_logging():
    """Test TSE client with enhanced logging to debug 0 valid records"""
    print("🧪 TESTING TSE FINANCIAL DATA WITH ENHANCED LOGGING")
    print("=" * 60)

    client = TSEClient()

    # Test with small data set - 2022 campaign finance
    print("📊 Testing TSE financial data processing with enhanced logging...")
    print("Year: 2022, Data type: all")

    try:
        # Get finance data with logging
        finance_records = client.get_finance_data(year=2022, data_type='all')

        print(f"\n✅ FINAL RESULT:")
        print(f"   Total finance records retrieved: {len(finance_records)}")

        if finance_records:
            print(f"   Sample record keys: {list(finance_records[0].keys())[:10]}...")

            # Show breakdown by data type
            data_types = {}
            for record in finance_records[:100]:  # Sample first 100
                data_type = record.get('tse_data_type', 'unknown')
                data_types[data_type] = data_types.get(data_type, 0) + 1

            print(f"   Data type breakdown (sample): {data_types}")
        else:
            print("   ❌ No valid records found - check the detailed logging above")

        return len(finance_records) > 0

    except Exception as e:
        print(f"❌ Error testing TSE logging: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run TSE logging test"""
    print("🚀 TSE ENHANCED LOGGING TEST")
    print("Debugging why we get 0 valid records")
    print("=" * 60)

    success = test_tse_logging()

    if success:
        print(f"\n🎉 SUCCESS: Found valid TSE financial records!")
        print(f"   The enhanced logging helped identify valid data")
    else:
        print(f"\n🔍 DEBUGGING NEEDED: Still getting 0 valid records")
        print(f"   Check the detailed logging output above to see:")
        print(f"   1. What fields are available in TSE files")
        print(f"   2. Where validation is failing")
        print(f"   3. What field names we should be looking for")


if __name__ == "__main__":
    main()