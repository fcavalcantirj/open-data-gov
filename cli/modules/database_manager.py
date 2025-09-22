"""
Database Manager Module
Handles database connections, schema initialization, and basic operations
Supports both SQLite (local) and PostgreSQL (production)
"""

import sqlite3
import psycopg2
import psycopg2.extras
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse


class DatabaseManager:
    """
    Manages database operations for the political transparency platform
    Supports both SQLite (local) and PostgreSQL (production)
    """

    def __init__(self, db_path: str = "political_transparency.db"):
        self.project_root = Path(__file__).parent.parent.parent

        # Check for PostgreSQL URL in environment
        self.postgres_url = os.getenv('POSTGRES_POOL_URL')

        if self.postgres_url:
            print(f"🐘 Using PostgreSQL database")
            self.db_type = 'postgresql'
            self.db_path = None
        else:
            print(f"📁 Using SQLite database: {db_path}")
            self.db_type = 'sqlite'
            self.db_path = db_path

    def get_connection(self):
        """Get database connection with proper configuration"""
        if self.db_type == 'postgresql':
            conn = psycopg2.connect(self.postgres_url)
            # Use RealDictCursor for column access by name
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            return conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            return conn

    def initialize_database(self, force: bool = False) -> None:
        """
        Initialize database by running the appropriate setup script

        Args:
            force: If True, recreate database even if it exists
        """
        if self.db_type == 'postgresql':
            # For PostgreSQL, always try to create tables (using IF NOT EXISTS)
            setup_script_path = self.project_root / "setup_postgres.py"
            print("🐘 Initializing PostgreSQL database...")
        else:
            # For SQLite, check if file exists
            if os.path.exists(self.db_path) and not force:
                print(f"Database {self.db_path} already exists. Use --force to recreate.")
                return
            setup_script_path = self.project_root / "setup_database.py"

        if not setup_script_path.exists():
            raise FileNotFoundError(f"Setup script not found at {setup_script_path}")

        # Execute the setup script
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(setup_script_path)],
            cwd=str(self.project_root),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"Database setup failed: {result.stderr}")

        print("Database initialized successfully")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[dict]:
        """
        Execute a SELECT query and return results

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of query results as dictionaries
        """
        # Convert SQLite ? placeholders to PostgreSQL %s if needed
        if self.db_type == 'postgresql' and query.count('?') > 0:
            query = query.replace('?', '%s')

        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()

            # Convert to list of dicts for consistency
            if self.db_type == 'postgresql':
                return [dict(row) for row in results]
            else:
                return [dict(row) for row in results]

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        # Convert SQLite ? placeholders to PostgreSQL %s if needed
        if self.db_type == 'postgresql' and query.count('?') > 0:
            query = query.replace('?', '%s')

        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute many operations in a single transaction

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of affected rows
        """
        # Convert SQLite ? placeholders to PostgreSQL %s if needed
        if self.db_type == 'postgresql' and query.count('?') > 0:
            query = query.replace('?', '%s')

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table"""
        if self.db_type == 'postgresql':
            query = """
                SELECT column_name as name, data_type as type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (table_name,))
                columns = cursor.fetchall()
                return [dict(col) for col in columns]
        else:
            query = f"PRAGMA table_info({table_name})"
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                columns = cursor.fetchall()
                return [dict(col) for col in columns]

    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0

    def show_status(self, detailed: bool = False) -> None:
        """
        Show database status and statistics

        Args:
            detailed: If True, show detailed statistics
        """
        tables = [
            'unified_politicians',
            'unified_financial_records',
            'financial_counterparts',
            'unified_political_networks',
            'unified_wealth_tracking',
            'politician_career_history',
            'politician_events',
            'politician_assets',
            'politician_professional_background'
        ]

        print("📊 DATABASE STATUS REPORT")
        print("=" * 50)
        if self.db_type == 'postgresql':
            print(f"Database: PostgreSQL ({self.postgres_url.split('@')[-1].split('/')[0] if '@' in self.postgres_url else 'remote'})")
        else:
            print(f"Database: {os.path.abspath(self.db_path)}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        total_records = 0

        for table in tables:
            try:
                count = self.get_table_count(table)
                total_records += count
                status = "✅" if count > 0 else "⚪"
                print(f"{status} {table:35} {count:>8,} records")

                if detailed and count > 0:
                    self._show_table_details(table)

            except Exception as e:
                print(f"❌ {table:35} ERROR: {e}")

        print("=" * 50)
        print(f"📈 TOTAL RECORDS: {total_records:,}")

        # Database file size (SQLite only)
        if self.db_type == 'sqlite' and os.path.exists(self.db_path):
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            print(f"💾 DATABASE SIZE: {size_mb:.2f} MB")

    def _show_table_details(self, table_name: str) -> None:
        """Show detailed statistics for a table"""
        try:
            if table_name == 'unified_politicians':
                # Politicians statistics
                if self.db_type == 'postgresql':
                    active_count = self.execute_query(
                        "SELECT COUNT(*) as count FROM unified_politicians WHERE deputy_active = true"
                    )[0]['count']
                else:
                    active_count = self.execute_query(
                        "SELECT COUNT(*) as count FROM unified_politicians WHERE deputy_active = 1"
                    )[0]['count']

                if self.db_type == 'postgresql':
                    with_tse = self.execute_query(
                        "SELECT COUNT(*) as count FROM unified_politicians WHERE tse_linked = true"
                    )[0]['count']
                else:
                    with_tse = self.execute_query(
                        "SELECT COUNT(*) as count FROM unified_politicians WHERE tse_linked = 1"
                    )[0]['count']

                print(f"    → Active deputies: {active_count}")
                print(f"    → TSE linked: {with_tse}")

            elif table_name == 'unified_financial_records':
                # Financial statistics
                total_amount = self.execute_query(
                    "SELECT SUM(amount) as total FROM unified_financial_records"
                )[0]['total'] or 0

                by_type = self.execute_query("""
                    SELECT transaction_type, COUNT(*) as count, SUM(amount) as total
                    FROM unified_financial_records
                    GROUP BY transaction_type
                """)

                print(f"    → Total amount: R$ {total_amount:,.2f}")
                for row in by_type:
                    print(f"    → {row['transaction_type']}: {row['count']} ({row['total']:,.2f})")

            elif table_name == 'financial_counterparts':
                # Counterparts statistics
                by_type = self.execute_query("""
                    SELECT entity_type, COUNT(*) as count
                    FROM financial_counterparts
                    GROUP BY entity_type
                """)

                for row in by_type:
                    print(f"    → {row['entity_type']}: {row['count']}")

        except Exception as e:
            print(f"    ⚠️ Error getting details: {e}")

    def get_politicians_for_processing(self, limit: Optional[int] = None,
                                     start_id: Optional[int] = None,
                                     active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get politicians for batch processing

        Args:
            limit: Maximum number to return
            start_id: Start from specific politician ID
            active_only: Only return active deputies

        Returns:
            List of politician records for processing
        """
        query = "SELECT id, cpf, deputy_id, nome_civil FROM unified_politicians WHERE 1=1"
        params = []

        if active_only:
            if self.db_type == 'postgresql':
                query += " AND deputy_active = true"
            else:
                query += " AND deputy_active = 1"

        if start_id:
            query += " AND id >= ?"
            params.append(start_id)

        query += " ORDER BY id"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        results = self.execute_query(query, tuple(params) if params else None)
        return [dict(row) for row in results]

    def check_politician_exists(self, cpf: str) -> Optional[int]:
        """
        Check if politician already exists by CPF

        Args:
            cpf: Politician CPF

        Returns:
            Politician ID if exists, None otherwise
        """
        query = "SELECT id FROM unified_politicians WHERE cpf = ?"
        result = self.execute_query(query, (cpf,))
        return result[0]['id'] if result else None

    def get_financial_counterpart_id(self, cnpj_cpf: str) -> Optional[int]:
        """
        Get financial counterpart ID by CNPJ/CPF

        Args:
            cnpj_cpf: CNPJ or CPF identifier

        Returns:
            Counterpart ID if exists, None otherwise
        """
        query = "SELECT id FROM financial_counterparts WHERE cnpj_cpf = ?"
        result = self.execute_query(query, (cnpj_cpf,))
        return result[0]['id'] if result else None

    def bulk_insert_records(self, table_name: str, records: List[Dict[str, Any]]) -> int:
        """
        Bulk insert records into a table

        Args:
            table_name: Target table name
            records: List of record dictionaries

        Returns:
            Number of inserted records
        """
        if not records:
            return 0

        # Get column names from first record
        columns = list(records[0].keys())

        # Use database-specific placeholders
        if self.db_type == 'postgresql':
            placeholders = ', '.join(['%s' for _ in columns])
        else:
            placeholders = ', '.join(['?' for _ in columns])

        column_names = ', '.join(columns)

        query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

        # Convert records to tuples
        values = [tuple(record.get(col) for col in columns) for record in records]

        return self.execute_many(query, values)

    def vacuum_database(self) -> None:
        """Optimize database by running VACUUM"""
        if self.db_type == 'postgresql':
            with self.get_connection() as conn:
                conn.execute("VACUUM ANALYZE")
                conn.commit()
        else:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
        print("Database optimized successfully")

    def clear_all_data(self) -> None:
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

        print("🗑️  Clearing tables in dependency order...")
        cleared_count = 0

        # Use transaction for atomic clearing
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Clear tables in dependency order (no foreign key modifications needed)
                for table in tables_in_dependency_order:
                    try:
                        # Check if table has data
                        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                        count_result = cursor.fetchone()
                        if self.db_type == 'postgresql':
                            record_count = count_result['count'] if count_result else 0
                        else:
                            record_count = count_result['count'] if count_result else 0

                        if record_count > 0:
                            # Use DELETE FROM for both databases (compatible with all permission levels)
                            cursor.execute(f"DELETE FROM {table}")
                            print(f"  ✅ Cleared {table}: {record_count} records deleted")
                            cleared_count += record_count
                        else:
                            print(f"  ⭕ {table}: Already empty")

                    except Exception as e:
                        print(f"  ❌ Error clearing {table}: {e}")
                        # Continue with other tables even if one fails
                        continue

                conn.commit()
                print(f"\n🎯 Total records cleared: {cleared_count}")

            except Exception as e:
                conn.rollback()
                print(f"\n❌ Error during database clearing: {e}")
                raise

    def get_all_politician_ids(self) -> List[int]:
        """Get all politician IDs from the database"""
        query = "SELECT id FROM unified_politicians ORDER BY id"
        result = self.execute_query(query)
        return [row['id'] for row in result]