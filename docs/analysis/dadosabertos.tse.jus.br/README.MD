# TSE Dados Abertos (Electoral Open Data) Documentation

## =ó Overview

The **TSE Dados Abertos** (Electoral Open Data Portal) is the Brazilian Superior Electoral Court's official platform for accessing comprehensive electoral data. This platform provides free access to historical and current electoral information including candidate registrations, election results, campaign finance records, and voting statistics dating back to 1933.

**Base URL**: `https://dadosabertos.tse.jus.br/`
**API Base**: `https://dadosabertos.tse.jus.br/api/3/`
**Platform**: CKAN (Comprehensive Knowledge Archive Network)
**Authentication**: None required
**Data Format**: Primarily CSV/ZIP, some JSON via API
**Total Datasets**: 164+

## =Ê Portal Architecture

### CKAN-Based System
The TSE portal uses CKAN, an open-source data management system that provides:
- **RESTful API**: Full programmatic access to datasets
- **Web Interface**: User-friendly browsing and search
- **Metadata Management**: Detailed dataset descriptions and structure
- **Resource Management**: Multiple file formats per dataset

### Historical Context
- **Launched**: January 2022 (replaced old Electoral Data Repository)
- **Coverage**: 1933 to present (90+ years of electoral data)
- **Scope**: Federal, state, and municipal elections
- **Language**: Portuguese (with some field names in Portuguese)

## = API Access

### No Authentication Required
Unlike many government APIs, TSE requires no registration or API keys:
```http
GET /api/3/action/{action}
Headers:
  User-Agent: Your-Application-Name/1.0
```

### CKAN API Endpoints

#### 1. **Package List** - Get All Datasets
**Endpoint**: `/api/3/action/package_list`
**Description**: Returns list of all available dataset identifiers
**Response**: JSON array of dataset names

```bash
curl "https://dadosabertos.tse.jus.br/api/3/action/package_list"
```

#### 2. **Package Show** - Get Dataset Details
**Endpoint**: `/api/3/action/package_show?id={dataset_id}`
**Description**: Returns detailed metadata for a specific dataset
**Response**: Complete dataset information including resources

```bash
curl "https://dadosabertos.tse.jus.br/api/3/action/package_show?id=candidatos-2022"
```

#### 3. **Resource Show** - Get File Details
**Endpoint**: `/api/3/action/resource_show?id={resource_id}`
**Description**: Returns metadata for a specific file/resource
**Response**: File details including download URL

#### 4. **Package Search** - Search Datasets
**Endpoint**: `/api/3/action/package_search?q={query}`
**Description**: Search datasets by keywords
**Parameters**:
- `q`: Search query
- `rows`: Number of results (default: 10)
- `start`: Offset for pagination

## =Ú Major Dataset Categories

### 1. **Candidatos** (Candidates)
**Pattern**: `candidatos-{year}`
**Description**: Complete candidate registrations for each election
**Coverage**: 1933-2024
**Key Use**: CPF-based politician identification and electoral history

#### Data Structure:
```csv
NR_TURNO,CD_TIPO_ELEICAO,NM_TIPO_ELEICAO,NR_ELEICAO,CD_PLEITO,DT_PLEITO,
TP_ABRANGENCIA,SG_UF,SG_UE,NM_UE,CD_CARGO,DS_CARGO,SQ_CANDIDATO,
NR_CANDIDATO,NM_CANDIDATO,NM_URNA_CANDIDATO,NM_SOCIAL_CANDIDATO,
NR_CPF_CANDIDATO,SG_PARTIDO,NR_PARTIDO,NM_PARTIDO,SQ_COLIGACAO,
NM_COLIGACAO,DS_COMPOSICAO_COLIGACAO,CD_SITUACAO_CANDIDATURA,
DS_SITUACAO_CANDIDATURA,CD_DETALHE_SITUACAO_CAND,DS_DETALHE_SITUACAO_CAND,
TP_AGREMIACAO,NR_PROCESSO,CD_SITUACAO_CANDIDATO_PLEITO,
DS_SITUACAO_CANDIDATO_PLEITO,CD_SITUACAO_CANDIDATO_URNA,
DS_SITUACAO_CANDIDATO_URNA,ST_CANDIDATO_INSERIDO_URNA,NR_TITULO_ELEITORAL_CANDIDATO,
CD_GENERO,DS_GENERO,CD_GRAU_INSTRUCAO,DS_GRAU_INSTRUCAO,CD_ESTADO_CIVIL,
DS_ESTADO_CIVIL,CD_COR_RACA,DS_COR_RACA,CD_OCUPACAO,DS_OCUPACAO,
CD_SIT_TOT_TURNO,DS_SIT_TOT_TURNO,ST_REELEICAO,ST_DECLARAR_BENS,
NR_PROTOCOLO_CANDIDATURA,NR_PROCESSO_PRESTACAO_CONTAS,ST_SUBSTITUIDO,
CD_TIPO_ELEICAO_ANTERIOR,NM_TIPO_ELEICAO_ANTERIOR,CD_PLEITO_ANTERIOR,
DT_PLEITO_ANTERIOR,SG_UF_NASCIMENTO,NM_MUNICIPIO_NASCIMENTO,DT_NASCIMENTO,
NR_IDADE_DATA_ELEICAO,NM_EMAIL,CD_NACIONALIDADE,DS_NACIONALIDADE,
SG_UF_NASCIMENTO,CD_MUNICIPIO_NASCIMENTO,NM_MUNICIPIO_NASCIMENTO
```

**Key Fields**:
- `NR_CPF_CANDIDATO`: CPF for cross-referencing
- `SQ_CANDIDATO`: Unique candidate identifier
- `DS_SIT_TOT_TURNO`: Final election outcome
- `CD_CARGO`: Position being sought (e.g., 6 = Federal Deputy)

### 2. **Resultados** (Results)
**Pattern**: `resultados-{year}`, `votacao-candidato-{year}`
**Description**: Detailed voting results by candidate and polling station
**Coverage**: 1933-2024
**Key Use**: Electoral performance analysis and vote distribution

#### Data Structure:
```csv
NR_TURNO,CD_TIPO_ELEICAO,NM_TIPO_ELEICAO,DT_PLEITO,TP_ABRANGENCIA,
SG_UF,SG_UE,NM_UE,CD_CARGO,DS_CARGO,SQ_CANDIDATO,NR_CANDIDATO,
NM_CANDIDATO,NM_URNA_CANDIDATO,NM_SOCIAL_CANDIDATO,NR_CPF_CANDIDATO,
NM_EMAIL,CD_SITUACAO_CANDIDATURA,DS_SITUACAO_CANDIDATURA,
CD_DETALHE_SITUACAO_CAND,DS_DETALHE_SITUACAO_CAND,TP_AGREMIACAO,
NR_PARTIDO,SG_PARTIDO,NM_PARTIDO,SQ_COLIGACAO,NM_COLIGACAO,
DS_COMPOSICAO_COLIGACAO,CD_SIT_TOT_TURNO,DS_SIT_TOT_TURNO,
QT_VOTOS_NOMINAIS,QT_VOTOS_NOMINAIS_VALIDOS,PC_VOTOS_NOMINAIS,
PC_VOTOS_NOMINAIS_VALIDOS,NM_TIPO_DESTINACAO_VOTOS,ST_VOTO_EM_TRANSITO
```

### 3. **Prestação de Contas** (Campaign Finance)
**Pattern**: `prestacao-de-contas-eleitorais-candidatos-{year}`
**Description**: Campaign finance records including donations and expenses
**Coverage**: 1998-2024
**Key Use**: Financial network analysis and donation tracking

#### Data Structure:
```csv
SQ_CANDIDATO,NR_CPF_CANDIDATO,NM_CANDIDATO,SG_UF,CD_CARGO,DS_CARGO,
SG_PARTIDO,NR_PARTIDO,NM_PARTIDO,NR_RECIBO_PRESTACAO_CONTAS,
DT_PRESTACAO_CONTAS,SQ_PRESTADOR_CONTAS,TP_PRESTADOR_CONTAS,
IC_PRESTADOR_CONTAS,NM_PRESTADOR_CONTAS,CD_CNPJ_PRESTADOR_CONTAS,
NR_CPF_PRESTADOR_CONTAS,NM_ADMINISTRADOR,CD_CNPJ_ADMINISTRADOR,
NR_CPF_ADMINISTRADOR,CD_SITUACAO_PRESTACAO_CONTAS,
DS_SITUACAO_PRESTACAO_CONTAS,DT_RECEITA,VR_RECEITA,
CD_ORIGEM_RECEITA,DS_ORIGEM_RECEITA,DS_RECEITA,
CD_CNPJ_CPF_DOADOR,NM_DOADOR_RFB,NM_DOADOR,
CD_CARGO_CANDIDATO_DOADOR,DS_CARGO_CANDIDATO_DOADOR,
SG_PARTIDO_DOADOR,NM_PARTIDO_DOADOR,CD_SETOR_ATIVIDADE_ECONOMICA,
DS_SETOR_ATIVIDADE_ECONOMICA,DT_DESPESA,VR_DESPESA,
CD_ORIGEM_DESPESA,DS_ORIGEM_DESPESA,DS_DESPESA,
CD_CNPJ_CPF_FORNECEDOR,NM_FORNECEDOR_RFB,NM_FORNECEDOR,
CD_SETOR_ATIVIDADE_ECONOMICA_FORNECEDOR,DS_SETOR_ATIVIDADE_ECONOMICA_FORNECEDOR
```

### 4. **Bens de Candidatos** (Candidate Assets)
**Pattern**: `bens-candidatos-{year}`
**Description**: Asset declarations by candidates
**Coverage**: 2006-2024
**Key Use**: Wealth tracking and asset analysis

### 5. **Pesquisas Eleitorais** (Electoral Polls)
**Pattern**: `pesquisas-eleitorais-{year}`
**Description**: Registered electoral research/polling data
**Coverage**: 2002-2024
**Key Use**: Pre-election sentiment analysis

### 6. **Consulta de Candidatos** (Candidate Search)
**Pattern**: `consulta-cand-{year}`
**Description**: Simplified candidate lookup data
**Coverage**: 2020-2024
**Key Use**: Quick candidate verification

## =Â Data Organization

### Geographic Structure
Most datasets are organized by:
- **BR** - National scope (federal elections)
- **UF** - State-level files (2-letter state codes: SP, RJ, MG, etc.)
- **MU** - Municipal-level files

### File Naming Convention
```
{type}_{year}_{scope}_{state}.{format}
```

Examples:
- `consulta_cand_2022_BRASIL.csv` - All candidates, national
- `consulta_cand_2022_SP.csv` - São Paulo state candidates
- `votacao_candidato_munzona_2022_BRASIL.csv` - Vote totals by municipality

### Compression and Encoding
- **Format**: Most files are ZIP-compressed
- **Encoding**: Latin-1 (ISO-8859-1) - requires special handling
- **Documentation**: Each ZIP contains `LEIAME.pdf` with field descriptions

## =» Implementation Examples

### Python - Get Available Datasets
```python
import requests

class TSEClient:
    def __init__(self):
        self.base_url = "https://dadosabertos.tse.jus.br/"
        self.api_base = "https://dadosabertos.tse.jus.br/api/3/"

    def get_packages(self):
        """Get all available datasets"""
        url = f"{self.api_base}action/package_list"
        response = requests.get(url)
        data = response.json()
        return data['result'] if data['success'] else []

    def get_package_info(self, package_id):
        """Get dataset details"""
        url = f"{self.api_base}action/package_show"
        params = {'id': package_id}
        response = requests.get(url, params=params)
        data = response.json()
        return data['result'] if data['success'] else None

# Usage
client = TSEClient()
packages = client.get_packages()
print(f"Found {len(packages)} datasets")

# Get 2022 candidates data
candidates_2022 = client.get_package_info('candidatos-2022')
resources = candidates_2022['resources']
for resource in resources:
    print(f"Resource: {resource['name']} ({resource['format']})")
```

### Python - Download and Process Candidate Data
```python
import zipfile
import csv
import io
import requests
from typing import List, Dict

def download_candidate_data(year: int = 2022) -> List[Dict]:
    """Download and parse candidate data for a specific year"""

    # Get dataset metadata
    api_url = f"https://dadosabertos.tse.jus.br/api/3/action/package_show?id=candidatos-{year}"
    response = requests.get(api_url)
    package_info = response.json()['result']

    # Find CSV resources
    candidate_files = []
    for resource in package_info['resources']:
        if resource['format'].lower() == 'csv' and 'candidato' in resource['name'].lower():
            candidate_files.append(resource)

    all_candidates = []

    for file_resource in candidate_files:
        print(f"Downloading: {file_resource['name']}")

        # Download file
        file_response = requests.get(file_resource['url'])

        if file_resource['name'].endswith('.zip'):
            # Handle ZIP files
            with zipfile.ZipFile(io.BytesIO(file_response.content)) as zip_file:
                for filename in zip_file.namelist():
                    if filename.endswith('.csv'):
                        with zip_file.open(filename) as csv_file:
                            # TSE uses Latin-1 encoding
                            csv_content = csv_file.read().decode('latin-1')
                            csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')
                            all_candidates.extend(list(csv_reader))
        else:
            # Handle direct CSV files
            csv_content = file_response.content.decode('latin-1')
            csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')
            all_candidates.extend(list(csv_reader))

    return all_candidates

# Usage
candidates = download_candidate_data(2022)
print(f"Found {len(candidates)} candidate records")

# Filter for federal deputies
deputies = [c for c in candidates if c.get('CD_CARGO') == '6']  # 6 = Federal Deputy
print(f"Found {len(deputies)} federal deputy candidates")
```

### CURL Examples

```bash
# List all datasets
curl "https://dadosabertos.tse.jus.br/api/3/action/package_list"

# Get 2022 candidates dataset info
curl "https://dadosabertos.tse.jus.br/api/3/action/package_show?id=candidatos-2022"

# Search for campaign finance datasets
curl "https://dadosabertos.tse.jus.br/api/3/action/package_search?q=prestacao+de+contas"

# Get resource details
curl "https://dadosabertos.tse.jus.br/api/3/action/resource_show?id={resource_id}"
```

## =' Data Processing Challenges

### 1. **Encoding Issues**
- **Problem**: TSE uses Latin-1 encoding (not UTF-8)
- **Solution**: Always specify encoding when reading files
```python
content = file.read().decode('latin-1')
```

### 2. **Large File Sizes**
- **Problem**: National datasets can exceed 1GB compressed
- **Solution**: Process state-by-state or use streaming
```python
# Process by state to reduce memory usage
states = ['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'GO', 'PE', 'CE']
for state in states:
    process_state_data(state, year)
```

### 3. **Inconsistent Field Names**
- **Problem**: Field names vary between years and datasets
- **Solution**: Create field mapping dictionaries
```python
CPF_FIELD_VARIANTS = [
    'NR_CPF_CANDIDATO',
    'nr_cpf_candidato',
    'CPF_CANDIDATO',
    'NR_CPF'
]

def get_cpf_field(row):
    for field in CPF_FIELD_VARIANTS:
        if field in row and row[field]:
            return row[field]
    return None
```

### 4. **Data Quality Issues**
- **Missing CPFs**: Some candidates lack CPF information
- **Name Variations**: Same person may have different name formats
- **Date Formats**: Inconsistent date formatting across years

## =Ê Integration Strategies

### For Politician Identification
1. **Primary Key**: Use CPF (`NR_CPF_CANDIDATO`) for exact matching
2. **Backup Matching**: Combine name + birth date + state
3. **Historical Tracking**: Follow `SQ_CANDIDATO` across elections
4. **Validation**: Cross-reference with Câmara deputy data

### For Electoral Analysis
1. **Vote Analysis**: Track electoral performance over time
2. **Geographic Patterns**: Analyze regional strength
3. **Party Movement**: Track party changes across elections
4. **Coalition Analysis**: Study political alliances

### For Campaign Finance
1. **Donation Networks**: Map donor-politician relationships
2. **Vendor Analysis**: Track campaign service providers
3. **Expense Patterns**: Identify spending categories
4. **Financial Growth**: Monitor campaign budget evolution

##   Known Limitations

### 1. **Data Availability**
- **Historical Gaps**: Some data incomplete before 2000
- **Format Changes**: Field structures vary across years
- **Update Frequency**: Data updated after elections only

### 2. **Technical Constraints**
- **No Rate Limiting**: But be respectful with requests
- **Large Downloads**: Multi-gigabyte files require robust handling
- **Network Dependencies**: Relies on external CDN for file delivery

### 3. **Data Quality**
- **Incomplete Records**: Not all fields populated for all candidates
- **Encoding Issues**: Non-standard character encoding
- **Duplicate Detection**: Same person may appear multiple times

## =€ Integration with CLI4 System

The TSE portal is integrated into CLI4 for:

### 1. **Politician Population**
- **CPF Discovery**: Extract CPFs for Câmara deputies
- **Identity Validation**: Confirm politician identity across systems
- **Historical Context**: Provide electoral background

### 2. **Electoral Records Population**
- **Election History**: Track all candidacies by CPF
- **Performance Metrics**: Calculate success rates and trends
- **Geographic Analysis**: Map electoral territories

### 3. **Asset Declarations**
- **Wealth Tracking**: Monitor declared assets over time
- **Growth Analysis**: Calculate wealth progression
- **Transparency**: Enable wealth evolution investigation

### CLI4 Commands
```bash
# Populate electoral records
python cli4/main.py populate-electoral --election-years 2018 2020 2022

# Populate asset declarations
python cli4/main.py populate-assets --election-years 2020 2022 2024

# Process specific politicians
python cli4/main.py populate-electoral --politician-ids 1 2 3
```

## =È Performance Optimization

### 1. **Caching Strategy**
- **Dataset Metadata**: Cache package information
- **Downloaded Files**: Store processed data locally
- **CPF Lookups**: Index by CPF for fast searches

### 2. **Batch Processing**
- **State-Level Processing**: Handle large datasets in chunks
- **Parallel Downloads**: Process multiple files simultaneously
- **Memory Management**: Stream large files instead of loading entirely

### 3. **Data Filtering**
- **Relevant Elections**: Focus on recent election years
- **Specific Positions**: Filter by office type (federal deputy = CD_CARGO = 6)
- **Geographic Scope**: Limit to specific states if needed

## =Ú Additional Resources

- **Official Portal**: https://dadosabertos.tse.jus.br/
- **CKAN Documentation**: https://docs.ckan.org/en/2.9/api/
- **Historical Coverage**: https://dadosabertos.tse.jus.br/group/resultados
- **Data Dictionary**: Available in LEIAME.pdf files within each dataset
- **Electoral Calendar**: https://www.tse.jus.br/eleicoes/calendario-eleitoral

## <¯ Conclusion

The TSE Dados Abertos portal provides unparalleled access to Brazilian electoral data spanning nearly a century. Its CKAN-based architecture enables both human and programmatic access to comprehensive datasets covering candidates, results, finances, and assets. While technical challenges exist (encoding, large files, data quality), the portal serves as a critical foundation for electoral transparency and political analysis in Brazil.

The CLI4 system successfully leverages this platform to maintain comprehensive electoral records for all federal deputies, enabling cross-source analysis and corruption detection through electoral, financial, and asset correlation.

---

*Last Updated: September 2025*
*Platform: CKAN 2.9+ (inferred)*
*Data Coverage: 1933-2024*
*Documentation by: CLI4 System Analysis*