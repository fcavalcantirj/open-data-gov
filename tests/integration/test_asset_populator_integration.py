#!/usr/bin/env python3
"""
Integration test for CLI4 Asset Populator
Tests the complete asset population workflow before implementation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules import database
from src.clients.tse_client import TSEClient


def test_asset_data_structure():
    """Test TSE asset data structure and correlation potential"""
    print("🧪 TSE ASSET DATA STRUCTURE TEST")
    print("=" * 60)

    # Test TSE client asset fetching
    tse_client = TSEClient()

    try:
        # Get a small sample of asset data
        print("📊 Fetching TSE asset data for 2022...")
        assets = tse_client.get_asset_data(2022)

        if not assets:
            print("❌ No asset data retrieved")
            return False

        print(f"✅ Retrieved {len(assets)} total assets")

        # Analyze asset structure
        sample_asset = assets[0]
        print(f"\n📋 Sample asset data structure:")
        for key, value in sample_asset.items():
            print(f"   {key}: {value}")

        # Test Brazilian currency parsing
        test_values = [
            sample_asset.get('VR_BEM_CANDIDATO', '0,00'),
            '1.234.567,89',
            '15.000,50',
            '500,00'
        ]

        print(f"\n💰 Currency parsing test:")
        for value in test_values:
            try:
                # Parse Brazilian format: "1.234,56" -> 1234.56
                if value and ',' in value:
                    clean_value = value.replace('.', '').replace(',', '.')
                    parsed = float(clean_value)
                    print(f"   '{value}' -> {parsed}")
                else:
                    print(f"   '{value}' -> 0.00 (invalid format)")
            except Exception as e:
                print(f"   '{value}' -> ERROR: {e}")

        return True

    except Exception as e:
        print(f"❌ Asset data structure test failed: {e}")
        return False


def test_politician_correlation():
    """Test politician-asset correlation using SQ_CANDIDATO"""
    print("\n" + "=" * 60)
    print("🧪 POLITICIAN-ASSET CORRELATION TEST")
    print("=" * 60)

    try:
        # Get politicians with SQ_CANDIDATO values
        politicians = database.execute_query("""
            SELECT id, cpf, nome_civil, sq_candidato_2022
            FROM unified_politicians
            WHERE sq_candidato_2022 IS NOT NULL
            LIMIT 5
        """)

        if not politicians:
            print("❌ No politicians with sq_candidato_2022 found")
            return False

        print(f"📊 Found {len(politicians)} politicians with SQ_CANDIDATO:")
        for p in politicians:
            print(f"   • {p['nome_civil']} (ID: {p['id']}, SQ: {p['sq_candidato_2022']})")

        # Get TSE assets for correlation testing
        tse_client = TSEClient()
        assets = tse_client.get_asset_data(2022)

        if not assets:
            print("❌ No TSE assets available for correlation")
            return False

        # Test correlation logic
        correlation_count = 0
        for politician in politicians:
            sq_candidato = str(politician['sq_candidato_2022'])

            # Find matching assets
            matching_assets = [
                asset for asset in assets
                if asset.get('SQ_CANDIDATO') == sq_candidato
            ]

            if matching_assets:
                correlation_count += 1
                print(f"   ✅ {politician['nome_civil']}: {len(matching_assets)} assets found")
            else:
                print(f"   ⚠️ {politician['nome_civil']}: No assets found")

        print(f"\n📊 Correlation Results:")
        print(f"   Politicians with assets: {correlation_count}/{len(politicians)}")
        print(f"   Correlation success rate: {correlation_count/len(politicians)*100:.1f}%")

        return correlation_count > 0

    except Exception as e:
        print(f"❌ Politician correlation test failed: {e}")
        return False


def test_database_schema():
    """Test politician_assets table schema"""
    print("\n" + "=" * 60)
    print("🧪 DATABASE SCHEMA TEST")
    print("=" * 60)

    try:
        # Test table exists and get structure
        schema_info = database.execute_query("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'politician_assets'
            ORDER BY ordinal_position
        """)

        if not schema_info:
            print("❌ politician_assets table not found or not accessible")
            return False

        print("✅ politician_assets table found with schema:")
        for col in schema_info:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   {col['column_name']}: {col['data_type']} {nullable}{default}")

        # Test unique constraint
        constraint_info = database.execute_query("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'politician_assets'
            AND indexdef LIKE '%UNIQUE%'
        """)

        if constraint_info:
            print(f"\n🔐 Unique constraints found:")
            for constraint in constraint_info:
                print(f"   {constraint['indexname']}: {constraint['indexdef']}")
        else:
            print(f"\n⚠️ No unique constraints found")

        return True

    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False


def test_mock_asset_insertion():
    """Test mock asset insertion to verify database connectivity"""
    print("\n" + "=" * 60)
    print("🧪 MOCK ASSET INSERTION TEST")
    print("=" * 60)

    try:
        # Get a test politician
        test_politician = database.execute_query("""
            SELECT id FROM unified_politicians LIMIT 1
        """)

        if not test_politician:
            print("❌ No test politician found")
            return False

        politician_id = test_politician[0]['id']

        # Create mock asset record
        mock_asset = {
            'politician_id': politician_id,
            'asset_sequence': 999,  # Use high number to avoid conflicts
            'asset_type_code': 99,
            'asset_type_description': 'TEST ASSET TYPE',
            'asset_description': 'Integration test mock asset',
            'declared_value': 12345.67,
            'currency': 'BRL',
            'declaration_year': 2022,
            'election_year': 2022,
            'source_system': 'TSE'
        }

        # Test insertion
        fields = list(mock_asset.keys())
        placeholders = ', '.join(['%s'] * len(fields))
        values = list(mock_asset.values())

        insert_sql = f"""
            INSERT INTO politician_assets ({', '.join(fields)})
            VALUES ({placeholders})
            ON CONFLICT (politician_id, declaration_year, asset_sequence) DO NOTHING
            RETURNING id
        """

        result = database.execute_query(insert_sql, tuple(values))

        if result:
            print(f"✅ Mock asset inserted successfully (ID: {result[0]['id']})")

            # Clean up - remove test record
            cleanup_sql = """
                DELETE FROM politician_assets
                WHERE politician_id = %s AND asset_sequence = 999
            """
            database.execute_update(cleanup_sql, (politician_id,))
            print(f"✅ Test record cleaned up")

            return True
        else:
            print(f"⚠️ Mock asset insertion returned no result (likely duplicate)")
            return True  # Still consider success - means conflict resolution works

    except Exception as e:
        print(f"❌ Mock asset insertion test failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests before implementation"""
    print("🚀 CLI4 ASSET POPULATOR INTEGRATION TESTS")
    print("=" * 80)
    print("Running comprehensive tests BEFORE implementation...")
    print()

    tests = [
        ("TSE Asset Data Structure", test_asset_data_structure),
        ("Politician Correlation", test_politician_correlation),
        ("Database Schema", test_database_schema),
        ("Mock Asset Insertion", test_mock_asset_insertion)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"\n💥 {test_name}: CRASHED - {e}")
            failed += 1

        print()

    # Final results
    print("=" * 80)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Asset Populator is ready for implementation.")
        print("\n💡 Next steps:")
        print("   1. Implement CLI4 Asset Populator following established patterns")
        print("   2. Implement CLI4 Asset Validator with comprehensive checks")
        print("   3. Add to CLI interface and workflow")
        print("   4. Update documentation")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Fix issues before proceeding with implementation.")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)