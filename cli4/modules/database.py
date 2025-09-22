"""
CLI4 Database Module
Simple PostgreSQL database functions - no unnecessary "manager" class
"""

import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
from datetime import datetime


def get_connection():
    """Get PostgreSQL connection"""
    postgres_url = os.getenv('POSTGRES_POOL_URL')

    if not postgres_url:
        raise Exception("🚨 POSTGRES_POOL_URL required in .env file")

    conn = psycopg2.connect(postgres_url)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def check_database():
    """Check if database is initialized"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'unified_politicians'
                )
            """)
            result = cursor.fetchone()
            table_exists = result['exists'] if result else False

        if table_exists:
            print("✅ Database ready - unified_politicians table exists")
            return True
        else:
            print("⚠️  Database not initialized. Run: python setup_postgres.py")
            return False

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure POSTGRES_POOL_URL is set and PostgreSQL is running")
        raise


def execute_query(query: str, params: Optional[tuple] = None) -> List[dict]:
    """Execute SELECT query"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        return [dict(row) for row in results]


def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """Execute INSERT/UPDATE/DELETE query"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.rowcount


def execute_insert_returning(query: str, params: Optional[tuple] = None) -> List[dict]:
    """Execute INSERT query with RETURNING clause"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        conn.commit()
        return [dict(row) for row in results]


def get_table_count(table_name: str) -> int:
    """Get row count for table"""
    result = execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
    return result[0]['count'] if result else 0


def show_status():
    """Show database status"""
    print("📊 CLI4 DATABASE STATUS")
    print("=" * 50)
    print(f"Database: PostgreSQL")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        total_politicians = get_table_count('unified_politicians')
        print(f"👥 Politicians: {total_politicians:,} records")

        if total_politicians > 0:
            # Active deputies
            active_count = execute_query(
                "SELECT COUNT(*) as count FROM unified_politicians WHERE deputy_active = true"
            )[0]['count']

            tse_linked = execute_query(
                "SELECT COUNT(*) as count FROM unified_politicians WHERE tse_linked = true"
            )[0]['count']

            print(f"  ✅ Active deputies: {active_count}")
            print(f"  🔗 TSE linked: {tse_linked}")

    except Exception as e:
        print(f"❌ Error getting status: {e}")

    print("=" * 50)


def clear_politicians():
    """Clear politicians table"""
    affected = execute_update("DELETE FROM unified_politicians")
    print(f"Cleared {affected} politicians from database")


def clear_all_data():
    """Clear all data from all tables in dependency order"""
    tables_in_dependency_order = [
        'unified_financial_records',
        'financial_counterparts',
        'unified_political_networks',
        'politician_career_history',
        'politician_professional_background',
        'politician_events',
        'politician_assets',
        'unified_wealth_tracking',
        'unified_politicians'
    ]

    total_cleared = 0
    for table in tables_in_dependency_order:
        try:
            affected = execute_update(f"DELETE FROM {table}")
            if affected > 0:
                print(f"  📋 {table}: {affected} records")
            total_cleared += affected
        except Exception as e:
            print(f"  ⚠️ {table}: {e}")

    print(f"Cleared {total_cleared} total records from all tables")


def validate_politicians() -> Dict[str, Any]:
    """Basic validation of politicians table"""
    issues = []

    # Check for missing CPFs
    missing_cpf = execute_query(
        "SELECT id, nome_civil FROM unified_politicians WHERE cpf IS NULL OR cpf = ''"
    )
    if missing_cpf:
        issues.append({
            'type': 'missing_cpf',
            'description': f'{len(missing_cpf)} politicians missing CPF',
            'count': len(missing_cpf)
        })

    # Check CPF length
    invalid_cpf = execute_query(
        "SELECT id, cpf FROM unified_politicians WHERE LENGTH(cpf) != 11"
    )
    if invalid_cpf:
        issues.append({
            'type': 'invalid_cpf',
            'description': f'{len(invalid_cpf)} politicians with invalid CPF length',
            'count': len(invalid_cpf)
        })

    # Check TSE correlation rate
    total_count = get_table_count('unified_politicians')
    if total_count > 0:
        tse_count = execute_query(
            "SELECT COUNT(*) as count FROM unified_politicians WHERE tse_linked = true"
        )[0]['count']

        correlation_rate = (tse_count / total_count) * 100
        if correlation_rate < 80:
            issues.append({
                'type': 'low_tse_correlation',
                'description': f'TSE correlation: {correlation_rate:.1f}% (expected >80%)',
                'count': total_count - tse_count
            })

    return {
        'total_issues': len(issues),
        'issues': issues,
        'validation_date': datetime.now().isoformat()
    }