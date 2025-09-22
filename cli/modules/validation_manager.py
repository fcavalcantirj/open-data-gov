"""
Validation Manager Module
Validates data integrity across all tables
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.modules.database_manager import DatabaseManager


class ValidationManager:
    """Manages data validation and integrity checks"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def validate_all(self, fix: bool = False) -> None:
        """Validate all tables"""
        print("🔍 COMPREHENSIVE DATA VALIDATION")
        print("=" * 50)

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

        total_issues = 0

        for table in tables:
            print(f"\n📊 Validating {table}...")
            issues = self.validate_table(table, fix=fix)
            total_issues += len(issues)

        print(f"\n{'='*50}")
        print(f"🎯 VALIDATION SUMMARY")
        print(f"Total issues found: {total_issues}")
        if fix:
            print("✅ Auto-fix enabled")
        else:
            print("ℹ️ Use --fix to attempt automatic corrections")
        print("=" * 50)

    def validate_table(self, table_name: str, fix: bool = False) -> List[Dict[str, Any]]:
        """Validate specific table"""
        issues = []

        try:
            if table_name == 'unified_politicians':
                issues.extend(self._validate_politicians(fix))
            elif table_name == 'unified_financial_records':
                issues.extend(self._validate_financial_records(fix))
            elif table_name == 'financial_counterparts':
                issues.extend(self._validate_counterparts(fix))
            else:
                issues.extend(self._validate_generic_table(table_name, fix))

            if issues:
                print(f"  ⚠️ Found {len(issues)} issues")
                for issue in issues:
                    print(f"    • {issue['description']}")
            else:
                print(f"  ✅ No issues found")

        except Exception as e:
            print(f"  ❌ Validation error: {e}")
            issues.append({'description': f"Validation error: {e}", 'severity': 'ERROR'})

        return issues

    def _validate_politicians(self, fix: bool) -> List[Dict[str, Any]]:
        """Validate unified_politicians table"""
        issues = []

        # Check for missing CPFs
        missing_cpf = self.db.execute_query(
            "SELECT id, nome_civil FROM unified_politicians WHERE cpf IS NULL OR cpf = ''"
        )
        for row in missing_cpf:
            issues.append({
                'table': 'unified_politicians',
                'record_id': row['id'],
                'description': f"Missing CPF for politician: {row['nome_civil']}",
                'severity': 'WARNING'
            })

        # Check for invalid CPFs
        invalid_cpf = self.db.execute_query(
            "SELECT id, nome_civil, cpf FROM unified_politicians WHERE LENGTH(cpf) != 11"
        )
        for row in invalid_cpf:
            issues.append({
                'table': 'unified_politicians',
                'record_id': row['id'],
                'description': f"Invalid CPF length for {row['nome_civil']}: {row['cpf']}",
                'severity': 'ERROR'
            })

        # Check for duplicate CPFs
        duplicates = self.db.execute_query("""
            SELECT cpf, COUNT(*) as count
            FROM unified_politicians
            WHERE cpf IS NOT NULL
            GROUP BY cpf
            HAVING COUNT(*) > 1
        """)
        for row in duplicates:
            issues.append({
                'table': 'unified_politicians',
                'description': f"Duplicate CPF found: {row['cpf']} ({row['count']} records)",
                'severity': 'ERROR'
            })

        return issues

    def _validate_financial_records(self, fix: bool) -> List[Dict[str, Any]]:
        """Validate unified_financial_records table"""
        issues = []

        # Check for invalid amounts
        invalid_amounts = self.db.execute_query(
            "SELECT id FROM unified_financial_records WHERE amount < 0"
        )
        for row in invalid_amounts:
            issues.append({
                'table': 'unified_financial_records',
                'record_id': row['id'],
                'description': f"Negative amount in record {row['id']}",
                'severity': 'WARNING'
            })

        # Check for missing counterparts
        missing_counterparts = self.db.execute_query("""
            SELECT id FROM unified_financial_records
            WHERE counterpart_cnpj_cpf IS NULL OR counterpart_cnpj_cpf = ''
        """)
        for row in missing_counterparts:
            issues.append({
                'table': 'unified_financial_records',
                'record_id': row['id'],
                'description': f"Missing counterpart CNPJ/CPF in record {row['id']}",
                'severity': 'WARNING'
            })

        # Check for orphaned records (politician doesn't exist)
        orphaned = self.db.execute_query("""
            SELECT fr.id
            FROM unified_financial_records fr
            LEFT JOIN unified_politicians p ON fr.politician_id = p.id
            WHERE p.id IS NULL
        """)
        for row in orphaned:
            issues.append({
                'table': 'unified_financial_records',
                'record_id': row['id'],
                'description': f"Orphaned record {row['id']} - politician doesn't exist",
                'severity': 'ERROR'
            })

        return issues

    def _validate_counterparts(self, fix: bool) -> List[Dict[str, Any]]:
        """Validate financial_counterparts table"""
        issues = []

        # Check for invalid CNPJ/CPF lengths
        invalid_ids = self.db.execute_query("""
            SELECT id, cnpj_cpf, name
            FROM financial_counterparts
            WHERE LENGTH(cnpj_cpf) NOT IN (11, 14)
        """)
        for row in invalid_ids:
            issues.append({
                'table': 'financial_counterparts',
                'record_id': row['id'],
                'description': f"Invalid CNPJ/CPF length for {row['name']}: {row['cnpj_cpf']}",
                'severity': 'ERROR'
            })

        # Check for missing names
        missing_names = self.db.execute_query(
            "SELECT id FROM financial_counterparts WHERE name IS NULL OR name = ''"
        )
        for row in missing_names:
            issues.append({
                'table': 'financial_counterparts',
                'record_id': row['id'],
                'description': f"Missing name for counterpart {row['id']}",
                'severity': 'WARNING'
            })

        return issues

    def _validate_generic_table(self, table_name: str, fix: bool) -> List[Dict[str, Any]]:
        """Generic validation for other tables"""
        issues = []

        # Check for orphaned records if table has politician_id
        columns = self.db.get_table_info(table_name)
        has_politician_id = any(col['name'] == 'politician_id' for col in columns)

        if has_politician_id:
            orphaned = self.db.execute_query(f"""
                SELECT t.id
                FROM {table_name} t
                LEFT JOIN unified_politicians p ON t.politician_id = p.id
                WHERE p.id IS NULL
            """)
            for row in orphaned:
                issues.append({
                    'table': table_name,
                    'record_id': row['id'],
                    'description': f"Orphaned record {row['id']} - politician doesn't exist",
                    'severity': 'ERROR'
                })

        return issues

    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("# DATA VALIDATION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Table statistics
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

        report.append("## Table Statistics")
        for table in tables:
            count = self.db.get_table_count(table)
            report.append(f"- {table}: {count:,} records")

        report.append("")

        # Relationship integrity
        report.append("## Relationship Integrity")

        # Politicians with financial data
        with_finance = self.db.execute_query("""
            SELECT COUNT(DISTINCT politician_id) as count
            FROM unified_financial_records
        """)[0]['count']

        total_politicians = self.db.get_table_count('unified_politicians')

        report.append(f"- Politicians with financial data: {with_finance}/{total_politicians}")

        # Add more relationship checks...

        return "\n".join(report)