# Brazilian Political Network: Data Architecture & Correlation Strategy

## The Big Picture: Data Universe Mapping

### Core Entities and Their Natural Homes

```
PERSON (The Universal Connector)
├── CPF (11 digits) - Universal Brazilian ID
├── Found in: Câmara, Senado, TSE, TCU, DataJud, Receita Federal
├── Problem: Not always exposed (privacy), name variations
└── Solution: Fuzzy matching + electoral number + party/state combo

COMPANY (The Money Trail)
├── CNPJ (14 digits) - Universal Business ID  
├── Found in: Portal Transparência, TCU, CEAP expenses, Receita Federal
├── Key: Links political expenses to government contracts
└── Hidden gem: QSA (ownership) reveals politician-business ties

MONEY FLOW (The Influence Network)
├── Campaign donations (TSE)
├── Parliamentary expenses (CEAP - Câmara/Senado)
├── Government contracts (Portal Transparência)
├── Amendments (SIOP)
└── All connect via: CPF ↔ CNPJ relationships

LEGISLATIVE BEHAVIOR (The Alliance Patterns)
├── Votes (Câmara/Senado)
├── Propositions (authorship/co-sponsorship)
├── Committee membership
├── Parliamentary fronts
└── Temporal dimension: Everything has timestamps
```

## Data Lake Architecture: What Lives Where

### Layer 1: Raw Data Lake (S3/MinIO)
```
/bronze/  (Raw, immutable, partitioned by date)
├── camara/
│   ├── votes/year=2023/month=11/day=15/
│   ├── expenses/year=2023/month=11/
│   ├── deputies/snapshot=2023-11-15/
│   └── propositions/year=2023/
├── senado/
│   └── [similar structure]
├── tse/
│   ├── candidates/election=2022/
│   ├── donations/election=2022/
│   └── results/election=2022/
├── transparency/
│   ├── contracts/year=2023/month=11/
│   └── sanctions/snapshot=2023-11-15/
└── judicial/
    └── processes/year=2023/tribunal=STF/
```

### Layer 2: Graph Database (Neo4j) - Relationships & Networks
```
What goes in:
- ENTITIES: Politicians, Companies, Donors, Committees
- RELATIONSHIPS: Voted_With, Donated_To, Contracted_By, Investigated_With
- WHY: Graph algorithms (PageRank, Community Detection, Shortest Path)

What stays out:
- Raw text (proposition content)
- Time series data (individual expenses)
- Large documents (PDFs, judicial files)
```

### Layer 3: SQL/TimeSeries (PostgreSQL/TimescaleDB) - Facts & Metrics
```
What goes in:
- Time series: votes, expenses, donations over time
- Aggregations: monthly spending, voting statistics
- Full-text search: proposition texts, speech transcripts
- Audit trails: data lineage, change tracking

What stays out:
- Relationship traversals
- Network algorithms
- Graph patterns
```

## Data Correlation Strategy

### Primary Keys & Join Strategy
```
POLITICIAN MATCHING:
1. Try CPF (if available)
2. Fallback: Name + Party + State + Legislature
3. Electoral number (TSE) ↔ Parliamentary ID
4. Fuzzy match: Normalize names (remove accents, titles)

COMPANY MATCHING:
1. CNPJ (always 14 digits)
2. Fallback: Exact name + state
3. Check: Related CNPJs (same address/owners)

TEMPORAL CORRELATION:
- Everything tied to Legislature (4-year periods)
- Sessions → Votes → Time-bounded relationships
- Electoral cycles affect donation patterns
```

## Data Flow Architecture

### Real-Time Streams (Event-Driven)
```
Kafka Topics:
├── votes.live (during sessions)
├── expenses.new (daily)
├── propositions.new (hourly)
└── news.mentions (external APIs)

Processing:
- Spark Streaming for windowed aggregations
- Flink for complex event processing
- Direct Neo4j updates for relationship changes
```

### Batch Processing (Scheduled)
```
HOURLY:
- Check new propositions
- Update committee memberships
- Process speech transcripts

DAILY (2 AM BRT):
- Full deputy roster sync
- Expense report updates  
- Judicial process checks
- Calculate daily influence metrics

WEEKLY:
- Community detection algorithms
- Network density calculations
- Temporal pattern analysis

MONTHLY:
- Historical data reconciliation
- QSA/ownership updates
- Complete graph rebuild
```

## The Discovery Phase: Test Scripts

### Script 1: Entity Discovery & Correlation
```python
# Pseudo-code for initial exploration

def discover_deputy_universe(cpf_or_name):
    """
    Map a single deputy across all systems
    """
    
    # Start with Câmara
    camara_data = fetch_camara_deputy(cpf_or_name)
    deputy_id = camara_data['id']
    
    # Build identity map
    identity = {
        'camara_id': deputy_id,
        'cpf': clean_cpf(camara_data.get('cpf')),
        'name_variations': [camara_data['nome']]
    }
    
    # Fetch related data
    expenses = fetch_deputy_expenses(deputy_id, last_n_months=12)
    votes = fetch_deputy_votes(deputy_id, last_n=1000)
    propositions = fetch_deputy_propositions(deputy_id)
    
    # Extract unique CNPJs from expenses
    vendor_cnpjs = extract_cnpjs(expenses)
    
    # Cross-reference with Portal Transparência
    for cnpj in vendor_cnpjs:
        contracts = fetch_government_contracts(cnpj)
        sanctions = check_sanctions(cnpj)
        ownership = fetch_qsa(cnpj)  # Receita Federal
        
    # TSE correlation
    tse_data = search_tse_candidate(
        name=normalize_name(identity['name']), 
        year=2022
    )
    if tse_data:
        identity['electoral_number'] = tse_data['numero']
        donations = fetch_donations(tse_data['id'])
    
    # Judicial correlation
    processes = search_datajud(identity['name_variations'])
    
    return {
        'identity': identity,
        'financial_network': vendor_cnpjs,
        'legislative_activity': len(propositions),
        'judicial_exposure': len(processes),
        'donation_network': donations
    }
```

### Script 2: Relationship Discovery
```python
def discover_hidden_relationships(deputy_ids: list):
    """
    Find non-obvious connections between deputies
    """
    
    relationships = []
    
    for i, deputy_a in enumerate(deputy_ids):
        for deputy_b in deputy_ids[i+1:]:
            
            # Shared vendors in expenses
            vendors_a = get_expense_vendors(deputy_a)
            vendors_b = get_expense_vendors(deputy_b)
            shared_vendors = vendors_a.intersection(vendors_b)
            
            if shared_vendors:
                relationships.append({
                    'type': 'SHARED_VENDOR',
                    'deputies': [deputy_a, deputy_b],
                    'vendors': list(shared_vendors),
                    'weight': len(shared_vendors)
                })
            
            # Co-authorship beyond party lines
            if different_parties(deputy_a, deputy_b):
                joint_props = find_co_authored_propositions(deputy_a, deputy_b)
                if joint_props:
                    relationships.append({
                        'type': 'CROSS_PARTY_COLLABORATION',
                        'deputies': [deputy_a, deputy_b],
                        'propositions': joint_props
                    })
            
            # Coordinated voting against party orientation
            rebel_votes = find_coordinated_rebellion(deputy_a, deputy_b)
            if rebel_votes:
                relationships.append({
                    'type': 'COORDINATED_REBELLION',
                    'deputies': [deputy_a, deputy_b],
                    'votes': rebel_votes
                })
    
    return relationships
```

### Script 3: Temporal Pattern Detection
```python
def analyze_temporal_patterns(entity_id, entity_type='deputy'):
    """
    Detect behavioral changes over time
    """
    
    if entity_type == 'deputy':
        # Voting pattern shifts
        voting_history = fetch_votes_timeline(entity_id)
        windows = sliding_window(voting_history, window_size='3_months')
        
        pattern_shifts = []
        for i, window in enumerate(windows[:-1]):
            current_pattern = calculate_voting_pattern(window)
            next_pattern = calculate_voting_pattern(windows[i+1])
            
            divergence = pattern_divergence(current_pattern, next_pattern)
            if divergence > THRESHOLD:
                # Something changed - investigate
                pattern_shifts.append({
                    'period': window['period'],
                    'divergence': divergence,
                    'trigger': find_potential_trigger(window['end_date'])
                })
        
        # Expense pattern changes
        expense_timeline = fetch_expenses_timeline(entity_id)
        anomalies = detect_expense_anomalies(expense_timeline)
        
        # Network position evolution
        monthly_networks = []
        for month in last_12_months():
            network = build_voting_network(month)
            position = calculate_network_position(entity_id, network)
            monthly_networks.append(position)
        
        return {
            'voting_shifts': pattern_shifts,
            'expense_anomalies': anomalies,
            'influence_trajectory': monthly_networks
        }
```

## Critical Data Decisions

### What Makes It to Graph DB vs SQL vs Lake

```
GRAPH DB (Neo4j) - "Who knows whom, who influences whom"
├── Current state only (latest legislature)
├── Entities: ~5K deputies + ~10K companies + ~50K donors
├── Relationships: ~500K edges (votes, donations, contracts)
├── Updated: Daily with new relationships
└── Queries: Shortest path, community detection, influence spread

SQL (PostgreSQL) - "What happened when, how much, how often"
├── Full history (2001-present)
├── Facts: 50M+ votes, 10M+ expenses, 300K+ propositions
├── Time-series: Partitioned by month
├── Updated: Hourly for current data
└── Queries: Aggregations, trends, full-text search

DATA LAKE (S3/MinIO) - "Everything, forever, raw"
├── Complete dumps from all sources
├── PDF documents, judicial files
├── Historical snapshots
├── Never deleted, only appended
└── Purpose: Reprocessing, audit, machine learning
```

### The Unknown Unknowns: What We'll Discover

1. **Shadow Networks**: Companies that don't directly contract but consistently appear in expense reports
2. **Temporal Coalitions**: Groups that vote together only on specific topics
3. **Influence Laundering**: Multi-hop influence paths through committees
4. **Regional Mafias**: State-level coordination patterns invisible at federal level
5. **Pre-Vote Negotiations**: Expense/travel patterns predicting vote outcomes

## Implementation Roadmap

### Week 1-2: Discovery Phase
```
1. Set up Jupyter environment with Brazilian data tools
2. Fetch sample data from 3-4 sources
3. Test entity correlation algorithms
4. Document data quality issues
5. Build data profile report
```

### Week 3-4: Prototype Data Pipeline
```
1. Design normalized entity model
2. Build extraction scripts for top 5 sources
3. Test correlation accuracy (sample of 100 deputies)
4. Prototype graph database population
5. Create basic visualization of sample network
```

### Week 5-6: Architecture Validation
```
1. Load test with full dataset
2. Benchmark graph algorithms performance  
3. Test real-time update mechanisms
4. Validate storage estimates
5. Design monitoring approach
```

## Key Technical Decisions

### Why Hybrid Approach (Graph + SQL + Lake)
- Graph: Relationship traversals are 1000x faster than SQL joins
- SQL: Time-series queries need columnar optimization
- Lake: Regulatory compliance requires immutable audit trail

### Why Event Streaming (Kafka)
- Legislative sessions require real-time updates
- Pattern detection needs windowed processing
- Multiple consumers (web, analytics, alerts)

### Why PostgreSQL over ClickHouse
- Need ACID transactions for financial data
- Brazilian document validation requires custom functions
- PostGIS for geographic analysis of voting patterns

## The First Script to Run

```python
"""
Start here: Fetch one deputy, trace them everywhere
This validates our correlation strategy
"""

import requests
from datetime import datetime, timedelta

# Pick a well-known deputy with likely rich data
SAMPLE_DEPUTY = "Deputado Arthur Lira"  # Current Chamber President

def validate_data_universe():
    # 1. Câmara - Get base identity
    print("=== CÂMARA DOS DEPUTADOS ===")
    camara_response = requests.get(
        "https://dadosabertos.camara.leg.br/api/v2/deputados",
        params={"nome": SAMPLE_DEPUTY}
    )
    
    # 2. Get their expenses - find CNPJs
    print("\n=== EXPENSES (CEAP) ===")
    # Get expenses, extract unique vendors
    
    # 3. TSE - Find electoral data
    print("\n=== TSE ELECTORAL DATA ===")
    # Match by name + state + party
    
    # 4. Portal Transparência - Check vendor contracts
    print("\n=== GOVERNMENT CONTRACTS ===")
    # Use CNPJs from expenses
    
    # 5. DataJud - Any judicial processes?
    print("\n=== JUDICIAL PROCESSES ===")
    # Search by name variations
    
    # 6. Graph potential - who votes like them?
    print("\n=== VOTING SIMILARITY ===")
    # Get recent votes, find patterns
    
    return "Full entity map"

# Run this first to understand data quality and correlation challenges
```

## Next Steps for Claude Code

1. **Create test environment** with sample data from each source
2. **Build correlation notebook** testing entity matching accuracy  
3. **Prototype the graph model** with 100 deputies
4. **Benchmark algorithms** on increasing data sizes
5. **Design the stream processing** for live sessions

This is our architectural blueprint - a living document that will evolve as we discover the data's hidden patterns.