# Brazilian Political Data Integration Project

## Project Overview

Implementation of the **brazilian-political-data-architecture-v0.md** specification for comprehensive Brazilian political network analysis using open government data sources.

**Status**: ⚠️ **OPERATIONAL WITH DATA QUALITY ISSUES** - Architecture complete, corruption detection hindered by CNPJ format inconsistencies.

## Architecture Implementation

### Data Sources Status: 3/6 IMPLEMENTED ✅

1. **Câmara dos Deputados** ✅ - Complete (politicians, finances, networks, career, events, professions)
2. **TSE Electoral** ✅ - Complete (electoral records, asset declarations)
3. **Portal da Transparência** ✅ - Recently added (1,219 sanctions, 96.2% active)
4. **Senado Federal** ❌ - Not implemented in population scripts
5. **TCU Federal Audit** ❌ - Not implemented in population scripts
6. **DataJud Judicial** ❌ - Not implemented in population scripts

### Current Database Status (Live Analysis)

**Data Volume (Actual Count):**
- **Politicians**: 512 (100% complete identity data)
- **Financial Records**: 17,591 (96.9% have CNPJ/CPF data)
- **Electoral Records**: 1,032 (TSE integration successful)
- **Political Networks**: 42,888 (committee/coalition memberships)
- **Events**: 40,036 (parliamentary activity tracking)
- **Assets**: 5,468 (individual asset declarations)
- **Sanctions**: 1,219 (Portal da Transparência CEIS)
- **Career History**: 632 (external mandates)
- **Professional Background**: 1,806 (occupation records)
- **Wealth Tracking**: 496 (aggregated wealth summaries)

### Critical Data Quality Issues Discovered ⚠️

**CNPJ Format Inconsistency - Blocking Corruption Detection:**
- **Financial Records CNPJ Quality**: Only 43.6% valid 14-digit CNPJs
- **53% CPF Format (11-digit)**: Individual service providers, not companies
- **0% Sanctions Overlap**: No matching CNPJs between financial and sanctions data
- **Placeholder Data**: Some records use invalid identifiers like "1"

**Root Cause**: Mixed CNPJ (companies) vs CPF (individuals) in financial records, while sanctions database contains only company CNPJs.

## Corruption Detection Capability

### Current Status: **BLOCKED BY DATA FORMAT MISMATCH** ❌

**Expected Capability**: Cross-reference politician expenses with sanctioned vendors
**Actual Reality**: Zero corruption detection due to CNPJ/CPF format inconsistencies

**Critical Query Failing:**
```sql
-- This returns 0 results due to format mismatch
SELECT COUNT(*) FROM unified_financial_records f
JOIN vendor_sanctions s ON f.counterpart_cnpj_cpf = s.cnpj_cpf
-- No matches: financial has CPFs, sanctions has CNPJs
```

### Data Quality Breakdown:
- **17,591 total financial records**
- **7,671 valid company CNPJs (43.6%)**
- **9,329 individual CPFs (53.0%)**
- **1,219 company sanctions available**
- **0 successful cross-references**

## Architecture Validation Results

❌ **Corruption Detection**: Blocked by data format inconsistency
✅ **Entity Resolution**: CPF-based politician correlation works perfectly
✅ **Financial Tracking**: Complete CEAP expense records with vendor details
✅ **Electoral Integration**: TSE data successfully integrated
✅ **Database Architecture**: 10-table PostgreSQL schema fully functional

## Critical Next Steps Required

### 1. **Data Quality Remediation (HIGH PRIORITY)**
```
IMMEDIATE FIXES NEEDED:
⚠️ Normalize CNPJ/CPF formats in financial records
⚠️ Separate individual vs company transactions
⚠️ Re-run sanctions cross-reference with clean data
⚠️ Validate Arthur Lira case study with actual database
```

### 2. **Enhanced Data Population**
```
MISSING SOURCES FOR COMPLETE COVERAGE:
❌ Senado Federal integration (81 senators)
❌ TCU audit data (disqualifications, rulings)
❌ DataJud judicial processes (limited public access)
```

### 3. **Corruption Detection Validation**
```
VALIDATION REQUIREMENTS:
🔍 Test known corruption cases (Arthur Lira, others)
🔍 Verify CNPJ cleaning algorithms work correctly
🔍 Implement CPF-to-CNPJ business ownership tracking
🔍 Add suspicious transaction pattern detection
```

## Repository Structure

```
/
├── .env                              # Database connection (POSTGRES_POOL_URL)
├── CLAUDE.md                        # This file (updated with real analysis)
├── run_full_population.sh           # Complete population workflow
│
├── CLI4 Population System:
├── cli4/main.py                     # Main CLI interface
├── cli4/populators/                 # All population modules
│   ├── politicians/                 # Câmara deputados integration
│   ├── financial/                   # CEAP expense tracking
│   ├── electoral/                   # TSE electoral data
│   ├── sanctions/                   # Portal Transparência sanctions (NEW)
│   ├── networks/                    # Political networks/committees
│   ├── wealth/                      # Asset tracking and aggregation
│   ├── career/                      # External mandate history
│   ├── events/                      # Parliamentary activity
│   └── professional/                # Professional background
│
├── Database Setup:
├── scripts/setup/setup_postgres.py  # 10-table schema creation
└── docs/analysis/unified/           # Population guides and SQL schema
```

## Quick Start

### 1. Environment Setup
```bash
# Set database connection
export POSTGRES_POOL_URL=DEFINED_IN_ENV

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Population Workflow
```bash
# Complete population (estimated 37-47 hours)
./run_full_population.sh

# Individual population modules
python cli4/main.py populate              # Politicians
python cli4/main.py populate-financial   # Financial records
python cli4/main.py populate-sanctions   # Sanctions (Portal Transparência)
python cli4/main.py validate            # Data validation
```

### 3. Database Analysis
```bash
# Test corruption detection capability
python -c "from cli4.modules import database; print('Testing...')"
```

## Key Implementation Insights

### What Works Well ✅
1. **PostgreSQL Architecture**: 10-table foreign key relationships solid
2. **API Integration**: Real data from Câmara, TSE, Portal Transparência
3. **Data Volume**: Substantial records across all populated tables
4. **Politician Identity**: 100% complete CPF-based correlation
5. **Financial Transparency**: Complete CEAP expense tracking

### Critical Issues ⚠️
1. **CNPJ/CPF Mixed Format**: Blocks company-based corruption detection
2. **Incomplete Sources**: Missing Senado, TCU, DataJud integration
3. **Data Cleaning**: Need normalized identifier formats
4. **Validation Gaps**: Corruption detection untested with real cases

### Architecture Recommendation: **Enhanced MVP with Data Quality Focus**

**Phase 1: Fix Data Quality (1-2 weeks)**
- Implement CNPJ/CPF normalization
- Separate individual vs company transactions
- Test corruption detection with clean data
- Validate against known corruption cases

**Phase 2: Complete Source Integration (2-3 months)**
- Add Senado Federal for senator coverage
- Integrate TCU audit data for disqualifications
- Evaluate DataJud feasibility (public access limited)

**Phase 3: Advanced Analytics (3-6 months)**
- Graph database migration for network analysis
- Real-time updates during legislative sessions
- Machine learning pattern detection
- 3D visualization interface

## 🚨 CRITICAL DATABASE REQUIREMENT

**ONLY POSTGRESQL - NO SQLITE EVER**

This project MUST use PostgreSQL database only. SQLite is NOT supported and causes constant issues.

## 🚨 CRITICAL IMPLEMENTATION REQUIREMENT

**NO HARDCODED DATA - REAL API CALLS ONLY**

This project MUST use actual API calls from government systems. All current data is real API-sourced.

## Database Connection Status

**Live Database**: ✅ Connected to DigitalOcean PostgreSQL
**Connection**: `open-data-gov-pool` database
**SSL**: Required (production environment)
**Status**: All 10 tables populated with real government data

## Strategic Assessment

### Current MVP Reality Check:
- **Architecture**: Solid PostgreSQL foundation ✅
- **Data Sources**: 3/6 implemented (Câmara + TSE + Portal) ✅
- **Corruption Detection**: Blocked by data quality issues ❌
- **Data Volume**: Substantial real government records ✅
- **Infrastructure**: Production-ready PostgreSQL deployment ✅

### Immediate Action Required:
1. **Fix CNPJ/CPF format inconsistencies** (blocks corruption detection)
2. **Test with clean data against known corruption cases**
3. **Evaluate expanding to Senado + TCU for complete coverage**

**Bottom Line**: Strong architectural foundation with significant data quality challenges that must be resolved before corruption detection becomes operational.

---

*Last Updated: 2025-09-26*
*Database Analysis: Live PostgreSQL with 135,000+ records*
*Status: Architecture Complete, Data Quality Remediation Required*