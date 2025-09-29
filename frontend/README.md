# Brazilian Political Network 3D Visualization

A powerful 3D interactive visualization of Brazilian political networks, revealing connections between politicians, parties, companies, and corruption patterns.

## 🎯 Features

### Core Visualization
- **3D Force-Directed Graph**: Interactive network using vasturiano/3d-force-graph
- **Multi-Level Zoom**: Different connection details at various zoom levels
- **Real-Time Filtering**: Toggle politicians, parties, companies, and sanctions
- **Focus Modes**: Overview, Political, Financial, and Corruption views

### Node Types
- 👥 **Politicians**: Deputies with corruption scores and financial records
- 🏛️ **Political Parties**: Party membership and leadership information
- 🏢 **Companies**: Business entities with transaction volumes
- ⚠️ **Sanctions**: Government penalties and disqualifications

### Connection Analysis
- 🎭 **Party Membership**: Political affiliations
- 💰 **Financial Transactions**: Money flows and contracts
- 🎁 **Campaign Donations**: Electoral financing networks
- 🚨 **Corruption Paths**: Detected suspicious connections

### Interactive Features
- **Clickable Nodes**: Detailed information panels
- **Connection Highlighting**: Trace relationships
- **Corruption Detection**: Automated risk scoring
- **Data Export**: JSON and image export capabilities

## 🚀 Quick Start

### Installation
```bash
cd frontend
npm install
```

### Development
```bash
npm run dev
# Opens http://localhost:3000
```

### Production
```bash
npm start
# Serves static files on port 3000
```

## 🎮 Controls

### Mouse/Touch
- **Drag**: Rotate 3D view
- **Scroll/Pinch**: Zoom in/out
- **Click**: Select node for details
- **Double-click**: Focus on node

### Keyboard Shortcuts
- **1-5**: Change focus mode (Overview, Politicians, Parties, Companies, Corruption)
- **R**: Reset camera position
- **Space**: Toggle physics simulation
- **P**: Toggle politicians visibility
- **O**: Toggle parties visibility
- **C**: Toggle companies visibility
- **S**: Toggle sanctions visibility
- **H**: Show help dialog
- **F**: Toggle fullscreen
- **I**: Close info panel
- **Esc**: Close all panels

## 📊 Data Integration

### Backend API Requirements

The frontend expects the following API endpoints:

```
GET /api/politicians
GET /api/parties
GET /api/companies
GET /api/sanctions
GET /api/connections
```

### Data Formats

#### Politicians
```json
{
  "id": 1,
  "nome": "Name",
  "cpf": "12345678901",
  "uf": "SP",
  "sigla_partido": "PP",
  "ultimo_status_situacao": "Exercício",
  "corruption_score": 85,
  "financial_records": [...]
}
```

#### Parties
```json
{
  "id": 1,
  "nome": "Party Name",
  "sigla": "PP",
  "total_membros": 45,
  "lider_atual": "Leader Name",
  "status": "Ativo"
}
```

#### Companies
```json
{
  "id": 1,
  "cnpj": "12345678901234",
  "nome_empresa": "Company Name",
  "transaction_count": 15,
  "total_value": 2500000
}
```

#### Connections
```json
{
  "source_id": "politician_1",
  "target_id": "party_1",
  "type": "party_membership",
  "value": 1,
  "strength": 1
}
```

## 🎨 Customization

### Node Colors
- Politicians: `#ff6b6b` (Red spectrum based on corruption score)
- Parties: `#4ecdc4` (Teal)
- Companies: `#ffe66d` (Yellow)
- Sanctions: `#ff8b94` (Pink)

### Connection Colors
- Party Membership: `#4ecdc4`
- Financial: `#ffe66d`
- Donations: `#a8e6cf`
- Sanctions: `#ff8b94`
- Corruption Paths: `#ff4757`

### Layout Configuration
```javascript
// Force simulation settings
chargeStrength: -300    // Node repulsion
linkDistance: 100       // Base link length
collisionRadius: 5      // Node collision buffer
```

## 🔧 Architecture

### Component Structure
```
src/
├── api/
│   └── data-loader.js          # API communication
├── components/
│   ├── network-renderer.js     # 3D graph rendering
│   ├── controls-handler.js     # UI controls management
│   └── info-panel.js          # Node details panel
├── styles/
│   ├── main.css               # Core application styles
│   ├── controls.css           # Control panel styles
│   └── info-panel.css         # Info panel styles
└── main.js                    # Application entry point
```

### Dependencies
- **3d-force-graph**: 3D network visualization
- **three.js**: 3D graphics rendering
- **d3-force**: Physics simulation

## 🎯 Focus Modes

### Overview Mode
- High-level network structure
- Party-politician relationships only
- Simplified node rendering

### Political Mode
- Focus on political entities
- Party memberships highlighted
- Leader connections emphasized

### Financial Mode
- Business transaction networks
- Company-politician relationships
- Transaction volume visualization

### Corruption Mode
- High-risk entities highlighted
- Suspicious connection paths
- Automated corruption scoring

## 🔍 Corruption Detection

### Scoring Algorithm
```javascript
// Base corruption score calculation
let score = 0;
score += cpfSanctions.length * 10;           // Direct sanctions
score += suspiciousTransactions.length * 5;  // Financial irregularities
score += tcuDisqualifications * 15;          // TCU audit issues
return Math.min(score, 100);                 // Cap at 100
```

### Risk Levels
- **Low (0-20)**: 🟢 Minimal risk detected
- **Medium (21-50)**: 🟡 Some irregularities found
- **High (51+)**: 🔴 Significant corruption indicators

## 📱 Responsive Design

### Desktop (1200px+)
- Full three-panel layout
- Advanced controls visible
- Optimal performance

### Tablet (900-1200px)
- Condensed control panels
- Touch-optimized interactions
- Simplified UI elements

### Mobile (<900px)
- Sliding panel overlays
- Touch gestures enabled
- Essential controls only

## 🚀 Performance

### Optimization Features
- **Dynamic LOD**: Level-of-detail based on zoom
- **Frustum Culling**: Render only visible nodes
- **Adaptive Quality**: Auto-adjust based on FPS
- **Memory Management**: Efficient data structures

### Performance Monitoring
- Real-time FPS display
- Memory usage tracking
- Automatic quality adjustment
- Performance warnings

## 🔐 Security

### Data Handling
- Client-side processing only
- No sensitive data storage
- Secure API communication
- CORS-enabled endpoints

### Privacy
- No user tracking
- Local configuration storage
- Anonymous usage patterns
- Encrypted API calls (HTTPS)

## 🧪 Development

### Mock Data
Development mode includes built-in mock data for testing without backend:
- Sample politicians (Arthur Lira, Rodrigo Maia)
- Mock parties (PP, DEM)
- Simulated companies and sanctions
- Generated connection networks

### Debug Mode
Press **D** to toggle debug information:
- Node/link counts
- FPS monitoring
- Memory usage
- Focus mode status

### Testing
```bash
# Manual testing with mock data
npm run dev

# Load real data (requires CLI4 backend)
# Ensure backend is running on expected endpoints
```

## 📈 Future Enhancements

### Planned Features
- **Temporal Analysis**: Time-based network evolution
- **Machine Learning**: Automated pattern detection
- **Real-time Updates**: Live data synchronization
- **Advanced Filtering**: Complex query builder
- **Export Options**: Multiple format support

### Integration Roadmap
- **Neo4j Backend**: Graph database integration
- **Real-time Alerts**: Automated corruption detection
- **Mobile App**: React Native version
- **API Gateway**: Scalable backend architecture

## 🤝 Contributing

### Development Setup
1. Clone repository
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`
4. Open browser to `http://localhost:3000`

### Code Style
- ES6+ JavaScript
- Component-based architecture
- Comprehensive documentation
- Performance-first approach

## 📄 License

MIT License - see LICENSE file for details.

---

**🏛️ Brazilian Political Network 3D**
*Transparency through visualization*