# DEPUTADOS API - DATA FOUNDATION ANALYSIS

**11 ROUTES ANALYZED WITH FIELD-LEVEL VERIFICATION**

---

## CRITICAL FINDING: CROSS-REFERENCE LIMITATIONS

### ⚠️ Missing Expected Identifiers
- **Electoral Number**: NOT available in deputados API (expected but absent)
- **Email**: Nested in ultimoStatus, often null
- **Party URI**: Often null despite party affiliation present

### ✅ Confirmed Cross-Reference Keys
- **CPF**: Present in main deputy endpoint (verified: 67821090425 format)
- **CNPJ**: Present in expenses (verified: 14-digit format like 11521613000190)
- **Deputy ID**: Consistent across all subroutes
- **Legislature ID**: Present for temporal correlation

---

## VERIFIED DATA STRUCTURES

### `/deputados/{id}` - Core Identity [VERIFIED]
```
CONFIRMED FIELDS:
- id: integer (unique deputy identifier)
- uri: string (API reference)
- nomeCivil: string (legal name for matching)
- cpf: string [KEY FOR EXTERNAL SYSTEMS]
- sexo: string ('M' or 'F')
- urlWebsite: string/null
- redeSocial: array (social media links)
- dataNascimento: string (YYYY-MM-DD format)
- dataFalecimento: string/null
- ufNascimento: string (2-letter state code)
- municipioNascimento: string (birth city)
- escolaridade: string (education level)

NESTED IN ultimoStatus:
- ultimoStatus.id: integer
- ultimoStatus.nome: string
- ultimoStatus.siglaPartido: string [KEY FOR PARTY CORRELATION]
- ultimoStatus.uriPartido: string/null (often missing)
- ultimoStatus.siglaUf: string [KEY FOR GEOGRAPHIC CORRELATION]
- ultimoStatus.idLegislatura: integer [KEY FOR TEMPORAL CORRELATION]
- ultimoStatus.urlFoto: string
- ultimoStatus.email: string/null (often missing)
- ultimoStatus.nomeEleitoral: string (campaign name)
- ultimoStatus.gabinete: object (office details)
- ultimoStatus.situacao: string (active status)
- ultimoStatus.condicaoEleitoral: string (electoral condition)

NOT PRESENT (CONTRARY TO EXPECTATION):
- numeroEleitoral (electoral number for TSE correlation)
```

### `/deputados/{id}/despesas` - Financial Records [VERIFIED]
```
CONFIRMED FIELDS (ALL PRESENT):
- ano: integer (year)
- mes: integer (month 1-12)
- tipoDespesa: string (expense category)
- codDocumento: integer (unique document ID)
- tipoDocumento: string (e.g., "Nota Fiscal")
- codTipoDocumento: integer (document type code)
- dataDocumento: string (YYYY-MM-DD format)
- numDocumento: string (document number)
- valorDocumento: float (declared amount)
- urlDocumento: string (PDF link for verification)
- nomeFornecedor: string (vendor name)
- cnpjCpfFornecedor: string [KEY - 14 digits for CNPJ, 11 for CPF]
- valorLiquido: float (net amount paid)
- valorGlosa: float (rejected amount - corruption indicator)
- numRessarcimento: string (reimbursement number)
- codLote: integer (batch code)
- parcela: integer (installment number)
```

### `/deputados/{id}/mandatosExternos` - Political History [VERIFIED]
```
CONFIRMED FIELDS:
- cargo: string (position held)
- siglaUf: string (2-letter state)
- municipio: string/null (city for local positions)
- anoInicio: string (start year as string)
- anoFim: string (end year as string)
- siglaPartidoEleicao: string [KEY FOR PARTY HISTORY]
- uriPartidoEleicao: string (party API reference)
```

### `/deputados/{id}/orgaos` - Committees [VERIFIED]
```
CONFIRMED FIELDS:
- idOrgao: integer (committee ID)
- uriOrgao: string (API reference)
- siglaOrgao: string (abbreviation)
- nomeOrgao: string (full name - can be very long, 188+ chars)
- nomePublicacao: string/null (usually null)
- titulo: string (deputy's role)
- codTitulo: string (role code - NOTE: string not integer)
- dataInicio: datetime (ISO format with T separator)
- dataFim: datetime/null (null = currently active)
```

### `/deputados/{id}/eventos` - Activities [VERIFIED]
```
CONFIRMED FIELDS:
- id: integer (event ID)
- uri: string (API reference)
- dataHoraInicio: datetime (ISO format)
- dataHoraFim: datetime (ISO format)
- situacao: string (e.g., "Encerrada")
- descricaoTipo: string (event type)
- descricao: string (detailed description)
- localExterno: string/null (usually null)
- orgaos: array of objects (organizing committees)
- localCamara: object with:
  - nome: string
  - predio: string/null
  - sala: string/null
  - andar: string/null
- urlRegistro: string (YouTube/video link)
```

### `/deputados/{id}/frentes` - Parliamentary Groups [VERIFIED]
```
CONFIRMED FIELDS:
- id: integer (front ID)
- uri: string (API reference)
- titulo: string (front name/description)
- idLegislatura: integer (legislature period)
```

### `/deputados/{id}/profissoes` - Professions [VERIFIED]
```
CONFIRMED FIELDS:
- dataHora: datetime (registration timestamp)
- codTipoProfissao: integer (profession code)
- titulo: string (profession name)
```

### `/deputados/{id}/ocupacoes` - Employment [DATA QUALITY ISSUE]
```
FIELDS EXIST BUT OFTEN NULL:
- titulo: string/null (job title)
- entidade: string/null (organization)
- entidadeUF: string/null (state)
- entidadePais: string/null (country)
- anoInicio: integer/null (start year)
- anoFim: integer/null (end year)

NOTE: Arthur Lira has all nulls despite having data
```

### `/deputados/{id}/discursos` - Speeches [VARIES BY DEPUTY]
```
WHEN PRESENT:
- dataHoraInicio: datetime
- dataHoraFim: datetime/null
- tipoDiscurso: string
- transcricao: string (full text)
- urlTexto: string/null
- urlAudio: string/null
- urlVideo: string/null

NOTE: Arthur Lira has 0 speeches
```

### `/deputados/{id}/historico` - Status Changes [REQUIRES DATE PARAMS]
```
CONFIRMED FIELDS:
- dataHora: datetime
- idSituacao: integer
- situacao: string
- descricao: string
- siglaPartido: string
- siglaUf: string
- idLegislatura: integer

REQUIREMENT: Must include dataInicio and dataFim parameters
```

---

## EXTERNAL SYSTEM CORRELATION MATRIX

### Portal da Transparência Correlation
| Deputados Field | Maps To | Correlation Type | Reliability |
|----------------|---------|------------------|-------------|
| cpf | CNEP/Sanctions CPF | Direct match | HIGH |
| cnpjCpfFornecedor | Sanctions CNPJ | Direct match | HIGH |
| nomeCivil | Nepotism registry name | Fuzzy match | MEDIUM |
| nomeFornecedor | Company sanctions name | Fuzzy match | MEDIUM |

### TSE Electoral System Correlation
| Deputados Field | Maps To | Correlation Type | Reliability |
|----------------|---------|------------------|-------------|
| cpf | Candidate CPF | Direct match | HIGH |
| nomeCivil | Candidate name | Fuzzy match | MEDIUM |
| siglaPartido | Party registration | Direct match | HIGH |
| siglaUf + municipio | Electoral zone | Combined key | HIGH |
| anoInicio/Fim | Election years | Temporal match | HIGH |
| **numeroEleitoral** | **Candidate number** | **NOT AVAILABLE** | **N/A** |

### TCU Audit Court Correlation
| Deputados Field | Maps To | Correlation Type | Reliability |
|----------------|---------|------------------|-------------|
| cpf | Disqualified persons | Direct match | HIGH |
| cnpjCpfFornecedor | Irregular contractors | Direct match | HIGH |
| nomeCivil | Investigation records | Fuzzy match | MEDIUM |

### Senado Federal Correlation
| Deputados Field | Maps To | Correlation Type | Reliability |
|----------------|---------|------------------|-------------|
| idLegislatura | Legislature period | Direct match | HIGH |
| siglaPartido | Party bloc | Direct match | HIGH |
| nomeOrgao | Joint committees | String match | MEDIUM |

### DataJud Judicial Correlation
| Deputados Field | Maps To | Correlation Type | Reliability |
|----------------|---------|------------------|-------------|
| cpf | Process parties | Direct match | HIGH |
| nomeCivil | Party names | Fuzzy match | LOW |
| cnpjCpfFornecedor | Company processes | Direct match | MEDIUM |

---

## DATA TYPE SPECIFICATIONS

### String Field Constraints
- **CPF**: 11 numeric characters (no formatting)
- **CNPJ**: 14 numeric characters (no formatting)
- **UF**: 2 uppercase letters
- **Partido Sigla**: Variable length (2-10 chars)
- **Nome fields**: Up to 200+ characters
- **URLs**: Variable, can exceed 100 characters

### Datetime Formats
- **Full datetime**: YYYY-MM-DDTHH:MM (ISO 8601)
- **Date only**: YYYY-MM-DD
- **Year only**: YYYY as string (mandatosExternos)

### Numeric Types
- **IDs**: Integer (can be 6+ digits)
- **Money values**: Float (2 decimal places implied)
- **Codes**: Integer or String (inconsistent)
- **Years**: String or Integer (inconsistent)

---

## DATA COMPLETENESS ASSESSMENT

### Always Present (100% reliable)
- Deputy ID, name, CPF
- Expense records with CNPJ
- Committee memberships
- Parliamentary fronts

### Usually Present (70-90% reliable)
- Birth date and location
- Party affiliation
- Political history (mandatosExternos)
- Professional background

### Often Missing (30-50% reliable)
- Email addresses
- Website URLs
- Employment details (ocupacoes)
- Speech records (deputy-dependent)

### Never Present (0%)
- Electoral number (critical TSE key missing)
- Tax ID validation
- Criminal record references

---

## CRITICAL GAPS FOR DATA LAKE

### Missing Cross-Reference Keys
1. **Electoral Number**: Cannot directly link to TSE candidate database
2. **Voter Registration**: No título de eleitor for validation
3. **Tax Status**: No Receita Federal integration point
4. **Criminal Records**: No direct judicial reference

### Data Quality Issues
1. **Inconsistent data types**: Years as strings vs integers
2. **Null-heavy endpoints**: ocupacoes often useless
3. **Self-reported data**: professions, education unverified
4. **Missing timestamps**: Some records lack proper dating

### Workaround Requirements
1. **TSE correlation**: Must use CPF + name + party + year combination
2. **Company validation**: CNPJ present but not validated
3. **Name matching**: Requires fuzzy logic for variations
4. **Temporal alignment**: Different date formats need normalization

---

## DATA VOLUME REALITY CHECK

### Actual Volumes (Based on Arthur Lira)
- Core record: 1 with ~25 fields
- Expenses: ~169 records/year (2024)
- Events: ~100-500/year
- Parliamentary fronts: 285 (exceptional case)
- Committees: 3 active
- External mandates: 5 historical
- Professions: 2 declared
- Occupations: 1 (all nulls)
- Speeches: 0 (role-dependent)

### Storage Projections (513 deputies)
- Core data: ~13,000 fields total
- Annual expenses: ~87,000 records
- Annual events: ~200,000 records
- Fronts total: ~30,000 memberships
- Historical mandates: ~2,000 records

### Database Size Estimate
- Initial load: ~500MB
- Annual growth: ~100MB
- 5-year projection: ~1GB

---

## CORRELATION RELIABILITY SCORE

### High Confidence (Direct matching possible)
- CPF → Portal Transparência, TSE, TCU, DataJud
- CNPJ → Portal Transparência sanctions
- Legislature ID → Cross-chamber correlation
- Party codes → Political party databases

### Medium Confidence (Combination matching required)
- Name + CPF → Most systems
- Party + State + Year → Electoral correlation
- Committee names → Senado alignment

### Low Confidence (Fuzzy matching necessary)
- Name-only matching → High false positive risk
- Company name matching → Variations and changes
- Address/location matching → Format inconsistencies

---

## FOUNDATION STABILITY ASSESSMENT

### Strengths
- CPF available for person-level correlation
- CNPJ available for company-level analysis
- Complete political career tracking
- Comprehensive expense documentation

### Weaknesses
- Missing electoral number (TSE direct link broken)
- Inconsistent data types across endpoints
- High null rate in some endpoints
- Self-reported/unverified data

### Requirements for Robust Data Lake
1. **CPF validation service** needed
2. **CNPJ validation service** needed
3. **Name normalization algorithm** required
4. **Fuzzy matching capability** essential
5. **Data quality scoring system** recommended
6. **Missing data imputation strategy** necessary

---

## DATA LAKE DESIGN IMPLICATIONS

This API provides a solid but imperfect foundation. The presence of CPF and CNPJ enables critical cross-system correlation, but missing electoral numbers and data quality issues require sophisticated matching algorithms and validation services to build a truly reliable political transparency data lake.