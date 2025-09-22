# /deputados/{id}/discursos

**Endpoint:** `GET /deputados/{id}/discursos`

## Purpose
Retrieve all speeches made by a specific deputy in the plenary sessions. Contains complete speech transcriptions, audio/video links when available, and metadata about the speaking context.

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
GET /deputados/204560/discursos?itens=10
GET /deputados/204560/discursos?dataInicio=2024-01-01&dataFim=2024-12-31
GET /deputados/204560/discursos?itens=50&pagina=1
```

## Response Schema
```json
{
  "dados": [
    {
      "dataHoraInicio": "2025-09-17T21:52",
      "dataHoraFim": null,
      "uriEvento": "",
      "faseEvento": {
        "titulo": "Ordem do Dia",
        "dataHoraInicio": null,
        "dataHoraFim": null
      },
      "tipoDiscurso": "PELA ORDEM",
      "urlTexto": null,
      "urlAudio": null,
      "urlVideo": null,
      "keywords": null,
      "sumario": null,
      "transcricao": "O SR. ADOLFO VIANA (Bloco/PSDB - BA. Pela ordem. Sem revisão do orador.) - Sr. Presidente, a Federação..."
    }
  ],
  "links": [...]
}
```

## Response Fields

| Field | Type | Description | Analysis Value |
|-------|------|-------------|----------------|
| **dataHoraInicio** | datetime | Speech start time | ✅ Timeline tracking |
| **dataHoraFim** | datetime/null | Speech end time | ✅ Duration analysis |
| **uriEvento** | string | Related event URI | ✅ Context linking |
| **faseEvento** | object | Session phase info | ✅ Parliamentary context |
| **tipoDiscurso** | string | Speech type | 🔥 **Speech classification** |
| **urlTexto** | string/null | Full text document URL | ✅ Complete transcript |
| **urlAudio** | string/null | Audio recording URL | ✅ Verification |
| **urlVideo** | string/null | Video recording URL | ✅ Visual analysis |
| **keywords** | string/null | Speech keywords | ✅ Topic analysis |
| **sumario** | string/null | Speech summary | ✅ Quick overview |
| **transcricao** | string | Complete speech transcription | 🔥 **Full text analysis** |

## Speech Types (tipoDiscurso)
Common speech types include:
- **PELA ORDEM** - Procedural speech
- **COMUNICAÇÃO** - Communication/announcement
- **DISCURSO** - Formal speech
- **APARTE** - Interruption/interjection
- **QUESTÃO DE ORDEM** - Point of order
- **LIDERANÇA** - Leadership speech

## Session Phases (faseEvento.titulo)
- **Ordem do Dia** - Main session agenda
- **Pequeno Expediente** - Brief announcements
- **Grande Expediente** - Extended speeches
- **Comunicações Parlamentares** - Parliamentary communications

## Data Lake Value

### 🔥 Political Analysis Gold Mine
1. **Content analysis**: Extract policy positions and rhetoric
2. **Speaking patterns**: Frequency and timing analysis
3. **Topic modeling**: Identify key issues and themes
4. **Sentiment analysis**: Political stance evolution
5. **Network analysis**: Cross-references and mentions

### Analysis Opportunities
- **Rhetoric evolution**: Track position changes over time
- **Activity levels**: Speaking frequency as engagement metric
- **Issue focus**: Policy area emphasis analysis
- **Coalition patterns**: Who speaks on similar topics
- **Media impact**: Speech timing vs news cycles

## Implementation Notes

### Data Availability Patterns
```python
# Not all deputies have recorded speeches
# Arthur Lira (ID: 160541): 0 speeches
# Adolfo Viana (ID: 204560): Multiple speeches
# Pattern: Leadership roles may limit floor speeches
```

### Text Processing Strategy
```python
def analyze_speech_content(discursos):
    analysis = {
        'total_speeches': len(discursos),
        'speech_types': {},
        'topics': [],
        'sentiment_timeline': []
    }

    for speech in discursos:
        # Count speech types
        speech_type = speech['tipoDiscurso']
        analysis['speech_types'][speech_type] = analysis['speech_types'].get(speech_type, 0) + 1

        # Extract content for NLP
        if speech['transcricao']:
            analysis['topics'].extend(extract_topics(speech['transcricao']))

    return analysis
```

### Crawling Strategy
```python
# Get speeches for active period
for deputy_id in active_deputies:
    speeches = get_speeches(deputy_id, year=2024)
    if speeches:
        process_speech_content(speeches)
        analyze_speaking_patterns(speeches)
```

## Statistical Insights

### Distribution Patterns
- **Leadership positions**: Often fewer floor speeches (committee work)
- **New deputies**: Higher speech frequency (establishing presence)
- **Opposition**: More procedural speeches ("PELA ORDEM")
- **Government**: More formal speeches ("DISCURSO")

### Data Volumes
- **Active speakers**: 50-200 speeches per year
- **Leadership**: 0-20 speeches per year
- **New deputies**: 20-100 speeches per year
- **Varies greatly** by deputy role and style

## Known Issues
- Some deputies have no recorded speeches
- Not all speeches have audio/video links
- Transcription quality varies
- Leadership positions correlate with fewer speeches

## Priority: **MEDIUM** ⭐
Valuable for political analysis and rhetoric tracking, but not critical for corruption detection. Essential for understanding deputy engagement and policy positions.