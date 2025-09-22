#!/usr/bin/env python3
"""
WORKING CLI FINAL - COMPLETES ALL 9 TABLES
Uses CLI v1 architecture but with fixed enhanced_logger
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


def working_populate_all_9_tables(db_manager, limit=None):
    """Working 9-table population using the original CLI v1 approach"""
    print("🚀 WORKING CLI FINAL: All 9 Tables")
    print("=" * 60)
    print(f"Limit: {limit if limit else 'No limit'}")
    print("=" * 60)

    # Import the actual working populators from CLI v1
    from cli.modules.politician_populator import PoliticianPopulator
    from cli.modules.financial_populator import FinancialPopulator
    from cli.modules.network_populator import NetworkPopulator
    from cli.modules.wealth_populator import WealthPopulator
    from cli.modules.career_populator import CareerPopulator
    from cli.modules.event_populator import EventPopulator
    from cli.modules.asset_populator import AssetPopulator
    from cli.modules.professional_populator import ProfessionalPopulator

    try:
        # Phase 1: Politicians (Foundation)
        print("\n1️⃣ POLITICIANS")
        start = time.time()
        politician_populator = PoliticianPopulator(db_manager)
        created_politician_ids = politician_populator.populate(limit=limit, active_only=True)
        duration = time.time() - start
        print(f"✅ Politicians: {len(created_politician_ids) if created_politician_ids else 0} processed in {duration:.1f}s")

        # Get politician IDs for other phases
        if limit:
            target_politician_ids = db_manager.execute_query(
                "SELECT id FROM unified_politicians ORDER BY id DESC LIMIT %s", (limit,)
            )
            politician_ids_for_processing = [row['id'] for row in target_politician_ids]
        else:
            politician_ids_for_processing = db_manager.get_all_politician_ids()

        print(f"📋 Processing {len(politician_ids_for_processing)} politicians for remaining tables")

        # Phase 2: Financial
        print("\n2️⃣ FINANCIAL")
        start = time.time()
        financial_populator = FinancialPopulator(db_manager)
        financial_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Financial populated in {duration:.1f}s")

        # Phase 3: Networks
        print("\n3️⃣ NETWORKS")
        start = time.time()
        network_populator = NetworkPopulator(db_manager)
        network_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Networks populated in {duration:.1f}s")

        # Phase 4: Wealth
        print("\n4️⃣ WEALTH")
        start = time.time()
        wealth_populator = WealthPopulator(db_manager)
        wealth_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Wealth populated in {duration:.1f}s")

        # Phase 5: Assets
        print("\n5️⃣ ASSETS")
        start = time.time()
        asset_populator = AssetPopulator(db_manager)
        asset_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Assets populated in {duration:.1f}s")

        # Phase 6: Career
        print("\n6️⃣ CAREER")
        start = time.time()
        career_populator = CareerPopulator(db_manager)
        career_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Career populated in {duration:.1f}s")

        # Phase 7: Events
        print("\n7️⃣ EVENTS")
        start = time.time()
        event_populator = EventPopulator(db_manager)
        event_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Events populated in {duration:.1f}s")

        # Phase 8: Professional
        print("\n8️⃣ PROFESSIONAL")
        start = time.time()
        professional_populator = ProfessionalPopulator(db_manager)
        professional_populator.populate(politician_ids=politician_ids_for_processing)
        duration = time.time() - start
        print(f"✅ Professional populated in {duration:.1f}s")

        print("\n🎯 WORKING CLI FINAL: ALL 9 TABLES COMPLETED!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


def show_complete_status(db_manager):
    """Show status of all 9 tables"""
    print("\n📊 COMPLETE DATABASE STATUS - ALL 9 TABLES")
    print("=" * 60)

    tables = [
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

    for table_name, query in tables:
        try:
            result = db_manager.execute_query(query)
            if result and len(result) > 0:
                count = result[0][0] if isinstance(result[0], (list, tuple)) else result[0].get('count', result[0].get('COUNT(*)', 0))
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
        print(f"✅ EXCELLENT: {success_rate:.0f}% success rate")
    elif success_rate >= 50:
        print(f"⚠️ PARTIAL: {success_rate:.0f}% success rate")
    else:
        print(f"❌ INCOMPLETE: {success_rate:.0f}% success rate")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Working CLI Final - Completes All 9 Tables")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status
    status_parser = subparsers.add_parser('status', help='Show all 9 tables status')

    # Populate
    pop_parser = subparsers.add_parser('populate', help='Populate database')
    pop_subparsers = pop_parser.add_subparsers(dest='table', help='What to populate')

    # All tables
    all_parser = pop_subparsers.add_parser('all', help='Populate all 9 tables')
    all_parser.add_argument('--limit', type=int, help='Limit number of politicians')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        db_manager = DatabaseManager()

        if args.command == 'status':
            show_complete_status(db_manager)

        elif args.command == 'populate':
            if not args.table:
                parser.print_help()
                return 1

            if args.table == 'all':
                success = working_populate_all_9_tables(db_manager, limit=args.limit)
                if success:
                    print("\n" + "="*60)
                    show_complete_status(db_manager)
                    print("="*60)
                    print("🎯 WORKING CLI FINAL COMPLETE!")
                    return 0
                else:
                    print("❌ Working CLI failed")
                    return 1
            else:
                print(f"❌ Unknown table: {args.table}")
                return 1

        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        print("✅ Working CLI completed successfully")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())