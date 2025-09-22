# Politician Populator - Migration Documentation

**Source File**: `cli/modules/politician_populator.py`
**Target**: `cli4/modules/politician_populator.py`
**Purpose**: Foundation table population with 100% field mapping (Deputados + TSE)

## Core Logic Analysis

### Architecture Pattern
- **Foundation Table**: Must be populated first (all others depend on it)
- **Dual Data Sources**: Deputados API + TSE CKAN correlation
- **CPF Universal Identifier**: Links politician across systems
- **Complete Field Mapping**: Implements DATA_POPULATION_GUIDE.md Phase 1

### Population Workflow
```python
1. Get all current deputies from Deputados API
2. For each deputy:
   a. Fetch detailed profile (deputados.cpf, nome_civil, etc.)
   b. Search TSE by CPF across multiple elections
   c. Get most recent TSE record for current data
   d. Map all fields from both sources
   e. Insert unified politician record
```

### Key Data Mapping
```python
# Universal Identifiers
cpf: deputados.cpf ↔ tse_candidates.nr_cpf_candidato
deputy_id: deputados.id (for subsequent API calls)
sq_candidato_current: tse_candidates.sq_candidato (most recent)

# Critical Gap Resolution
electoral_number: tse_candidates.nr_candidato (MISSING from Deputados)

# Field Priority
Demographics: TSE primary, Deputados secondary
Political Status: Deputados primary, TSE enrichment
Contact Info: Deputados only
Career Timeline: Calculated from all TSE records
```

## Identified Issues

### 🐛 Critical Bug #1: Hardcoded Election Years
**Problem**: Only searches recent election years for performance
```python
# LIMITATION: Only searches 2020+ for speed
if year >= 2020:  # Only last 2 election cycles for speed
    recent_years.append(year)
```
**Impact**: Missing older political career data
**Fix**: Dynamic year calculation based on politician age/career

### 🐛 Bug #2: Complex TSE Search Logic
**Problem**: Complex nested loops for TSE candidate matching
```python
for year in recent_years:
    candidates = self.tse_client.get_candidate_data(year)
    matching_records = [
        candidate for candidate in candidates
        if candidate.get('nr_cpf_candidato') == cpf
    ]
```
**Impact**: Slow performance, potential memory issues
**Fix**: Optimized search with early termination

### 🐛 Bug #3: Rate Limiting in Loops
**Problem**: Rate limiting logic scattered throughout loops
```python
if processed % 10 == 0 and processed > 0:
    print(f"  ⏸️ Rate limiting: processed {processed}, pausing 2 seconds...")
    time.sleep(2)
else:
    time.sleep(0.5)  # Small delay between each politician
```
**Impact**: Inconsistent delays, potential hanging
**Fix**: Centralized rate limiting

### 🐛 Bug #4: Complex Field Mapping
**Problem**: Massive field mapping method with repetitive logic
```python
def _map_politician_fields(self, deputy_detail, deputy_status, most_recent_tse, all_tse_records):
    # 200+ lines of field mapping with complex conditionals
    record = {
        'cpf': cpf,
        'nome_civil': nome_civil,
        # ... 50+ more fields with complex logic
    }
```
**Impact**: Hard to maintain, debug, and test
**Fix**: Modular field mapping with clear separation

### 🐛 Bug #5: Database Insert Logic
**Problem**: Complex ID retrieval after insertion
```python
# For PostgreSQL, we need to get the ID differently
if self.db.db_type == 'postgresql':
    query = "SELECT id FROM unified_politicians WHERE cpf = ? ORDER BY id DESC LIMIT 1"
    result = self.db.execute_query(query, (record['cpf'],))
    return result[0]['id'] if result else None
```
**Impact**: Database-specific logic, potential race conditions
**Fix**: Use RETURNING clause or simplify approach

## Field Mapping Analysis

### Complete Field Coverage (100%)
```python
# UNIVERSAL IDENTIFIERS (3 fields)
cpf, nome_civil, nome_completo_normalizado

# SOURCE SYSTEM LINKS (3 fields)
deputy_id, sq_candidato_current, deputy_active

# DEPUTADOS CORE IDENTITY (3 fields)
nome_eleitoral, url_foto, data_falecimento

# TSE CORE IDENTITY (4 fields)
electoral_number, nr_titulo_eleitoral, nome_urna_candidato, nome_social_candidato

# CURRENT POLITICAL STATUS (5 fields)
current_party, current_state, current_legislature, situacao, condicao_eleitoral

# TSE POLITICAL DETAILS (5 fields)
nr_partido, nm_partido, nr_federacao, sg_federacao, current_position

# TSE ELECTORAL STATUS (4 fields)
cd_situacao_candidatura, ds_situacao_candidatura, cd_sit_tot_turno, ds_sit_tot_turno

# DEMOGRAPHICS (12 fields)
birth_date, birth_state, birth_municipality, gender, gender_code,
education_level, education_code, occupation, occupation_code,
marital_status, marital_status_code, race_color, race_color_code

# GEOGRAPHIC DETAILS (2 fields)
sg_ue, nm_ue

# CONTACT INFORMATION (5 fields)
email, phone, website, social_networks

# OFFICE DETAILS (5 fields)
office_building, office_room, office_floor, office_phone, office_email

# CAREER TIMELINE (4 fields)
first_election_year, last_election_year, total_elections, first_mandate_year

# DATA VALIDATION FLAGS (3 fields)
cpf_validated, tse_linked, last_updated_date
```

## CLI4 Migration Plan

### ✅ Keep (Core Logic)
1. **Foundation Table Pattern**: First table in dependency chain
2. **Dual Source Integration**: Deputados + TSE correlation
3. **CPF Universal Identifier**: Links across all systems
4. **Complete Field Mapping**: 100% coverage from both sources
5. **Validation Flags**: CPF validation, TSE linking status
6. **Career Timeline Calculation**: Min/max years from TSE records

### 🔧 Fix (Critical Issues)
1. **Dynamic Year Calculation**: Base search years on politician birth/career data
2. **Optimized TSE Search**: Early termination, efficient matching
3. **Centralized Rate Limiting**: Use CLI4 rate limiter
4. **Modular Field Mapping**: Separate methods for different field groups
5. **Simplified Database Operations**: Use proper RETURNING or upsert patterns

### 🚀 Improve (Enhancements)
1. **Parallel Processing**: Process multiple politicians concurrently
2. **Caching**: Cache TSE data to avoid repeated API calls
3. **Progress Tracking**: Real-time progress indicators
4. **Error Recovery**: Resume processing from last successful politician
5. **Data Quality Checks**: Validate field mapping completeness

## Implementation Strategy

### 1. Modular Field Mapping
```python
class CLI4PoliticianMapper:
    """Modular field mapping for politician data"""

    def map_universal_identifiers(self, deputy_detail: dict) -> dict:
        """Map universal identifier fields"""
        cpf = deputy_detail.get('cpf')
        nome_civil = deputy_detail.get('nomeCivil', '')

        return {
            'cpf': cpf,
            'nome_civil': nome_civil,
            'nome_completo_normalizado': self._normalize_name(nome_civil)
        }

    def map_deputados_identity(self, deputy_detail: dict, deputy_status: dict) -> dict:
        """Map Deputados-specific identity fields"""
        return {
            'nome_eleitoral': deputy_status.get('nomeEleitoral'),
            'url_foto': deputy_status.get('urlFoto'),
            'data_falecimento': self._parse_date(deputy_detail.get('dataFalecimento'))
        }

    def map_tse_identity(self, tse_record: dict) -> dict:
        """Map TSE-specific identity fields"""
        if not tse_record:
            return {field: None for field in TSE_IDENTITY_FIELDS}

        return {
            'electoral_number': tse_record.get('nr_candidato'),
            'nr_titulo_eleitoral': tse_record.get('nr_titulo_eleitoral_candidato'),
            'nome_urna_candidato': tse_record.get('nm_urna_candidato'),
            'nome_social_candidato': tse_record.get('nm_social_candidato')
        }
```

### 2. Optimized TSE Search
```python
def find_tse_candidate_by_cpf(self, cpf: str, birth_year: int = None) -> List[dict]:
    """Optimized TSE search with dynamic year calculation"""

    # Calculate relevant search years
    search_years = self._calculate_search_years(birth_year)
    print(f"    🔍 Searching {len(search_years)} election years: {search_years}")

    all_records = []
    for year in search_years:
        try:
            # Use optimized search with early termination
            year_records = self.tse_client.search_candidates_by_cpf(cpf, year)
            if year_records:
                all_records.extend(year_records)
                print(f"      ✓ Found {len(year_records)} records in {year}")

        except Exception as e:
            print(f"      ⚠️ Error searching {year}: {e}")
            continue

    return all_records

def _calculate_search_years(self, birth_year: int = None) -> List[int]:
    """Calculate relevant election years dynamically"""
    current_year = datetime.now().year

    if birth_year:
        # Start from when politician could first run (25 years old)
        min_year = birth_year + 25
        # Align to election years (even years in Brazil)
        start_year = min_year if min_year % 2 == 0 else min_year + 1
    else:
        # Default: last 10 years of elections
        start_year = current_year - 10

    # Generate election years (even years only)
    search_years = []
    year = start_year
    while year <= current_year:
        if year % 2 == 0:  # Brazilian elections are even years
            search_years.append(year)
        year += 1

    return search_years
```

### 3. Centralized Population Control
```python
class CLI4PoliticianPopulator:
    """Enhanced politician populator with better error handling"""

    def __init__(self, db_manager, rate_limiter, logger):
        self.db = db_manager
        self.rate_limiter = rate_limiter
        self.logger = logger
        self.mapper = CLI4PoliticianMapper()
        self.deputados_client = DeputadosClient()
        self.tse_client = TSEClient()

    def populate(self, limit: int = None, start_id: int = None,
                active_only: bool = True) -> List[int]:
        """Main population workflow with enhanced error handling"""

        self.logger.log_processing("politician_population", "session", "started")

        # Get deputies list
        deputies_list = self._get_deputies_list(active_only, limit, start_id)

        # Process in batches for better memory management
        created_ids = []
        batch_size = 50

        for i in range(0, len(deputies_list), batch_size):
            batch = deputies_list[i:i + batch_size]
            batch_ids = self._process_politician_batch(batch)
            created_ids.extend(batch_ids)

            # Progress update
            progress = min(i + batch_size, len(deputies_list))
            print(f"📊 Progress: {progress}/{len(deputies_list)} deputies processed")

        self.logger.log_processing("politician_population", "session", "completed",
                                 {"total_created": len(created_ids)})
        return created_ids
```

### 4. Enhanced Error Handling
```python
def _process_politician_batch(self, deputies_batch: List[dict]) -> List[int]:
    """Process batch of politicians with individual error handling"""
    created_ids = []

    for deputy in deputies_batch:
        try:
            # Rate limiting
            wait_time = self.rate_limiter.wait_if_needed("deputados")
            if wait_time > 0:
                time.sleep(wait_time)

            # Process single politician
            politician_id = self._process_single_politician(deputy)
            if politician_id:
                created_ids.append(politician_id)

        except Exception as e:
            self.logger.log_processing("politician", deputy['id'], "error",
                                     {"error": str(e), "name": deputy.get('nome', 'Unknown')})
            # Continue with next politician
            continue

    return created_ids

def _process_single_politician(self, deputy: dict) -> Optional[int]:
    """Process single politician with complete error isolation"""
    deputy_id = deputy['id']

    # Check if already exists
    existing_id = self._check_existing_politician(deputy_id)
    if existing_id:
        return existing_id

    # Build politician record
    politician_record = self._build_politician_record(deputy_id)
    if not politician_record:
        return None

    # Insert into database
    politician_id = self._insert_politician_safe(politician_record)
    return politician_id
```

## Integration with CLI4 Architecture

### Standard Usage
```python
from cli4.modules.politician_populator import CLI4PoliticianPopulator

# Initialize with dependencies
populator = CLI4PoliticianPopulator(
    db_manager=cli4_db,
    rate_limiter=cli4_rate_limiter,
    logger=cli4_logger
)

# Run population
created_ids = populator.populate(limit=100, active_only=True)
```

### Error Recovery
```python
# Resume from specific point
last_processed_id = get_last_processed_politician_id()
created_ids = populator.populate(start_id=last_processed_id + 1)
```

## Testing Strategy

### Field Mapping Tests
```python
def test_complete_field_mapping():
    """Ensure all 50+ fields are mapped correctly"""
    mapper = CLI4PoliticianMapper()

    # Test with complete data
    deputy_detail = load_test_deputy_data()
    tse_record = load_test_tse_data()

    record = mapper.map_all_fields(deputy_detail, tse_record)

    # Verify all expected fields are present
    assert len(record) >= 50
    assert record['cpf'] is not None
    assert record['nome_civil'] is not None
    # ... test all critical fields
```

### TSE Correlation Tests
```python
def test_tse_correlation():
    """Test TSE search and correlation logic"""
    populator = CLI4PoliticianPopulator(mock_db, mock_limiter, mock_logger)

    # Test with known CPF
    cpf = "67821090425"  # Arthur Lira test case
    tse_records = populator.find_tse_candidate_by_cpf(cpf, 1970)

    assert len(tse_records) > 0
    assert any(record.get('nr_cpf_candidato') == cpf for record in tse_records)
```

### Performance Tests
```python
def test_batch_processing():
    """Test batch processing performance"""
    populator = CLI4PoliticianPopulator(test_db, test_limiter, test_logger)

    # Process large batch
    start_time = time.time()
    deputies = [{'id': i, 'nome': f'Deputy {i}'} for i in range(100)]
    result = populator._process_politician_batch(deputies)
    elapsed = time.time() - start_time

    # Should complete within reasonable time
    assert elapsed < 300  # 5 minutes for 100 politicians
    assert len(result) > 0
```

## Success Criteria
1. ✅ 100% field mapping preserved from original
2. ✅ Dynamic TSE search years based on politician data
3. ✅ Optimized performance with batch processing
4. ✅ Centralized rate limiting integration
5. ✅ Modular, testable field mapping
6. ✅ Robust error handling and recovery
7. ✅ Complete CPF-TSE correlation capability
8. ✅ Foundation for all other table populations

This politician populator migration maintains complete functionality while fixing performance and reliability issues.