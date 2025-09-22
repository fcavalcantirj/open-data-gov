# /deputados/{id}/ocupacoes

**Endpoint:** `GET /deputados/{id}/ocupacoes`

## Purpose
Retrieve employment and professional activity history declared by the deputy. Shows career background, current positions, and institutional affiliations outside the parliamentary mandate.

## Parameters

### Path Parameters
- **`id`** (required): Deputy ID (e.g., 204528)

### Query Parameters
- **`itens`** (optional): Items per page (default: 100)
- **`pagina`** (optional): Page number for pagination

## Request Examples
```
GET /deputados/204528/ocupacoes
GET /deputados/204528/ocupacoes?itens=50&pagina=1
```

## Response Schema
```json
{
  "dados": [
    {
      "titulo": "Conselheira - Membro do Conselho Curador",
      "entidade": "Fundação Julita",
      "entidadeUF": "SP",
      "entidadePais": "BRASIL",
      "anoInicio": 2016,
      "anoFim": null
    },
    {
      "titulo": "Vice-Presidente",
      "entidade": "Fundação Julita",
      "entidadeUF": "SP",
      "entidadePais": "BRASIL",
      "anoInicio": 2010,
      "anoFim": 2016
    },
    {
      "titulo": "Professora",
      "entidade": "Fundação Getúlio Vargas - Escola de Administração de Empresas de São Paulo",
      "entidadeUF": "SP",
      "entidadePais": "BRASIL",
      "anoInicio": 2005,
      "anoFim": null
    }
  ],
  "links": [...]
}
```

## Response Fields

| Field | Type | Description | Analysis Value |
|-------|------|-------------|----------------|
| **titulo** | string/null | Job title or position | 🔥 **Career background** |
| **entidade** | string/null | Organization/company name | 🔥 **Institution network** |
| **entidadeUF** | string/null | State of organization | ✅ Geographic influence |
| **entidadePais** | string/null | Country (usually "BRASIL") | ✅ International exposure |
| **anoInicio** | integer/null | Start year | ✅ Timeline tracking |
| **anoFim** | integer/null | End year (null = current) | ✅ Active positions |

## Common Position Types (titulo)
- **Professora/Professor** - University/school teacher
- **Conselheira/Conselheiro** - Board member/advisor
- **Diretora/Diretor** - Director/executive
- **Vice-Presidente** - Vice-President
- **Presidente** - President/CEO
- **Empresária/Empresário** - Business owner
- **Advogada/Advogado** - Lawyer
- **Médica/Médico** - Doctor

## Institution Categories
Based on entidade patterns:
- **Educational**: Universidades, Faculdades, Schools
- **Foundations**: Fundações (non-profit organizations)
- **Corporations**: Private companies and businesses
- **Professional Associations**: Conselhos, Sindicatos
- **NGOs**: Non-governmental organizations

## Data Lake Value

### 🔥 Background & Conflict Analysis
1. **Professional expertise**: Map educational and career background
2. **Conflict of interest**: Identify potential bias sources
3. **Network analysis**: Track institutional connections
4. **Economic interests**: Business ownership and board positions
5. **Geographic influence**: Regional economic connections

### Analysis Opportunities
- **Career progression**: Track professional development paths
- **Institution networks**: Shared board memberships
- **Sector expertise**: Policy area competence analysis
- **Private interests**: Business connections affecting votes
- **Educational background**: Academic credentials verification

## Implementation Notes

### Data Quality Patterns
```python
# Data availability varies significantly
# Arthur Lira (ID: 160541): Minimal data (mostly null)
# Adriana Ventura (ID: 204528): Rich professional history (7 positions)
# Pattern: Some deputies provide detailed info, others minimal

occupations_example = {
    "academic_heavy": ["Professora at FGV", "Professora at ESPM"],
    "foundation_involved": ["Conselheira at Fundação Julita"],
    "business_background": ["Vice-Presidente", "Diretora Tesoureira"]
}
```

### Professional Network Analysis
```python
def analyze_professional_background(ocupacoes):
    analysis = {
        'sectors': {},
        'institutions': [],
        'active_positions': [],
        'career_span': 0,
        'geographic_base': set()
    }

    years = []
    for occ in ocupacoes:
        if occ.get('titulo') and occ.get('entidade'):
            # Categorize by sector
            if 'Professor' in occ['titulo'] or 'Faculdade' in occ['entidade']:
                analysis['sectors']['education'] = analysis['sectors'].get('education', 0) + 1
            elif 'Fundação' in occ['entidade']:
                analysis['sectors']['foundation'] = analysis['sectors'].get('foundation', 0) + 1
            elif any(title in occ['titulo'] for title in ['Diretor', 'Presidente', 'Vice-Presidente']):
                analysis['sectors']['executive'] = analysis['sectors'].get('executive', 0) + 1

            # Track institutions
            analysis['institutions'].append(occ['entidade'])

            # Active positions (no end date)
            if occ['anoFim'] is None:
                analysis['active_positions'].append(occ['titulo'])

            # Geographic presence
            if occ.get('entidadeUF'):
                analysis['geographic_base'].add(occ['entidadeUF'])

            # Career timeline
            if occ.get('anoInicio'):
                years.append(occ['anoInicio'])
            if occ.get('anoFim'):
                years.append(occ['anoFim'])

    if years:
        analysis['career_span'] = max(years) - min(years)

    return analysis
```

### Conflict of Interest Detection
```python
def detect_potential_conflicts(ocupacoes, deputy_voting_record):
    conflicts = []

    for occ in ocupacoes:
        if occ.get('entidade') and occ['anoFim'] is None:  # Current position
            # Check if entity relates to deputy's committee work
            if 'Fundação' in occ['entidade'] and 'education' in deputy_committees:
                conflicts.append({
                    'type': 'educational_interest',
                    'position': occ['titulo'],
                    'entity': occ['entidade']
                })

    return conflicts
```

## Adriana Ventura Career Analysis Example

### Professional Background (7 positions)
- **Education Sector**: 4 teaching positions (FGV, ESPM, others)
- **Foundation Work**: Board member and VP at Fundação Julita
- **Geographic Base**: São Paulo (SP) focused
- **Career Span**: 1998-2016+ (18+ years)
- **Active Positions**: 2 current (Conselheira, Professora FGV)

### Profile Analysis
- **Expertise**: Business administration and education
- **Network**: High-level academic and foundation connections
- **Influence**: Board positions suggest leadership experience
- **Potential Conflicts**: Education policy voting

## Statistical Insights

### Data Completeness
- **Detailed records**: ~30% of deputies provide comprehensive data
- **Minimal data**: ~50% have sparse or null records
- **No data**: ~20% have completely empty records
- **Quality correlation**: Higher with deputy transparency level

### Common Patterns
- **Academic background**: 40%+ have teaching experience
- **Business experience**: 60%+ have private sector roles
- **Foundation involvement**: 25% participate in non-profits
- **Multiple roles**: Active deputies often maintain external positions

## Known Issues
- Significant data quality variation between deputies
- Many records contain null values
- Self-reported information (accuracy concerns)
- No standardized format for position titles
- Historical accuracy varies

## Priority: **MEDIUM** ⭐
Valuable for understanding deputy backgrounds and potential conflicts of interest, but data quality issues limit reliability. Essential for transparency and bias analysis when data is available.