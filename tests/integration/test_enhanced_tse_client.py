#!/usr/bin/env python3
"""
TEST SCRIPT: Enhanced TSE Client with Electoral Outcomes
Test the enhanced TSE client to verify electoral outcome processing
"""

import sys
import os
# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.clients.tse_client import TSEClient


def test_enhanced_tse_client():
    """Test the enhanced TSE client with electoral outcome features"""
    print("🧪 TESTING ENHANCED TSE CLIENT")
    print("With electoral outcome processing capabilities")
    print("=" * 60)

    client = TSEClient()

    # Test candidate data retrieval with electoral outcomes
    print("\n📊 TESTING CANDIDATE DATA WITH ELECTORAL OUTCOMES")
    print("Getting 2022 candidates from Acre (AC) - small state for testing")

    try:
        candidates = client.get_candidate_data(year=2022, state='AC')
        print(f"✅ Retrieved {len(candidates)} candidates")

        if candidates:
            # Analyze electoral outcomes
            elected_count = sum(1 for c in candidates if c.get('was_elected'))
            not_elected_count = sum(1 for c in candidates if c.get('election_status_category') == 'NOT_ELECTED')
            substitute_count = sum(1 for c in candidates if c.get('election_status_category') == 'SUBSTITUTE')

            print(f"\n📈 ELECTORAL OUTCOMES ANALYSIS:")
            print(f"   Elected: {elected_count}")
            print(f"   Not Elected: {not_elected_count}")
            print(f"   Substitutes: {substitute_count}")

            # Show sample candidates with electoral data
            print(f"\n👥 SAMPLE CANDIDATES WITH ELECTORAL OUTCOMES:")
            for i, candidate in enumerate(candidates[:5], 1):
                name = candidate.get('name', 'Unknown')[:30]
                outcome = candidate.get('electoral_outcome', 'N/A')
                category = candidate.get('election_status_category', 'N/A')
                elected = candidate.get('was_elected', False)
                votes = candidate.get('votes_received_int', 0)

                print(f"   {i}. {name:<30} | {outcome:<15} | {category:<15} | Elected: {elected} | Votes: {votes}")

            # Test specific candidate search
            print(f"\n🔍 TESTING SPECIFIC CANDIDATE SEARCH")
            if candidates:
                test_candidate = candidates[0]
                search_name = test_candidate.get('name', '')
                if search_name:
                    matches = client.find_candidate_by_name(search_name, year=2022)
                    print(f"   Search for '{search_name[:30]}': {len(matches)} matches")

                    if matches:
                        match = matches[0]
                        print(f"   Found: {match.get('name', 'N/A')}")
                        print(f"   Electoral outcome: {match.get('electoral_outcome', 'N/A')}")
                        print(f"   Was elected: {match.get('was_elected', False)}")

        return True

    except Exception as e:
        print(f"❌ Error testing enhanced TSE client: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_electoral_success_statistics():
    """Test the electoral success statistics method"""
    print(f"\n📊 TESTING ELECTORAL SUCCESS STATISTICS")
    print("=" * 50)

    client = TSEClient()

    # First get some candidates to test with
    try:
        candidates = client.get_candidate_data(year=2022, state='AC')

        if candidates:
            # Find a candidate with CPF
            test_candidate = None
            for candidate in candidates:
                if candidate.get('cpf') and len(candidate['cpf']) == 11:
                    test_candidate = candidate
                    break

            if test_candidate:
                print(f"Testing statistics for: {test_candidate.get('name', 'Unknown')}")
                print(f"CPF: {test_candidate.get('cpf')}")

                # Get electoral statistics
                stats = client.get_electoral_success_statistics(test_candidate['cpf'], years=[2022])

                print(f"\n📈 ELECTORAL STATISTICS:")
                print(f"   Total elections: {stats['total_elections']}")
                print(f"   Elections won: {stats['elections_won']}")
                print(f"   Success rate: {stats['success_rate']:.2f}")
                print(f"   Career trajectory: {stats['career_trajectory']}")
                print(f"   Total votes: {stats['total_votes']:,}")

                if stats['elections_detail']:
                    print(f"\n📋 ELECTION DETAILS:")
                    for detail in stats['elections_detail']:
                        print(f"   {detail['year']}: {detail['electoral_outcome']} ({detail['position']})")

                return True
            else:
                print("⚠️ No candidates with valid CPF found for testing")
                return False
        else:
            print("⚠️ No candidates found for testing")
            return False

    except Exception as e:
        print(f"❌ Error testing electoral statistics: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all enhanced TSE client tests"""
    print("🚀 ENHANCED TSE CLIENT TEST SUITE")
    print("Testing electoral outcome data processing")
    print("=" * 60)

    # Test 1: Basic enhanced client functionality
    test1_success = test_enhanced_tse_client()

    # Test 2: Electoral success statistics
    test2_success = test_electoral_success_statistics()

    # Summary
    print(f"\n📋 TEST RESULTS SUMMARY:")
    print(f"   Enhanced Client Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"   Electoral Statistics Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")

    if test1_success and test2_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   TSE client is ready for production with electoral outcomes")
        print(f"   Ready to enhance metrics calculator with real electoral data")
        return True
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"   Review errors above before proceeding")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)