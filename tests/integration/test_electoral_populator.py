#!/usr/bin/env python3
"""
Integration test for CLI4 Electoral Populator
Tests all critical functionality with real TSE data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.populators.electoral.populator import ElectoralRecordsPopulator
from src.clients.tse_client import TSEClient


def test_field_extraction():
    """Test that TSE field extraction works correctly"""
    print("\n🧪 TEST 1: TSE Field Extraction")
    print("-" * 50)

    # Test TSE client field extraction
    tse_client = TSEClient()

    # Test with a known CPF (this should be cached from previous runs)
    test_cpf = "74287028287"  # ACÁCIO DA SILVA FAVACHO NETO
    test_year = 2018

    print(f"Testing CPF: {test_cpf}")
    print(f"Year: {test_year}")

    candidates = tse_client.get_candidate_data(test_year)
    # Filter for our test CPF
    candidates = [c for c in candidates if c.get('NR_CPF_CANDIDATO') == test_cpf or c.get('cpf') == test_cpf]

    if candidates:
        print(f"✅ Found {len(candidates)} candidates")
        for candidate in candidates[:1]:  # Check first candidate
            print("\nField Inspection:")
            # Check both original and normalized fields
            important_fields = [
                'DS_CARGO', 'position',
                'DS_SITUACAO_CANDIDATURA', 'status',
                'DS_SIT_TOT_TURNO', 'electoral_outcome',
                'NM_CANDIDATO', 'name',
                'NR_CPF_CANDIDATO', 'cpf'
            ]

            for field in important_fields:
                value = candidate.get(field, 'NOT FOUND')
                if value != 'NOT FOUND':
                    print(f"  {field}: {value}")
    else:
        print("❌ No candidates found - may need to fetch from TSE")

    return len(candidates) > 0


def test_date_parsing():
    """Test Brazilian date format parsing"""
    print("\n🧪 TEST 2: Date Parsing")
    print("-" * 50)

    from datetime import date

    def _parse_brazilian_date(date_str):
        """Parse Brazilian date format DD/MM/YYYY to PostgreSQL date"""
        if not date_str:
            return None

        try:
            date_str = str(date_str).strip()
            if not date_str or date_str in ['#NULO#', '', 'NULL']:
                return None

            # Handle Brazilian date format: DD/MM/YYYY
            if '/' in date_str and len(date_str) == 10:
                day, month, year = date_str.split('/')
                return date(int(year), int(month), int(day))

            # Handle ISO format: YYYY-MM-DD (already correct)
            elif '-' in date_str and len(date_str) == 10:
                year, month, day = date_str.split('-')
                return date(int(year), int(month), int(day))

            return None
        except (ValueError, TypeError, AttributeError):
            print(f"    ⚠️ Error parsing date '{date_str}', using NULL")
            return None

    test_dates = [
        ('05/10/2018', date(2018, 10, 5)),
        ('2018-10-05', date(2018, 10, 5)),
        ('#NULO#', None),
        ('', None),
        (None, None),
    ]

    all_passed = True
    for date_str, expected in test_dates:
        result = _parse_brazilian_date(date_str)
        if result == expected:
            print(f"✅ '{date_str}' -> {result}")
        else:
            print(f"❌ '{date_str}' -> {result} (expected {expected})")
            all_passed = False

    return all_passed


def test_electoral_populator_init():
    """Test Electoral Populator initialization"""
    print("\n🧪 TEST 3: Electoral Populator Initialization")
    print("-" * 50)

    try:
        logger = CLI4Logger()
        rate_limiter = CLI4RateLimiter()

        populator = ElectoralRecordsPopulator(logger, rate_limiter)

        # Check that required attributes exist
        assert hasattr(populator, 'logger'), "Missing logger"
        assert hasattr(populator, 'rate_limiter'), "Missing rate_limiter"
        assert hasattr(populator, 'tse_client'), "Missing tse_client"

        # Check that methods exist
        assert hasattr(populator, 'populate'), "Missing populate method"
        assert hasattr(populator, '_convert_tse_candidacy_to_record'), "Missing conversion method"
        assert hasattr(populator, '_bulk_insert_records'), "Missing bulk insert method"

        print("✅ Electoral Populator initialized successfully")
        print(f"  - Logger: {type(populator.logger).__name__}")
        print(f"  - Rate Limiter: {type(populator.rate_limiter).__name__}")
        print(f"  - TSE Client: {type(populator.tse_client).__name__}")

        return True

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False


def test_database_operations():
    """Test database operations without actual insertion"""
    print("\n🧪 TEST 4: Database Operations")
    print("-" * 50)

    # Test that we can connect to database
    try:
        result = database.execute_query("SELECT COUNT(*) as count FROM unified_politicians")
        politician_count = result[0]['count'] if result else 0
        print(f"✅ Database connection OK - {politician_count} politicians in database")

        # Test the execute_batch_returning method exists
        assert hasattr(database, 'execute_batch_returning'), "Missing execute_batch_returning method"
        print("✅ execute_batch_returning method exists")

        # Check table structure
        result = database.execute_query("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'unified_electoral_records'
            ORDER BY ordinal_position
            LIMIT 5
        """)

        if result:
            print("✅ Electoral records table structure:")
            for col in result:
                print(f"  - {col['column_name']}: {col['data_type']}")

        return True

    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        return False


def test_record_conversion():
    """Test TSE candidacy to database record conversion"""
    print("\n🧪 TEST 5: Record Conversion")
    print("-" * 50)

    logger = CLI4Logger()
    rate_limiter = CLI4RateLimiter()
    populator = ElectoralRecordsPopulator(logger, rate_limiter)

    # Create a mock TSE candidacy record with all expected fields
    mock_candidacy = {
        # Original TSE fields
        'SQ_CANDIDATO': '12345',
        'NM_CANDIDATO': 'TEST CANDIDATE',
        'NR_CPF_CANDIDATO': '12345678901',
        'DS_CARGO': 'DEPUTADO FEDERAL',
        'CD_CARGO': 6,
        'DS_SITUACAO_CANDIDATURA': 'APTO',
        'CD_SITUACAO_CANDIDATURA': 2,
        'DS_SIT_TOT_TURNO': 'ELEITO POR QP',
        'CD_SIT_TOT_TURNO': 2,
        'SG_PARTIDO': 'PT',
        'NR_PARTIDO': 13,
        'NM_PARTIDO': 'PARTIDO DOS TRABALHADORES',
        'SG_UF': 'AP',
        'DT_ELEICAO': '05/10/2018',
        'NR_TURNO': 1,
        'QT_VOTOS_NOMINAIS': 50000,

        # Normalized fields (if TSE client returns these)
        'name': 'TEST CANDIDATE',
        'cpf': '12345678901',
        'position': 'DEPUTADO FEDERAL',
        'status': 'APTO',
        'electoral_outcome': 'ELEITO POR QP',
        'state': 'AP',
    }

    try:
        # Test conversion
        record = populator._convert_tse_candidacy_to_record(1, mock_candidacy, 2018)

        if record:
            print("✅ Record conversion successful")
            print("Sample fields:")
            important_fields = [
                'politician_id',
                'election_year',
                'position_description',
                'candidacy_status_description',
                'final_result_description',
                'source_record_id'
            ]

            for field in important_fields:
                if field in record:
                    print(f"  {field}: {record[field]}")

            return True
        else:
            print("❌ Conversion returned None")
            return False

    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mini_population():
    """Test population with a single politician"""
    print("\n🧪 TEST 6: Mini Population Test")
    print("-" * 50)

    try:
        # Get a test politician with known electoral history
        result = database.execute_query("""
            SELECT id, cpf, nome_civil
            FROM unified_politicians
            WHERE cpf = '74287028287'
            LIMIT 1
        """)

        if not result:
            print("⚠️ Test politician not found, creating one...")
            # Insert test politician if not exists
            database.execute_query("""
                INSERT INTO unified_politicians (cpf, nome_civil)
                VALUES ('74287028287', 'TEST - ACÁCIO DA SILVA FAVACHO NETO')
                ON CONFLICT (cpf) DO UPDATE SET nome_civil = EXCLUDED.nome_civil
                RETURNING id, cpf, nome_civil
            """)
            result = database.execute_query("""
                SELECT id, cpf, nome_civil
                FROM unified_politicians
                WHERE cpf = '74287028287'
                LIMIT 1
            """)

        if result:
            politician = result[0]
            print(f"Using test politician: {politician['nome_civil']} (ID: {politician['id']})")

            # Initialize populator
            logger = CLI4Logger()
            rate_limiter = CLI4RateLimiter()
            populator = ElectoralRecordsPopulator(logger, rate_limiter)

            # Run population for just this politician and 2018
            print("Running population for 2018...")
            records_inserted = populator.populate(
                politician_ids=[politician['id']],
                election_years=[2018]
            )

            print(f"✅ Population completed: {records_inserted} records")

            # Verify records were inserted
            result = database.execute_query("""
                SELECT COUNT(*) as count
                FROM unified_electoral_records
                WHERE politician_id = %s
            """, (politician['id'],))

            actual_count = result[0]['count'] if result else 0
            print(f"  Records in database: {actual_count}")

            return actual_count > 0
        else:
            print("❌ Could not create test politician")
            return False

    except Exception as e:
        print(f"❌ Mini population failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("🚀 ELECTORAL POPULATOR INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        ("Field Extraction", test_field_extraction),
        ("Date Parsing", test_date_parsing),
        ("Populator Initialization", test_electoral_populator_init),
        ("Database Operations", test_database_operations),
        ("Record Conversion", test_record_conversion),
        ("Mini Population", test_mini_population),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed out of {len(tests)} tests")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Electoral populator is ready for production.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please fix issues before running in production.")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)