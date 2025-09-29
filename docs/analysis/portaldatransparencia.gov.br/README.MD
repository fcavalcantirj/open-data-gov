# Portal da Transparência API Documentation

## 🏛️ Overview

The **Portal da Transparência** (Transparency Portal) is the Brazilian federal government's official API for accessing public spending, contracts, sanctions, and administrative data. This API is crucial for transparency analysis, corruption detection, and financial accountability research.

**Base URL**: `https://api.portaldatransparencia.gov.br/api-de-dados/`
**Swagger UI**: `https://api.portaldatransparencia.gov.br/swagger-ui/index.html`
**Authentication**: API Key required (via header `chave-api-dados`)
**Response Format**: JSON
**Rate Limiting**: Yes (approximately 30 requests/minute)

## 🔑 Authentication

### Getting an API Key
1. Visit: https://portaldatransparencia.gov.br/api-de-dados
2. Register with your CPF (Brazilian tax ID)
3. API key is personal and non-transferable
4. Free for non-commercial use

### Using the API Key
```http
GET /api-de-dados/{endpoint}
Headers:
  chave-api-dados: YOUR_API_KEY_HERE
```

## 📚 Available Endpoints

### 1. **CEPIM** - Cadastro de Empresas Punidas
**Endpoint**: `/api-de-dados/cepim`
**Description**: Sanctioned companies registry - entities prohibited from contracting with federal government
**Key Use**: Cross-reference politician vendor payments with sanctioned companies for corruption detection

#### Parameters:
- `pagina` (integer): Page number for pagination
- `cnpjSancionado` (string): Filter by sanctioned company CNPJ
- `cpfSancionado` (string): Filter by sanctioned individual CPF
- `nomeSancionado` (string): Filter by sanctioned entity name
- `ufSancionado` (string): Filter by state (UF)
- `orgaoSancionador` (string): Filter by sanctioning agency
- `dataInicialSancao` (string): Start date filter (dd/MM/yyyy)
- `dataFinalSancao` (string): End date filter (dd/MM/yyyy)

#### Response Fields:
```json
{
  "id": 12345,
  "dataReferencia": "15/09/2024",
  "motivo": "Fraude em licitação",
  "orgaoSuperior": {
    "nome": "MINISTERIO DA SAUDE",
    "codigoSIAFI": "36000"
  },
  "pessoaJuridica": {
    "cnpj": "12345678000199",
    "razaoSocialReceita": "EMPRESA EXEMPLO LTDA",
    "nomeFantasiaReceita": "EXEMPLO"
  },
  "convenio": {
    "codigo": "123456",
    "objeto": "Construção de hospital"
  },
  "dataInicioSancao": "01/01/2024",
  "dataFimSancao": "01/01/2029"
}
```

### 2. **CEIS** - Cadastro de Empresas Inidôneas e Suspensas
**Endpoint**: `/api-de-dados/ceis`
**Description**: Registry of companies declared unsuitable or suspended from government contracts
**Key Use**: Primary source for vendor sanctions in corruption detection

#### Parameters:
- `pagina` (integer): Page number
- `cnpjSancionado` (string): Filter by CNPJ ⚠️ **BROKEN** - Returns empty even for known sanctioned CNPJs
- `nomeSancionado` (string): Filter by name
- `ufSancionado` (string): Filter by state
- `orgaoSancionador` (string): Filter by sanctioning agency

#### Response Fields:
```json
{
  "id": 1,
  "tipo": "Inidoneidade",
  "dataPublicacao": "15/09/2024",
  "pessoaJuridica": {
    "cnpj": "12345678000199",
    "razaoSocial": "EMPRESA SANCIONADA LTDA"
  },
  "sancionado": {
    "nome": "EMPRESA SANCIONADA LTDA",
    "codigoFormatado": "12.345.678/0001-99"
  },
  "orgaoSancionador": {
    "nome": "CONTROLADORIA-GERAL DA UNIAO",
    "poder": "EXECUTIVO"
  },
  "fundamentacaoLegal": "Lei 8.666/93, art. 87, inciso IV",
  "dataInicioSancao": "01/01/2024",
  "dataFimSancao": "01/01/2029"
}
```

### 3. **CNEP** - Cadastro Nacional de Empresas Punidas
**Endpoint**: `/api-de-dados/cnep`
**Description**: National registry of punished companies based on Anti-Corruption Law
**Key Use**: Identify companies involved in corruption acts against public administration

#### Parameters:
- `pagina` (integer): Page number
- `cnpjSancionado` (string): Filter by CNPJ
- `cpfSancionado` (string): Filter by CPF
- `nomeSancionado` (string): Filter by name
- `ufSancionado` (string): Filter by state

### 4. **Contratos** - Government Contracts
**Endpoint**: `/api-de-dados/contratos`
**Description**: Federal government contracts with suppliers
**Key Use**: Track contract values and patterns with specific vendors

#### Parameters:
- `codigoOrgao` (string): **REQUIRED** - Agency code
- `cnpjContratada` (string): Filter by contracted company CNPJ
- `dataInicial` (string): Start date (dd/MM/yyyy)
- `dataFinal` (string): End date (dd/MM/yyyy)
- `pagina` (integer): Page number

#### Response Fields:
```json
{
  "id": "123456",
  "numero": "01/2024",
  "dataAssinatura": "01/01/2024",
  "dataInicioVigencia": "01/01/2024",
  "dataFimVigencia": "31/12/2024",
  "valorInicial": 1000000.00,
  "objeto": "Prestação de serviços de consultoria",
  "orgao": {
    "codigo": "20101",
    "nome": "CAMARA DOS DEPUTADOS"
  },
  "contratado": {
    "cnpjCpf": "12345678000199",
    "nome": "EMPRESA CONTRATADA LTDA"
  }
}
```

### 5. **Servidores** - Public Servants
**Endpoint**: `/api-de-dados/servidores`
**Description**: Federal public servants registry
**Key Use**: Identify public servants for nepotism analysis

#### Parameters:
- `codigoOrgao` (string): **REQUIRED** - Agency code
- `nome` (string): Filter by servant name
- `cpf` (string): Filter by CPF
- `matricula` (string): Filter by registration number
- `pagina` (integer): Page number

### 6. **Cartões** - Government Payment Cards
**Endpoint**: `/api-de-dados/cartoes`
**Description**: Government credit card expenses
**Key Use**: Track detailed spending patterns

#### Parameters:
- `mesAnoInicio` (string): **REQUIRED** - Start period (MMYYYY)
- `mesAnoFim` (string): **REQUIRED** - End period (MMYYYY)
- `codigoOrgao` (string): Filter by agency
- `cpfPortador` (string): Filter by cardholder CPF
- `pagina` (integer): Page number

### 7. **Despesas** - Government Expenses
**Endpoint**: `/api-de-dados/despesas`
**Description**: Detailed federal government expenses
**Key Use**: Comprehensive spending analysis

#### Parameters:
- `mesAnoInicio` (string): **REQUIRED** - Start period (MMYYYY)
- `mesAnoFim` (string): **REQUIRED** - End period (MMYYYY)
- `codigoOrgao` (string): Filter by agency
- `pagina` (integer): Page number

### 8. **Licitações** - Public Bids
**Endpoint**: `/api-de-dados/licitacoes`
**Description**: Federal government procurement processes
**Key Use**: Track bidding patterns and participants

#### Parameters:
- `codigoOrgao` (string): **REQUIRED** - Agency code
- `dataInicial` (string): Start date
- `dataFinal` (string): End date
- `cnpjParticipante` (string): Filter by participant CNPJ
- `pagina` (integer): Page number

### 9. **Convênios** - Government Agreements
**Endpoint**: `/api-de-dados/convenios`
**Description**: Cooperation agreements and transfers
**Key Use**: Track resource transfers to entities

#### Parameters:
- `convenente` (string): Filter by recipient
- `codigoOrgao` (string): Filter by agency
- `dataInicial` (string): Start date
- `dataFinal` (string): End date
- `pagina` (integer): Page number

### 10. **Transferências** - Resource Transfers
**Endpoint**: `/api-de-dados/transferencias`
**Description**: Direct transfers to states and municipalities
**Key Use**: Track federal resource distribution

#### Parameters:
- `mesAnoInicio` (string): Start period
- `mesAnoFim` (string): End period
- `codigoIbge` (string): Filter by IBGE municipality code
- `pagina` (integer): Page number

### 11. **Auxílio Emergencial** - Emergency Aid (COVID-19)
**Endpoint**: `/api-de-dados/auxilio-emergencial`
**Description**: COVID-19 emergency aid payments
**Key Use**: Track emergency benefit distribution

#### Parameters:
- `mesAno` (string): Period (MMYYYY)
- `codigoIbge` (string): Municipality code
- `cpf` (string): Beneficiary CPF
- `pagina` (integer): Page number

### 12. **Benefícios ao Cidadão** - Citizen Benefits
**Endpoint**: `/api-de-dados/beneficios-cidadao`
**Description**: Social benefit payments (Bolsa Família, BPC, etc.)
**Key Use**: Social program analysis

#### Parameters:
- `codigoBeneficio` (string): Benefit type code
- `mesAno` (string): Period (MMYYYY)
- `codigoIbge` (string): Municipality code
- `cpf` (string): Beneficiary CPF
- `pagina` (integer): Page number

### 13. **Viagens** - Official Travels
**Endpoint**: `/api-de-dados/viagens`
**Description**: Government official travel expenses
**Key Use**: Track travel patterns and costs

#### Parameters:
- `codigoOrgao` (string): Agency code
- `cpf` (string): Traveler CPF
- `dataInicial` (string): Start date
- `dataFinal` (string): End date
- `pagina` (integer): Page number

## 🔄 Pagination

All endpoints support pagination with standard parameters:
- `pagina`: Page number (starts at 1)
- Default page size: 15 records
- Maximum records per page: 500 (varies by endpoint)

### Pagination Headers
The API returns pagination info in response headers:
- `X-Total-Count`: Total number of records
- `Link`: Links to first, prev, next, last pages

## 📊 Data Integration Strategy

### For Corruption Detection
1. **Primary Source**: CEPIM and CEIS endpoints for sanctions
2. **Cross-Reference**: Match politician vendor CNPJs with sanctioned entities
3. **Risk Scoring**: Calculate based on transaction volumes with sanctioned vendors
4. **Timeline Analysis**: Correlate sanction dates with transaction dates

### For Network Analysis
1. **Contract Patterns**: Use Contratos endpoint to identify vendor relationships
2. **Bidding Networks**: Use Licitações to find bid participants
3. **Resource Flows**: Track Convênios and Transferências for resource distribution
4. **Expense Patterns**: Analyze Despesas for spending anomalies

## ⚠️ Known Issues and Limitations

### 1. CNPJ Filter Bug (CEIS Endpoint)
- **Issue**: `cnpjSancionado` parameter returns empty results even for known sanctioned CNPJs
- **Workaround**: Fetch all pages and filter locally (implemented in CLI4)
- **Impact**: Requires fetching ~12,000+ records for complete sanctions database

### 2. Rate Limiting
- **Limit**: Approximately 30 requests per minute
- **Strategy**: Implement exponential backoff and request queuing
- **Headers**: No explicit rate limit headers provided

### 3. Data Completeness
- **CEPIM**: ~12,600 active sanctions (as of Sept 2025)
- **CEIS**: Similar overlap with CEPIM
- **CNEP**: Smaller dataset focused on Anti-Corruption Law violations

### 4. Required Parameters
- Several endpoints require agency codes (`codigoOrgao`)
- Date ranges often required for expense/payment endpoints
- No global search across all sanctions databases

## 💻 Implementation Examples

### Python Example - Fetch All Sanctions
```python
import requests
import time

class PortalClient:
    def __init__(self, api_key):
        self.base_url = "https://api.portaldatransparencia.gov.br/api-de-dados/"
        self.headers = {'chave-api-dados': api_key}

    def fetch_all_sanctions(self):
        sanctions = []
        page = 1

        while True:
            response = requests.get(
                f"{self.base_url}cepim",
                headers=self.headers,
                params={'pagina': page}
            )

            if response.status_code != 200:
                break

            data = response.json()
            if not data:
                break

            sanctions.extend(data)
            page += 1
            time.sleep(2)  # Rate limiting

        return sanctions
```

### CURL Example - Check Specific CNPJ
```bash
curl -X GET "https://api.portaldatransparencia.gov.br/api-de-dados/cepim?cnpjSancionado=12345678000199&pagina=1" \
  -H "chave-api-dados: YOUR_API_KEY"
```

## 🔒 Security and Compliance

- **Personal API Keys**: Keys are tied to individual CPFs
- **Non-Commercial Use**: Free tier for research and transparency
- **Data Protection**: Follow LGPD guidelines when handling personal data
- **Audit Trail**: All API calls should be logged for transparency

## 📈 Performance Tips

1. **Batch Processing**: Fetch complete datasets during off-peak hours
2. **Local Caching**: Store sanctions database locally for fast lookups
3. **Incremental Updates**: Use date filters to fetch only new records
4. **Parallel Processing**: Use multiple endpoints simultaneously (respect rate limits)
5. **Database Indexing**: Index CNPJ/CPF fields for fast cross-referencing

## 🚀 Integration with CLI4 System

The Portal da Transparência API is integrated into the CLI4 system for:
1. **Vendor Sanctions Population**: ~12,600 sanctions for corruption detection
2. **Cross-Reference Analysis**: Match politician expenses with sanctioned vendors
3. **Risk Scoring**: Calculate corruption risk based on vendor relationships
4. **Investigation Support**: Provide evidence trail for transparency research

### CLI4 Commands
```bash
# Populate sanctions database
python cli4/main.py populate-sanctions --max-pages 1500

# Update existing sanctions
python cli4/main.py populate-sanctions --update-existing

# Validate sanctions data
python cli4/main.py validate --table sanctions
```

## 📚 Additional Resources

- **Official Portal**: https://portaldatransparencia.gov.br/
- **API Registration**: https://portaldatransparencia.gov.br/api-de-dados
- **Swagger Documentation**: https://api.portaldatransparencia.gov.br/swagger-ui/
- **Support**: api@portaldatransparencia.gov.br
- **Terms of Use**: https://portaldatransparencia.gov.br/pagina-interna/603392-termos-de-uso

## 🎯 Conclusion

The Portal da Transparência API is a critical component for Brazilian political transparency analysis. Despite some limitations (CNPJ filter bug, rate limiting), it provides comprehensive access to sanctions, contracts, and expense data essential for corruption detection and network analysis. The CLI4 system successfully integrates this API to maintain a local sanctions database for rapid cross-referencing with politician financial records.

---

*Last Updated: September 2025*
*API Version: v1 (inferred from behavior)*
*Documentation by: CLI4 System Analysis*