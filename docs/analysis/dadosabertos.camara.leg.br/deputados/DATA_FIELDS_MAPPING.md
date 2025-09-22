# DATA FIELDS MAPPING - DEPUTADOS DATA LAKE

## AVAILABLE FIELDS FOR CORRELATION

### 🔑 PRIMARY IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **cpf** | `/deputados/{id}` | 11 digits | Portal Transparência, TSE, TCU, DataJud | Universal person identifier |
| **cnpjCpfFornecedor** | `/deputados/{id}/despesas` | 14/11 digits | Portal Transparência sanctions, TCU contracts | Vendor corruption detection |
| **nomeCivil** | `/deputados/{id}` | String | All systems (fuzzy) | Legal name matching |
| **nomeEleitoral** | `/deputados/{id}/ultimoStatus` | String | TSE candidates | Campaign name matching |
| **idDeputado** | All endpoints | Integer | Internal only | Primary key for all subroutes |
| **idLegislatura** | Multiple endpoints | Integer | Senado, TSE | Temporal correlation |

### 📍 GEOGRAPHIC IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **siglaUf** | `/deputados/{id}/ultimoStatus` | 2 letters | TSE zones, IBGE | State-level analysis |
| **municipioNascimento** | `/deputados/{id}` | String | TSE, IBGE | Birth location validation |
| **municipio** | `/deputados/{id}/mandatosExternos` | String | TSE electoral zones | Political base tracking |

### 🏛️ POLITICAL IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **siglaPartido** | `/deputados/{id}/ultimoStatus` | String | TSE, Senado | Party affiliation |
| **siglaPartidoEleicao** | `/deputados/{id}/mandatosExternos` | String | TSE elections | Historical party tracking |
| **cargo** | `/deputados/{id}/mandatosExternos` | String | TSE candidacies | Position validation |
| **idOrgao** | `/deputados/{id}/orgaos` | Integer | Internal committees | Committee correlation |
| **idFrentes** | `/deputados/{id}/frentes` | Integer | Internal fronts | Network analysis |

### 📅 TEMPORAL IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **dataNascimento** | `/deputados/{id}` | YYYY-MM-DD | TSE, validation | Age/eligibility verification |
| **anoInicio/anoFim** | `/deputados/{id}/mandatosExternos` | YYYY string | TSE elections | Career timeline |
| **dataDocumento** | `/deputados/{id}/despesas` | YYYY-MM-DD | Audit timing | Expense validation |
| **dataHoraInicio** | `/deputados/{id}/eventos` | ISO datetime | Activity tracking | Presence verification |

### 💰 FINANCIAL IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **valorDocumento** | `/deputados/{id}/despesas` | Float | Portal Transparência | Amount validation |
| **valorGlosa** | `/deputados/{id}/despesas` | Float | TCU audits | Rejection tracking |
| **urlDocumento** | `/deputados/{id}/despesas` | URL | Direct verification | PDF audit trail |
| **nomeFornecedor** | `/deputados/{id}/despesas` | String | Company registries | Vendor identification |
| **tipoDespesa** | `/deputados/{id}/despesas` | String | Category analysis | Spending patterns |

### 📝 SUPPLEMENTARY IDENTIFIERS (HAVE)

| Field | Source | Format | Cross-References | Purpose |
|-------|--------|--------|------------------|---------|
| **escolaridade** | `/deputados/{id}` | String | Background check | Education validation |
| **codTipoProfissao** | `/deputados/{id}/profissoes` | Integer | Professional registry | Background verification |
| **entidade** | `/deputados/{id}/ocupacoes` | String (often null) | Company registry | Employment verification |
| **urlRegistro** | `/deputados/{id}/eventos` | URL | YouTube/media | Activity verification |
| **transcricao** | `/deputados/{id}/discursos` | Text | NLP analysis | Content analysis |

---

## MISSING FIELDS REQUIRING ENRICHMENT

### 🚨 CRITICAL MISSING IDENTIFIERS (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **numeroEleitoral** | TSE direct link | TSE API enrichment | Cannot match candidates directly | CRITICAL |
| **tituloEleitoral** | Voter validation | TSE database | Cannot verify voter registration | HIGH |
| **pis/pasep** | Social security | Receita Federal | Cannot track benefits | MEDIUM |
| **registroOAB** | Lawyer validation | OAB registry | Cannot verify legal credentials | LOW |
| **cnh** | Identity validation | DETRAN | Additional identity verification | LOW |

### 💼 BUSINESS/FINANCIAL MISSING (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **cnpjValidation** | Company status | Receita Federal API | Cannot verify company existence | CRITICAL |
| **sociosEmpresa** | Ownership network | Receita Federal | Cannot map business relationships | HIGH |
| **contaBancaria** | Financial tracking | Banking regulation | Cannot track money flow | MEDIUM |
| **patrimonioDeclarado** | Wealth tracking | TSE declarations | Cannot verify enrichment | HIGH |
| **dividas** | Debt tracking | SERASA/SPC | Cannot assess financial health | MEDIUM |

### ⚖️ JUDICIAL/COMPLIANCE MISSING (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **processosJudiciais** | Legal status | DataJud enrichment | Cannot track lawsuits directly | HIGH |
| **antecedentesDetails** | Criminal check | Police databases | Cannot verify clean record | CRITICAL |
| **sanctionsDetails** | Detailed sanctions | Portal Transparência API | Only have boolean, need details | HIGH |
| **tcuProcessNumbers** | Audit tracking | TCU database | Cannot link specific audits | MEDIUM |
| **investigacoes** | Investigation status | MPF/PF | Cannot track investigations | HIGH |

### 🗳️ ELECTORAL MISSING (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **votosRecebidos** | Electoral strength | TSE results | Cannot measure popularity | MEDIUM |
| **campanhaFinanciamento** | Campaign finance | TSE prestação contas | Cannot track donors | CRITICAL |
| **coligacao** | Coalition tracking | TSE registration | Cannot map alliances | MEDIUM |
| **zonaEleitoral** | Voter base | TSE zones | Cannot map constituencies | LOW |
| **secaoEleitoral** | Detailed location | TSE | Cannot do precinct analysis | LOW |

### 👥 RELATIONSHIP MISSING (NEED)

| Field | Required For | Potential Source | Impact | Priority |
|-------|--------------|------------------|---------|----------|
| **parentesServidores** | Nepotism detection | Portal Transparência | Cannot detect family hiring | CRITICAL |
| **conjuge** | Relationship mapping | Civil registry | Cannot track family wealth | HIGH |
| **filiacaoPartidaria** | Party history dates | TSE filiados | Cannot track party loyalty | MEDIUM |
| **assessores** | Staff network | Chamber HR | Cannot map influence network | MEDIUM |
| **doadoresCampanha** | Donor network | TSE | Cannot track obligations | CRITICAL |

---

## ENRICHMENT STRATEGY

### IMMEDIATE ENRICHMENT REQUIRED
1. **TSE API**: Get numeroEleitoral, campaign finance, vote counts
2. **Portal Transparência Deep Dive**: Get detailed sanctions, nepotism lists
3. **TCU Detailed API**: Get specific process numbers and rulings
4. **Receita Federal** (if accessible): Validate CNPJs, get company ownership

### SECONDARY ENRICHMENT
1. **DataJud API Enhancement**: Get detailed case information
2. **State-level APIs**: Get local political history
3. **Social Media APIs**: Get public statements and positions
4. **News APIs**: Track media mentions and scandals

### DATA QUALITY FLAGS NEEDED
```
validation_flags:
  - cpf_validated: boolean (Receita check)
  - cnpj_active: boolean (company status)
  - electoral_match: boolean (TSE confirmed)
  - sanctions_checked: date (last verification)
  - enrichment_complete: percentage
```

---

## COMPOSITE KEYS FOR MATCHING

### When Electoral Number Missing
```
TSE_MATCH_KEY = cpf + siglaPartido + siglaUf + anoEleicao
ALT_MATCH_KEY = nomeCivil + dataNascimento + municipioNascimento
```

### For Company Correlation
```
COMPANY_KEY = cnpj + razaoSocial (normalize)
VENDOR_KEY = cnpj + nomeFornecedor + uf
```

### For Temporal Analysis
```
TIMELINE_KEY = idDeputado + idLegislatura + dataHora
CAREER_KEY = cpf + cargo + anoInicio + municipio
```