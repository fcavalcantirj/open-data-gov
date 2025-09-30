/**
 * Main Application Entry Point
 * Brazilian Political Network 3D Visualization
 */

class PoliticalNetwork3DApp {
    constructor() {
        this.dataLoader = null;
        this.networkRenderer = null;
        this.controlsHandler = null;
        this.infoPanel = null;

        this.isInitialized = false;
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingStatus = document.getElementById('loading-status');

        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            this.showLoading('Initializing 3D Political Network...');

            // Initialize components
            this.initializeComponents();

            // Load and render data
            await this.loadAndRenderData();

            // Setup event handlers
            this.setupEventHandlers();

            // Load saved configuration
            this.loadConfiguration();

            this.hideLoading();
            this.isInitialized = true;

            console.log('🏛️ Brazilian Political Network 3D initialized successfully');

        } catch (error) {
            console.error('Error initializing application:', error);
            this.showError('Failed to initialize application: ' + error.message);
        }
    }

    /**
     * Initialize all components
     */
    initializeComponents() {
        this.showLoading('Initializing components...');

        // Initialize data loader
        this.dataLoader = new DataLoader();
        this.dataLoader.onLoadingUpdate(message => {
            this.updateLoadingStatus(message);
        });

        // Initialize 3D network renderer
        const graphContainer = document.getElementById('3d-graph');
        this.networkRenderer = new NetworkRenderer(graphContainer, {
            nodeResolution: 8,
            linkResolution: 4,
            showArrows: true,
            enableNodeDrag: true,
            enableZoom: true,
            backgroundColor: 'rgba(12, 20, 69, 0.1)'
        });

        // Initialize controls handler
        this.controlsHandler = new ControlsHandler(this.networkRenderer);

        // Initialize info panel
        const infoPanelElement = document.getElementById('info-panel');
        this.infoPanel = new InfoPanel(infoPanelElement);

        // Load and display versions
        this.loadVersions();

        // Make components globally available
        window.networkRenderer = this.networkRenderer;
        window.controlsHandler = this.controlsHandler;
        window.infoPanel = this.infoPanel;
        window.dataLoader = this.dataLoader;

        console.log('✅ Components initialized');
    }

    /**
     * Load and render network data
     */
    async loadAndRenderData() {
        try {
            this.showLoading('Loading network data...');

            // Load complete network data
            const networkData = await this.dataLoader.loadNetworkData();

            this.showLoading('Rendering 3D network...');

            // Set data to renderer
            await this.networkRenderer.setData(networkData);

            // Update statistics
            this.controlsHandler.updateStats();

            console.log('✅ Network data loaded and rendered');
            console.log(`📊 Stats: ${networkData.nodes.length} nodes, ${networkData.links.length} links`);

        } catch (error) {
            console.error('Error loading network data:', error);
            throw new Error('Failed to load network data: ' + error.message);
        }
    }

    /**
     * Setup application event handlers
     */
    setupEventHandlers() {
        // Network renderer events
        this.networkRenderer.addEventListener('nodeClick', (node) => {
            this.infoPanel.showNodeDetails(node);
        });

        this.networkRenderer.addEventListener('zoomChange', (zoomLevel) => {
            this.handleZoomChange(zoomLevel);
        });

        // Window events
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });

        window.addEventListener('beforeunload', () => {
            this.saveConfiguration();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeyboard(e);
        });

        // Mobile toggle buttons
        this.setupMobileToggles();

        // Performance monitoring
        this.setupPerformanceMonitoring();

        console.log('✅ Event handlers setup');
    }

    /**
     * Setup mobile toggle buttons
     */
    setupMobileToggles() {
        const controlsToggle = document.getElementById('mobile-controls-toggle');
        const infoToggle = document.getElementById('mobile-info-toggle');
        const controlsPanel = document.querySelector('.controls-panel');
        const infoPanel = document.querySelector('.info-panel');

        if (controlsToggle && controlsPanel) {
            controlsToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const isOpen = controlsPanel.classList.contains('open');

                if (isOpen) {
                    // Close menu
                    controlsPanel.classList.remove('open');
                    controlsToggle.textContent = '☰';
                    controlsToggle.style.position = 'fixed';
                    controlsToggle.style.top = '70px';
                    controlsToggle.style.left = '10px';
                    controlsToggle.style.zIndex = '1002';
                    controlsToggle.style.fontSize = '';
                    controlsToggle.style.width = '';
                    controlsToggle.style.height = '';
                } else {
                    // Open menu
                    controlsPanel.classList.add('open');
                    controlsToggle.textContent = '✕';
                    controlsToggle.style.position = 'fixed';
                    controlsToggle.style.top = '70px';
                    controlsToggle.style.right = '20px';
                    controlsToggle.style.left = 'auto';
                    controlsToggle.style.zIndex = '1003';
                    controlsToggle.style.fontSize = '18px';
                    controlsToggle.style.width = '40px';
                    controlsToggle.style.height = '40px';
                }

                // Close info panel if open
                if (infoPanel && infoPanel.classList.contains('open')) {
                    infoPanel.classList.remove('open');
                }
            });
        }

        if (infoToggle && infoPanel) {
            infoToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                infoPanel.classList.toggle('open');
                // Close controls panel if open
                if (controlsPanel && controlsPanel.classList.contains('open')) {
                    controlsPanel.classList.remove('open');
                }
            });
        }

        // Close panels when clicking on the graph (but not on nodes)
        const graph = document.getElementById('3d-graph');
        if (graph) {
            graph.addEventListener('click', (e) => {
                // Only close if it's a direct click on the graph background, not on nodes
                if (e.target === graph && window.innerWidth <= 900) {
                    if (controlsPanel) controlsPanel.classList.remove('open');
                    if (infoPanel) infoPanel.classList.remove('open');
                }
            });
        }
    }

    /**
     * Handle zoom level changes
     */
    handleZoomChange(zoomLevel) {
        // Auto-adjust settings based on zoom level
        if (zoomLevel < 0.2) {
            // Overview mode - reduce detail
            this.networkRenderer.graph.nodeResolution(4);
            this.networkRenderer.graph.linkResolution(2);
        } else if (zoomLevel > 0.7) {
            // Detail mode - increase detail
            this.networkRenderer.graph.nodeResolution(12);
            this.networkRenderer.graph.linkResolution(6);
        } else {
            // Normal mode
            this.networkRenderer.graph.nodeResolution(8);
            this.networkRenderer.graph.linkResolution(4);
        }
    }

    /**
     * Handle window resize
     */
    handleWindowResize() {
        // Debounce resize events
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            if (this.networkRenderer && this.networkRenderer.graph) {
                // Force graph to resize
                this.networkRenderer.graph.width(window.innerWidth);
                this.networkRenderer.graph.height(window.innerHeight);
            }
        }, 250);
    }

    /**
     * Handle global keyboard shortcuts
     */
    handleGlobalKeyboard(e) {
        // Skip if typing in input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        switch (e.key.toLowerCase()) {
            case 'h':
                this.showHelp();
                break;
            case 'f':
                this.toggleFullscreen();
                break;
            case 'd':
                this.toggleDebugMode();
                break;
            case 'x':
                this.exportCurrentView();
                break;
            case 'i':
                this.infoPanel.hide();
                break;
        }
    }

    /**
     * Setup performance monitoring
     */
    setupPerformanceMonitoring() {
        // Monitor FPS
        let frameCount = 0;
        let lastTime = performance.now();

        const monitorFPS = () => {
            frameCount++;
            const currentTime = performance.now();

            if (currentTime - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));

                // Update FPS display (if element exists)
                const fpsDisplay = document.getElementById('fps-display');
                if (fpsDisplay) {
                    fpsDisplay.textContent = `FPS: ${fps}`;
                }

                // Warn if FPS is too low
                if (fps < 20 && this.isInitialized) {
                    console.warn(`⚠️ Low FPS detected: ${fps}. Consider reducing node count or detail level.`);
                }

                frameCount = 0;
                lastTime = currentTime;
            }

            requestAnimationFrame(monitorFPS);
        };

        requestAnimationFrame(monitorFPS);

        // Monitor memory usage (if available)
        if (performance.memory) {
            setInterval(() => {
                const memoryMB = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);

                if (memoryMB > 500) {
                    console.warn(`⚠️ High memory usage: ${memoryMB}MB`);
                }
            }, 10000);
        }
    }

    /**
     * Show loading overlay
     */
    showLoading(message) {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('hidden');
            this.updateLoadingStatus(message);
        }
    }

    /**
     * Hide loading overlay
     */
    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('hidden');
        }
    }

    /**
     * Update loading status message
     */
    updateLoadingStatus(message) {
        if (this.loadingStatus) {
            this.loadingStatus.textContent = message;
        }
        console.log(`🔄 ${message}`);
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error('❌', message);

        // Update loading overlay to show error
        if (this.loadingOverlay && this.loadingStatus) {
            this.loadingStatus.innerHTML = `
                <div style="color: #ff6b6b;">
                    <h3>❌ Error</h3>
                    <p>${message}</p>
                    <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background: #4a9eff; border: none; border-radius: 4px; color: white; cursor: pointer;">
                        🔄 Retry
                    </button>
                </div>
            `;
        }
    }

    /**
     * Show help dialog
     */
    showHelp() {
        const helpContent = `
            <div style="max-width: 600px; background: rgba(0,0,0,0.9); padding: 20px; border-radius: 8px; color: white;">
                <h2>🏛️ Political Network 3D - Help</h2>

                <h3>🎮 Controls</h3>
                <ul>
                    <li><strong>Mouse:</strong> Drag to rotate, scroll to zoom</li>
                    <li><strong>Click:</strong> Select nodes for details</li>
                    <li><strong>Double-click:</strong> Focus on node</li>
                </ul>

                <h3>⌨️ Keyboard Shortcuts</h3>
                <ul>
                    <li><strong>1-5:</strong> Change focus mode</li>
                    <li><strong>R:</strong> Reset camera</li>
                    <li><strong>Space:</strong> Toggle physics</li>
                    <li><strong>P:</strong> Toggle politicians</li>
                    <li><strong>O:</strong> Toggle parties</li>
                    <li><strong>C:</strong> Toggle companies</li>
                    <li><strong>S:</strong> Toggle sanctions</li>
                    <li><strong>H:</strong> Show this help</li>
                    <li><strong>F:</strong> Toggle fullscreen</li>
                    <li><strong>I:</strong> Close info panel</li>
                    <li><strong>Esc:</strong> Close panels</li>
                </ul>

                <h3>🎯 Focus Modes</h3>
                <ul>
                    <li><strong>Overview:</strong> Full network view</li>
                    <li><strong>Politicians:</strong> Focus on political figures</li>
                    <li><strong>Parties:</strong> Focus on political parties</li>
                    <li><strong>Companies:</strong> Focus on business networks</li>
                    <li><strong>Corruption:</strong> Highlight corruption paths</li>
                </ul>

                <button onclick="this.parentElement.parentElement.remove()"
                        style="margin-top: 15px; padding: 8px 16px; background: #4a9eff; border: none; border-radius: 4px; color: white; cursor: pointer;">
                    Close Help
                </button>
            </div>
        `;

        this.showModal(helpContent);
    }

    /**
     * Toggle fullscreen mode
     */
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.warn('Could not enter fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * Toggle debug mode
     */
    toggleDebugMode() {
        const debugInfo = document.getElementById('debug-info') || this.createDebugInfo();
        debugInfo.style.display = debugInfo.style.display === 'none' ? 'block' : 'none';
    }

    /**
     * Create debug info panel
     */
    createDebugInfo() {
        const debugDiv = document.createElement('div');
        debugDiv.id = 'debug-info';
        debugDiv.style.cssText = `
            position: fixed;
            top: 60px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            z-index: 1000;
            max-width: 300px;
        `;

        const updateDebugInfo = () => {
            const stats = this.networkRenderer?.getStats() || {};
            debugDiv.innerHTML = `
                <strong>🐛 Debug Info</strong><br>
                Nodes: ${stats.total_nodes || 0}<br>
                Links: ${stats.total_links || 0}<br>
                Zoom: ${stats.zoom_level || '0.0'}<br>
                FPS: <span id="fps-display">--</span><br>
                Memory: ${performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) + 'MB' : 'N/A'}<br>
                Focus: ${this.controlsHandler?.elements.focusMode?.value || 'unknown'}
            `;
        };

        updateDebugInfo();
        setInterval(updateDebugInfo, 1000);

        document.body.appendChild(debugDiv);
        return debugDiv;
    }

    /**
     * Export current view as image
     */
    exportCurrentView() {
        if (!this.networkRenderer || !this.networkRenderer.graph) {
            console.warn('Cannot export: renderer not available');
            return;
        }

        try {
            // Get renderer canvas
            const canvas = this.networkRenderer.graph.renderer().domElement;

            // Create download link
            canvas.toBlob(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `political_network_3d_${new Date().toISOString().slice(0, 10)}.png`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                console.log('✅ View exported as image');
            });

        } catch (error) {
            console.error('Error exporting view:', error);
        }
    }

    /**
     * Show modal dialog
     */
    showModal(content) {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        `;

        modal.innerHTML = content;
        document.body.appendChild(modal);

        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        // Close on Escape
        const closeOnEscape = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', closeOnEscape);
            }
        };
        document.addEventListener('keydown', closeOnEscape);
    }

    /**
     * Save current configuration
     */
    saveConfiguration() {
        if (this.controlsHandler) {
            this.controlsHandler.saveConfiguration();
        }
    }

    /**
     * Load saved configuration
     */
    loadConfiguration() {
        if (this.controlsHandler) {
            this.controlsHandler.loadConfiguration();
        }
    }

    /**
     * Load and display versions dynamically
     */
    async loadVersions() {
        try {
            // Load frontend version from package.json
            const packageResponse = await fetch('./package.json');
            const packageData = await packageResponse.json();
            const frontendVersion = packageData.version;

            // Load API version from backend
            let apiVersion = 'N/A';
            try {
                const apiResponse = await fetch('https://open-data-gov.onrender.com/version');
                if (apiResponse.ok) {
                    const apiData = await apiResponse.json();
                    apiVersion = apiData.version || apiData.data?.version || 'unknown';
                }
            } catch (error) {
                console.warn('Could not fetch API version:', error.message);
            }

            // Update header displays
            const frontendElement = document.getElementById('frontend-version');
            const apiElement = document.getElementById('api-version');

            if (frontendElement) {
                frontendElement.textContent = `Frontend: v${frontendVersion}`;
            }

            if (apiElement) {
                apiElement.textContent = `API: v${apiVersion}`;
            }

            console.log('📋 Versions loaded:', { frontend: frontendVersion, api: apiVersion });

        } catch (error) {
            console.warn('Error loading versions:', error.message);
        }
    }

    /**
     * Get application state
     */
    getState() {
        return {
            initialized: this.isInitialized,
            renderer: this.networkRenderer?.getStats(),
            controls: this.controlsHandler?.getState(),
            infoPanel: this.infoPanel?.getState()
        };
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        if (this.networkRenderer) {
            this.networkRenderer.dispose();
        }

        // Clear timers
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }

        console.log('🧹 Application cleaned up');
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.politicalNetworkApp = new PoliticalNetwork3DApp();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.politicalNetworkApp) {
        window.politicalNetworkApp.cleanup();
    }
});