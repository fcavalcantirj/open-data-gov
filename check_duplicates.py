#!/usr/bin/env python3
"""
Check for duplicate records that might be causing high counts
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

from cli.modules.database_manager import DatabaseManager

def main():
    db = DatabaseManager()

    print('🔍 ANALYZING HIGH RECORD COUNTS')
    print('=' * 50)

    # Check political networks - 25,675 records seems high for 95 politicians
    print('📊 Top 5 politicians by network records:')
    networks = db.execute_query('''
        SELECT politician_id, COUNT(*) as count
        FROM unified_political_networks
        GROUP BY politician_id
        ORDER BY count DESC LIMIT 5
    ''')

    for record in networks:
        politician = db.execute_query('SELECT nome_civil FROM unified_politicians WHERE id = %s', (record['politician_id'],))
        name = politician[0]['nome_civil'] if politician else 'Unknown'
        print(f'  {name}: {record["count"]} networks')

    print()

    # Check financial records - 13,433 records for 95 politicians
    print('💰 Top 5 politicians by financial records:')
    financial = db.execute_query('''
        SELECT politician_id, COUNT(*) as count
        FROM unified_financial_records
        GROUP BY politician_id
        ORDER BY count DESC LIMIT 5
    ''')

    for record in financial:
        politician = db.execute_query('SELECT nome_civil FROM unified_politicians WHERE id = %s', (record['politician_id'],))
        name = politician[0]['nome_civil'] if politician else 'Unknown'
        print(f'  {name}: {record["count"]} financial records')

    print()

    # Check for potential duplicates
    print('🔍 Checking for potential duplicates...')

    # Network duplicates
    network_dupes = db.execute_query('''
        SELECT politician_id, network_type, network_id, COUNT(*) as count
        FROM unified_political_networks
        GROUP BY politician_id, network_type, network_id
        HAVING COUNT(*) > 1
        LIMIT 3
    ''')
    print(f'Network duplicates found: {len(network_dupes)}')
    for dupe in network_dupes:
        print(f'  Politician {dupe["politician_id"]}: {dupe["count"]} copies of {dupe["network_type"]} {dupe["network_id"]}')

    # Financial duplicates
    financial_dupes = db.execute_query('''
        SELECT politician_id, transaction_type, amount, description, COUNT(*) as count
        FROM unified_financial_records
        GROUP BY politician_id, transaction_type, amount, description
        HAVING COUNT(*) > 1
        LIMIT 3
    ''')
    print(f'Financial duplicates found: {len(financial_dupes)}')
    for dupe in financial_dupes:
        print(f'  Politician {dupe["politician_id"]}: {dupe["count"]} copies of {dupe["transaction_type"]} R${dupe["amount"]}')

    print()

    # Calculate averages
    print('📈 AVERAGES:')
    networks_avg = 25675 / 95
    financial_avg = 13433 / 95
    print(f'  Networks per politician: {networks_avg:.1f}')
    print(f'  Financial records per politician: {financial_avg:.1f}')

    # Brazilian politicians often participate in many parliamentary fronts
    # Financial records span 5 years (2020-2024), so 141 records per politician is reasonable

if __name__ == "__main__":
    main()