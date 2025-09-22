#!/usr/bin/env python3
"""
CLI v3 - COMPLETE & NO HANGING
Full 9-table population using existing code but with ultra-simple logging
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

from cli.modules.database_manager import DatabaseManager


def populate_all_9_tables_v3(db_manager, limit=None):
    """Complete 9-table population - CLI v3 with no hanging"""
    print("🚀 CLI v3: Complete 9-Table Population - NO HANGING")
    print("=" * 60)
    print(f"Limit: {limit if limit else 'No limit'}")
    print("=" * 60)

    # Override enhanced_logger to prevent hanging
    import cli.modules.enhanced_logger as enhanced_logger_module

    class NoHangLogger:
        def log_processing(self, *args, **kwargs):
            # Just print without hanging
            if len(args) >= 3:
                entity_type, entity_id, status = args[0], args[1], args[2]
                details = kwargs.get('details', {})
                if status == "success":
                    print(f"✅ {entity_type} {entity_id}: success")
                elif status == "error":
                    print(f"❌ {entity_type} {entity_id}: error")
                elif status == "warning":
                    print(f"⚠️ {entity_type} {entity_id}: warning")

        def log_api_call(self, *args, **kwargs): pass
        def log_data_issue(self, *args, **kwargs): pass
        def save_session_metrics(self): pass

    # Replace the enhanced logger
    enhanced_logger_module.enhanced_logger = NoHangLogger()

    try:
        # Import populators
        from cli.modules.politician_populator import PoliticianPopulator
        from cli.modules.financial_populator import FinancialPopulator
        from cli.modules.network_populator import NetworkPopulator
        from cli.modules.wealth_populator import WealthPopulator
        from cli.modules.career_populator import CareerPopulator
        from cli.modules.event_populator import EventPopulator
        from cli.modules.asset_populator import AssetPopulator
        from cli.modules.professional_populator import ProfessionalPopulator

        # Table 1: POLITICIANS
        print("\n1️⃣ UNIFIED_POLITICIANS")
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
        else:
            politician_ids_for_processing = db_manager.get_all_politician_ids()

        print(f"📋 Processing {len(politician_ids_for_processing)} politicians for subsequent phases")

        # Table 2 & 3: FINANCIAL
        print("\n2️⃣ FINANCIAL DATA")
        start = time.time()
        financial_populator = FinancialPopulator(db_manager)
        financial_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Financial data populated in {duration:.1f}s")

        # Table 4: NETWORKS
        print("\n3️⃣ POLITICAL NETWORKS")
        start = time.time()
        network_populator = NetworkPopulator(db_manager)
        network_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Networks populated in {duration:.1f}s")

        # Table 5: WEALTH
        print("\n4️⃣ WEALTH TRACKING")
        start = time.time()
        wealth_populator = WealthPopulator(db_manager)
        wealth_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Wealth populated in {duration:.1f}s")

        # Table 6: ASSETS
        print("\n5️⃣ POLITICIAN ASSETS")
        start = time.time()
        asset_populator = AssetPopulator(db_manager)
        asset_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Assets populated in {duration:.1f}s")

        # Table 7: CAREER
        print("\n6️⃣ CAREER HISTORY")
        start = time.time()
        career_populator = CareerPopulator(db_manager)
        career_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Career populated in {duration:.1f}s")

        # Table 8: EVENTS
        print("\n7️⃣ EVENTS")
        start = time.time()
        event_populator = EventPopulator(db_manager)
        event_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Events populated in {duration:.1f}s")

        # Table 9: PROFESSIONAL
        print("\n8️⃣ PROFESSIONAL BACKGROUND")
        start = time.time()
        professional_populator = ProfessionalPopulator(db_manager)
        professional_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Professional populated in {duration:.1f}s")

        print("\n🎯 CLI v3: ALL 9 TABLES POPULATED SUCCESSFULLY!")
        return True

    except Exception as e:
        print(f"❌ Error in CLI v3: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


def show_final_status_v3(db_manager):
    """Show status of all 9 tables"""
    print("\n📊 FINAL DATABASE STATUS - ALL 9 TABLES")
    print("=" * 60)

    tables = [
        "unified_politicians",
        "financial_counterparts",
        "unified_financial_records",
        "unified_political_networks",
        "unified_wealth_tracking",
        "politician_assets",
        "politician_career_history",
        "politician_events",
        "politician_professional_background"
    ]

    total_records = 0
    populated_tables = 0

    for i, table in enumerate(tables, 1):
        try:
            result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            count = result[0]['count'] if result else 0

            total_records += count
            if count > 0:
                populated_tables += 1
                status = "✅"
            else:
                status = "⚪"

            print(f"{status} {i}. {table:<35} {count:>10,} records")

        except Exception as e:
            print(f"❌ {i}. {table:<35} ERROR: {e}")

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
    """Main CLI v3 entry point"""
    parser = argparse.ArgumentParser(description="CLI v3 - Complete & No Hanging")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show all 9 tables status')

    # Populate commands
    pop_parser = subparsers.add_parser('populate', help='Populate database')
    pop_subparsers = pop_parser.add_subparsers(dest='table', help='Table to populate')

    # All tables
    all_parser = pop_subparsers.add_parser('all', help='Populate all 9 tables')
    all_parser.add_argument('--limit', type=int, help='Limit number of politicians')

    # Test command
    test_parser = subparsers.add_parser('test', help='Quick database test')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        db_manager = DatabaseManager()

        if args.command == 'status':
            show_final_status_v3(db_manager)

        elif args.command == 'test':
            print("🚀 CLI v3 - Quick Test")
            result = db_manager.execute_query("SELECT COUNT(*) as count FROM unified_politicians")
            count = result[0]['count'] if result else 0
            print(f"✅ Database connected, {count} politicians found")

        elif args.command == 'populate':
            if not args.table:
                parser.print_help()
                return 1

            if args.table == 'all':
                success = populate_all_9_tables_v3(db_manager, limit=args.limit)
                if success:
                    print("\n" + "="*60)
                    show_final_status_v3(db_manager)
                    print("="*60)
                    print("🎯 CLI v3 COMPLETE! All 9 tables processed.")
                    return 0
                else:
                    print("❌ CLI v3 workflow failed")
                    return 1
            else:
                print(f"❌ Unknown table: {args.table}")
                return 1

        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        print("✅ CLI v3 completed successfully")
        return 0

    except Exception as e:
        print(f"❌ CLI v3 Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())