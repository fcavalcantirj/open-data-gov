#!/usr/bin/env python3
"""
SIMPLE TEST: Download and examine ONE TSE financial file
No guessing - just look at actual data
"""

import requests
import zipfile
import io
import csv


def examine_specific_tse_file():
    """Download and examine one specific TSE file"""
    print("🔍 EXAMINING ONE SPECIFIC TSE FINANCIAL FILE")
    print("=" * 50)

    # Let's examine the candidate finance file from 2022
    # This should contain actual financial transactions
    url = "https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2022.zip"

    print(f"📥 Downloading: {url}")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        print(f"✅ Downloaded {len(response.content) / (1024*1024):.1f} MB")

        # Examine ZIP contents
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            files = zf.namelist()
            print(f"📁 ZIP contains {len(files)} files:")

            for filename in files[:10]:  # Show first 10 files
                print(f"   - {filename}")

            # Pick first CSV/TXT file to examine
            for filename in files:
                if filename.endswith(('.csv', '.txt')):
                    print(f"\n🔍 EXAMINING FILE: {filename}")

                    with zf.open(filename) as csvfile:
                        # Read first chunk
                        chunk = csvfile.read(10000)  # First 10KB

                        # Try different encodings
                        content = None
                        for encoding in ['latin-1', 'utf-8', 'cp1252']:
                            try:
                                content = chunk.decode(encoding)
                                print(f"✅ Decoded with: {encoding}")
                                break
                            except UnicodeDecodeError:
                                continue

                        if not content:
                            print("❌ Could not decode file")
                            continue

                        # Parse header and first few lines
                        lines = content.split('\n')
                        if len(lines) > 0:
                            header_line = lines[0]

                            # Detect delimiter
                            delimiter = ';' if ';' in header_line else ','
                            headers = header_line.split(delimiter)

                            print(f"📊 HEADERS ({len(headers)} fields, delimiter='{delimiter}'):")
                            for i, header in enumerate(headers):
                                print(f"   {i+1:2d}. {header.strip()}")

                            # Show sample record
                            if len(lines) > 1 and lines[1].strip():
                                sample_line = lines[1]
                                sample_values = sample_line.split(delimiter)

                                print(f"\n📋 SAMPLE RECORD:")
                                for header, value in zip(headers[:10], sample_values[:10]):
                                    print(f"   {header.strip()}: {value.strip()}")

                                if len(headers) > 10:
                                    print(f"   ... and {len(headers)-10} more fields")

                            # Look for key financial indicators
                            print(f"\n💰 FINANCIAL FIELD ANALYSIS:")
                            financial_keywords = ['cpf', 'cnpj', 'valor', 'pagamento', 'receita', 'despesa', 'doador', 'fornecedor']
                            found_financial = []

                            for header in headers:
                                header_lower = header.lower()
                                for keyword in financial_keywords:
                                    if keyword in header_lower:
                                        found_financial.append(f"{header} (contains '{keyword}')")

                            if found_financial:
                                print("   ✅ Found financial fields:")
                                for field in found_financial:
                                    print(f"      - {field}")
                            else:
                                print("   ❌ No obvious financial fields found")

                            # Check if this looks like metadata vs transaction data
                            has_amounts = any('valor' in h.lower() or 'vr_' in h.lower() for h in headers)
                            has_cpfs = any('cpf' in h.lower() for h in headers)
                            has_cnpjs = any('cnpj' in h.lower() for h in headers)

                            print(f"\n🔬 DATA TYPE ANALYSIS:")
                            print(f"   Has amounts: {has_amounts}")
                            print(f"   Has CPFs: {has_cpfs}")
                            print(f"   Has CNPJs: {has_cnpjs}")

                            if has_amounts and (has_cpfs or has_cnpjs):
                                print("   ✅ LOOKS LIKE TRANSACTION DATA")
                            else:
                                print("   ⚠️ LOOKS LIKE METADATA/HEADER DATA")

                    # Only examine first CSV file
                    break

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run the examination"""
    examine_specific_tse_file()


if __name__ == "__main__":
    main()