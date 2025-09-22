#!/usr/bin/env python3
"""
Asset Matching Investigation Script
Analyzes why CPF matching fails despite having 2M+ asset records
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
from src.clients.tse_client import TSEClient


def investigate_asset_matching():
    """Investigate why asset CPF matching is failing"""
    print("🔍 ASSET MATCHING INVESTIGATION")
    print("=" * 50)

    # Get politicians from database
    db = DatabaseManager()
    politicians = db.execute_query("SELECT id, cpf, nome_civil FROM unified_politicians LIMIT 3")

    print(f"📋 Found {len(politicians)} politicians in database:")
    for p in politicians:
        print(f"  - ID {p['id']}: {p['nome_civil']} (CPF: {p['cpf']})")

    # Get TSE asset data
    tse_client = TSEClient()

    print("\n🏦 Analyzing TSE asset data structure...")

    # Get a small sample of 2022 assets to examine structure
    print("Getting asset data sample from 2022...")
    assets_2022 = tse_client.get_asset_data(2022)

    if not assets_2022:
        print("❌ No asset data returned from 2022")
        return

    print(f"✅ Retrieved {len(assets_2022)} asset records from 2022")

    # Examine first few records to understand structure
    print("\n📊 ASSET DATA STRUCTURE ANALYSIS:")
    print("=" * 50)

    for i, asset in enumerate(assets_2022[:5]):
        print(f"\nAsset Record {i+1}:")
        print(f"  Keys: {list(asset.keys())}")

        # Look for CPF fields
        cpf_fields = [k for k in asset.keys() if 'cpf' in k.lower()]
        print(f"  CPF fields: {cpf_fields}")

        for field in cpf_fields:
            print(f"  {field}: {asset.get(field)}")

    # Test CPF matching with actual politician CPFs
    print("\n🔍 CPF MATCHING TEST:")
    print("=" * 50)

    for politician in politicians:
        pol_cpf = politician['cpf']
        clean_pol_cpf = ''.join(filter(str.isdigit, str(pol_cpf)))

        print(f"\n👤 Testing {politician['nome_civil']}:")
        print(f"  Database CPF: {pol_cpf}")
        print(f"  Clean CPF: {clean_pol_cpf}")

        matches = 0
        sample_matches = []

        # Check first 1000 records for matches
        for i, asset in enumerate(assets_2022[:1000]):
            # Try all possible CPF field names
            asset_cpf = (asset.get('nr_cpf_candidato') or
                        asset.get('NR_CPF_CANDIDATO') or
                        asset.get('CPF') or
                        asset.get('cpf') or
                        asset.get('nr_cpf') or
                        asset.get('NR_CPF'))

            if asset_cpf:
                clean_asset_cpf = ''.join(filter(str.isdigit, str(asset_cpf)))
                if clean_asset_cpf == clean_pol_cpf:
                    matches += 1
                    if len(sample_matches) < 3:
                        sample_matches.append(asset)

        print(f"  Matches in first 1000 records: {matches}")

        if sample_matches:
            print(f"  Sample match: {sample_matches[0]}")

    # Get unique CPF samples from asset data
    print("\n📝 ASSET CPF SAMPLES:")
    print("=" * 50)

    cpf_samples = set()
    for asset in assets_2022[:1000]:
        asset_cpf = (asset.get('nr_cpf_candidato') or
                    asset.get('NR_CPF_CANDIDATO') or
                    asset.get('CPF') or
                    asset.get('cpf') or
                    asset.get('nr_cpf') or
                    asset.get('NR_CPF'))

        if asset_cpf:
            cpf_samples.add(str(asset_cpf))
            if len(cpf_samples) >= 10:
                break

    print(f"Sample CPFs from asset data:")
    for cpf in list(cpf_samples)[:10]:
        print(f"  - {cpf}")

    # Check if politicians' CPFs exist in any form
    print("\n🔎 BROADER CPF SEARCH:")
    print("=" * 50)

    for politician in politicians:
        pol_cpf = politician['cpf']

        print(f"\n👤 Searching for {politician['nome_civil']} CPF variations:")
        print(f"  Target CPF: {pol_cpf}")

        # Try different CPF format variations
        variations = [
            pol_cpf,  # Original
            pol_cpf.replace('.', '').replace('-', ''),  # Digits only
            pol_cpf.zfill(11),  # Zero-padded
        ]

        for variation in variations:
            found = False
            for asset in assets_2022[:1000]:
                asset_cpf_raw = (asset.get('nr_cpf_candidato') or
                               asset.get('NR_CPF_CANDIDATO') or
                               asset.get('CPF') or
                               asset.get('cpf') or
                               asset.get('nr_cpf') or
                               asset.get('NR_CPF'))

                if asset_cpf_raw and str(asset_cpf_raw) == variation:
                    found = True
                    print(f"  ✅ Found match for variation '{variation}': {asset_cpf_raw}")
                    break

            if not found:
                print(f"  ❌ No match for variation: {variation}")


if __name__ == "__main__":
    investigate_asset_matching()