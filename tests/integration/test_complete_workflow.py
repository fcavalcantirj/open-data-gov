#!/usr/bin/env python3
"""
Complete Workflow Validation Test
Tests all phases of the political transparency data population pipeline
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
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


def test_complete_workflow():
    """Test the complete data population workflow"""
    print("🔬 COMPLETE WORKFLOW VALIDATION TEST")
    print("=" * 60)

    # Initialize database manager
    db_manager = DatabaseManager()
    print(f"📊 Database: {db_manager.db_type}")

    # Clear database for clean test
    print("\n🗑️  Clearing database for clean test...")
    db_manager.clear_all_data()

    # Show initial empty state
    print("\n📋 Initial database state:")
    db_manager.show_status()

    # Test Phase 1: Politicians
    print("\n" + "=" * 60)
    print("🏛️  PHASE 1: POLITICIANS POPULATION")
    print("=" * 60)

    politician_populator = PoliticianPopulator(db_manager)
    try:
        # Populate just 3 politicians for testing
        politician_populator.populate(limit=3)
        print("✅ Politicians phase completed")
    except Exception as e:
        print(f"❌ Politicians phase failed: {e}")
        return False

    # Get politician IDs for subsequent phases
    politician_ids = db_manager.get_all_politician_ids()
    print(f"📋 Found {len(politician_ids)} politicians for subsequent phases")

    if not politician_ids:
        print("❌ No politicians found - cannot continue workflow")
        return False

    # Test Phase 2: Financial Data
    print("\n" + "=" * 60)
    print("💰 PHASE 2: FINANCIAL DATA POPULATION")
    print("=" * 60)

    financial_populator = FinancialPopulator(db_manager)
    try:
        financial_populator.populate(politician_ids=politician_ids[:2])  # Test with first 2
        print("✅ Financial phase completed")
    except Exception as e:
        print(f"❌ Financial phase failed: {e}")

    # Test Phase 3: Networks
    print("\n" + "=" * 60)
    print("🕸️  PHASE 3: POLITICAL NETWORKS POPULATION")
    print("=" * 60)

    network_populator = NetworkPopulator(db_manager)
    try:
        network_populator.populate(politician_ids=politician_ids[:2])
        print("✅ Networks phase completed")
    except Exception as e:
        print(f"❌ Networks phase failed: {e}")

    # Test Phase 4: Wealth Tracking
    print("\n" + "=" * 60)
    print("💎 PHASE 4: WEALTH TRACKING POPULATION")
    print("=" * 60)

    wealth_populator = WealthPopulator(db_manager)
    try:
        wealth_populator.populate(politician_ids=politician_ids[:2])
        print("✅ Wealth tracking phase completed")
    except Exception as e:
        print(f"❌ Wealth tracking phase failed: {e}")

    # Test Phase 5: Career History
    print("\n" + "=" * 60)
    print("📋 PHASE 5: CAREER HISTORY POPULATION")
    print("=" * 60)

    career_populator = CareerPopulator(db_manager)
    try:
        career_populator.populate(politician_ids=politician_ids[:2])
        print("✅ Career history phase completed")
    except Exception as e:
        print(f"❌ Career history phase failed: {e}")

    # Test Phase 6: Events
    print("\n" + "=" * 60)
    print("📅 PHASE 6: POLITICAL EVENTS POPULATION")
    print("=" * 60)

    event_populator = EventPopulator(db_manager)
    try:
        event_populator.populate(politician_ids=politician_ids[:2])
        print("✅ Events phase completed")
    except Exception as e:
        print(f"❌ Events phase failed: {e}")

    # Test Phase 7: Individual Assets
    print("\n" + "=" * 60)
    print("🏠 PHASE 7: INDIVIDUAL ASSETS POPULATION")
    print("=" * 60)

    asset_populator = AssetPopulator(db_manager)
    try:
        asset_populator.populate(politician_ids=politician_ids[:2])
        print("✅ Individual assets phase completed")
    except Exception as e:
        print(f"❌ Individual assets phase failed: {e}")

    # Test Phase 8: Professional Background
    print("\n" + "=" * 60)
    print("👔 PHASE 8: PROFESSIONAL BACKGROUND POPULATION")
    print("=" * 60)

    professional_populator = ProfessionalPopulator(db_manager)
    try:
        professional_populator.populate(politician_ids=politician_ids[:2])
        print("✅ Professional background phase completed")
    except Exception as e:
        print(f"❌ Professional background phase failed: {e}")

    # Final Database Status
    print("\n" + "=" * 60)
    print("📊 FINAL DATABASE STATUS")
    print("=" * 60)

    db_manager.show_status(detailed=True)

    # Validation Summary
    print("\n" + "=" * 60)
    print("✅ WORKFLOW VALIDATION SUMMARY")
    print("=" * 60)

    tables = [
        'unified_politicians',
        'unified_financial_records',
        'financial_counterparts',
        'unified_political_networks',
        'unified_wealth_tracking',
        'politician_career_history',
        'politician_events',
        'politician_assets',
        'politician_professional_background'
    ]

    populated_tables = 0
    total_records = 0

    for table in tables:
        try:
            count = db_manager.get_table_count(table)
            if count > 0:
                populated_tables += 1
                total_records += count
                print(f"✅ {table}: {count} records")
            else:
                print(f"⚪ {table}: Empty")
        except Exception as e:
            print(f"❌ {table}: Error - {e}")

    print(f"\n📈 Summary:")
    print(f"   Tables populated: {populated_tables}/9")
    print(f"   Total records: {total_records:,}")

    success_rate = (populated_tables / 9) * 100
    print(f"   Success rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("\n🎉 WORKFLOW VALIDATION: EXCELLENT")
        return True
    elif success_rate >= 60:
        print("\n✅ WORKFLOW VALIDATION: GOOD")
        return True
    elif success_rate >= 40:
        print("\n⚠️  WORKFLOW VALIDATION: PARTIAL")
        return False
    else:
        print("\n❌ WORKFLOW VALIDATION: FAILED")
        return False


if __name__ == "__main__":
    print("🔬 Brazilian Political Transparency - Complete Workflow Test")
    print("=" * 70)

    success = test_complete_workflow()

    print("\n" + "=" * 70)
    if success:
        print("✅ COMPLETE WORKFLOW TEST: PASSED")
    else:
        print("❌ COMPLETE WORKFLOW TEST: FAILED")
    print("=" * 70)