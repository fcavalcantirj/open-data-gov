# TODO: Enhanced Metrics Quality Issues

## 🚨 CRITICAL: Family Network Detection

**Status**: DISABLED - All values set to -1 (unreliable)

**Current Problem**:
- Simple surname matching produces massive false positives
- Example: All 51 politicians with "SILVA" show 30 family members (clearly wrong)
- No validation of actual family relationships

**Required Fix**:
1. Multi-factor family correlation:
   - Birth location matching (same municipality + surname)
   - Age/generation analysis (parent/child age gaps)
   - Multiple surname matching (not just last name)
   - Direct indicators (FILHO, JUNIOR, NETO)
   - Special handling for common surnames (SILVA, SANTOS, OLIVEIRA)

2. Additional data sources needed:
   - TSE parental names (NM_PAI_CANDIDATO, NM_MAE_CANDIDATO) - not currently in database
   - Portal da Transparência nepotism registry
   - Electoral coalition patterns (families often run together)

**Fields Affected**:
- `family_senators_count` → Currently -1 (TODO)
- `family_deputies_count` → Currently -1 (TODO)
- `family_parties_senado` → Currently "TODO"
- `family_parties_camara` → Currently "TODO"

## ✅ RELIABLE FIELDS (Keep using)

- **Corruption Detection**: Working correctly
  - `corruption_risk_score`
  - `tcu_disqualifications_*`
  - `sanctioned_vendors_*`

- **Career Metrics**: Working correctly
  - `career_*` fields
  - `professional_background_*`
  - `parliamentary_*`

- **Wealth Tracking**: Working correctly
  - `wealth_*` fields
  - `asset_*` fields

- **Electoral**: Working correctly
  - `electoral_success_rate`
  - `first_election_year`
  - `last_election_year`
  - `total_elections`

## 📋 Data Quality Principle

**Better to have fewer high-quality fields than many low-quality fields**

Convention: `-1` in numeric fields = TODO/unreliable data that needs fixing