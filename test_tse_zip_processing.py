#!/usr/bin/env python3
"""
Test script for TSE asset ZIP file processing
Validates ZIP download, content inspection, and data extraction
"""

import sys
from pathlib import Path
import zipfile
import io
import csv
import requests
from typing import Dict, List, Any

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.clients.tse_client import TSEClient


def test_zip_content_inspection():
    """Test downloading and inspecting ZIP file contents"""
    print("🔍 TESTING TSE ASSET ZIP PROCESSING")
    print("=" * 50)

    tse_client = TSEClient()

    # Test with 2024 data (most recent)
    year = 2024
    print(f"\n📅 Testing with {year} asset data")

    try:
        # Find candidate packages for asset data
        print("🔗 Searching for candidate packages...")
        candidate_packages = tse_client.search_candidates_packages(year)

        if not candidate_packages:
            print("❌ No candidate packages found")
            return False

        print(f"📦 Found {len(candidate_packages)} candidate packages for {year}")

        # Get the main candidates package
        main_package = None
        for pkg in candidate_packages:
            if f'candidatos-{year}' == pkg:
                main_package = pkg
                break

        if not main_package:
            print("❌ No main candidate package found")
            return False

        print(f"🧪 Testing package: {main_package}")

        # Get package details
        package_info = tse_client.get_package_info(main_package)
        resources = package_info.get('resources', [])
        print(f"📄 Package contains {len(resources)} resources")

        # Look for asset resources (Bens de candidatos)
        asset_resources = []
        zip_resources = []
        csv_resources = []
        other_resources = []

        for resource in resources:
            resource_name = resource.get('name', '')
            download_url = resource.get('url', '')

            if resource.get('format', '').lower() in ['csv', 'txt']:
                if 'bens' in resource_name.lower() and 'candidatos' in resource_name.lower():
                    asset_resources.append(resource)
                    if download_url.endswith('.zip'):
                        zip_resources.append(resource)
                    elif download_url.endswith('.csv') or download_url.endswith('.txt'):
                        csv_resources.append(resource)
            else:
                other_resources.append(resource)

        print(f"  📋 Asset resources: {len(asset_resources)}")
        print(f"  📦 ZIP files: {len(zip_resources)}")
        print(f"  📊 CSV files: {len(csv_resources)}")
        print(f"  📋 Other files: {len(other_resources)}")

        if not asset_resources:
            print("❌ No asset resources found")
            return False

        # Test ZIP processing if available
        if zip_resources:
            test_resource = zip_resources[0]
            print(f"\n🔬 Testing ZIP resource: {test_resource.get('name')}")
            return test_zip_file_processing(test_resource)
        elif csv_resources:
            test_resource = csv_resources[0]
            print(f"\n🔬 Testing CSV resource: {test_resource.get('name')}")
            return test_csv_file_processing(test_resource)
        else:
            print("❌ No suitable test resources found")
            return False

    except Exception as e:
        print(f"❌ Error in dataset inspection: {e}")
        return False


def test_zip_file_processing(resource: Dict[str, Any]) -> bool:
    """Test processing a specific ZIP file"""
    download_url = resource.get('url', '')
    resource_name = resource.get('name', '')

    print(f"📥 Downloading: {resource_name}")
    print(f"🔗 URL: {download_url}")

    try:
        # Download the ZIP file
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()

        print(f"✅ Downloaded {len(response.content)} bytes")

        # Inspect ZIP contents
        print("\n🔍 Inspecting ZIP contents...")

        with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zip_file:
            file_list = zip_file.namelist()
            print(f"📁 ZIP contains {len(file_list)} files:")

            for file_name in file_list:
                file_info = zip_file.getinfo(file_name)
                print(f"  📄 {file_name} ({file_info.file_size} bytes)")

                # Check file type
                if file_name.lower().endswith('.csv'):
                    print(f"    → CSV file detected")
                elif file_name.lower().endswith('.txt'):
                    print(f"    → Text file detected")
                elif file_name.lower().endswith('.pdf'):
                    print(f"    → PDF file detected (will skip)")
                else:
                    print(f"    → Unknown file type")

        # Test data extraction
        print("\n🧮 Testing data extraction...")
        tse_client = TSEClient()
        assets = tse_client._process_zip_asset_data(response.content)

        print(f"✅ Extracted {len(assets)} asset records")

        # Show sample data
        if assets:
            print("\n📊 Sample asset record:")
            sample_asset = assets[0]
            for key, value in list(sample_asset.items())[:5]:
                print(f"  {key}: {value}")
            if len(sample_asset) > 5:
                print(f"  ... and {len(sample_asset) - 5} more fields")

        return True

    except Exception as e:
        print(f"❌ Error processing ZIP file: {e}")
        return False


def test_csv_file_processing(resource: Dict[str, Any]) -> bool:
    """Test processing a specific CSV file"""
    download_url = resource.get('url', '')
    resource_name = resource.get('name', '')

    print(f"📥 Downloading: {resource_name}")
    print(f"🔗 URL: {download_url}")

    try:
        # Download the CSV file
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()

        print(f"✅ Downloaded {len(response.content)} bytes")

        # Test data extraction
        print("\n🧮 Testing CSV data extraction...")
        tse_client = TSEClient()
        assets = tse_client._process_csv_asset_data(response.text)

        print(f"✅ Extracted {len(assets)} asset records")

        # Show sample data
        if assets:
            print("\n📊 Sample asset record:")
            sample_asset = assets[0]
            for key, value in list(sample_asset.items())[:5]:
                print(f"  {key}: {value}")
            if len(sample_asset) > 5:
                print(f"  ... and {len(sample_asset) - 5} more fields")

        return True

    except Exception as e:
        print(f"❌ Error processing CSV file: {e}")
        return False


def test_edge_cases():
    """Test edge cases in ZIP processing"""
    print("\n🚧 TESTING EDGE CASES")
    print("=" * 30)

    # Test with malformed ZIP
    print("🧪 Testing malformed ZIP data...")
    try:
        tse_client = TSEClient()
        malformed_data = b"this is not a zip file"
        assets = tse_client._process_zip_asset_data(malformed_data)
        print(f"✅ Handled malformed ZIP: {len(assets)} assets (expected 0)")
    except Exception as e:
        print(f"❌ Error with malformed ZIP: {e}")

    # Test with empty ZIP
    print("\n🧪 Testing empty ZIP...")
    try:
        # Create an empty ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            pass  # Create empty ZIP

        tse_client = TSEClient()
        assets = tse_client._process_zip_asset_data(zip_buffer.getvalue())
        print(f"✅ Handled empty ZIP: {len(assets)} assets (expected 0)")
    except Exception as e:
        print(f"❌ Error with empty ZIP: {e}")


if __name__ == "__main__":
    print("🔬 TSE ASSET ZIP PROCESSING TEST")
    print("=" * 50)

    success = test_zip_content_inspection()

    test_edge_cases()

    print("\n" + "=" * 50)
    if success:
        print("✅ ZIP PROCESSING TEST COMPLETED SUCCESSFULLY")
    else:
        print("❌ ZIP PROCESSING TEST FAILED")
    print("=" * 50)