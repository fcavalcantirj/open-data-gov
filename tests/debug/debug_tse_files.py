#!/usr/bin/env python3
"""
DEBUG SCRIPT: TSE File Structure Analysis
Actually examine what files are in TSE packages and their content
"""

import sys
import os
sys.path.append('/Users/fcavalcanti/dev/open-data-gov/src')

from clients.tse_client import TSEClient
import requests
import zipfile
import io
import csv


def debug_tse_package_structure():
    """Debug actual TSE package structure - don't guess!"""
    print("🔍 DEBUGGING ACTUAL TSE PACKAGE STRUCTURE")
    print("=" * 60)

    client = TSEClient()

    # Get 2022 finance packages
    try:
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

        # Examine each resource
        for i, resource in enumerate(resources):
            name = resource.get('name', 'Unknown')
            format_type = resource.get('format', 'Unknown')
            url = resource.get('url', '')

            print(f"\n   📄 Resource {i+1}: {name}")
            print(f"       Format: {format_type}")
            print(f"       URL: {url[:100]}...")

            # Try to download first few ZIP resources to see what's inside
            if format_type.lower() == 'zip' and i < 3:  # Only check first 3 ZIP files
                print(f"       🔍 Examining ZIP contents...")
                try:
                    # Download ZIP
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        # Examine ZIP contents
                        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                            files_in_zip = zf.namelist()
                            print(f"       📁 ZIP contains {len(files_in_zip)} files:")

                            for zip_file in files_in_zip[:5]:  # Show first 5 files
                                print(f"          - {zip_file}")

                                # Try to read CSV headers from first file
                                if zip_file.endswith(('.csv', '.txt')) and zip_file == files_in_zip[0]:
                                    print(f"          🔍 Examining CSV headers in: {zip_file}")

                                    with zf.open(zip_file) as csvfile:
                                        # Try to decode
                                        try:
                                            content = csvfile.read().decode('latin-1')
                                        except:
                                            try:
                                                content = csvfile.read().decode('utf-8')
                                            except:
                                                content = csvfile.read().decode('cp1252', errors='ignore')

                                        # Get first few lines
                                        lines = content.split('\n')
                                        if len(lines) > 0:
                                            # Try to parse header
                                            header_line = lines[0]
                                            if ';' in header_line:
                                                headers = header_line.split(';')
                                            elif ',' in header_line:
                                                headers = header_line.split(',')
                                            else:
                                                headers = [header_line]

                                            print(f"          📊 Headers ({len(headers)} fields):")
                                            for j, header in enumerate(headers[:10]):  # Show first 10
                                                print(f"             {j+1}. {header.strip()}")

                                            if len(headers) > 10:
                                                print(f"             ... and {len(headers)-10} more fields")

                                            # Show a sample record
                                            if len(lines) > 1 and lines[1].strip():
                                                sample_record = lines[1]
                                                if ';' in sample_record:
                                                    sample_values = sample_record.split(';')
                                                elif ',' in sample_record:
                                                    sample_values = sample_record.split(',')
                                                else:
                                                    sample_values = [sample_record]

                                                print(f"          📋 Sample record:")
                                                for k, (header, value) in enumerate(zip(headers[:5], sample_values[:5])):
                                                    print(f"             {header.strip()}: {value.strip()}")

                                                # Look for key financial fields
                                                financial_indicators = ['cpf', 'cnpj', 'valor', 'pagamento', 'receita', 'despesa', 'doador', 'fornecedor']
                                                found_financial = []
                                                for header in headers:
                                                    header_lower = header.lower()
                                                    for indicator in financial_indicators:
                                                        if indicator in header_lower:
                                                            found_financial.append(header)
                                                            break

                                                if found_financial:
                                                    print(f"          💰 Financial fields found: {found_financial[:5]}")
                                                else:
                                                    print(f"          ⚠️ No obvious financial fields found")

                            if len(files_in_zip) > 5:
                                print(f"          ... and {len(files_in_zip)-5} more files")

                    else:
                        print(f"       ❌ Failed to download: {response.status_code}")

                except Exception as e:
                    print(f"       ❌ Error examining ZIP: {e}")

            if i >= 2:  # Stop after examining first 3 resources
                print(f"\n   ... and {len(resources)-3} more resources")
                break

    except Exception as e:
        print(f"❌ Error debugging TSE structure: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run TSE structure debugging"""
    print("🚀 TSE PACKAGE STRUCTURE DEBUGGING")
    print("Let's see what's ACTUALLY in these files!")
    print("=" * 60)

    debug_tse_package_structure()

    print(f"\n✅ TSE STRUCTURE ANALYSIS COMPLETE")
    print(f"Now we know exactly what files contain what data!")


if __name__ == "__main__":
    main()