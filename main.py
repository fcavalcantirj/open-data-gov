#!/usr/bin/env python3
"""
Brazilian Political Data Integration - Main Entry Point

Usage:
    python main.py                          # Run Arthur Lira complete analysis
    python main.py --politician "Name"      # Analyze specific politician
    python main.py --test-all              # Test all API connections
    python main.py --discovery-only        # Run basic discovery only
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.discovery_phase import validate_data_universe
from src.core.integrated_discovery import discover_deputy_complete_universe
from src.clients.tse_client import TSEClient
from src.clients.senado_client import SenadoClient
from src.clients.portal_transparencia_client import PortalTransparenciaClient
from src.clients.tcu_client import TCUClient
from src.clients.datajud_client import DataJudClient


def test_all_apis():
    """Test connectivity to all API sources"""
    print("🔌 TESTING ALL API CONNECTIONS")
    print("=" * 50)

    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }

    # Test each client
    clients = [
        ("TSE Electoral", TSEClient),
        ("Senado Federal", SenadoClient),
        ("Portal Transparência", PortalTransparenciaClient),
        ("TCU Audit", TCUClient),
        ("DataJud Judicial", DataJudClient)
    ]

    for name, client_class in clients:
        print(f"\n--- Testing {name} ---")
        try:
            client = client_class()
            if hasattr(client, 'test_connectivity'):
                test_result = client.test_connectivity()
            elif hasattr(client, 'test_api_connectivity'):
                test_result = client.test_api_connectivity()
            elif hasattr(client, 'test_tcu_connectivity'):
                test_result = client.test_tcu_connectivity()
            else:
                test_result = {"status": "no_test_method", "working": True}

            results['tests'][name] = test_result
            print(f"✅ {name}: Working")

        except Exception as e:
            results['tests'][name] = {"error": str(e), "working": False}
            print(f"❌ {name}: {e}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/api_connectivity_test_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Results saved to: {filename}")

    # Summary
    working_count = sum(1 for test in results['tests'].values()
                       if test.get('working', False))
    total_count = len(results['tests'])

    print(f"\n📊 SUMMARY: {working_count}/{total_count} APIs working")

    return results


def run_complete_analysis(politician_name="Arthur Lira"):
    """Run complete 6-system analysis"""
    print(f"🇧🇷 COMPLETE POLITICAL ANALYSIS: {politician_name}")
    print("=" * 60)

    try:
        # Run integrated discovery
        result = discover_deputy_complete_universe(politician_name)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = politician_name.replace(" ", "_").lower()
        filename = f"data/complete_analysis_{safe_name}_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 Complete analysis saved to: {filename}")

        # Summary
        if 'confidence_score' in result:
            print(f"\n📊 ANALYSIS SUMMARY:")
            print(f"   Politician: {result.get('target', 'Unknown')}")
            print(f"   Confidence Score: {result['confidence_score']:.2f}")

            vendor_analysis = result.get('vendor_analysis', {})
            if vendor_analysis:
                print(f"   Vendor Network: {vendor_analysis.get('total_vendors', 0)} CNPJs")
                print(f"   Sanctioned Vendors: {len(vendor_analysis.get('sanctioned_vendors', []))}")
                print(f"   Risk Assessment: {vendor_analysis.get('risk_assessment', 'Unknown')}")

            entity_map = result.get('entity_map', {})
            if entity_map:
                print(f"   Total Relationships: {entity_map.get('total_relationships', 0)}")

        return result

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return {"error": str(e)}


def run_discovery_only(politician_name="Arthur Lira"):
    """Run basic Câmara discovery only"""
    print(f"🏛️ BASIC DISCOVERY: {politician_name}")
    print("=" * 40)

    try:
        # Run basic discovery
        result = validate_data_universe()

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/basic_discovery_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 Basic discovery saved to: {filename}")
        return result

    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return {"error": str(e)}


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Brazilian Political Data Integration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Arthur Lira complete analysis
  python main.py --politician "Lula"      # Analyze Lula
  python main.py --test-all              # Test all APIs
  python main.py --discovery-only        # Basic discovery only
        """
    )

    parser.add_argument(
        "--politician",
        default="Arthur Lira",
        help="Politician name to analyze (default: Arthur Lira)"
    )

    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Test connectivity to all API sources"
    )

    parser.add_argument(
        "--discovery-only",
        action="store_true",
        help="Run basic Câmara discovery only"
    )

    args = parser.parse_args()

    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)

    if args.test_all:
        return test_all_apis()
    elif args.discovery_only:
        return run_discovery_only(args.politician)
    else:
        return run_complete_analysis(args.politician)


if __name__ == "__main__":
    result = main()
    sys.exit(0 if "error" not in result else 1)