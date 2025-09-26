"""
CLI4 Financial Records Populator
Populate unified_financial_records table (Phase 2b)
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, date
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.modules.dependency_checker import DependencyChecker
from src.clients.tse_client import TSEClient


class CLI4RecordsPopulator:
    """Populate unified_financial_records table with all transactions"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.camara_base = "https://dadosabertos.camara.leg.br/api/v2"
        self.tse_client = TSEClient()

    def _parse_brazilian_float(self, value) -> float:
        """Parse Brazilian formatted numbers (comma as decimal separator)"""
        if not value:
            return 0.0

        # Convert to string if not already
        str_value = str(value).strip()
        if not str_value:
            return 0.0

        try:
            # Handle Brazilian format: 1.234.567,89 or 6100,00
            # Replace comma with dot for decimal separator
            if ',' in str_value:
                # Check if comma is decimal separator (no dots after comma)
                comma_parts = str_value.split(',')
                if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                    # This is decimal separator, replace with dot
                    str_value = str_value.replace('.', '').replace(',', '.')

            return float(str_value)
        except (ValueError, TypeError):
            print(f"    ⚠️ Error parsing amount '{value}', using 0.0")
            return 0.0

    def _parse_brazilian_date(self, date_str) -> Optional[date]:
        """Parse Brazilian date format DD/MM/YYYY to PostgreSQL date"""
        if not date_str:
            return None

        try:
            date_str = str(date_str).strip()
            if not date_str or date_str in ['#NULO#', '', 'NULL']:
                return None

            # Handle Brazilian date format: DD/MM/YYYY
            if '/' in date_str and len(date_str) == 10:
                day, month, year = date_str.split('/')
                return date(int(year), int(month), int(day))

            # Handle ISO format: YYYY-MM-DD (already correct)
            elif '-' in date_str and len(date_str) == 10:
                year, month, day = date_str.split('-')
                return date(int(year), int(month), int(day))

            return None
        except (ValueError, TypeError, AttributeError):
            print(f"    ⚠️ Error parsing date '{date_str}', using NULL")
            return None

    def populate(self, politician_ids: Optional[List[int]] = None,
                 start_year: Optional[int] = None,
                 end_year: Optional[int] = None) -> int:
        """Populate unified financial records table"""

        print("📊 UNIFIED FINANCIAL RECORDS POPULATION")
        print("=" * 50)
        print("Phase 2b: All financial transactions")
        print()

        # Check dependencies
        DependencyChecker.print_dependency_warning(
            required_steps=["politicians"],
            current_step="FINANCIAL RECORDS POPULATION"
        )

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

        # Log initial system state
        self.logger.log_system_checkpoint("Financial processing start")

        total_records = 0

        for i, politician in enumerate(politicians, 1):
            print(f"\n👤 [{i}/{len(politicians)}] Processing politician {politician['id']}")

            try:
                # PHASE 1: Deputados expenses
                deputados_records = self._process_deputados_expenses(
                    politician, start_year, end_year
                )

                # PHASE 2: Insert Deputados records first (memory efficient)
                if deputados_records:
                    deputados_inserted = self._bulk_insert_records(deputados_records)
                    total_records += deputados_inserted
                    print(f"  ✅ Inserted {deputados_inserted} Deputados financial records")

                # PHASE 3: TSE campaign finance (streaming with immediate inserts)
                # Log checkpoint before heavy TSE processing
                if i % 10 == 0:  # Every 10 politicians
                    self.logger.log_system_checkpoint(f"Processing politician {i}/{len(politicians)}")

                # SPACE ENGINEER FIX: Use proven streaming method
                tse_inserted = self._process_tse_finance_streaming(
                    politician, start_year, end_year
                )
                total_records += tse_inserted
                if tse_inserted > 0:
                    print(f"  ✅ Inserted {tse_inserted} TSE financial records")

                    self.logger.log_processing(
                        'financial_records', str(politician['id']), 'success',
                        {'deputados_count': len(deputados_records), 'tse_count': tse_inserted}
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
        """Process TSE campaign finance for a politician - ALL 4 TSE DATA TYPES"""
        print("⚠️⚠️⚠️ OLD METHOD CALLED - THIS WILL CAUSE MEMORY ISSUES! ⚠️⚠️⚠️")
        print("⚠️ Stack trace: THIS SHOULD NOT BE CALLED!")
        import traceback
        traceback.print_stack()

        records = []
        politician_cpf = politician['cpf']
        politician_id = politician['id']

        if not politician_cpf:
            return records

        # Calculate campaign years (election years + pre-campaign year before)
        campaign_years = self._calculate_campaign_years(start_year, end_year)
        print(f"    📅 TSE campaign years to search: {campaign_years}")

        # Define all TSE finance data types
        tse_data_types = ['receitas', 'despesas_contratadas', 'despesas_pagas', 'doador_originario']

        for year in campaign_years:
            try:
                print(f"    🗳️ TSE {year}...")
                total_year_records = 0

                # Process each TSE data type separately
                for data_type in tse_data_types:
                    try:
                        print(f"      📊 Processing {data_type}...")

                        # Get TSE finance data for specific type using streaming method
                        print(f"         🌊 Using streaming method for memory efficiency...")
                        finance_data = self.tse_client.get_finance_data_streaming(year, data_type, politician_cpf)

                        if finance_data:
                            type_records = 0
                            for record in finance_data:
                                candidate_cpf = record.get('nr_cpf_candidato') or record.get('cpf_candidato')

                                # Check if this record belongs to our politician
                                if candidate_cpf == politician_cpf:
                                    financial_record = self._build_tse_record(politician_id, record, year)
                                    if financial_record:
                                        records.append(financial_record)
                                        type_records += 1

                            if type_records > 0:
                                print(f"        ✅ Found {type_records} {data_type} records")
                                total_year_records += type_records

                    except Exception as e:
                        print(f"        ⚠️ Error processing {data_type}: {e}")
                        continue

                if total_year_records > 0:
                    print(f"      ✅ Total {year}: {total_year_records} TSE records")

            except Exception as e:
                print(f"    ⚠️ Error processing TSE {year}: {e}")
                continue

        return records

    def _process_tse_finance_streaming(self, politician: Dict, start_year: int,
                                      end_year: int) -> int:
        """Process TSE campaign finance with STREAMING + IMMEDIATE INSERTS (memory efficient)"""
        politician_cpf = politician['cpf']
        politician_id = politician['id']
        total_inserted = 0

        if not politician_cpf:
            print(f"    ⚠️ No CPF for politician {politician_id}, skipping TSE")
            return 0

        # Calculate campaign years (election years + pre-campaign year before)
        campaign_years = self._calculate_campaign_years(start_year, end_year)
        print(f"    📅 TSE campaign years to search: {campaign_years}")

        # Define all TSE finance data types
        tse_data_types = ['receitas', 'despesas_contratadas', 'despesas_pagas', 'doador_originario']

        for year in campaign_years:
            try:
                print(f"    🗳️ TSE {year}...")

                # Process each TSE data type separately with streaming
                for data_type in tse_data_types:
                    try:
                        print(f"      📊 Streaming {data_type}...")

                        # Get TSE finance data iterator (not full list)
                        type_inserted = self._stream_tse_data_type(
                            politician_cpf, politician_id, year, data_type
                        )

                        total_inserted += type_inserted
                        if type_inserted > 0:
                            print(f"        ✅ Inserted {type_inserted} {data_type} records")

                    except Exception as e:
                        print(f"        ⚠️ Error streaming {data_type}: {e}")
                        continue

            except Exception as e:
                print(f"    ⚠️ Error processing TSE {year}: {e}")
                continue

        return total_inserted

    def _stream_tse_data_type(self, politician_cpf: str, politician_id: int,
                             year: int, data_type: str) -> int:
        """Stream ONE TSE data type, filter by CPF, insert immediately"""

        # Get iterator from TSE client (don't load all data)
        finance_data_iterator = self.tse_client.get_finance_data_streaming(year, data_type, politician_cpf)

        batch_records = []
        batch_size = 100  # Insert every 100 matching records
        total_inserted = 0

        for record in finance_data_iterator:
            # Record already filtered by CPF in streaming method
            financial_record = self._build_tse_record(politician_id, record, year)
            if financial_record:
                batch_records.append(financial_record)

                # Insert batch when full
                if len(batch_records) >= batch_size:
                    inserted = self._bulk_insert_records(batch_records)
                    total_inserted += inserted
                    batch_records = []  # Clear memory

        # Insert remaining records
        if batch_records:
            inserted = self._bulk_insert_records(batch_records)
            total_inserted += inserted

        return total_inserted

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
        """Build financial record from TSE campaign finance - ALL 4 TSE DATA TYPES"""

        # Detect data type from record metadata
        data_type = record.get('tse_data_type', 'receitas')

        # Type-specific field extraction
        if data_type == 'receitas':
            return self._build_receitas_record(politician_id, record, year)
        elif data_type == 'despesas_contratadas':
            return self._build_despesas_contratadas_record(politician_id, record, year)
        elif data_type == 'despesas_pagas':
            return self._build_despesas_pagas_record(politician_id, record, year)
        elif data_type == 'doador_originario':
            return self._build_doador_originario_record(politician_id, record, year)
        else:
            # Fallback to receitas for backward compatibility
            return self._build_receitas_record(politician_id, record, year)

    def _build_receitas_record(self, politician_id: int, record: Dict, year: int) -> Optional[Dict]:
        """Build financial record from TSE campaign donations"""

        # Validate required fields
        amount = record.get('vr_receita') or record.get('valor_receita')
        if not amount:
            return None

        transaction_date_raw = record.get('dt_receita') or record.get('data_receita')
        transaction_date = self._parse_brazilian_date(transaction_date_raw)
        if not transaction_date:
            return None

        cnpj_cpf = record.get('nr_cpf_cnpj_doador') or record.get('cnpj_cpf_doador', '')
        cnpj_cpf_clean = ''.join(filter(str.isdigit, cnpj_cpf)) if cnpj_cpf else None

        return {
            'politician_id': politician_id,

            # SOURCE IDENTIFICATION
            'source_system': 'TSE',
            'source_record_id': f"tse_receita_{year}_{record.get('sq_receita', '')}",

            # TRANSACTION CLASSIFICATION
            'transaction_type': 'CAMPAIGN_DONATION',
            'transaction_category': record.get('ds_especie_receita') or record.get('descricao_receita'),

            # FINANCIAL DETAILS
            'amount': self._parse_brazilian_float(amount),
            'amount_net': self._parse_brazilian_float(amount),

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
            'election_date': self._parse_brazilian_date(record.get('dt_eleicao')),

            # VALIDATION FLAGS
            'cnpj_validated': False,
            'sanctions_checked': False,
            'external_validation_date': None
        }

    def _build_despesas_contratadas_record(self, politician_id: int, record: Dict, year: int) -> Optional[Dict]:
        """Build financial record from TSE contracted expenses"""

        # Validate required fields
        amount = record.get('vr_despesa')
        if not amount:
            return None

        transaction_date_raw = record.get('dt_despesa')
        transaction_date = self._parse_brazilian_date(transaction_date_raw)
        if not transaction_date:
            return None

        cnpj_cpf = record.get('nr_cpf_cnpj_fornecedor', '')
        cnpj_cpf_clean = ''.join(filter(str.isdigit, cnpj_cpf)) if cnpj_cpf else None

        return {
            'politician_id': politician_id,

            # SOURCE IDENTIFICATION
            'source_system': 'TSE',
            'source_record_id': f"tse_despesa_contratada_{year}_{record.get('sq_despesa', '')}",

            # TRANSACTION CLASSIFICATION
            'transaction_type': 'CAMPAIGN_EXPENSE_CONTRACTED',
            'transaction_category': record.get('ds_despesa'),

            # FINANCIAL DETAILS
            'amount': self._parse_brazilian_float(amount),
            'amount_net': self._parse_brazilian_float(amount),

            # TEMPORAL DETAILS
            'transaction_date': transaction_date,
            'year': year,

            # COUNTERPART INFORMATION
            'counterpart_name': record.get('nm_fornecedor'),
            'counterpart_cnpj_cpf': cnpj_cpf_clean,
            'counterpart_type': 'VENDOR',

            # ELECTION CONTEXT
            'election_year': year,

            # VALIDATION FLAGS
            'cnpj_validated': False,
            'sanctions_checked': False,
            'external_validation_date': None
        }

    def _build_despesas_pagas_record(self, politician_id: int, record: Dict, year: int) -> Optional[Dict]:
        """Build financial record from TSE paid expenses"""

        # Validate required fields
        amount = record.get('vr_pagamento')
        if not amount:
            return None

        transaction_date_raw = record.get('dt_pagamento')
        transaction_date = self._parse_brazilian_date(transaction_date_raw)
        if not transaction_date:
            return None

        cnpj_cpf = record.get('nr_cpf_cnpj_fornecedor', '')
        cnpj_cpf_clean = ''.join(filter(str.isdigit, cnpj_cpf)) if cnpj_cpf else None

        return {
            'politician_id': politician_id,

            # SOURCE IDENTIFICATION
            'source_system': 'TSE',
            'source_record_id': f"tse_despesa_paga_{year}_{record.get('sq_despesa_paga', '')}",

            # TRANSACTION CLASSIFICATION
            'transaction_type': 'CAMPAIGN_EXPENSE_PAID',
            'transaction_category': record.get('ds_despesa'),

            # FINANCIAL DETAILS
            'amount': self._parse_brazilian_float(amount),
            'amount_net': self._parse_brazilian_float(amount),

            # TEMPORAL DETAILS
            'transaction_date': transaction_date,
            'year': year,

            # COUNTERPART INFORMATION
            'counterpart_name': record.get('nm_fornecedor'),
            'counterpart_cnpj_cpf': cnpj_cpf_clean,
            'counterpart_type': 'VENDOR',

            # ELECTION CONTEXT
            'election_year': year,

            # VALIDATION FLAGS
            'cnpj_validated': False,
            'sanctions_checked': False,
            'external_validation_date': None
        }

    def _build_doador_originario_record(self, politician_id: int, record: Dict, year: int) -> Optional[Dict]:
        """Build financial record from TSE original donor tracking"""

        # Validate required fields
        amount = record.get('vr_receita')
        if not amount:
            return None

        transaction_date_raw = record.get('dt_receita')
        transaction_date = self._parse_brazilian_date(transaction_date_raw)
        if not transaction_date:
            return None

        cnpj_cpf = record.get('nr_cpf_cnpj_doador_originario', '')
        cnpj_cpf_clean = ''.join(filter(str.isdigit, cnpj_cpf)) if cnpj_cpf else None

        return {
            'politician_id': politician_id,

            # SOURCE IDENTIFICATION
            'source_system': 'TSE',
            'source_record_id': f"tse_doador_originario_{year}_{record.get('sq_receita', '')}",

            # TRANSACTION CLASSIFICATION
            'transaction_type': 'CAMPAIGN_DONATION_ORIGINAL',
            'transaction_category': record.get('ds_receita'),

            # FINANCIAL DETAILS
            'amount': self._parse_brazilian_float(amount),
            'amount_net': self._parse_brazilian_float(amount),

            # TEMPORAL DETAILS
            'transaction_date': transaction_date,
            'year': year,

            # COUNTERPART INFORMATION (Original donor, not intermediary)
            'counterpart_name': record.get('nm_doador_originario'),
            'counterpart_cnpj_cpf': cnpj_cpf_clean,
            'counterpart_type': 'ORIGINAL_DONOR',

            # BUSINESS CLASSIFICATION (for corporate donors)
            'counterpart_cnae': record.get('cd_cnae_doador_originario'),
            'counterpart_business_type': record.get('ds_cnae_doador_originario'),

            # ELECTION CONTEXT
            'election_year': year,

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
                # Build bulk insert query - ALL SCHEMA FIELDS INCLUDED (WITH NEW TSE FIELDS)
                fields = [
                    'politician_id', 'source_system', 'source_record_id', 'source_url',
                    'transaction_type', 'transaction_category', 'amount', 'amount_net',
                    'amount_rejected', 'original_amount', 'transaction_date', 'year',
                    'month', 'counterpart_name', 'counterpart_cnpj_cpf', 'counterpart_type',
                    'counterpart_cnae', 'counterpart_business_type', 'state', 'municipality',
                    'document_number', 'document_code', 'document_type', 'document_type_code',
                    'document_url', 'lote_code', 'installment', 'reimbursement_number',
                    'election_year', 'election_round', 'election_date', 'cnpj_validated',
                    'sanctions_checked', 'external_validation_date'
                ]

                placeholders = ', '.join(['%s'] * len(fields))
                fields_str = ', '.join(fields)

                query = f"""
                    INSERT INTO unified_financial_records ({fields_str})
                    VALUES ({placeholders})
                    ON CONFLICT (source_system, source_record_id) DO UPDATE SET
                        amount = EXCLUDED.amount,
                        amount_net = EXCLUDED.amount_net,
                        transaction_date = EXCLUDED.transaction_date,
                        updated_at = CURRENT_TIMESTAMP
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

                # Execute batch with retry logic for individual records
                try:
                    results = database.execute_batch_returning(query, values)
                    inserted_count += len(results)
                except Exception as batch_error:
                    print(f"    ⚠️ Batch {i//batch_size + 1} failed: {batch_error}")
                    print(f"    🔄 Retrying individual records...")
                    # Try inserting records one by one to identify problematic records
                    for j, record_values in enumerate(values):
                        try:
                            single_result = database.execute_batch_returning(query, [record_values])
                            inserted_count += len(single_result)
                        except Exception as record_error:
                            print(f"    ❌ Record {j+1} failed: {record_error}")
                            # Log the problematic record data for debugging
                            record_data = batch[j]
                            state_val = record_data.get('state')
                            source_id = record_data.get('source_record_id', 'unknown')
                            print(f"       Source ID: {source_id}, State: '{state_val}'")
                            continue  # Skip this record but continue with others

            except Exception as e:
                print(f"    ❌ Unexpected error in batch {i//batch_size + 1}: {e}")
                continue

        return inserted_count

    def _calculate_campaign_years(self, start_year: int, end_year: int) -> List[int]:
        """
        Calculate campaign finance years from service period

        Brazilian elections happen every 4 years: 2014, 2018, 2022, 2026...
        Campaign finance data includes:
        - Election year itself
        - Year before election (pre-campaign period)
        """
        campaign_years = set()

        # Find all election years within and around the period
        # Start from the first election year that could affect this period
        first_election_year = ((start_year - 1) // 4) * 4 + 2  # 2014, 2018, 2022...

        election_year = first_election_year
        while election_year <= end_year + 4:  # Look ahead for post-service campaigns
            # Add election year if it's relevant
            if election_year >= start_year - 1 and election_year <= end_year + 1:
                campaign_years.add(election_year)

            # Add pre-campaign year (year before election)
            pre_campaign_year = election_year - 1
            if pre_campaign_year >= start_year - 1 and pre_campaign_year <= end_year + 1:
                campaign_years.add(pre_campaign_year)

            election_year += 4

        return sorted(list(campaign_years))