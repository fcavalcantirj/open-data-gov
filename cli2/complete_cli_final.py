#!/usr/bin/env python3
"""
CLI v2 - COMPLETE IMPLEMENTATION FOR ALL 9 TABLES
Based on docs/analysis/unified/ comprehensive architecture
Sequential, No-Hanging, Production-Ready
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

from cli.modules.database_manager import DatabaseManager


def populate_all_9_tables_v2(db_manager, limit=None):
    """Complete 9-table population workflow - CLI v2"""
    print("🚀 CLI v2: Complete 9-Table Population Workflow")
    print("=" * 60)
    print("Based on docs/analysis/unified/ architecture")
    print(f"Limit: {limit if limit else 'No limit'}")
    print("=" * 60)

    # Import all the original populators (they work, just disable enhanced_logger)
    from cli.modules.politician_populator import PoliticianPopulator
    from cli.modules.financial_populator import FinancialPopulator
    from cli.modules.network_populator import NetworkPopulator
    from cli.modules.wealth_populator import WealthPopulator
    from cli.modules.career_populator import CareerPopulator
    from cli.modules.event_populator import EventPopulator
    from cli.modules.asset_populator import AssetPopulator
    from cli.modules.professional_populator import ProfessionalPopulator

    # Disable enhanced_logger globally by replacing it
    import cli.modules.enhanced_logger as enhanced_logger_module

    class DummyLogger:
        def log_processing(self, *args, **kwargs): pass
        def log_api_call(self, *args, **kwargs): pass
        def log_data_issue(self, *args, **kwargs): pass
        def save_session_metrics(self): pass

    enhanced_logger_module.enhanced_logger = DummyLogger()

    try:
        # Table 1: POLITICIANS (Foundation)
        print("\n1️⃣ UNIFIED_POLITICIANS (Foundation Table)")
        start = time.time()
        politician_populator = PoliticianPopulator(db_manager)
        created_politician_ids = politician_populator.populate(limit=limit, active_only=True)
        duration = time.time() - start
        print(f"✅ Politicians: {len(created_politician_ids) if created_politician_ids else 0} processed in {duration:.1f}s")

        # Get politician IDs for subsequent phases
        if limit:
            target_politician_ids = db_manager.execute_query(
                "SELECT id FROM unified_politicians ORDER BY id DESC LIMIT ?", (limit,)
            )
            politician_ids_for_processing = [row['id'] for row in target_politician_ids]
            print(f"📋 Using limited set of {len(politician_ids_for_processing)} politicians for subsequent phases")
        else:
            politician_ids_for_processing = db_manager.get_all_politician_ids()
            print(f"📋 Using all {len(politician_ids_for_processing)} politicians for subsequent phases")

        # Table 2 & 3: FINANCIAL (counterparts + records)
        print("\n2️⃣ FINANCIAL COUNTERPARTS + UNIFIED_FINANCIAL_RECORDS")
        start = time.time()
        financial_populator = FinancialPopulator(db_manager)
        financial_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Financial data populated in {duration:.1f}s")

        # Table 4: POLITICAL NETWORKS
        print("\n3️⃣ UNIFIED_POLITICAL_NETWORKS")
        start = time.time()
        network_populator = NetworkPopulator(db_manager)
        network_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Political networks populated in {duration:.1f}s")

        # Table 5: WEALTH TRACKING
        print("\n4️⃣ UNIFIED_WEALTH_TRACKING")
        start = time.time()
        wealth_populator = WealthPopulator(db_manager)
        wealth_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Wealth tracking populated in {duration:.1f}s")

        # Table 6: POLITICIAN ASSETS
        print("\n5️⃣ POLITICIAN_ASSETS")
        start = time.time()
        asset_populator = AssetPopulator(db_manager)
        asset_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Individual assets populated in {duration:.1f}s")

        # Table 7: CAREER HISTORY
        print("\n6️⃣ POLITICIAN_CAREER_HISTORY")
        start = time.time()
        career_populator = CareerPopulator(db_manager)
        career_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Career history populated in {duration:.1f}s")

        # Table 8: EVENTS
        print("\n7️⃣ POLITICIAN_EVENTS")
        start = time.time()
        event_populator = EventPopulator(db_manager)
        event_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Events populated in {duration:.1f}s")

        # Table 9: PROFESSIONAL BACKGROUND
        print("\n8️⃣ POLITICIAN_PROFESSIONAL_BACKGROUND")
        start = time.time()
        professional_populator = ProfessionalPopulator(db_manager)
        professional_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Professional background populated in {duration:.1f}s")

        print("\n🎯 CLI v2: ALL 9 TABLES POPULATED SUCCESSFULLY!")
        return True

    except Exception as e:
        print(f"❌ Error in CLI v2 workflow: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


def show_final_status(db_manager):
    """Show comprehensive status of all 9 tables"""
    print("\n📊 FINAL DATABASE STATUS - ALL 9 TABLES")
    print("=" * 60)

    table_queries = [
        ("1. unified_politicians", "SELECT COUNT(*) FROM unified_politicians"),
        ("2. financial_counterparts", "SELECT COUNT(*) FROM financial_counterparts"),
        ("3. unified_financial_records", "SELECT COUNT(*) FROM unified_financial_records"),
        ("4. unified_political_networks", "SELECT COUNT(*) FROM unified_political_networks"),
        ("5. unified_wealth_tracking", "SELECT COUNT(*) FROM unified_wealth_tracking"),
        ("6. politician_assets", "SELECT COUNT(*) FROM politician_assets"),
        ("7. politician_career_history", "SELECT COUNT(*) FROM politician_career_history"),
        ("8. politician_events", "SELECT COUNT(*) FROM politician_events"),
        ("9. politician_professional_background", "SELECT COUNT(*) FROM politician_professional_background")
    ]

    total_records = 0
    populated_tables = 0

    for table_name, query in table_queries:
        try:
            result = db_manager.execute_query(query)
            # Handle different result formats
            if result and len(result) > 0:
                if isinstance(result[0], dict):
                    count = result[0].get('COUNT(*)', 0)
                elif isinstance(result[0], (list, tuple)):
                    count = result[0][0] if len(result[0]) > 0 else 0
                else:
                    count = result[0]
            else:
                count = 0

            total_records += count
            if count > 0:
                populated_tables += 1
                status = "✅"
            else:
                status = "⚪"
            print(f"{status} {table_name:<35} {count:>10,} records")
        except Exception as e:
            print(f"❌ {table_name:<35} ERROR: {e}")

    print("=" * 60)
    print(f"📈 SUMMARY: {populated_tables}/9 tables populated, {total_records:,} total records")

    success_rate = (populated_tables / 9) * 100
    if success_rate == 100:
        print("🎉 PERFECT! All 9 tables successfully populated!")
    elif success_rate >= 80:
        print(f"✅ GOOD: {success_rate:.0f}% success rate")
    else:
        print(f"⚠️ NEEDS WORK: {success_rate:.0f}% success rate")


def main():
    """Main CLI v2 entry point"""
    parser = argparse.ArgumentParser(description="CLI v2 - Complete 9-Table Implementation")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show all 9 tables status')

    # Populate commands
    pop_parser = subparsers.add_parser('populate', help='Populate database')
    pop_subparsers = pop_parser.add_subparsers(dest='table', help='Table to populate')

    # All tables
    all_parser = pop_subparsers.add_parser('all', help='Populate all 9 tables')
    all_parser.add_argument('--limit', type=int, help='Limit number of politicians')

    # Individual table commands (for testing)
    politicians_parser = pop_subparsers.add_parser('politicians', help='Test politicians only')
    politicians_parser.add_argument('--limit', type=int, help='Limit number')

    financial_parser = pop_subparsers.add_parser('financial', help='Test financial only')
    financial_parser.add_argument('--limit', type=int, help='Limit number')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        db_manager = DatabaseManager()

        if args.command == 'status':
            show_final_status(db_manager)

        elif args.command == 'populate':
            if not args.table:
                parser.print_help()
                return 1

            if args.table == 'all':
                success = populate_all_9_tables_v2(db_manager, limit=args.limit)
                if success:
                    print("\n" + "="*60)
                    show_final_status(db_manager)
                    print("="*60)
                    print("🎯 CLI v2 COMPLETE! All 9 tables processed.")
                    return 0
                else:
                    print("❌ CLI v2 workflow failed")
                    return 1

            elif args.table == 'politicians':
                # Simple test for politicians only
                from cli.modules.politician_populator import PoliticianPopulator
                populator = PoliticianPopulator(db_manager)
                result = populator.populate(limit=args.limit, active_only=True)
                print(f"✅ Politicians test: {len(result) if result else 0}")

            elif args.table == 'financial':
                # Simple test for financial only
                from cli.modules.financial_populator import FinancialPopulator
                populator = FinancialPopulator(db_manager)

                # Get politician IDs
                if args.limit:
                    politicians = db_manager.execute_query(
                        "SELECT id FROM unified_politicians LIMIT ?", (args.limit,)
                    )
                else:
                    politicians = db_manager.execute_query(
                        "SELECT id FROM unified_politicians LIMIT 5"
                    )

                politician_ids = [p['id'] for p in politicians]
                populator.populate(politician_ids=politician_ids)
                print(f"✅ Financial test: {len(politician_ids)} politicians")

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
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())