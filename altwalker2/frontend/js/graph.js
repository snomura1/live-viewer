/**
 * Graph Visualization using AntV G6
 */

class GraphVisualizer {
    constructor(containerId) {
        this.containerId = containerId;
        this.graph = null;
        this.models = [];
        this.visitCounts = {};
        this.currentStepId = null;
        this.failedStepId = null;
        this.layoutDirection = 'TB';

        // Color scale for visit counts
        this.colorScale = d3.scaleLinear()
            .domain([0, 5])
            .range(['#d1f4e0', '#10b981'])
            .clamp(true);
    }

    initialize() {
        const container = document.getElementById(this.containerId);
        const width = container.offsetWidth;
        const height = container.offsetHeight;

        this.graph = new G6.Graph({
            container: this.containerId,
            width: width,
            height: height,
            fitView: true,
            fitViewPadding: [40, 40, 40, 40],
            modes: {
                default: ['drag-canvas', 'zoom-canvas', 'drag-node']
            },
            layout: {
                type: 'dagre',
                rankdir: this.layoutDirection,
                nodesep: 50,
                ranksep: 70,
                controlPoints: true
            },
            defaultNode: {
                type: 'rect',
                size: [120, 40],
                style: {
                    fill: '#ffffff',
                    stroke: '#5B8FF9',
                    lineWidth: 2,
                    radius: 4
                },
                labelCfg: {
                    style: {
                        fill: '#1f2937',
                        fontSize: 12,
                        fontWeight: 500
                    }
                }
            },
            defaultEdge: {
                type: 'polyline',
                style: {
                    stroke: '#94a3b8',
                    lineWidth: 2,
                    endArrow: {
                        path: G6.Arrow.triangle(8, 10, 0),
                        fill: '#94a3b8'
                    }
                },
                labelCfg: {
                    autoRotate: true,
                    style: {
                        fill: '#64748b',
                        fontSize: 10,
                        background: {
                            fill: '#ffffff',
                            padding: [2, 4, 2, 4],
                            radius: 2
                        }
                    }
                }
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());
    }

    handleResize() {
        if (!this.graph) return;

        const container = document.getElementById(this.containerId);
        const width = container.offsetWidth;
        const height = container.offsetHeight;

        this.graph.changeSize(width, height);
        this.graph.fitView(40);
    }

    setModels(modelsData) {
        console.log('DEBUG [GRAPH]: setModels called with:', modelsData);
        this.models = modelsData;
        this.visitCounts = {};
        this.currentStepId = null;
        this.failedStepId = null;
        this.renderGraph();
    }

    renderGraph() {
        console.log('DEBUG [GRAPH]: renderGraph called');
        console.log('DEBUG [GRAPH]: this.graph exists:', !!this.graph);
        console.log('DEBUG [GRAPH]: this.models:', this.models);
        console.log('DEBUG [GRAPH]: this.models.length:', this.models ? this.models.length : 0);

        if (!this.graph || !this.models || this.models.length === 0) {
            console.warn('DEBUG [GRAPH]: Cannot render - missing graph or models');
            return;
        }

        const graphData = this.convertModelsToG6Data(this.models);
        console.log('DEBUG [GRAPH]: Converted graph data:', graphData);
        console.log('DEBUG [GRAPH]: Nodes count:', graphData.nodes.length);
        console.log('DEBUG [GRAPH]: Edges count:', graphData.edges.length);

        this.graph.data(graphData);
        this.graph.render();
        this.graph.fitView(40);
        console.log('DEBUG [GRAPH]: Graph rendered successfully');
    }

    convertModelsToG6Data(models) {
        console.log('DEBUG [GRAPH]: convertModelsToG6Data called with:', models);
        const nodes = [];
        const edges = [];

        models.forEach((model, index) => {
            console.log(`DEBUG [GRAPH]: Processing model ${index}:`, model);
            console.log(`DEBUG [GRAPH]: model.name:`, model.name);
            console.log(`DEBUG [GRAPH]: model.models:`, model.models);
            console.log(`DEBUG [GRAPH]: model keys:`, Object.keys(model));

            const modelName = model.name || 'default';

            // Handle nested models structure
            const actualModels = model.models || [model];
            console.log(`DEBUG [GRAPH]: Processing ${actualModels.length} actual model(s)`);

            actualModels.forEach((actualModel, subIndex) => {
                console.log(`DEBUG [GRAPH]: Processing sub-model ${subIndex}:`, actualModel);
                console.log(`DEBUG [GRAPH]: actualModel.vertices:`, actualModel.vertices);
                console.log(`DEBUG [GRAPH]: actualModel.edges:`, actualModel.edges);

                // Add vertices as nodes
                if (actualModel.vertices) {
                    console.log(`DEBUG [GRAPH]: Found ${actualModel.vertices.length} vertices`);
                    actualModel.vertices.forEach(vertex => {
                        // Use name as ID since GraphWalker doesn't provide currentElementID
                        nodes.push({
                            id: vertex.name || vertex.id,
                            label: vertex.name || vertex.id,
                            originalId: vertex.id,
                            modelName: modelName,
                            type: 'rect',
                            style: {
                                fill: '#ffffff',
                                stroke: '#5B8FF9'
                            }
                        });
                    });
                } else {
                    console.warn('DEBUG [GRAPH]: No vertices found in sub-model');
                }

                // Add edges
                if (actualModel.edges) {
                    console.log(`DEBUG [GRAPH]: Found ${actualModel.edges.length} edges`);
                    actualModel.edges.forEach(edge => {
                        // Use name as ID since GraphWalker doesn't provide currentElementID
                        // For source/target, we need to map vertex IDs to vertex names
                        const sourceVertex = actualModel.vertices?.find(v => v.id === edge.sourceVertexId);
                        const targetVertex = actualModel.vertices?.find(v => v.id === edge.targetVertexId);

                        edges.push({
                            id: edge.name || edge.id,
                            source: sourceVertex?.name || edge.sourceVertexId,
                            target: targetVertex?.name || edge.targetVertexId,
                            label: edge.name || '',
                            originalId: edge.id,
                            modelName: modelName
                        });
                    });
                } else {
                    console.warn('DEBUG [GRAPH]: No edges found in sub-model');
                }
            });
        });

        console.log('DEBUG [GRAPH]: Returning nodes:', nodes.length, nodes);
        console.log('DEBUG [GRAPH]: Returning edges:', edges.length, edges);
        return { nodes, edges };
    }

    updateStep(stepId) {
        // CRITICAL: Log BEFORE any checks to capture all calls
        console.log('ENTRY [GRAPH-UPDATE]: updateStep called', {
            stepId: stepId,
            stepIdType: typeof stepId,
            hasGraph: !!this.graph,
            graphType: typeof this.graph,
            graphConstructor: this.graph ? this.graph.constructor.name : 'N/A'
        });

        if (!this.graph) {
            console.error('EXIT [GRAPH-UPDATE]: No graph instance!');
            return;
        }

        if (!stepId) {
            console.error('EXIT [GRAPH-UPDATE]: No stepId provided!');
            return;
        }

        console.log('DEBUG [GRAPH-UPDATE]: Passed guard clauses, proceeding...');

        // Try to find the item by ID
        const item = this.graph.findById(stepId);
        console.log('DEBUG [GRAPH-UPDATE]: Found item by ID:', !!item);

        if (!item) {
            console.warn('DEBUG [GRAPH-UPDATE]: Could not find element with id:', stepId);
            console.warn('DEBUG [GRAPH-UPDATE]: Available nodes:', this.graph.getNodes().map(n => n.getID()));
            console.warn('DEBUG [GRAPH-UPDATE]: Available edges:', this.graph.getEdges().map(e => e.getID()));
            return;
        }

        // Remove highlight from previous step
        if (this.currentStepId) {
            console.log('DEBUG [GRAPH-UPDATE]: Removing highlight from previous step:', this.currentStepId);
            this.highlightElement(this.currentStepId, false);
        }

        // Increment visit count
        this.visitCounts[stepId] = (this.visitCounts[stepId] || 0) + 1;
        console.log('DEBUG [GRAPH-UPDATE]: Visit count for', stepId, ':', this.visitCounts[stepId]);

        // Update current step
        this.currentStepId = stepId;

        // Apply visit count color
        console.log('DEBUG [GRAPH-UPDATE]: Updating element color');
        this.updateElementColor(stepId);

        // Highlight current step
        console.log('DEBUG [GRAPH-UPDATE]: Highlighting current step');
        this.highlightElement(stepId, true);

        // Note: Removed focusItem() to prevent graph shaking/movement
    }

    updateElementColor(elementId) {
        const visitCount = this.visitCounts[elementId] || 0;
        const color = this.colorScale(visitCount);

        const item = this.graph.findById(elementId);
        if (!item) return;

        if (item.getType() === 'node') {
            this.graph.updateItem(elementId, {
                style: {
                    fill: color,
                    stroke: color
                }
            });
        } else if (item.getType() === 'edge') {
            this.graph.updateItem(elementId, {
                style: {
                    stroke: color,
                    endArrow: {
                        path: G6.Arrow.triangle(8, 10, 0),
                        fill: color
                    }
                }
            });
        }
    }

    highlightElement(elementId, highlight) {
        const item = this.graph.findById(elementId);
        if (!item) return;

        if (item.getType() === 'node') {
            this.graph.updateItem(elementId, {
                style: {
                    lineWidth: highlight ? 4 : 2,
                    shadowColor: highlight ? '#3b82f6' : undefined,
                    shadowBlur: highlight ? 10 : 0
                }
            });
        } else if (item.getType() === 'edge') {
            this.graph.updateItem(elementId, {
                style: {
                    lineWidth: highlight ? 4 : 2,
                    shadowColor: highlight ? '#3b82f6' : undefined,
                    shadowBlur: highlight ? 10 : 0
                }
            });
        }
    }

    markElementAsFailed(elementId) {
        this.failedStepId = elementId;

        const item = this.graph.findById(elementId);
        if (!item) return;

        if (item.getType() === 'node') {
            this.graph.updateItem(elementId, {
                style: {
                    fill: '#ef4444',
                    stroke: '#dc2626'
                }
            });
        } else if (item.getType() === 'edge') {
            this.graph.updateItem(elementId, {
                style: {
                    stroke: '#ef4444',
                    endArrow: {
                        path: G6.Arrow.triangle(8, 10, 0),
                        fill: '#ef4444'
                    }
                }
            });
        }
    }

    updateLayout(direction) {
        this.layoutDirection = direction;

        if (!this.graph) return;

        this.graph.updateLayout({
            type: 'dagre',
            rankdir: direction,
            nodesep: 50,
            ranksep: 70,
            controlPoints: true
        });

        setTimeout(() => {
            this.graph.fitView(40);
        }, 300);
    }

    clear() {
        if (this.graph) {
            this.graph.clear();
        }
        this.visitCounts = {};
        this.currentStepId = null;
        this.failedStepId = null;
    }

    destroy() {
        if (this.graph) {
            this.graph.destroy();
            this.graph = null;
        }
    }
}
