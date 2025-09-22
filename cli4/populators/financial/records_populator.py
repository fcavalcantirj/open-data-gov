"""
CLI4 Financial Records Populator
Populate unified_financial_records table (Phase 2b)
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from src.clients.tse_client import TSEClient


class CLI4RecordsPopulator:
    """Populate unified_financial_records table with all transactions"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.camara_base = "https://dadosabertos.camara.leg.br/api/v2"
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None,
                 start_year: Optional[int] = None,
                 end_year: Optional[int] = None) -> int:
        """Populate unified financial records table"""

        print("📊 UNIFIED FINANCIAL RECORDS POPULATION")
        print("=" * 50)
        print("Phase 2b: All financial transactions")
        print()

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = database.execute_query(
                "SELECT id, deputy_id, cpf FROM unified_politicians"
            )

        print(f"📋 Processing {len(politicians)} politicians")

        # Set date range
        if not start_year:
            start_year = 2019
        if not end_year:
            end_year = 2024

        print(f"📅 Date range: {start_year} - {end_year}")
        print()

        total_records = 0

        for i, politician in enumerate(politicians, 1):
            print(f"\n👤 [{i}/{len(politicians)}] Processing politician {politician['id']}")

            try:
                # PHASE 1: Deputados expenses
                deputados_records = self._process_deputados_expenses(
                    politician, start_year, end_year
                )

                # PHASE 2: TSE campaign finance
                tse_records = self._process_tse_finance(
                    politician, start_year, end_year
                )

                # PHASE 3: Bulk insert all records
                all_records = deputados_records + tse_records
                if all_records:
                    inserted = self._bulk_insert_records(all_records)
                    total_records += inserted
                    print(f"  ✅ Inserted {inserted} financial records")

                    self.logger.log_processing(
                        'financial_records', str(politician['id']), 'success',
                        {'deputados_count': len(deputados_records), 'tse_count': len(tse_records)}
                    )

            except Exception as e:
                print(f"  ❌ Error processing politician {politician['id']}: {e}")
                self.logger.log_processing(
                    'financial_records', str(politician['id']), 'error',
                    {'error': str(e)}
                )
                continue

        print(f"\n✅ Financial records population completed: {total_records} total records")
        return total_records

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict]:
        """Get politicians by specific IDs"""
        placeholders = ','.join(['%s'] * len(politician_ids))
        query = f"SELECT id, deputy_id, cpf FROM unified_politicians WHERE id IN ({placeholders})"
        return database.execute_query(query, tuple(politician_ids))

    def _process_deputados_expenses(self, politician: Dict, start_year: int,
                                   end_year: int) -> List[Dict]:
        """Process Deputados expenses for a politician"""
        records = []
        deputy_id = politician['deputy_id']
        politician_id = politician['id']

        for year in range(start_year, end_year + 1):
            wait_time = self.rate_limiter.wait_if_needed('camara')

            start_time = time.time()
            url = f"{self.camara_base}/deputados/{deputy_id}/despesas"
            params = {'ano': year, 'ordem': 'ASC', 'ordenarPor': 'mes'}

            try:
                response = requests.get(url, params=params, timeout=30)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    self.logger.log_api_call('camara', f'/deputados/{deputy_id}/despesas', 'success', response_time)

                    data = response.json()
                    expenses = data.get('dados', [])

                    print(f"    📄 {year}: {len(expenses)} expenses")

                    for expense in expenses:
                        record = self._build_deputados_record(politician_id, expense)
                        if record:
                            records.append(record)

                else:
                    self.logger.log_api_call('camara', f'/deputados/{deputy_id}/despesas', 'error', response_time)

            except Exception as e:
                print(f"    ⚠️ Error fetching {year} expenses: {e}")
                continue

        return records

    def _process_tse_finance(self, politician: Dict, start_year: int,
                            end_year: int) -> List[Dict]:
        """Process TSE campaign finance for a politician"""
        records = []
        politician_cpf = politician['cpf']
        politician_id = politician['id']

        if not politician_cpf:
            return records

        for year in range(start_year, end_year + 1):
            try:
                print(f"    🗳️ TSE {year}...")

                # Get TSE finance data
                finance_data = self.tse_client.get_finance_data(year)

                if finance_data:
                    year_records = 0
                    for record in finance_data:
                        candidate_cpf = record.get('nr_cpf_candidato') or record.get('cpf_candidato')

                        # Check if this record belongs to our politician
                        if candidate_cpf == politician_cpf:
                            financial_record = self._build_tse_record(politician_id, record, year)
                            if financial_record:
                                records.append(financial_record)
                                year_records += 1

                    if year_records > 0:
                        print(f"      ✅ Found {year_records} TSE records")

            except Exception as e:
                print(f"    ⚠️ Error processing TSE {year}: {e}")
                continue

        return records

    def _build_deputados_record(self, politician_id: int, expense: Dict) -> Optional[Dict]:
        """Build financial record from Deputados expense"""

        # Validate required fields
        if not expense.get('valorLiquido') or not expense.get('dataDocumento'):
            return None

        cnpj_cpf = expense.get('cnpjCpfFornecedor', '')
        cnpj_cpf_clean = ''.join(filter(str.isdigit, cnpj_cpf)) if cnpj_cpf else None

        return {
            'politician_id': politician_id,

            # SOURCE IDENTIFICATION
            'source_system': 'DEPUTADOS',
            'source_record_id': f"dep_exp_{expense.get('codDocumento')}",
            'source_url': expense.get('urlDocumento'),

            # TRANSACTION CLASSIFICATION
            'transaction_type': 'PARLIAMENTARY_EXPENSE',
            'transaction_category': expense.get('tipoDespesa'),

            # FINANCIAL DETAILS
            'amount': float(expense['valorLiquido']),
            'amount_net': float(expense.get('valorLiquido', 0)),
            'amount_rejected': float(expense.get('valorGlosa', 0)),
            'original_amount': float(expense.get('valorDocumento', 0)),

            # TEMPORAL DETAILS
            'transaction_date': expense['dataDocumento'],
            'year': int(expense.get('ano', 0)),
            'month': int(expense.get('mes', 0)),

            # COUNTERPART INFORMATION
            'counterpart_name': expense.get('nomeFornecedor'),
            'counterpart_cnpj_cpf': cnpj_cpf_clean,
            'counterpart_type': 'VENDOR',

            # DOCUMENT REFERENCES
            'document_number': expense.get('numDocumento'),
            'document_code': int(expense.get('codDocumento', 0)),
            'document_type': expense.get('tipoDocumento'),
            'document_type_code': int(expense.get('codTipoDocumento', 0)),
            'document_url': expense.get('urlDocumento'),

            # PROCESSING DETAILS
            'lote_code': int(expense.get('codLote', 0)) if expense.get('codLote') else None,
            'installment': int(expense.get('parcela', 0)) if expense.get('parcela') else None,
            'reimbursement_number': expense.get('numRessarcimento'),

            # ELECTION CONTEXT (None for Deputados records)
            'election_date': None,

            # VALIDATION FLAGS
            'cnpj_validated': False,
            'sanctions_checked': False,
            'external_validation_date': None
        }

    def _build_tse_record(self, politician_id: int, record: Dict, year: int) -> Optional[Dict]:
        """Build financial record from TSE campaign finance"""

        # Validate required fields
        amount = record.get('vr_receita') or record.get('valor_receita')
        if not amount:
            return None

        transaction_date = record.get('dt_receita') or record.get('data_receita')
        if not transaction_date:
            return None

        cnpj_cpf = record.get('nr_cpf_cnpj_doador') or record.get('cnpj_cpf_doador', '')
        cnpj_cpf_clean = ''.join(filter(str.isdigit, cnpj_cpf)) if cnpj_cpf else None

        return {
            'politician_id': politician_id,

            # SOURCE IDENTIFICATION
            'source_system': 'TSE',
            'source_record_id': f"tse_fin_{year}_{record.get('sq_receita', '')}",

            # TRANSACTION CLASSIFICATION
            'transaction_type': 'CAMPAIGN_DONATION',
            'transaction_category': record.get('ds_especie_receita') or record.get('descricao_receita'),

            # FINANCIAL DETAILS
            'amount': float(amount),
            'amount_net': float(amount),

            # TEMPORAL DETAILS
            'transaction_date': transaction_date,
            'year': year,

            # COUNTERPART INFORMATION
            'counterpart_name': record.get('nm_doador') or record.get('nome_doador'),
            'counterpart_cnpj_cpf': cnpj_cpf_clean,
            'counterpart_type': 'DONOR',

            # GEOGRAPHIC CONTEXT
            'state': record.get('sg_uf_doador'),
            'municipality': record.get('nm_municipio_doador'),

            # ELECTION CONTEXT
            'election_year': year,
            'election_round': int(record.get('nr_turno', 1)),
            'election_date': record.get('dt_eleicao'),

            # VALIDATION FLAGS
            'cnpj_validated': False,
            'sanctions_checked': False,
            'external_validation_date': None
        }

    def _bulk_insert_records(self, records: List[Dict]) -> int:
        """Bulk insert financial records"""

        if not records:
            return 0

        batch_size = 100
        inserted_count = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            try:
                # Build bulk insert query - ALL SCHEMA FIELDS INCLUDED
                fields = [
                    'politician_id', 'source_system', 'source_record_id', 'source_url',
                    'transaction_type', 'transaction_category', 'amount', 'amount_net',
                    'amount_rejected', 'original_amount', 'transaction_date', 'year',
                    'month', 'counterpart_name', 'counterpart_cnpj_cpf', 'counterpart_type',
                    'state', 'municipality', 'document_number', 'document_code',
                    'document_type', 'document_type_code', 'document_url', 'lote_code',
                    'installment', 'reimbursement_number', 'election_year', 'election_round',
                    'election_date', 'cnpj_validated', 'sanctions_checked', 'external_validation_date'
                ]

                placeholders = ', '.join(['%s'] * len(fields))
                fields_str = ', '.join(fields)

                query = f"""
                    INSERT INTO unified_financial_records ({fields_str})
                    VALUES ({placeholders})
                    RETURNING id
                """

                # Prepare values
                values = []
                for record in batch:
                    record_values = []
                    for field in fields:
                        value = record.get(field)
                        # Handle None values and type conversions
                        if value is None:
                            record_values.append(None)
                        elif field in ['amount', 'amount_net', 'amount_rejected', 'original_amount']:
                            record_values.append(float(value) if value else 0.0)
                        elif field in ['year', 'month', 'document_code', 'document_type_code',
                                     'lote_code', 'installment', 'election_year', 'election_round']:
                            record_values.append(int(value) if value else None)
                        elif field in ['cnpj_validated', 'sanctions_checked']:
                            record_values.append(bool(value))
                        elif field in ['transaction_date', 'election_date', 'external_validation_date']:
                            record_values.append(value)  # Already DATE type
                        else:
                            record_values.append(value)
                    values.append(tuple(record_values))

                # Execute batch
                results = database.execute_batch_returning(query, values)
                inserted_count += len(results)

            except Exception as e:
                print(f"    ❌ Error in batch {i//batch_size + 1}: {e}")
                continue

        return inserted_count