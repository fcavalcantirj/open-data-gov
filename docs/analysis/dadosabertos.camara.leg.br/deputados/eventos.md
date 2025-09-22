# /deputados/{id}/eventos

**Endpoint:** `GET /deputados/{id}/eventos`

## Purpose
Retrieve all events and sessions where a deputy participated. Includes committee meetings, plenary sessions, public hearings, and other parliamentary activities with detailed timing and location information.

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
GET /deputados/160541/eventos?itens=10
GET /deputados/160541/eventos?dataInicio=2024-01-01&dataFim=2024-12-31
GET /deputados/160541/eventos?itens=50&pagina=1
```

## Response Schema
```json
{
  "dados": [
    {
      "id": 79236,
      "uri": "https://dadosabertos.camara.leg.br/api/v2/eventos/79236",
      "dataHoraInicio": "2025-09-16T13:55",
      "dataHoraFim": "2025-09-17T00:19",
      "situacao": "Encerrada",
      "descricaoTipo": "Sessão Deliberativa",
      "descricao": "Sessão Deliberativa Extraordinária Presencial (AM nº 123/2020)",
      "localExterno": null,
      "orgaos": [
        {
          "id": 180,
          "uri": "https://dadosabertos.camara.leg.br/api/v2/orgaos/180",
          "sigla": "PLEN",
          "nome": "Plenário",
          "apelido": "Plenário",
          "codTipoOrgao": 26,
          "tipoOrgao": "Plenário Virtual",
          "nomePublicacao": "Plenário",
          "nomeResumido": "Plenário"
        }
      ],
      "localCamara": {
        "nome": "Plenário da Câmara dos Deputados",
        "predio": null,
        "sala": null,
        "andar": null
      },
      "urlRegistro": "https://www.youtube.com/watch?v=wpF09bdO_68"
    }
  ],
  "links": [...]
}
```

## Response Fields

| Field | Type | Description | Analysis Value |
|-------|------|-------------|----------------|
| **id** | integer | Event unique ID | ✅ Cross-reference key |
| **uri** | string | Event details API endpoint | ✅ Deep event data |
| **dataHoraInicio** | datetime | Event start time | ✅ Timeline tracking |
| **dataHoraFim** | datetime | Event end time | ✅ Duration analysis |
| **situacao** | string | Event status | ✅ Completion tracking |
| **descricaoTipo** | string | Event type description | 🔥 **Activity classification** |
| **descricao** | string | Detailed event description | ✅ Context understanding |
| **localExterno** | string/null | External location | ✅ Location tracking |
| **orgaos** | array | Organizing bodies/committees | 🔥 **Committee involvement** |
| **localCamara** | object | Chamber location details | ✅ Internal location |
| **urlRegistro** | string | Video/audio recording URL | ✅ Verification |

## Event Types (descricaoTipo)
Common event types include:
- **Sessão Deliberativa** - Deliberative session (voting)
- **Sessão Ordinária** - Regular session
- **Reunião Deliberativa** - Committee deliberative meeting
- **Audiência Pública** - Public hearing
- **Reunião de Instalação** - Installation meeting
- **Sessão Solene** - Ceremonial session
- **Reunião Temática** - Thematic meeting

## Event Status (situacao)
- **Encerrada** - Concluded
- **Em Andamento** - In progress
- **Prevista** - Scheduled
- **Cancelada** - Cancelled
- **Adiada** - Postponed

## Data Lake Value

### 🔥 Parliamentary Activity Analysis
1. **Participation tracking**: Attendance and engagement metrics
2. **Committee influence**: Map committee involvement patterns
3. **Activity intensity**: Meeting frequency and duration analysis
4. **Cross-committee networks**: Identify overlapping memberships
5. **Leadership activities**: Presidential duties and special sessions

### Analysis Opportunities
- **Attendance patterns**: Participation frequency by event type
- **Committee centrality**: Most active committees and networks
- **Time analysis**: Working hours and session duration trends
- **Location analysis**: Chamber vs external event participation
- **Video evidence**: Direct access to recorded proceedings

## Implementation Notes

### Arthur Lira Activity Patterns
```python
# As Chamber President, extensive event participation
# Example from test: 10+ hour session (13:55 to 00:19 next day)
# High frequency of plenary sessions
# YouTube recordings available for verification
```

### Activity Scoring Algorithm
```python
def calculate_parliamentary_activity(eventos):
    activity_score = 0
    meeting_types = {}
    total_hours = 0

    for event in eventos:
        # Calculate event duration
        start = datetime.fromisoformat(event['dataHoraInicio'])
        if event['dataHoraFim']:
            end = datetime.fromisoformat(event['dataHoraFim'])
            hours = (end - start).total_seconds() / 3600
            total_hours += hours

        # Weight by event type
        event_type = event['descricaoTipo']
        if 'Deliberativa' in event_type:
            activity_score += 5  # High weight for voting sessions
        elif 'Audiência' in event_type:
            activity_score += 3  # Medium weight for hearings
        else:
            activity_score += 1  # Base weight

        meeting_types[event_type] = meeting_types.get(event_type, 0) + 1

    return {
        'activity_score': activity_score,
        'total_hours': total_hours,
        'meeting_distribution': meeting_types,
        'avg_hours_per_month': total_hours / 12
    }
```

### Committee Network Analysis
```python
def build_committee_network(deputy_events):
    committees = {}
    for event in deputy_events:
        for orgao in event['orgaos']:
            committee_id = orgao['id']
            committee_name = orgao['nome']
            committees[committee_id] = {
                'name': committee_name,
                'participation_count': committees.get(committee_id, {}).get('participation_count', 0) + 1
            }
    return committees
```

## Statistical Insights

### Participation Patterns
- **Leadership positions**: High plenary session participation
- **Committee chairs**: Frequent committee meetings
- **New deputies**: Mixed participation while learning
- **Opposition**: May skip government-led sessions

### Data Volumes by Role
- **Chamber President**: 500+ events per year
- **Committee chairs**: 200-400 events per year
- **Regular deputies**: 100-300 events per year
- **Inactive deputies**: <50 events per year

## Known Issues
- Not all events have end times
- Some external locations not specified
- Video URLs may expire over time
- Historical events may lack recording links

## Priority: **HIGH** ⭐
Essential for understanding deputy engagement and parliamentary participation patterns. Critical for activity-based influence scoring and committee network analysis.