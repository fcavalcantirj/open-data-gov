#!/usr/bin/env python3
"""
Integration test for CLI4 Career Populator
Tests the complete career population workflow
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.populators.career import CareerPopulator, CareerValidator
from cli4.modules import database


def test_career_populator():
    """Test career populator with small sample"""
    print("🧪 CLI4 CAREER POPULATOR INTEGRATION TEST")
    print("=" * 60)

    # Initialize components
    logger = CLI4Logger()
    rate_limiter = CLI4RateLimiter()
    career_populator = CareerPopulator(logger, rate_limiter)

    # Test with a small sample of politicians (limit to 3 for testing)
    print("📊 Testing with first 3 politicians that have deputy_id...")

    # Get test politicians
    test_politicians = database.execute_query("""
        SELECT id, deputy_id, nome_civil
        FROM unified_politicians
        WHERE deputy_id IS NOT NULL
        LIMIT 3
    """)

    if not test_politicians:
        print("❌ No politicians with deputy_id found for testing")
        return False

    print(f"🎯 Found {len(test_politicians)} test politicians:")
    for politician in test_politicians:
        print(f"   • {politician['nome_civil']} (ID: {politician['id']}, Deputy: {politician['deputy_id']})")
    print()

    # Run career population
    politician_ids = [p['id'] for p in test_politicians]

    try:
        records_inserted = career_populator.populate(politician_ids=politician_ids)

        print(f"✅ Career population completed!")
        print(f"📊 Total records inserted: {records_inserted}")

        # Verify results in database
        verification_query = """
            SELECT
                p.nome_civil,
                c.office_name,
                c.mandate_type,
                c.start_year,
                c.end_year,
                c.state,
                c.municipality
            FROM politician_career_history c
            JOIN unified_politicians p ON p.id = c.politician_id
            WHERE c.politician_id = ANY(%s)
            ORDER BY p.nome_civil, c.start_year
        """

        results = database.execute_query(verification_query, (politician_ids,))

        print(f"\n📋 Career records found in database:")
        current_politician = None
        for result in results:
            if result['nome_civil'] != current_politician:
                current_politician = result['nome_civil']
                print(f"\n👤 {current_politician}:")

            years = f"{result['start_year']}-{result['end_year'] or 'present'}"
            location = f"{result['municipality'] or result['state'] or 'N/A'}"
            print(f"   • {result['office_name']} ({result['mandate_type']}) {years} in {location}")

        return True

    except Exception as e:
        print(f"❌ Career population test failed: {e}")
        return False


def test_career_validator():
    """Test career validator"""
    print("\n" + "=" * 60)
    print("🧪 CLI4 CAREER VALIDATOR INTEGRATION TEST")
    print("=" * 60)

    try:
        career_validator = CareerValidator()

        # Run validation on limited sample
        validation_results = career_validator.validate_all_career_records(limit=50)

        print(f"✅ Career validation completed!")
        print(f"📊 Compliance score: {validation_results['compliance_score']:.1f}%")
        print(f"🚨 Critical issues: {len(validation_results['critical_issues'])}")
        print(f"⚠️ Warnings: {len(validation_results['warnings'])}")

        return validation_results['compliance_score'] > 0

    except Exception as e:
        print(f"❌ Career validation test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting CLI4 Career Integration Tests...")
    print()

    # Test populator
    populator_success = test_career_populator()

    # Test validator
    validator_success = test_career_validator()

    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)
    print(f"📋 Career Populator: {'✅ PASSED' if populator_success else '❌ FAILED'}")
    print(f"🔍 Career Validator: {'✅ PASSED' if validator_success else '❌ FAILED'}")

    if populator_success and validator_success:
        print("\n🎉 ALL TESTS PASSED! Career populator is ready for production.")
    else:
        print("\n⚠️ Some tests failed. Check implementation before proceeding.")

    print("\n💡 Next steps:")
    print("   1. Add to cli4/main.py CLI interface")
    print("   2. Update run_full_population.sh")
    print("   3. Mark as completed in migration docs")