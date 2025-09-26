#!/usr/bin/env python3
"""
Test script for optimizing wealth populator year selection
Analyzes politician timelines and TSE data availability to improve efficiency
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli4.modules import database
from src.clients.tse_client import TSEClient

class WealthYearSelectionTester:
    """Test and analyze year selection patterns for wealth population"""

    def __init__(self):
        self.tse_client = TSEClient()

    def analyze_current_approach(self, sample_size=10):
        """Analyze current year selection approach"""
        print("🔍 ANALYZING CURRENT YEAR SELECTION APPROACH")
        print("=" * 60)

        # Get sample politicians with different timelines
        politicians = database.execute_query(f"""
            SELECT p.id, p.nome_civil, p.cpf, p.sq_candidato_current,
                   p.first_election_year, p.last_election_year,
                   p.total_candidacies, p.total_mandates
            FROM unified_politicians p
            WHERE p.cpf IS NOT NULL
              AND p.sq_candidato_current IS NOT NULL
              AND p.first_election_year IS NOT NULL
            ORDER BY p.total_candidacies DESC
            LIMIT {sample_size}
        """)

        print(f"📊 Analyzing {len(politicians)} politicians with diverse timelines\n")

        # Current default years
        default_years = [2018, 2020, 2022, 2024]

        results = {
            'politician_analysis': [],
            'tse_data_availability': {},
            'optimization_opportunities': []
        }

        # Test TSE data availability for each year
        print("📅 Testing TSE data availability by year:")
        for year in range(2014, 2025, 2):  # Test even years (election years)
            try:
                asset_data = self.tse_client.get_asset_data(year)
                asset_count = len(asset_data) if asset_data else 0
                results['tse_data_availability'][year] = asset_count

                status = "✅" if asset_count > 0 else "❌"
                print(f"   {status} {year}: {asset_count:,} assets available")

            except Exception as e:
                results['tse_data_availability'][year] = 0
                print(f"   ❌ {year}: Error - {str(e)[:50]}...")

        print("\n👥 Analyzing politician-specific timelines:")

        for politician in politicians:
            timeline = self.analyze_politician_timeline(politician, default_years)
            results['politician_analysis'].append(timeline)

            print(f"\n🏛️ {politician['nome_civil'][:30]}")
            print(f"   Career: {politician['first_election_year']}-{politician['last_election_year']} ({politician['total_candidacies']} candidacies)")
            print(f"   Current approach searches: {default_years}")
            print(f"   Optimal years would be: {timeline['recommended_years']}")
            print(f"   Efficiency gain: {timeline['efficiency_improvement']}")

        # Generate recommendations
        self.generate_recommendations(results)

        return results

    def analyze_politician_timeline(self, politician, default_years):
        """Analyze individual politician timeline and recommend optimal years"""
        first_year = politician.get('first_election_year')
        last_year = politician.get('last_election_year')

        if not first_year or not last_year:
            return {
                'politician_id': politician['id'],
                'recommended_years': default_years,
                'efficiency_improvement': "No timeline data available"
            }

        # Calculate smart year selection
        recommended_years = []

        # 1. Add years during active period (every 4 years for federal, 2 years overlap)
        current_year = first_year
        while current_year <= last_year:
            if current_year >= 2014:  # TSE data availability threshold
                recommended_years.append(current_year)
            current_year += 2  # Check every 2 years

        # 2. Add 2 years before first election (financial preparation)
        prep_year = first_year - 2
        if prep_year >= 2014 and prep_year not in recommended_years:
            recommended_years.insert(0, prep_year)

        # 3. Add 2 years after last election (wealth retention analysis)
        post_year = last_year + 2
        if post_year <= 2024 and post_year not in recommended_years:
            recommended_years.append(post_year)

        # Remove years with no TSE data
        available_years = []
        for year in sorted(set(recommended_years)):
            # Check if we have data for this year (simplified check)
            if year in [2014, 2016, 2018, 2022, 2024]:  # Known good years
                available_years.append(year)

        # Calculate efficiency improvement
        default_searches = len(default_years)
        optimal_searches = len(available_years)

        if optimal_searches < default_searches:
            efficiency = f"Reduce searches by {default_searches - optimal_searches} years ({((default_searches - optimal_searches) / default_searches) * 100:.1f}% fewer)"
        elif optimal_searches > default_searches:
            efficiency = f"Add {optimal_searches - default_searches} years for complete coverage ({((optimal_searches - default_searches) / default_searches) * 100:.1f}% more thorough)"
        else:
            efficiency = "Same number of searches, but better targeted"

        return {
            'politician_id': politician['id'],
            'first_election_year': first_year,
            'last_election_year': last_year,
            'default_years': default_years,
            'recommended_years': available_years,
            'efficiency_improvement': efficiency
        }

    def generate_recommendations(self, results):
        """Generate optimization recommendations"""
        print("\n📈 OPTIMIZATION RECOMMENDATIONS")
        print("=" * 50)

        # TSE Data recommendations
        good_years = [year for year, count in results['tse_data_availability'].items() if count > 0]
        bad_years = [year for year, count in results['tse_data_availability'].items() if count == 0]

        print(f"✅ Years with TSE data: {good_years}")
        print(f"❌ Years without data (skip): {bad_years}")

        # Politician-specific recommendations
        total_politicians = len(results['politician_analysis'])
        if total_politicians > 0:
            # Calculate average efficiency gains
            efficiency_gains = []
            for analysis in results['politician_analysis']:
                default_count = len(analysis['default_years'])
                optimal_count = len(analysis['recommended_years'])
                gain = default_count - optimal_count
                efficiency_gains.append(gain)

            avg_reduction = sum(efficiency_gains) / len(efficiency_gains)
            print(f"\n📊 Average year reduction per politician: {avg_reduction:.1f} years")

            if avg_reduction > 0:
                print(f"💰 Potential efficiency gain: {avg_reduction:.1f} fewer API calls per politician")

        print("\n🚀 IMPLEMENTATION STRATEGY:")
        print("1. Skip years without TSE data packages (2020)")
        print("2. Use politician timeline analysis for targeted searches")
        print("3. Add 2 years before/after active periods for complete wealth tracking")
        print("4. Default to safe years [2018, 2022, 2024] for politicians without timeline data")

    def test_enhanced_algorithm(self, politician_id=None):
        """Test the enhanced year selection algorithm"""
        print("\n🧪 TESTING ENHANCED YEAR SELECTION ALGORITHM")
        print("=" * 60)

        if politician_id:
            politicians = database.execute_query("""
                SELECT id, nome_civil, cpf, sq_candidato_current,
                       first_election_year, last_election_year, total_candidacies
                FROM unified_politicians
                WHERE id = %s
            """, (politician_id,))
        else:
            # Get a few test politicians
            politicians = database.execute_query("""
                SELECT id, nome_civil, cpf, sq_candidato_current,
                       first_election_year, last_election_year, total_candidacies
                FROM unified_politicians
                WHERE cpf IS NOT NULL AND first_election_year IS NOT NULL
                ORDER BY total_candidacies DESC
                LIMIT 3
            """)

        for politician in politicians:
            print(f"\n🏛️ Testing: {politician['nome_civil']}")

            # Current approach
            current_years = [2018, 2020, 2022, 2024]

            # Enhanced approach
            enhanced_years = self.calculate_smart_years(politician)

            print(f"   Current: {current_years} ({len(current_years)} searches)")
            print(f"   Enhanced: {enhanced_years} ({len(enhanced_years)} searches)")

            # Simulate API efficiency
            current_calls = len(current_years)
            enhanced_calls = len(enhanced_years)

            if enhanced_calls < current_calls:
                savings = current_calls - enhanced_calls
                print(f"   💰 Efficiency gain: {savings} fewer API calls ({(savings/current_calls)*100:.1f}% reduction)")
            elif enhanced_calls > current_calls:
                additional = enhanced_calls - current_calls
                print(f"   📈 Comprehensive gain: {additional} more searches for complete coverage")
            else:
                print(f"   ⚖️ Same number of calls but better targeted")

    def calculate_smart_years(self, politician):
        """Calculate smart year selection for a politician"""
        first_year = politician.get('first_election_year')
        last_year = politician.get('last_election_year')

        # Known years with TSE data
        available_years = [2014, 2016, 2018, 2022, 2024]

        if not first_year or not last_year:
            # Default to safe years if no timeline
            return [year for year in [2018, 2022, 2024] if year in available_years]

        smart_years = set()

        # Add active period years
        for year in available_years:
            if first_year <= year <= last_year:
                smart_years.add(year)

        # Add preparation year (2 years before first election)
        prep_year = first_year - 2
        if prep_year in available_years:
            smart_years.add(prep_year)

        # Add post-career year (2 years after last election)
        post_year = last_year + 2
        if post_year in available_years:
            smart_years.add(post_year)

        return sorted(list(smart_years))


def main():
    """Main test execution"""
    print("🧪 WEALTH YEAR SELECTION OPTIMIZATION TEST")
    print("=" * 60)
    print("Analyzing current approach and proposing optimizations")
    print()

    tester = WealthYearSelectionTester()

    # Run analysis
    results = tester.analyze_current_approach(sample_size=5)

    # Test enhanced algorithm
    tester.test_enhanced_algorithm()

    print(f"\n✅ Analysis completed. Review recommendations above.")
    print(f"💡 Next step: Implement optimized _calculate_relevant_years() method")


if __name__ == "__main__":
    main()