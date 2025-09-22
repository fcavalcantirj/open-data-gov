# DATA FIELDS MAPPING - TSE ELECTORAL DATA LAKE

## AVAILABLE FIELDS FOR CORRELATION

### 🔑 PRIMARY IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **NR_CPF_CANDIDATO** | Candidate data | 11 digits | Deputados, Portal Transparência, TCU, DataJud | Universal person identifier |
| **NR_CANDIDATO** | Candidate data | Variable | **FILLS DEPUTADOS GAP** | Electoral number missing from deputados |
| **NR_TITULO_ELEITORAL_CANDIDATO** | Candidate data | 12 digits | Voter registration databases | Electoral validation |
| **SQ_CANDIDATO** | Candidate data | Integer | Internal linking to assets/finance | Primary key for TSE ecosystem |
| **NM_CANDIDATO** | Candidate data | String | All systems (fuzzy) | Legal name matching |
| **NM_URNA_CANDIDATO** | Candidate data | String | Electoral materials | Ballot name correlation |
| **DS_EMAIL** | Candidate data | String | Contact databases | Communication tracking |

### 📍 GEOGRAPHIC IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **SG_UF** | All data | 2 letters | Deputados state, IBGE | State-level analysis |
| **SG_UE** | All data | TSE code | Electoral unit mapping | Constituency tracking |
| **NM_UE** | All data | String | Municipality names | Local political base |
| **SG_UF_NASCIMENTO** | Candidate data | 2 letters | Birth location analysis | Migration patterns |

### 🏛️ POLITICAL IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **SG_PARTIDO** | Candidate data | String | Deputados party, Senado | Party affiliation tracking |
| **NR_PARTIDO** | Candidate data | Integer | Party registration | Numerical party ID |
| **NM_PARTIDO** | Candidate data | String | Full party names | Party evolution tracking |
| **NM_COLIGACAO** | Candidate data | String | Coalition analysis | Alliance patterns |
| **DS_COMPOSICAO_COLIGACAO** | Candidate data | Text | Detailed coalition mapping | Network analysis |
| **NR_FEDERACAO** | Candidate data | Integer | Federation tracking | Modern alliance structures |
| **SG_FEDERACAO** | Candidate data | String | Federation abbreviations | Coalition abbreviations |

### 📅 TEMPORAL IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **ANO_ELEICAO** | All data | YYYY | Deputados mandate years | Electoral timeline |
| **DT_ELEICAO** | All data | YYYY-MM-DD | Election scheduling | Date correlation |
| **DT_NASCIMENTO** | Candidate data | YYYY-MM-DD | Age verification | Eligibility validation |
| **NR_TURNO** | All data | 1 or 2 | Round analysis | Electoral process |
| **DT_GERACAO** | All data | YYYY-MM-DD | Data freshness | Update tracking |

### 💰 FINANCIAL IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **VR_BEM_CANDIDATO** | Assets data | Decimal | Wealth progression | Enrichment tracking |
| **CD_TIPO_BEM_CANDIDATO** | Assets data | Integer | Asset categorization | Wealth analysis |
| **DS_BEM_CANDIDATO** | Assets data | Text | Asset descriptions | Detailed wealth tracking |
| **CNPJs** | Finance data | 14 digits | Portal sanctions, Deputados expenses | Donor-vendor correlation |

### 👤 DEMOGRAPHIC IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **CD_GENERO** | Candidate data | Integer | Gender analysis | Demographic tracking |
| **DS_GENERO** | Candidate data | String | Gender descriptions | Profile completion |
| **CD_GRAU_INSTRUCAO** | Candidate data | Integer | Education analysis | Background verification |
| **DS_GRAU_INSTRUCAO** | Candidate data | String | Education levels | Qualification assessment |
| **CD_ESTADO_CIVIL** | Candidate data | Integer | Marital status | Personal profile |
| **CD_COR_RACA** | Candidate data | Integer | Racial demographics | Representation analysis |
| **CD_OCUPACAO** | Candidate data | Integer | Professional background | Career correlation |
| **DS_OCUPACAO** | Candidate data | String | Occupation descriptions | Professional networks |

### 🗳️ ELECTORAL PERFORMANCE (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **CD_SITUACAO_CANDIDATURA** | Candidate data | Integer | Candidacy status | Eligibility tracking |
| **DS_SITUACAO_CANDIDATURA** | Candidate data | String | Status descriptions | Candidacy validation |
| **CD_SIT_TOT_TURNO** | Candidate data | Integer | Final results | Electoral performance |
| **DS_SIT_TOT_TURNO** | Candidate data | String | Result descriptions | Success/failure tracking |

---

## MISSING FIELDS REQUIRING ENRICHMENT

### 🚨 CRITICAL MISSING IDENTIFIERS (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **currentAddress** | Contact correlation | Deputados gabinete, Electoral registry | Cannot track current location | HIGH |
| **currentPhone** | Contact verification | Chamber directory, Electoral updates | Cannot verify active contact | HIGH |
| **familyMembers** | Nepotism detection | Civil registry, Cross-reference | Cannot detect family hiring | CRITICAL |
| **businessPartnership** | Conflict detection | Receita Federal | Cannot track company ownership | CRITICAL |
| **currentIncome** | Wealth analysis | Income tax, Parliamentary salary | Cannot assess enrichment patterns | HIGH |

### 💼 BUSINESS/FINANCIAL MISSING (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **currentAssetValues** | Wealth progression | Updated declarations | Only have campaign-time snapshots | HIGH |
| **companyOwnership** | Conflict analysis | Receita Federal | Cannot track business interests | CRITICAL |
| **bankAccounts** | Financial tracking | Banking regulation | Cannot trace money flows | MEDIUM |
| **investmentPortfolio** | Wealth analysis | Securities regulation | Cannot track market investments | MEDIUM |
| **realEstateDetails** | Asset verification | Property registries | Limited asset detail | MEDIUM |

### ⚖️ JUDICIAL/COMPLIANCE MISSING (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **criminalRecord** | Background check | Police databases | Only have candidacy status | CRITICAL |
| **civilLawsuits** | Legal exposure | DataJud detailed | Need case-by-case correlation | HIGH |
| **administrativePenalties** | Compliance check | Regulatory agencies | Cannot track professional sanctions | HIGH |
| **taxCompliance** | Financial integrity | Receita Federal | Cannot verify tax status | HIGH |

### 👥 RELATIONSHIP MISSING (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **spouseDetails** | Family wealth | Civil registry | Cannot track family enrichment | CRITICAL |
| **childrenInfo** | Nepotism tracking | Civil registry | Cannot detect family benefits | HIGH |
| **politicalMentors** | Network analysis | Career tracking | Cannot map influence networks | MEDIUM |
| **businessPartners** | Conflict analysis | Company registries | Cannot track business relationships | CRITICAL |
| **campaignStaff** | Network tracking | Campaign records | Cannot map operational networks | MEDIUM |

### 🏛️ CURRENT POLITICAL STATUS (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **currentPositions** | Office tracking | Deputados orgaos | Need real-time correlation | HIGH |
| **currentCommittees** | Influence analysis | Chamber records | TSE data is historical only | HIGH |
| **votingRecord** | Performance analysis | Chamber voting | Cannot correlate promises vs actions | CRITICAL |
| **currentPartyStatus** | Loyalty tracking | Real-time party records | TSE data is election-time only | HIGH |

---

## ENRICHMENT STRATEGY

### IMMEDIATE CORRELATION REQUIRED
1. **CPF Matching**: Link all TSE candidates to deputados by CPF
2. **Electoral Number Filling**: Populate missing deputados electoral numbers
3. **Asset Timeline Construction**: Track wealth progression across elections
4. **Campaign Finance Network**: Map donor CNPJs to vendor sanctions

### SECONDARY ENRICHMENT
1. **Civil Registry Integration**: Get family relationship data
2. **Receita Federal**: Validate company ownership and tax compliance
3. **Property Registries**: Detailed asset verification
4. **Professional Councils**: Validate occupation credentials

### DATA QUALITY FLAGS NEEDED
```
tse_validation_flags:
  - cpf_verified: boolean (cross-system match)
  - electoral_number_assigned: boolean (filled deputados gap)
  - asset_progression_tracked: boolean (multi-year wealth)
  - campaign_finance_mapped: boolean (donor networks)
  - demographic_complete: percentage (profile completeness)
  - family_data_enriched: boolean (nepotism detection ready)
```

---

## COMPOSITE KEYS FOR MATCHING

### Primary Correlation Strategy
```
PERFECT_MATCH_KEY = NR_CPF_CANDIDATO + ANO_ELEICAO
DEPUTY_CORRELATION = CPF (deputados) + CPF (TSE) + matching timeline
```

### When CPF Partial/Missing
```
FUZZY_MATCH_KEY = NM_CANDIDATO + DT_NASCIMENTO + SG_UF + SG_PARTIDO
NAME_VARIANTS = NM_CANDIDATO + NM_URNA_CANDIDATO + NM_SOCIAL_CANDIDATO
```

### For Asset Progression Analysis
```
WEALTH_TIMELINE_KEY = SQ_CANDIDATO + ANO_ELEICAO + VR_BEM_CANDIDATO
ASSET_CATEGORY_KEY = CD_TIPO_BEM_CANDIDATO + DS_TIPO_BEM_CANDIDATO
```

### For Campaign Finance Correlation
```
DONOR_NETWORK_KEY = CNPJ + ANO_ELEICAO + SQ_CANDIDATO
VENDOR_CORRELATION = CNPJ (TSE finance) + CNPJ (deputados expenses)
```

---

## SPECIALIZED TSE CORRELATION PATTERNS

### Electoral Number Recovery
```
# Fill critical gap from deputados API
ELECTORAL_NUMBER_MAP = {
  deputados.cpf: tse_candidates.nr_candidato
  WHERE tse_candidates.nr_cpf_candidato = deputados.cpf
  AND tse_candidates.ano_eleicao = [most_recent_election]
  AND tse_candidates.ds_cargo = 'DEPUTADO FEDERAL'
}
```

### Wealth Progression Analysis
```
# Track asset changes across elections
WEALTH_PROGRESSION = {
  candidate_cpf: {
    election_year: total_assets_value,
    asset_categories: [real_estate, vehicles, investments],
    growth_rate: year_over_year_change,
    suspicious_growth: boolean_flag
  }
}
```

### Coalition Network Mapping
```
# Political alliance patterns
COALITION_NETWORKS = {
  election_year: {
    coalition_name: [party_list],
    alliance_stability: multi_election_consistency,
    cross_party_connections: shared_coalition_members
  }
}
```

### Campaign Finance Risk Assessment
```
# Donor-vendor correlation
FINANCE_RISK_MATRIX = {
  candidate_cpf: {
    total_campaign_donations: sum(finance_records),
    sanctioned_donors: count(cnpj_in_portal_sanctions),
    vendor_overlap: count(cnpj_in_deputados_expenses),
    risk_score: calculated_composite_score
  }
}
```