#!/usr/bin/env python3
"""
COMPREHENSIVE TSE FILE ANALYSIS
Examine ALL TSE financial file types to understand their structure
"""

import requests
import zipfile
import io
import csv
import os
from pathlib import Path


def examine_local_data():
    """Examine the downloaded TSE data first"""
    print("🔍 EXAMINING LOCAL TSE DATA")
    print("=" * 50)

    local_path = "/Users/fcavalcanti/Downloads/prestacao_de_contas_eleitorais_candidatos_2022"

    if os.path.exists(local_path):
        print(f"📁 Found local data at: {local_path}")

        # List all files
        files = list(Path(local_path).rglob("*.csv"))
        print(f"📄 Found {len(files)} CSV files")

        # Group by file type
        file_types = {}
        for file_path in files:
            filename = file_path.name
            if 'receitas' in filename:
                file_type = 'receitas'
            elif 'despesas_pagas' in filename:
                file_type = 'despesas_pagas'
            elif 'despesas_contratadas' in filename:
                file_type = 'despesas_contratadas'
            elif 'doador_originario' in filename:
                file_type = 'doador_originario'
            else:
                file_type = 'other'

            if file_type not in file_types:
                file_types[file_type] = []
            file_types[file_type].append(file_path)

        print(f"\n📊 FILE TYPE BREAKDOWN:")
        for file_type, files in file_types.items():
            print(f"   {file_type}: {len(files)} files")

        # Examine one file from each type
        for file_type, files in file_types.items():
            if files:
                examine_csv_file(files[0], file_type)
    else:
        print(f"❌ Local data not found at: {local_path}")


def examine_csv_file(file_path, file_type):
    """Examine a specific CSV file"""
    print(f"\n🔍 EXAMINING {file_type.upper()} FILE:")
    print(f"   📄 {file_path.name}")

    try:
        # Try different encodings
        content = None
        encoding_used = None
        for encoding in ['latin-1', 'utf-8', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read(50000)  # First 50KB
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue

        if not content:
            print("   ❌ Could not decode file")
            return

        print(f"   ✅ Decoded with: {encoding_used}")

        # Parse header
        lines = content.split('\n')
        if len(lines) > 0:
            header_line = lines[0]

            # Remove quotes and detect delimiter
            if header_line.startswith('"'):
                headers = [h.strip('"') for h in header_line.split('","')]
            else:
                delimiter = ';' if ';' in header_line else ','
                headers = header_line.split(delimiter)

            print(f"   📊 {len(headers)} fields:")

            # Show all headers with numbers
            for i, header in enumerate(headers):
                print(f"      {i+1:2d}. {header.strip()}")

            # Show sample record
            if len(lines) > 1 and lines[1].strip():
                sample_line = lines[1]
                if sample_line.startswith('"'):
                    sample_values = [v.strip('"') for v in sample_line.split('","')]
                else:
                    delimiter = ';' if ';' in sample_line else ','
                    sample_values = sample_line.split(delimiter)

                print(f"\n   📋 SAMPLE RECORD:")
                for i, (header, value) in enumerate(zip(headers[:10], sample_values[:10])):
                    print(f"      {header.strip()}: {value.strip()}")

                if len(headers) > 10:
                    print(f"      ... and {len(headers)-10} more fields")

            # Analyze key fields for this type
            analyze_fields_for_type(headers, file_type)

    except Exception as e:
        print(f"   ❌ Error: {e}")


def analyze_fields_for_type(headers, file_type):
    """Analyze fields specific to each file type"""
    print(f"\n   💰 {file_type.upper()} FIELD ANALYSIS:")

    # Common fields
    common_patterns = {
        'cpf_candidate': ['NR_CPF_CANDIDATO', 'CPF_CANDIDATO'],
        'candidate_name': ['NM_CANDIDATO', 'NOME_CANDIDATO'],
        'candidate_id': ['SQ_CANDIDATO', 'SEQUENCIAL_CANDIDATO']
    }

    # Type-specific patterns
    type_patterns = {
        'receitas': {
            'amount': ['VR_RECEITA', 'VALOR_RECEITA'],
            'donor_cpf_cnpj': ['NR_CPF_CNPJ_DOADOR', 'CNPJ_CPF_DOADOR'],
            'donor_name': ['NM_DOADOR', 'NOME_DOADOR'],
            'receipt_date': ['DT_RECEITA', 'DATA_RECEITA']
        },
        'despesas_pagas': {
            'amount': ['VR_PAGAMENTO', 'VALOR_PAGAMENTO', 'VR_DESPESA_PAGA'],
            'vendor_cpf_cnpj': ['NR_CPF_CNPJ_FORNECEDOR', 'CNPJ_CPF_FORNECEDOR'],
            'vendor_name': ['NM_FORNECEDOR', 'NOME_FORNECEDOR'],
            'payment_date': ['DT_PAGAMENTO', 'DATA_PAGAMENTO']
        },
        'despesas_contratadas': {
            'amount': ['VR_DESPESA_CONTRATADA', 'VALOR_DESPESA', 'VR_DESPESA'],
            'vendor_cpf_cnpj': ['NR_CPF_CNPJ_FORNECEDOR', 'CNPJ_CPF_FORNECEDOR'],
            'vendor_name': ['NM_FORNECEDOR', 'NOME_FORNECEDOR'],
            'contract_date': ['DT_DESPESA', 'DATA_DESPESA']
        },
        'doador_originario': {
            'amount': ['VR_RECEITA', 'VALOR_RECEITA'],
            'original_donor_cpf_cnpj': ['NR_CPF_CNPJ_DOADOR_ORIGINARIO'],
            'original_donor_name': ['NM_DOADOR_ORIGINARIO'],
            'cnae_code': ['CD_CNAE_DOADOR_ORIGINARIO']
        }
    }

    # Combine patterns
    all_patterns = {**common_patterns, **type_patterns.get(file_type, {})}

    found_fields = {}
    for field_purpose, possible_names in all_patterns.items():
        for possible_name in possible_names:
            if possible_name in headers:
                found_fields[field_purpose] = possible_name
                break

    # Report findings
    if found_fields:
        print("      ✅ FOUND KEY FIELDS:")
        for purpose, field_name in found_fields.items():
            print(f"         {purpose}: {field_name}")

    # Report missing critical fields
    missing_fields = []
    for purpose, possible_names in all_patterns.items():
        if purpose not in found_fields:
            missing_fields.append(f"{purpose} (looking for: {', '.join(possible_names)})")

    if missing_fields:
        print("      ❌ MISSING FIELDS:")
        for missing in missing_fields:
            print(f"         {missing}")

    # Special check for amount fields
    amount_fields = [h for h in headers if 'VR_' in h or 'VALOR' in h.upper()]
    if amount_fields:
        print(f"      💵 ALL AMOUNT FIELDS: {amount_fields}")


def examine_remote_tse_files():
    """Examine all file types from remote TSE"""
    print(f"\n🌐 EXAMINING REMOTE TSE FILES")
    print("=" * 50)

    # Different file types to examine
    urls_to_examine = [
        ("receitas", "https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2022.zip"),
    ]

    for file_type, url in urls_to_examine:
        examine_remote_zip(file_type, url)


def examine_remote_zip(context, url):
    """Examine specific remote ZIP file"""
    print(f"\n📥 DOWNLOADING {context.upper()} DATA")
    print(f"   URL: {url}")

    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        print(f"   ✅ Downloaded {len(response.content) / (1024*1024):.1f} MB")

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            files = zf.namelist()

            # Group files by type
            file_groups = {}
            for filename in files:
                if 'receitas' in filename:
                    group = 'receitas'
                elif 'despesas_pagas' in filename:
                    group = 'despesas_pagas'
                elif 'despesas_contratadas' in filename:
                    group = 'despesas_contratadas'
                elif 'doador_originario' in filename:
                    group = 'doador_originario'
                else:
                    group = 'other'

                if group not in file_groups:
                    file_groups[group] = []
                file_groups[group].append(filename)

            print(f"   📊 FILE BREAKDOWN:")
            for group, files in file_groups.items():
                print(f"      {group}: {len(files)} files")

            # Examine one file from each group
            for group, files in file_groups.items():
                if files and group != 'other':
                    # Take first file from group
                    filename = files[0]
                    print(f"\n   🔍 EXAMINING {group.upper()}: {filename}")

                    with zf.open(filename) as csvfile:
                        chunk = csvfile.read(20000)  # First 20KB

                        # Decode
                        content = None
                        for encoding in ['latin-1', 'utf-8', 'cp1252']:
                            try:
                                content = chunk.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue

                        if content:
                            lines = content.split('\n')
                            if lines:
                                header_line = lines[0]

                                # Parse headers
                                if header_line.startswith('"'):
                                    headers = [h.strip('"') for h in header_line.split('","')]
                                else:
                                    delimiter = ';' if ';' in header_line else ','
                                    headers = header_line.split(delimiter)

                                print(f"      📊 {len(headers)} fields")

                                # Analyze for this specific type
                                analyze_fields_for_type(headers, group)
                        else:
                            print(f"      ❌ Could not decode {filename}")

    except Exception as e:
        print(f"   ❌ Error: {e}")


def main():
    """Run comprehensive TSE analysis"""
    print("🚀 COMPREHENSIVE TSE FINANCIAL DATA ANALYSIS")
    print("Examining ALL file types to understand structure")
    print("=" * 70)

    # First examine local data if available
    examine_local_data()

    # Then examine remote data for completeness
    examine_remote_tse_files()

    print(f"\n✅ COMPREHENSIVE ANALYSIS COMPLETE")
    print("Now we know exactly what fields each file type has!")


if __name__ == "__main__":
    main()