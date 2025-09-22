# CLI4 Complete Migration Strategy

**Source**: `cli/` (functional but hanging)
**Target**: `cli4/` (optimized and reliable)
**Goal**: Port 100% functionality while fixing hanging and performance issues

## Executive Summary

The CLI4 migration preserves the complete functionality of the working CLI system while addressing critical issues that cause hanging, performance problems, and reliability concerns. This document outlines the complete migration strategy for creating a production-ready CLI4 system.

## Migration Overview

### ✅ What Works (Keep)
1. **Complete 9-Table Architecture**: Foundation → Financial → Networks → Wealth → Assets → Career → Events → Professional
2. **Dual Database Support**: SQLite + PostgreSQL compatibility
3. **100% Field Mapping**: Complete coverage from Deputados + TSE sources
4. **CPF Universal Correlation**: Links politicians across all systems
5. **Modular Populator Design**: Clean separation of concerns
6. **Comprehensive CLI Interface**: All commands and parameters working
7. **Error Isolation**: Individual failures don't stop batch processing
8. **Bulk Operations**: Efficient batch inserts and updates

### 🐛 Critical Issues (Fix)
1. **Database Manager Hanging**: Subprocess initialization and SQLite preference
2. **Logging File I/O Issues**: Traditional logging can cause hangs
3. **Rate Limiting Problems**: Inefficient and inconsistent throttling
4. **Memory Growth**: Large datasets cause memory issues
5. **Missing TSE Finance Implementation**: Incomplete campaign finance data
6. **Complex Error Handling**: Difficult to debug and maintain
7. **Performance Bottlenecks**: Slow execution on large datasets
8. **Limited Validation**: Only 3 of 9 tables validated

### 🚀 Enhancements (Improve)
1. **Progress Tracking**: Visual progress indicators
2. **Parallel Processing**: Concurrent execution where safe
3. **Resume Capability**: Recover from interruptions
4. **Performance Monitoring**: Real-time metrics and optimization
5. **Enhanced Validation**: All 9 tables with cross-table checks
6. **Smart Caching**: Reduce redundant API calls
7. **Better Error Context**: Detailed error reporting and recovery

## Migration Architecture

### CLI4 Directory Structure
```
cli4/
├── main.py                 # Enhanced CLI entry point
├── modules/
│   ├── __init__.py
│   ├── database_manager.py  # Fixed database layer
│   ├── logger.py           # Unified safe logging
│   ├── rate_limiter.py     # Enhanced rate limiting
│   ├── validation_manager.py # Complete 9-table validation
│   │
│   └── populators/
│       ├── __init__.py
│       ├── base_populator.py     # Shared base class
│       ├── politician_populator.py   # Foundation table
│       ├── financial_populator.py    # Financial data (with TSE finance)
│       ├── network_populator.py      # Political networks
│       ├── wealth_populator.py       # Wealth tracking
│       ├── asset_populator.py        # Individual assets
│       ├── career_populator.py       # Career history
│       ├── event_populator.py        # Parliamentary events
│       └── professional_populator.py # Professional background
│
├── config/
│   ├── database_schemas.py  # Direct SQL schemas
│   └── validation_rules.py  # Validation configuration
│
└── tests/
    ├── test_database_manager.py
    ├── test_populators.py
    └── test_integration.py
```

## Phase-by-Phase Migration Plan

### Phase 1: Core Infrastructure (Week 1)
**Priority: Fix hanging issues**

#### 1.1 Database Manager Migration
```python
# cli4/modules/database_manager.py
class CLI4DatabaseManager:
    def __init__(self, db_path: str = "political_transparency.db"):
        # FIX: Check PostgreSQL FIRST
        self.postgres_url = os.getenv('POSTGRES_POOL_URL')
        if self.postgres_url:
            self.db_type = 'postgresql'
        else:
            self.db_type = 'sqlite'
            self.db_path = db_path

    def initialize_database(self, force: bool = False):
        # FIX: Direct SQL execution, no subprocess
        if self.db_type == 'postgresql':
            schema_sql = load_postgres_schema()
        else:
            schema_sql = load_sqlite_schema()
        self.execute_schema(schema_sql)

    def bulk_insert_chunked(self, table: str, records: List[dict], chunk_size: int = 1000):
        # FIX: Chunked operations to prevent memory issues
        for chunk in chunks(records, chunk_size):
            self.bulk_insert_records(table, chunk)
```

#### 1.2 Unified Logger Migration
```python
# cli4/modules/logger.py
class CLI4Logger:
    def __init__(self, console: bool = True, file: bool = False, async_file: bool = True):
        # SAFE: Default to console-only to prevent hanging
        self.console = console
        self.file = file
        if file and async_file:
            self.file_worker = AsyncFileWriter()  # Background thread

    def log_api_call(self, api: str, endpoint: str, status: str, response_time: float):
        # SAFE: Never hang on logging errors
        try:
            if self.console:
                print(f"{'✅' if status == 'success' else '❌'} {api}: {status} ({response_time:.2f}s)")
            if self.file:
                self.file_worker.queue_log(log_entry)
        except Exception:
            pass  # Never crash on logging errors
```

#### 1.3 Enhanced Rate Limiter Migration
```python
# cli4/modules/rate_limiter.py
class CLI4RateLimiter:
    def __init__(self):
        self.limits = {
            "tse": {"calls": 20, "period": 60, "burst": 5},      # Optimized
            "deputados": {"calls": 50, "period": 60, "burst": 10}, # Increased
        }

    def wait_if_needed(self, api_name: str) -> float:
        # RETURN wait time instead of blocking
        return self._calculate_wait_time(api_name)

    def sleep_interruptible(self, wait_time: float) -> bool:
        # INTERRUPTIBLE: Handle Ctrl+C gracefully
        try:
            time.sleep(wait_time)
            return True
        except KeyboardInterrupt:
            return False
```

**Testing Phase 1**:
```bash
# Test core infrastructure
python -m pytest cli4/tests/test_database_manager.py
python -m pytest cli4/tests/test_logger.py
python -m pytest cli4/tests/test_rate_limiter.py

# Integration test
python cli4/main.py init-db
python cli4/main.py status
```

### Phase 2: Foundation Populator (Week 2)
**Priority: Get politician population working**

#### 2.1 Base Populator Class
```python
# cli4/modules/populators/base_populator.py
class CLI4BasePopulator:
    def __init__(self, db_manager, rate_limiter, logger):
        self.db = db_manager
        self.rate_limiter = rate_limiter
        self.logger = logger

    def populate(self, politician_ids: List[int] = None, **kwargs) -> None:
        politicians = self._get_politicians_to_process(politician_ids)
        with self._progress_bar(len(politicians)) as pbar:
            self._populate_batch(politicians, pbar, **kwargs)

    def _safe_api_call(self, api_name: str, func, *args, **kwargs):
        """Safe API call with rate limiting and error handling"""
        wait_time = self.rate_limiter.wait_if_needed(api_name)
        if wait_time > 0 and not self.rate_limiter.sleep_interruptible(wait_time):
            raise KeyboardInterrupt("User cancelled operation")

        return func(*args, **kwargs)
```

#### 2.2 Politician Populator Migration
```python
# cli4/modules/populators/politician_populator.py
class CLI4PoliticianPopulator(CLI4BasePopulator):
    def _populate_batch(self, politicians: List[dict], pbar, **kwargs) -> List[int]:
        created_ids = []
        for deputy in politicians:
            try:
                politician_id = self._process_single_politician(deputy)
                if politician_id:
                    created_ids.append(politician_id)
                pbar.update(1)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.logger.log_processing("politician", deputy['id'], "error", {"error": str(e)})
                continue

        return created_ids

    def _find_tse_candidate_dynamic_years(self, cpf: str, birth_year: int = None) -> List[dict]:
        # FIX: Dynamic year calculation instead of hardcoded [2020, 2022]
        search_years = self._calculate_search_years(birth_year)
        return self._search_tse_by_cpf_optimized(cpf, search_years)
```

**Testing Phase 2**:
```bash
# Test politician population
python cli4/main.py populate politicians --limit 5
python cli4/main.py status --detailed
```

### Phase 3: Financial Populator (Week 3)
**Priority: Implement complete financial data including TSE**

#### 3.1 Complete TSE Finance Implementation
```python
# cli4/modules/populators/financial_populator.py
class CLI4FinancialPopulator(CLI4BasePopulator):
    def _collect_tse_financial_data_complete(self, cpf: str, years: List[int]) -> List[dict]:
        """COMPLETE TSE finance implementation (was stubbed in CLI)"""
        all_finance = []

        for year in years:
            try:
                # Campaign donations
                donations = self.tse_client.get_campaign_donations(cpf, year)
                for donation in donations:
                    donation['transaction_type'] = 'CAMPAIGN_DONATION'
                all_finance.extend(donations)

                # Campaign expenses
                expenses = self.tse_client.get_campaign_expenses(cpf, year)
                for expense in expenses:
                    expense['transaction_type'] = 'CAMPAIGN_EXPENSE'
                all_finance.extend(expenses)

            except Exception as e:
                self.logger.log_api_call("TSE", f"finance/{year}", "error", 0, {"error": str(e)})
                continue

        return all_finance

    def _bulk_upsert_counterparts_efficient(self, counterparts: List[dict]) -> None:
        """FIX: Efficient bulk upsert instead of individual operations"""
        if self.db.db_type == 'postgresql':
            self._postgresql_upsert(counterparts)
        else:
            self._sqlite_upsert(counterparts)
```

**Testing Phase 3**:
```bash
# Test financial population with TSE
python cli4/main.py populate financial --politician-ids 1 2 3
python cli4/main.py validate financial
```

### Phase 4: Remaining Populators (Week 4)
**Priority: Complete all 9 tables**

#### 4.1 Unified Populator Framework
```python
# Apply base class pattern to all remaining populators
# cli4/modules/populators/network_populator.py
# cli4/modules/populators/wealth_populator.py
# cli4/modules/populators/asset_populator.py
# cli4/modules/populators/career_populator.py
# cli4/modules/populators/event_populator.py
# cli4/modules/populators/professional_populator.py

class CLI4NetworkPopulator(CLI4BasePopulator):
    # Inherit safe API calls, rate limiting, progress tracking
    # Fix: Add TSE coalition data
    # Fix: Dynamic date ranges
    # Fix: Enhanced error handling
```

**Testing Phase 4**:
```bash
# Test all tables
python cli4/main.py populate all --limit 10
python cli4/main.py validate
```

### Phase 5: Enhanced Validation (Week 5)
**Priority: Complete data quality assurance**

#### 5.1 9-Table Validation Manager
```python
# cli4/modules/validation_manager.py
class CLI4ValidationManager:
    def validate_comprehensive(self, fix_mode: str = "report") -> dict:
        # Validate all 9 tables
        # Cross-table relationship validation
        # Performance validation
        # Auto-fix capabilities
        # Structured reporting
```

**Testing Phase 5**:
```bash
# Test comprehensive validation
python cli4/main.py validate --table all
python cli4/main.py validate --fix
```

### Phase 6: Performance Optimization (Week 6)
**Priority: Production-ready performance**

#### 6.1 Parallel Processing
```python
# cli4/modules/populators/parallel_processor.py
class CLI4ParallelProcessor:
    def populate_parallel(self, tables: List[str], politician_ids: List[int] = None):
        """Safe parallel processing where dependencies allow"""
        # networks, wealth, assets, career, events, professional can run in parallel
        # after politicians and financial are complete
```

#### 6.2 Caching and Optimization
```python
# cli4/modules/cache_manager.py
class CLI4CacheManager:
    def cache_tse_data(self, year: int, data_type: str, data: List[dict]):
        """Cache TSE data to avoid repeated API calls"""

    def get_cached_tse_data(self, year: int, data_type: str) -> Optional[List[dict]]:
        """Retrieve cached TSE data"""
```

**Testing Phase 6**:
```bash
# Test performance optimizations
time python cli4/main.py populate all --limit 50
python cli4/main.py populate networks wealth assets career events professional --parallel
```

## Testing Strategy

### Unit Tests
```python
# cli4/tests/test_database_manager.py
def test_postgresql_detection_priority():
    """Ensure PostgreSQL is detected before SQLite"""

def test_chunked_bulk_operations():
    """Test memory-efficient bulk operations"""

def test_no_subprocess_initialization():
    """Ensure direct SQL initialization"""

# cli4/tests/test_populators.py
def test_politician_tse_correlation():
    """Test complete TSE correlation functionality"""

def test_financial_tse_implementation():
    """Test TSE campaign finance implementation"""

def test_error_isolation():
    """Test individual politician error isolation"""
```

### Integration Tests
```python
# cli4/tests/test_integration.py
def test_complete_workflow():
    """Test full populate all workflow"""
    result = subprocess.run([
        "python", "cli4/main.py", "populate", "all", "--limit", "5"
    ], capture_output=True, text=True)

    assert result.returncode == 0
    assert "✅ Operation completed successfully" in result.stdout

def test_no_hanging():
    """Test that operations complete within reasonable time"""
    start_time = time.time()
    # Run population
    elapsed = time.time() - start_time
    assert elapsed < 600  # Should complete within 10 minutes
```

### Performance Tests
```python
def test_memory_usage():
    """Test memory usage stays reasonable"""
    import psutil
    process = psutil.Process()
    initial_memory = process.memory_info().rss

    # Run large operation
    run_large_population()

    final_memory = process.memory_info().rss
    assert (final_memory - initial_memory) < 1024 * 1024 * 1024  # < 1GB growth

def test_execution_speed():
    """Test execution speed improvements"""
    start_time = time.time()
    # Run standardized test
    elapsed = time.time() - start_time
    assert elapsed < BASELINE_TIME * 1.5  # No more than 50% slower than baseline
```

## Compatibility Requirements

### Command Compatibility
```bash
# All existing CLI commands must work identically
python cli4/main.py init-db --force
python cli4/main.py clear-db --confirm
python cli4/main.py populate politicians --limit 10 --active-only
python cli4/main.py populate financial --start-year 2020 --end-year 2023
python cli4/main.py populate all --limit 50
python cli4/main.py validate --table politicians --fix
python cli4/main.py status --detailed
```

### Data Compatibility
```sql
-- CLI4 must produce identical data to CLI
-- Same table schemas
-- Same field mappings
-- Same correlation logic
-- Same validation rules
```

### Environment Compatibility
```bash
# Must work with existing .env files
# Same database connection strings
# Same API client configurations
# Same file paths and structure
```

## Deployment Strategy

### Development Environment
```bash
# 1. Setup CLI4 alongside CLI
git checkout -b cli4-migration
cp -r cli/ cli4/
cd cli4/

# 2. Implement phase by phase
# Start with core infrastructure
# Add populators one by one
# Test thoroughly at each phase

# 3. Compare results
python cli/main.py populate politicians --limit 5
python cli4/main.py populate politicians --limit 5
# Verify identical data output
```

### Testing Environment
```bash
# 1. Automated testing
python -m pytest cli4/tests/ -v

# 2. Performance comparison
time python cli/main.py populate all --limit 10
time python cli4/main.py populate all --limit 10

# 3. Reliability testing
# Run extended operations to test for hanging
timeout 1800 python cli4/main.py populate all --limit 100
```

### Production Deployment
```bash
# 1. Side-by-side deployment
mv cli/ cli_backup/
mv cli4/ cli/

# 2. Verification
python cli/main.py status
python cli/main.py validate

# 3. Rollback plan
# Keep cli_backup/ until CLI4 is proven stable
```

## Success Criteria

### Functional Requirements
- ✅ All 15 CLI commands work identically
- ✅ All 9 tables populated with 100% field mapping
- ✅ TSE campaign finance data fully implemented
- ✅ CPF correlation rate maintained (95%+)
- ✅ Database initialization works without subprocess
- ✅ Validation covers all 9 tables

### Performance Requirements
- ✅ No hanging issues during any operation
- ✅ Memory usage < 2GB for 1000 politicians
- ✅ Execution time improved by 30%+
- ✅ Rate limiting prevents API bans
- ✅ Parallel processing where safe

### Reliability Requirements
- ✅ Individual politician errors don't stop batch
- ✅ Graceful handling of Ctrl+C interruption
- ✅ Resume capability for interrupted operations
- ✅ Comprehensive error logging and context
- ✅ Auto-recovery from transient failures

### Quality Requirements
- ✅ 90%+ test coverage
- ✅ All integration tests pass
- ✅ Performance tests within bounds
- ✅ No regression in data quality
- ✅ Enhanced validation catches more issues

## Risk Mitigation

### Risk: Data Integrity Issues
**Mitigation**:
- Comprehensive testing with known good data
- Side-by-side comparison CLI vs CLI4
- Enhanced validation before production use

### Risk: Performance Regression
**Mitigation**:
- Performance benchmarking at each phase
- Memory usage monitoring
- Timeout testing for hanging prevention

### Risk: API Changes
**Mitigation**:
- Robust error handling for API failures
- Fallback mechanisms for missing data
- Enhanced logging for debugging

### Risk: Database Issues
**Mitigation**:
- Support for both SQLite and PostgreSQL
- Transaction-based operations
- Backup and recovery procedures

This CLI4 migration strategy ensures a reliable, high-performance system that maintains all existing functionality while fixing critical issues.