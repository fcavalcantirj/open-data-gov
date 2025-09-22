#!/usr/bin/env python3
"""
CLI v2 - Ultra-Simple, Zero-Dependencies Architecture
No inheritance from broken classes, completely standalone.
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


def test_simple_workflow(limit=None):
    """Ultra-simple test that just works"""
    print("🚀 CLI v2 - Simple Workflow Test")

    db_manager = DatabaseManager()

    # Step 1: Check status
    print("\n📊 Database Status:")
    db_manager.show_status()

    # Step 2: Test a simple query
    print(f"\n🔍 Testing simple politician query...")
    if limit:
        politicians = db_manager.execute_query(
            "SELECT id, name FROM unified_politicians LIMIT ?", (limit,)
        )
    else:
        politicians = db_manager.execute_query(
            "SELECT id, name FROM unified_politicians LIMIT 5"
        )

    print(f"✅ Found {len(politicians)} politicians:")
    for p in politicians[:3]:  # Show first 3
        print(f"  - ID {p['id']}: {p['name']}")

    print(f"\n🎯 Simple workflow completed successfully!")
    return True


def main():
    """Main CLI v2 entry point"""
    parser = argparse.ArgumentParser(description="CLI v2 - Simple & Reliable")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run simple test workflow')
    test_parser.add_argument('--limit', type=int, default=5, help='Limit results')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show database status')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == 'test':
            test_simple_workflow(limit=args.limit)
        elif args.command == 'status':
            db_manager = DatabaseManager()
            db_manager.show_status(detailed=True)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        print("✅ CLI v2 completed successfully")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())