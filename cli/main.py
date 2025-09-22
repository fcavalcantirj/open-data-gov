#!/usr/bin/env python3
"""
Political Transparency Database CLI
Modular CLI system for populating the unified political transparency database
Following the DATA_POPULATION_GUIDE.md with clean separation of concerns
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(project_root / '.env')

from cli.modules.database_manager import DatabaseManager
from cli.modules.politician_populator import PoliticianPopulator
from cli.modules.financial_populator import FinancialPopulator
from cli.modules.network_populator import NetworkPopulator
from cli.modules.wealth_populator import WealthPopulator
from cli.modules.career_populator import CareerPopulator
from cli.modules.event_populator import EventPopulator
from cli.modules.asset_populator import AssetPopulator
from cli.modules.professional_populator import ProfessionalPopulator
from cli.modules.validation_manager import ValidationManager


def setup_cli():
    """Setup command line interface with all modules"""
    parser = argparse.ArgumentParser(
        description="Political Transparency Database CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database
  python cli/main.py init-db

  # Populate politicians (foundation table - run first)
  python cli/main.py populate politicians --limit 10

  # Populate specific table
  python cli/main.py populate financial

  # Full population workflow
  python cli/main.py populate all

  # Validate data integrity
  python cli/main.py validate

  # Status report
  python cli/main.py status
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Database initialization
    init_parser = subparsers.add_parser('init-db', help='Initialize database with schema')
    init_parser.add_argument('--force', action='store_true', help='Force recreation of existing database')

    # Clear database
    clear_parser = subparsers.add_parser('clear-db', help='Clear all data from database tables')
    clear_parser.add_argument('--confirm', action='store_true', help='Confirm you want to delete all data')

    # Population commands
    pop_parser = subparsers.add_parser('populate', help='Populate database tables')
    pop_subparsers = pop_parser.add_subparsers(dest='table', help='Table to populate')

    # Politicians (foundation table)
    politicians_parser = pop_subparsers.add_parser('politicians', help='Populate unified_politicians table')
    politicians_parser.add_argument('--limit', type=int, help='Limit number of politicians to process')
    politicians_parser.add_argument('--start-id', type=int, help='Start from specific deputy ID')
    politicians_parser.add_argument('--active-only', action='store_true', default=True, help='Process only active deputies')

    # Financial records
    financial_parser = pop_subparsers.add_parser('financial', help='Populate financial tables')
    financial_parser.add_argument('--politician-ids', nargs='+', type=int, help='Specific politician IDs to process')
    financial_parser.add_argument('--start-year', type=int, help='Starting year for financial data')
    financial_parser.add_argument('--end-year', type=int, help='Ending year for financial data')

    # Political networks
    networks_parser = pop_subparsers.add_parser('networks', help='Populate political networks table')
    networks_parser.add_argument('--politician-ids', nargs='+', type=int, help='Specific politician IDs to process')

    # Wealth tracking
    wealth_parser = pop_subparsers.add_parser('wealth', help='Populate wealth tracking tables')
    wealth_parser.add_argument('--politician-ids', nargs='+', type=int, help='Specific politician IDs to process')

    # Career history
    career_parser = pop_subparsers.add_parser('career', help='Populate career history table')
    career_parser.add_argument('--politician-ids', nargs='+', type=int, help='Specific politician IDs to process')

    # Events
    events_parser = pop_subparsers.add_parser('events', help='Populate events table')
    events_parser.add_argument('--politician-ids', nargs='+', type=int, help='Specific politician IDs to process')
    events_parser.add_argument('--days-back', type=int, default=365, help='Days back to collect events')

    # Assets
    assets_parser = pop_subparsers.add_parser('assets', help='Populate individual assets table')
    assets_parser.add_argument('--politician-ids', nargs='+', type=int, help='Specific politician IDs to process')

    # Professional background
    professional_parser = pop_subparsers.add_parser('professional', help='Populate professional background table')
    professional_parser.add_argument('--politician-ids', nargs='+', type=int, help='Specific politician IDs to process')

    # All tables in order
    all_parser = pop_subparsers.add_parser('all', help='Populate all tables in dependency order')
    all_parser.add_argument('--limit', type=int, help='Limit number of politicians for full workflow')

    # Validation commands
    validate_parser = subparsers.add_parser('validate', help='Validate data integrity')
    validate_parser.add_argument('--table', help='Validate specific table')
    validate_parser.add_argument('--fix', action='store_true', help='Attempt to fix validation issues')

    # Status commands
    status_parser = subparsers.add_parser('status', help='Show database status')
    status_parser.add_argument('--detailed', action='store_true', help='Show detailed statistics')

    return parser


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

        if args.command == 'init-db':
            print("🔧 Initializing database...")
            db_manager.initialize_database(force=args.force)
            print("✅ Database initialized successfully")

        elif args.command == 'clear-db':
            if not args.confirm:
                print("❌ Must use --confirm flag to clear database")
                print("⚠️  This will delete ALL data from ALL tables!")
                return 1

            print("🗑️  Clearing all data from database...")
            db_manager.clear_all_data()
            print("✅ Database cleared successfully")

        elif args.command == 'populate':
            if not args.table:
                parser.print_help()
                return 1

            if args.table == 'politicians':
                print("👥 Populating politicians table...")
                populator = PoliticianPopulator(db_manager)
                populator.populate(
                    limit=args.limit,
                    start_id=args.start_id,
                    active_only=args.active_only
                )

            elif args.table == 'financial':
                print("💰 Populating financial tables...")
                populator = FinancialPopulator(db_manager)
                populator.populate(
                    politician_ids=args.politician_ids,
                    start_year=args.start_year,
                    end_year=args.end_year
                )

            elif args.table == 'networks':
                print("🤝 Populating political networks table...")
                populator = NetworkPopulator(db_manager)
                populator.populate(politician_ids=args.politician_ids)

            elif args.table == 'wealth':
                print("💎 Populating wealth tracking tables...")
                populator = WealthPopulator(db_manager)
                populator.populate(politician_ids=args.politician_ids)

            elif args.table == 'career':
                print("📋 Populating career history table...")
                populator = CareerPopulator(db_manager)
                populator.populate(politician_ids=args.politician_ids)

            elif args.table == 'events':
                print("📅 Populating events table...")
                populator = EventPopulator(db_manager)
                populator.populate(
                    politician_ids=args.politician_ids,
                    days_back=args.days_back
                )

            elif args.table == 'assets':
                print("🏠 Populating individual assets table...")
                populator = AssetPopulator(db_manager)
                populator.populate(politician_ids=args.politician_ids)

            elif args.table == 'professional':
                print("🎓 Populating professional background table...")
                populator = ProfessionalPopulator(db_manager)
                populator.populate(politician_ids=args.politician_ids)

            elif args.table == 'all':
                print("🚀 Starting complete database population workflow...")
                print("Following dependency order from DATA_POPULATION_GUIDE.md")

                limit = args.limit

                # Step 1: Politicians (foundation)
                print("\n1️⃣ POLITICIANS (Foundation table)")
                politician_populator = PoliticianPopulator(db_manager)
                created_politician_ids = politician_populator.populate(limit=limit, active_only=True)

                # Use the limited set for subsequent phases if --limit was specified
                if limit:
                    # Get the politician IDs that were actually created/processed in this session
                    target_politician_ids = db_manager.execute_query(
                        "SELECT id FROM unified_politicians ORDER BY id DESC LIMIT ?", (limit,)
                    )
                    politician_ids_for_processing = [row['id'] for row in target_politician_ids]
                    print(f"📋 Using limited set of {len(politician_ids_for_processing)} politicians for subsequent phases")
                else:
                    # Get all existing politician IDs for subsequent phases
                    politician_ids_for_processing = db_manager.get_all_politician_ids()
                    print(f"📋 Using all {len(politician_ids_for_processing)} politicians for subsequent phases")

                # Step 2: Financial counterparts + records
                print("\n2️⃣ FINANCIAL RECORDS")
                financial_populator = FinancialPopulator(db_manager)
                financial_populator.populate(politician_ids=politician_ids_for_processing)

                # Step 3: Political networks
                print("\n3️⃣ POLITICAL NETWORKS")
                network_populator = NetworkPopulator(db_manager)
                network_populator.populate(politician_ids=politician_ids_for_processing)

                # Step 4: Wealth tracking
                print("\n4️⃣ WEALTH TRACKING")
                wealth_populator = WealthPopulator(db_manager)
                wealth_populator.populate(politician_ids=politician_ids_for_processing)

                # Step 5: Individual assets
                print("\n5️⃣ INDIVIDUAL ASSETS")
                asset_populator = AssetPopulator(db_manager)
                asset_populator.populate(politician_ids=politician_ids_for_processing)

                # Step 6: Career history
                print("\n6️⃣ CAREER HISTORY")
                career_populator = CareerPopulator(db_manager)
                career_populator.populate(politician_ids=politician_ids_for_processing)

                # Step 7: Events
                print("\n7️⃣ PARLIAMENTARY EVENTS")
                event_populator = EventPopulator(db_manager)
                event_populator.populate(politician_ids=politician_ids_for_processing)

                # Step 8: Professional background
                print("\n8️⃣ PROFESSIONAL BACKGROUND")
                professional_populator = ProfessionalPopulator(db_manager)
                professional_populator.populate(politician_ids=politician_ids_for_processing)

                print("\n🎯 COMPLETE WORKFLOW FINISHED!")
                print(f"✅ Successfully processed {len(politician_ids_for_processing)} politicians across all tables")
                return 0  # Explicit exit

            else:
                print(f"❌ Unknown table: {args.table}")
                return 1

        elif args.command == 'validate':
            print("🔍 Running data validation...")
            validator = ValidationManager(db_manager)

            if args.table:
                validator.validate_table(args.table, fix=args.fix)
            else:
                validator.validate_all(fix=args.fix)

        elif args.command == 'status':
            print("📊 Database Status Report")
            db_manager.show_status(detailed=args.detailed)

        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        print("✅ Operation completed successfully")
        return 0

    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())