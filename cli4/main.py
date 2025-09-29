#!/usr/bin/env python3
"""
CLI4 - Political Transparency Database CLI (Foundation)
Rock-solid implementation starting with politicians table only
"""

import argparse
import sys
import os
import time
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
from cli4.populators.electoral import ElectoralRecordsPopulator, ElectoralRecordsValidator
from cli4.populators.parties import CLI4PartiesPopulator, CLI4PartiesValidator
from cli4.populators.wealth import CLI4WealthPopulator, CLI4WealthValidator
from cli4.populators.career import CareerPopulator, CareerValidator
from cli4.populators.assets import AssetsPopulator, AssetsValidator
from cli4.populators.professional import ProfessionalPopulator, ProfessionalValidator
from cli4.populators.events import EventsPopulator, EventsValidator
from cli4.populators.sanctions import SanctionsPopulator, SanctionsValidator
from cli4.populators.tcu import TCUPopulator, TCUValidator
from cli4.populators.senado import SenadoPopulator, SenadoValidator


def setup_cli():
    """Setup command line interface for CLI4 foundation"""
    parser = argparse.ArgumentParser(
        description="CLI4 - Political Transparency Database (Foundation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CLI4 Foundation - Complete Political Transparency Database

Examples:
  # Initialize database
  python cli4/main.py init-db

  # Populate politicians table
  python cli4/main.py populate --limit 10

  # Populate ALL politicians (including inactive)
  python cli4/main.py populate --include-inactive

  # Populate financial records
  python cli4/main.py populate-financial

  # Populate electoral records (NEW!)
  python cli4/main.py populate-electoral

  # Populate political parties (NEW!)
  python cli4/main.py populate-parties --limit 10
  python cli4/main.py populate-parties --legislatura-id 57

  # Populate wealth tracking (NEW!)
  python cli4/main.py populate-wealth --politician-ids 1 2 3
  python cli4/main.py populate-wealth --election-years 2018 2020 2022 2024

  # Populate career history (NEW!)
  python cli4/main.py populate-career --politician-ids 1 2 3

  # Populate asset declarations (NEW!)
  python cli4/main.py populate-assets --politician-ids 1 2 3
  python cli4/main.py populate-assets --election-years 2018 2020 2022 2024

  # Populate professional background (NEW!)
  python cli4/main.py populate-professional --politician-ids 1 2 3

  # Populate parliamentary events (NEW!)
  python cli4/main.py populate-events --politician-ids 1 2 3
  python cli4/main.py populate-events --days-back 180

  # Populate vendor sanctions (NEW!)
  python cli4/main.py populate-sanctions --max-pages 100
  python cli4/main.py populate-sanctions --update-existing

  # Populate TCU disqualifications (NEW!)
  python cli4/main.py populate-tcu --max-pages 50
  python cli4/main.py populate-tcu --update-existing

  # Populate Senado politicians (NEW!)
  python cli4/main.py populate-senado
  python cli4/main.py populate-senado --update-existing

  # Post-process: Calculate aggregate career fields (NEW!)
  python cli4/main.py post-process --fields electoral
  python cli4/main.py post-process --enhanced --fields corruption
  python cli4/main.py post-process --enhanced --fields all

  # Show status
  python cli4/main.py status

  # Validate specific tables
  python cli4/main.py validate --table electoral
  python cli4/main.py validate --table parties
  python cli4/main.py validate --table wealth
  python cli4/main.py validate --table assets
  python cli4/main.py validate --table professional
  python cli4/main.py validate --table events
  python cli4/main.py validate --table tcu
  python cli4/main.py validate --table senado
  python cli4/main.py validate --table all
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
    pop_parser.add_argument('--include-inactive', action='store_true', default=False, help='Include inactive deputies (on leave, vacant seats, etc.)')
    pop_parser.add_argument('--resume-from', type=int, help='Resume from specific politician ID')

    # Financial population commands
    financial_parser = subparsers.add_parser('populate-financial', help='Populate financial tables')
    financial_parser.add_argument('--phase', choices=['counterparts', 'records', 'all'], default='all',
                                 help='Financial phase to populate')
    financial_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')
    financial_parser.add_argument('--start-year', type=int, help='Start year for financial data')
    financial_parser.add_argument('--end-year', type=int, help='End year for financial data')

    # Electoral population commands (NEW)
    electoral_parser = subparsers.add_parser('populate-electoral', help='Populate electoral records table')
    electoral_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')
    electoral_parser.add_argument('--election-years', type=int, nargs='+', default=[2018, 2020, 2022],
                                 help='Election years to process (default: 2018 2020 2022)')
    electoral_parser.add_argument('--force-refresh', action='store_true',
                                 help='Refresh existing records (skip duplicate check)')

    # Parties population commands (NEW)
    parties_parser = subparsers.add_parser('populate-parties', help='Populate political parties and memberships tables')
    parties_parser.add_argument('--limit', type=int, help='Limit number of parties to process')
    parties_parser.add_argument('--legislatura-id', type=int, help='Legislature ID to process (default: 57)')
    parties_parser.add_argument('--force-refresh', action='store_true',
                                help='Force refresh existing records (skip duplicate check)')

    # Network population commands (NEW)
    network_parser = subparsers.add_parser('populate-networks', help='Populate political networks table')
    network_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')

    # Wealth population commands (NEW)
    wealth_parser = subparsers.add_parser('populate-wealth', help='Populate wealth tracking table')
    wealth_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')
    wealth_parser.add_argument('--election-years', type=int, nargs='+', default=[2018, 2020, 2022, 2024],
                               help='Election years to process (default: 2018 2020 2022 2024)')
    wealth_parser.add_argument('--force-refresh', action='store_true',
                               help='Refresh existing records (skip duplicate check)')

    # Career population commands (NEW)
    career_parser = subparsers.add_parser('populate-career', help='Populate career history table')
    career_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')

    # Assets population commands (NEW)
    assets_parser = subparsers.add_parser('populate-assets', help='Populate individual asset declarations table')
    assets_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')
    assets_parser.add_argument('--election-years', type=int, nargs='+', default=[2018, 2020, 2022, 2024],
                               help='Election years to process (default: 2018 2020 2022 2024)')
    assets_parser.add_argument('--force-refresh', action='store_true',
                               help='Refresh existing records (skip duplicate check)')

    # Professional population commands (NEW)
    professional_parser = subparsers.add_parser('populate-professional', help='Populate professional background table')
    professional_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')

    # Events population commands (NEW)
    events_parser = subparsers.add_parser('populate-events', help='Populate parliamentary events table')
    events_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')
    events_parser.add_argument('--days-back', type=int, default=365, help='Days back to fetch events (default: 365)')

    # Comprehensive sanctions population (ALL endpoints)
    sanctions_parser = subparsers.add_parser('populate-sanctions', help='Populate ALL sanctions: CEIS + CEPIM + CNEP (comprehensive corruption detection)')
    sanctions_parser.add_argument('--max-pages', type=int, default=500, help='Maximum pages per endpoint (default: 500)')
    sanctions_parser.add_argument('--update-existing', action='store_true', help='Update existing records instead of skipping')

    # CEIS sanctions population (individual)
    ceis_parser = subparsers.add_parser('populate-ceis', help='Populate CEIS sanctions only (Empresas Inidôneas e Suspensas)')
    ceis_parser.add_argument('--max-pages', type=int, default=500, help='Maximum pages (default: 500)')
    ceis_parser.add_argument('--update-existing', action='store_true', help='Update existing records')

    # CEPIM sanctions population (CRITICAL MISSING DATA)
    cepim_parser = subparsers.add_parser('populate-cepim', help='Populate CEPIM sanctions (CRITICAL: missing from corruption detection)')
    cepim_parser.add_argument('--max-pages', type=int, default=500, help='Maximum pages (default: 500)')
    cepim_parser.add_argument('--update-existing', action='store_true', help='Update existing records')

    # CNEP sanctions population
    cnep_parser = subparsers.add_parser('populate-cnep', help='Populate CNEP sanctions (CRITICAL: missing from corruption detection)')
    cnep_parser.add_argument('--max-pages', type=int, default=500, help='Maximum pages (default: 500)')
    cnep_parser.add_argument('--update-existing', action='store_true', help='Update existing records')

    # TCU disqualifications population
    tcu_parser = subparsers.add_parser('populate-tcu', help='Populate TCU disqualifications table (corruption detection)')
    tcu_parser.add_argument('--max-pages', type=int, default=100, help='Maximum pages to fetch (default: 100, reasonable limit)')
    tcu_parser.add_argument('--update-existing', action='store_true', help='Update existing records instead of skipping')

    # Senado politicians population
    senado_parser = subparsers.add_parser('populate-senado', help='Populate Senado politicians table (family network detection)')
    senado_parser.add_argument('--update-existing', action='store_true', help='Update existing records instead of skipping')

    # Status commands
    status_parser = subparsers.add_parser('status', help='Show database status')
    status_parser.add_argument('--detailed', action='store_true', help='Show detailed statistics')

    # Validation commands
    validate_parser = subparsers.add_parser('validate', help='Validate data tables')
    validate_parser.add_argument('--table', choices=['politicians', 'financial', 'electoral', 'parties', 'networks', 'wealth', 'career', 'assets', 'professional', 'events', 'sanctions', 'tcu', 'senado', 'all'], default='all',
                                help='Table to validate (default: all available tables)')
    validate_parser.add_argument('--limit', type=int, help='Limit number of records to validate')
    validate_parser.add_argument('--detailed', action='store_true', help='Show detailed validation results')
    validate_parser.add_argument('--fix', action='store_true', help='Attempt to fix validation issues')
    validate_parser.add_argument('--export', help='Export validation results to file (JSON/CSV)')

    # Post-processing commands (ENHANCED)
    postprocess_parser = subparsers.add_parser('post-process', help='Calculate comprehensive aggregate fields with corruption detection')
    postprocess_parser.add_argument('--politician-ids', type=int, nargs='+', help='Specific politician IDs to process')
    postprocess_parser.add_argument('--fields', choices=['electoral', 'financial', 'corruption', 'networks', 'career', 'wealth', 'all'], default='all',
                                   help='Which aggregate fields to calculate (default: all)')
    postprocess_parser.add_argument('--force-refresh', action='store_true',
                                   help='Recalculate all fields even if already populated')
    postprocess_parser.add_argument('--enhanced', action='store_true',
                                   help='Use enhanced post-processor with corruption detection and family networks')

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
                active_only=not args.include_inactive,  # If include_inactive=True, then active_only=False
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

        elif args.command == 'populate-electoral':
            print("🗳️ ELECTORAL RECORDS POPULATION")
            print("Electoral outcome data from TSE with win/loss tracking")
            print("=" * 60)

            # Initialize electoral populator
            electoral_populator = ElectoralRecordsPopulator(logger, rate_limiter)

            # Run electoral population
            electoral_count = electoral_populator.populate(
                politician_ids=args.politician_ids,
                election_years=args.election_years
            )

            print(f"\n🏆 Electoral population completed: {electoral_count} records")
            print(f"   Election years processed: {', '.join(map(str, args.election_years))}")

        elif args.command == 'populate-parties':
            print("🏛️ POLITICAL PARTIES POPULATION")
            print("Political parties and membership relationships from Câmara")
            print("=" * 60)

            # Initialize parties populator
            parties_populator = CLI4PartiesPopulator(logger, rate_limiter)

            # Run parties population
            parties_count = parties_populator.populate(
                limit=args.limit,
                legislatura_id=args.legislatura_id,
                force_refresh=args.force_refresh
            )

            print(f"\n🏆 Parties population completed: {len(parties_count)} parties processed")

        elif args.command == 'populate-networks':
            print("🤝 POLITICAL NETWORKS POPULATION")
            print("Committee, front, coalition, and federation memberships")
            print("=" * 60)

            # Initialize network populator
            from cli4.populators.network.populator import NetworkPopulator
            network_populator = NetworkPopulator(logger, rate_limiter)

            # Run network population
            network_count = network_populator.populate(
                politician_ids=args.politician_ids
            )

            print(f"\n🏆 Network population completed: {network_count} records")

        elif args.command == 'populate-wealth':
            print("💎 WEALTH TRACKING POPULATION")
            print("TSE asset declarations with wealth progression analysis")
            print("=" * 60)

            # Initialize wealth populator
            wealth_populator = CLI4WealthPopulator(logger, rate_limiter)

            # Run wealth population
            wealth_count = wealth_populator.populate(
                politician_ids=args.politician_ids,
                election_years=args.election_years,
                force_refresh=args.force_refresh
            )

            print(f"\n🏆 Wealth population completed: {wealth_count} records")
            print(f"   Election years processed: {', '.join(map(str, args.election_years))}")

        elif args.command == 'populate-career':
            print("📋 CAREER HISTORY POPULATION")
            print("External mandates and political career tracking")
            print("=" * 60)
            # Initialize career populator
            career_populator = CareerPopulator(logger, rate_limiter)
            # Run career population
            career_count = career_populator.populate(
                politician_ids=args.politician_ids
            )
            print(f"\n🏆 Career population completed: {career_count} records")

        elif args.command == 'populate-assets':
            print("🏛️ INDIVIDUAL ASSET DECLARATIONS POPULATION")
            print("TSE candidate asset declarations with detailed asset tracking")
            print("=" * 60)

            # Initialize assets populator
            assets_populator = AssetsPopulator(logger, rate_limiter)

            # Run assets population
            assets_count = assets_populator.populate(
                politician_ids=args.politician_ids,
                election_years=args.election_years,
                force_refresh=args.force_refresh
            )

            print(f"\n🏆 Asset population completed: {assets_count} records")
            print(f"   Election years processed: {', '.join(map(str, args.election_years))}")

        elif args.command == 'populate-professional':
            print("💼 PROFESSIONAL BACKGROUND POPULATION")
            print("Deputados professional background with career analysis")
            print("=" * 60)

            # Initialize professional populator
            professional_populator = ProfessionalPopulator(logger, rate_limiter)

            # Run professional population
            professional_count = professional_populator.populate(
                politician_ids=args.politician_ids
            )

            print(f"\n🏆 Professional population completed: {professional_count} records")

        elif args.command == 'populate-events':
            print("🏛️ PARLIAMENTARY EVENTS POPULATION")
            print("Deputados parliamentary activity with session analysis")
            print("=" * 60)

            # Initialize events populator
            events_populator = EventsPopulator(logger, rate_limiter)

            # Run events population
            events_count = events_populator.populate(
                politician_ids=args.politician_ids,
                days_back=args.days_back
            )

            print(f"\n🏆 Events population completed: {events_count} records")

        elif args.command == 'populate-sanctions':
            print("⚠️  COMPREHENSIVE VENDOR SANCTIONS POPULATION")
            print("Portal da Transparência: CEIS + CEPIM + CNEP for complete corruption detection")
            print("=" * 80)

            total_records = 0
            start_time = time.time()

            # 1. CEIS - Cadastro de Empresas Inidôneas e Suspensas
            print("\n🔍 STEP 1/3: CEIS SANCTIONS")
            print("=" * 50)
            sanctions_populator = SanctionsPopulator(logger, rate_limiter)
            ceis_count = sanctions_populator.populate(
                max_pages=args.max_pages,
                update_existing=args.update_existing
            )
            total_records += ceis_count
            print(f"✅ CEIS: {ceis_count:,} records")

            # 2. CEPIM - Cadastro de Empresas Punidas
            print("\n🔍 STEP 2/3: CEPIM SANCTIONS")
            print("=" * 50)
            from cli4.populators.sanctions.cepim.populator import CEPIMPopulator
            cepim_populator = CEPIMPopulator(logger, rate_limiter)
            cepim_count = cepim_populator.populate(
                max_pages=args.max_pages,
                update_existing=args.update_existing
            )
            total_records += cepim_count
            print(f"✅ CEPIM: {cepim_count:,} records")

            # 3. CNEP - Cadastro Nacional de Empresas Punidas
            print("\n🔍 STEP 3/3: CNEP SANCTIONS")
            print("=" * 50)
            from cli4.populators.sanctions.cnep.populator import CNEPPopulator
            cnep_populator = CNEPPopulator(logger, rate_limiter)
            cnep_count = cnep_populator.populate(
                max_pages=args.max_pages,
                update_existing=args.update_existing
            )
            total_records += cnep_count
            print(f"✅ CNEP: {cnep_count:,} records")

            # Final comprehensive summary
            elapsed_time = time.time() - start_time
            print(f"\n🏆 COMPREHENSIVE SANCTIONS POPULATION COMPLETED")
            print("=" * 60)
            print(f"📊 CEIS:  {ceis_count:,} records")
            print(f"📊 CEPIM: {cepim_count:,} records")
            print(f"📊 CNEP:  {cnep_count:,} records")
            print(f"📊 TOTAL: {total_records:,} sanctions records")
            print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
            print(f"🔥 CRITICAL: Complete sanctions coverage achieved!")
            print(f"💡 Next: Run 'post-process --enhanced' to recalculate corruption scores")

        elif args.command == 'populate-ceis':
            print("⚠️  CEIS SANCTIONS POPULATION")
            print("Portal da Transparência CEIS (Empresas Inidôneas e Suspensas)")
            print("=" * 60)

            # Initialize CEIS populator
            sanctions_populator = SanctionsPopulator(logger, rate_limiter)

            # Run CEIS population
            ceis_count = sanctions_populator.populate(
                max_pages=args.max_pages,
                update_existing=args.update_existing
            )

            print(f"\n✅ CEIS population completed: {ceis_count:,} records")

        elif args.command == 'populate-cepim':
            print("🚨 CRITICAL: CEPIM SANCTIONS POPULATION")
            print("MISSING DATA essential for corruption detection!")
            print("=" * 60)

            from cli4.populators.sanctions.cepim.populator import CEPIMPopulator
            cepim_populator = CEPIMPopulator(logger, rate_limiter)

            # Run CEPIM population
            cepim_count = cepim_populator.populate(
                max_pages=args.max_pages,
                update_existing=args.update_existing
            )

            print(f"\n🔥 CEPIM POPULATION COMPLETED: {cepim_count:,} records")
            print("💡 CRITICAL: This data was missing from corruption detection!")
            print("💡 Next: Run 'post-process --enhanced' to recalculate corruption scores")

        elif args.command == 'populate-cnep':
            print("🚨 CRITICAL: CNEP SANCTIONS POPULATION")
            print("MISSING DATA essential for corruption detection!")
            print("=" * 60)

            from cli4.populators.sanctions.cnep.populator import CNEPPopulator
            cnep_populator = CNEPPopulator(logger, rate_limiter)

            # Run CNEP population
            cnep_count = cnep_populator.populate(
                max_pages=args.max_pages,
                update_existing=args.update_existing
            )

            print(f"\n🔥 CNEP POPULATION COMPLETED: {cnep_count:,} records")
            print("💡 CRITICAL: This data was missing from corruption detection!")
            print("💡 Next: Run 'post-process --enhanced' to recalculate corruption scores")

        elif args.command == 'populate-tcu':
            print("⚖️  TCU DISQUALIFICATIONS POPULATION")
            print("Federal Audit Court disqualifications for corruption detection")
            print("=" * 60)

            # Initialize TCU populator
            tcu_populator = TCUPopulator(logger, rate_limiter)

            # Run TCU population
            tcu_count = tcu_populator.populate(
                max_pages=args.max_pages,
                update_existing=args.update_existing
            )

            print(f"\n🏆 TCU population completed: {tcu_count} records")

        elif args.command == 'populate-senado':
            print("🏛️  SENADO POLITICIANS POPULATION")
            print("Senate Federal politicians for family network detection")
            print("=" * 60)

            # Initialize Senado populator
            senado_populator = SenadoPopulator(logger, rate_limiter)

            # Run Senado population
            senado_count = senado_populator.populate(
                update_existing=args.update_existing
            )

            print(f"\n🏆 Senado population completed: {senado_count} records")

        elif args.command == 'post-process':
            if args.enhanced:
                print("📊 ENHANCED POST-PROCESSING: COMPREHENSIVE AGGREGATE FIELDS")
                print("Computing corruption detection, family networks, career progression, and wealth analysis")
                print("=" * 80)

                # Import the enhanced post-processor
                from cli4.populators.metrics_enhanced import EnhancedCLI4PostProcessor
                post_processor = EnhancedCLI4PostProcessor(logger, rate_limiter)
            else:
                print("📊 POST-PROCESSING: CALCULATE AGGREGATE CAREER FIELDS")
                print("Computing electoral success rates, career timelines, and financial summaries")
                print("=" * 70)

                # Import the standard post-processor
                from cli4.populators.metrics import CLI4PostProcessor
                post_processor = CLI4PostProcessor(logger, rate_limiter)

            # Run post-processing
            updated_count = post_processor.calculate_aggregate_fields(
                politician_ids=args.politician_ids,
                fields=args.fields,
                force_refresh=args.force_refresh
            )

            processor_type = "Enhanced" if args.enhanced else "Standard"
            print(f"\n🏆 {processor_type} post-processing completed: {updated_count} politicians updated")
            print(f"   Fields calculated: {args.fields}")

        elif args.command == 'status':
            database.show_status()

        elif args.command == 'validate':
            print("\n🔍 COMPREHENSIVE DATA VALIDATION")
            print("=" * 50)

            # Import dependency checker
            from cli4.modules.dependency_checker import DependencyChecker

            # Validation needs ALL data to be populated for comprehensive checks
            required_tables = []
            if args.table == 'all':
                required_tables = ["politicians", "financial", "electoral", "parties", "networks", "wealth", "assets", "professional", "events", "sanctions", "tcu", "senado"]
                DependencyChecker.print_dependency_warning(
                    required_steps=required_tables,
                    current_step="FULL VALIDATION (ALL TABLES)"
                )
            elif args.table == 'financial':
                DependencyChecker.print_dependency_warning(
                    required_steps=["politicians", "financial"],
                    current_step="FINANCIAL VALIDATION"
                )
            elif args.table == 'electoral':
                DependencyChecker.print_dependency_warning(
                    required_steps=["politicians", "electoral"],
                    current_step="ELECTORAL VALIDATION"
                )
            elif args.table == 'parties':
                DependencyChecker.print_dependency_warning(
                    required_steps=["parties"],
                    current_step="PARTIES VALIDATION"
                )
            elif args.table == 'networks':
                DependencyChecker.print_dependency_warning(
                    required_steps=["politicians", "networks"],
                    current_step="NETWORK VALIDATION"
                )
            elif args.table == 'wealth':
                DependencyChecker.print_dependency_warning(
                    required_steps=["politicians", "wealth"],
                    current_step="WEALTH VALIDATION"
                )
            elif args.table == 'assets':
                DependencyChecker.print_dependency_warning(
                    required_steps=["politicians", "assets"],
                    current_step="ASSET DECLARATIONS VALIDATION"
                )
            elif args.table == 'professional':
                DependencyChecker.print_dependency_warning(
                    required_steps=["politicians", "professional"],
                    current_step="PROFESSIONAL BACKGROUND VALIDATION"
                )
            elif args.table == 'events':
                DependencyChecker.print_dependency_warning(
                    required_steps=["politicians", "events"],
                    current_step="PARLIAMENTARY EVENTS VALIDATION"
                )
            elif args.table == 'sanctions':
                DependencyChecker.print_dependency_warning(
                    required_steps=["sanctions"],
                    current_step="VENDOR SANCTIONS VALIDATION"
                )
            elif args.table == 'tcu':
                DependencyChecker.print_dependency_warning(
                    required_steps=["tcu"],
                    current_step="TCU DISQUALIFICATIONS VALIDATION"
                )
            elif args.table == 'senado':
                DependencyChecker.print_dependency_warning(
                    required_steps=["senado"],
                    current_step="SENADO POLITICIANS VALIDATION"
                )

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

            if args.table == 'electoral' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE ELECTORAL VALIDATION")
                print("Validating unified_electoral_records with electoral outcome analysis")
                print("=" * 60)

                # Initialize electoral validator
                electoral_validator = ElectoralRecordsValidator()
                electoral_results = electoral_validator.validate_all_electoral()

                # Export results if requested
                if args.export:
                    # Note: would need to implement export_results method for electoral validator
                    print(f"📄 Electoral validation results logged")

                # Show completion message
                if electoral_results['compliance_score'] >= 90:
                    print("🏆 Electoral validation completed - Excellent compliance!")
                elif electoral_results['compliance_score'] >= 70:
                    print("👍 Electoral validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Electoral validation completed - Significant improvements needed")

            if args.table == 'parties' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE PARTIES VALIDATION")
                print("Validating political_parties and party_memberships tables")
                print("=" * 60)

                # Initialize parties validator
                parties_validator = CLI4PartiesValidator()
                parties_results = parties_validator.validate_all_parties(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 Parties validation results logged")

                # Show completion message
                if parties_results['compliance_score'] >= 90:
                    print("🏆 Parties validation completed - Excellent compliance!")
                elif parties_results['compliance_score'] >= 70:
                    print("👍 Parties validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Parties validation completed - Significant improvements needed")

            if args.table == 'networks' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE NETWORKS VALIDATION")
                print("Validating unified_political_networks with network membership analysis")
                print("=" * 60)

                # Initialize network validator
                from cli4.populators.network.validator import NetworkValidator
                network_validator = NetworkValidator()
                network_results = network_validator.validate_all_networks(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 Network validation results logged")

                # Show completion message
                if network_results['compliance_score'] >= 90:
                    print("🏆 Network validation completed - Excellent compliance!")
                elif network_results['compliance_score'] >= 70:
                    print("👍 Network validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Network validation completed - Significant improvements needed")

            if args.table == 'wealth' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE WEALTH VALIDATION")
                print("Validating unified_wealth_tracking with wealth progression analysis")
                print("=" * 60)

                # Initialize wealth validator
                wealth_validator = CLI4WealthValidator()
                wealth_results = wealth_validator.validate_all_wealth(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 Wealth validation results logged")

                # Show completion message
                if wealth_results['compliance_score'] >= 90:
                    print("🏆 Wealth validation completed - Excellent compliance!")
                elif wealth_results['compliance_score'] >= 70:
                    print("👍 Wealth validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Wealth validation completed - Significant improvements needed")

            if args.table == 'career' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE CAREER VALIDATION")
                print("Validating politician_career_history with mandate progression analysis")
                print("=" * 60)

                # Initialize career validator
                career_validator = CareerValidator()
                career_results = career_validator.validate_all_career_records(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 Career validation results logged")

                # Show completion message
                if career_results['compliance_score'] >= 90:
                    print("🏆 Career validation completed - Excellent compliance!")
                elif career_results['compliance_score'] >= 70:
                    print("👍 Career validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Career validation completed - Significant improvements needed")

            if args.table == 'assets' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE ASSET DECLARATIONS VALIDATION")
                print("Validating politician_assets with TSE asset declaration analysis")
                print("=" * 60)

                # Initialize assets validator
                assets_validator = AssetsValidator()
                assets_results = assets_validator.validate_all_assets(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 Asset validation results logged")

                # Show completion message
                if assets_results['compliance_score'] >= 90:
                    print("🏆 Asset validation completed - Excellent compliance!")
                elif assets_results['compliance_score'] >= 70:
                    print("👍 Asset validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Asset validation completed - Significant improvements needed")

            if args.table == 'professional' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE PROFESSIONAL VALIDATION")
                print("Validating politician_professional_background with career background analysis")
                print("=" * 60)

                # Initialize professional validator
                professional_validator = ProfessionalValidator()
                professional_results = professional_validator.validate_all_professional(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 Professional validation results logged")

                # Show completion message
                if professional_results['compliance_score'] >= 90:
                    print("🏆 Professional validation completed - Excellent compliance!")
                elif professional_results['compliance_score'] >= 70:
                    print("👍 Professional validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Professional validation completed - Significant improvements needed")

            if args.table == 'events' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE EVENTS VALIDATION")
                print("Validating politician_events with parliamentary activity analysis")
                print("=" * 60)

                # Initialize events validator
                events_validator = EventsValidator()
                events_results = events_validator.validate_all_events(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 Events validation results logged")

                # Show completion message
                if events_results['compliance_score'] >= 90:
                    print("🏆 Events validation completed - Excellent compliance!")
                elif events_results['compliance_score'] >= 70:
                    print("👍 Events validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Events validation completed - Significant improvements needed")

            if args.table == 'sanctions' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE SANCTIONS VALIDATION")
                print("Validating vendor_sanctions with corruption detection readiness")
                print("=" * 60)

                # Initialize sanctions validator
                sanctions_validator = SanctionsValidator()
                sanctions_results = sanctions_validator.validate_all_sanctions(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 Sanctions validation results logged")

                # Show completion message
                if sanctions_results['compliance_score'] >= 90:
                    print("🏆 Sanctions validation completed - Excellent compliance! Ready for corruption detection")
                elif sanctions_results['compliance_score'] >= 70:
                    print("👍 Sanctions validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Sanctions validation completed - Significant improvements needed")

            if args.table == 'tcu' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE TCU VALIDATION")
                print("Validating tcu_disqualifications with corruption detection readiness")
                print("=" * 60)

                # Initialize TCU validator
                tcu_validator = TCUValidator()
                tcu_results = tcu_validator.validate_all_tcu(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 TCU validation results logged")

                # Show completion message
                if tcu_results['compliance_score'] >= 90:
                    print("🏆 TCU validation completed - Excellent compliance! Ready for corruption detection")
                elif tcu_results['compliance_score'] >= 70:
                    print("👍 TCU validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ TCU validation completed - Significant improvements needed")

            if args.table == 'senado' or args.table == 'all':
                print("\n🔍 COMPREHENSIVE SENADO VALIDATION")
                print("Validating senado_politicians with family network detection readiness")
                print("=" * 60)

                # Initialize Senado validator
                senado_validator = SenadoValidator(logger)
                senado_results = senado_validator.validate_all_senado(limit=args.limit)

                # Export results if requested
                if args.export:
                    print(f"📄 Senado validation results logged")

                # Show completion message
                if senado_results['compliance_score'] >= 90:
                    print("🏆 Senado validation completed - Excellent compliance! Ready for family network detection")
                elif senado_results['compliance_score'] >= 70:
                    print("👍 Senado validation completed - Good compliance with minor issues")
                else:
                    print("⚠️ Senado validation completed - Significant improvements needed")

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