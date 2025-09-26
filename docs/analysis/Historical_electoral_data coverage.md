# Brazilian electoral data sources for comprehensive political career tracking

## Historical electoral data coverage across all offices

The Brazilian electoral system provides remarkably comprehensive data access, though quality and completeness vary significantly by time period. **The TSE Electoral Memory Project successfully digitized 83,000+ candidates from 17 elections between 1945-1990**, though this initially excluded mayors and city councilors. Complete digital coverage exists from 1994 onwards for all requested office types: Prefeito (Mayor), Governador (Governor), Senador (Senator), Deputado Federal, Deputado Estadual, and Vereador (City Councilor).

For pre-2000 data, you'll find basic candidate information and party affiliations in digitized format, but demographic profiling and financial data only become available from 1994 onwards. The most significant limitation is that data before 1994 exists only in basic digitized form from paper records, with variable quality depending on the regional electoral court that originally maintained them. Full electoral profiling with gender and age demographics starts in 1994, party financial accounts appear from 2002, and campaign finance data becomes available from 2017.

The critical insight for implementation is that **both wins and losses are recorded for all candidates**, enabling complete career trajectory analysis. However, tracking politicians across elections requires manual record linkage since the TSE's sequential candidate numbers change between elections.

## TSE data repository architecture and access methods

The TSE completely restructured their data access in January 2022, replacing the old "Repositório de Dados Eleitorais" with the new Portal de Dados Abertos. The primary access point is **https://dadosabertos.tse.jus.br/** which provides 164+ datasets with no authentication required. Data comes primarily as ZIP-compressed CSV files organized by state (UF) and election year, with each archive containing a "LEIAME.pdf" documentation file explaining field structures.

### Critical TSE endpoints and undocumented API

While TSE operates an internal REST API at **https://divulgacandcontas.tse.jus.br/divulga/**, it lacks official documentation. The developer community maintains unofficial OpenAPI documentation at **https://github.com/augusto-herrmann/divulgacandcontas-doc** with the divulgacandcontas-swagger.yaml specification file. This API requires no authentication but lacks CORS support and needs careful rate limiting to avoid IP blocking.

For bulk downloads, the structured approach is:
1. Access https://dadosabertos.tse.jus.br/dataset/
2. Select by election year and data type
3. Download state-organized ZIP files
4. Note that some files arrive with .txt extensions but must be renamed to .csv
5. Files often exceed Excel's 1,048,576 row limit, requiring specialized processing tools

## Consolidated academic databases offering superior access

### CEPESP-FGV: The gold standard for cleaned data

**CEPESP provides the most refined access to Brazilian electoral data** through multiple interfaces at **https://cepespdata.io/**. Their system offers pre-processed data from 1998-2018 with consistent formatting across years, filtered for TSE-approved candidacies only, and available through both REST API and programming libraries.

Access methods include:
- **R Package**: `devtools::install_github("Cepesp-Fgv/cepesp-r")`
- **Python Package**: Available at https://github.com/Cepesp-Fgv/cepesp-python
- **Direct API**: https://github.com/Cepesp-Fgv/cepesp-rest

The CEPESP advantage lies in their HiveQL and Pandas post-processing, which provides standardized variable names across different election years and multiple aggregation levels instantly available through their Athena SQL backend.

### Base dos Dados: BigQuery-powered analysis

**Base dos Dados** (https://basedosdados.org/) offers TSE election data integrated with Brazil's broader socioeconomic datasets through Google BigQuery. Access their electoral dataset at **https://basedosdados.org/dataset/br-tse-eleicoes** with 1TB monthly free usage through BigQuery.

The SQL interface enables complex queries like:
```sql
SELECT * FROM `basedosdados.br_tse_eleicoes.candidatos` 
WHERE ano = 2018 AND cargo = 'presidente'
```

This platform excels for cross-dataset analysis, joining electoral results with demographic or economic indicators.

### ElectionsBR: Most current data access

The **electionsBR R package** (https://github.com/silvadenisson/electionsBR) provides the most up-to-date coverage through 2024, wrapping both TSE and CEPESP APIs:

```r
library(electionsBR)
candidates_2024 <- elections_tse(year = 2024, type = "candidate")
results_2024 <- elections_tse(year = 2024, type = "vote_mun_zone", encoding = "UTF-8")
```

## Data structure and candidate identification systems

### Primary identifiers and tracking challenges

The TSE uses **SQ_CANDIDATO** (sequential candidate number) as the primary identifier within each election, but this number changes between elections, making longitudinal tracking complex. While CPF (Cadastro de Pessoas Físicas) appears in some datasets, particularly CEPESP's API as "CPF_CANDIDATO", it's not universally available in historical data.

Key field names you'll encounter:
- `NM_CANDIDATO`: Full candidate name
- `NM_URNA_CANDIDATO`: Ballot name
- `NR_CANDIDATO`: Ballot number
- `CD_CARGO`/`DS_CARGO`: Office code and description
- `NR_PARTIDO`/`SG_PARTIDO`: Party number and abbreviation
- `QT_VOTOS_NOMINAIS`: Votes received
- `DS_SIT_TOT_TURNO`: Electoral outcome

### Linking candidates across elections

Since TSE provides no built-in longitudinal tracking, researchers must implement fuzzy matching on names, birth dates, and geographic patterns. The recommended approach combines:
1. Name standardization (remove accents, normalize spacing)
2. Jaro-Winkler similarity scoring for name matching
3. Biographical validation using birthdate and hometown when available
4. Political pattern analysis tracking party movements

Several GitHub repositories tackle this challenge, notably **renovabr/electoral-history** which provides ETL pipelines for standardizing TSE data with cross-election linking.

### State-level TRE integration

Brazil's 27 Regional Electoral Courts (TREs) replicate data daily to TSE's central system. While individual TRE portals (like tre-sp.jus.br) exist, they don't typically provide additional APIs beyond TSE's central system. The main value of TRE-level access is potentially more current data before TSE consolidation.

## Practical implementation specifications

### Download and processing requirements

**File sizes represent a significant challenge** - datasets are split by state to manage size but still require substantial bandwidth and storage. Plan for multi-terabyte requirements for complete historical data. TSE files use Latin-1 encoding by default, requiring conversion:

```r
df <- read.csv("candidatos.csv", encoding = "Latin-1")
df$nome <- iconv(df$nome, from = "Latin-1", to = "UTF-8")
```

### Optimal data access strategy

For immediate implementation, follow this hierarchy:
1. **Use CEPESP** for cleaned historical data (1998-2018) with standardized formats
2. **Deploy electionsBR** for recent elections (2020-2024) with direct TSE access
3. **Leverage Base dos Dados** when you need socioeconomic context via BigQuery
4. **Access TSE directly** only for verification or data not available elsewhere

### Storage architecture recommendations

For production systems, implement:
- **PostgreSQL** for structured relational storage with JSONB support for complex fields
- **BigQuery** for large-scale analytics with automatic scaling
- **Partition by election year** for query optimization
- **Cluster by geographic identifiers** (state, municipality) for spatial queries
- **Implement caching layers** to avoid repeated downloads of large files

### Critical implementation warnings

Several pitfalls require careful handling:
- **Candidate dropouts** affect vote margin calculations and appear inconsistently
- **Municipality codes change over time** - maintain IBGE code mapping tables
- **Data versioning is crucial** - TSE frequently updates databases
- **Memory limitations** - use chunked processing for files exceeding available RAM
- **Regular vs supplementary elections** must be distinguished in analysis

The Brazilian electoral data ecosystem provides exceptional depth and accessibility, but successful implementation requires understanding these structural complexities and using the appropriate access methods for your specific use case. Start with the consolidated academic sources for cleaned data, then supplement with direct TSE access only when necessary for completeness or verification.