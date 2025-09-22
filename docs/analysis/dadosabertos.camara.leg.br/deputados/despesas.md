# /deputados/{id}/despesas

**Endpoint:** `GET /deputados/{id}/despesas`

## Purpose
Retrieve parliamentary expenses (CEAP - Cota para o Exercício da Atividade Parlamentar) for a specific deputy. This is the MOST CRITICAL endpoint for corruption detection and financial transparency.

## Parameters

### Path Parameters
- **`id`** (required): Deputy ID (e.g., 160541)

### Query Parameters
- **`ano`** (optional but recommended): Year filter (e.g., 2024)
- **`mes`** (optional): Month filter (1-12)
- **`itens`** (optional): Items per page (default: 100, max: 500)
- **`pagina`** (optional): Page number for pagination

## Request Examples
```
GET /deputados/160541/despesas?ano=2024
GET /deputados/160541/despesas?ano=2024&mes=3
GET /deputados/160541/despesas?ano=2024&itens=100&pagina=1
```

## Response Schema
```json
{
  "dados": [
    {
      "ano": 2024,
      "mes": 3,
      "tipoDespesa": "MANUTENÇÃO DE ESCRITÓRIO DE APOIO À ATIVIDADE PARLAMENTAR",
      "codDocumento": 7711615,
      "tipoDocumento": "Nota Fiscal",
      "codTipoDocumento": 0,
      "dataDocumento": "2024-03-26T00:00:00",
      "numDocumento": "00000773",
      "valorDocumento": 1000.0,
      "urlDocumento": "https://www.camara.leg.br/cota-parlamentar/documentos/publ/2377/2024/7711615.pdf",
      "nomeFornecedor": "TECNEGOCIOS SOLUÇÕES EM INFORMÁTICA LTDA",
      "cnpjCpfFornecedor": "11521613000190",
      "valorLiquido": 1000.0,
      "valorGlosa": 0.0,
      "numRessarcimento": "",
      "codLote": 2026388,
      "parcela": 0
    }
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://dadosabertos.camara.leg.br/api/v2/deputados/160541/despesas?ano=2024&pagina=1"
    },
    {
      "rel": "next",
      "href": "https://dadosabertos.camara.leg.br/api/v2/deputados/160541/despesas?ano=2024&pagina=2"
    }
  ]
}
```

## Response Fields

| Field | Type | Description | Critical for Analysis |
|-------|------|-------------|----------------------|
| **ano** | integer | Expense year | ✅ Temporal analysis |
| **mes** | integer | Expense month | ✅ Spending patterns |
| **tipoDespesa** | string | Expense category | ✅ Category anomaly detection |
| **codDocumento** | integer | Document code | ✅ Unique identifier |
| **tipoDocumento** | string | Document type (e.g., "Nota Fiscal") | |
| **dataDocumento** | datetime | Document date | ✅ Timeline tracking |
| **numDocumento** | string | Document number | |
| **valorDocumento** | float | Document value | ✅ Amount analysis |
| **urlDocumento** | string | Direct PDF link | ✅ Verification |
| **nomeFornecedor** | string | Vendor name | ✅ Network analysis |
| **cnpjCpfFornecedor** | string | Vendor CNPJ/CPF | 🔥 **CRITICAL** - Sanctions cross-reference |
| **valorLiquido** | float | Net amount paid | ✅ Actual expense |
| **valorGlosa** | float | Amount rejected/returned | ✅ Irregularity indicator |
| **numRessarcimento** | string | Reimbursement number | |
| **codLote** | integer | Batch code | |
| **parcela** | integer | Installment number | |

## Expense Types (tipoDespesa)
Common categories include:
- MANUTENÇÃO DE ESCRITÓRIO DE APOIO À ATIVIDADE PARLAMENTAR
- PASSAGEM AÉREA - SIGEPA
- COMBUSTÍVEIS E LUBRIFICANTES
- TELEFONIA
- DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR
- CONSULTORIAS, PESQUISAS E TRABALHOS TÉCNICOS
- LOCAÇÃO OU FRETAMENTO DE VEÍCULOS AUTOMOTORES

## Data Lake Value

### 🔥 Critical for Corruption Detection
1. **cnpjCpfFornecedor**: Cross-reference with Portal Transparência sanctions
2. **Vendor patterns**: Identify recurring suspicious vendors
3. **Amount anomalies**: Detect unusual spending patterns
4. **Document verification**: Direct PDF links for audit trail

### Analysis Opportunities
- **Time series analysis**: Monthly/yearly spending trends
- **Vendor network mapping**: Relationship patterns
- **Category analysis**: Spending distribution anomalies
- **Glosa tracking**: Rejected expense patterns

## Implementation Notes

### Recommended Crawling Strategy
```python
# Crawl all expenses for current year
for month in range(1, 13):
    expenses = get_expenses(deputy_id, year=2024, month=month)
    process_cnpjs_for_sanctions(expenses)
```

### Data Volume
- Arthur Lira 2024: ~169 expense records
- Average deputy: 100-300 records per year
- 513 active deputies = ~100,000-150,000 records per year

### Rate Limiting
- No explicit limits observed
- Recommend 1-2 requests per second
- Use pagination for large datasets

## Known Issues
- None - fully functional endpoint
- Reliable performance
- Complete data from 2008-present

## Priority: **CRITICAL** 🔥
This is THE most important endpoint for financial transparency and corruption detection in the entire API.