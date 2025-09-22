# Brazilian political network visualization through open data APIs

The Brazilian government provides an unprecedented level of transparency through robust APIs and open data platforms, creating exceptional opportunities for revealing hidden patterns in political relationships through 3D network visualization. This comprehensive analysis maps the technical architecture, data relationships, and visualization strategies needed to build an interactive political network similar to the 3d-force-graph example.

## The Brazilian Chamber of Deputies API ecosystem

The Câmara dos Deputados offers a mature RESTful API at `https://dadosabertos.camara.leg.br/api/v2/` with over 40 documented endpoints covering legislative activity from 1827 to present. The API requires no authentication and provides data in JSON and XML formats without rate limiting, though responsible usage patterns are expected. **The system updates daily for most datasets, with real-time updates during active legislative sessions**, making it ideal for tracking dynamic political relationships.

The API's hierarchical data model centers on legislative terms (4-year periods) containing deputies, committees, propositions, and voting records. Each deputy has a unique ID persisting across terms, enabling temporal analysis of career trajectories and shifting alliances. The expense tracking endpoint `/deputados/{id}/despesas` provides granular CEAP (parliamentary quota) data since 2008, revealing spending patterns across 15 categories including consulting services, travel, and office maintenance. Committee memberships accessible through `/deputados/{id}/orgaos` expose power structures, while the `/frentes` endpoints map cross-party parliamentary fronts that often indicate ideological alignments beyond official party lines.

For efficient data retrieval, the API supports sophisticated filtering through query parameters including date ranges, party affiliations, states, and legislative terms. Pagination handles large result sets with configurable page sizes up to 200 items. Historical data quality varies significantly - voting records are comprehensive from the early 2000s, while propositions before 2001 have limited metadata. Bulk download files in CSV, JSON, and Excel formats complement the API for complete historical datasets, reducing the need for thousands of individual API calls.

## Financial transparency reveals hidden networks  

Brazil's political financial ecosystem exposes multiple layers of economic relationships through interconnected databases. The CEAP expense system tracks deputy spending with daily updates, recording vendor relationships, expense categories, and payment patterns that can reveal coordinated activities or suspicious clustering. **Since 2014, digital receipts provide unprecedented transparency**, enabling analysis of vendor networks shared across multiple politicians.

The TSE's DivulgaCandContas system maintains campaign finance records from 2004 onward, though corporate donations were banned by the Supreme Court, shifting focus to individual donors and indirect corporate influence through consulting contracts and event sponsorships. The Portal da Transparência API (requiring email registration) provides government contract data with 90 requests per minute rate limiting, enabling cross-reference between CEAP vendors and government contractors.

Operation Car Wash's legacy, despite the task force's 2021 disbanding, provides extensive corruption network documentation with 280+ convictions and detailed corporate-political relationship mappings across Latin America. The TCU (Federal Audit Court) maintains real-time APIs for sanctions, irregular accounts (CADIRREG), and congressional investigation requests, with endpoints like `/api-de-dados/empresas-sancionadas` identifying companies banned from government contracts.

Financial anomaly patterns particularly valuable for visualization include deputies consistently hitting quota limits, identical expense amounts across multiple politicians suggesting coordination, high-value consulting contracts with vague descriptions, and geographic clustering of expenses outside home states. The lack of formal lobbying registration in Brazil makes these indirect financial relationships crucial for understanding influence networks.

## Legislative behavior patterns through algorithmic analysis

Voting records provide the richest source for quantifying political relationships through mathematical similarity measures. The API endpoint `/votacoes` returns detailed voting sessions with individual deputy positions (Sim/Não/Abstenção/Obstrução), enabling calculation of pairwise agreement scores. **Brazilian political scientists use cosine similarity and Jaccard indices to measure voting alignment**, with research showing that accounting for abstentions and obstructions (parliamentary tactics) significantly improves accuracy.

A weighted similarity algorithm considering Brazilian-specific vote types produces scores from -1 (complete opposition) to +1 (perfect alignment):
- Same substantive votes (both Yes or both No): +1.0 weight
- Shared abstentions: +0.5 weight (indicates tactical coordination)
- Opposite votes: -1.0 weight  
- Obstruction against any position: -1.0 weight (strong disagreement signal)

Party discipline metrics reveal when deputies break from official orientations, identifying mavericks and coalition fractures. The API's party orientation data (`orientacaoVoto`) enables tracking loyalty scores over time. Parliamentary front memberships often predict voting behavior better than party affiliation, with front cohesion measurable through member voting similarity on relevant topics.

Co-sponsorship networks extracted from `/proposicoes/{id}/autores` reveal collaborative relationships beyond voting. Deputies co-authoring multiple bills form dense clusters indicating working relationships that transcend party boundaries. Committee overlap analysis through `/orgaos/{id}/membros` identifies power brokers holding multiple strategic positions, with leadership roles (President, Vice-President, Rapporteur) weighted higher in influence calculations.

Temporal analysis tracks alliance evolution by comparing voting similarity matrices across legislative sessions, identifying pivotal votes that reshape political positioning. The disparity filter algorithm extracts the "backbone" of significant connections from the complete network, reducing visual complexity while preserving essential structures.

## Cross-referencing judicial and electoral databases

Brazil's judicial system provides multiple APIs revealing legal entanglements of political figures. The CNJ's DataJud platform offers comprehensive access to all court instances through `https://api-publica.datajud.cnj.jus.br/` with state-specific endpoints and 10,000 record response limits. **The system excludes confidential cases under Portaria 160/2020 but includes most political corruption cases**, updating daily with new filings.

The TCU webservices ecosystem deserves special attention with endpoints for rulings (`/api/acordao/recupera-acordaos`), sanctioned companies, and consolidated corporate queries by CNPJ. The CADIRREG database identifies officials with irregular account judgments - a critical red flag for network analysis. While the STF restricts direct API access, the STJ integrates with DataJud providing superior court case metadata in JSON format with daily updates.

TSE's comprehensive electoral API covers results from 1933-2024, candidate information, geographic voting patterns, and historical campaign finance. Electoral alliance data reveals temporary coalitions that shift between elections, while asset declarations track wealth accumulation correlated with political advancement. The API's real-time election feeds and municipal-level granularity enable geographic influence mapping.

The Receita Federal CNPJ database, accessible through government and third-party APIs, exposes corporate ownership structures including the critical QSA (shareholder registry) revealing politician-business relationships. Cross-referencing CNPJ data with government contracts and CEAP expenses uncovers potential conflicts of interest through shared addresses, similar corporate structures, and transaction patterns between politician-linked companies.

Investigative journalism platforms like Abraji's CruzaGrafos provide pre-analyzed relationship graphs combining 29.4 million records from federal and electoral sources. These tools demonstrate the value of visual network exploration for revealing non-obvious connections, though access requires journalistic credentials.

## Designing the 3D force-directed visualization

The 3d-force-graph library by Vasturiano leverages ThreeJS/WebGL rendering with d3-force-3d physics simulation, capable of smoothly handling 1,000-5,000 nodes - sufficient for Brazil's 513 deputies and 81 senators plus key external actors. Performance degrades significantly above 12,000 elements, requiring level-of-detail optimization and dynamic loading strategies.

### Node representation strategy

Deputies should be encoded with **size representing influence scores** calculated from voting power, committee leadership, and media mentions. Party affiliation determines color using official Brazilian party colors (PT: #E20026, PSDB: #4682B4, MDB: #FFD700), with ideological positioning on a left-right spectrum providing additional hue variation. Custom 3D geometries distinguish roles - spheres for regular deputies, cylinders for committee chairs, pyramids for party leaders.

Progressive labeling based on zoom level prevents information overload: showing only party abbreviation at distance, adding names at medium range, and full details including committee memberships and recent votes when close. Node metadata should include temporal data enabling animation of career progression and party switches.

### Multi-dimensional edge taxonomy

Connections require careful visual differentiation through width, color, opacity, and curvature:

**Voting similarity edges** (blue gradient): Width proportional to agreement percentage, opacity indicating vote count reliability. Temporal data enables animation showing strengthening or weakening relationships.

**Financial connections** (green gradient): CEAP vendor sharing, campaign finance relationships, and government contract networks. Edge weight represents transaction volumes with directional arrows for money flow.

**Committee overlap** (purple): Shared committee memberships with weight based on Jaccard similarity and leadership position multipliers.

**Party hierarchy** (party colors): Official leadership structures and caucus memberships with strong visual prominence.

**Judicial connections** (red): Co-defendant status, shared legal representation, or involvement in the same investigations. Opacity indicates case severity.

### Interactive features and filtering

A time slider controlling temporal evolution represents the most critical interface element, smoothly transitioning network structures across legislative sessions while maintaining node positions for visual continuity. **The Louvain algorithm for community detection should run dynamically**, coloring detected communities while preserving party color coding through border highlighting.

Multi-layered filtering enables focusing on specific relationship types, party coalitions, geographic regions, or influence thresholds. Click interactions reveal detailed panels with deputy profiles, recent votes, financial summaries, and judicial status. Edge clicking displays relationship details including temporal strength variations and specific shared votes or transactions.

Search functionality with autocomplete navigates to specific politicians with the camera smoothly zooming to highlighted nodes. A "focus mode" dims unrelated nodes when examining specific subnetworks. Preset views for common analyses (government coalition, opposition block, committee structures) provide starting points for exploration.

### Performance optimization approaches

Dynamic level-of-detail adjusts geometric complexity based on camera distance, reducing distant nodes to simple sprites while rendering close nodes with full detail. Edge pruning hides connections below significance thresholds at distance, with user-adjustable sensitivity. Viewport culling excludes nodes outside camera frustum from physics calculations.

For large temporal datasets, implement progressive loading starting with the current legislative session and loading historical data on demand. Cache calculated metrics like voting similarity matrices to avoid repeated computation. Mobile devices require limiting networks to 1,000 nodes with simplified materials and reduced physics simulation complexity.

## Implementation architecture and data pipeline

A robust data pipeline should combine real-time API calls with preprocessed analytics:

1. **Daily batch processing**: Aggregate voting records, calculate similarity matrices, update influence scores
2. **Real-time updates**: Fetch latest votes, expenses, and news during active sessions
3. **Cross-reference layer**: Match entities across databases using CPF/CNPJ identifiers
4. **Anomaly detection**: Flag unusual patterns for visual emphasis
5. **Cache layer**: Store computed relationships with temporal versioning

The frontend should lazy-load network segments, starting with high-influence nodes and progressively adding peripheral actors. WebSocket connections can push real-time updates during legislative sessions, animating new votes or expenses as they occur.

## Revealing hidden patterns through meaningful connections

The most valuable network patterns for visualization include:

**Voting blocks transcending party lines**: Deputies consistently voting together despite different party affiliations, revealed through community detection algorithms finding dense subgraphs with high internal similarity.

**Financial vendor networks**: Clusters of politicians using the same consultants or service providers, particularly those with vague service descriptions or prices just below reporting thresholds.

**Geographic influence networks**: Cross-state expense patterns and travel networks suggesting coordination, especially visible through CEAP accommodation and transportation expenses.

**Committee power brokers**: Central nodes with high betweenness centrality in committee overlap networks, indicating gatekeepers controlling legislative flow.

**Temporal coalition shifts**: Animated transitions showing alliance reconfigurations around key votes, elections, or political crises like impeachments.

**Dynasty networks**: Family relationships extracted through surname analysis and corporate registries, revealing nepotistic appointment patterns.

By combining these multi-layered data sources with sophisticated visualization techniques, the resulting 3D network transforms raw government data into an intuitive exploration tool revealing the true structure of Brazilian political relationships - from official party hierarchies to hidden financial dependencies and informal power networks that shape legislative outcomes.