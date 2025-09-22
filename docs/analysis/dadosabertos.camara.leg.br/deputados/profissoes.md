# /deputados/{id}/profissoes

**Endpoint:** `GET /deputados/{id}/profissoes`

## Purpose
List declared professions of a deputy. Shows professional categories officially registered during their parliamentary registration, providing insight into their background and potential expertise areas.

## Parameters

### Path Parameters
- **`id`** (required): Deputy ID (e.g., 160541)

### Query Parameters
- **`itens`** (optional): Items per page (default: 100)
- **`pagina`** (optional): Page number for pagination

## Request Examples
```
GET /deputados/160541/profissoes
GET /deputados/204528/profissoes
GET /deputados/160541/profissoes?itens=50&pagina=1
```

## Response Schema
```json
{
  "dados": [
    {
      "dataHora": "2018-08-14T16:36",
      "codTipoProfissao": 182,
      "titulo": "Empresário"
    },
    {
      "dataHora": "2018-08-14T16:36",
      "codTipoProfissao": 18,
      "titulo": "Agropecuarista"
    }
  ],
  "links": [...]
}
```

## Response Fields

| Field | Type | Description | Analysis Value |
|-------|------|-------------|----------------|
| **dataHora** | datetime | Registration date/time | ✅ Timeline tracking |
| **codTipoProfissao** | integer | Profession type code | ✅ Classification system |
| **titulo** | string | Profession name | 🔥 **Professional background** |

## Arthur Lira's Declared Professions

### 👔 Empresário (Business Owner)
- **Code**: 182
- **Registered**: August 14, 2018
- **Significance**: Business interests and private sector background

### 🌾 Agropecuarista (Agriculture/Livestock)
- **Code**: 18
- **Registered**: August 14, 2018
- **Significance**: Agricultural sector connections (important for Brazil)

## Common Profession Categories

### Business & Finance
- **Empresário** (182) - Business owner/entrepreneur
- **Administradora** (1) - Administrator
- **Economista** - Economist
- **Contador** - Accountant

### Legal & Public Service
- **Advogado** - Lawyer
- **Delegado** - Police delegate
- **Promotor** - Prosecutor
- **Servidor Público** - Public servant

### Healthcare & Education
- **Médico** - Doctor
- **Professor** - Teacher
- **Enfermeiro** - Nurse
- **Psicólogo** - Psychologist

### Agriculture & Industry
- **Agropecuarista** (18) - Agriculture/livestock
- **Engenheiro** - Engineer
- **Técnico** - Technician

## Data Lake Value

### 🔥 Professional Background Analysis
1. **Policy expertise**: Match professions to committee assignments
2. **Interest representation**: Identify potential sector bias
3. **Qualification assessment**: Evaluate relevant experience
4. **Network analysis**: Group deputies by professional background
5. **Conflict detection**: Business interests vs voting patterns

### Analysis Opportunities
- **Sector representation**: Map professional distribution in Chamber
- **Committee alignment**: Professional background vs committee membership
- **Regional patterns**: Geographic correlation with profession types
- **Party analysis**: Professional composition by political party
- **Voting correlation**: How profession affects policy positions

## Implementation Notes

### Professional Classification System
```python
def categorize_professions(profissoes):
    categories = {
        'business': ['Empresário', 'Administrador', 'Economista'],
        'legal': ['Advogado', 'Delegado', 'Promotor'],
        'healthcare': ['Médico', 'Enfermeiro', 'Psicólogo'],
        'education': ['Professor', 'Pedagogo'],
        'agriculture': ['Agropecuarista', 'Veterinário'],
        'technical': ['Engenheiro', 'Técnico'],
        'public_service': ['Servidor Público', 'Militar']
    }

    deputy_categories = []
    for prof in profissoes:
        title = prof['titulo']
        for category, professions in categories.items():
            if any(p in title for p in professions):
                deputy_categories.append(category)

    return list(set(deputy_categories))  # Remove duplicates
```

### Profession-Committee Correlation
```python
def analyze_profession_committee_match(professions, committees):
    matches = []

    profession_titles = [p['titulo'] for p in professions]

    # Check for relevant matches
    if 'Agropecuarista' in profession_titles:
        agriculture_committees = [c for c in committees if 'agric' in c['nomeOrgao'].lower()]
        if agriculture_committees:
            matches.append('agriculture_aligned')

    if 'Médico' in profession_titles:
        health_committees = [c for c in committees if 'saúde' in c['nomeOrgao'].lower()]
        if health_committees:
            matches.append('healthcare_aligned')

    return matches
```

### Professional Network Analysis
```python
def build_professional_networks(all_deputy_professions):
    networks = {}

    for deputy_id, professions in all_deputy_professions.items():
        for prof in professions:
            profession_code = prof['codTipoProfissao']
            if profession_code not in networks:
                networks[profession_code] = {
                    'title': prof['titulo'],
                    'deputies': []
                }
            networks[profession_code]['deputies'].append(deputy_id)

    return networks
```

## Statistical Insights

### Professional Distribution in Chamber
Based on patterns observed:
- **Business backgrounds**: 30-40% (Empresário, Administrador)
- **Legal professionals**: 25-35% (Advogado, Delegado)
- **Public service**: 20-30% (Servidor Público, Militar)
- **Healthcare**: 10-15% (Médico, Enfermeiro)
- **Education**: 10-15% (Professor, Pedagogo)
- **Agriculture**: 8-12% (Agropecuarista, Veterinário)

### Multiple Professions
- **Arthur Lira**: 2 professions (Business + Agriculture)
- **Adriana Ventura**: 1 profession (Administration)
- **Average**: 1-3 declared professions per deputy
- **Pattern**: Multiple professions indicate diverse experience

## Registration Patterns
- Most professions registered during initial mandate setup
- Same timestamp often indicates batch registration
- Historical data available from 2018+ elections

## Known Issues
- Self-declared information (accuracy varies)
- Not all deputies declare multiple professions
- Some professional categories may be outdated
- Code system not fully documented
- Limited historical profession tracking

## Priority: **MEDIUM** ⭐
Useful for understanding deputy backgrounds and potential policy expertise, but limited by self-reporting accuracy. Important for committee assignment analysis and conflict of interest detection.