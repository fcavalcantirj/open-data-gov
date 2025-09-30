/**
 * Network Renderer for 3D Political Network Visualization
 * Handles 3D force graph rendering and interactions
 */

class NetworkRenderer {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            nodeResolution: 8,
            linkResolution: 4,
            showArrows: true,
            enableNodeDrag: true,
            enableZoom: true,
            backgroundColor: 'rgba(12, 20, 69, 0.1)',
            ...options
        };

        this.graph = null;
        this.data = { nodes: [], links: [] };
        this.filters = {
            politicians: true,
            parties: true,
            companies: true,
            sanctions: true
        };
        this.connectionFilters = {
            party_membership: true,
            financial: true,
            donations: false,
            corruption_paths: false
        };

        this.selectedNode = null;
        this.focusMode = 'overview';
        this.zoomLevel = 0;

        this.eventCallbacks = {
            nodeClick: [],
            nodeHover: [],
            zoomChange: []
        };

        this.init();
    }

    /**
     * Initialize the 3D force graph with professional styling
     */
    init() {
        this.graph = ForceGraph3D()(this.container);

        // Configure graph with proper vasturiano API
        this.graph
            .backgroundColor('#0a0a0a')
            .showNavInfo(false)

            // Node configuration following vasturiano API
            .nodeId('id')
            .nodeLabel(node => this.getNodeLabel(node))
            .nodeVal(node => this.getNodeSize(node))
            .nodeColor(node => this.getNodeColor(node))  // Manual color management instead of auto
            .nodeOpacity(0.75)     // Default vasturiano opacity
            .nodeRelSize(6)        // Proper nodeRelSize (controls sphere volume per value unit)
            .enableNodeDrag(this.options.enableNodeDrag)

            // Link configuration following vasturiano API
            .linkSource('source')
            .linkTarget('target')
            .linkColor(link => this.getLinkColor(link))
            .linkOpacity(0.6)                    // Higher opacity for visibility
            .linkWidth(link => this.getLinkWidth(link))
            .linkDirectionalArrowLength(3)       // Simple arrow length
            .linkDirectionalArrowRelPos(1)       // Arrow at end of link

            // Interactions
            .onNodeClick(node => this.handleNodeClick(node))
            .onNodeHover(node => this.handleNodeHover(node));

        // Add zoom handler if available
        if (typeof this.graph.onZoom === 'function') {
            this.graph.onZoom(({ k, x, y, z }) => this.handleZoomChange(k, x, y, z));
        } else {
            console.warn('onZoom not available in this version of 3d-force-graph');
            // Alternative: Monitor camera position changes
            this.setupAlternativeZoomTracking();
        }

        // Add controls
        this.setupControls();
    }

    /**
     * Setup alternative zoom tracking for older versions
     */
    setupAlternativeZoomTracking() {
        // Monitor camera distance as a proxy for zoom level
        if (this.graph.camera) {
            let lastDistance = 0;
            const checkZoom = () => {
                try {
                    const camera = this.graph.camera();
                    if (camera && camera.position) {
                        const distance = camera.position.length();
                        if (Math.abs(distance - lastDistance) > 10) {
                            // Convert distance to zoom level (0-1)
                            const zoomLevel = Math.max(0, Math.min(1, (1000 - distance) / 1000));
                            this.handleZoomChange(zoomLevel, 0, 0, 0);
                            lastDistance = distance;
                        }
                    }
                } catch (error) {
                    // Ignore errors in zoom tracking
                }
                requestAnimationFrame(checkZoom);
            };
            requestAnimationFrame(checkZoom);
        }
    }

    /**
     * Setup graph controls and physics
     */
    setupControls() {
        // Initialize forces safely
        try {
            // Basic forces
            this.graph.d3Force('charge', this.graph.d3Force('charge') || null);
            this.graph.d3Force('link', this.graph.d3Force('link') || null);
            this.graph.d3Force('center', this.graph.d3Force('center') || null);

            // Update forces with custom settings
            this.updateForcesByZoom();
        } catch (error) {
            console.warn('Force setup error (will retry after data load):', error);
        }
    }

    /**
     * Load and render network data
     */
    async setData(data) {
        this.data = data;
        this.applyFilters();
    }

    /**
     * Apply current filters and update display
     */
    applyFilters() {
        console.log('🔍 FILTER STATE:', this.filters);

        const filteredNodes = this.data.nodes.filter(node => {
            // Map node types to filter keys
            const filterKey = {
                'politician': 'politicians',
                'party': 'parties',
                'company': 'companies',
                'sanction': 'sanctions'
            }[node.type];

            const isVisible = this.filters[filterKey] === true;
            if (!isVisible) {
                console.log(`❌ FILTERING OUT: ${node.type} -> ${filterKey} = ${this.filters[filterKey]}`);
            }
            return isVisible;
        });

        console.log(`📊 FILTERED: ${this.data.nodes.length} → ${filteredNodes.length} nodes`);

        const filteredLinks = this.data.links.filter(link => {
            // Check if both source and target nodes are visible
            const sourceVisible = filteredNodes.some(n => n.id === link.source.id || n.id === link.source);
            const targetVisible = filteredNodes.some(n => n.id === link.target.id || n.id === link.target);

            // Check if connection type is enabled
            const connectionEnabled = this.connectionFilters[link.type] !== false;

            return sourceVisible && targetVisible && connectionEnabled;
        });

        this.graph.graphData({ nodes: filteredNodes, links: filteredLinks });

        // Center the network properly after loading new data
        this.centerNetwork();

        // Update focus based on current mode
        this.updateFocusMode();
    }

    /**
     * Update focus mode and camera position
     */
    updateFocusMode() {
        console.log('🎯 updateFocusMode called with:', this.focusMode);
        switch (this.focusMode) {
            case 'politicians':
                this.focusOnNodeType('politician'); // Convert plural to singular
                break;
            case 'parties':
                this.focusOnNodeType('party'); // Convert plural to singular
                break;
            case 'companies':
                this.focusOnNodeType('company'); // Convert plural to singular
                break;
            case 'corruption':
                this.focusOnCorruptionNetwork();
                break;
            case 'overview':
            default:
                this.clearFocusFilter();
                this.resetCamera();
                break;
        }
    }

    /**
     * Focus camera on specific node type
     */
    focusOnNodeType(nodeType) {
        if (!this.graph || !this.data || !this.data.nodes) {
            console.warn('Graph or data not ready for focus mode');
            return;
        }

        // DEBUG: Show ALL node types in the data
        const allTypes = [...new Set(this.data.nodes.map(n => n.type))];
        console.log('🔍 ALL NODE TYPES IN DATA:', allTypes);
        console.log('🔍 TOTAL NODES:', this.data.nodes.length);

        // Count each type
        const typeCounts = {};
        this.data.nodes.forEach(n => {
            typeCounts[n.type] = (typeCounts[n.type] || 0) + 1;
        });
        console.log('🔍 NODE TYPE COUNTS:', typeCounts);

        const nodes = this.data.nodes.filter(n => n.type === nodeType);
        console.log(`🎯 Looking for nodeType: "${nodeType}"`);
        console.log(`🎯 Found ${nodes.length} matching nodes`);

        if (nodes.length === 0) {
            console.error(`❌ NO NODES FOUND FOR TYPE: "${nodeType}"`);
            console.error('Available types:', allTypes);
            return;
        }

        // Apply visual focus immediately
        this.applyFocusFilter(nodeType);

        // Wait for graph to be properly positioned
        setTimeout(() => {
            // Get fresh node positions from the graph
            const graphData = this.graph.graphData();
            const focusNodes = graphData.nodes.filter(n => n.type === nodeType);

            if (focusNodes.length === 0) {
                this.resetCamera();
                return;
            }

            // Calculate center of nodes with actual positions
            const center = focusNodes.reduce((acc, node) => {
                acc.x += node.x || 0;
                acc.y += node.y || 0;
                acc.z += node.z || 0;
                return acc;
            }, { x: 0, y: 0, z: 0 });

            center.x /= focusNodes.length;
            center.y /= focusNodes.length;
            center.z /= focusNodes.length;

            // Calculate appropriate camera distance based on node spread
            const spread = focusNodes.reduce((max, node) => {
                const distance = Math.sqrt(
                    Math.pow((node.x || 0) - center.x, 2) +
                    Math.pow((node.y || 0) - center.y, 2) +
                    Math.pow((node.z || 0) - center.z, 2)
                );
                return Math.max(max, distance);
            }, 0);

            const cameraDistance = Math.max(spread * 2, 250);

            // Smooth camera transition to focus on these nodes
            this.graph.cameraPosition(
                { x: center.x, y: center.y, z: center.z + cameraDistance },
                { x: center.x, y: center.y, z: center.z },
                2000 // 2 second transition
            );

        }, 500); // Wait for graph layout to settle
    }

    /**
     * Focus on corruption network (high corruption score nodes)
     */
    focusOnCorruptionNetwork() {
        if (!this.graph || !this.data || !this.data.nodes) {
            console.warn('Graph or data not ready for corruption focus mode');
            return;
        }

        const corruptNodes = this.data.nodes.filter(n =>
            (n.type === 'politician' && (n.corruption_score > 50 || n.sanction_count > 0)) ||
            n.type === 'sanction'
        );

        if (corruptNodes.length === 0) {
            console.warn('No corruption-related nodes found');
            this.resetCamera();
            return;
        }

        console.log(`🚨 Focusing on ${corruptNodes.length} corruption-related nodes`);

        // Apply corruption focus filter
        this.applyCorruptionFilter();

        // Wait for graph positioning
        setTimeout(() => {
            const graphData = this.graph.graphData();
            const focusNodes = graphData.nodes.filter(n =>
                (n.type === 'politician' && (n.corruption_score > 50 || n.sanction_count > 0)) ||
                n.type === 'sanction'
            );

            if (focusNodes.length === 0) {
                this.resetCamera();
                return;
            }

            this.focusOnNodesArray(focusNodes);

        }, 500);
    }

    /**
     * Apply visual focus filter for specific node type
     */
    applyFocusFilter(focusType) {
        if (!this.graph || !this.data) return;

        console.log(`🎯 APPLYING VISUAL FOCUS FILTER FOR: ${focusType} - NEW CODE LOADED!!!`);

        // Count nodes by type for debugging
        const nodeCounts = {};
        this.data.nodes.forEach(node => {
            nodeCounts[node.type] = (nodeCounts[node.type] || 0) + 1;
        });
        console.log('Node type counts:', nodeCounts);

        // DEBUG: Log what's happening to each node
        console.log('🔍 APPLYING FOCUS FILTER FOR:', focusType);

        // KEEP ALL NODES FULLY VISIBLE - NO OPACITY CHANGES
        this.graph.nodeOpacity(1.0);  // All nodes fully visible

        // Use SIZE to show focus instead of opacity
        this.graph.nodeVal(node => {
            const isFocused = node.type === focusType;
            if (isFocused) {
                console.log('✅ HIGHLIGHTING WITH SIZE:', node.name, node.type);
                return 20; // Bigger size for focused nodes
            } else {
                return 3;  // Smaller size for non-focused nodes
            }
        });

        // Update link opacity based on focus - show only relevant connections
        this.graph.linkOpacity(link => {
            const sourceIsFocused = link.source.type === focusType;
            const targetIsFocused = link.target.type === focusType;

            if (sourceIsFocused || targetIsFocused) {
                return 0.8;
            }
            return 0.02; // Nearly invisible for non-focused links
        });

        // Refresh the graph to apply changes
        this.graph.refresh();
    }

    /**
     * Apply corruption focus filter
     */
    applyCorruptionFilter() {
        if (!this.graph || !this.data) return;

        console.log(`🚨 Applying corruption focus filter`);

        // Update node opacity based on corruption
        this.graph.nodeOpacity(node => {
            const isCorrupted = (node.type === 'politician' && (node.corruption_score > 50 || node.sanction_count > 0)) ||
                              node.type === 'sanction';
            return isCorrupted ? 1.0 : 0.2;
        });

        // Update node size based on corruption
        this.graph.nodeVal(node => {
            const baseSize = this.getNodeSize(node);
            const isCorrupted = (node.type === 'politician' && (node.corruption_score > 50 || node.sanction_count > 0)) ||
                              node.type === 'sanction';
            return isCorrupted ? baseSize * 2 : baseSize * 0.5;
        });

        // Update link opacity for corruption networks
        this.graph.linkOpacity(link => {
            const sourceCorrupted = (link.source.type === 'politician' && (link.source.corruption_score > 50 || link.source.sanction_count > 0)) ||
                                  link.source.type === 'sanction';
            const targetCorrupted = (link.target.type === 'politician' && (link.target.corruption_score > 50 || link.target.sanction_count > 0)) ||
                                  link.target.type === 'sanction';

            if (sourceCorrupted || targetCorrupted) {
                return 0.9;
            }
            return 0.05;
        });

        // Refresh the graph
        this.graph.refresh();
    }

    /**
     * Clear all focus filters and return to normal view
     */
    clearFocusFilter() {
        if (!this.graph) return;

        console.log(`🔄 Clearing focus filters`);

        // Reset node opacity
        this.graph.nodeOpacity(1.0);

        // Reset node size
        this.graph.nodeVal(node => this.getNodeSize(node));

        // Reset link opacity
        this.graph.linkOpacity(0.6);

        // Refresh the graph
        this.graph.refresh();
    }

    /**
     * Focus camera on array of nodes
     */
    focusOnNodesArray(nodes) {
        if (!nodes || nodes.length === 0) {
            this.resetCamera();
            return;
        }

        // Calculate center of nodes with actual positions
        const center = nodes.reduce((acc, node) => {
            acc.x += node.x || 0;
            acc.y += node.y || 0;
            acc.z += node.z || 0;
            return acc;
        }, { x: 0, y: 0, z: 0 });

        center.x /= nodes.length;
        center.y /= nodes.length;
        center.z /= nodes.length;

        // Calculate appropriate camera distance based on node spread
        const spread = nodes.reduce((max, node) => {
            const distance = Math.sqrt(
                Math.pow((node.x || 0) - center.x, 2) +
                Math.pow((node.y || 0) - center.y, 2) +
                Math.pow((node.z || 0) - center.z, 2)
            );
            return Math.max(max, distance);
        }, 0);

        const cameraDistance = Math.max(spread * 2, 250);

        // Smooth camera transition
        this.graph.cameraPosition(
            { x: center.x, y: center.y, z: center.z + cameraDistance },
            { x: center.x, y: center.y, z: center.z },
            2000
        );
    }

    /**
     * Highlight specific nodes
     */
    highlightNodes(nodes) {
        if (!nodes || !this.graph) return;

        // Clear previous highlights
        this.clearHighlights();

        // Set highlight flag on nodes
        nodes.forEach(node => {
            node.highlighted = true;
        });

        console.log(`✨ Highlighted ${nodes.length} nodes`);
    }

    /**
     * Clear all node highlights
     */
    clearHighlights() {
        if (!this.graph || !this.data) return;

        // Clear highlights from all nodes
        if (this.data.nodes) {
            this.data.nodes.forEach(node => {
                node.highlighted = false;
            });
        }
    }

    /**
     * Highlight corruption connection paths
     */
    highlightCorruptionPaths(nodes) {
        // Find all links connected to high-corruption nodes
        const corruptionLinks = this.data.links.filter(link => {
            const sourceCorrupt = nodes.some(n => n.id === link.source.id || n.id === link.source);
            const targetCorrupt = nodes.some(n => n.id === link.target.id || n.id === link.target);
            return sourceCorrupt || targetCorrupt;
        });

        // Temporarily highlight these links
        corruptionLinks.forEach(link => {
            link.highlighted = true;
        });

        // Update display
        this.graph.linkColor(link =>
            link.highlighted ? '#ff4757' : this.getLinkColor(link)
        );

        // Reset highlighting after 3 seconds
        setTimeout(() => {
            corruptionLinks.forEach(link => {
                link.highlighted = false;
            });
            this.graph.linkColor(link => this.getLinkColor(link));
        }, 3000);
    }

    /**
     * Focus camera on specific nodes
     */
    focusOnNodes(nodes) {
        if (nodes.length === 0) return;

        const center = nodes.reduce((acc, node) => {
            acc.x += node.x || 0;
            acc.y += node.y || 0;
            acc.z += node.z || 0;
            return acc;
        }, { x: 0, y: 0, z: 0 });

        center.x /= nodes.length;
        center.y /= nodes.length;
        center.z /= nodes.length;

        this.graph.cameraPosition(
            { x: center.x, y: center.y, z: center.z + 150 },
            { x: center.x, y: center.y, z: center.z },
            1500
        );
    }

    /**
     * Reset camera to default position
     */
    resetCamera() {
        this.graph.cameraPosition(
            { x: 0, y: 0, z: 1500 }, // Much farther back to see all nodes
            { x: 0, y: 0, z: 0 },
            1000
        );
    }

    /**
     * Get node label for hover tooltip
     */
    getNodeLabel(node) {
        let label = `<div style="background: rgba(0,0,0,0.8); padding: 8px; border-radius: 4px; color: white; font-size: 12px;">`;

        switch (node.type) {
            case 'politician':
                label += `<strong>${node.name}</strong><br/>`;
                label += `${node.party} - ${node.state}<br/>`;
                label += `Status: ${node.status}<br/>`;
                if (node.corruption_score > 0) {
                    label += `⚠️ Corruption Score: ${node.corruption_score}`;
                }
                break;
            case 'party':
                label += `<strong>${node.name}</strong><br/>`;
                label += `${node.sigla}<br/>`;
                label += `Members: ${node.members_count}<br/>`;
                if (node.leader) {
                    label += `Leader: ${node.leader}`;
                }
                break;
            case 'company':
                label += `<strong>${node.name}</strong><br/>`;
                label += `CNPJ: ${node.cnpj}<br/>`;
                label += `Transactions: ${node.transaction_count}<br/>`;
                label += `Total: R$ ${this.formatCurrency(node.total_value)}`;
                break;
            case 'sanction':
                label += `<strong>${node.name}</strong><br/>`;
                label += `Type: ${node.sanction_type}<br/>`;
                label += `Value: R$ ${this.formatCurrency(node.value)}<br/>`;
                label += `Date: ${node.date}`;
                break;
        }

        label += `</div>`;
        return label;
    }

    /**
     * Get node size following vasturiano standards
     */
    getNodeSize(node) {
        if (!node) return 1;

        // Simple node sizing based on type
        switch (node.type) {
            case 'politician':
                return 1;  // Standard size
            case 'party':
                return 3;  // Larger for parties
            case 'company':
                return 1.5;  // Medium size
            case 'sanction':
                return 0.8;  // Smaller
            default:
                return 1;
        }
    }

    /**
     * Get node color
     */
    getNodeColor(node) {
        if (!node) return '#ffffff';

        // Define colors by node type
        let color;
        switch (node.type) {
            case 'politician':
                color = '#ffb366';  // Light orange for politicians
                break;
            case 'party':
                color = '#4ecdc4';  // Teal for parties
                break;
            case 'company':
                color = '#ffe66d';  // Yellow for companies
                break;
            case 'sanction':
                color = '#ff6b6b';  // Red for sanctions
                break;
            default:
                color = '#ffffff';
        }

        // Highlight selected node
        if (this.selectedNode && this.selectedNode.id === node.id) {
            color = '#ffffff';
        }

        return color;
    }

    /**
     * Get link color
     */
    getLinkColor(link) {
        if (!link) return 'rgba(255,255,255,0.3)';

        // Use predefined color or default
        return link.color || 'rgba(255,255,255,0.3)';
    }

    /**
     * Get link width based on strength and zoom
     */
    getLinkWidth(link) {
        if (!link) return 2;

        const baseWidth = Math.max((link.strength || 1) * 2, 1);

        // Adjust width based on zoom level
        if (this.zoomLevel > 0.5) {
            return baseWidth * 3;
        }

        return baseWidth;
    }

    /**
     * Handle node click events
     */
    handleNodeClick(node) {
        this.selectedNode = node;

        // Trigger callbacks for info panel
        this.eventCallbacks.nodeClick.forEach(callback => callback(node));

        // Directly call info panel
        if (window.infoPanel) {
            window.infoPanel.showNodeDetails(node);
        }

        // Zoom to node with smooth animation
        this.zoomToNode(node);
    }

    /**
     * Smoothly pan and zoom camera to focus on a specific node
     */
    zoomToNode(node) {
        if (!node || !this.graph) return;

        try {
            // Get node position (may be undefined if node hasn't been positioned yet)
            const nodeX = node.x || 0;
            const nodeY = node.y || 0;
            const nodeZ = node.z || 0;

            // Get current camera position
            const currentPos = this.graph.cameraPosition();
            const currentDistance = currentPos ?
                Math.sqrt(currentPos.x ** 2 + currentPos.y ** 2 + currentPos.z ** 2) : 400;

            // More conservative zoom - only reduce distance by 30% or min 250 units
            const targetDistance = Math.max(currentDistance * 0.7, 250);

            // Get current camera direction vector
            const currentDir = currentPos ? {
                x: currentPos.x / currentDistance,
                y: currentPos.y / currentDistance,
                z: currentPos.z / currentDistance
            } : { x: 0, y: 0, z: 1 };

            // Position camera maintaining relative angle but closer to node
            const newCameraPos = {
                x: nodeX + (currentDir.x * targetDistance),
                y: nodeY + (currentDir.y * targetDistance),
                z: nodeZ + (currentDir.z * targetDistance)
            };

            // Smooth pan and zoom transition (2 seconds for gentleness)
            this.graph.cameraPosition(
                newCameraPos, // new camera position
                { x: nodeX, y: nodeY, z: nodeZ }, // look at the node
                2000 // 2 second smooth transition
            );

            console.log(`🎯 Panned to ${node.type}: ${node.name} (distance: ${targetDistance.toFixed(0)})`);

        } catch (error) {
            console.warn('Error panning to node:', error);
        }
    }

    /**
     * Center the network view on the data's center of mass
     */
    centerNetwork() {
        if (!this.graph || !this.data || !this.data.nodes.length) return;

        try {
            // Calculate center of mass for all visible nodes
            const visibleNodes = this.data.nodes.filter(node =>
                !this.nodeFilters || this.nodeFilters[node.type] !== false
            );

            if (visibleNodes.length === 0) return;

            const center = visibleNodes.reduce((acc, node) => {
                acc.x += node.x || 0;
                acc.y += node.y || 0;
                acc.z += node.z || 0;
                return acc;
            }, { x: 0, y: 0, z: 0 });

            center.x /= visibleNodes.length;
            center.y /= visibleNodes.length;
            center.z /= visibleNodes.length;

            // Calculate appropriate distance based on network size
            const maxDistance = visibleNodes.reduce((max, node) => {
                const distance = Math.sqrt(
                    ((node.x || 0) - center.x) ** 2 +
                    ((node.y || 0) - center.y) ** 2 +
                    ((node.z || 0) - center.z) ** 2
                );
                return Math.max(max, distance);
            }, 0);

            // Set camera at appropriate distance to see whole network
            const optimalDistance = Math.max(maxDistance * 4, 1200); // Much farther back

            // Position camera to look at center
            this.graph.cameraPosition(
                { x: center.x, y: center.y, z: center.z + optimalDistance },
                center,
                1500 // 1.5 second smooth transition
            );

            console.log(`📍 Centered network: ${visibleNodes.length} nodes, distance: ${optimalDistance.toFixed(0)}`);

        } catch (error) {
            console.warn('Error centering network:', error);
        }
    }

    showNodeModal(node) {
        // Create modal overlay
        const overlay = document.createElement('div');
        overlay.className = 'node-modal-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(5px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

        // Create modal content
        const modal = document.createElement('div');
        modal.className = 'node-modal-content';
        modal.style.cssText = `
            background: linear-gradient(145deg, #1a1a2e, #16213e);
            border: 2px solid #4a9eff;
            border-radius: 16px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            color: #ffffff;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            transform: scale(0.8);
            transition: transform 0.3s ease;
        `;

        modal.innerHTML = this.getNodeModalContent(node);

        // Add close functionality
        const closeBtn = modal.querySelector('.close-modal');
        const closeModal = () => {
            overlay.style.opacity = '0';
            modal.style.transform = 'scale(0.8)';
            setTimeout(() => overlay.remove(), 300);
        };

        closeBtn.addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal();
        });

        // Add to DOM and animate
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Trigger animation
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            modal.style.transform = 'scale(1)';
        });
    }

    getNodeModalContent(node) {
        const getTypeIcon = (type) => {
            switch(type) {
                case 'politician': return '👥';
                case 'party': return '🏛️';
                case 'company': return '🏢';
                case 'sanction': return '⚖️';
                default: return '🔸';
            }
        };

        const getTypeColor = (type) => {
            switch(type) {
                case 'politician': return '#ff6b6b';
                case 'party': return '#4ecdc4';
                case 'company': return '#ffe66d';
                case 'sanction': return '#ff8b94';
                default: return '#ffffff';
            }
        };

        if (node.type === 'politician') {
            return `
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 32px; margin-bottom: 8px;">${getTypeIcon(node.type)}</div>
                    <h2 style="color: ${getTypeColor(node.type)}; margin: 0; font-size: 1.4rem;">${node.name}</h2>
                    <div style="color: #b8c5d1; font-size: 0.9rem; margin-top: 4px;">Político</div>
                </div>

                <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px;">
                    ${node.cpf ? `<div><strong>CPF:</strong> ${node.cpf}</div>` : ''}
                    ${node.state ? `<div><strong>Estado:</strong> ${node.state}</div>` : ''}
                    ${node.party ? `<div><strong>Partido:</strong> ${node.party}</div>` : ''}
                    ${node.status ? `<div><strong>Status:</strong> ${node.status}</div>` : ''}
                    ${node.email ? `<div><strong>Email:</strong> ${node.email}</div>` : ''}
                    ${node.corruption_score ? `<div><strong>Score de Risco:</strong> <span style="color: ${node.corruption_score > 50 ? '#ff4757' : node.corruption_score > 20 ? '#ffa502' : '#2ed573'}">${node.corruption_score}</span></div>` : ''}
                </div>

                <button class="close-modal" style="
                    background: #4a9eff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 1rem;
                    width: 100%;
                    transition: background 0.3s ease;
                " onmouseover="this.style.background='#357abd'" onmouseout="this.style.background='#4a9eff'">
                    Fechar
                </button>
            `;
        } else if (node.type === 'party') {
            return `
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 32px; margin-bottom: 8px;">${getTypeIcon(node.type)}</div>
                    <h2 style="color: ${getTypeColor(node.type)}; margin: 0; font-size: 1.4rem;">${node.name}</h2>
                    <div style="color: #b8c5d1; font-size: 0.9rem; margin-top: 4px;">Partido Político</div>
                </div>

                <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px;">
                    ${node.sigla ? `<div><strong>Sigla:</strong> ${node.sigla}</div>` : ''}
                    ${node.members_count ? `<div><strong>Membros:</strong> ${node.members_count}</div>` : ''}
                    ${node.leader ? `<div><strong>Líder:</strong> ${node.leader}</div>` : ''}
                    ${node.status ? `<div><strong>Status:</strong> ${node.status}</div>` : ''}
                </div>

                <button class="close-modal" style="
                    background: #4a9eff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 1rem;
                    width: 100%;
                    transition: background 0.3s ease;
                " onmouseover="this.style.background='#357abd'" onmouseout="this.style.background='#4a9eff'">
                    Fechar
                </button>
            `;
        } else if (node.type === 'company') {
            return `
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 32px; margin-bottom: 8px;">${getTypeIcon(node.type)}</div>
                    <h2 style="color: ${getTypeColor(node.type)}; margin: 0; font-size: 1.4rem;">${node.name}</h2>
                    <div style="color: #b8c5d1; font-size: 0.9rem; margin-top: 4px;">Empresa</div>
                </div>

                <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px;">
                    ${node.cnpj ? `<div><strong>CNPJ:</strong> ${node.cnpj}</div>` : ''}
                    ${node.transaction_count ? `<div><strong>Transações:</strong> ${node.transaction_count}</div>` : ''}
                    ${node.total_value ? `<div><strong>Valor Total:</strong> R$ ${node.total_value.toLocaleString('pt-BR')}</div>` : ''}
                </div>

                <button class="close-modal" style="
                    background: #4a9eff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 1rem;
                    width: 100%;
                    transition: background 0.3s ease;
                " onmouseover="this.style.background='#357abd'" onmouseout="this.style.background='#4a9eff'">
                    Fechar
                </button>
            `;
        } else if (node.type === 'sanction') {
            return `
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 32px; margin-bottom: 8px;">${getTypeIcon(node.type)}</div>
                    <h2 style="color: ${getTypeColor(node.type)}; margin: 0; font-size: 1.4rem;">${node.name}</h2>
                    <div style="color: #b8c5d1; font-size: 0.9rem; margin-top: 4px;">Sanção</div>
                </div>

                <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px;">
                    ${node.sanction_type ? `<div><strong>Tipo:</strong> ${node.sanction_type}</div>` : ''}
                    ${node.target_cnpj ? `<div><strong>CNPJ Alvo:</strong> ${node.target_cnpj}</div>` : ''}
                    ${node.target_cpf ? `<div><strong>CPF Alvo:</strong> ${node.target_cpf}</div>` : ''}
                    ${node.value ? `<div><strong>Valor da Multa:</strong> R$ ${node.value.toLocaleString('pt-BR')}</div>` : ''}
                    ${node.date ? `<div><strong>Data:</strong> ${node.date}</div>` : ''}
                </div>

                <button class="close-modal" style="
                    background: #4a9eff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 1rem;
                    width: 100%;
                    transition: background 0.3s ease;
                " onmouseover="this.style.background='#357abd'" onmouseout="this.style.background='#4a9eff'">
                    Fechar
                </button>
            `;
        }
    }

    /**
     * Handle node hover events
     */
    handleNodeHover(node) {
        // Trigger callbacks
        this.eventCallbacks.nodeHover.forEach(callback => callback(node));
    }



    /**
     * Handle zoom change events
     */
    handleZoomChange(k, x, y, z) {
        this.zoomLevel = Math.max(0, Math.min(1, (k - 0.5) / 2)); // Normalize to 0-1

        // Update forces based on zoom level
        this.updateForcesByZoom();

        // Trigger callbacks
        this.eventCallbacks.zoomChange.forEach(callback => callback(this.zoomLevel, k, x, y, z));
    }

    /**
     * Update physics forces based on zoom level
     */
    updateForcesByZoom() {
        if (!this.graph) return;

        try {
            // Adjust forces based on zoom level
            const chargeStrength = -120 - (this.zoomLevel * 80); // Reduced repulsion for tighter clusters
            const linkDistance = 40 + (this.zoomLevel * 20); // Shorter links for closer nodes

            // Check if d3 force simulation is available
            if (this.graph.d3Force) {
                // Only update if forces exist
                const chargeForce = this.graph.d3Force('charge');
                const linkForce = this.graph.d3Force('link');

                if (chargeForce && typeof chargeForce.strength === 'function') {
                    chargeForce.strength(chargeStrength);
                }

                if (linkForce && typeof linkForce.distance === 'function') {
                    linkForce.distance(linkDistance).strength(0.5);
                }
            }
        } catch (error) {
            console.warn('Force update error:', error);
        }
    }

    /**
     * Highlight connections for a specific node
     */
    highlightNodeConnections(node) {
        // Find all connected links
        const connectedLinks = this.data.links.filter(link =>
            link.source.id === node.id || link.target.id === node.id ||
            link.source === node.id || link.target === node.id
        );

        // Temporarily highlight connected links
        connectedLinks.forEach(link => {
            link.highlighted = true;
        });

        this.graph.linkColor(link =>
            link.highlighted ? '#4a9eff' : this.getLinkColor(link)
        );

        // Reset after 2 seconds
        setTimeout(() => {
            connectedLinks.forEach(link => {
                link.highlighted = false;
            });
            this.graph.linkColor(link => this.getLinkColor(link));
        }, 2000);
    }


    /**
     * Set node type filter
     */
    setNodeFilter(type, visible) {
        this.filters[type] = visible;
        this.applyFilters();
    }

    /**
     * Set connection type filter
     */
    setConnectionFilter(type, visible) {
        this.connectionFilters[type] = visible;
        this.applyFilters();
    }

    /**
     * Set focus mode
     */
    setFocusMode(mode) {
        this.focusMode = mode;
        this.updateFocusMode();
    }

    /**
     * Update graph layout settings
     */
    updateLayoutSettings(settings) {
        if (!this.graph) return;

        try {
            if (settings.forceStrength !== undefined) {
                const strength = -settings.forceStrength * 10;
                const chargeForce = this.graph.d3Force('charge');
                if (chargeForce && typeof chargeForce.strength === 'function') {
                    chargeForce.strength(strength);
                }
            }

            if (settings.linkDistance !== undefined) {
                const linkForce = this.graph.d3Force('link');
                if (linkForce && typeof linkForce.distance === 'function') {
                    linkForce.distance(settings.linkDistance).strength(0.5);
                }
            }
        } catch (error) {
            console.warn('Layout update error:', error);
        }
    }

    /**
     * Toggle physics simulation
     */
    togglePhysics(enabled) {
        if (enabled) {
            this.graph.resumeAnimation();
        } else {
            this.graph.pauseAnimation();
        }
    }

    /**
     * Add event listener
     */
    addEventListener(event, callback) {
        if (this.eventCallbacks[event]) {
            this.eventCallbacks[event].push(callback);
        }
    }

    /**
     * Utility: Format currency
     */
    formatCurrency(value) {
        if (!value) return '0';
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    /**
     * Get current graph statistics
     */
    getStats() {
        const nodes = this.graph.graphData().nodes;
        const links = this.graph.graphData().links;

        const stats = {
            total_nodes: nodes.length,
            total_links: links.length,
            politicians: nodes.filter(n => n.type === 'politician').length,
            parties: nodes.filter(n => n.type === 'party').length,
            companies: nodes.filter(n => n.type === 'company').length,
            sanctions: nodes.filter(n => n.type === 'sanction').length,
            zoom_level: this.zoomLevel.toFixed(1)
        };

        return stats;
    }

    /**
     * Cleanup
     */
    dispose() {
        if (this.graph) {
            this.graph._destructor();
        }
    }
}

// Export for use in other modules
window.NetworkRenderer = NetworkRenderer;