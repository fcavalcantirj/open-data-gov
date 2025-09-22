# Remaining Populators - Migration Documentation

**Source Files**:
- `cli/modules/network_populator.py`
- `cli/modules/wealth_populator.py`
- `cli/modules/asset_populator.py`
- `cli/modules/career_populator.py`
- `cli/modules/event_populator.py`
- `cli/modules/professional_populator.py`

**Target**: `cli4/modules/[corresponding_populators].py`
**Purpose**: Complete the 9-table architecture with optimized populators

## Architecture Overview

These 6 remaining populators complete the unified database architecture:
1. **Network Populator** → unified_political_networks (committees, fronts, coalitions)
2. **Wealth Populator** → unified_wealth_tracking (TSE asset summaries)
3. **Asset Populator** → politician_assets (individual TSE assets)
4. **Career Populator** → politician_career_history (external mandates)
5. **Event Populator** → politician_events (parliamentary activities)
6. **Professional Populator** → politician_professional_background (professions/occupations)

## Common Patterns Across All Populators

### ✅ Shared Working Logic
1. **Dependency on Politicians Table**: All require unified_politicians as foundation
2. **Politician ID Processing**: Get politician IDs and iterate through them
3. **API Client Integration**: Use DeputadosClient and/or TSEClient
4. **Bulk Insert Pattern**: Collect records and bulk insert at end
5. **Enhanced Logger Integration**: Comprehensive logging and metrics
6. **Error Isolation**: Individual politician failures don't stop batch

### 🐛 Common Issues Across All Populators
1. **Debug Output Spam**: Excessive debug prints that clutter output
2. **Manual Rate Limiting**: Individual sleep() calls instead of centralized
3. **Memory Accumulation**: Store all records in memory before bulk insert
4. **Limited Error Context**: Basic error messages without detailed context
5. **No Progress Tracking**: No visual progress indicators
6. **Repetitive Code**: Similar patterns duplicated across files

## Individual Populator Analysis

### 1. Network Populator (`network_populator.py`)

**Purpose**: Political networks (committees, fronts, coalitions)

**Current Logic**:
```python
for politician in politicians:
    committees = self.deputados_client.get_deputy_committees(deputy_id)
    fronts = self.deputados_client.get_deputy_fronts(deputy_id)
    # Insert immediately for each politician
    self.db.bulk_insert_records('unified_political_networks', politician_networks)
```

**Issues**:
- ✅ **Works Well**: Immediate insertion per politician prevents memory issues
- 🐛 **Issue**: Missing TSE coalition/federation data
- 🐛 **Issue**: No network metadata (size, description)

**Migration Strategy**:
```python
# Add TSE coalition data
coalitions = self.tse_client.get_politician_coalitions(cpf, election_years)

# Add network size calculation
network_record['network_size'] = self._calculate_network_size(network_id, network_type)
```

### 2. Wealth Populator (`wealth_populator.py`)

**Purpose**: Aggregated wealth tracking from TSE asset declarations

**Current Logic**:
```python
for politician in politicians:
    asset_data = self._get_tse_asset_data(sq_candidato)
    yearly_wealth = self._group_assets_by_year(asset_data)
    # Create summary records per year
```

**Issues**:
- ✅ **Works Well**: Proper asset aggregation by year
- 🐛 **Issue**: Hard-coded years [2022, 2024] instead of dynamic calculation
- 🐛 **Issue**: No wealth progression analysis
- 🐛 **Issue**: Currency parsing issues with Brazilian format

**Migration Strategy**:
```python
# Dynamic year calculation
search_years = self._calculate_asset_years_for_politician(politician)

# Enhanced wealth progression
record['wealth_change_percentage'] = self._calculate_wealth_change(current, previous)
record['wealth_growth_rate'] = self._calculate_growth_rate(years_diff, change)

# Improved currency parsing
def _parse_currency_br(self, value_str: str) -> float:
    """Handle Brazilian currency: 1.234.567,89 → 1234567.89"""
    if not value_str:
        return 0.0
    # Remove thousands separators, replace decimal comma
    clean_value = value_str.replace('.', '').replace(',', '.')
    return float(clean_value)
```

### 3. Asset Populator (`asset_populator.py`)

**Purpose**: Individual TSE asset declarations

**Current Logic**:
```python
for politician in politicians:
    assets = self._get_individual_assets(sq_candidato)
    # Map each asset with full details
    asset_record = {
        'asset_sequence': asset['NR_ORDEM_BEM_CANDIDATO'],
        'declared_value': self._parse_currency_value(asset['VR_BEM_CANDIDATO']),
        # ... other asset fields
    }
```

**Issues**:
- ✅ **Works Well**: Complete individual asset mapping
- 🐛 **Issue**: Truncation logic for VARCHAR constraints is crude
- 🐛 **Issue**: Same hard-coded years as wealth populator
- 🐛 **Issue**: No asset verification/validation

**Migration Strategy**:
```python
# Smart truncation with ellipsis preservation
def _smart_truncate(self, text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

# Asset validation
def _validate_asset_data(self, asset: dict) -> dict:
    """Validate and clean asset data"""
    validation_results = {
        'value_reasonable': self._check_reasonable_value(asset['VR_BEM_CANDIDATO']),
        'description_complete': bool(asset.get('DS_BEM_CANDIDATO')),
        'type_valid': asset.get('CD_TIPO_BEM_CANDIDATO') in VALID_ASSET_TYPES
    }
    return validation_results
```

### 4. Career Populator (`career_populator.py`)

**Purpose**: External mandates and career history

**Current Logic**:
```python
mandates = self.deputados_client.get_deputy_external_mandates(deputy_id)
for mandate in mandates:
    career_record = {
        'office_name': mandate.get('cargo'),
        'start_year': int(mandate.get('anoInicio')),
        # ... other mandate fields
    }
```

**Issues**:
- ✅ **Works Well**: Straightforward mandate mapping
- 🐛 **Issue**: Limited to only Deputados external mandates
- 🐛 **Issue**: No career progression analysis
- 🐛 **Issue**: Missing start/end date approximation

**Migration Strategy**:
```python
# Enhanced career analysis
def _analyze_career_progression(self, mandates: List[dict]) -> dict:
    """Analyze career progression patterns"""
    return {
        'career_length_years': self._calculate_career_span(mandates),
        'position_progression': self._detect_progression_pattern(mandates),
        'geographic_mobility': self._analyze_geographic_changes(mandates),
        'party_changes': self._count_party_switches(mandates)
    }

# Date approximation
def _approximate_mandate_dates(self, mandate: dict) -> dict:
    """Create approximate dates from year data"""
    start_year = mandate.get('anoInicio')
    end_year = mandate.get('anoFim')

    return {
        'start_date': f"{start_year}-01-01" if start_year else None,
        'end_date': f"{end_year}-12-31" if end_year else None
    }
```

### 5. Event Populator (`event_populator.py`)

**Purpose**: Parliamentary events and activities

**Current Logic**:
```python
events = self.deputados_client.get_deputy_events(deputy_id, start_date_str, end_date_str)
for event in events:
    event_record = {
        'event_id': str(event.get('id', '')),
        'start_datetime': self._parse_datetime(event.get('dataHoraInicio')),
        'duration_minutes': self._calculate_duration(...),
        # ... other event fields
    }
```

**Issues**:
- ✅ **Works Well**: Complete event data mapping
- ✅ **Works Well**: Duration calculation logic
- 🐛 **Issue**: Fixed days_back parameter (365 days) may be too limiting
- 🐛 **Issue**: Excessive debug output in loops
- 🐛 **Issue**: No event categorization or analysis

**Migration Strategy**:
```python
# Smarter date range calculation
def _calculate_event_date_range(self, politician: dict, days_back: int) -> tuple:
    """Calculate optimal date range for events"""
    # Consider politician's active period
    if politician.get('first_mandate_year'):
        start_date = max(
            datetime.now() - timedelta(days=days_back),
            datetime(politician['first_mandate_year'], 1, 1)
        )
    else:
        start_date = datetime.now() - timedelta(days=days_back)

    return start_date, datetime.now()

# Event categorization
def _categorize_event(self, event: dict) -> str:
    """Categorize events by type and importance"""
    event_type = event.get('descricaoTipo', '').lower()

    if 'sessão' in event_type:
        return 'SESSION'
    elif 'comissão' in event_type:
        return 'COMMITTEE'
    elif 'audiência' in event_type:
        return 'HEARING'
    else:
        return 'OTHER'
```

### 6. Professional Populator (`professional_populator.py`)

**Purpose**: Professional background (professions + occupations)

**Current Logic**:
```python
professions = self.deputados_client.get_deputy_professions(deputy_id)
occupations = self.deputados_client.get_deputy_occupations(deputy_id)

# Map professions
for profession in professions:
    record = {'profession_type': 'PROFESSION', ...}

# Map occupations
for occupation in occupations:
    record = {'profession_type': 'OCCUPATION', ...}
```

**Issues**:
- ✅ **Works Well**: Clear separation of professions vs occupations
- 🐛 **Issue**: No professional background analysis
- 🐛 **Issue**: Missing entity validation (company names, etc.)
- 🐛 **Issue**: No chronological ordering of occupations

**Migration Strategy**:
```python
# Professional background analysis
def _analyze_professional_background(self, professions: List[dict],
                                   occupations: List[dict]) -> dict:
    """Analyze professional background patterns"""
    return {
        'primary_profession': self._determine_primary_profession(professions),
        'career_sectors': self._extract_career_sectors(occupations),
        'private_vs_public': self._analyze_sector_distribution(occupations),
        'career_timeline': self._build_career_timeline(occupations)
    }

# Entity validation
def _validate_entity_name(self, entity_name: str) -> dict:
    """Validate and enrich entity information"""
    if not entity_name:
        return {'valid': False, 'reason': 'missing_name'}

    return {
        'valid': True,
        'normalized_name': self._normalize_entity_name(entity_name),
        'entity_type': self._guess_entity_type(entity_name),  # Government, Private, NGO
        'confidence': self._calculate_confidence(entity_name)
    }
```

## Unified CLI4 Populator Framework

### Base Populator Class
```python
class CLI4BasePopulator:
    """Base class for all CLI4 populators"""

    def __init__(self, db_manager, rate_limiter, logger):
        self.db = db_manager
        self.rate_limiter = rate_limiter
        self.logger = logger
        self.progress_bar = None

    def populate(self, politician_ids: List[int] = None, **kwargs) -> None:
        """Standard population workflow"""
        politicians = self._get_politicians_to_process(politician_ids)

        self._initialize_progress_bar(len(politicians))

        try:
            self._populate_batch(politicians, **kwargs)
        finally:
            self._cleanup_progress_bar()

    def _populate_batch(self, politicians: List[dict], **kwargs) -> None:
        """Override in subclasses"""
        raise NotImplementedError

    def _get_politicians_to_process(self, politician_ids: List[int] = None) -> List[dict]:
        """Standard politician selection logic"""
        if politician_ids:
            return self._get_politicians_by_ids(politician_ids)
        else:
            return self.db.get_politicians_for_processing(active_only=False)

    def _process_politician_with_rate_limiting(self, politician: dict,
                                             api_name: str) -> Any:
        """Standard rate limiting wrapper"""
        wait_time = self.rate_limiter.wait_if_needed(api_name)
        if wait_time > 0:
            self.logger.log_processing("rate_limit", politician['id'], "waiting",
                                     {"wait_time": wait_time, "api": api_name})
            time.sleep(wait_time)
```

### Enhanced Error Handling
```python
class CLI4PopulatorError(Exception):
    """Base exception for populator errors"""
    pass

class APIError(CLI4PopulatorError):
    """API-related errors"""
    pass

class DataValidationError(CLI4PopulatorError):
    """Data validation errors"""
    pass

def safe_populate_politician(func):
    """Decorator for safe politician processing"""
    def wrapper(self, politician: dict, *args, **kwargs):
        try:
            return func(self, politician, *args, **kwargs)
        except APIError as e:
            self.logger.log_processing("politician", politician['id'], "error",
                                     {"error_type": "api", "error": str(e)})
            return None
        except DataValidationError as e:
            self.logger.log_processing("politician", politician['id'], "error",
                                     {"error_type": "validation", "error": str(e)})
            return None
        except Exception as e:
            self.logger.log_processing("politician", politician['id'], "error",
                                     {"error_type": "unexpected", "error": str(e)})
            return None
    return wrapper
```

## Testing Strategy for All Populators

### Common Test Patterns
```python
class BasePopulatorTest:
    """Base test class for all populators"""

    def test_population_workflow(self):
        """Test complete population workflow"""
        # Setup test politicians
        test_politicians = self.create_test_politicians(count=5)

        # Run population
        populator = self.create_populator()
        populator.populate(politician_ids=[p['id'] for p in test_politicians])

        # Verify results
        assert self.get_table_count() > 0

    def test_error_isolation(self):
        """Test that individual politician errors don't stop batch"""
        # Include one politician that will cause error
        test_politicians = self.create_test_politicians_with_error()

        populator = self.create_populator()
        populator.populate(politician_ids=[p['id'] for p in test_politicians])

        # Should have processed the valid politicians
        assert self.get_table_count() >= len(test_politicians) - 1

    def test_rate_limiting_integration(self):
        """Test rate limiting integration"""
        populator = self.create_populator()

        # Mock rate limiter to track calls
        with patch.object(populator.rate_limiter, 'wait_if_needed') as mock_wait:
            mock_wait.return_value = 0.1

            populator.populate(politician_ids=[1, 2, 3])

            # Should have called rate limiter
            assert mock_wait.call_count > 0
```

## Success Criteria for All Populators
1. ✅ Unified base class with common functionality
2. ✅ Enhanced error handling and isolation
3. ✅ Centralized rate limiting integration
4. ✅ Progress tracking and visual indicators
5. ✅ Memory-efficient streaming processing
6. ✅ Comprehensive logging and metrics
7. ✅ Dynamic date/time range calculations
8. ✅ Data validation and quality checks
9. ✅ Consistent bulk insert patterns
10. ✅ Complete field mapping preservation

This unified approach ensures all remaining populators follow consistent patterns while fixing common issues and adding enhancements for reliability and performance.