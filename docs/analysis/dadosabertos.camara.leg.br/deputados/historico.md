# /deputados/{id}/historico

**Endpoint:** `GET /deputados/{id}/historico`

## Purpose
Track changes in parliamentary exercise status for a deputy over time. This includes changes in party affiliation, leadership positions, temporary absences, and status modifications.

## Parameters

### Path Parameters
- **`id`** (required): Deputy ID (e.g., 160541)

### Query Parameters
- **`dataInicio`** (required for large datasets): Start date in format `AAAA-MM-DD` (e.g., 2024-01-01)
- **`dataFim`** (required for large datasets): End date in format `AAAA-MM-DD` (e.g., 2025-01-01)
- **`itens`** (optional): Items per page (default: 100)
- **`pagina`** (optional): Page number for pagination

## ⚠️ IMPORTANT: Date Parameters Required
Without date parameters, this endpoint often returns 504 Gateway Timeout due to large historical datasets. Always use date ranges!

## Request Examples
```
✅ CORRECT - With date range:
GET /deputados/160541/historico?dataInicio=2024-01-01&dataFim=2025-01-01

✅ CORRECT - Last 30 days:
GET /deputados/160541/historico?dataInicio=2024-08-20&dataFim=2024-09-20

❌ INCORRECT - Will timeout:
GET /deputados/160541/historico
```

## Response Schema
```json
{
  "dados": [
    {
      "dataHora": "2024-02-01T10:00:00",
      "idSituacao": 1,
      "situacao": "Exercício",
      "descricao": "Assumiu exercício",
      "siglaPartido": "PP",
      "siglaUf": "AL",
      "idLegislatura": 57,
      "idEvento": 123456,
      "uriEvento": "https://dadosabertos.camara.leg.br/api/v2/eventos/123456",
      "tipoEvento": "Posse"
    },
    {
      "dataHora": "2023-11-15T14:30:00",
      "idSituacao": 2,
      "situacao": "Licenciado",
      "descricao": "Licença médica",
      "siglaPartido": "PP",
      "siglaUf": "AL",
      "idLegislatura": 57,
      "dataInicio": "2023-11-15",
      "dataFim": "2023-11-30"
    }
  ],
  "links": [...]
}
```

## Response Fields

| Field | Type | Description | Analysis Value |
|-------|------|-------------|----------------|
| **dataHora** | datetime | Date/time of status change | ✅ Timeline tracking |
| **idSituacao** | integer | Situation code | ✅ Status correlation |
| **situacao** | string | Situation name (e.g., "Exercício", "Licenciado") | ✅ Current status |
| **descricao** | string | Detailed description of change | ✅ Context understanding |
| **siglaPartido** | string | Party at time of change | 🔥 **Party switching tracking** |
| **siglaUf** | string | State representation | |
| **idLegislatura** | integer | Legislature ID | ✅ Period tracking |
| **idEvento** | integer | Related event ID | |
| **uriEvento** | string | Link to related event | |
| **tipoEvento** | string | Event type | |
| **dataInicio** | date | Start date (for temporary status) | ✅ Duration tracking |
| **dataFim** | date | End date (for temporary status) | ✅ Duration tracking |

## Status Types (situacao)
Common status values:
- **Exercício**: Active duty
- **Licenciado**: On leave
- **Suplente em Exercício**: Substitute in exercise
- **Afastado**: Away/suspended
- **Titular**: Regular member
- **Contínuo**: Continuous service

## Data Lake Value

### 🎯 Political Analysis
1. **Party switching history**: Track party changes over time
2. **Leadership evolution**: Monitor position changes
3. **Absence patterns**: Identify strategic absences
4. **Career timeline**: Complete political trajectory

### Analysis Opportunities
- **Party loyalty analysis**: Frequency of party changes
- **Leadership tracking**: Time in leadership positions
- **Absence correlation**: Link absences to key votes
- **Career progression**: Path to leadership roles

## Implementation Notes

### Recommended Query Strategy
```python
from datetime import datetime, timedelta

# Get last year of history
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

url = f"/deputados/{deputy_id}/historico?dataInicio={start_date}&dataFim={end_date}"
```

### Crawling Strategy
```python
# Crawl by year to avoid timeouts
for year in range(2019, 2025):
    start = f"{year}-01-01"
    end = f"{year}-12-31"
    history = get_historico(deputy_id, start, end)
    process_party_changes(history)
```

### Data Volume
- Varies greatly by deputy
- New deputies: Few records
- Veterans: Hundreds of status changes
- Arthur Lira: Extensive history across multiple legislatures

## Known Issues

### ⚠️ Timeout Issues
- **Problem**: 504 Gateway Timeout without date parameters
- **Solution**: ALWAYS use dataInicio and dataFim
- **Recommended range**: Maximum 1 year at a time

### Performance Tips
- Query smaller date ranges for better performance
- Use pagination for large result sets
- Cache results as historical data doesn't change

## Priority: **HIGH** ⭐
Essential for tracking political career evolution and party loyalty analysis.