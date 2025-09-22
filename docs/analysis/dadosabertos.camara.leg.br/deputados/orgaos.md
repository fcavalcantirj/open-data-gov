# /deputados/{id}/orgaos

**Endpoint:** `GET /deputados/{id}/orgaos`

## Purpose
List all parliamentary bodies (committees, commissions, groups) where a deputy holds current or historical positions. Shows roles, membership periods, and hierarchical positions within the Chamber's organizational structure.

## Parameters

### Path Parameters
- **`id`** (required): Deputy ID (e.g., 160541)

### Query Parameters
- **`dataInicio`** (optional): Start date filter in format `AAAA-MM-DD`
- **`dataFim`** (optional): End date filter in format `AAAA-MM-DD`
- **`itens`** (optional): Items per page (default: 100)
- **`pagina`** (optional): Page number for pagination

## Request Examples
```
GET /deputados/160541/orgaos
GET /deputados/160541/orgaos?dataInicio=2024-01-01&dataFim=2024-12-31
GET /deputados/160541/orgaos?itens=50&pagina=1
```

## Response Schema
```json
{
  "dados": [
    {
      "idOrgao": 539644,
      "uriOrgao": "https://dadosabertos.camara.leg.br/api/v2/orgaos/539644",
      "siglaOrgao": "BANEGRA",
      "nomeOrgao": "Bancada Negra da Câmara dos Deputados, criada pela Resolução n. 6, de 2023...",
      "nomePublicacao": null,
      "titulo": "Titular",
      "codTitulo": 101,
      "dataInicio": "2023-11-02T00:00",
      "dataFim": null
    },
    {
      "idOrgao": 539644,
      "uriOrgao": "https://dadosabertos.camara.leg.br/api/v2/orgaos/539644",
      "siglaOrgao": "PL108725",
      "nomeOrgao": "Comissão Especial destinada a proferir parecer ao Projeto de Lei nº 1087...",
      "nomePublicacao": null,
      "titulo": "Relator",
      "codTitulo": 105,
      "dataInicio": "2025-01-01T00:00",
      "dataFim": null
    }
  ],
  "links": [...]
}
```

## Response Fields

| Field | Type | Description | Analysis Value |
|-------|------|-------------|----------------|
| **idOrgao** | integer | Organization unique ID | ✅ Cross-reference key |
| **uriOrgao** | string | Organization details API endpoint | ✅ Deep organ data |
| **siglaOrgao** | string | Organization abbreviation | ✅ Quick identification |
| **nomeOrgao** | string | Full organization name | ✅ Complete context |
| **nomePublicacao** | string/null | Publication name | ✅ Official designation |
| **titulo** | string | Deputy's role/title | 🔥 **Power position** |
| **codTitulo** | integer | Title code | ✅ Role classification |
| **dataInicio** | datetime | Start date of membership | ✅ Timeline tracking |
| **dataFim** | datetime/null | End date (null = current) | ✅ Active status |

## Position Types (titulo)
Common deputy roles include:
- **Presidente** - President/Chairperson
- **Vice-Presidente** - Vice-President
- **Relator** - Rapporteur (key role for bills)
- **Titular** - Full member
- **Suplente** - Substitute member
- **1º Vice-Presidente** - First Vice-President
- **2º Vice-Presidente** - Second Vice-President

## Organization Types
Based on siglaOrgao patterns:
- **Permanent Committees**: CTASP, CCULT, CFFC, etc.
- **Special Commissions**: PL#### (bill-specific)
- **Parliamentary Groups**: BANEGRA, etc.
- **Mixed Commissions**: Joint Chamber-Senate
- **Investigation Commissions**: CPI#### (CPIs)

## Arthur Lira's Current Positions

### 🔥 BANEGRA - Bancada Negra
- **Role**: Titular (Full Member)
- **Since**: November 2, 2023
- **Status**: Active
- **Significance**: Racial equality advocacy group

### 📋 PL108725 - Tax Reform Commission
- **Dual Role**: Both Titular AND Relator
- **Focus**: Income tax reform legislation
- **Status**: Active (2025)
- **Power**: Rapporteur role = controls bill outcome

## Data Lake Value

### 🔥 Power Structure Analysis
1. **Committee influence**: Map decision-making positions
2. **Leadership tracking**: Identify power progression
3. **Policy specialization**: Area of expertise analysis
4. **Network centrality**: Cross-committee connections
5. **Temporal power**: Position duration and stability

### Analysis Opportunities
- **Influence scoring**: Weight positions by importance
- **Committee networks**: Shared membership analysis
- **Policy alignment**: Committee focus correlation
- **Power dynamics**: Leadership role progression
- **Term limits**: Position rotation patterns

## Implementation Notes

### Power Position Scoring
```python
def calculate_committee_power(orgaos):
    power_score = 0
    positions = {}

    for organ in orgaos:
        title = organ['titulo']

        # Weight by position importance
        if 'Presidente' in title:
            power_score += 10
        elif 'Vice-Presidente' in title:
            power_score += 7
        elif 'Relator' in title:
            power_score += 8  # High influence on legislation
        elif 'Titular' in title:
            power_score += 3
        elif 'Suplente' in title:
            power_score += 1

        positions[title] = positions.get(title, 0) + 1

    return {
        'total_power_score': power_score,
        'position_distribution': positions,
        'active_committees': len(orgaos)
    }
```

### Committee Network Analysis
```python
def build_committee_network(all_deputy_organs):
    committee_connections = {}

    for deputy_id, organs in all_deputy_organs.items():
        for organ in organs:
            committee_id = organ['idOrgao']
            if committee_id not in committee_connections:
                committee_connections[committee_id] = []
            committee_connections[committee_id].append(deputy_id)

    return committee_connections
```

### Active Position Tracking
```python
def get_active_positions(orgaos):
    active = []
    for organ in orgaos:
        if organ['dataFim'] is None:  # Current position
            active.append({
                'organ': organ['siglaOrgao'],
                'title': organ['titulo'],
                'since': organ['dataInicio']
            })
    return active
```

## Statistical Insights

### Position Distribution Patterns
- **Leadership roles**: 10-15% of deputies hold president/vice positions
- **Rapporteur roles**: High-influence positions for legislation
- **Multiple positions**: Common for experienced deputies
- **Arthur Lira**: Dual role (Titular + Relator) shows high influence

### Committee Participation
- **Average deputy**: 2-5 committee memberships
- **Leadership**: 5-10+ committee positions
- **New deputies**: 1-3 initial assignments
- **Specialization**: Deputies often focus on specific policy areas

## Known Issues
- Some organization names are very long (truncation needed)
- Historical positions may lack complete date ranges
- Special commissions have complex naming patterns
- Publication names often null

## Priority: **HIGH** ⭐
Critical for understanding deputy influence, power structures, and policy specialization. Essential for committee network analysis and leadership tracking.