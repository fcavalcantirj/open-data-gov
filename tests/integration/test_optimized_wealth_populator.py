#!/usr/bin/env python3
"""
Test script for the optimized CLI4 Wealth Populator
Demonstrates the enhanced year selection logic with real politician data
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.populators.wealth import CLI4WealthPopulator

def test_optimized_year_selection():
    """Test the optimized year selection with real politician data"""
    print("🧪 TESTING OPTIMIZED WEALTH POPULATOR YEAR SELECTION")
    print("=" * 60)
    print("Comparing old vs new year selection logic\n")

    # Get a few politicians with different timeline profiles
    politicians = database.execute_query("""
        SELECT id, nome_civil, cpf, sq_candidato_current,
               first_election_year, last_election_year, total_candidacies
        FROM unified_politicians
        WHERE cpf IS NOT NULL
          AND sq_candidato_current IS NOT NULL
          AND first_election_year IS NOT NULL
          AND last_election_year IS NOT NULL
        ORDER BY
            CASE
                WHEN last_election_year - first_election_year > 10 THEN 1  -- Long careers first
                WHEN last_election_year >= 2020 THEN 2                     -- Recent politicians
                ELSE 3                                                      -- Others
            END,
            total_candidacies DESC
        LIMIT 5
    """)

    if not politicians:
        print("❌ No politicians found with complete timeline data")
        return

    print(f"📊 Testing {len(politicians)} politicians with diverse career profiles:")

    # Initialize components
    logger = CLI4Logger(console=True, file=False)
    rate_limiter = CLI4RateLimiter()
    wealth_populator = CLI4WealthPopulator(logger, rate_limiter)

    for i, politician in enumerate(politicians, 1):
        print(f"\n{i}. 🏛️ {politician['nome_civil'][:40]}")
        print(f"   ID: {politician['id']} | Career: {politician['first_election_year']}-{politician['last_election_year']}")
        print(f"   Total candidacies: {politician['total_candidacies']}")

        # Test old approach (default years)
        old_years = [2018, 2020, 2022, 2024]

        # Test new optimized approach
        new_years = wealth_populator._calculate_relevant_years(politician, old_years)

        print(f"   📅 Old approach: {old_years} ({len(old_years)} API calls)")
        print(f"   🎯 Optimized: {new_years} ({len(new_years)} API calls)")

        # Calculate efficiency
        old_valid_years = len([y for y in old_years if y != 2020])  # 2020 has no data
        new_valid_years = len(new_years)

        if new_valid_years < old_valid_years:
            savings = old_valid_years - new_valid_years
            print(f"   💰 Efficiency: {savings} fewer calls ({(savings/old_valid_years)*100:.1f}% reduction)")
        elif new_valid_years > old_valid_years:
            additional = new_valid_years - old_valid_years
            print(f"   📈 Coverage: +{additional} calls for complete timeline")
        else:
            print(f"   ⚖️ Same efficiency but better targeted (skips 2020)")

        # Show year selection reasoning
        print(f"   📝 Logic: ", end="")
        reasoning = []
        first_year = politician['first_election_year']
        last_year = politician['last_election_year']

        for year in new_years:
            if year < first_year:
                reasoning.append(f"{year}(pre-career)")
            elif first_year <= year <= last_year:
                reasoning.append(f"{year}(active)")
            elif year > last_year:
                reasoning.append(f"{year}(post-career)")

        print(", ".join(reasoning))

def test_specific_politician_processing(politician_id=None):
    """Test processing a specific politician with optimized approach"""
    print(f"\n🔬 TESTING ACTUAL WEALTH PROCESSING")
    print("=" * 50)

    if not politician_id:
        # Find a politician with assets
        test_politician = database.execute_query("""
            SELECT id, nome_civil, cpf, sq_candidato_current,
                   first_election_year, last_election_year
            FROM unified_politicians
            WHERE cpf IS NOT NULL
              AND sq_candidato_current IS NOT NULL
              AND first_election_year IS NOT NULL
            ORDER BY total_candidacies DESC
            LIMIT 1
        """)

        if not test_politician:
            print("❌ No suitable test politician found")
            return

        politician_id = test_politician[0]['id']
        print(f"🎯 Using test politician: {test_politician[0]['nome_civil']} (ID: {politician_id})")

    # Initialize wealth populator
    logger = CLI4Logger(console=True, file=False)
    rate_limiter = CLI4RateLimiter()

    print(f"\n💎 Running optimized wealth populator on politician {politician_id}...")
    print("Note: This will show the enhanced year selection in action")

    # Run with DRY_RUN to avoid actual database changes
    import os
    os.environ['DRY_RUN'] = 'true'

    try:
        wealth_populator = CLI4WealthPopulator(logger, rate_limiter)
        result = wealth_populator.populate(politician_ids=[politician_id])
        print(f"\n✅ Test completed. Would have processed {result} records.")

    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        # Clean up
        if 'DRY_RUN' in os.environ:
            del os.environ['DRY_RUN']

def main():
    """Main test execution"""
    print("🚀 Starting optimized wealth populator tests...\n")

    try:
        # Test year selection logic
        test_optimized_year_selection()

        # Test actual processing (dry run)
        test_specific_politician_processing()

        print(f"\n🎉 All tests completed!")
        print(f"💡 The optimized populator now:")
        print(f"   • Skips 2020 (no TSE data available)")
        print(f"   • Uses politician timeline for targeted searches")
        print(f"   • Adds pre/post career years for complete wealth tracking")
        print(f"   • Provides clear efficiency feedback")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    main()