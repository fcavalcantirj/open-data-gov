/**
 * Controls Handler for 3D Political Network Visualization
 * Manages UI controls and user interactions
 */

class ControlsHandler {
    constructor(networkRenderer) {
        this.renderer = networkRenderer;
        this.elements = {};
        this.init();
    }

    /**
     * Initialize controls and event listeners
     */
    init() {
        this.bindElements();
        this.setupEventListeners();
        this.setupNetworkEventListeners();
    }

    /**
     * Bind DOM elements
     */
    bindElements() {
        // Focus mode
        this.elements.focusMode = document.getElementById('focus-mode');

        // Filters
        this.elements.showPoliticians = document.getElementById('show-politicians');
        this.elements.showParties = document.getElementById('show-parties');
        this.elements.showCompanies = document.getElementById('show-companies');
        this.elements.showSanctions = document.getElementById('show-sanctions');

        // Connections
        this.elements.showPartyMembership = document.getElementById('show-party-membership');
        this.elements.showFinancial = document.getElementById('show-financial');
        this.elements.showDonations = document.getElementById('show-donations');
        this.elements.showCorruptionPaths = document.getElementById('show-corruption-paths');

        // Layout controls - display only (auto-managed)
        this.elements.forceValue = document.getElementById('force-value');
        this.elements.distanceValue = document.getElementById('distance-value');
        this.elements.resetCamera = document.getElementById('reset-camera');
        this.elements.togglePhysics = document.getElementById('toggle-physics');

        // Data size controls
        this.elements.politiciansLimit = document.getElementById('politicians-limit');
        this.elements.politiciansLimitValue = document.getElementById('politicians-limit-value');
        this.elements.companiesLimit = document.getElementById('companies-limit');
        this.elements.companiesLimitValue = document.getElementById('companies-limit-value');
        this.elements.sanctionsLimit = document.getElementById('sanctions-limit');
        this.elements.sanctionsLimitValue = document.getElementById('sanctions-limit-value');
        this.elements.reloadData = document.getElementById('reload-data');

        // Stats displays
        this.elements.nodeCount = document.getElementById('node-count');
        this.elements.linkCount = document.getElementById('link-count');
        this.elements.zoomLevel = document.getElementById('zoom-level');
        this.elements.politiciansCount = document.getElementById('politicians-count');
        this.elements.partiesCount = document.getElementById('parties-count');
        this.elements.companiesCount = document.getElementById('companies-count');
        this.elements.sanctionsCount = document.getElementById('sanctions-count');
    }

    /**
     * Setup event listeners for controls
     */
    setupEventListeners() {
        // Focus mode
        this.elements.focusMode?.addEventListener('change', (e) => {
            this.renderer.setFocusMode(e.target.value);
        });

        // Node type filters
        this.elements.showPoliticians?.addEventListener('change', (e) => {
            this.renderer.setNodeFilter('politicians', e.target.checked);
            this.updateStats();
        });

        this.elements.showParties?.addEventListener('change', (e) => {
            this.renderer.setNodeFilter('parties', e.target.checked);
            this.updateStats();
        });

        this.elements.showCompanies?.addEventListener('change', (e) => {
            this.renderer.setNodeFilter('companies', e.target.checked);
            this.updateStats();
        });

        this.elements.showSanctions?.addEventListener('change', (e) => {
            this.renderer.setNodeFilter('sanctions', e.target.checked);
            this.updateStats();
        });

        // Connection type filters
        this.elements.showPartyMembership?.addEventListener('change', (e) => {
            this.renderer.setConnectionFilter('party_membership', e.target.checked);
            this.updateStats();
        });

        this.elements.showFinancial?.addEventListener('change', (e) => {
            this.renderer.setConnectionFilter('financial', e.target.checked);
            this.updateStats();
        });

        this.elements.showDonations?.addEventListener('change', (e) => {
            this.renderer.setConnectionFilter('donations', e.target.checked);
            this.updateStats();
        });

        this.elements.showCorruptionPaths?.addEventListener('change', (e) => {
            this.renderer.setConnectionFilter('corruption_paths', e.target.checked);
            this.updateStats();
        });

        // Layout controls - now auto-managed by zoom level

        this.elements.resetCamera?.addEventListener('click', () => {
            this.renderer.resetCamera();
        });

        this.elements.togglePhysics?.addEventListener('click', (e) => {
            const isActive = e.target.classList.contains('active');
            if (isActive) {
                e.target.classList.remove('active');
                e.target.textContent = '⚡ Physics: OFF';
                this.renderer.togglePhysics(false);
            } else {
                e.target.classList.add('active');
                e.target.textContent = '⚡ Physics: ON';
                this.renderer.togglePhysics(true);
            }
        });

        // Data size controls - instant visual feedback
        this.elements.politiciansLimit?.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            this.elements.politiciansLimitValue.textContent = value === 1000 ? 'ALL' : value;
            this.updateDataLimits();
            // Show preview of what will be loaded
            this.showDataPreview();
        });

        this.elements.companiesLimit?.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            this.elements.companiesLimitValue.textContent = value === 1000 ? 'ALL' : value;
            this.updateDataLimits();
            this.showDataPreview();
        });

        this.elements.sanctionsLimit?.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            this.elements.sanctionsLimitValue.textContent = value === 500 ? 'ALL' : value;
            this.updateDataLimits();
            this.showDataPreview();
        });

        this.elements.reloadData?.addEventListener('click', () => {
            this.reloadNetworkData();
            this.closeMobileMenu();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }

    /**
     * Setup event listeners for network events
     */
    setupNetworkEventListeners() {
        // Listen for zoom changes to update display
        this.renderer.addEventListener('zoomChange', (zoomLevel) => {
            this.updateZoomLevel(zoomLevel);
        });

        // Listen for node clicks to update info panel
        this.renderer.addEventListener('nodeClick', (node) => {
            this.showNodeInfo(node);
        });
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(e) {
        // Only handle shortcuts if not typing in input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
            return;
        }

        switch (e.key.toLowerCase()) {
            case '1':
                this.setFocusMode('overview');
                break;
            case '2':
                this.setFocusMode('politicians');
                break;
            case '3':
                this.setFocusMode('parties');
                break;
            case '4':
                this.setFocusMode('companies');
                break;
            case '5':
                this.setFocusMode('corruption');
                break;
            case 'r':
                this.renderer.resetCamera();
                break;
            case ' ':
                e.preventDefault();
                this.togglePhysics();
                break;
            case 'p':
                this.toggleFilter('politicians');
                break;
            case 'o':
                this.toggleFilter('parties');
                break;
            case 'c':
                this.toggleFilter('companies');
                break;
            case 's':
                this.toggleFilter('sanctions');
                break;
        }
    }

    /**
     * Set focus mode programmatically
     */
    setFocusMode(mode) {
        if (this.elements.focusMode) {
            this.elements.focusMode.value = mode;
            this.renderer.setFocusMode(mode);
        }
    }

    /**
     * Toggle filter programmatically
     */
    toggleFilter(type) {
        const checkbox = this.elements[`show${type.charAt(0).toUpperCase() + type.slice(1)}`];
        if (checkbox) {
            checkbox.checked = !checkbox.checked;
            checkbox.dispatchEvent(new Event('change'));
        }
    }

    /**
     * Toggle physics programmatically
     */
    togglePhysics() {
        this.elements.togglePhysics?.click();
    }

    /**
     * Update statistics display
     */
    updateStats() {
        const stats = this.renderer.getStats();

        if (this.elements.nodeCount) {
            this.elements.nodeCount.textContent = `Nodes: ${stats.total_nodes}`;
        }

        if (this.elements.linkCount) {
            this.elements.linkCount.textContent = `Links: ${stats.total_links}`;
        }

        if (this.elements.politiciansCount) {
            this.elements.politiciansCount.textContent = stats.politicians;
        }

        if (this.elements.partiesCount) {
            this.elements.partiesCount.textContent = stats.parties;
        }

        if (this.elements.companiesCount) {
            this.elements.companiesCount.textContent = stats.companies;
        }

        if (this.elements.sanctionsCount) {
            this.elements.sanctionsCount.textContent = stats.sanctions;
        }
    }

    /**
     * Update filter counts to reflect actual loaded data
     */
    updateFilterCounts() {
        const stats = this.renderer.getStats();

        // Update filter labels with current counts
        if (this.elements.politiciansCount) {
            this.elements.politiciansCount.textContent = stats.politicians || 0;
        }

        if (this.elements.partiesCount) {
            this.elements.partiesCount.textContent = stats.parties || 0;
        }

        if (this.elements.companiesCount) {
            this.elements.companiesCount.textContent = stats.companies || 0;
        }

        if (this.elements.sanctionsCount) {
            this.elements.sanctionsCount.textContent = stats.sanctions || 0;
        }

        console.log('🔄 Updated filter counts:', stats);
    }

    /**
     * Show preview of data that will be loaded
     */
    showDataPreview() {
        const limits = this.getDataLimits();

        // Update reload button text to show what will be loaded
        if (this.elements.reloadData) {
            const totalNodes = limits.politicians + limits.parties + limits.companies + limits.sanctions;
            const limitText = Object.entries(limits)
                .filter(([key, value]) => key !== 'connections' && value > 0)
                .map(([key, value]) => `${value === 10000 ? 'ALL' : value} ${key}`)
                .join(', ');

            this.elements.reloadData.textContent = `🔄 LOAD: ${limitText}`;
            // Add subtle styling with transparency and blur
            this.elements.reloadData.style.backgroundColor = 'rgba(46, 204, 113, 0.3)';
            this.elements.reloadData.style.color = '#2ecc71';
            this.elements.reloadData.style.border = '1px solid rgba(46, 204, 113, 0.6)';
            this.elements.reloadData.style.fontWeight = 'bold';
            this.elements.reloadData.style.cursor = 'pointer';
            this.elements.reloadData.style.padding = '8px 12px';
            this.elements.reloadData.style.borderRadius = '6px';
            this.elements.reloadData.style.backdropFilter = 'blur(4px)';
            this.elements.reloadData.style.transition = 'all 0.3s ease';
            this.elements.reloadData.style.animation = 'subtle-pulse 2s infinite';

            // Add CSS keyframes for subtle blinking
            if (!document.getElementById('button-animation-style')) {
                const style = document.createElement('style');
                style.id = 'button-animation-style';
                style.textContent = `
                    @keyframes subtle-pulse {
                        0%, 100% { opacity: 0.7; }
                        50% { opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
            }

            // Add hover effects
            this.elements.reloadData.onmouseenter = () => {
                this.elements.reloadData.style.backgroundColor = 'rgba(46, 204, 113, 0.5)';
                this.elements.reloadData.style.color = 'white';
                this.elements.reloadData.style.animation = 'none';
            };
            this.elements.reloadData.onmouseleave = () => {
                this.elements.reloadData.style.backgroundColor = 'rgba(46, 204, 113, 0.3)';
                this.elements.reloadData.style.color = '#2ecc71';
                this.elements.reloadData.style.animation = 'subtle-pulse 2s infinite';
            };

            this.elements.reloadData.title = `Click to load approximately ${totalNodes >= 10000 ? 'ALL' : totalNodes} total nodes`;
        }
    }

    /**
     * Update zoom level display
     */
    updateZoomLevel(zoomLevel) {
        if (this.elements.zoomLevel) {
            this.elements.zoomLevel.textContent = `Zoom: ${(zoomLevel * 100).toFixed(0)}%`;
        }

        // Update UI based on zoom level for better UX
        this.updateUIForZoomLevel(zoomLevel);
    }

    /**
     * Update UI elements based on zoom level
     */
    updateUIForZoomLevel(zoomLevel) {
        // Show/hide different control sections based on zoom
        const detailControls = document.querySelectorAll('.detail-controls');

        if (zoomLevel > 0.6) {
            // High zoom - show detailed controls
            detailControls.forEach(ctrl => ctrl.style.display = 'block');
        } else {
            // Low zoom - hide detailed controls
            detailControls.forEach(ctrl => ctrl.style.display = 'none');
        }

        // Auto-adjust layout settings based on zoom level
        this.autoAdjustLayoutForZoom(zoomLevel);

        // Update connection visibility recommendations
        if (zoomLevel < 0.3) {
            // Suggest hiding financial connections at overview level
            this.suggestConnectionFilters({
                party_membership: true,
                financial: false,
                donations: false,
                corruption_paths: false
            });
        } else if (zoomLevel > 0.7) {
            // Show all connections at detail level
            this.suggestConnectionFilters({
                party_membership: true,
                financial: true,
                donations: true,
                corruption_paths: true
            });
        }
    }

    /**
     * Automatically adjust layout settings based on zoom level
     */
    autoAdjustLayoutForZoom(zoomLevel) {
        // Calculate optimal force strength and link distance based on zoom
        // Overview (zoom out): Stronger forces, shorter links for clustering
        // Detail (zoom in): Weaker forces, longer links for better node spacing

        const minForce = 20;
        const maxForce = 80;
        const minDistance = 50;
        const maxDistance = 200;

        // Invert zoom for force strength (zoom out = stronger forces)
        const forceStrength = Math.round(maxForce - (zoomLevel * (maxForce - minForce)));

        // Direct zoom for link distance (zoom in = longer distances)
        const linkDistance = Math.round(minDistance + (zoomLevel * (maxDistance - minDistance)));

        // Update layout settings if they've changed significantly
        const currentForce = parseInt(this.elements.forceValue?.textContent || 30);
        const currentDistance = parseInt(this.elements.distanceValue?.textContent || 100);

        if (Math.abs(currentForce - forceStrength) > 5 || Math.abs(currentDistance - linkDistance) > 10) {
            // Update display values
            if (this.elements.forceValue) {
                this.elements.forceValue.textContent = forceStrength;
            }

            if (this.elements.distanceValue) {
                this.elements.distanceValue.textContent = linkDistance;
            }

            // Apply to renderer
            this.renderer.updateLayoutSettings({
                forceStrength,
                linkDistance
            });

            console.log(`🎛️ Auto-adjusted layout: Force ${forceStrength}, Distance ${linkDistance} (zoom: ${(zoomLevel * 100).toFixed(0)}%)`);
        }
    }

    /**
     * Suggest connection filter settings (visual cues only)
     */
    suggestConnectionFilters(suggestions) {
        Object.entries(suggestions).forEach(([type, suggested]) => {
            const checkbox = this.elements[`show${this.camelCase(type)}`];
            if (checkbox) {
                // Add visual cue if current setting differs from suggestion
                const current = checkbox.checked;
                if (current !== suggested) {
                    checkbox.parentElement.style.background = 'rgba(74, 158, 255, 0.1)';
                    checkbox.parentElement.style.borderRadius = '4px';
                    checkbox.parentElement.title = `Recommended: ${suggested ? 'enabled' : 'disabled'} at this zoom level`;
                } else {
                    checkbox.parentElement.style.background = '';
                    checkbox.parentElement.title = '';
                }
            }
        });
    }

    /**
     * Show node information in info panel
     */
    showNodeInfo(node) {
        // This will be handled by InfoPanel component
        if (window.infoPanel) {
            window.infoPanel.showNodeDetails(node);
        }
    }

    /**
     * Apply preset configurations
     */
    applyPreset(presetName) {
        const presets = {
            overview: {
                focus: 'overview',
                filters: { politicians: true, parties: true, companies: false, sanctions: false },
                connections: { party_membership: true, financial: false, donations: false, corruption_paths: false }
            },
            political: {
                focus: 'politicians',
                filters: { politicians: true, parties: true, companies: false, sanctions: false },
                connections: { party_membership: true, financial: true, donations: false, corruption_paths: false }
            },
            financial: {
                focus: 'companies',
                filters: { politicians: true, parties: false, companies: true, sanctions: false },
                connections: { party_membership: false, financial: true, donations: true, corruption_paths: false }
            },
            corruption: {
                focus: 'corruption',
                filters: { politicians: true, parties: false, companies: true, sanctions: true },
                connections: { party_membership: false, financial: true, donations: true, corruption_paths: true }
            }
        };

        const preset = presets[presetName];
        if (!preset) return;

        // Apply focus mode
        this.setFocusMode(preset.focus);

        // Apply filters
        Object.entries(preset.filters).forEach(([type, enabled]) => {
            const checkbox = this.elements[`show${this.camelCase(type)}`];
            if (checkbox) {
                checkbox.checked = enabled;
                checkbox.dispatchEvent(new Event('change'));
            }
        });

        // Apply connection filters
        Object.entries(preset.connections).forEach(([type, enabled]) => {
            const checkbox = this.elements[`show${this.camelCase(type)}`];
            if (checkbox) {
                checkbox.checked = enabled;
                checkbox.dispatchEvent(new Event('change'));
            }
        });
    }

    /**
     * Save current configuration to localStorage
     */
    saveConfiguration() {
        const config = {
            focusMode: this.elements.focusMode?.value,
            filters: {
                politicians: this.elements.showPoliticians?.checked,
                parties: this.elements.showParties?.checked,
                companies: this.elements.showCompanies?.checked,
                sanctions: this.elements.showSanctions?.checked
            },
            connections: {
                party_membership: this.elements.showPartyMembership?.checked,
                financial: this.elements.showFinancial?.checked,
                donations: this.elements.showDonations?.checked,
                corruption_paths: this.elements.showCorruptionPaths?.checked
            },
            layout: {
                forceStrength: parseInt(this.elements.forceStrength?.value || 30),
                linkDistance: parseInt(this.elements.linkDistance?.value || 100)
            }
        };

        localStorage.setItem('politicalNetwork3D_config', JSON.stringify(config));
    }

    /**
     * Load configuration from localStorage
     */
    loadConfiguration() {
        const savedConfig = localStorage.getItem('politicalNetwork3D_config');
        if (!savedConfig) return;

        try {
            const config = JSON.parse(savedConfig);

            // Apply saved configuration
            if (config.focusMode && this.elements.focusMode) {
                this.elements.focusMode.value = config.focusMode;
            }

            // Apply filters
            Object.entries(config.filters || {}).forEach(([type, enabled]) => {
                const checkbox = this.elements[`show${this.camelCase(type)}`];
                if (checkbox) {
                    checkbox.checked = enabled;
                }
            });

            // Apply connections
            Object.entries(config.connections || {}).forEach(([type, enabled]) => {
                const checkbox = this.elements[`show${this.camelCase(type)}`];
                if (checkbox) {
                    checkbox.checked = enabled;
                }
            });

            // Apply layout settings
            if (config.layout) {
                if (this.elements.forceStrength && config.layout.forceStrength) {
                    this.elements.forceStrength.value = config.layout.forceStrength;
                    this.elements.forceValue.textContent = config.layout.forceStrength;
                }
                if (this.elements.linkDistance && config.layout.linkDistance) {
                    this.elements.linkDistance.value = config.layout.linkDistance;
                    this.elements.distanceValue.textContent = config.layout.linkDistance;
                }
            }

        } catch (error) {
            console.warn('Error loading saved configuration:', error);
        }
    }

    /**
     * Utility: Convert snake_case to camelCase
     */
    camelCase(str) {
        return str.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
    }

    /**
     * Update data limits configuration
     */
    updateDataLimits() {
        const limits = this.getDataLimits();

        // Update global config with new limits
        if (window.APP_CONFIG) {
            window.APP_CONFIG.NETWORK_LIMITS = {
                ...window.APP_CONFIG.NETWORK_LIMITS,
                ...limits
            };
        }
    }

    /**
     * Get current data limits from sliders
     */
    getDataLimits() {
        const politiciansLimit = parseInt(this.elements.politiciansLimit?.value || 100);
        const companiesLimit = parseInt(this.elements.companiesLimit?.value || 100);
        const sanctionsLimit = parseInt(this.elements.sanctionsLimit?.value || 100);

        return {
            politicians: politiciansLimit === 1000 ? 10000 : politiciansLimit, // 10000 = "ALL"
            parties: 30, // Keep parties small since we only have 3
            companies: companiesLimit === 1000 ? 10000 : companiesLimit,
            sanctions: sanctionsLimit === 500 ? 10000 : sanctionsLimit,
            connections: 5000 // Increase connections for larger datasets
        };
    }

    /**
     * Reload network data with new limits
     */
    async reloadNetworkData() {
        try {
            // Show loading
            const loadingOverlay = document.getElementById('loading-overlay');
            const loadingStatus = document.getElementById('loading-status');

            if (loadingOverlay) {
                loadingOverlay.classList.remove('hidden');
                loadingStatus.textContent = 'Reloading with new data limits...';
            }

            // Clear data loader cache to force fresh data
            if (window.dataLoader) {
                window.dataLoader.clearCache();
            }

            // Update limits
            this.updateDataLimits();

            // Reload network data via main app
            if (window.politicalNetworkApp) {
                await window.politicalNetworkApp.loadAndRenderData();
            }

            // Hide loading
            if (loadingOverlay) {
                setTimeout(() => {
                    loadingOverlay.classList.add('hidden');
                }, 500);
            }

            // Update stats and filter counts
            this.updateStats();
            this.updateFilterCounts();

            // Reset reload button text
            if (this.elements.reloadData) {
                this.elements.reloadData.textContent = '🔄 Reload Network';
                this.elements.reloadData.title = '';
            }

        } catch (error) {
            console.error('Error reloading network data:', error);

            // Hide loading on error
            const loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.classList.add('hidden');
            }

            alert('Error reloading data. Please try again.');
        }
    }

    /**
     * Close mobile menu if open
     */
    closeMobileMenu() {
        if (window.innerWidth <= 900) {
            const controlsPanel = document.querySelector('.controls-panel');
            const controlsToggle = document.getElementById('mobile-controls-toggle');

            if (controlsPanel && controlsPanel.classList.contains('open')) {
                controlsPanel.classList.remove('open');
                if (controlsToggle) {
                    controlsToggle.textContent = '☰';
                    controlsToggle.style.position = 'fixed';
                    controlsToggle.style.top = '70px';
                    controlsToggle.style.left = '10px';
                    controlsToggle.style.zIndex = '1002';
                    controlsToggle.style.fontSize = '';
                    controlsToggle.style.width = '';
                    controlsToggle.style.height = '';
                }
            }
        }
    }

    /**
     * Get current control states
     */
    getState() {
        return {
            focusMode: this.elements.focusMode?.value,
            filters: {
                politicians: this.elements.showPoliticians?.checked,
                parties: this.elements.showParties?.checked,
                companies: this.elements.showCompanies?.checked,
                sanctions: this.elements.showSanctions?.checked
            },
            connections: {
                party_membership: this.elements.showPartyMembership?.checked,
                financial: this.elements.showFinancial?.checked,
                donations: this.elements.showDonations?.checked,
                corruption_paths: this.elements.showCorruptionPaths?.checked
            },
            dataLimits: this.getDataLimits()
        };
    }
}

// Export for use in other modules
window.ControlsHandler = ControlsHandler;