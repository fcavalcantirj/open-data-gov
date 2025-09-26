"""
CLI4 Post-Processor - Calculate Aggregate Career Fields
Computes electoral success rates, career timelines, and financial summaries
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker


class CLI4PostProcessor:
    """Calculate aggregate career fields for politicians table"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter

    def calculate_aggregate_fields(self, politician_ids: Optional[List[int]] = None,
                                 fields: str = 'all', force_refresh: bool = False) -> int:
        """Calculate aggregate career fields for politicians"""

        print("📊 AGGREGATE CAREER FIELDS CALCULATION")
        print("=" * 60)
        print("Calculating electoral success rates, career timelines, and financial summaries")
        print()

        # Check dependencies - needs electoral and/or financial data
        required_deps = ["politicians"]
        if fields in ['electoral', 'all']:
            required_deps.append("electoral")
        if fields in ['financial', 'all']:
            required_deps.append("financial")

        DependencyChecker.print_dependency_warning(
            required_steps=required_deps,
            current_step="POST-PROCESSING"
        )

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            # Get politicians with missing aggregate fields or force refresh
            politicians = self._get_politicians_needing_calculation(force_refresh)

        print(f"👥 Processing {len(politicians)} politicians")
        print(f"🔧 Fields to calculate: {fields}")
        print(f"🔄 Force refresh: {force_refresh}")
        print()

        updated_count = 0
        skipped_count = 0

        for i, politician in enumerate(politicians, 1):
            print(f"\n👤 [{i}/{len(politicians)}] Processing: {politician['nome_civil'][:40]}")
            print(f"   CPF: {politician['cpf']} | ID: {politician['id']}")

            try:
                # Calculate fields based on request
                updates = {}

                if fields in ['electoral', 'all']:
                    electoral_updates = self._calculate_electoral_fields(politician['id'])
                    updates.update(electoral_updates)

                if fields in ['financial', 'all']:
                    financial_updates = self._calculate_financial_fields(politician['id'])
                    updates.update(financial_updates)

                # Update politician record
                if updates:
                    self._update_politician_fields(politician['id'], updates)
                    updated_count += 1

                    # Show calculated values
                    self._print_calculated_fields(updates)

                    self.logger.log_processing(
                        'post_processing', str(politician['id']), 'success',
                        {'fields_updated': list(updates.keys()), 'politician_name': politician['nome_civil']}
                    )
                else:
                    print("   ⏭️ No updates needed")
                    skipped_count += 1

            except Exception as e:
                print(f"   ❌ Error processing politician {politician['id']}: {e}")
                self.logger.log_processing(
                    'post_processing', str(politician['id']), 'error',
                    {'error': str(e)}
                )
                continue

            # Rate limiting between politicians
            self.rate_limiter.wait_if_needed('default')

        print(f"\n✅ POST-PROCESSING COMPLETED")
        print(f"   Politicians updated: {updated_count}")
        print(f"   Politicians skipped: {skipped_count}")
        print(f"   Fields calculated: {fields}")

        return updated_count

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs"""
        placeholders = ','.join(['%s'] * len(politician_ids))
        query = f"SELECT id, cpf, nome_civil FROM unified_politicians WHERE id IN ({placeholders})"
        return database.execute_query(query, tuple(politician_ids))

    def _get_politicians_needing_calculation(self, force_refresh: bool) -> List[Dict]:
        """Get politicians that need aggregate field calculation"""
        if force_refresh:
            # Get all politicians with CPF (needed for correlation)
            query = "SELECT id, cpf, nome_civil FROM unified_politicians WHERE cpf IS NOT NULL ORDER BY id"
        else:
            # Get politicians missing key aggregate fields
            query = """
                SELECT id, cpf, nome_civil
                FROM unified_politicians
                WHERE cpf IS NOT NULL
                AND (
                    first_election_year IS NULL OR
                    last_election_year IS NULL OR
                    number_of_elections IS NULL OR
                    electoral_success_rate IS NULL
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

        return {
            'first_election_year': first_election_year,
            'last_election_year': last_election_year,
            'number_of_elections': number_of_elections,
            'electoral_success_rate': electoral_success_rate
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

        # Build SET clause
        set_clauses = []
        values = []
        for field, value in updates.items():
            set_clauses.append(f"{field} = %s")
            values.append(value)

        # Add updated_at timestamp
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
        """Print the calculated field values"""
        print("      📊 Calculated fields:")
        for field, value in updates.items():
            if isinstance(value, float):
                print(f"         {field}: {value:.2f}")
            elif isinstance(value, (datetime, type(None))):
                print(f"         {field}: {value}")
            else:
                print(f"         {field}: {value}")