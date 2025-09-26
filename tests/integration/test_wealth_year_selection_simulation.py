#!/usr/bin/env python3
"""
Simulated test script for optimizing wealth populator year selection
Demonstrates the optimization approach without requiring database connection
"""

import sys
from pathlib import Path

class WealthYearSelectionSimulator:
    """Simulate and analyze year selection patterns for wealth population"""

    def __init__(self):
        # Simulate TSE data availability (based on known patterns)
        self.tse_data_availability = {
            2014: 85000,   # Available
            2016: 120000,  # Available
            2018: 187000,  # Available (confirmed from previous run)
            2020: 0,       # No data (confirmed from previous run)
            2022: 185000,  # Available (confirmed from previous run)
            2024: 1800000, # Available (confirmed from previous run)
        }

    def simulate_politician_scenarios(self):
        """Simulate different politician timeline scenarios"""
        scenarios = [
            {
                'name': 'Veteran Senator',
                'first_election_year': 2010,
                'last_election_year': 2022,
                'total_candidacies': 4,
                'profile': 'Long career spanning multiple election cycles'
            },
            {
                'name': 'New Deputy',
                'first_election_year': 2018,
                'last_election_year': 2022,
                'total_candidacies': 2,
                'profile': 'Recent entry into politics'
            },
            {
                'name': 'Municipal Mayor',
                'first_election_year': 2016,
                'last_election_year': 2020,
                'total_candidacies': 2,
                'profile': 'Municipal focus, limited federal activity'
            },
            {
                'name': 'Career Politician',
                'first_election_year': 2006,
                'last_election_year': 2024,
                'total_candidacies': 6,
                'profile': 'Extensive political career'
            },
            {
                'name': 'Single Term Deputy',
                'first_election_year': 2014,
                'last_election_year': 2014,
                'total_candidacies': 1,
                'profile': 'Brief political involvement'
            }
        ]
        return scenarios

    def analyze_optimization_approach(self):
        """Analyze current vs optimized approach"""
        print("🧪 WEALTH YEAR SELECTION OPTIMIZATION SIMULATION")
        print("=" * 60)
        print("Demonstrating smart year selection without database dependency\n")

        # Current default approach
        default_years = [2018, 2020, 2022, 2024]

        print("📅 TSE Data Availability Analysis:")
        print("=" * 40)
        total_available = 0
        available_years = []

        for year, count in self.tse_data_availability.items():
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {year}: {count:,} assets")
            if count > 0:
                available_years.append(year)
                total_available += count

        print(f"\n📊 Total assets across all years: {total_available:,}")
        print(f"Years with data: {available_years}")
        print(f"Years without data (should skip): {[y for y, c in self.tse_data_availability.items() if c == 0]}")

        print(f"\n👥 POLITICIAN SCENARIO ANALYSIS")
        print("=" * 40)

        scenarios = self.simulate_politician_scenarios()
        total_api_savings = 0

        for i, politician in enumerate(scenarios, 1):
            print(f"\n{i}. {politician['name']} ({politician['profile']})")
            print(f"   Career span: {politician['first_election_year']}-{politician['last_election_year']}")

            # Current approach (fixed years)
            current_searches = default_years
            current_api_calls = len(current_searches)

            # Optimized approach
            optimized_years = self.calculate_smart_years(politician)
            optimized_api_calls = len(optimized_years)

            print(f"   Current approach: {current_searches} ({current_api_calls} API calls)")
            print(f"   Optimized approach: {optimized_years} ({optimized_api_calls} API calls)")

            # Calculate efficiency
            if optimized_api_calls < current_api_calls:
                savings = current_api_calls - optimized_api_calls
                percentage = (savings / current_api_calls) * 100
                print(f"   💰 Efficiency gain: {savings} fewer calls ({percentage:.1f}% reduction)")
                total_api_savings += savings
            elif optimized_api_calls > current_api_calls:
                additional = optimized_api_calls - current_api_calls
                percentage = (additional / current_api_calls) * 100
                print(f"   📈 Enhanced coverage: {additional} more calls ({percentage:.1f}% increase)")
                total_api_savings -= additional
            else:
                print(f"   ⚖️ Same API calls but better targeted")

            # Show reasoning
            self.explain_year_selection_logic(politician, optimized_years)

        print(f"\n📈 OVERALL OPTIMIZATION IMPACT")
        print("=" * 40)
        total_politicians = len(scenarios)
        avg_savings = total_api_savings / total_politicians

        if avg_savings > 0:
            print(f"✅ Average API call reduction: {avg_savings:.1f} per politician")
            print(f"💰 For 1000 politicians: ~{avg_savings * 1000:.0f} fewer API calls")
        else:
            print(f"📊 Average API calls: {abs(avg_savings):.1f} more per politician (better coverage)")

        print(f"\n🚀 RECOMMENDED IMPLEMENTATION:")
        self.generate_implementation_recommendations()

    def calculate_smart_years(self, politician):
        """Calculate optimized year selection for a politician"""
        first_year = politician['first_election_year']
        last_year = politician['last_election_year']

        # Available years (skip years with no TSE data)
        available_years = [year for year, count in self.tse_data_availability.items() if count > 0]

        smart_years = set()

        # 1. Add years during active political period
        for year in available_years:
            if first_year <= year <= last_year:
                smart_years.add(year)

        # 2. Add preparation years (2 years before first election for wealth baseline)
        prep_year = first_year - 2
        while prep_year >= 2014 and prep_year not in smart_years:
            if prep_year in available_years:
                smart_years.add(prep_year)
                break
            prep_year -= 2

        # 3. Add post-career years (2 years after for wealth retention analysis)
        post_year = last_year + 2
        while post_year <= 2024 and post_year not in smart_years:
            if post_year in available_years:
                smart_years.add(post_year)
                break
            post_year += 2

        # 4. Ensure we have at least one recent year for current politicians
        if last_year >= 2020:
            recent_years = [2024, 2022, 2018]
            for year in recent_years:
                if year in available_years and year not in smart_years:
                    smart_years.add(year)
                    break

        return sorted(list(smart_years))

    def explain_year_selection_logic(self, politician, selected_years):
        """Explain the logic behind year selection"""
        first_year = politician['first_election_year']
        last_year = politician['last_election_year']

        print(f"      📝 Selection logic:")

        for year in selected_years:
            if year < first_year:
                print(f"         • {year}: Pre-career baseline (wealth before politics)")
            elif first_year <= year <= last_year:
                print(f"         • {year}: Active period (during political career)")
            elif year > last_year:
                print(f"         • {year}: Post-career analysis (wealth retention)")

    def generate_implementation_recommendations(self):
        """Generate specific implementation recommendations"""
        print("1. Skip years without TSE data packages:")
        print(f"   - SKIP: 2020 (no candidate packages available)")
        print(f"   - USE: {[y for y, c in self.tse_data_availability.items() if c > 0]}")

        print("\n2. Implement politician-specific timeline analysis:")
        print("   - Use first_election_year and last_election_year from unified_politicians")
        print("   - Search 2 years before first election (wealth baseline)")
        print("   - Search during active career (every available election year)")
        print("   - Search 2 years after last election (wealth retention)")

        print("\n3. Fallback strategy for incomplete data:")
        print("   - Default to [2018, 2022, 2024] for politicians without timeline")
        print("   - Ensure at least one recent year for active politicians")

        print("\n4. Performance optimization:")
        print("   - Cache TSE data availability checks")
        print("   - Group politicians by similar timelines")
        print("   - Implement progressive year selection (most recent first)")

        print(f"\n💡 Code implementation:")
        print(f"   Update _calculate_relevant_years() in CLI4WealthPopulator")
        print(f"   Add TSE data availability cache")
        print(f"   Implement politician timeline analysis")

    def demonstrate_code_structure(self):
        """Show the recommended code structure"""
        print(f"\n🔧 RECOMMENDED CODE STRUCTURE")
        print("=" * 40)

        code_example = '''
def _calculate_relevant_years(self, politician: Dict, election_years: List[int]) -> List[int]:
    """Calculate relevant election years based on politician timeline and TSE data availability"""

    # Known years with TSE data (cache this)
    available_years = [2014, 2016, 2018, 2022, 2024]  # Skip 2020

    first_year = politician.get('first_election_year')
    last_year = politician.get('last_election_year')

    if not first_year or not last_year:
        # Fallback for politicians without timeline data
        return [year for year in [2018, 2022, 2024] if year in available_years]

    smart_years = set()

    # Active career years
    for year in available_years:
        if first_year <= year <= last_year:
            smart_years.add(year)

    # Pre-career baseline (2 years before)
    prep_year = first_year - 2
    if prep_year in available_years:
        smart_years.add(prep_year)

    # Post-career analysis (2 years after)
    post_year = last_year + 2
    if post_year in available_years:
        smart_years.add(post_year)

    return sorted(list(smart_years))
        '''

        print(code_example)


def main():
    """Main simulation execution"""
    simulator = WealthYearSelectionSimulator()
    simulator.analyze_optimization_approach()
    simulator.demonstrate_code_structure()


if __name__ == "__main__":
    main()