#!/usr/bin/env python3
"""
CLI v4 FINAL - FROM SCRATCH, NO HANGING
Creates tables and populates from zero, direct API calls only
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


def create_tables_v4(db_manager):
    """Create essential tables from scratch"""
    print("🔧 Creating tables...")

    # Politicians table
    politicians_sql = """
    CREATE TABLE IF NOT EXISTS unified_politicians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deputy_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        cpf TEXT,
        email TEXT,
        party TEXT,
        state TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    # Financial records table
    financial_sql = """
    CREATE TABLE IF NOT EXISTS unified_financial_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        politician_id INTEGER,
        amount REAL,
        description TEXT,
        supplier_name TEXT,
        supplier_cnpj TEXT,
        date_document TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (politician_id) REFERENCES unified_politicians (id)
    )
    """

    try:
        db_manager.execute_query(politicians_sql)
        db_manager.execute_query(financial_sql)
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def populate_politicians_v4(db_manager, limit=5):
    """Populate politicians from scratch"""
    print(f"👥 Populating {limit} politicians...")

    try:
        # Fetch from Câmara API
        url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
        print(f"🌐 Fetching from: {url}")

        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()
        deputies = data.get('dados', [])[:limit]

        print(f"📋 Found {len(deputies)} deputies")

        created = 0
        for deputy in deputies:
            deputy_id = deputy.get('id')
            name = deputy.get('nome', 'Unknown')

            print(f"  Processing: {name}")

            # Check if exists
            existing = db_manager.execute_query(
                "SELECT id FROM unified_politicians WHERE deputy_id = ?", (deputy_id,)
            )

            if existing:
                print(f"    ⏭️ Already exists")
                continue

            # Get detailed info
            detail_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputy_id}"
            detail_response = requests.get(detail_url, timeout=10)

            if detail_response.status_code == 200:
                detail_data = detail_response.json().get('dados', {})
                email = detail_data.get('ultimoStatus', {}).get('email', '')
                party = detail_data.get('ultimoStatus', {}).get('siglaPartido', '')
                state = detail_data.get('ultimoStatus', {}).get('siglaUf', '')
                cpf = detail_data.get('cpf', '')
            else:
                email = party = state = cpf = ''

            # Insert politician
            insert_sql = """
            INSERT INTO unified_politicians (deputy_id, name, cpf, email, party, state)
            VALUES (?, ?, ?, ?, ?, ?)
            """

            db_manager.execute_query(insert_sql, (deputy_id, name, cpf, email, party, state))
            print(f"    ✅ Created")
            created += 1

        print(f"✅ Politicians: {created} created")
        return True

    except Exception as e:
        print(f"❌ Failed to populate politicians: {e}")
        return False


def populate_financial_v4(db_manager, limit=5):
    """Populate financial records from scratch"""
    print(f"💰 Populating financial records...")

    try:
        # Get politicians
        politicians = db_manager.execute_query(
            "SELECT id, deputy_id, name FROM unified_politicians LIMIT ?", (limit,)
        )

        if not politicians:
            print("❌ No politicians found")
            return False

        total_records = 0

        for politician in politicians:
            politician_id = politician['id']
            deputy_id = politician['deputy_id']
            name = politician['name']

            print(f"  Processing {name}...")

            # Get expenses from API
            year = 2024
            url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputy_id}/despesas"
            params = {'ano': year, 'itens': 50}  # Limit to 50 to avoid hanging

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"    ⚠️ Failed to get expenses")
                continue

            expenses = response.json().get('dados', [])

            for expense in expenses:
                amount = float(expense.get('valorLiquido', 0))
                description = expense.get('tipoDespesa', '')
                supplier_name = expense.get('nomeFornecedor', '')
                supplier_cnpj = expense.get('cnpjCpfFornecedor', '')
                date_document = expense.get('dataDocumento', '')

                insert_sql = """
                INSERT INTO unified_financial_records
                (politician_id, amount, description, supplier_name, supplier_cnpj, date_document)
                VALUES (?, ?, ?, ?, ?, ?)
                """

                db_manager.execute_query(insert_sql, (
                    politician_id, amount, description, supplier_name, supplier_cnpj, date_document
                ))

            print(f"    ✅ Added {len(expenses)} records")
            total_records += len(expenses)

        print(f"✅ Financial: {total_records} records created")
        return True

    except Exception as e:
        print(f"❌ Failed to populate financial: {e}")
        return False


def show_status_v4(db_manager):
    """Show database status"""
    print("\n📊 DATABASE STATUS")
    print("=" * 40)

    try:
        # Politicians
        pol_result = db_manager.execute_query("SELECT COUNT(*) as count FROM unified_politicians")
        pol_count = pol_result[0]['count'] if pol_result else 0

        # Financial
        fin_result = db_manager.execute_query("SELECT COUNT(*) as count FROM unified_financial_records")
        fin_count = fin_result[0]['count'] if fin_result else 0

        # Financial sum
        sum_result = db_manager.execute_query("SELECT SUM(amount) as total FROM unified_financial_records")
        total_amount = sum_result[0]['total'] if sum_result and sum_result[0]['total'] else 0

        pol_status = "✅" if pol_count > 0 else "⚪"
        fin_status = "✅" if fin_count > 0 else "⚪"

        print(f"{pol_status} Politicians: {pol_count:,}")
        print(f"{fin_status} Financial records: {fin_count:,}")
        print(f"💰 Total amount: R$ {total_amount:,.2f}")

        total_records = pol_count + fin_count
        print("=" * 40)
        print(f"📈 Total records: {total_records:,}")

        if total_records > 0:
            print("🎉 Database is working!")
        else:
            print("⚪ Database is empty")

    except Exception as e:
        print(f"❌ Status check failed: {e}")


def populate_all_v4(db_manager, limit=5):
    """Complete population workflow"""
    print("🚀 CLI v4 FINAL - FROM SCRATCH POPULATION")
    print("=" * 50)
    print(f"Target: {limit} politicians + their financial data")
    print("=" * 50)

    start_total = time.time()

    try:
        # Step 1: Create tables
        print("\n1️⃣ SETUP")
        if not create_tables_v4(db_manager):
            return False

        # Step 2: Politicians
        print("\n2️⃣ POLITICIANS")
        start = time.time()
        if not populate_politicians_v4(db_manager, limit=limit):
            return False
        duration = time.time() - start
        print(f"⏱️ Politicians completed in {duration:.1f}s")

        # Step 3: Financial
        print("\n3️⃣ FINANCIAL")
        start = time.time()
        if not populate_financial_v4(db_manager, limit=limit):
            return False
        duration = time.time() - start
        print(f"⏱️ Financial completed in {duration:.1f}s")

        total_duration = time.time() - start_total
        print(f"\n🎯 CLI v4 COMPLETE!")
        print(f"⏱️ Total time: {total_duration:.1f}s")
        print("✅ NO POPULATORS, NO HANGING, DIRECT API ONLY")

        return True

    except Exception as e:
        print(f"❌ Population failed: {e}")
        return False


def main():
    """CLI v4 main entry point"""
    parser = argparse.ArgumentParser(description="CLI v4 Final - From Scratch, No Hanging")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status
    status_parser = subparsers.add_parser('status', help='Show database status')

    # Populate
    pop_parser = subparsers.add_parser('populate', help='Populate from scratch')
    pop_subparsers = pop_parser.add_subparsers(dest='table', help='What to populate')

    # All
    all_parser = pop_subparsers.add_parser('all', help='Populate everything from scratch')
    all_parser.add_argument('--limit', type=int, default=5, help='Number of politicians')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        db_manager = DatabaseManager()

        if args.command == 'status':
            show_status_v4(db_manager)

        elif args.command == 'populate':
            if not args.table:
                parser.print_help()
                return 1

            if args.table == 'all':
                success = populate_all_v4(db_manager, limit=args.limit)
                if success:
                    show_status_v4(db_manager)
                    return 0
                else:
                    return 1
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