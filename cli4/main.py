#!/usr/bin/env python3
"""
CLI4 - Political Transparency Database CLI (Foundation)
Rock-solid implementation starting with politicians table only
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

from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.populators import CLI4PoliticianPopulator, CLI4PoliticianValidator
from cli4.populators.financial import CLI4CounterpartsPopulator, CLI4RecordsPopulator, CLI4FinancialValidator


def setup_cli():
    """Setup command line interface for CLI4 foundation"""
    parser = argparse.ArgumentParser(
        description="CLI4 - Political Transparency Database (Foundation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CLI4 Foundation - Starting with politicians table only

Examples:
  # Initialize database
  python cli4/main.py init-db

  # Populate politicians table
  python cli4/main.py populate --limit 10

  # Show status
  python cli4/main.py status

  # Validate data
  python cli4/main.py validate
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Database initialization
    init_parser = subparsers.add_parser('init-db', help='Initialize database with schema')
    init_parser.add_argument('--force', action='store_true', help='Force recreation of existing database')

    # Clear database
    clear_parser = subparsers.add_parser('clear-db', help='Clear politicians table')
    clear_parser.add_argument('--confirm', action='store_true', help='Confirm you want to delete all data')
    clear_parser.add_argument('--all-tables', action='store_true', help='Clear ALL tables (politicians, financial, etc.)')

    # Population commands
    pop_parser = subparsers.add_parser('populate', help='Populate politicians table')
    pop_parser.add_argument('--limit', type=int, help='Limit number of politicians to process')
    pop_parser.add_argument('--start-id', type=int, help='Start from specific deputy ID')
    pop_parser.add_argument('--active-only', action='store_true', default=True, help='Process only active deputies')
    pop_parser.add_argument('--resume-from', type=int, help='Resume from specific politician ID')

    # Financial population commands
    financial_parser = subparsers.add_parser('populate-financial', help='Populate financial tables')
    financial_parser.add_argument('--phase', choices=['counterparts', 'records', 'all'], default='all',
                                 help='Financial phase to populate')
    financial_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')
    financial_parser.add_argument('--start-year', type=int, help='Start year for financial data')
    financial_parser.add_argument('--end-year', type=int, help='End year for financial data')

    # Status commands
    status_parser = subparsers.add_parser('status', help='Show database status')
    status_parser.add_argument('--detailed', action='store_true', help='Show detailed statistics')

    # Validation commands
    validate_parser = subparsers.add_parser('validate', help='Validate data tables')
    validate_parser.add_argument('--table', choices=['politicians', 'financial', 'all'], default='all',
                                help='Table to validate (default: all available tables)')
    validate_parser.add_argument('--limit', type=int, help='Limit number of records to validate')
    validate_parser.add_argument('--detailed', action='store_true', help='Show detailed validation results')
    validate_parser.add_argument('--fix', action='store_true', help='Attempt to fix validation issues')
    validate_parser.add_argument('--export', help='Export validation results to file (JSON/CSV)')

    return parser


def main():
    """Main CLI4 entry point"""
    parser = setup_cli()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        # Initialize core infrastructure
        print("🔧 Initializing CLI4 infrastructure...")

        logger = CLI4Logger(console=True, file=True)
        rate_limiter = CLI4RateLimiter()

        print(f"✅ Database: PostgreSQL")
        print(f"✅ Logger: Console + File")
        print(f"✅ Rate Limiter: Initialized")

        if args.command == 'init-db':
            print("\n🏗️  Checking database...")
            database.check_database()

        elif args.command == 'clear-db':
            if not args.confirm:
                print("❌ Must use --confirm flag to clear database")
                if args.all_tables:
                    print("⚠️  This will delete ALL data from ALL tables!")
                else:
                    print("⚠️  This will delete ALL politicians data!")
                return 1

            if args.all_tables:
                print("🗑️  Clearing ALL tables...")
                database.clear_all_data()
                print("✅ All tables cleared")
            else:
                print("🗑️  Clearing politicians table...")
                database.clear_politicians()
                print("✅ Politicians table cleared")

        elif args.command == 'populate':
            print("\n👥 POLITICIANS TABLE POPULATION")
            print("=" * 50)

            # Initialize populator
            populator = CLI4PoliticianPopulator(logger, rate_limiter)

            # Run population
            created_ids = populator.populate(
                limit=args.limit,
                start_id=args.start_id,
                active_only=args.active_only,
                resume_from=args.resume_from
            )

            print(f"\n✅ Population completed: {len(created_ids)} politicians processed")

        elif args.command == 'populate-financial':
            print("💰 FINANCIAL POPULATION WORKFLOW")
            print("Phase 2: financial_counterparts + unified_financial_records")
            print("=" * 50)

            # Initialize components
            logger = CLI4Logger(console=True, file=True)
            rate_limiter = CLI4RateLimiter()

            if args.phase in ['counterparts', 'all']:
                print("\n💰 Phase 2a: Financial Counterparts")
                counterparts_populator = CLI4CounterpartsPopulator(logger, rate_limiter)
                counterparts_count = counterparts_populator.populate(
                    politician_ids=args.politician_ids,
                    start_year=args.start_year,
                    end_year=args.end_year
                )
                print(f"✅ Counterparts phase completed: {counterparts_count} records")

            if args.phase in ['records', 'all']:
                print("\n📊 Phase 2b: Financial Records")
                records_populator = CLI4RecordsPopulator(logger, rate_limiter)
                records_count = records_populator.populate(
                    politician_ids=args.politician_ids,
                    start_year=args.start_year,
                    end_year=args.end_year
                )
                print(f"✅ Records phase completed: {records_count} records")

            print("\n🏆 Financial population workflow completed!")

        elif args.command == 'status':
            database.show_status()

        elif args.command == 'validate':
            # Determine what to validate
            if args.table == 'politicians' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE POLITICIANS VALIDATION")
                print("Following DATA_POPULATION_GUIDE.md specifications")
                print("=" * 50)

                # Initialize comprehensive validator
                validator = CLI4PoliticianValidator()
                validation_results = validator.validate_all_politicians(
                    limit=args.limit,
                    detailed=args.detailed
                )

                # Export results if requested
                if args.export:
                    validator.export_results(args.export, validation_results)
                    print(f"📄 Validation results exported to: {args.export}")

                # Show completion message
                if validation_results['compliance_score'] >= 90:
                    print("🏆 Validation completed - Excellent compliance!")
                elif validation_results['compliance_score'] >= 70:
                    print("👍 Validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Validation completed - Significant improvements needed")

            if args.table == 'financial' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE FINANCIAL VALIDATION")
                print("Validating financial_counterparts + unified_financial_records")
                print("=" * 50)

                # Initialize financial validator
                financial_validator = CLI4FinancialValidator()
                financial_results = financial_validator.validate_all_financial()

                # Export results if requested
                if args.export:
                    financial_validator.export_results(args.export, financial_results)
                    print(f"📄 Financial validation results exported to: {args.export}")

        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        # Show session summary
        logger.print_summary()

        print("\n✅ CLI4 operation completed successfully")
        return 0

    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ CLI4 Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return 1
    finally:
        # Cleanup logger
        if 'logger' in locals():
            logger.cleanup()


if __name__ == "__main__":
    sys.exit(main())