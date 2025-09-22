# Validation Manager - Migration Documentation

**Source File**: `cli/modules/validation_manager.py`
**Target**: `cli4/modules/validation_manager.py`
**Purpose**: Data integrity validation across all 9 tables

## Core Logic Analysis

### Current Architecture
```python
class ValidationManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def validate_all(self, fix: bool = False) -> None:
        """Validate all tables"""
        tables = [
            'unified_politicians',
            'unified_financial_records',
            'financial_counterparts',
            # ... all 9 tables
        ]

    def validate_table(self, table_name: str, fix: bool = False) -> List[Dict[str, Any]]:
        """Validate specific table"""
        # Route to specific validation method
```

### Validation Categories

#### 1. Politicians Table Validation
```python
def _validate_politicians(self, fix: bool) -> List[Dict[str, Any]]:
    # Check for missing CPFs
    missing_cpf = "SELECT id, nome_civil FROM unified_politicians WHERE cpf IS NULL"

    # Check for invalid CPFs
    invalid_cpf = "SELECT id, cpf FROM unified_politicians WHERE LENGTH(cpf) != 11"

    # Check for duplicate CPFs
    duplicates = "SELECT cpf, COUNT(*) FROM unified_politicians GROUP BY cpf HAVING COUNT(*) > 1"
```

#### 2. Financial Records Validation
```python
def _validate_financial_records(self, fix: bool) -> List[Dict[str, Any]]:
    # Check for invalid amounts
    invalid_amounts = "SELECT id FROM unified_financial_records WHERE amount < 0"

    # Check for missing counterparts
    missing_counterparts = "WHERE counterpart_cnpj_cpf IS NULL"

    # Check for orphaned records
    orphaned = "LEFT JOIN unified_politicians p ON fr.politician_id = p.id WHERE p.id IS NULL"
```

#### 3. Counterparts Validation
```python
def _validate_counterparts(self, fix: bool) -> List[Dict[str, Any]]:
    # Check for invalid CNPJ/CPF lengths
    invalid_ids = "WHERE LENGTH(cnpj_cpf) NOT IN (11, 14)"

    # Check for missing names
    missing_names = "WHERE name IS NULL OR name = ''"
```

## Identified Issues

### 🐛 Issue #1: Limited Validation Scope
**Problem**: Only validates 3 tables out of 9
```python
# Only validates: politicians, financial_records, counterparts
# Missing: networks, wealth, assets, career, events, professional
```
**Impact**: 6 tables have no data quality validation
**Fix**: Add validation for all 9 tables

### 🐛 Issue #2: No Cross-Table Validation
**Problem**: Validates tables individually, not relationships
```python
# Missing validations:
# - TSE correlation completeness
# - Financial record totals vs individual assets
# - Timeline consistency across tables
# - Network membership consistency
```
**Fix**: Add comprehensive relationship validation

### 🐛 Issue #3: Basic Fix Functionality
**Problem**: Fix parameter is accepted but limited fixes implemented
```python
# No actual fix implementations
if fix:
    # TODO: Implement fixes
    pass
```
**Fix**: Implement comprehensive data fixing capabilities

### 🐛 Issue #4: No Performance Validation
**Problem**: No validation of database performance or optimization
```python
# Missing:
# - Index usage validation
# - Query performance checks
# - Table size monitoring
# - Constraint validation
```
**Fix**: Add performance and optimization validation

### 🐛 Issue #5: Limited Reporting
**Problem**: Basic text output, no structured reporting
```python
def generate_validation_report(self) -> str:
    # Basic text report only
    report.append("# DATA VALIDATION REPORT")
```
**Fix**: JSON/structured output for automated processing

## CLI4 Enhanced Validation Strategy

### Comprehensive 9-Table Validation
```python
class CLI4ValidationManager:
    """Enhanced validation manager for complete 9-table architecture"""

    def __init__(self, db_manager, logger):
        self.db = db_manager
        self.logger = logger
        self.validation_rules = self._load_validation_rules()

    VALIDATION_TABLES = [
        'unified_politicians',           # Foundation
        'financial_counterparts',        # Vendor/donor registry
        'unified_financial_records',     # All transactions
        'unified_political_networks',    # Committees, coalitions
        'unified_wealth_tracking',       # Wealth summaries
        'politician_assets',            # Individual assets
        'politician_career_history',    # External mandates
        'politician_events',            # Parliamentary activities
        'politician_professional_background'  # Professions/occupations
    ]

    def validate_comprehensive(self, fix_mode: str = "report") -> dict:
        """
        Comprehensive validation with multiple fix modes
        fix_mode: "report", "auto_fix", "interactive"
        """
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'tables': {},
            'cross_table': {},
            'performance': {},
            'summary': {}
        }

        # 1. Individual table validation
        for table in self.VALIDATION_TABLES:
            validation_results['tables'][table] = self._validate_table_comprehensive(table, fix_mode)

        # 2. Cross-table relationship validation
        validation_results['cross_table'] = self._validate_relationships(fix_mode)

        # 3. Performance and optimization validation
        validation_results['performance'] = self._validate_performance()

        # 4. Generate summary
        validation_results['summary'] = self._generate_summary(validation_results)

        return validation_results
```

### Enhanced Table-Specific Validation

#### Politicians Table (Enhanced)
```python
def _validate_politicians_comprehensive(self, fix_mode: str) -> dict:
    """Comprehensive politician table validation"""
    issues = []

    # Basic validations (existing)
    issues.extend(self._validate_cpf_completeness(fix_mode))
    issues.extend(self._validate_cpf_format(fix_mode))
    issues.extend(self._validate_cpf_duplicates(fix_mode))

    # Enhanced validations
    issues.extend(self._validate_tse_correlation_rate(fix_mode))
    issues.extend(self._validate_demographic_completeness(fix_mode))
    issues.extend(self._validate_timeline_consistency(fix_mode))
    issues.extend(self._validate_political_status_logic(fix_mode))

    return {
        'table': 'unified_politicians',
        'total_issues': len(issues),
        'issues': issues,
        'health_score': self._calculate_health_score(issues)
    }

def _validate_tse_correlation_rate(self, fix_mode: str) -> List[dict]:
    """Validate TSE correlation success rate"""
    total_politicians = self.db.get_table_count('unified_politicians')
    tse_linked = self.db.execute_query(
        "SELECT COUNT(*) as count FROM unified_politicians WHERE tse_linked = TRUE"
    )[0]['count']

    correlation_rate = (tse_linked / total_politicians * 100) if total_politicians > 0 else 0

    if correlation_rate < 80:  # Expected 80%+ correlation rate
        issue = {
            'type': 'tse_correlation_low',
            'severity': 'WARNING',
            'description': f'TSE correlation rate: {correlation_rate:.1f}% (expected >80%)',
            'affected_records': total_politicians - tse_linked,
            'fix_available': fix_mode != "report"
        }

        if fix_mode == "auto_fix":
            self._fix_tse_correlation_gaps()

        return [issue]

    return []
```

#### New Table Validations

#### Political Networks Validation
```python
def _validate_political_networks(self, fix_mode: str) -> dict:
    """Validate political networks table"""
    issues = []

    # Network consistency
    issues.extend(self._validate_network_membership_consistency())
    issues.extend(self._validate_network_timeline_logic())
    issues.extend(self._validate_network_role_completeness())

    # Data quality
    issues.extend(self._validate_network_name_completeness())
    issues.extend(self._validate_source_system_consistency())

    return {
        'table': 'unified_political_networks',
        'total_issues': len(issues),
        'issues': issues
    }

def _validate_network_timeline_logic(self) -> List[dict]:
    """Validate network timeline logic"""
    invalid_timelines = self.db.execute_query("""
        SELECT id, network_name, start_date, end_date
        FROM unified_political_networks
        WHERE start_date IS NOT NULL
          AND end_date IS NOT NULL
          AND start_date > end_date
    """)

    if invalid_timelines:
        return [{
            'type': 'invalid_timeline',
            'severity': 'ERROR',
            'description': f'{len(invalid_timelines)} networks with invalid timelines (start > end)',
            'affected_records': len(invalid_timelines),
            'sample_data': invalid_timelines[:3]
        }]

    return []
```

#### Wealth and Assets Validation
```python
def _validate_wealth_assets_consistency(self, fix_mode: str) -> List[dict]:
    """Cross-validate wealth tracking vs individual assets"""
    issues = []

    # Check wealth totals vs individual asset sums
    inconsistent_wealth = self.db.execute_query("""
        SELECT
            wt.politician_id,
            wt.year,
            wt.total_declared_wealth,
            SUM(pa.declared_value) as individual_assets_sum
        FROM unified_wealth_tracking wt
        LEFT JOIN politician_assets pa ON wt.politician_id = pa.politician_id
                                       AND wt.year = pa.declaration_year
        GROUP BY wt.politician_id, wt.year, wt.total_declared_wealth
        HAVING ABS(wt.total_declared_wealth - COALESCE(SUM(pa.declared_value), 0)) > 1000
    """)

    if inconsistent_wealth:
        issues.append({
            'type': 'wealth_asset_mismatch',
            'severity': 'WARNING',
            'description': f'{len(inconsistent_wealth)} politicians with wealth/asset sum mismatches',
            'affected_records': len(inconsistent_wealth),
            'sample_data': inconsistent_wealth[:3]
        })

    return issues
```

### Cross-Table Relationship Validation
```python
def _validate_relationships(self, fix_mode: str) -> dict:
    """Validate relationships across all tables"""
    relationship_issues = {}

    # 1. Politician relationship consistency
    relationship_issues['politician_references'] = self._validate_politician_references()

    # 2. Financial relationship consistency
    relationship_issues['financial_consistency'] = self._validate_financial_relationships()

    # 3. Timeline consistency across tables
    relationship_issues['timeline_consistency'] = self._validate_cross_table_timelines()

    # 4. Source system consistency
    relationship_issues['source_consistency'] = self._validate_source_system_references()

    return relationship_issues

def _validate_politician_references(self) -> List[dict]:
    """Validate all foreign key references to politicians table"""
    issues = []

    dependent_tables = [
        'unified_financial_records',
        'unified_political_networks',
        'unified_wealth_tracking',
        'politician_assets',
        'politician_career_history',
        'politician_events',
        'politician_professional_background'
    ]

    for table in dependent_tables:
        orphaned = self.db.execute_query(f"""
            SELECT COUNT(*) as count
            FROM {table} t
            LEFT JOIN unified_politicians p ON t.politician_id = p.id
            WHERE p.id IS NULL
        """)[0]['count']

        if orphaned > 0:
            issues.append({
                'type': 'orphaned_records',
                'table': table,
                'severity': 'ERROR',
                'description': f'{orphaned} orphaned records in {table}',
                'affected_records': orphaned
            })

    return issues
```

### Performance Validation
```python
def _validate_performance(self) -> dict:
    """Validate database performance and optimization"""
    performance_results = {}

    # 1. Index usage validation
    performance_results['indexes'] = self._validate_index_usage()

    # 2. Query performance checks
    performance_results['query_performance'] = self._validate_query_performance()

    # 3. Table size monitoring
    performance_results['table_sizes'] = self._validate_table_sizes()

    # 4. Foreign key constraint validation
    performance_results['constraints'] = self._validate_constraints()

    return performance_results

def _validate_index_usage(self) -> dict:
    """Validate critical indexes exist and are used"""
    critical_indexes = [
        ('unified_politicians', 'cpf'),
        ('unified_politicians', 'deputy_id'),
        ('unified_financial_records', 'politician_id'),
        ('unified_financial_records', 'counterpart_cnpj_cpf'),
        ('financial_counterparts', 'cnpj_cpf'),
        # ... all critical indexes
    ]

    missing_indexes = []
    for table, column in critical_indexes:
        if not self._index_exists(table, column):
            missing_indexes.append(f"{table}.{column}")

    return {
        'missing_critical_indexes': missing_indexes,
        'total_missing': len(missing_indexes),
        'performance_impact': 'HIGH' if missing_indexes else 'NONE'
    }
```

### Auto-Fix Capabilities
```python
def _auto_fix_common_issues(self, issues: List[dict]) -> dict:
    """Automatically fix common, safe issues"""
    fix_results = {
        'attempted': 0,
        'successful': 0,
        'failed': 0,
        'details': []
    }

    for issue in issues:
        if issue['type'] in SAFE_AUTO_FIX_TYPES:
            fix_results['attempted'] += 1

            try:
                success = self._apply_fix(issue)
                if success:
                    fix_results['successful'] += 1
                else:
                    fix_results['failed'] += 1

                fix_results['details'].append({
                    'issue_type': issue['type'],
                    'status': 'success' if success else 'failed',
                    'description': issue['description']
                })

            except Exception as e:
                fix_results['failed'] += 1
                fix_results['details'].append({
                    'issue_type': issue['type'],
                    'status': 'error',
                    'error': str(e)
                })

    return fix_results

SAFE_AUTO_FIX_TYPES = [
    'missing_indexes',
    'inconsistent_nulls',
    'format_standardization',
    'orphaned_cleanup'  # Only if confirmed safe
]
```

### Structured Reporting
```python
def generate_structured_report(self, validation_results: dict) -> dict:
    """Generate structured validation report"""
    report = {
        'metadata': {
            'timestamp': validation_results['timestamp'],
            'database_type': self.db.db_type,
            'total_tables_validated': len(validation_results['tables']),
            'validation_version': '4.0'
        },
        'summary': {
            'overall_health_score': self._calculate_overall_health_score(validation_results),
            'total_issues': sum(table['total_issues'] for table in validation_results['tables'].values()),
            'critical_issues': self._count_critical_issues(validation_results),
            'warnings': self._count_warnings(validation_results),
            'performance_score': self._calculate_performance_score(validation_results['performance'])
        },
        'recommendations': self._generate_recommendations(validation_results),
        'detailed_results': validation_results
    }

    return report

def _generate_recommendations(self, validation_results: dict) -> List[dict]:
    """Generate actionable recommendations"""
    recommendations = []

    # Performance recommendations
    if validation_results['performance']['indexes']['total_missing'] > 0:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'performance',
            'action': 'Add missing indexes',
            'impact': 'Significant query performance improvement',
            'commands': self._generate_index_creation_commands(validation_results['performance']['indexes'])
        })

    # Data quality recommendations
    total_issues = sum(table['total_issues'] for table in validation_results['tables'].values())
    if total_issues > 100:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'data_quality',
            'action': 'Address data quality issues',
            'impact': 'Improved data reliability and analysis accuracy',
            'auto_fix_available': True
        })

    return recommendations
```

## Testing Strategy

### Validation Coverage Tests
```python
def test_all_tables_validated():
    """Ensure all 9 tables have validation coverage"""
    validator = CLI4ValidationManager(test_db, test_logger)
    results = validator.validate_comprehensive()

    # Should validate all 9 tables
    assert len(results['tables']) == 9
    for table in CLI4ValidationManager.VALIDATION_TABLES:
        assert table in results['tables']

def test_cross_table_validation():
    """Test cross-table relationship validation"""
    validator = CLI4ValidationManager(test_db, test_logger)

    # Create test data with known relationship issues
    create_test_data_with_orphans()

    results = validator.validate_comprehensive()

    # Should detect orphaned records
    assert len(results['cross_table']['politician_references']) > 0

def test_auto_fix_functionality():
    """Test auto-fix capabilities"""
    validator = CLI4ValidationManager(test_db, test_logger)

    # Create test data with fixable issues
    create_test_data_with_fixable_issues()

    results = validator.validate_comprehensive(fix_mode="auto_fix")

    # Should have attempted and succeeded fixes
    assert results['summary']['fixes_attempted'] > 0
    assert results['summary']['fixes_successful'] > 0
```

### Performance Tests
```python
def test_validation_performance():
    """Test validation performance on large datasets"""
    validator = CLI4ValidationManager(large_test_db, test_logger)

    start_time = time.time()
    results = validator.validate_comprehensive()
    elapsed = time.time() - start_time

    # Should complete within reasonable time
    assert elapsed < 300  # 5 minutes for large dataset
    assert results['metadata']['total_tables_validated'] == 9
```

## Success Criteria
1. ✅ All 9 tables have comprehensive validation coverage
2. ✅ Cross-table relationship validation implemented
3. ✅ Performance and optimization validation included
4. ✅ Auto-fix capabilities for safe, common issues
5. ✅ Structured reporting with actionable recommendations
6. ✅ Health scoring and trend analysis
7. ✅ Integration with CLI4 logging and error handling
8. ✅ Fast validation performance on large datasets

This enhanced validation manager provides comprehensive data quality assurance across the entire unified database architecture.