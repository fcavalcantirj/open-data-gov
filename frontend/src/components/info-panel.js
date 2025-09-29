/**
 * Info Panel Component for 3D Political Network Visualization
 * Displays detailed information about selected nodes
 */

class InfoPanel {
    constructor(panelElement) {
        this.panel = panelElement;
        this.title = document.getElementById('info-title');
        this.content = document.getElementById('info-content');
        this.closeButton = document.getElementById('close-info');

        this.currentNode = null;
        this.isVisible = false;

        this.init();
    }

    /**
     * Initialize info panel
     */
    init() {
        this.setupEventListeners();
        this.hide();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        this.closeButton?.addEventListener('click', () => {
            this.hide();
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hide();
            }
        });

        // Close when clicking outside (for mobile)
        document.addEventListener('click', (e) => {
            if (this.isVisible && !this.panel.contains(e.target) &&
                !e.target.closest('#3d-graph')) {
                this.hide();
            }
        });
    }

    /**
     * Show node details
     */
    showNodeDetails(node) {
        if (!node) {
            this.hide();
            return;
        }

        this.currentNode = node;
        this.isVisible = true;

        // Update title
        this.title.textContent = this.getNodeTitle(node);

        // Generate content
        this.content.innerHTML = this.generateNodeContent(node);

        // Show panel
        this.panel.classList.add('open');
        this.panel.style.display = 'flex';

        // Add animation
        this.panel.classList.add('slide-in-right');
    }

    /**
     * Hide info panel
     */
    hide() {
        this.isVisible = false;
        this.currentNode = null;

        this.panel.classList.remove('open', 'slide-in-right');

        // Delay hiding to allow animation
        setTimeout(() => {
            if (!this.isVisible) {
                this.panel.style.display = 'none';
            }
        }, 300);
    }

    /**
     * Get node title for header
     */
    getNodeTitle(node) {
        const typeIcons = {
            politician: '👤',
            party: '🏛️',
            company: '🏢',
            sanction: '⚠️'
        };

        const icon = typeIcons[node.type] || '📄';
        return `${icon} ${node.name}`;
    }

    /**
     * Generate detailed content for node
     */
    generateNodeContent(node) {
        let html = '';

        // Entity card
        html += this.generateEntityCard(node);

        // Connections section
        html += this.generateConnectionsSection(node);

        // Action buttons
        html += this.generateActionButtons(node);

        return html;
    }

    /**
     * Generate entity information card
     */
    generateEntityCard(node) {
        let html = `<div class="entity-card ${node.type}">`;

        // Entity type badge
        html += `<div class="entity-type">${node.type}</div>`;

        // Entity name
        html += `<div class="entity-name">${node.name}</div>`;

        // Type-specific details
        html += '<div class="entity-details">';
        html += this.generateEntityDetails(node);
        html += '</div>';

        // Corruption indicators
        if (node.type === 'politician' && node.corruption_score > 0) {
            html += this.generateCorruptionIndicators(node);
        }

        html += '</div>';
        return html;
    }

    /**
     * Generate entity-specific details
     */
    generateEntityDetails(node) {
        let html = '';

        switch (node.type) {
            case 'politician':
                html += this.generatePoliticianDetails(node);
                break;
            case 'party':
                html += this.generatePartyDetails(node);
                break;
            case 'company':
                html += this.generateCompanyDetails(node);
                break;
            case 'sanction':
                html += this.generateSanctionDetails(node);
                break;
        }

        return html;
    }

    /**
     * Generate politician details
     */
    generatePoliticianDetails(node) {
        let html = '';

        if (node.cpf) {
            html += this.createDetailRow('CPF', this.formatCPF(node.cpf));
        }

        if (node.state) {
            html += this.createDetailRow('Estado', node.state);
        }

        if (node.party) {
            html += this.createDetailRow('Partido', node.party);
        }

        if (node.status) {
            html += this.createDetailRow('Status', node.status);
        }

        if (node.email) {
            html += this.createDetailRow('Email', node.email);
        }

        if (node.data?.financial_records?.length) {
            html += this.createDetailRow('Registros Financeiros', node.data.financial_records.length.toString());
        }

        return html;
    }

    /**
     * Generate party details
     */
    generatePartyDetails(node) {
        let html = '';

        if (node.sigla) {
            html += this.createDetailRow('Sigla', node.sigla);
        }

        if (node.members_count) {
            html += this.createDetailRow('Membros', node.members_count.toString());
        }

        if (node.leader) {
            html += this.createDetailRow('Líder', node.leader);
        }

        if (node.status) {
            html += this.createDetailRow('Status', node.status);
        }

        return html;
    }

    /**
     * Generate company details
     */
    generateCompanyDetails(node) {
        let html = '';

        if (node.cnpj) {
            html += this.createDetailRow('CNPJ', this.formatCNPJ(node.cnpj));
        }

        if (node.transaction_count) {
            html += this.createDetailRow('Transações', node.transaction_count.toString());
        }

        if (node.total_value) {
            html += this.createDetailRow('Valor Total', this.formatCurrency(node.total_value));
        }

        return html;
    }

    /**
     * Generate sanction details
     */
    generateSanctionDetails(node) {
        let html = '';

        if (node.sanction_type) {
            html += this.createDetailRow('Tipo', node.sanction_type);
        }

        if (node.target_cnpj) {
            html += this.createDetailRow('CNPJ Alvo', this.formatCNPJ(node.target_cnpj));
        }

        if (node.target_cpf) {
            html += this.createDetailRow('CPF Alvo', this.formatCPF(node.target_cpf));
        }

        if (node.value) {
            html += this.createDetailRow('Valor', this.formatCurrency(node.value));
        }

        if (node.date) {
            html += this.createDetailRow('Data', this.formatDate(node.date));
        }

        return html;
    }

    /**
     * Create a detail row
     */
    createDetailRow(label, value) {
        return `
            <div class="detail-row">
                <span class="detail-label">${label}:</span>
                <span class="detail-value">${value}</span>
            </div>
        `;
    }

    /**
     * Generate corruption indicators
     */
    generateCorruptionIndicators(node) {
        let html = '<div style="margin-top: 12px;">';

        const score = node.corruption_score || 0;
        let levelClass = 'low';
        let levelText = 'Baixo';

        if (score > 50) {
            levelClass = 'high';
            levelText = 'Alto';
        } else if (score > 20) {
            levelClass = 'medium';
            levelText = 'Médio';
        }

        html += `<div class="corruption-indicator ${levelClass}">
            Risco de Corrupção: ${levelText} (${score})
        </div>`;

        html += '</div>';
        return html;
    }

    /**
     * Generate connections section
     */
    generateConnectionsSection(node) {
        // This would require access to the full network data
        // For now, show a placeholder
        let html = '<div class="connections-section">';
        html += '<div class="connections-title">Conexões <span class="connections-count">0</span></div>';
        html += '<div class="connection-list">';
        html += '<p style="color: #b8c5d1; font-style: italic;">Clique em "Explorar Conexões" para ver as relações desta entidade.</p>';
        html += '</div>';
        html += '</div>';

        return html;
    }

    /**
     * Generate action buttons
     */
    generateActionButtons(node) {
        let html = '<div class="action-buttons">';

        html += '<button class="action-button" onclick="window.infoPanel.exploreConnections()">🔍 Explorar Conexões</button>';

        if (node.type === 'politician') {
            html += '<button class="action-button" onclick="window.infoPanel.showFinancialHistory()">💰 Histórico Financeiro</button>';
            html += '<button class="action-button" onclick="window.infoPanel.showCorruptionAnalysis()">⚠️ Análise de Corrupção</button>';
        }

        if (node.type === 'company') {
            html += '<button class="action-button" onclick="window.infoPanel.showCompanyNetwork()">🏢 Rede Empresarial</button>';
        }

        html += '<button class="action-button" onclick="window.infoPanel.focusOnNode()">🎯 Focar no Mapa</button>';
        html += '<button class="action-button" onclick="window.infoPanel.exportNodeData()">📊 Exportar Dados</button>';

        html += '</div>';
        return html;
    }

    /**
     * Action: Explore connections
     */
    exploreConnections() {
        if (!this.currentNode) return;

        // Highlight node connections in the graph
        if (window.networkRenderer) {
            window.networkRenderer.highlightNodeConnections(this.currentNode);
            window.networkRenderer.focusOnNodes([this.currentNode]);
        }

        this.showToast('Conexões destacadas no mapa 3D');
    }

    /**
     * Action: Show financial history
     */
    showFinancialHistory() {
        if (!this.currentNode || this.currentNode.type !== 'politician') return;

        // Update content to show financial details
        const financialRecords = this.currentNode.data?.financial_records || [];

        let html = '<div class="financial-history">';
        html += '<h4>📊 Histórico Financeiro</h4>';

        if (financialRecords.length === 0) {
            html += '<p>Nenhum registro financeiro encontrado.</p>';
        } else {
            html += '<div class="financial-list">';
            financialRecords.slice(0, 10).forEach(record => {
                html += `
                    <div class="financial-item">
                        <div class="financial-value">${this.formatCurrency(record.valor)}</div>
                        <div class="financial-cnpj">CNPJ: ${this.formatCNPJ(record.cnpj)}</div>
                        <div class="financial-date">${this.formatDate(record.data)}</div>
                    </div>
                `;
            });
            html += '</div>';

            if (financialRecords.length > 10) {
                html += `<p style="color: #4a9eff; font-size: 0.9rem;">... e mais ${financialRecords.length - 10} registros</p>`;
            }
        }

        html += '</div>';

        this.content.innerHTML = html;
    }

    /**
     * Action: Show corruption analysis
     */
    showCorruptionAnalysis() {
        if (!this.currentNode || this.currentNode.type !== 'politician') return;

        let html = '<div class="corruption-analysis">';
        html += '<h4>⚠️ Análise de Corrupção</h4>';

        const score = this.currentNode.corruption_score || 0;

        html += `<div class="score-display">
            <div class="score-number">${score}</div>
            <div class="score-label">Pontuação de Risco</div>
        </div>`;

        html += '<div class="risk-factors">';
        html += '<h5>Fatores de Risco:</h5>';

        if (score > 50) {
            html += '<div class="risk-item high">🔴 Alto risco identificado</div>';
            html += '<div class="risk-item">• Múltiplas sanções encontradas</div>';
            html += '<div class="risk-item">• Transações suspeitas detectadas</div>';
        } else if (score > 20) {
            html += '<div class="risk-item medium">🟡 Risco moderado</div>';
            html += '<div class="risk-item">• Algumas irregularidades identificadas</div>';
        } else {
            html += '<div class="risk-item low">🟢 Baixo risco</div>';
            html += '<div class="risk-item">• Nenhuma irregularidade significativa</div>';
        }

        html += '</div>';
        html += '</div>';

        this.content.innerHTML = html;
    }

    /**
     * Action: Focus on node in map
     */
    focusOnNode() {
        if (!this.currentNode || !window.networkRenderer) return;

        window.networkRenderer.focusOnNodes([this.currentNode]);
        this.showToast('Focalizando no mapa 3D');
    }

    /**
     * Action: Export node data
     */
    exportNodeData() {
        if (!this.currentNode) return;

        const data = {
            node_info: {
                id: this.currentNode.id,
                name: this.currentNode.name,
                type: this.currentNode.type
            },
            detailed_data: this.currentNode.data || {}
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentNode.type}_${this.currentNode.id}_data.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showToast('Dados exportados com sucesso');
    }

    /**
     * Show toast notification
     */
    showToast(message) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: rgba(74, 158, 255, 0.9);
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            z-index: 10000;
            animation: slideInRight 0.3s ease;
        `;
        toast.textContent = message;

        document.body.appendChild(toast);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                if (toast.parentNode) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Utility: Format CPF
     */
    formatCPF(cpf) {
        if (!cpf || cpf.length !== 11) return cpf;
        return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }

    /**
     * Utility: Format CNPJ
     */
    formatCNPJ(cnpj) {
        if (!cnpj || cnpj.length !== 14) return cnpj;
        return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }

    /**
     * Utility: Format currency
     */
    formatCurrency(value) {
        if (!value) return 'R$ 0,00';
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    /**
     * Utility: Format date
     */
    formatDate(dateString) {
        if (!dateString) return '';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('pt-BR');
        } catch {
            return dateString;
        }
    }

    /**
     * Update info for current node (if panel is open)
     */
    refresh() {
        if (this.isVisible && this.currentNode) {
            this.showNodeDetails(this.currentNode);
        }
    }

    /**
     * Get current state
     */
    getState() {
        return {
            isVisible: this.isVisible,
            currentNodeId: this.currentNode?.id || null
        };
    }
}

// Export for use in other modules
window.InfoPanel = InfoPanel;