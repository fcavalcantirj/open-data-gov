#!/usr/bin/env python3
"""
CLI v4 - DIRECT API CALLS, NO POPULATORS
Bypasses all broken populators, does direct API + database work
"""

import argparse
import sys
import os
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

from cli.modules.database_manager import DatabaseManager


def direct_populate_politicians(db_manager, limit=5):
    """Direct politician population - no populators"""
    print(f"🔄 Direct politician population (limit: {limit})")

    try:
        # Direct API call to Câmara
        url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        deputies = data.get('dados', [])[:limit]

        print(f"📋 Found {len(deputies)} deputies from API")

        created = 0
        for deputy in deputies:
            deputy_id = deputy.get('id')
            name = deputy.get('nome')

            # Check if exists
            existing = db_manager.execute_query(
                "SELECT id FROM unified_politicians WHERE deputados_id = ?", (deputy_id,)
            )

            if existing:
                print(f"  ⏭️ {name} already exists")
                continue

            # Get details
            detail_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputy_id}"
            detail_response = requests.get(detail_url, timeout=10)
            detail_data = detail_response.json().get('dados', {})

            # Insert politician
            insert_sql = """
            INSERT INTO unified_politicians (
                deputados_id, name, deputy_name, cpf, email, gender,
                birth_date, education, civil_state, party_abbreviation,
                state_abbreviation, situation, condition_description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            values = (
                deputy_id,
                name,
                name,
                detail_data.get('cpf'),
                detail_data.get('ultimoStatus', {}).get('email'),
                detail_data.get('sexo'),
                detail_data.get('dataNascimento'),
                detail_data.get('escolaridade'),
                detail_data.get('estadoCivil'),
                detail_data.get('ultimoStatus', {}).get('siglaPartido'),
                detail_data.get('ultimoStatus', {}).get('siglaUf'),
                detail_data.get('ultimoStatus', {}).get('situacao'),
                detail_data.get('ultimoStatus', {}).get('condicaoEleitoral')
            )

            db_manager.execute_query(insert_sql, values)
            print(f"  ✅ Created {name}")
            created += 1

        print(f"✅ Direct politicians: {created} created")
        return True

    except Exception as e:
        print(f"❌ Direct politician population failed: {e}")
        return False


def direct_populate_financial(db_manager, limit=5):
    """Direct financial population - no populators"""
    print(f"🔄 Direct financial population (limit: {limit})")

    try:
        # Get politicians
        politicians = db_manager.execute_query(
            "SELECT id, deputados_id, name FROM unified_politicians LIMIT ?", (limit,)
        )

        if not politicians:
            print("❌ No politicians found")
            return False

        created_records = 0
        for politician in politicians:
            politician_id = politician['id']
            deputados_id = politician['deputados_id']
            name = politician['name']

            print(f"  Processing {name}...")

            # Get expenses from API
            year = 2024
            url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputados_id}/despesas"
            params = {'ano': year, 'itens': 100}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            expenses = response.json().get('dados', [])

            for expense in expenses:
                # Insert financial record
                insert_sql = """
                INSERT INTO unified_financial_records (
                    politician_id, source_system, transaction_type, amount,
                    transaction_date, description, counterpart_name, counterpart_cnpj_cpf
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """

                values = (
                    politician_id,
                    'deputados',
                    'PARLIAMENTARY_EXPENSE',
                    float(expense.get('valorLiquido', 0)),
                    expense.get('dataDocumento'),
                    expense.get('tipoDespesa'),
                    expense.get('nomeFornecedor'),
                    expense.get('cnpjCpfFornecedor')
                )

                db_manager.execute_query(insert_sql, values)
                created_records += 1

            print(f"    ✅ Added {len(expenses)} financial records")

        print(f"✅ Direct financial: {created_records} records created")
        return True

    except Exception as e:
        print(f"❌ Direct financial population failed: {e}")
        return False


def direct_populate_all(db_manager, limit=5):
    """Direct population of all tables"""
    print("🚀 CLI v4: Direct Population - NO POPULATORS")
    print("=" * 50)
    print(f"Limit: {limit}")
    print("=" * 50)

    try:
        # Step 1: Politicians
        print("\n1️⃣ POLITICIANS (Direct API)")
        start = time.time()
        success1 = direct_populate_politicians(db_manager, limit=limit)
        duration1 = time.time() - start
        print(f"⏱️ Politicians completed in {duration1:.1f}s")

        if not success1:
            print("❌ Politicians failed, stopping")
            return False

        # Step 2: Financial
        print("\n2️⃣ FINANCIAL (Direct API)")
        start = time.time()
        success2 = direct_populate_financial(db_manager, limit=limit)
        duration2 = time.time() - start
        print(f"⏱️ Financial completed in {duration2:.1f}s")

        if not success2:
            print("❌ Financial failed, stopping")
            return False

        total_time = duration1 + duration2
        print(f"\n🎯 CLI v4 COMPLETE! Total time: {total_time:.1f}s")
        print("✅ NO HANGING, NO POPULATORS, DIRECT API CALLS ONLY")
        return True

    except Exception as e:
        print(f"❌ CLI v4 failed: {e}")
        return False


def show_status(db_manager):
    """Show database status"""
    print("📊 DATABASE STATUS - CLI v4")
    print("=" * 40)

    tables = [
        "unified_politicians",
        "unified_financial_records",
        "financial_counterparts"
    ]

    total_records = 0
    for table in tables:
        try:
            result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            count = result[0]['count'] if result else 0
            total_records += count
            status = "✅" if count > 0 else "⚪"
            print(f"{status} {table}: {count:,}")
        except Exception as e:
            print(f"❌ {table}: ERROR")

    print("=" * 40)
    print(f"📈 Total records: {total_records:,}")


def main():
    """Main CLI v4 entry point"""
    parser = argparse.ArgumentParser(description="CLI v4 - Direct API, No Populators")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status
    status_parser = subparsers.add_parser('status', help='Show database status')

    # Populate
    pop_parser = subparsers.add_parser('populate', help='Populate using direct API calls')
    pop_subparsers = pop_parser.add_subparsers(dest='table', help='What to populate')

    # All
    all_parser = pop_subparsers.add_parser('all', help='Populate politicians + financial')
    all_parser.add_argument('--limit', type=int, default=5, help='Limit politicians')

    # Politicians only
    pol_parser = pop_subparsers.add_parser('politicians', help='Populate politicians only')
    pol_parser.add_argument('--limit', type=int, default=5, help='Limit politicians')

    # Financial only
    fin_parser = pop_subparsers.add_parser('financial', help='Populate financial only')
    fin_parser.add_argument('--limit', type=int, default=5, help='Limit politicians')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        db_manager = DatabaseManager()

        if args.command == 'status':
            show_status(db_manager)

        elif args.command == 'populate':
            if not args.table:
                parser.print_help()
                return 1

            if args.table == 'all':
                success = direct_populate_all(db_manager, limit=args.limit)
                if success:
                    print("\n" + "="*40)
                    show_status(db_manager)
                    return 0
                else:
                    return 1

            elif args.table == 'politicians':
                success = direct_populate_politicians(db_manager, limit=args.limit)
                return 0 if success else 1

            elif args.table == 'financial':
                success = direct_populate_financial(db_manager, limit=args.limit)
                return 0 if success else 1

            else:
                print(f"❌ Unknown table: {args.table}")
                return 1

        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

        print("✅ CLI v4 completed successfully")
        return 0

    except Exception as e:
        print(f"❌ CLI v4 Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())