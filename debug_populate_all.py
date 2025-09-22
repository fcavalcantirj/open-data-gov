#!/usr/bin/env python3
"""
Debug version of populate all to find exact hanging point
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

from cli.modules.database_manager import DatabaseManager
from cli.modules.politician_populator import PoliticianPopulator
from cli.modules.financial_populator import FinancialPopulator
from cli.modules.network_populator import NetworkPopulator

def debug_populate_all():
    print("🔍 DEBUG: Starting populate all workflow")

    db_manager = DatabaseManager()
    limit = 1

    # Step 1: Politicians
    print("\n🔍 DEBUG: Step 1 - Politicians")
    politician_populator = PoliticianPopulator(db_manager)
    created_politician_ids = politician_populator.populate(limit=limit, active_only=True)
    print("🔍 DEBUG: Politicians phase completed")

    # Get politician IDs for subsequent phases
    print("\n🔍 DEBUG: Getting politician IDs for subsequent phases")
    if limit:
        target_politician_ids = db_manager.execute_query(
            "SELECT id FROM unified_politicians ORDER BY id DESC LIMIT ?", (limit,)
        )
        politician_ids_for_processing = [row['id'] for row in target_politician_ids]
        print(f"🔍 DEBUG: Using limited set of {len(politician_ids_for_processing)} politicians: {politician_ids_for_processing}")
    else:
        politician_ids_for_processing = db_manager.get_all_politician_ids()
        print(f"🔍 DEBUG: Using all {len(politician_ids_for_processing)} politicians")

    # Step 2: Financial
    print("\n🔍 DEBUG: Step 2 - Financial")
    print("🔍 DEBUG: Creating FinancialPopulator...")
    financial_populator = FinancialPopulator(db_manager)
    print("🔍 DEBUG: Calling financial_populator.populate()...")
    financial_populator.populate(politician_ids=politician_ids_for_processing)
    print("🔍 DEBUG: Financial phase completed")

    # Step 3: Networks - THIS IS WHERE IT HANGS
    print("\n🔍 DEBUG: Step 3 - Networks (CRITICAL SECTION)")
    print("🔍 DEBUG: Creating NetworkPopulator...")
    try:
        network_populator = NetworkPopulator(db_manager)
        print("🔍 DEBUG: NetworkPopulator created successfully")
        print("🔍 DEBUG: About to call network_populator.populate()...")
        network_populator.populate(politician_ids=politician_ids_for_processing)
        print("🔍 DEBUG: Networks phase completed")
    except Exception as e:
        print(f"🔍 DEBUG: Networks phase FAILED: {e}")
        import traceback
        print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        return

    print("\n🔍 DEBUG: All phases completed successfully!")

if __name__ == "__main__":
    debug_populate_all()