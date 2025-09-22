#!/usr/bin/env python3
"""
CLI v3 - MINIMAL, NO HANGING
Ultra-simple, direct database operations only
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


def minimal_test(db_manager, limit=None):
    """Ultra-minimal test - just database operations"""
    print("🚀 CLI v3 - Minimal Test (NO HANGING)")
    print("=" * 50)

    try:
        # Test 1: Simple query
        print("\n1️⃣ Testing basic database connection...")
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM unified_politicians")
        current_count = result[0]['count'] if result else 0
        print(f"✅ Current politicians: {current_count}")

        # Test 2: Show all table counts
        print("\n2️⃣ Testing all table counts...")
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

        for table in tables:
            try:
                result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                count = result[0]['count'] if result else 0
                status = "✅" if count > 0 else "⚪"
                print(f"{status} {table}: {count}")
            except Exception as e:
                print(f"❌ {table}: ERROR - {e}")

        print("\n🎯 Minimal test completed - NO HANGING!")
        return True

    except Exception as e:
        print(f"❌ Minimal test failed: {e}")
        return False


def main():
    """Main CLI v3 entry point"""
    parser = argparse.ArgumentParser(description="CLI v3 - Minimal & No Hanging")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run minimal test')
    test_parser.add_argument('--limit', type=int, help='Limit (not used yet)')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show database status')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        db_manager = DatabaseManager()

        if args.command == 'test':
            minimal_test(db_manager, limit=args.limit)
        elif args.command == 'status':
            db_manager.show_status(detailed=True)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        print("✅ CLI v3 completed successfully")
        return 0

    except Exception as e:
        print(f"❌ CLI v3 Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())