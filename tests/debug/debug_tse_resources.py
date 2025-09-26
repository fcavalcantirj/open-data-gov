#!/usr/bin/env python3
"""
DEBUG SCRIPT: Check what resources are actually in TSE packages
"""

import sys
import os
sys.path.append('/Users/fcavalcanti/dev/open-data-gov/src')

from clients.tse_client import TSEClient


def debug_tse_resources():
    """Debug what resources are actually in TSE packages"""
    print("🔍 DEBUGGING TSE PACKAGE RESOURCES")
    print("=" * 50)

    client = TSEClient()

    try:
        # Get 2022 finance packages
        packages = client.search_finance_packages(2022)
        print(f"📦 Found {len(packages)} finance packages for 2022:")
        for pkg in packages:
            print(f"   - {pkg}")

        if not packages:
            print("❌ No packages found")
            return

        # Get first package details
        main_package = packages[0]
        print(f"\n🔍 Examining package: {main_package}")

        package_info = client.get_package_info(main_package)
        resources = package_info.get('resources', [])

        print(f"📋 Package has {len(resources)} resources:")

        # Show all resources to see what's actually there
        for i, resource in enumerate(resources):
            name = resource.get('name', 'Unknown')
            format_type = resource.get('format', 'Unknown')
            url = resource.get('url', '')

            print(f"\n   📄 Resource {i+1}: {name}")
            print(f"       Format: {format_type}")
            print(f"       URL: {url[:100]}...")

            # Check if it looks like finance data
            if any(keyword in name.lower() for keyword in ['receita', 'despesa', 'financ', 'prestacao']):
                print(f"       💰 LOOKS LIKE FINANCE DATA!")

            if format_type.lower() == 'zip':
                print(f"       📦 ZIP file - might contain finance CSVs")

    except Exception as e:
        print(f"❌ Error debugging resources: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run resource debugging"""
    print("🚀 TSE RESOURCE DEBUGGING")
    print("Find out what's actually in the TSE packages")
    print("=" * 60)

    debug_tse_resources()


if __name__ == "__main__":
    main()