# Financial Populator - Migration Documentation

**Source File**: `cli/modules/financial_populator.py`
**Target**: `cli4/modules/financial_populator.py`
**Purpose**: Populate financial_counterparts + unified_financial_records (Phase 2)

## Core Logic Analysis

### Architecture Pattern
- **Dependency**: Requires unified_politicians table (populated first)
- **Dual Table Population**: financial_counterparts → unified_financial_records
- **Dual Data Sources**: Deputados expenses + TSE campaign finance
- **CNPJ/CPF Correlation**: Links vendor/donor networks across politicians

### Population Workflow
```python
1. Get politicians to process (by IDs or all active)
2. For each politician:
   a. Calculate dynamic date range based on career timeline
   b. Collect Deputados expenses for calculated years
   c. Collect TSE campaign finance for calculated years
   d. Extract unique counterparts (CNPJ/CPF entities)
   e. Build financial records from both sources
3. Bulk insert counterparts (with upsert logic)
4. Bulk insert financial records
```

### Dynamic Date Range Strategy
```python
# Instead of hardcoded years, calculate based on politician career
if first_election and last_election:
    start_year = max(first_election - 2, 2002)  # 2-year buffer, TSE data starts 2002
    end_year = min(last_election + 2, current_year)
else:
    # Fallback to default range
    start_year = default_start
    end_year = default_end
```

## Identified Issues

### 🐛 Critical Bug #1: TSE Finance Data Not Implemented
**Problem**: TSE campaign finance collection is stubbed out
```python
# TODO: Implement TSE campaign finance data collection
print(f"      → Skipping TSE finance package {package} (not implemented)")
continue
```
**Impact**: Missing critical campaign finance data
**Fix**: Implement complete TSE finance data collection

### 🐛 Bug #2: Complex Counterpart Extraction
**Problem**: Duplicate code for extracting counterparts from different sources
```python
# Process deputados expenses
for expense in deputados_data:
    cnpj_cpf = expense.get('cnpjCpfFornecedor')
    # ... complex extraction logic

# Process TSE finance data
for finance_record in tse_data:
    cnpj_cpf = finance_record.get('cnpj_cpf_doador')
    # ... duplicate extraction logic
```
**Fix**: Unified counterpart extraction method

### 🐛 Bug #3: Inefficient Upsert Logic
**Problem**: Individual upsert operations for each counterpart
```python
for counterpart in counterparts:
    existing_id = self.db.get_financial_counterpart_id(counterpart['cnpj_cpf'])
    if existing_id:
        # Update existing (individual query)
    else:
        # Insert new (individual query)
```
**Impact**: Thousands of individual database operations
**Fix**: Bulk upsert with ON CONFLICT resolution

### 🐛 Bug #4: Rate Limiting in Nested Loops
**Problem**: Rate limiting scattered in politician and year loops
```python
for politician in politicians:
    for year in years:
        # API call with potential hanging
        expenses = self.deputados_client.get_deputy_expenses(deputy_id, year)
```
**Fix**: Centralized rate limiting with better batching

### 🐛 Bug #5: Memory Growth with Large Datasets
**Problem**: Accumulates all records in memory before bulk insert
```python
all_counterparts = {}  # Grows indefinitely
all_financial_records = []  # Can become very large
```
**Impact**: Memory issues with large politician sets
**Fix**: Streaming processing with periodic flushes

## Data Mapping Analysis

### Financial Counterparts Table
```python
# From Deputados Expenses
cnpj_cpf: expense.cnpjCpfFornecedor (cleaned)
name: expense.nomeFornecedor
entity_type: 'COMPANY' if len(cnpj_cpf) == 14 else 'INDIVIDUAL'
transaction_count: count of transactions
total_transaction_amount: sum of valores
first/last_transaction_date: date range

# From TSE Campaign Finance
cnpj_cpf: finance.cnpj_cpf_doador (cleaned)
name: finance.nome_doador
entity_type: 'COMPANY' if len(cnpj_cpf) == 14 else 'INDIVIDUAL'
```

### Unified Financial Records Table
```python
# Deputados Expenses → PARLIAMENTARY_EXPENSE
source_system: 'DEPUTADOS'
transaction_type: 'PARLIAMENTARY_EXPENSE'
amount: expense.valorLiquido
counterpart_cnpj_cpf: expense.cnpjCpfFornecedor (cleaned)
document_url: expense.urlDocumento
# + 15 other deputados-specific fields

# TSE Finance → CAMPAIGN_DONATION/CAMPAIGN_EXPENSE
source_system: 'TSE'
transaction_type: 'CAMPAIGN_DONATION' or 'CAMPAIGN_EXPENSE'
amount: finance.valor_transacao
counterpart_cnpj_cpf: finance.cnpj_cpf_doador (cleaned)
election_year: finance.ano_eleicao
# + TSE-specific fields
```

## CLI4 Migration Plan

### ✅ Keep (Core Logic)
1. **Dynamic Date Range Calculation**: Career-based year calculation
2. **Dual Source Integration**: Deputados + TSE financial data
3. **CNPJ/CPF Normalization**: Clean and validate identifiers
4. **Entity Type Classification**: COMPANY vs INDIVIDUAL based on ID length
5. **Complete Field Mapping**: All available fields from both sources
6. **Bulk Operations**: Batch inserts for performance

### 🔧 Fix (Critical Issues)
1. **Implement TSE Finance**: Complete campaign finance data collection
2. **Unified Counterpart Extraction**: Single method for all sources
3. **Bulk Upsert Operations**: Efficient ON CONFLICT handling
4. **Centralized Rate Limiting**: Consistent API throttling
5. **Streaming Processing**: Process in chunks to manage memory

### 🚀 Improve (Enhancements)
1. **Parallel Processing**: Process multiple politicians concurrently
2. **Caching**: Cache repeated API calls
3. **Progress Tracking**: Real-time progress indicators
4. **Data Validation**: Validate CNPJ/CPF formats
5. **Error Recovery**: Resume from last processed politician

## Implementation Strategy

### 1. Complete TSE Finance Implementation
```python
def _collect_tse_financial_data(self, cpf: str, years: List[int]) -> List[dict]:
    """Complete TSE campaign finance collection"""
    all_finance = []

    for year in years:
        try:
            # Get campaign donations (receitas)
            donations = self.tse_client.get_campaign_donations(cpf, year)
            for donation in donations:
                donation['finance_type'] = 'DONATION'
                donation['transaction_type'] = 'CAMPAIGN_DONATION'
            all_finance.extend(donations)

            # Get campaign expenses (despesas)
            expenses = self.tse_client.get_campaign_expenses(cpf, year)
            for expense in expenses:
                expense['finance_type'] = 'EXPENSE'
                expense['transaction_type'] = 'CAMPAIGN_EXPENSE'
            all_finance.extend(expenses)

        except Exception as e:
            self.logger.log_api_call("TSE", f"finance/{year}", "error", 0,
                                   {"year": year, "cpf": cpf, "error": str(e)})
            continue

    return all_finance
```

### 2. Unified Counterpart Extraction
```python
class CLI4CounterpartExtractor:
    """Unified counterpart extraction from all financial sources"""

    def extract_counterparts(self, deputados_data: List[dict],
                           tse_data: List[dict]) -> Dict[str, dict]:
        """Extract and merge counterparts from all sources"""
        counterparts = {}

        # Process all sources with unified logic
        sources = [
            (deputados_data, self._extract_from_deputados),
            (tse_data, self._extract_from_tse)
        ]

        for data, extractor in sources:
            for record in data:
                counterpart = extractor(record)
                if counterpart:
                    cnpj_cpf = counterpart['cnpj_cpf']
                    if cnpj_cpf in counterparts:
                        self._merge_counterpart_stats(counterparts[cnpj_cpf], counterpart)
                    else:
                        counterparts[cnpj_cpf] = counterpart

        return counterparts

    def _extract_from_deputados(self, expense: dict) -> Optional[dict]:
        """Extract counterpart from deputados expense"""
        cnpj_cpf = self._clean_cnpj_cpf(expense.get('cnpjCpfFornecedor'))
        if not cnpj_cpf:
            return None

        return {
            'cnpj_cpf': cnpj_cpf,
            'name': expense.get('nomeFornecedor', ''),
            'normalized_name': self._normalize_name(expense.get('nomeFornecedor', '')),
            'entity_type': 'COMPANY' if len(cnpj_cpf) == 14 else 'INDIVIDUAL',
            'transaction_count': 1,
            'total_transaction_amount': float(expense.get('valorLiquido', 0)),
            'first_transaction_date': expense.get('dataDocumento'),
            'last_transaction_date': expense.get('dataDocumento'),
            'source_systems': ['DEPUTADOS']
        }

    def _extract_from_tse(self, finance: dict) -> Optional[dict]:
        """Extract counterpart from TSE finance record"""
        cnpj_cpf = self._clean_cnpj_cpf(finance.get('cnpj_cpf_doador'))
        if not cnpj_cpf:
            return None

        return {
            'cnpj_cpf': cnpj_cpf,
            'name': finance.get('nome_doador', ''),
            'normalized_name': self._normalize_name(finance.get('nome_doador', '')),
            'entity_type': 'COMPANY' if len(cnpj_cpf) == 14 else 'INDIVIDUAL',
            'transaction_count': 1,
            'total_transaction_amount': float(finance.get('valor_transacao', 0)),
            'first_transaction_date': finance.get('data_transacao'),
            'last_transaction_date': finance.get('data_transacao'),
            'source_systems': ['TSE']
        }
```

### 3. Bulk Upsert Operations
```python
def _bulk_upsert_counterparts(self, counterparts: List[dict]) -> None:
    """Efficient bulk upsert for counterparts"""
    if not counterparts:
        return

    if self.db.db_type == 'postgresql':
        self._postgresql_upsert_counterparts(counterparts)
    else:
        self._sqlite_upsert_counterparts(counterparts)

def _postgresql_upsert_counterparts(self, counterparts: List[dict]) -> None:
    """PostgreSQL ON CONFLICT upsert"""
    query = """
        INSERT INTO financial_counterparts (
            cnpj_cpf, name, normalized_name, entity_type,
            transaction_count, total_transaction_amount,
            first_transaction_date, last_transaction_date,
            created_at, updated_at
        ) VALUES %s
        ON CONFLICT (cnpj_cpf) DO UPDATE SET
            transaction_count = financial_counterparts.transaction_count + EXCLUDED.transaction_count,
            total_transaction_amount = financial_counterparts.total_transaction_amount + EXCLUDED.total_transaction_amount,
            last_transaction_date = GREATEST(financial_counterparts.last_transaction_date, EXCLUDED.last_transaction_date),
            updated_at = EXCLUDED.updated_at
    """

    # Use psycopg2.extras.execute_values for efficiency
    values = [
        (cp['cnpj_cpf'], cp['name'], cp['normalized_name'], cp['entity_type'],
         cp['transaction_count'], cp['total_transaction_amount'],
         cp['first_transaction_date'], cp['last_transaction_date'],
         datetime.now().isoformat(), datetime.now().isoformat())
        for cp in counterparts
    ]

    self.db.execute_values(query, values)
```

### 4. Streaming Processing
```python
class CLI4FinancialPopulator:
    """Streaming financial data populator"""

    def __init__(self, db_manager, rate_limiter, logger):
        self.db = db_manager
        self.rate_limiter = rate_limiter
        self.logger = logger
        self.extractor = CLI4CounterpartExtractor()
        self.batch_size = 100  # Process in batches

    def populate_streaming(self, politician_ids: List[int] = None) -> None:
        """Stream processing with memory management"""
        politicians = self._get_politicians_to_process(politician_ids)

        # Process in batches to manage memory
        for i in range(0, len(politicians), self.batch_size):
            batch = politicians[i:i + self.batch_size]
            self._process_politician_batch(batch)

            # Periodic cleanup
            if i % (self.batch_size * 5) == 0:
                self.db.vacuum_database()  # Optimize database
                gc.collect()  # Force garbage collection

    def _process_politician_batch(self, politicians: List[dict]) -> None:
        """Process batch with streaming to database"""
        batch_counterparts = {}
        batch_records = []

        for politician in politicians:
            try:
                # Rate limiting
                wait_time = self.rate_limiter.wait_if_needed("deputados")
                if wait_time > 0:
                    time.sleep(wait_time)

                # Collect data for this politician
                politician_data = self._collect_politician_financial_data(politician)

                # Extract counterparts and records
                counterparts = self.extractor.extract_counterparts(
                    politician_data['deputados'], politician_data['tse']
                )
                records = self._build_financial_records(
                    politician['id'], politician_data['deputados'], politician_data['tse']
                )

                # Merge into batch
                for cnpj_cpf, counterpart in counterparts.items():
                    if cnpj_cpf in batch_counterparts:
                        self._merge_counterpart_stats(batch_counterparts[cnpj_cpf], counterpart)
                    else:
                        batch_counterparts[cnpj_cpf] = counterpart

                batch_records.extend(records)

            except Exception as e:
                self.logger.log_processing("politician_financial", politician['id'], "error",
                                         {"error": str(e), "name": politician.get('nome_civil', 'Unknown')})
                continue

        # Bulk insert batch
        self._bulk_upsert_counterparts(list(batch_counterparts.values()))
        self._bulk_insert_financial_records(batch_records)
```

### 5. Enhanced Error Handling and Recovery
```python
def populate_with_recovery(self, politician_ids: List[int] = None,
                          resume_from: int = None) -> None:
    """Population with checkpoint recovery"""
    politicians = self._get_politicians_to_process(politician_ids)

    if resume_from:
        politicians = [p for p in politicians if p['id'] >= resume_from]
        self.logger.log_processing("financial_population", "session", "resumed",
                                 {"resume_from": resume_from})

    checkpoint_file = "financial_population_checkpoint.json"
    processed_count = 0

    try:
        for politician in politicians:
            self._process_single_politician_safe(politician)
            processed_count += 1

            # Save checkpoint every 10 politicians
            if processed_count % 10 == 0:
                checkpoint = {
                    'last_processed_id': politician['id'],
                    'processed_count': processed_count,
                    'timestamp': datetime.now().isoformat()
                }
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint, f)

    except KeyboardInterrupt:
        print(f"\n⏹️ Interrupted. Resume with --resume-from {politician['id']}")
    except Exception as e:
        self.logger.log_processing("financial_population", "session", "error",
                                 {"error": str(e), "last_processed": politician['id']})
        raise
    finally:
        # Cleanup checkpoint file on successful completion
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
```

## Testing Strategy

### TSE Finance Integration Tests
```python
def test_tse_finance_collection():
    """Test complete TSE finance data collection"""
    populator = CLI4FinancialPopulator(test_db, test_limiter, test_logger)

    # Test with known politician CPF
    cpf = "67821090425"  # Arthur Lira
    years = [2020, 2022]

    tse_data = populator._collect_tse_financial_data(cpf, years)

    # Should return campaign finance records
    assert len(tse_data) > 0
    assert any(record.get('transaction_type') == 'CAMPAIGN_DONATION' for record in tse_data)
```

### Bulk Operations Tests
```python
def test_bulk_upsert_performance():
    """Test bulk upsert performance and correctness"""
    populator = CLI4FinancialPopulator(test_db, test_limiter, test_logger)

    # Create test counterparts
    counterparts = [
        {'cnpj_cpf': f'1234567890{i:02d}', 'name': f'Company {i}', 'transaction_count': 1}
        for i in range(1000)
    ]

    start_time = time.time()
    populator._bulk_upsert_counterparts(counterparts)
    elapsed = time.time() - start_time

    # Should be fast and all records should exist
    assert elapsed < 5  # Should complete in under 5 seconds
    assert test_db.get_table_count('financial_counterparts') >= 1000
```

### Memory Management Tests
```python
def test_streaming_memory_usage():
    """Test memory usage during streaming processing"""
    import psutil
    process = psutil.Process()

    populator = CLI4FinancialPopulator(test_db, test_limiter, test_logger)

    initial_memory = process.memory_info().rss

    # Process large dataset
    large_politician_list = list(range(1000))
    populator.populate_streaming(large_politician_list)

    final_memory = process.memory_info().rss
    memory_growth = final_memory - initial_memory

    # Memory growth should be reasonable (less than 500MB)
    assert memory_growth < 500 * 1024 * 1024
```

## Success Criteria
1. ✅ Complete TSE campaign finance data collection
2. ✅ Unified counterpart extraction from all sources
3. ✅ Bulk upsert operations for efficiency
4. ✅ Streaming processing for memory management
5. ✅ Centralized rate limiting and error handling
6. ✅ Checkpoint recovery for interrupted operations
7. ✅ Dynamic date range calculation preserved
8. ✅ 100% field mapping from both sources maintained

This financial populator migration addresses the critical missing TSE finance implementation while optimizing performance and reliability.