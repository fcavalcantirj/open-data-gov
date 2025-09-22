# Architecture Decision Report - Brazilian Political Data System
**Date:** 2025-09-19
**Status:** APPROVED for Implementation
**Decision:** Pre-Crawl + Cache Strategy (v0)

## Executive Summary

After analyzing system requirements and data access patterns for Brazilian political transparency, we recommend implementing a **pre-crawl architecture** that builds a comprehensive PostgreSQL database updated daily via async crawlers, rather than real-time API calls.

## Context & Problem

We have successfully implemented a proof-of-concept corruption detection system that integrates 6 Brazilian government data sources:
- Câmara dos Deputados (CEAP expenses)
- Portal da Transparência (sanctions, contracts)
- TSE (electoral data)
- TCU (audit records)
- Senado Federal (senate data)
- DataJud (judicial records)

**Current State:** Manual report generation with real-time API calls
**Goal:** Scalable system serving fast, comprehensive political transparency reports

## Decision: Pre-Crawl + Cache Strategy

### Why Pre-Crawl Wins

1. **Historical Pattern Detection**
   - Corruption emerges over time through spending patterns
   - Need trend analysis across multiple years/politicians
   - Relationship mapping requires structured historical data

2. **Performance Requirements**
   - Citizens expect instant responses when checking politicians
   - Complex analytics (cross-politician networks) need pre-computed data
   - Real-time API calls too slow for user-facing applications

3. **Reliability & Availability**
   - External government APIs frequently fail or rate-limit
   - Our transparency system must always be available
   - Cached data ensures consistent service

4. **Advanced Analytics**
   - Cross-politician/company relationship analysis
   - Statistical anomaly detection across full dataset
   - Network analysis of sanctioned companies

5. **API Rate Limiting**
   - Batch processing avoids throttling
   - Respectful of government infrastructure
   - Allows comprehensive data collection

## Database Architecture

### Core Tables

```sql
-- Politicians
politicians (
  id SERIAL PRIMARY KEY,
  camara_id INTEGER UNIQUE,
  name VARCHAR(255),
  cpf VARCHAR(14),
  party VARCHAR(10),
  state VARCHAR(2),
  photo_url TEXT,
  last_updated TIMESTAMP
);

--array of previous parties?

-- Companies & Entities
entities (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(18) UNIQUE,
  name VARCHAR(255),
  entity_type VARCHAR(50), -- 'company', 'person', etc
  last_updated TIMESTAMP
);

-- Sanctions (from Portal Transparência)
sanctions (
  id SERIAL PRIMARY KEY,
  entity_id INTEGER REFERENCES entities(id),
  sanction_type VARCHAR(100),
  start_date DATE,
  end_date DATE,
  amount DECIMAL(15,2),
  source_url TEXT,
  last_updated TIMESTAMP
);

-- Expenses (CEAP data)
expenses (
  id SERIAL PRIMARY KEY,
  politician_id INTEGER REFERENCES politicians(id),
  entity_id INTEGER REFERENCES entities(id),
  date DATE,
  amount DECIMAL(10,2),
  description TEXT,
  document_url TEXT,
  year INTEGER,
  month INTEGER,
  last_updated TIMESTAMP
);

-- Risk Scores (calculated daily)
risk_scores (
  id SERIAL PRIMARY KEY,
  politician_id INTEGER REFERENCES politicians(id),
  calculation_date DATE,
  final_score DECIMAL(5,4),
  financial_score DECIMAL(5,4),
  network_score DECIMAL(5,4),
  legal_score DECIMAL(5,4),
  transparency_score DECIMAL(5,4),
  statistical_score DECIMAL(5,4),
  confidence DECIMAL(3,2),
  metadata JSONB -- store full breakdown
);
```

## Pipeline Architecture

```
Daily Crawler → Data Lake → Processing → PostgreSQL → API → Frontend
     ↓             ↓           ↓           ↓        ↓        ↓
   6 APIs      Raw JSON    Enrichment   Structured  Fast   Beautiful
              Storage      Analytics    Relationships Queries Reports
```

### Pipeline Components

1. **Daily Crawl (4am)**: Async collection from all 6 APIs for all active politicians
2. **Data Processing**: Clean, dedupe, entity resolution, relationship mapping
3. **Risk Calculation**: Run transparent scoring system with full historical context
4. **API Layer**: Fast JSON endpoints for frontend consumption
5. **Frontend**: Beautiful reports (like ultimate_unified_report_20250919_192738.html)

## Implementation Phases

### Phase 1: Foundation (Week 1)
- PostgreSQL schema setup with DigitalOcean connection
- Basic crawler for single politician (Arthur Lira test case)
- Data ingestion pipeline for CEAP + sanctions
- Basic risk scoring implementation

### Phase 2: Scale (Week 2-3)
- Extend to all active politicians (~513 deputies)
- All 6 data sources integrated
- Complete risk scoring system
- Basic API endpoints

### Phase 3: Analytics & Frontend (Week 4+)
- Advanced relationship analysis
- Interactive frontend
- Real-time updates for new data
- Public API for developers

## Technical Specifications

**Database:** PostgreSQL (DigitalOcean)
**Connection:** ``

**Data Update Frequency:**
- CEAP expenses: Daily
- Sanctions: Weekly
- TSE declarations: Election periods
- TCU records: Weekly
- Judicial data: Weekly

**API Response Time Target:** <200ms for politician lookup
**Data Freshness:** Max 24 hours old for critical data

## Success Metrics

1. **Performance**: Sub-200ms API responses
2. **Coverage**: 100% active federal politicians
3. **Accuracy**: >95% data quality scores
4. **Availability**: 99.9% uptime
5. **Impact**: Measurable increase in transparency engagement

## Risk Mitigation

**Data Quality**: Implement validation checks and confidence scoring
**API Failures**: Graceful degradation, retry mechanisms
**Storage Costs**: Data retention policies, archival strategies
**Legal Compliance**: Full attribution, transparent methodology

## Current Status

✅ **COMPLETED:**
- Proof-of-concept system working
- 6 data source integrations validated
- Transparent risk scoring system implemented
- Ultimate unified report template (near-perfect)
- Real corruption detected (Arthur Lira case)

🔄 **NEXT STEPS:**
1. Set up PostgreSQL schema
2. Implement basic crawler for Arthur Lira
3. Test data pipeline end-to-end
4. Scale to multiple politicians

## Conclusion

The pre-crawl strategy provides the best foundation for a scalable, reliable, and comprehensive Brazilian political transparency system. This approach enables sophisticated analytics while ensuring fast, dependable access for citizens.

**Recommended Action:** Proceed with Phase 1 implementation immediately.

---
*This report documents the architectural decision for the open-data-gov Brazilian political transparency project.*