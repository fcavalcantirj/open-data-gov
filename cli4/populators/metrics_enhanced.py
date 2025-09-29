"""
Enhanced CLI4 Post-Processor - Calculate Comprehensive Aggregate Fields
NOW INCLUDES: Corruption detection, family networks, career analysis, wealth progression
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker


class EnhancedCLI4PostProcessor:
    """Enhanced post-processor for 13-table architecture with corruption detection"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter

    def calculate_aggregate_fields(self, politician_ids: Optional[List[int]] = None,
                                 fields: str = 'all', force_refresh: bool = False) -> int:
        """Enhanced calculation with corruption detection and family networks"""

        print("📊 ENHANCED AGGREGATE FIELDS CALCULATION")
        print("=" * 70)
        print("Computing electoral, financial, corruption, family network, and career metrics")
        print()

        # Check dependencies for comprehensive analysis
        required_deps = ["politicians"]
        if fields in ['electoral', 'all']:
            required_deps.extend(["electoral"])
        if fields in ['financial', 'all']:
            required_deps.extend(["financial"])
        if fields in ['corruption', 'all']:
            required_deps.extend(["sanctions", "tcu"])
        if fields in ['networks', 'all']:
            required_deps.extend(["networks", "senado"])
        if fields in ['career', 'all']:
            required_deps.extend(["career", "professional", "events"])
        if fields in ['wealth', 'all']:
            required_deps.extend(["assets"])

        DependencyChecker.print_dependency_warning(
            required_steps=required_deps,
            current_step="ENHANCED POST-PROCESSING"
        )

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = self._get_politicians_needing_calculation(force_refresh)

        print(f"👥 Processing {len(politicians)} politicians")
        print(f"🔧 Enhanced fields to calculate: {fields}")
        print(f"🔄 Force refresh: {force_refresh}")
        print()

        updated_count = 0
        for i, politician in enumerate(politicians, 1):
            print(f"\n👤 [{i}/{len(politicians)}] Processing: {politician['nome_civil'][:40]}")
            print(f"   CPF: {politician['cpf']} | ID: {politician['id']}")

            try:
                updates = {}

                # Original fields
                if fields in ['electoral', 'all']:
                    electoral_updates = self._calculate_electoral_fields(politician['id'])
                    updates.update(electoral_updates)

                if fields in ['financial', 'all']:
                    financial_updates = self._calculate_financial_fields(politician['id'])
                    updates.update(financial_updates)

                # NEW: Corruption Detection Fields
                if fields in ['corruption', 'all']:
                    corruption_updates = self._calculate_corruption_fields(politician['id'], politician['cpf'])
                    updates.update(corruption_updates)

                # NEW: Family Network Fields
                if fields in ['networks', 'all']:
                    network_updates = self._calculate_network_fields(politician['id'], politician['nome_civil'])
                    updates.update(network_updates)

                # NEW: Career Progression Fields
                if fields in ['career', 'all']:
                    career_updates = self._calculate_career_fields(politician['id'])
                    updates.update(career_updates)

                # NEW: Wealth Progression Fields
                if fields in ['wealth', 'all']:
                    wealth_updates = self._calculate_wealth_fields(politician['id'])
                    updates.update(wealth_updates)

                # Update politician record
                if updates:
                    self._update_politician_fields(politician['id'], updates)
                    updated_count += 1
                    self._print_calculated_fields(updates)

                    self.logger.log_processing(
                        'enhanced_post_processing', str(politician['id']), 'success',
                        {'fields_updated': list(updates.keys()), 'politician_name': politician['nome_civil']}
                    )
                else:
                    print("   ⏭️ No updates needed")

            except Exception as e:
                print(f"   ❌ Error processing politician {politician['id']}: {e}")
                continue

            self.rate_limiter.wait_if_needed('default')

        print(f"\n✅ ENHANCED POST-PROCESSING COMPLETED")
        print(f"   Politicians updated: {updated_count}")
        print(f"   Enhanced fields calculated: {fields}")

        return updated_count

    def _calculate_corruption_fields(self, politician_id: int, cpf: str) -> Dict:
        """NEW: Calculate corruption detection metrics"""
        print("   🚨 Calculating corruption detection fields...")

        corruption_metrics = {}

        # TCU disqualifications check
        tcu_records = database.execute_query("""
            SELECT COUNT(*) as total_disqualifications,
                   COUNT(CASE WHEN data_final IS NULL OR data_final > CURRENT_DATE THEN 1 END) as active_disqualifications,
                   MIN(data_transito_julgado) as first_disqualification,
                   MAX(data_transito_julgado) as latest_disqualification
            FROM tcu_disqualifications
            WHERE cpf = %s
        """, (cpf,))

        if tcu_records and tcu_records[0]['total_disqualifications'] > 0:
            tcu_data = tcu_records[0]
            corruption_metrics.update({
                'tcu_disqualifications_total': tcu_data['total_disqualifications'],
                'tcu_disqualifications_active': tcu_data['active_disqualifications'],
                'tcu_first_disqualification': tcu_data['first_disqualification'],
                'tcu_latest_disqualification': tcu_data['latest_disqualification']
            })
            print(f"      🚨 TCU: {tcu_data['total_disqualifications']} disqualifications ({tcu_data['active_disqualifications']} active)")
        else:
            corruption_metrics.update({
                'tcu_disqualifications_total': 0,
                'tcu_disqualifications_active': 0
            })
            print("      ✅ TCU: Clean record")

        # Vendor sanctions correlation
        sanctioned_vendors = database.execute_query("""
            SELECT COUNT(DISTINCT vs.cnpj_cpf) as sanctioned_vendors,
                   COUNT(*) as total_sanctions,
                   SUM(fr.amount) as sanctioned_vendor_amount
            FROM unified_financial_records fr
            JOIN vendor_sanctions vs ON fr.counterpart_cnpj_cpf = vs.cnpj_cpf
            WHERE fr.politician_id = %s
            AND vs.is_active = TRUE
        """, (politician_id,))

        if sanctioned_vendors and sanctioned_vendors[0]['sanctioned_vendors'] > 0:
            sanctions_data = sanctioned_vendors[0]
            corruption_metrics.update({
                'sanctioned_vendors_count': sanctions_data['sanctioned_vendors'],
                'sanctioned_vendors_total_sanctions': sanctions_data['total_sanctions'],
                'sanctioned_vendors_amount': sanctions_data['sanctioned_vendor_amount']
            })
            print(f"      🚨 SANCTIONS: {sanctions_data['sanctioned_vendors']} sanctioned vendors, R$ {sanctions_data['sanctioned_vendor_amount']:,.2f}")
        else:
            corruption_metrics.update({
                'sanctioned_vendors_count': 0,
                'sanctioned_vendors_total_sanctions': 0,
                'sanctioned_vendors_amount': 0
            })
            print("      ✅ SANCTIONS: Clean vendor record")

        # Calculate corruption risk score
        risk_score = self._calculate_corruption_risk_score(corruption_metrics)
        corruption_metrics['corruption_risk_score'] = risk_score
        print(f"      📊 Corruption Risk Score: {risk_score}/100")

        return corruption_metrics

    def _calculate_network_fields(self, politician_id: int, nome_civil: str) -> Dict:
        """NEW: Calculate family/business network metrics"""
        print("   👨‍👩‍👧‍👦 Calculating family network fields...")

        network_metrics = {}

        # TODO: Implement proper family detection with multiple factors:
        # - Birth location correlation
        # - Age/generation analysis
        # - Multiple surname matching (not just last name)
        # - Direct family indicators (FILHO, JUNIOR, NETO)
        # - Exclude common surnames (SILVA, SANTOS, etc) without additional evidence
        # Current implementation is BROKEN - produces massive false positives

        # Set to -1 to indicate TODO/unreliable data
        network_metrics['family_senators_count'] = -1
        network_metrics['family_deputies_count'] = -1
        network_metrics['family_parties_senado'] = 'TODO'
        network_metrics['family_parties_camara'] = 'TODO'
        print("      ⚠️ FAMILY: Set to -1 (TODO - current surname matching is unreliable)")

        # Political network diversity
        political_networks = database.execute_query("""
            SELECT COUNT(DISTINCT network_type) as network_types,
                   COUNT(*) as total_networks,
                   COUNT(CASE WHEN is_leadership = TRUE THEN 1 END) as leadership_positions
            FROM unified_political_networks
            WHERE politician_id = %s
        """, (politician_id,))

        if political_networks and political_networks[0]['total_networks'] > 0:
            net_data = political_networks[0]
            network_metrics.update({
                'political_network_types': net_data['network_types'],
                'total_political_networks': net_data['total_networks'],
                'leadership_positions_count': net_data['leadership_positions']
            })
            print(f"      🏛️ NETWORKS: {net_data['total_networks']} networks, {net_data['leadership_positions']} leadership roles")

        return network_metrics

    def _calculate_career_fields(self, politician_id: int) -> Dict:
        """NEW: Calculate comprehensive career progression metrics"""
        print("   💼 Calculating career progression fields...")

        career_metrics = {}

        # Career diversity analysis
        career_data = database.execute_query("""
            SELECT COUNT(DISTINCT office_name) as unique_offices,
                   COUNT(*) as total_mandates,
                   MIN(start_year) as career_start_year,
                   MAX(end_year) as career_latest_year,
                   COUNT(DISTINCT state) as states_served
            FROM politician_career_history
            WHERE politician_id = %s
        """, (politician_id,))

        if career_data and career_data[0]['total_mandates'] > 0:
            career = career_data[0]
            career_span = (career['career_latest_year'] or datetime.now().year) - (career['career_start_year'] or datetime.now().year)

            career_metrics.update({
                'career_unique_offices': career['unique_offices'],
                'career_total_mandates': career['total_mandates'],
                'career_start_year': career['career_start_year'],
                'career_latest_year': career['career_latest_year'],
                'career_span_years': max(career_span, 0),
                'career_states_served': career['states_served']
            })
            print(f"      💼 CAREER: {career['total_mandates']} mandates, {career['unique_offices']} offices, {career_span} years")

        # Professional background diversity
        professional_data = database.execute_query("""
            SELECT COUNT(DISTINCT profession_type) as profession_types,
                   COUNT(*) as total_professions,
                   STRING_AGG(DISTINCT profession_name, ', ') as profession_list
            FROM politician_professional_background
            WHERE politician_id = %s
        """, (politician_id,))

        if professional_data and professional_data[0]['total_professions'] > 0:
            prof = professional_data[0]
            career_metrics.update({
                'professional_background_types': prof['profession_types'],
                'professional_background_total': prof['total_professions'],
                'professional_background_list': prof['profession_list']
            })
            print(f"      🎓 PROFESSIONS: {prof['total_professions']} backgrounds")

        # Parliamentary activity level
        events_data = database.execute_query("""
            SELECT COUNT(*) as total_events,
                   COUNT(DISTINCT event_type) as event_types,
                   COUNT(CASE WHEN attendance_confirmed = TRUE THEN 1 END) as confirmed_attendance
            FROM politician_events
            WHERE politician_id = %s
        """, (politician_id,))

        if events_data and events_data[0]['total_events'] > 0:
            events = events_data[0]
            attendance_rate = (events['confirmed_attendance'] / events['total_events'] * 100) if events['total_events'] > 0 else 0

            career_metrics.update({
                'parliamentary_events_total': events['total_events'],
                'parliamentary_event_types': events['event_types'],
                'parliamentary_attendance_rate': attendance_rate
            })
            print(f"      🏛️ PARLIAMENT: {events['total_events']} events, {attendance_rate:.1f}% attendance")

        return career_metrics

    def _calculate_wealth_fields(self, politician_id: int) -> Dict:
        """NEW: Calculate wealth progression and asset diversity"""
        print("   💎 Calculating wealth progression fields...")

        wealth_metrics = {}

        # Wealth progression analysis
        wealth_progression = database.execute_query("""
            SELECT COUNT(*) as wealth_declarations,
                   MIN(year) as first_wealth_year,
                   MAX(year) as latest_wealth_year,
                   MIN(total_declared_wealth) as lowest_wealth,
                   MAX(total_declared_wealth) as highest_wealth,
                   AVG(total_declared_wealth) as average_wealth
            FROM unified_wealth_tracking
            WHERE politician_id = %s
        """, (politician_id,))

        if wealth_progression and wealth_progression[0]['wealth_declarations'] > 0:
            wealth = wealth_progression[0]
            wealth_growth = wealth['highest_wealth'] - wealth['lowest_wealth'] if wealth['highest_wealth'] and wealth['lowest_wealth'] else 0

            wealth_metrics.update({
                'wealth_declarations_count': wealth['wealth_declarations'],
                'wealth_first_year': wealth['first_wealth_year'],
                'wealth_latest_year': wealth['latest_wealth_year'],
                'wealth_lowest_declared': wealth['lowest_wealth'],
                'wealth_highest_declared': wealth['highest_wealth'],
                'wealth_average_declared': wealth['average_wealth'],
                'wealth_total_growth': wealth_growth
            })
            print(f"      💎 WEALTH: {wealth['wealth_declarations']} declarations, R$ {wealth_growth:,.2f} growth")

        # Asset diversity analysis
        asset_diversity = database.execute_query("""
            SELECT COUNT(DISTINCT asset_type_description) as asset_types,
                   COUNT(*) as total_assets,
                   SUM(declared_value) as total_asset_value,
                   AVG(declared_value) as average_asset_value
            FROM politician_assets
            WHERE politician_id = %s
        """, (politician_id,))

        if asset_diversity and asset_diversity[0]['total_assets'] > 0:
            assets = asset_diversity[0]
            wealth_metrics.update({
                'asset_types_diversity': assets['asset_types'],
                'total_individual_assets': assets['total_assets'],
                'total_individual_asset_value': assets['total_asset_value'],
                'average_individual_asset_value': assets['average_asset_value']
            })
            print(f"      🏠 ASSETS: {assets['total_assets']} assets, {assets['asset_types']} types")

        return wealth_metrics

    def _calculate_corruption_risk_score(self, corruption_metrics: Dict) -> float:
        """Calculate corruption risk score (0-100, higher = more risk)"""
        score = 0

        # TCU disqualifications (high weight)
        if corruption_metrics.get('tcu_disqualifications_total', 0) > 0:
            score += 40
            if corruption_metrics.get('tcu_disqualifications_active', 0) > 0:
                score += 20

        # Sanctioned vendors (high weight)
        if corruption_metrics.get('sanctioned_vendors_count', 0) > 0:
            score += 30
            # Additional points for high amounts or multiple vendors
            if corruption_metrics.get('sanctioned_vendors_count', 0) > 2:
                score += 10

        return min(score, 100)  # Cap at 100

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs"""
        placeholders = ','.join(['%s'] * len(politician_ids))
        query = f"SELECT id, cpf, nome_civil FROM unified_politicians WHERE id IN ({placeholders})"
        return database.execute_query(query, tuple(politician_ids))

    def _get_politicians_needing_calculation(self, force_refresh: bool) -> List[Dict]:
        """Get politicians that need enhanced aggregate field calculation"""
        if force_refresh:
            query = "SELECT id, cpf, nome_civil FROM unified_politicians WHERE cpf IS NOT NULL ORDER BY id"
        else:
            # Check for missing any of the new enhanced fields
            query = """
                SELECT id, cpf, nome_civil
                FROM unified_politicians
                WHERE cpf IS NOT NULL
                AND (
                    first_election_year IS NULL OR
                    last_election_year IS NULL OR
                    tcu_disqualifications_total IS NULL OR
                    sanctioned_vendors_count IS NULL OR
                    corruption_risk_score IS NULL
                )
                ORDER BY id
            """
        return database.execute_query(query)

    def _calculate_electoral_fields(self, politician_id: int) -> Dict:
        """Calculate electoral aggregate fields"""
        print("   📊 Calculating electoral fields...")

        # Get electoral records for this politician
        electoral_records = database.execute_query("""
            SELECT
                election_year,
                electoral_outcome,
                candidacy_status,
                position_description
            FROM unified_electoral_records
            WHERE politician_id = %s
            ORDER BY election_year
        """, (politician_id,))

        if not electoral_records:
            print("      ⚠️ No electoral records found")
            return {}

        # Calculate fields
        election_years = [record['election_year'] for record in electoral_records]
        first_election_year = min(election_years)
        last_election_year = max(election_years)
        number_of_elections = len(electoral_records)

        # Calculate electoral success (count wins)
        wins = 0
        for record in electoral_records:
            # Check for winning status in final result or candidacy status
            electoral_outcome = (record.get('electoral_outcome') or '').upper()
            candidacy_status = (record.get('candidacy_status') or '').upper()

            # Common winning patterns in TSE data
            if ('ELEITO' in electoral_outcome or 'ELEITO' in candidacy_status):
                wins += 1

        electoral_success_rate = (wins / number_of_elections * 100) if number_of_elections > 0 else 0

        print(f"      ✅ Elections: {number_of_elections} ({first_election_year}-{last_election_year})")
        print(f"      🏆 Success rate: {electoral_success_rate:.1f}% ({wins} wins)")

        # Calculate first mandate year (first time elected)
        first_mandate_year = None
        for record in electoral_records:
            electoral_outcome = (record.get('electoral_outcome') or '').upper()
            candidacy_status = (record.get('candidacy_status') or '').upper()
            if 'ELEITO' in electoral_outcome or 'ELEITO' in candidacy_status:
                if not first_mandate_year or record['election_year'] < first_mandate_year:
                    first_mandate_year = record['election_year']

        return {
            'first_election_year': first_election_year,
            'last_election_year': last_election_year,
            'number_of_elections': number_of_elections,
            'total_elections': number_of_elections,  # Map to both field names
            'electoral_success_rate': electoral_success_rate,
            'first_mandate_year': first_mandate_year  # New field for first elected position
        }

    def _calculate_financial_fields(self, politician_id: int) -> Dict:
        """Calculate financial aggregate fields"""
        print("   💰 Calculating financial fields...")

        # Get financial summary for this politician
        financial_summary = database.execute_query("""
            SELECT
                COUNT(*) as total_transactions,
                SUM(amount) as total_amount,
                MIN(transaction_date) as first_transaction,
                MAX(transaction_date) as last_transaction,
                COUNT(DISTINCT counterpart_cnpj_cpf) as unique_counterparts
            FROM unified_financial_records
            WHERE politician_id = %s
        """, (politician_id,))

        if not financial_summary or not financial_summary[0]['total_transactions']:
            print("      ⚠️ No financial records found")
            return {}

        summary = financial_summary[0]
        print(f"      ✅ Transactions: {summary['total_transactions']}")
        print(f"      💵 Total amount: R$ {summary['total_amount']:,.2f}")
        print(f"      🤝 Unique counterparts: {summary['unique_counterparts']}")

        return {
            'total_financial_transactions': summary['total_transactions'],
            'total_financial_amount': summary['total_amount'],
            'financial_counterparts_count': summary['unique_counterparts'],
            'first_transaction_date': summary['first_transaction'],
            'last_transaction_date': summary['last_transaction']
        }

    def _update_politician_fields(self, politician_id: int, updates: Dict):
        """Update politician record with calculated fields"""
        if not updates:
            return

        set_clauses = []
        values = []
        for field, value in updates.items():
            set_clauses.append(f"{field} = %s")
            values.append(value)

        set_clauses.append("updated_at = %s")
        values.append(datetime.now())
        values.append(politician_id)

        query = f"""
            UPDATE unified_politicians
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """

        database.execute_update(query, tuple(values))

    def _print_calculated_fields(self, updates: Dict):
        """Print the calculated field values with enhanced formatting"""
        print("      📊 Enhanced calculated fields:")

        # Group fields by category for better readability
        categories = {
            'Electoral': [k for k in updates.keys() if any(term in k.lower() for term in ['election', 'electoral', 'success'])],
            'Financial': [k for k in updates.keys() if any(term in k.lower() for term in ['financial', 'transaction', 'amount', 'counterpart'])],
            'Corruption': [k for k in updates.keys() if any(term in k.lower() for term in ['tcu', 'sanction', 'corruption', 'risk'])],
            'Networks': [k for k in updates.keys() if any(term in k.lower() for term in ['family', 'network', 'leadership'])],
            'Career': [k for k in updates.keys() if any(term in k.lower() for term in ['career', 'professional', 'parliamentary', 'mandate'])],
            'Wealth': [k for k in updates.keys() if any(term in k.lower() for term in ['wealth', 'asset'])]
        }

        for category, fields in categories.items():
            if fields:
                print(f"         {category}:")
                for field in fields:
                    value = updates[field]
                    if isinstance(value, float):
                        print(f"           {field}: {value:.2f}")
                    else:
                        print(f"           {field}: {value}")


def main():
    """Standalone test of enhanced post-processor"""
    print("🧪 TESTING ENHANCED POST-PROCESSOR")
    print("=" * 50)

    from cli4.modules.logger import CLI4Logger
    from cli4.modules.rate_limiter import CLI4RateLimiter

    logger = CLI4Logger()
    rate_limiter = CLI4RateLimiter()

    processor = EnhancedCLI4PostProcessor(logger, rate_limiter)

    # Test with limited politicians
    result = processor.calculate_aggregate_fields(politician_ids=[1, 2, 3], fields='all')
    print(f"\n🎯 Test completed: {result} politicians updated")


if __name__ == "__main__":
    main()