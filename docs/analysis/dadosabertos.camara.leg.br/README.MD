# Câmara dos Deputados API Documentation

## <Û Overview

The **Câmara dos Deputados Open Data API** (dadosabertos.camara.leg.br) is the Brazilian Chamber of Deputies' official API for accessing comprehensive legislative, financial, and political data. This API serves as the primary source for federal deputy information, including personal details, expenses, voting records, committee memberships, and political activities.

**Base URL**: `https://dadosabertos.camara.leg.br/api/v2/`
**Swagger Documentation**: `https://dadosabertos.camara.leg.br/swagger/api.html`
**Authentication**: None required
**Response Format**: JSON
**Rate Limiting**: Recommended 500ms between requests
**Data Updates**: Daily

## = API Access

### No Authentication Required
The Câmara API is completely open and requires no registration or API keys:

```http
GET /api/v2/{endpoint}
Headers:
  User-Agent: Your-Application-Name/1.0
  Accept: application/json
```

### Rate Limiting Best Practices
While no formal rate limits are enforced, respectful usage is recommended:
- **500ms delay** between requests
- **Batch processing** during off-peak hours
- **Local caching** of static data (deputy profiles, committees)

## =Ú Core Endpoints

### 1. **Deputies** - Federal Deputy Registry
**Endpoint**: `/deputados`
**Description**: Complete registry of all federal deputies who have served in the Chamber
**Key Use**: Primary source for deputy identification and basic information

#### Parameters:
- `id` (integer): Specific deputy ID
- `nome` (string): Filter by deputy name
- `idLegislatura` (integer): Filter by legislature
- `siglaUf` (string): Filter by state (UF)
- `siglaPartido` (string): Filter by party
- `siglaSexo` (string): Filter by gender (M/F)
- `itens` (integer): Number of results per page (max 100)
- `ordem` (string): Sort order (ASC/DESC)
- `ordenarPor` (string): Sort field

#### Response Structure:
```json
{
  "dados": [
    {
      "id": 220595,
      "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/220595",
      "nome": "Arthur Oliveira Maia",
      "siglaPartido": "PP",
      "uriPartido": "https://dadosabertos.camara.leg.br/api/v2/partidos/36899",
      "siglaUf": "BA",
      "idLegislatura": 57,
      "urlFoto": "https://www.camara.leg.br/internet/deputado/bandep/220595.jpg",
      "email": "dep.arthurmaia@camara.leg.br"
    }
  ],
  "links": [...],
  "count": 2156
}
```

### 2. **Deputy Details** - Complete Deputy Profile
**Endpoint**: `/deputados/{id}`
**Description**: Comprehensive personal and political information for a specific deputy
**Key Use**: Primary identity source for politician correlation across systems

#### Response Structure:
```json
{
  "dados": {
    "id": 220595,
    "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/220595",
    "nomeCivil": "Arthur Oliveira Maia",
    "cpf": "67821090425",
    "sexo": "M",
    "urlWebsite": "http://arthurmaia.com.br",
    "redeSocial": [
      "https://www.facebook.com/arthurmaiadeputado",
      "https://twitter.com/arthurmaia_"
    ],
    "dataNascimento": "1971-05-28",
    "dataFalecimento": null,
    "ufNascimento": "BA",
    "municipioNascimento": "Salvador",
    "escolaridade": "Superior Completo",
    "ultimoStatus": {
      "id": 220595,
      "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/220595",
      "nome": "Arthur Maia",
      "siglaPartido": "PP",
      "uriPartido": "https://dadosabertos.camara.leg.br/api/v2/partidos/36899",
      "siglaUf": "BA",
      "idLegislatura": 57,
      "urlFoto": "https://www.camara.leg.br/internet/deputado/bandep/220595.jpg",
      "email": "dep.arthurmaia@camara.leg.br",
      "data": "2024-09-27T16:35:42",
      "nomeEleitoral": "Arthur Maia",
      "gabinete": {
        "nome": "Arthur Maia",
        "predio": "4",
        "sala": "602",
        "andar": "6",
        "telefone": "(61) 3215-5602",
        "email": "dep.arthurmaia@camara.leg.br"
      },
      "situacao": "Exercício",
      "condicaoEleitoral": "Titular",
      "descricaoStatus": "Deputado Federal - Exercício"
    }
  }
}
```

**Key Fields for Integration**:
- `cpf`: **Primary key** for TSE electoral correlation
- `nomeCivil`: Legal name for exact matching
- `ultimoStatus.siglaPartido`: Current party affiliation
- `ultimoStatus.siglaUf`: Electoral state
- `ultimoStatus.idLegislatura`: Current legislature
- `ultimoStatus.email`: Contact information

### 3. **Deputy Expenses** - Financial Transactions
**Endpoint**: `/deputados/{id}/despesas`
**Description**: Detailed parliamentary expense records including vendor information
**Key Use**: Primary source for financial network analysis and vendor correlation

#### Parameters:
- `ano` (integer): Filter by year
- `mes` (integer): Filter by month (1-12)
- `cnpjCpfFornecedor` (string): Filter by vendor CNPJ/CPF
- `ordem` (string): Sort order
- `ordenarPor` (string): Sort field (ano, mes, valorLiquido)
- `itens` (integer): Results per page

#### Response Structure:
```json
{
  "dados": [
    {
      "ano": 2024,
      "mes": 8,
      "tipoDespesa": "PASSAGENS AÉREAS",
      "codDocumento": 6811155,
      "tipoDocumento": "Nota Fiscal",
      "codTipoDocumento": 2,
      "dataDocumento": "2024-08-26",
      "numDocumento": "0000008270",
      "valorDocumento": 6100.00,
      "urlDocumento": "https://www.camara.leg.br/cota-parlamentar/documentos/publ/220595/2024/6811155.pdf",
      "nomeFornecedor": "LATAM AIRLINES BRASIL",
      "cnpjCpfFornecedor": "02012862000160",
      "valorLiquido": 6100.00,
      "valorGlosa": 0,
      "numRessarcimento": null,
      "codLote": 1659822,
      "parcela": 0
    }
  ]
}
```

**Key Fields for Analysis**:
- `cnpjCpfFornecedor`: **Critical** for vendor sanctions cross-reference
- `valorLiquido`: Net amount paid
- `valorGlosa`: Rejected amount (corruption indicator)
- `urlDocumento`: PDF receipt for verification
- `tipoDespesa`: Expense category for pattern analysis

### 4. **External Mandates** - Political Career History
**Endpoint**: `/deputados/{id}/mandatosExternos`
**Description**: Previous political positions held outside the federal chamber
**Key Use**: Career history mapping and political trajectory analysis

#### Response Structure:
```json
{
  "dados": [
    {
      "cargo": "Deputado Estadual",
      "siglaUf": "BA",
      "municipio": null,
      "anoInicio": "2007",
      "anoFim": "2011",
      "siglaPartidoEleicao": "DEM",
      "uriPartidoEleicao": "https://dadosabertos.camara.leg.br/api/v2/partidos/36844"
    },
    {
      "cargo": "Vereador",
      "siglaUf": "BA",
      "municipio": "Salvador",
      "anoInicio": "2001",
      "anoFim": "2007",
      "siglaPartidoEleicao": "PFL",
      "uriPartidoEleicao": null
    }
  ]
}
```

### 5. **Committee Memberships** - Legislative Committees
**Endpoint**: `/deputados/{id}/orgaos`
**Description**: Current and historical committee memberships
**Key Use**: Legislative influence mapping and specialization analysis

#### Response Structure:
```json
{
  "dados": [
    {
      "idOrgao": 180,
      "uriOrgao": "https://dadosabertos.camara.leg.br/api/v2/orgaos/180",
      "siglaOrgao": "CCJC",
      "nomeOrgao": "Comissão de Constituição e Justiça e de Cidadania",
      "nomePublicacao": null,
      "titulo": "Titular",
      "dataInicio": "2023-02-09",
      "dataFim": null
    }
  ]
}
```

### 6. **Parliamentary Fronts** - Cross-Party Groups
**Endpoint**: `/deputados/{id}/frentes`
**Description**: Parliamentary front memberships (caucuses)
**Key Use**: Policy interest mapping and cross-party coalition analysis

#### Response Structure:
```json
{
  "dados": [
    {
      "id": 54255,
      "uri": "https://dadosabertos.camara.leg.br/api/v2/frentes/54255",
      "titulo": "Frente Parlamentar Mista da Micro e Pequena Empresa",
      "dataInicio": "2023-03-06",
      "dataFim": null
    }
  ]
}
```

### 7. **Events** - Parliamentary Activities
**Endpoint**: `/deputados/{id}/eventos`
**Description**: Event participation including sessions, hearings, and meetings
**Key Use**: Activity level monitoring and engagement analysis

#### Parameters:
- `dataInicio` (string): Start date (YYYY-MM-DD)
- `dataFim` (string): End date (YYYY-MM-DD)
- `ordem` (string): Sort order
- `ordenarPor` (string): Sort field

#### Response Structure:
```json
{
  "dados": [
    {
      "id": 67890,
      "uri": "https://dadosabertos.camara.leg.br/api/v2/eventos/67890",
      "dataHoraInicio": "2024-09-25T14:00",
      "dataHoraFim": "2024-09-25T18:00",
      "situacao": "Encerrada",
      "descricaoTipo": "Audiência Pública",
      "descricao": "Audiência pública sobre política energética",
      "localExterno": null,
      "orgaos": [
        {
          "id": 180,
          "sigla": "CCJC",
          "nome": "Comissão de Constituição e Justiça e de Cidadania",
          "apelido": "CCJ"
        }
      ]
    }
  ]
}
```

### 8. **Professions** - Professional Background
**Endpoint**: `/deputados/{id}/profissoes`
**Description**: Professional classifications and backgrounds
**Key Use**: Professional network analysis and conflict of interest identification

#### Response Structure:
```json
{
  "dados": [
    {
      "id": 25,
      "titulo": "Advogado",
      "codTipoItem": "1999",
      "dataInicio": "2023-02-01",
      "dataFim": null
    }
  ]
}
```

### 9. **Occupations** - Current Positions
**Endpoint**: `/deputados/{id}/ocupacoes`
**Description**: Current institutional positions and roles
**Key Use**: Power structure mapping and institutional influence analysis

#### Response Structure:
```json
{
  "dados": [
    {
      "id": 12345,
      "titulo": "Presidente da Comissão de Constituição e Justiça",
      "dataInicio": "2023-02-01",
      "dataFim": null,
      "entidade": {
        "id": 180,
        "nome": "Comissão de Constituição e Justiça e de Cidadania",
        "sigla": "CCJC"
      }
    }
  ]
}
```

### 10. **Discourses** - Parliamentary Speeches
**Endpoint**: `/deputados/{id}/discursos`
**Description**: Parliamentary speeches and interventions
**Key Use**: Position tracking and discourse analysis

#### Parameters:
- `dataInicio` (string): Start date
- `dataFim` (string): End date
- `ordem` (string): Sort order
- `ordenarPor` (string): Sort field

#### Response Structure:
```json
{
  "dados": [
    {
      "id": "12345",
      "dataHoraInicio": "2024-09-25T14:30",
      "transcricao": "Sr. Presidente, nobres colegas...",
      "uriEvento": "https://dadosabertos.camara.leg.br/api/v2/eventos/67890",
      "urlTexto": "https://www.camara.leg.br/internet/sitaqweb/TextoHTML.asp?etapa=5&nuSessao=278.1.57.O",
      "palavrasChave": ["política energética", "sustentabilidade"]
    }
  ]
}
```

## = Pagination and Filtering

### Standard Pagination
All list endpoints support pagination:
- `pagina` (integer): Page number (default: 1)
- `itens` (integer): Items per page (max: 100, default: 15)

### Response Structure
```json
{
  "dados": [...],
  "links": [
    {
      "rel": "self",
      "href": "https://dadosabertos.camara.leg.br/api/v2/deputados?pagina=1"
    },
    {
      "rel": "next",
      "href": "https://dadosabertos.camara.leg.br/api/v2/deputados?pagina=2"
    }
  ]
}
```

### Navigation Headers
- **X-Total-Count**: Total number of records
- **Link**: Navigation links (first, prev, next, last)

## =Ê Data Integration Strategy

### For Politician Identification
1. **Primary Key**: Use `cpf` from `/deputados/{id}` for TSE correlation
2. **Backup Matching**: Combine `nomeCivil` + `dataNascimento` + `siglaUf`
3. **Electoral Validation**: Cross-reference with TSE candidate records
4. **Name Normalization**: Handle electoral vs. civil name variations

### For Financial Network Analysis
1. **Vendor Extraction**: Extract all `cnpjCpfFornecedor` from expenses
2. **Sanctions Cross-Reference**: Check vendor CNPJs against Portal da Transparência
3. **Pattern Analysis**: Identify unusual expense categories or amounts
4. **Timeline Correlation**: Match expense dates with political events

### For Political Career Mapping
1. **Career Progression**: Track positions from `mandatosExternos`
2. **Committee Influence**: Map power through `orgaos` memberships
3. **Policy Interests**: Analyze `frentes` participation
4. **Activity Levels**: Monitor `eventos` participation

##   Known Issues and Limitations

### 1. **Missing Electoral Numbers**
- **Issue**: No `numeroEleitoral` field for direct TSE correlation
- **Workaround**: Use CPF-based matching with TSE candidate data
- **Impact**: Requires additional TSE API calls for complete correlation

### 2. **Inconsistent Email Availability**
- **Issue**: Email field often null or missing
- **Workaround**: Check both deputy profile and `gabinete.email`
- **Impact**: Contact information may be incomplete

### 3. **Large Expense Datasets**
- **Issue**: Some deputies have 1000+ expense records per year
- **Strategy**: Use date filters and pagination for memory efficiency
- **Optimization**: Cache processed data locally

### 4. **Document URL Access**
- **Issue**: PDF receipt URLs may become inaccessible over time
- **Strategy**: Download and store critical documents immediately
- **Priority**: Focus on high-value or suspicious transactions

## =» Implementation Examples

### Python - Complete Deputy Profile Collection
```python
import requests
import time
from typing import Dict, List, Any

class CamaraClient:
    def __init__(self):
        self.base_url = "https://dadosabertos.camara.leg.br/api/v2/"
        self.rate_limit_delay = 0.5

    def get_deputy_complete_profile(self, deputy_id: int) -> Dict[str, Any]:
        """Get complete deputy profile across all endpoints"""

        profile = {
            'deputy_id': deputy_id,
            'basic_info': {},
            'expenses': [],
            'committees': [],
            'fronts': [],
            'external_mandates': [],
            'events': [],
            'professions': [],
            'occupations': []
        }

        # Basic information
        profile['basic_info'] = self._make_request(f"deputados/{deputy_id}")

        # Financial records (last 2 years)
        current_year = 2024
        for year in [current_year - 1, current_year]:
            expenses = self._make_request(f"deputados/{deputy_id}/despesas", {'ano': year})
            profile['expenses'].extend(expenses.get('dados', []))

        # Political activities
        profile['committees'] = self._make_request(f"deputados/{deputy_id}/orgaos").get('dados', [])
        profile['fronts'] = self._make_request(f"deputados/{deputy_id}/frentes").get('dados', [])
        profile['external_mandates'] = self._make_request(f"deputados/{deputy_id}/mandatosExternos").get('dados', [])

        # Professional background
        profile['professions'] = self._make_request(f"deputados/{deputy_id}/profissoes").get('dados', [])
        profile['occupations'] = self._make_request(f"deputados/{deputy_id}/ocupacoes").get('dados', [])

        return profile

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request with rate limiting"""
        time.sleep(self.rate_limit_delay)
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params or {})
        response.raise_for_status()
        return response.json()

# Usage
client = CamaraClient()
profile = client.get_deputy_complete_profile(220595)
print(f"Deputy: {profile['basic_info']['dados']['nomeCivil']}")
print(f"Expenses: {len(profile['expenses'])} records")
print(f"Committees: {len(profile['committees'])} memberships")
```

### Python - Financial Network Analysis
```python
def extract_vendor_network(deputy_id: int) -> List[Dict[str, Any]]:
    """Extract vendor network from deputy expenses"""

    client = CamaraClient()
    vendors = {}

    # Get expenses for last 3 years
    for year in [2022, 2023, 2024]:
        expenses_response = client._make_request(
            f"deputados/{deputy_id}/despesas",
            {'ano': year}
        )

        for expense in expenses_response.get('dados', []):
            cnpj_cpf = expense.get('cnpjCpfFornecedor')
            if not cnpj_cpf:
                continue

            if cnpj_cpf not in vendors:
                vendors[cnpj_cpf] = {
                    'cnpj_cpf': cnpj_cpf,
                    'name': expense.get('nomeFornecedor'),
                    'entity_type': 'COMPANY' if len(cnpj_cpf) == 14 else 'INDIVIDUAL',
                    'total_amount': 0,
                    'transaction_count': 0,
                    'expense_categories': set(),
                    'suspicious_indicators': []
                }

            vendor = vendors[cnpj_cpf]
            vendor['total_amount'] += float(expense.get('valorLiquido', 0))
            vendor['transaction_count'] += 1
            vendor['expense_categories'].add(expense.get('tipoDespesa'))

            # Flag suspicious patterns
            if float(expense.get('valorGlosa', 0)) > 0:
                vendor['suspicious_indicators'].append('REJECTED_AMOUNT')

    # Convert sets to lists for JSON serialization
    for vendor in vendors.values():
        vendor['expense_categories'] = list(vendor['expense_categories'])

    return list(vendors.values())

# Usage
vendors = extract_vendor_network(220595)
high_value_vendors = [v for v in vendors if v['total_amount'] > 50000]
print(f"High-value vendors: {len(high_value_vendors)}")
```

### CURL Examples
```bash
# Get all active deputies
curl "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome"

# Get specific deputy details
curl "https://dadosabertos.camara.leg.br/api/v2/deputados/220595"

# Get deputy expenses for 2024
curl "https://dadosabertos.camara.leg.br/api/v2/deputados/220595/despesas?ano=2024"

# Get deputy committees
curl "https://dadosabertos.camara.leg.br/api/v2/deputados/220595/orgaos"

# Search deputies by name
curl "https://dadosabertos.camara.leg.br/api/v2/deputados?nome=Arthur"

# Get deputies from specific state
curl "https://dadosabertos.camara.leg.br/api/v2/deputados?siglaUf=BA"
```

## = Data Quality and Validation

### Required Field Validation
- **CPF Format**: 11 digits, no formatting characters
- **CNPJ Format**: 14 digits, no formatting characters
- **Date Format**: YYYY-MM-DD (ISO 8601)
- **Money Format**: Float values with 2 decimal places

### Data Integrity Checks
1. **CPF Validation**: Use Brazilian CPF algorithm
2. **CNPJ Validation**: Use Brazilian CNPJ algorithm
3. **Date Consistency**: Validate date ranges and chronology
4. **Amount Validation**: Check for negative values and outliers

### Cross-Reference Validation
1. **Party Consistency**: Verify party affiliations across endpoints
2. **Committee Membership**: Validate committee existence and periods
3. **Expense Categories**: Check against known valid categories
4. **Vendor CNPJs**: Validate format and existence

## =È Performance Optimization

### Caching Strategy
1. **Deputy Profiles**: Cache basic information (changes infrequently)
2. **Committee Structure**: Cache committee metadata
3. **Party Information**: Cache party details and hierarchies
4. **Processed Expenses**: Cache cleaned and validated financial data

### Batch Processing
1. **Bulk Deputy Processing**: Process multiple deputies in parallel
2. **Year-Based Chunking**: Handle expense data year by year
3. **Committee Batch Updates**: Update committee memberships in batches
4. **Vendor Deduplication**: Process vendor networks across multiple deputies

### Memory Management
1. **Streaming Processing**: Handle large datasets with generators
2. **Selective Loading**: Load only required fields for specific analyses
3. **Regular Cleanup**: Clear processed data from memory regularly
4. **Database Offloading**: Store processed data in PostgreSQL immediately

## =€ Integration with CLI4 System

The Câmara dos Deputados API is the primary data source in the CLI4 system for:

### 1. **Politician Population**
- **Identity Establishment**: Create master politician records with CPF
- **TSE Correlation**: Use CPF to link with electoral history
- **Basic Demographics**: Extract birth date, education, location
- **Contact Information**: Gather office and personal contact details

### 2. **Financial Records Population**
- **Vendor Network Mapping**: Extract all CNPJs for sanctions cross-reference
- **Expense Pattern Analysis**: Identify unusual spending patterns
- **Document Archival**: Download suspicious transaction receipts
- **Corruption Indicators**: Flag rejected amounts and problematic vendors

### 3. **Career History Population**
- **Political Trajectory**: Map career progression through external mandates
- **Committee Influence**: Track committee positions and duration
- **Policy Specialization**: Analyze parliamentary front participation
- **Activity Monitoring**: Track event participation and engagement

### 4. **Professional Background Population**
- **Occupation History**: Extract professional background for conflict analysis
- **Educational Background**: Map educational qualifications
- **Private Sector Connections**: Identify potential conflicts of interest
- **Expertise Areas**: Map professional specializations to committee assignments

### CLI4 Implementation Commands
```bash
# Populate politician base records
python cli4/main.py populate-politicians --active-only --limit 100

# Update financial records
python cli4/main.py populate-financial --start-year 2020 --end-year 2024

# Populate career histories
python cli4/main.py populate-career --politician-ids 1 2 3

# Update professional backgrounds
python cli4/main.py populate-professional --all

# Validate data integrity
python cli4/main.py validate --table politicians --check-cpf
```

### Integration Architecture
```
Câmara API ’ CLI4 Populators ’ PostgreSQL ’ Analysis Tools
    “              “               “            “
Deputies     Politician     unified_       Network
Expenses  ’  Records    ’   politicians ’  Analysis
Committees   Financial      financial_     Corruption
Events       Records        records        Detection
```

## =Ú Additional Resources

- **Official API Portal**: https://dadosabertos.camara.leg.br/
- **Swagger Documentation**: https://dadosabertos.camara.leg.br/swagger/api.html
- **Chamber Website**: https://www.camara.leg.br/
- **Data Update Schedule**: Daily at 6:00 AM Brasília time
- **Support Contact**: dadosabertos@camara.leg.br
- **Terms of Use**: https://dadosabertos.camara.leg.br/termos-de-uso

## <¯ Conclusion

The Câmara dos Deputados API provides comprehensive access to Brazilian federal legislative data, serving as the foundation for political transparency analysis. With complete deputy profiles, detailed financial records, and extensive political activity data, this API enables sophisticated corruption detection, network analysis, and political accountability research.

The CLI4 system successfully leverages this API to maintain a comprehensive database of federal deputies, their financial networks, and political activities, enabling real-time correlation with sanctions data from other government sources. The API's open access, reliable structure, and comprehensive coverage make it an essential tool for Brazilian political transparency initiatives.

Key strengths include complete financial transparency, detailed career tracking, and robust cross-reference capabilities through CPF-based identity correlation. The main challenges involve handling large datasets efficiently and managing the complexity of political network relationships across multiple data endpoints.

---

*Last Updated: September 2025*
*API Version: v2*
*Documentation by: CLI4 System Analysis*
*Total Endpoints Documented: 10 core deputy endpoints*