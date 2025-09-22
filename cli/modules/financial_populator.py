"""
Financial Populator Module
Populates financial_counterparts and unified_financial_records tables
Implements the strategy from DATA_POPULATION_GUIDE.md Phase 2
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import re
import time

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.clients.deputados_client import DeputadosClient
from src.clients.tse_client import TSEClient
from cli.modules.database_manager import DatabaseManager

# Import enhanced logger
try:
    from cli.modules.enhanced_logger import enhanced_logger
except:
    # Fallback if enhanced logger not available
    class DummyLogger:
        def log_processing(self, *args, **kwargs): pass
        def log_api_call(self, *args, **kwargs): pass
        def log_data_issue(self, *args, **kwargs): pass
        def save_session_metrics(self): pass
    enhanced_logger = DummyLogger()


class FinancialPopulator:
    """
    Populates financial tables with complete field mapping
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.deputados_client = DeputadosClient()
        self.tse_client = TSEClient()

    def populate(self, politician_ids: Optional[List[int]] = None,
                start_year: Optional[int] = None,
                end_year: Optional[int] = None) -> None:
        """
        Populate financial tables

        Args:
            politician_ids: Specific politician IDs to process (if None, process all)
            start_year: Starting year for financial data
            end_year: Ending year for financial data
        """
        print("💰 FINANCIAL POPULATION WORKFLOW")
        print("=" * 50)
        print("Following DATA_POPULATION_GUIDE.md Phase 2 strategy")
        print("Population order: counterparts -> financial_records")
        print()

        enhanced_logger.log_processing("financial_population", "session", "started",
                                      {"politician_ids": politician_ids, "start_year": start_year, "end_year": end_year})

        # Get politicians to process
        if politician_ids:
            politicians = self._get_politicians_by_ids(politician_ids)
        else:
            politicians = self.db.get_politicians_for_processing(active_only=True)

        print(f"Processing {len(politicians)} politicians")

        if not start_year:
            start_year = datetime.now().year - 5  # Default: last 5 years
        if not end_year:
            end_year = datetime.now().year

        print(f"Date range: {start_year} - {end_year}")
        print()

        all_counterparts = {}
        all_financial_records = []
        processed = 0
        errors = 0

        for politician in politicians:
            try:
                politician_id = politician['id']
                deputy_id = politician['deputy_id']
                cpf = politician['cpf']

                print(f"\n💼 Processing politician {politician_id}: {politician['nome_civil']}")

                # Calculate dynamic date range for this politician
                politician_years = self._calculate_politician_years(politician, start_year, end_year)
                print(f"  📅 Dynamic years: {politician_years}")

                # Phase 1: Deputados financial data
                deputados_data = self._collect_deputados_financial_data(
                    deputy_id, politician_years
                )
                enhanced_logger.log_processing("deputados_financial", politician_id, "success",
                                              {"deputados_records": len(deputados_data), "name": politician['nome_civil']})

                # Phase 2: TSE financial data
                tse_data = self._collect_tse_financial_data(cpf, politician_years)
                enhanced_logger.log_processing("tse_financial", politician_id, "success",
                                              {"tse_records": len(tse_data), "name": politician['nome_civil']})

                # Phase 3: Extract counterparts
                counterparts = self._extract_counterparts(deputados_data, tse_data)
                for cnpj_cpf, counterpart in counterparts.items():
                    if cnpj_cpf not in all_counterparts:
                        all_counterparts[cnpj_cpf] = counterpart
                    else:
                        # Merge statistics
                        existing = all_counterparts[cnpj_cpf]
                        existing['transaction_count'] += counterpart['transaction_count']
                        existing['total_transaction_amount'] += counterpart['total_transaction_amount']
                        existing['politician_count'] += 1

                # Phase 4: Build financial records
                records = self._build_financial_records(
                    politician_id, deputados_data, tse_data
                )
                all_financial_records.extend(records)

                processed += 1
                enhanced_logger.log_processing("politician_financial", politician_id, "success",
                                              {"deputados_records": len(deputados_data), "tse_records": len(tse_data),
                                               "financial_records": len(records), "name": politician['nome_civil']})
                print(f"  ✅ Processed: {len(deputados_data)} deputados + {len(tse_data)} TSE records")

                # Rate limiting: small delay between politicians to avoid API bans
                if processed % 5 == 0 and processed > 0:
                    print(f"  ⏸️ Rate limiting: processed {processed}, pausing 1 second...")
                    time.sleep(1)
                else:
                    time.sleep(0.3)  # Small delay between each politician

            except Exception as e:
                errors += 1
                enhanced_logger.log_processing("politician_financial", politician_id, "error",
                                              {"error": str(e), "name": politician.get('nome_civil', 'Unknown')})
                print(f"  ❌ Error processing politician {politician_id}: {e}")
                continue

        # Bulk insert counterparts first
        print(f"\n💾 Inserting {len(all_counterparts)} counterparts...")
        self._insert_counterparts(list(all_counterparts.values()))
        enhanced_logger.log_processing("bulk_insert", "financial_counterparts", "success",
                                      {"records_inserted": len(all_counterparts)})

        # Bulk insert financial records
        print(f"💾 Inserting {len(all_financial_records)} financial records...")
        self._insert_financial_records(all_financial_records)
        enhanced_logger.log_processing("bulk_insert", "unified_financial_records", "success",
                                      {"records_inserted": len(all_financial_records)})

        # Summary
        print("\n" + "=" * 50)
        print("📊 FINANCIAL POPULATION SUMMARY")
        print(f"Politicians processed: {processed}")
        print(f"Errors: {errors}")
        print(f"Counterparts created: {len(all_counterparts)}")
        print(f"Financial records created: {len(all_financial_records)}")
        print("=" * 50)

        enhanced_logger.save_session_metrics()

    def _get_politicians_by_ids(self, politician_ids: List[int]) -> List[Dict[str, Any]]:
        """Get specific politicians by IDs"""
        placeholders = ', '.join(['?' for _ in politician_ids])
        query = f"""
            SELECT id, cpf, deputy_id, nome_civil, first_election_year, last_election_year
            FROM unified_politicians
            WHERE id IN ({placeholders})
        """
        results = self.db.execute_query(query, tuple(politician_ids))
        return [dict(row) for row in results]

    def _calculate_politician_years(self, politician: Dict[str, Any],
                                  default_start: int, default_end: int) -> List[int]:
        """Calculate dynamic date range for politician"""
        # Get politician's career timeline
        first_election = politician.get('first_election_year')
        last_election = politician.get('last_election_year')

        if first_election and last_election:
            # Use politician's career span with 2-year buffer
            start_year = max(first_election - 2, 2002)  # TSE data starts from 2002
            end_year = min(last_election + 2, default_end)
        else:
            # Fallback to default range
            start_year = default_start
            end_year = default_end

        return list(range(start_year, end_year + 1))

    def _collect_deputados_financial_data(self, deputy_id: int, years: List[int]) -> List[Dict[str, Any]]:
        """Collect all deputados expense data for specified years"""
        all_expenses = []

        if not deputy_id:
            return all_expenses

        for year in years:
            try:
                api_start = time.time()
                expenses = self.deputados_client.get_deputy_expenses(deputy_id, year)
                api_time = time.time() - api_start
                enhanced_logger.log_api_call("DEPUTADOS", f"expenses/{deputy_id}/{year}", "success", api_time,
                                            {"year": year, "deputy_id": deputy_id, "records_received": len(expenses)})
                all_expenses.extend(expenses)
            except Exception as e:
                enhanced_logger.log_api_call("DEPUTADOS", f"expenses/{deputy_id}/{year}", "error", 0,
                                            {"year": year, "deputy_id": deputy_id, "error": str(e)})
                print(f"    ⚠️ Failed to get deputados expenses for {year}: {e}")
                continue

        print(f"    ✓ Collected {len(all_expenses)} deputados expenses")
        return all_expenses

    def _collect_tse_financial_data(self, cpf: str, years: List[int]) -> List[Dict[str, Any]]:
        """Collect TSE campaign finance data for specified years"""
        all_finance = []

        if not cpf:
            return all_finance

        try:
            # Get TSE campaign finance data
            packages = self.tse_client.get_packages()

            for year in years:
                # Look for campaign finance packages for this year
                finance_packages = [
                    p for p in packages
                    if f'receitas_candidatos_{year}' in p or f'despesas_candidatos_{year}' in p
                ]

                for package in finance_packages:
                    try:
                        package_info = self.tse_client.get_package_info(package)
                        # Skip TSE finance data for now - complex implementation needed
                        # TODO: Implement TSE campaign finance data collection
                        print(f"      → Skipping TSE finance package {package} (not implemented)")
                        continue
                    except Exception as e:
                        print(f"      ⚠️ Error getting TSE finance for {package}: {e}")
                        continue

        except Exception as e:
            print(f"    ⚠️ Error in TSE finance collection: {e}")

        print(f"    ✓ Collected {len(all_finance)} TSE finance records")
        return all_finance

    def _extract_counterparts(self, deputados_data: List[Dict[str, Any]],
                            tse_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Extract unique financial counterparts from all transaction data"""
        counterparts = {}

        # Process deputados expenses
        for expense in deputados_data:
            cnpj_cpf = expense.get('cnpjCpfFornecedor')
            if not cnpj_cpf:
                continue

            clean_id = re.sub(r'[^\d]', '', cnpj_cpf)
            if len(clean_id) not in [11, 14]:
                continue

            if clean_id not in counterparts:
                counterparts[clean_id] = {
                    'cnpj_cpf': clean_id,
                    'name': expense.get('nomeFornecedor', ''),
                    'normalized_name': self._normalize_name(expense.get('nomeFornecedor', '')),
                    'entity_type': 'COMPANY' if len(clean_id) == 14 else 'INDIVIDUAL',
                    'transaction_count': 0,
                    'total_transaction_amount': 0.0,
                    'politician_count': 1,
                    'first_transaction_date': None,
                    'last_transaction_date': None,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }

            counterpart = counterparts[clean_id]
            counterpart['transaction_count'] += 1
            counterpart['total_transaction_amount'] += float(expense.get('valorLiquido', 0))

            # Update date range
            transaction_date = expense.get('dataDocumento')
            if transaction_date:
                if not counterpart['first_transaction_date'] or transaction_date < counterpart['first_transaction_date']:
                    counterpart['first_transaction_date'] = transaction_date
                if not counterpart['last_transaction_date'] or transaction_date > counterpart['last_transaction_date']:
                    counterpart['last_transaction_date'] = transaction_date

        # Process TSE finance data
        for finance_record in tse_data:
            cnpj_cpf = finance_record.get('cnpj_cpf_doador')
            if not cnpj_cpf:
                continue

            clean_id = re.sub(r'[^\d]', '', cnpj_cpf)
            if len(clean_id) not in [11, 14]:
                continue

            if clean_id not in counterparts:
                counterparts[clean_id] = {
                    'cnpj_cpf': clean_id,
                    'name': finance_record.get('nome_doador', ''),
                    'normalized_name': self._normalize_name(finance_record.get('nome_doador', '')),
                    'entity_type': 'COMPANY' if len(clean_id) == 14 else 'INDIVIDUAL',
                    'transaction_count': 0,
                    'total_transaction_amount': 0.0,
                    'politician_count': 1,
                    'first_transaction_date': None,
                    'last_transaction_date': None
                }

            counterpart = counterparts[clean_id]
            counterpart['transaction_count'] += 1
            counterpart['total_transaction_amount'] += float(finance_record.get('valor_transacao', 0))

            # Update date range
            transaction_date = finance_record.get('data_transacao')
            if transaction_date:
                if not counterpart['first_transaction_date'] or transaction_date < counterpart['first_transaction_date']:
                    counterpart['first_transaction_date'] = transaction_date
                if not counterpart['last_transaction_date'] or transaction_date > counterpart['last_transaction_date']:
                    counterpart['last_transaction_date'] = transaction_date

        return counterparts

    def _build_financial_records(self, politician_id: int,
                               deputados_data: List[Dict[str, Any]],
                               tse_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build unified financial records from both sources"""
        records = []

        # Process deputados expenses
        for expense in deputados_data:
            record = {
                'politician_id': politician_id,
                'source_system': 'DEPUTADOS',
                'source_record_id': str(expense.get('id', '')),
                'source_url': expense.get('urlDocumento'),
                'transaction_type': 'PARLIAMENTARY_EXPENSE',
                'transaction_category': expense.get('tipoDespesa'),
                'amount': float(expense.get('valorLiquido', 0)),
                'amount_net': float(expense.get('valorLiquido', 0)),
                'amount_rejected': float(expense.get('valorGlosa', 0)),
                'original_amount': float(expense.get('valorDocumento', 0)),
                'transaction_date': self._parse_date(expense.get('dataDocumento')),
                'year': int(expense.get('ano', 0)) if expense.get('ano') else None,
                'month': int(expense.get('mes', 0)) if expense.get('mes') else None,
                'counterpart_name': expense.get('nomeFornecedor'),
                'counterpart_cnpj_cpf': re.sub(r'[^\d]', '', expense.get('cnpjCpfFornecedor', '')),
                'counterpart_type': 'VENDOR',
                'document_number': expense.get('numDocumento'),
                'document_code': int(expense.get('codDocumento', 0)) if expense.get('codDocumento') else None,
                'document_type': expense.get('tipoDocumento'),
                'document_type_code': int(expense.get('codTipoDocumento', 0)) if expense.get('codTipoDocumento') else None,
                'document_url': expense.get('urlDocumento'),
                'lote_code': int(expense.get('codLote', 0)) if expense.get('codLote') else None,
                'installment': int(expense.get('parcela', 0)) if expense.get('parcela') else None,
                'reimbursement_number': expense.get('numRessarcimento'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            records.append(record)

        # Process TSE finance data
        for finance in tse_data:
            record = {
                'politician_id': politician_id,
                'source_system': 'TSE',
                'source_record_id': str(finance.get('sq_receita', finance.get('sq_despesa', ''))),
                'transaction_type': 'CAMPAIGN_DONATION' if finance.get('sq_receita') else 'CAMPAIGN_EXPENSE',
                'transaction_category': finance.get('descricao_especie'),
                'amount': float(finance.get('valor_transacao', 0)),
                'transaction_date': self._parse_date(finance.get('data_transacao')),
                'year': int(finance.get('ano_eleicao', 0)) if finance.get('ano_eleicao') else None,
                'counterpart_name': finance.get('nome_doador', finance.get('nome_fornecedor')),
                'counterpart_cnpj_cpf': re.sub(r'[^\d]', '', finance.get('cnpj_cpf_doador', finance.get('cnpj_cpf_fornecedor', ''))),
                'counterpart_type': 'DONOR' if finance.get('sq_receita') else 'VENDOR',
                'state': finance.get('sg_uf_doador', finance.get('sg_uf_fornecedor')),
                'municipality': finance.get('nm_municipio_doador', finance.get('nm_municipio_fornecedor')),
                'election_year': int(finance.get('ano_eleicao', 0)) if finance.get('ano_eleicao') else None,
                'election_round': int(finance.get('nr_turno', 0)) if finance.get('nr_turno') else None,
                'election_date': self._parse_date(finance.get('dt_eleicao')),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            records.append(record)

        return records

    def _insert_counterparts(self, counterparts: List[Dict[str, Any]]) -> None:
        """Insert counterparts using upsert logic"""
        for counterpart in counterparts:
            try:
                # Check if exists
                existing_id = self.db.get_financial_counterpart_id(counterpart['cnpj_cpf'])

                if existing_id:
                    # Update existing
                    query = """
                        UPDATE financial_counterparts
                        SET transaction_count = transaction_count + ?,
                            total_transaction_amount = total_transaction_amount + ?,
                            politician_count = politician_count + 1,
                            last_transaction_date = ?,
                            updated_at = ?
                        WHERE id = ?
                    """
                    self.db.execute_update(query, (
                        counterpart['transaction_count'],
                        counterpart['total_transaction_amount'],
                        counterpart['last_transaction_date'],
                        datetime.now().isoformat(),
                        existing_id
                    ))
                else:
                    # Insert new
                    counterpart['created_at'] = datetime.now().isoformat()
                    counterpart['updated_at'] = datetime.now().isoformat()
                    self.db.bulk_insert_records('financial_counterparts', [counterpart])

            except Exception as e:
                print(f"    ⚠️ Error inserting counterpart {counterpart['cnpj_cpf']}: {e}")

    def _insert_financial_records(self, records: List[Dict[str, Any]]) -> None:
        """Bulk insert financial records"""
        if records:
            self.db.bulk_insert_records('unified_financial_records', records)

    def _normalize_name(self, name: str) -> str:
        """Normalize names for matching"""
        if not name:
            return ""
        return re.sub(r'[^\w\s]', '', name.upper()).strip()

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None

        try:
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            return None
        except Exception:
            return None