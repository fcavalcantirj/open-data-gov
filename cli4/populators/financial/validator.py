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
        """Validate financial_counterparts table - ALL FIELDS FROM DATA_POPULATION_GUIDE.md"""
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

        # Check ALL fields from DATA_POPULATION_GUIDE.md
        missing_cnpj_cpf = [c for c in counterparts if not c.get('cnpj_cpf')]
        missing_name = [c for c in counterparts if not c.get('name')]
        missing_normalized_name = [c for c in counterparts if not c.get('normalized_name')]
        missing_entity_type = [c for c in counterparts if not c.get('entity_type')]
        missing_total_amount = [c for c in counterparts if c.get('total_transaction_amount') is None]
        missing_transaction_count = [c for c in counterparts if c.get('transaction_count') is None]
        missing_first_transaction = [c for c in counterparts if not c.get('first_transaction_date')]
        missing_last_transaction = [c for c in counterparts if not c.get('last_transaction_date')]
        missing_created_at = [c for c in counterparts if not c.get('created_at')]
        missing_updated_at = [c for c in counterparts if not c.get('updated_at')]

        # Check CNPJ/CPF format validation
        invalid_cnpj_cpf = []
        wrong_entity_type = []
        for c in counterparts:
            cnpj_cpf = c.get('cnpj_cpf', '')
            entity_type = c.get('entity_type', '')
            if cnpj_cpf:
                if len(cnpj_cpf) not in [11, 14]:
                    invalid_cnpj_cpf.append(c)
                else:
                    expected_type = 'COMPANY' if len(cnpj_cpf) == 14 else 'INDIVIDUAL'
                    if entity_type not in [expected_type, 'UNKNOWN']:
                        wrong_entity_type.append(c)

        # Report issues (critical vs warning)
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

        # Report optional field completion - ONLY FIELDS FROM DATA_POPULATION_GUIDE.md
        if missing_normalized_name:
            issues.append(f"⚠️ {len(missing_normalized_name)} counterparts missing normalized_name")
        if missing_total_amount:
            issues.append(f"⚠️ {len(missing_total_amount)} counterparts missing total_transaction_amount")
        if missing_transaction_count:
            issues.append(f"⚠️ {len(missing_transaction_count)} counterparts missing transaction_count")
        if missing_first_transaction:
            issues.append(f"⚠️ {len(missing_first_transaction)} counterparts missing first_transaction_date")
        if missing_last_transaction:
            issues.append(f"⚠️ {len(missing_last_transaction)} counterparts missing last_transaction_date")
        if missing_created_at:
            issues.append(f"⚠️ {len(missing_created_at)} counterparts missing created_at")
        if missing_updated_at:
            issues.append(f"⚠️ {len(missing_updated_at)} counterparts missing updated_at")

        # Calculate completion rate based on ALL 11 documented fields from DATA_POPULATION_GUIDE.md
        all_fields = ['id', 'cnpj_cpf', 'name', 'normalized_name', 'entity_type',
                     'total_transaction_amount', 'transaction_count', 'first_transaction_date', 'last_transaction_date',
                     'created_at', 'updated_at']

        total_possible_fields = len(counterparts) * len(all_fields)
        valid_fields = 0

        for record in counterparts:
            for field in all_fields:
                if record.get(field) is not None:
                    valid_fields += 1

        completion_rate = (valid_fields / total_possible_fields) * 100 if total_possible_fields > 0 else 0

        self.validation_results['counterparts'] = {
            'total_records': total_records,
            'completion_rate': completion_rate,
            'total_fields_checked': len(all_fields),
            'issues': issues
        }

    def _validate_financial_records(self):
        """Validate unified_financial_records table - ALL 32 FIELDS FROM DATA_POPULATION_GUIDE.md"""
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

        # Check ALL 32 fields from DATA_POPULATION_GUIDE.md
        # Core identification fields
        missing_politician_id = [r for r in records if not r.get('politician_id')]
        missing_source_system = [r for r in records if not r.get('source_system')]
        missing_source_record_id = [r for r in records if not r.get('source_record_id')]
        missing_source_url = [r for r in records if not r.get('source_url')]

        # Transaction classification
        missing_transaction_type = [r for r in records if not r.get('transaction_type')]
        missing_transaction_category = [r for r in records if not r.get('transaction_category')]

        # Financial details
        missing_amount = [r for r in records if not r.get('amount')]
        missing_amount_net = [r for r in records if not r.get('amount_net')]
        missing_amount_rejected = [r for r in records if r.get('amount_rejected') is None]
        missing_original_amount = [r for r in records if not r.get('original_amount')]

        # Temporal details
        missing_transaction_date = [r for r in records if not r.get('transaction_date')]
        missing_year = [r for r in records if not r.get('year')]
        missing_month = [r for r in records if not r.get('month')]

        # Counterpart information
        missing_counterpart_name = [r for r in records if not r.get('counterpart_name')]
        missing_counterpart_cnpj_cpf = [r for r in records if not r.get('counterpart_cnpj_cpf')]
        missing_counterpart_type = [r for r in records if not r.get('counterpart_type')]

        # Geographic context
        missing_state = [r for r in records if not r.get('state')]
        missing_municipality = [r for r in records if not r.get('municipality')]

        # Document references
        missing_document_number = [r for r in records if not r.get('document_number')]
        missing_document_code = [r for r in records if not r.get('document_code')]
        missing_document_type = [r for r in records if not r.get('document_type')]
        missing_document_type_code = [r for r in records if not r.get('document_type_code')]
        missing_document_url = [r for r in records if not r.get('document_url')]

        # Processing details
        missing_lote_code = [r for r in records if not r.get('lote_code')]
        missing_installment = [r for r in records if not r.get('installment')]
        missing_reimbursement_number = [r for r in records if not r.get('reimbursement_number')]

        # Election context
        missing_election_year = [r for r in records if not r.get('election_year')]
        missing_election_round = [r for r in records if not r.get('election_round')]
        missing_election_date = [r for r in records if not r.get('election_date')]

        # Validation flags
        missing_cnpj_validated = [r for r in records if r.get('cnpj_validated') is None]
        missing_sanctions_checked = [r for r in records if r.get('sanctions_checked') is None]
        missing_external_validation_date = [r for r in records if not r.get('external_validation_date')]

        # Validation checks
        invalid_amounts = [r for r in records if r.get('amount') and float(r['amount']) <= 0]
        valid_sources = ['DEPUTADOS', 'TSE']
        invalid_sources = [r for r in records if r.get('source_system') and r['source_system'] not in valid_sources]
        valid_types = ['PARLIAMENTARY_EXPENSE', 'CAMPAIGN_DONATION', 'CAMPAIGN_EXPENSE']
        invalid_types = [r for r in records if r.get('transaction_type') and r['transaction_type'] not in valid_types]

        # Report critical issues
        if missing_politician_id:
            issues.append(f"❌ {len(missing_politician_id)} records missing politician_id")
        if missing_source_system:
            issues.append(f"❌ {len(missing_source_system)} records missing source_system")
        if missing_transaction_type:
            issues.append(f"❌ {len(missing_transaction_type)} records missing transaction_type")
        if missing_amount:
            issues.append(f"❌ {len(missing_amount)} records missing amount")
        if missing_transaction_date:
            issues.append(f"❌ {len(missing_transaction_date)} records missing transaction_date")
        if invalid_amounts:
            issues.append(f"⚠️ {len(invalid_amounts)} records with invalid amounts (≤0)")
        if invalid_sources:
            issues.append(f"⚠️ {len(invalid_sources)} records with invalid source_system")
        if invalid_types:
            issues.append(f"⚠️ {len(invalid_types)} records with invalid transaction_type")

        # Report optional field completion (sample - showing key ones)
        if missing_source_record_id:
            issues.append(f"⚠️ {len(missing_source_record_id)} records missing source_record_id")
        if missing_transaction_category:
            issues.append(f"⚠️ {len(missing_transaction_category)} records missing transaction_category")
        if missing_counterpart_name:
            issues.append(f"⚠️ {len(missing_counterpart_name)} records missing counterpart_name")
        if missing_document_code:
            issues.append(f"⚠️ {len(missing_document_code)} records missing document_code")

        # Calculate completion rate based on ALL 36 documented fields (INCLUDING NEW TSE FIELDS)
        all_fields = [
            'id', 'politician_id', 'source_system', 'source_record_id', 'source_url',
            'transaction_type', 'transaction_category', 'amount', 'amount_net',
            'amount_rejected', 'original_amount', 'transaction_date', 'year',
            'month', 'counterpart_name', 'counterpart_cnpj_cpf', 'counterpart_type',
            'counterpart_cnae', 'counterpart_business_type', 'state', 'municipality',
            'document_number', 'document_code', 'document_type', 'document_type_code',
            'document_url', 'lote_code', 'installment', 'reimbursement_number',
            'election_year', 'election_round', 'election_date', 'cnpj_validated',
            'sanctions_checked', 'external_validation_date', 'created_at', 'updated_at'
        ]

        total_possible_fields = len(records) * len(all_fields)
        valid_fields = 0

        for record in records:
            for field in all_fields:
                if record.get(field) is not None:
                    valid_fields += 1

        completion_rate = (valid_fields / total_possible_fields) * 100 if total_possible_fields > 0 else 0

        self.validation_results['financial_records'] = {
            'total_records': total_records,
            'completion_rate': completion_rate,
            'total_fields_checked': len(all_fields),
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