#!/usr/bin/env python3
"""
CLI v2 - Complete Implementation
Simple, sequential, no-hanging architecture
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

from cli.modules.database_manager import DatabaseManager


def populate_politicians_v2(db_manager, limit=None):
    """Simplified politician population without enhanced_logger"""
    print("🔄 CLI v2: Populating politicians...")

    try:
        from cli.modules.politician_populator import PoliticianPopulator

        # Create a simplified version
        class SimplePoliticianPopulator(PoliticianPopulator):
            def populate(self, limit=None, start_id=None, active_only=True):
                """Simplified populate without enhanced logging"""
                print(f"👥 Starting politician population (limit: {limit})")

                try:
                    # Get deputies from API
                    deputies_response = self.deputados_client.get_deputies()
                    if not deputies_response or 'dados' not in deputies_response:
                        print("❌ Failed to fetch deputies from API")
                        return []

                    deputies = deputies_response['dados']
                    if limit:
                        deputies = deputies[:limit]

                    print(f"📋 Processing {len(deputies)} deputies")

                    created_ids = []
                    processed = 0
                    skipped = 0
                    errors = 0

                    for deputy in deputies:
                        try:
                            deputy_id = deputy.get('id')
                            deputy_name = deputy.get('nome', 'Unknown')

                            print(f"  Processing {deputy_name} (ID: {deputy_id})")

                            # Check if already exists
                            existing = self.db_manager.execute_query(
                                "SELECT id FROM unified_politicians WHERE deputados_id = ?",
                                (deputy_id,)
                            )

                            if existing:
                                print(f"    ⏭️ Already exists")
                                skipped += 1
                                continue

                            # Get detailed profile
                            profile = self.deputados_client.get_deputy_details(deputy_id)
                            if not profile:
                                print(f"    ❌ Failed to get profile")
                                errors += 1
                                continue

                            # Create politician record
                            politician_data = self._build_politician_record(deputy, profile)
                            politician_id = self._insert_politician(politician_data)

                            if politician_id:
                                created_ids.append(politician_id)
                                print(f"    ✅ Created politician {politician_id}")
                                processed += 1
                            else:
                                print(f"    ❌ Failed to create politician")
                                errors += 1

                        except Exception as e:
                            print(f"    ❌ Error processing {deputy.get('nome', 'Unknown')}: {e}")
                            errors += 1

                    print(f"\n📊 Summary: {processed} created, {skipped} skipped, {errors} errors")
                    return created_ids

                except Exception as e:
                    print(f"❌ Population failed: {e}")
                    return []

        populator = SimplePoliticianPopulator(db_manager)
        result = populator.populate(limit=limit, active_only=True)

        print(f"✅ Politicians populated: {len(result) if result else 0}")
        return True

    except Exception as e:
        print(f"❌ Politician population failed: {e}")
        return False


def populate_financial_v2(db_manager, limit=None):
    """Simplified financial population without enhanced_logger"""
    print("🔄 CLI v2: Populating financial data...")

    try:
        # Get politician IDs
        if limit:
            politicians = db_manager.execute_query(
                "SELECT id, name FROM unified_politicians ORDER BY id DESC LIMIT ?", (limit,)
            )
        else:
            politicians = db_manager.execute_query(
                "SELECT id, name FROM unified_politicians ORDER BY id DESC"
            )

        if not politicians:
            print("❌ No politicians found. Run 'populate politicians' first.")
            return False

        print(f"💰 Processing financial data for {len(politicians)} politicians")

        from cli.modules.financial_populator import FinancialPopulator

        # Use the original populator but call it simply without enhanced logging
        class SimpleFinancialPopulator(FinancialPopulator):
            def populate_simple(self, politician_ids):
                """Simple financial population"""
                politicians = self._get_politicians_by_ids(politician_ids)

                processed = 0
                errors = 0

                for politician in politicians:
                    try:
                        name = politician.get('name', f"ID {politician['id']}")
                        print(f"  Processing {name}...")

                        # Get financial data - using parent class methods
                        deputados_data = self._fetch_deputados_expenses(politician)
                        tse_data = self._fetch_tse_finance_data(politician)

                        # Build and insert records
                        financial_records = self._build_financial_records(
                            politician['id'], deputados_data, tse_data
                        )

                        if financial_records:
                            self._insert_financial_records(financial_records)
                            print(f"    ✅ Inserted {len(financial_records)} records")
                        else:
                            print(f"    ⚠️ No financial records found")

                        processed += 1

                    except Exception as e:
                        print(f"    ❌ Error: {e}")
                        errors += 1

                print(f"\n💰 Financial Summary: {processed} processed, {errors} errors")
                return True

        populator = SimpleFinancialPopulator(db_manager)
        politician_ids = [p['id'] for p in politicians]
        result = populator.populate_simple(politician_ids)

        print("✅ Financial data populated")
        return result

    except Exception as e:
        print(f"❌ Financial population failed: {e}")
        return False


def main():
    """Main CLI v2 entry point"""
    parser = argparse.ArgumentParser(description="CLI v2 - Simple & Reliable")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status
    status_parser = subparsers.add_parser('status', help='Show database status')

    # Populate
    pop_parser = subparsers.add_parser('populate', help='Populate database')
    pop_subparsers = pop_parser.add_subparsers(dest='table', help='Table to populate')

    # Politicians
    politicians_parser = pop_subparsers.add_parser('politicians', help='Populate politicians')
    politicians_parser.add_argument('--limit', type=int, help='Limit number')

    # Financial
    financial_parser = pop_subparsers.add_parser('financial', help='Populate financial')
    financial_parser.add_argument('--limit', type=int, help='Limit number')

    # All
    all_parser = pop_subparsers.add_parser('all', help='Populate all tables')
    all_parser.add_argument('--limit', type=int, help='Limit number')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        db_manager = DatabaseManager()

        if args.command == 'status':
            print("📊 CLI v2 Database Status")
            db_manager.show_status(detailed=True)

        elif args.command == 'populate':
            if not args.table:
                parser.print_help()
                return 1

            if args.table == 'politicians':
                populate_politicians_v2(db_manager, limit=args.limit)

            elif args.table == 'financial':
                populate_financial_v2(db_manager, limit=args.limit)

            elif args.table == 'all':
                print("🚀 CLI v2: Sequential Population Workflow")

                # Step 1: Politicians
                print("\n1️⃣ POLITICIANS")
                if not populate_politicians_v2(db_manager, limit=args.limit):
                    print("❌ Politicians failed, stopping workflow")
                    return 1

                # Step 2: Financial
                print("\n2️⃣ FINANCIAL")
                if not populate_financial_v2(db_manager, limit=args.limit):
                    print("❌ Financial failed, stopping workflow")
                    return 1

                print("\n🎯 CLI v2: All tables populated successfully!")

            else:
                print(f"❌ Unknown table: {args.table}")
                return 1

        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        print("✅ CLI v2 completed successfully")
        return 0

    except Exception as e:
        print(f"❌ CLI v2 Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())