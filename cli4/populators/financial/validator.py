"""
CLI4 Financial Validator
Validate financial_counterparts and unified_financial_records tables
"""

from typing import Dict, List, Any
from cli4.modules import database


class CLI4FinancialValidator:
    """Comprehensive financial data validation"""

    def __init__(self):
        self.validation_results = {
            'counterparts': {},
            'financial_records': {},
            'referential_integrity': {},
            'summary': {},
            'compliance_score': 0.0
        }

    def validate_all_financial(self) -> Dict[str, Any]:
        """Run comprehensive validation on financial tables"""
        print("🔍 COMPREHENSIVE FINANCIAL VALIDATION")
        print("=" * 60)
        print("Validating financial_counterparts + unified_financial_records")
        print("=" * 60)

        # Validate counterparts table
        self._validate_counterparts()

        # Validate financial records table
        self._validate_financial_records()

        # Validate referential integrity
        self._validate_referential_integrity()

        # Calculate compliance score
        self._calculate_compliance_score()

        # Print results
        self._print_validation_summary()

        return self.validation_results

    def _validate_counterparts(self):
        """Validate financial_counterparts table"""
        print("📊 Validating financial_counterparts table...")

        # Get counterparts data
        counterparts = database.execute_query("SELECT * FROM financial_counterparts")

        if not counterparts:
            self.validation_results['counterparts'] = {
                'total_records': 0,
                'issues': ['❌ No counterparts found in database'],
                'completion_rate': 0
            }
            return

        issues = []
        total_records = len(counterparts)

        # Check required fields
        missing_cnpj_cpf = [c for c in counterparts if not c.get('cnpj_cpf')]
        missing_name = [c for c in counterparts if not c.get('name')]
        missing_entity_type = [c for c in counterparts if not c.get('entity_type')]

        # Check CNPJ/CPF format
        invalid_cnpj_cpf = []
        for c in counterparts:
            cnpj_cpf = c.get('cnpj_cpf', '')
            if cnpj_cpf and len(cnpj_cpf) not in [11, 14]:
                invalid_cnpj_cpf.append(c)

        # Check entity type classification
        wrong_entity_type = []
        for c in counterparts:
            cnpj_cpf = c.get('cnpj_cpf', '')
            entity_type = c.get('entity_type', '')
            if cnpj_cpf:
                expected_type = 'COMPANY' if len(cnpj_cpf) == 14 else 'INDIVIDUAL'
                if entity_type not in [expected_type, 'UNKNOWN'] and len(cnpj_cpf) in [11, 14]:
                    wrong_entity_type.append(c)

        # Report issues
        if missing_cnpj_cpf:
            issues.append(f"❌ {len(missing_cnpj_cpf)} counterparts missing CNPJ/CPF")
        if missing_name:
            issues.append(f"❌ {len(missing_name)} counterparts missing name")
        if missing_entity_type:
            issues.append(f"❌ {len(missing_entity_type)} counterparts missing entity_type")
        if invalid_cnpj_cpf:
            issues.append(f"⚠️ {len(invalid_cnpj_cpf)} counterparts with invalid CNPJ/CPF format")
        if wrong_entity_type:
            issues.append(f"⚠️ {len(wrong_entity_type)} counterparts with wrong entity_type")

        # Calculate completion rate
        required_fields = ['cnpj_cpf', 'name', 'entity_type']
        valid_records = 0
        for record in counterparts:
            if all(record.get(field) for field in required_fields):
                valid_records += 1

        completion_rate = (valid_records / total_records) * 100 if total_records > 0 else 0

        self.validation_results['counterparts'] = {
            'total_records': total_records,
            'valid_records': valid_records,
            'completion_rate': completion_rate,
            'issues': issues
        }

    def _validate_financial_records(self):
        """Validate unified_financial_records table"""
        print("📊 Validating unified_financial_records table...")

        # Get financial records data
        records = database.execute_query("SELECT * FROM unified_financial_records")

        if not records:
            self.validation_results['financial_records'] = {
                'total_records': 0,
                'issues': ['❌ No financial records found in database'],
                'completion_rate': 0
            }
            return

        issues = []
        total_records = len(records)

        # Check required fields
        missing_politician_id = [r for r in records if not r.get('politician_id')]
        missing_amount = [r for r in records if not r.get('amount')]
        missing_transaction_date = [r for r in records if not r.get('transaction_date')]
        missing_source_system = [r for r in records if not r.get('source_system')]

        # Check amount validity
        invalid_amounts = [r for r in records if r.get('amount') and float(r['amount']) <= 0]

        # Check source system values
        valid_sources = ['DEPUTADOS', 'TSE']
        invalid_sources = [r for r in records if r.get('source_system') and r['source_system'] not in valid_sources]

        # Check transaction types
        valid_types = ['PARLIAMENTARY_EXPENSE', 'CAMPAIGN_DONATION', 'CAMPAIGN_EXPENSE']
        invalid_types = [r for r in records if r.get('transaction_type') and r['transaction_type'] not in valid_types]

        # Report issues
        if missing_politician_id:
            issues.append(f"❌ {len(missing_politician_id)} records missing politician_id")
        if missing_amount:
            issues.append(f"❌ {len(missing_amount)} records missing amount")
        if missing_transaction_date:
            issues.append(f"❌ {len(missing_transaction_date)} records missing transaction_date")
        if missing_source_system:
            issues.append(f"❌ {len(missing_source_system)} records missing source_system")
        if invalid_amounts:
            issues.append(f"⚠️ {len(invalid_amounts)} records with invalid amounts (≤0)")
        if invalid_sources:
            issues.append(f"⚠️ {len(invalid_sources)} records with invalid source_system")
        if invalid_types:
            issues.append(f"⚠️ {len(invalid_types)} records with invalid transaction_type")

        # Calculate completion rate
        required_fields = ['politician_id', 'amount', 'transaction_date', 'source_system']
        valid_records = 0
        for record in records:
            if all(record.get(field) for field in required_fields):
                if record.get('amount') and float(record['amount']) > 0:
                    valid_records += 1

        completion_rate = (valid_records / total_records) * 100 if total_records > 0 else 0

        self.validation_results['financial_records'] = {
            'total_records': total_records,
            'valid_records': valid_records,
            'completion_rate': completion_rate,
            'issues': issues
        }

    def _validate_referential_integrity(self):
        """Validate referential integrity between tables"""
        print("📊 Validating referential integrity...")

        issues = []

        # Check politician_id references
        orphaned_records = database.execute_query("""
            SELECT COUNT(*) as count
            FROM unified_financial_records fr
            LEFT JOIN unified_politicians p ON fr.politician_id = p.id
            WHERE p.id IS NULL
        """)

        if orphaned_records and orphaned_records[0]['count'] > 0:
            issues.append(f"❌ {orphaned_records[0]['count']} financial records with invalid politician_id")

        # Check counterpart correlation
        missing_counterparts = database.execute_query("""
            SELECT COUNT(DISTINCT fr.counterpart_cnpj_cpf) as count
            FROM unified_financial_records fr
            LEFT JOIN financial_counterparts fc ON fr.counterpart_cnpj_cpf = fc.cnpj_cpf
            WHERE fr.counterpart_cnpj_cpf IS NOT NULL
            AND fc.cnpj_cpf IS NULL
        """)

        if missing_counterparts and missing_counterparts[0]['count'] > 0:
            issues.append(f"⚠️ {missing_counterparts[0]['count']} counterparts in records but not in counterparts table")

        # Calculate referential integrity score
        total_records = self.validation_results.get('financial_records', {}).get('total_records', 0)
        orphaned_count = orphaned_records[0]['count'] if orphaned_records else 0

        integrity_score = ((total_records - orphaned_count) / total_records * 100) if total_records > 0 else 100

        self.validation_results['referential_integrity'] = {
            'integrity_score': integrity_score,
            'issues': issues
        }

    def _calculate_compliance_score(self):
        """Calculate overall compliance score"""
        scores = []

        # Counterparts score
        counterparts_score = self.validation_results.get('counterparts', {}).get('completion_rate', 0)
        scores.append(counterparts_score * 0.3)  # 30% weight

        # Financial records score
        records_score = self.validation_results.get('financial_records', {}).get('completion_rate', 0)
        scores.append(records_score * 0.5)  # 50% weight

        # Referential integrity score
        integrity_score = self.validation_results.get('referential_integrity', {}).get('integrity_score', 0)
        scores.append(integrity_score * 0.2)  # 20% weight

        self.validation_results['compliance_score'] = sum(scores)

    def _print_validation_summary(self):
        """Print comprehensive validation summary"""
        print(f"\n📊 FINANCIAL VALIDATION SUMMARY")
        print("=" * 60)

        # Counterparts summary
        counterparts = self.validation_results.get('counterparts', {})
        if counterparts:
            print(f"💰 Financial Counterparts: {counterparts.get('completion_rate', 0):.1f}%")
            print(f"   📊 {counterparts.get('total_records', 0)} total records")
            for issue in counterparts.get('issues', []):
                print(f"   {issue}")

        # Financial records summary
        records = self.validation_results.get('financial_records', {})
        if records:
            print(f"📄 Financial Records: {records.get('completion_rate', 0):.1f}%")
            print(f"   📊 {records.get('total_records', 0)} total records")
            for issue in records.get('issues', []):
                print(f"   {issue}")

        # Referential integrity summary
        integrity = self.validation_results.get('referential_integrity', {})
        if integrity:
            print(f"🔗 Referential Integrity: {integrity.get('integrity_score', 0):.1f}%")
            for issue in integrity.get('issues', []):
                print(f"   {issue}")

        print("=" * 60)
        print(f"🎯 OVERALL COMPLIANCE SCORE: {self.validation_results['compliance_score']:.1f}%")

        compliance_score = self.validation_results['compliance_score']
        if compliance_score >= 90:
            print("🏆 EXCELLENT - Financial data quality")
        elif compliance_score >= 70:
            print("👍 GOOD - Minor improvements needed")
        else:
            print("⚠️ NEEDS IMPROVEMENT - Significant data quality issues")

        print("=" * 60)