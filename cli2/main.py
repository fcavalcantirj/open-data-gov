#!/usr/bin/env python3
"""
CLI v2 - Simplified, Sequential Architecture
No complex logging, no concurrency issues, just works.
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


def setup_cli():
    """Setup command line interface"""
    parser = argparse.ArgumentParser(description="Political Transparency Database CLI v2")

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Status
    status_parser = subparsers.add_parser('status', help='Show database status')

    # Populate commands
    pop_parser = subparsers.add_parser('populate', help='Populate database tables')
    pop_subparsers = pop_parser.add_subparsers(dest='table', help='Table to populate')

    # Politicians
    politicians_parser = pop_subparsers.add_parser('politicians', help='Populate politicians')
    politicians_parser.add_argument('--limit', type=int, help='Limit number of politicians')

    # Financial
    financial_parser = pop_subparsers.add_parser('financial', help='Populate financial data')
    financial_parser.add_argument('--limit', type=int, help='Limit number of politicians')

    # All (sequential, simple)
    all_parser = pop_subparsers.add_parser('all', help='Populate all tables sequentially')
    all_parser.add_argument('--limit', type=int, help='Limit number of politicians')

    return parser


def populate_politicians_simple(db_manager, limit=None):
    """Simple politician population - no complex logging"""
    print("🔄 Populating politicians...")

    from cli.modules.politician_populator import PoliticianPopulator
    populator = PoliticianPopulator(db_manager)

    # Simple call, no complex metrics
    created_ids = populator.populate(limit=limit, active_only=True)

    print(f"✅ Politicians: {len(created_ids) if created_ids else 0} processed")
    return True


def populate_financial_simple(db_manager, limit=None):
    """Simple financial population - no complex logging"""
    print("🔄 Populating financial data...")

    # Get politician IDs to process
    if limit:
        result = db_manager.execute_query(
            "SELECT id FROM unified_politicians ORDER BY id DESC LIMIT ?", (limit,)
        )
        politician_ids = [row['id'] for row in result]
    else:
        politician_ids = db_manager.get_all_politician_ids()

    print(f"📋 Processing {len(politician_ids)} politicians")

    # Simple sequential processing
    from cli.modules.financial_populator import FinancialPopulator

    # Create a simplified version that doesn't use enhanced_logger
    class SimpleFinancialPopulator(FinancialPopulator):
        def populate(self, politician_ids=None, start_year=None, end_year=None):
            """Simplified populate without enhanced logging"""
            politicians = self._get_politicians_by_ids(politician_ids) if politician_ids else self._get_all_politicians()

            print(f"💰 Processing {len(politicians)} politicians for financial data")

            processed = 0
            errors = 0

            for politician in politicians:
                try:
                    name = politician.get('name', politician.get('deputy_name', f"ID {politician['id']}"))
                    print(f"  Processing {name}...")

                    # Get financial data
                    deputados_data = self._fetch_deputados_expenses(politician)
                    tse_data = self._fetch_tse_finance_data(politician)

                    # Build records
                    financial_records = self._build_financial_records(
                        politician['id'], deputados_data, tse_data
                    )

                    # Insert records
                    if financial_records:
                        self._insert_financial_records(financial_records)
                        print(f"    ✅ Inserted {len(financial_records)} records")

                    processed += 1

                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    errors += 1

            print(f"📊 Financial Summary: {processed} processed, {errors} errors")
            return True

    populator = SimpleFinancialPopulator(db_manager)
    populator.populate(politician_ids=politician_ids)

    print("✅ Financial data populated")
    return True


def main():
    """Main CLI entry point"""
    parser = setup_cli()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        # Initialize database manager
        db_manager = DatabaseManager()

        if args.command == 'status':
            print("📊 Database Status")
            db_manager.show_status(detailed=True)

        elif args.command == 'populate':
            if not args.table:
                parser.print_help()
                return 1

            if args.table == 'politicians':
                populate_politicians_simple(db_manager, limit=args.limit)

            elif args.table == 'financial':
                populate_financial_simple(db_manager, limit=args.limit)

            elif args.table == 'all':
                print("🚀 Starting simplified sequential population...")

                # Step 1: Politicians
                print("\n1️⃣ POLITICIANS")
                populate_politicians_simple(db_manager, limit=args.limit)

                # Step 2: Financial
                print("\n2️⃣ FINANCIAL")
                populate_financial_simple(db_manager, limit=args.limit)

                print("\n🎯 COMPLETE! All tables populated successfully.")

            else:
                print(f"❌ Unknown table: {args.table}")
                return 1

        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        print("✅ Operation completed")
        return 0

    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())