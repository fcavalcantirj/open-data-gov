/**
 * Data Loader for Political Network 3D Visualization
 * Handles API communication with CLI4 backend
 */

class DataLoader {
    constructor() {
        // Use environment variable or fallback to localhost
        this.apiUrl = window.API_URL || 'https://open-data-gov.onrender.com';
        this.cache = new Map();
        this.loadingCallbacks = [];
    }

    /**
     * Set loading status callback
     */
    onLoadingUpdate(callback) {
        this.loadingCallbacks.push(callback);
    }

    /**
     * Update loading status
     */
    updateLoadingStatus(message) {
        this.loadingCallbacks.forEach(callback => callback(message));
    }

    /**
     * Load complete network data for 3D visualization
     */
    async loadNetworkData() {
        try {
            this.updateLoadingStatus('Loading politicians data...');
            const politicians = await this.loadPoliticians();

            this.updateLoadingStatus('Loading political parties...');
            const parties = await this.loadParties();

            this.updateLoadingStatus('Loading companies and vendors...');
            let companies = [];
            try {
                companies = await this.loadCompanies();
            } catch (error) {
                console.warn('Companies data unavailable, continuing without:', error.message);
            }

            this.updateLoadingStatus('Loading sanctions data...');
            let sanctions = [];
            try {
                sanctions = await this.loadSanctions();
            } catch (error) {
                console.warn('Sanctions data unavailable, continuing without:', error.message);
            }

            this.updateLoadingStatus('Building network connections...');
            const connections = await this.loadConnections();

            this.updateLoadingStatus('Building visualization...');

            // Log loaded data counts for debugging
            console.log('📊 Loaded data counts:', {
                politicians: politicians.length,
                parties: parties.length,
                companies: companies.length,
                sanctions: sanctions.length,
                connections: connections.length
            });

            // Transform data for 3D force graph
            const networkData = this.transformToNetworkFormat({
                politicians,
                parties,
                companies,
                sanctions,
                connections
            });

            console.log('🌐 Generated network:', {
                nodes: networkData.nodes.length,
                links: networkData.links.length
            });

            this.updateLoadingStatus('Network ready!');
            return networkData;

        } catch (error) {
            console.error('Error loading network data:', error);
            this.updateLoadingStatus(`Error: ${error.message}`);
            throw error;
        }
    }

    /**
     * Load politicians data
     */
    async loadPoliticians() {
        if (this.cache.has('politicians')) {
            return this.cache.get('politicians');
        }

        try {
            // Try backend API first
            const response = await fetch(`${this.apiUrl}/politicians?limit=${window.APP_CONFIG?.NETWORK_LIMITS?.politicians || 100}`);
            if (response.ok) {
                const apiResponse = await response.json();
                if (apiResponse.success) {
                    const data = apiResponse.data || [];
                    this.cache.set('politicians', data);
                    return data;
                }
            }
            throw new Error(`API response not ok: ${response.status}`);
        } catch (error) {
            console.error('Failed to load politicians data:', error.message);
            throw error;
        }
    }

    /**
     * Load political parties data
     */
    async loadParties() {
        if (this.cache.has('parties')) {
            return this.cache.get('parties');
        }

        try {
            const response = await fetch(`${this.apiUrl}/parties?limit=${window.APP_CONFIG?.NETWORK_LIMITS?.parties || 30}`);
            if (response.ok) {
                const apiResponse = await response.json();
                if (apiResponse.success) {
                    const data = apiResponse.data || [];
                    this.cache.set('parties', data);
                    return data;
                }
            }
            throw new Error(`API response not ok: ${response.status}`);
        } catch (error) {
            console.error('Failed to load parties data:', error.message);
            throw error;
        }
    }

    /**
     * Load companies data
     */
    async loadCompanies() {
        if (this.cache.has('companies')) {
            return this.cache.get('companies');
        }

        try {
            const response = await fetch(`${this.apiUrl}/companies?limit=${window.APP_CONFIG?.NETWORK_LIMITS?.companies || 100}`);
            if (response.ok) {
                const apiResponse = await response.json();
                if (apiResponse.success) {
                    const data = apiResponse.data || [];
                    this.cache.set('companies', data);
                    return data;
                }
            }
            throw new Error(`API response not ok: ${response.status}`);
        } catch (error) {
            console.error('Failed to load companies data:', error.message);
            throw error;
        }
    }

    /**
     * Load sanctions data
     */
    async loadSanctions() {
        if (this.cache.has('sanctions')) {
            return this.cache.get('sanctions');
        }

        try {
            const response = await fetch(`${this.apiUrl}/sanctions?limit=${window.APP_CONFIG?.NETWORK_LIMITS?.sanctions || 100}`);
            if (response.ok) {
                const apiResponse = await response.json();
                if (apiResponse.success) {
                    const data = apiResponse.data || [];
                    this.cache.set('sanctions', data);
                    return data;
                }
            }
            throw new Error(`API response not ok: ${response.status}`);
        } catch (error) {
            console.error('Failed to load sanctions data:', error.message);
            throw error;
        }
    }

    /**
     * Load connections data
     */
    async loadConnections() {
        if (this.cache.has('connections')) {
            return this.cache.get('connections');
        }

        try {
            const response = await fetch(`${this.apiUrl}/connections`);
            if (response.ok) {
                const apiResponse = await response.json();
                if (apiResponse.success) {
                    const data = apiResponse.data || [];
                    this.cache.set('connections', data);
                    return data;
                }
            }
            throw new Error(`API response not ok: ${response.status}`);
        } catch (error) {
            console.error('Failed to load connections data:', error.message);
            throw error;
        }
    }

    /**
     * Transform raw data to 3D force graph format
     */
    transformToNetworkFormat({ politicians, parties, companies, sanctions, connections }) {
        const nodes = [];
        const links = [];

        // Add politician nodes
        politicians.forEach(politician => {
            nodes.push({
                id: `politician_${politician.id}`,
                type: 'politician',
                name: politician.nome || politician.name,
                cpf: politician.cpf,
                state: politician.uf,
                party: politician.sigla_partido,
                status: politician.ultimo_status_situacao,
                email: politician.ultimo_status_email,
                corruption_score: this.calculateCorruptionScore(politician, sanctions),
                size: this.calculateNodeSize('politician', politician),
                color: this.getNodeColor('politician', politician),
                data: politician
            });
        });

        // Add party nodes
        parties.forEach(party => {
            nodes.push({
                id: `party_${party.id}`,
                type: 'party',
                name: party.nome || party.name,
                sigla: party.sigla,
                members_count: party.total_membros || 0,
                leader: party.lider_atual,
                status: party.status,
                size: this.calculateNodeSize('party', party),
                color: this.getNodeColor('party', party),
                data: party
            });
        });

        // Add company nodes
        companies.forEach(company => {
            nodes.push({
                id: `company_${company.cnpj || company.id}`,
                type: 'company',
                name: company.nome_empresa || company.name,
                cnpj: company.cnpj,
                transaction_count: company.transaction_count || 0,
                total_value: company.total_value || 0,
                size: this.calculateNodeSize('company', company),
                color: this.getNodeColor('company', company),
                data: company
            });
        });

        // Add sanction nodes (if showing sanctions)
        sanctions.forEach(sanction => {
            nodes.push({
                id: `sanction_${sanction.id}`,
                type: 'sanction',
                name: `Sanção: ${sanction.tipo_sancao}`,
                sanction_type: sanction.tipo_sancao,
                target_cnpj: sanction.cnpj,
                target_cpf: sanction.cpf,
                value: sanction.valor_multa,
                date: sanction.data_inicio_sancao,
                size: this.calculateNodeSize('sanction', sanction),
                color: this.getNodeColor('sanction', sanction),
                data: sanction
            });
        });

        // Add connections as links
        connections.forEach(connection => {
            links.push({
                source: connection.source_id,
                target: connection.target_id,
                type: connection.type,
                value: connection.value || 1,
                strength: connection.strength || 1,
                color: this.getLinkColor(connection.type),
                data: connection
            });
        });

        // Debug: Log network structure to verify data integrity
        if (nodes.length > 0 && links.length > 0) {
            console.log('🔍 Node IDs preview:', nodes.slice(0, 5).map(n => n.id));
            console.log('🔗 Connection preview:', links.slice(0, 5).map(l => `${l.source} -> ${l.target}`));
        }

        return { nodes, links };
    }

    /**
     * Calculate corruption score for a politician
     */
    calculateCorruptionScore(politician, sanctions) {
        let score = 0;

        // Check for CPF matches in sanctions
        const cpfSanctions = sanctions.filter(s => s.cpf === politician.cpf);
        score += cpfSanctions.length * 10;

        // Check for financial irregularities
        if (politician.financial_records) {
            const suspiciousTransactions = politician.financial_records.filter(
                r => r.valor > 50000 || r.suspicious_patterns
            );
            score += suspiciousTransactions.length * 5;
        }

        // Check for TCU disqualifications
        if (politician.tcu_disqualifications > 0) {
            score += politician.tcu_disqualifications * 15;
        }

        return Math.min(score, 100); // Cap at 100
    }

    /**
     * Calculate node size based on type and importance
     */
    calculateNodeSize(type, data) {
        switch (type) {
            case 'politician':
                return 8 + (data.financial_records?.length || 0) * 0.5;
            case 'party':
                return 12 + (data.total_membros || 0) * 0.2;
            case 'company':
                return 6 + Math.log10((data.total_value || 1000) / 1000) * 2;
            case 'sanction':
                return 4 + Math.log10((data.valor_multa || 1000) / 1000);
            default:
                return 5;
        }
    }

    /**
     * Get node color based on type and properties
     */
    getNodeColor(type, data) {
        const colors = {
            politician: '#ff6b6b',
            party: '#4ecdc4',
            company: '#ffe66d',
            sanction: '#ff8b94'
        };

        let baseColor = colors[type] || '#ffffff';

        // Modify color based on corruption score for politicians
        if (type === 'politician' && data.corruption_score) {
            if (data.corruption_score > 50) baseColor = '#ff4757'; // Red for high corruption
            else if (data.corruption_score > 20) baseColor = '#ffa502'; // Orange for medium
        }

        return baseColor;
    }

    /**
     * Get link color based on connection type
     */
    getLinkColor(type) {
        const colors = {
            party_membership: '#4ecdc4',
            financial: '#ffe66d',
            donation: '#a8e6cf',
            sanction: '#ff8b94',
            corruption_path: '#ff4757'
        };
        return colors[type] || '#ffffff';
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.cache.clear();
    }
}

// Export for use in other modules
window.DataLoader = DataLoader;