/**
 * UI Management for AltWalker2
 */

class UIManager {
    constructor() {
        this.elements = {
            // Overlays
            setupOverlay: document.getElementById('setup-overlay'),
            settingsOverlay: document.getElementById('settings-overlay'),

            // Setup form
            portInput: document.getElementById('port-input'),
            connectBtn: document.getElementById('connect-btn'),
            connectBtnText: document.getElementById('connect-btn-text'),
            connectBtnLoading: document.getElementById('connect-btn-loading'),
            errorAlert: document.getElementById('error-alert'),
            errorAlertText: document.getElementById('error-alert-text'),

            // Settings
            settingsBtn: document.getElementById('settings-btn'),
            saveSettingsBtn: document.getElementById('save-settings-btn'),
            closeSettingsBtn: document.getElementById('close-settings-btn'),
            layoutDirection: document.getElementById('layout-direction'),

            // Panels
            leftPanel: document.getElementById('left-panel'),
            rightPanel: document.getElementById('right-panel'),
            resizer: document.getElementById('resizer'),

            // Current step
            currentStepSection: document.getElementById('current-step-section'),
            stepName: document.getElementById('step-name'),
            stepId: document.getElementById('step-id'),
            stepModel: document.getElementById('step-model'),
            stepData: document.getElementById('step-data'),

            // Statistics
            statisticsSection: document.getElementById('statistics-section'),
            statsStatus: document.getElementById('stats-status'),
            statsModelsTotal: document.getElementById('stats-models-total'),
            statsModelsCompleted: document.getElementById('stats-models-completed'),
            statsModelsFailed: document.getElementById('stats-models-failed'),
            statsEdgeCoverage: document.getElementById('stats-edge-coverage'),
            statsEdgesVisited: document.getElementById('stats-edges-visited'),
            statsEdgesUnvisited: document.getElementById('stats-edges-unvisited'),
            statsVertexCoverage: document.getElementById('stats-vertex-coverage'),
            statsVerticesVisited: document.getElementById('stats-vertices-visited'),
            statsVerticesUnvisited: document.getElementById('stats-vertices-unvisited'),

            // Output
            outputText: document.getElementById('output-text'),
            autoScroll: document.getElementById('auto-scroll'),

            // Error
            errorMessage: document.getElementById('error-message'),
            errorTrace: document.getElementById('error-trace')
        };

        this.setupEventListeners();
        this.setupResizer();
    }

    setupEventListeners() {
        // Settings button
        this.elements.settingsBtn.addEventListener('click', () => {
            this.showSettings();
        });

        this.elements.saveSettingsBtn.addEventListener('click', () => {
            this.saveSettings();
        });

        this.elements.closeSettingsBtn.addEventListener('click', () => {
            this.hideSettings();
        });
    }

    setupResizer() {
        let isResizing = false;

        this.elements.resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;

            const containerWidth = window.innerWidth;
            const leftWidth = e.clientX;
            const rightWidth = containerWidth - leftWidth - 8; // 8px for resizer

            if (leftWidth > 300 && rightWidth > 300) {
                this.elements.leftPanel.style.width = `${leftWidth}px`;
                this.elements.rightPanel.style.width = `${rightWidth}px`;

                // Trigger graph resize
                window.dispatchEvent(new Event('resize'));
            }
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    showSetupOverlay() {
        this.elements.setupOverlay.classList.remove('hidden');
    }

    hideSetupOverlay() {
        this.elements.setupOverlay.classList.add('hidden');
        this.hideError();
    }

    showSettings() {
        this.elements.settingsOverlay.classList.remove('hidden');
    }

    hideSettings() {
        this.elements.settingsOverlay.classList.add('hidden');
    }

    saveSettings() {
        const direction = this.elements.layoutDirection.value;
        if (window.graphVisualizer) {
            window.graphVisualizer.updateLayout(direction);
        }
        this.hideSettings();
    }

    showError(message) {
        this.elements.errorAlertText.textContent = message;
        this.elements.errorAlert.classList.remove('hidden');
    }

    hideError() {
        this.elements.errorAlert.classList.add('hidden');
    }

    showConnecting() {
        this.elements.connectBtnText.classList.add('hidden');
        this.elements.connectBtnLoading.classList.remove('hidden');
        this.elements.connectBtn.disabled = true;
    }

    hideConnecting() {
        this.elements.connectBtnText.classList.remove('hidden');
        this.elements.connectBtnLoading.classList.add('hidden');
        this.elements.connectBtn.disabled = false;
    }

    showCurrentStepSection() {
        this.elements.currentStepSection.classList.remove('hidden');
    }

    hideCurrentStepSection() {
        this.elements.currentStepSection.classList.add('hidden');
    }

    showStatisticsSection() {
        this.elements.statisticsSection.classList.remove('hidden');
    }

    hideStatisticsSection() {
        this.elements.statisticsSection.classList.add('hidden');
    }

    updateStepInfo(step) {
        this.elements.stepName.value = step.name || '';
        this.elements.stepId.value = step.id || '';
        this.elements.stepModel.value = step.modelName || '';
        this.elements.stepData.value = step.data ? JSON.stringify(step.data, null, 2) : '{}';
    }

    appendOutput(text) {
        this.elements.outputText.value += text + '\n';

        if (this.elements.autoScroll.checked) {
            this.elements.outputText.scrollTop = this.elements.outputText.scrollHeight;
        }
    }

    clearOutput() {
        this.elements.outputText.value = '';
    }

    updateError(message, trace) {
        this.elements.errorMessage.value = message || '';
        this.elements.errorTrace.value = trace || '';
    }

    clearError() {
        this.elements.errorMessage.value = '';
        this.elements.errorTrace.value = '';
    }

    updateStatistics(statistics) {
        // Status
        const status = statistics.status;
        if (status !== undefined) {
            this.elements.statsStatus.textContent = status ? 'Passed' : 'Failed';
            this.elements.statsStatus.className = 'px-3 py-1 rounded-full text-sm font-medium ' +
                (status ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800');
        }

        // Models
        this.elements.statsModelsTotal.textContent = statistics.totalNumberOfModels || 0;
        this.elements.statsModelsCompleted.textContent = statistics.totalCompletedNumberOfModels || 0;
        this.elements.statsModelsFailed.textContent = statistics.totalFailedNumberOfModels || 0;

        // Edges
        const edgeCoverage = statistics.edgeCoverage || 0;
        this.elements.statsEdgeCoverage.textContent = `${edgeCoverage}%`;
        this.elements.statsEdgeCoverage.className = 'px-2 py-1 rounded text-xs font-medium ' +
            this.getCoverageClass(edgeCoverage);
        this.elements.statsEdgesVisited.textContent = statistics.totalNumberOfVisitedEdges || 0;
        this.elements.statsEdgesUnvisited.textContent = statistics.totalNumberOfUnvisitedEdges || 0;

        // Vertices
        const vertexCoverage = statistics.vertexCoverage || 0;
        this.elements.statsVertexCoverage.textContent = `${vertexCoverage}%`;
        this.elements.statsVertexCoverage.className = 'px-2 py-1 rounded text-xs font-medium ' +
            this.getCoverageClass(vertexCoverage);
        this.elements.statsVerticesVisited.textContent = statistics.totalNumberOfVisitedVertices || 0;
        this.elements.statsVerticesUnvisited.textContent = statistics.totalNumberOfUnvisitedVertices || 0;
    }

    getCoverageClass(percentage) {
        if (percentage >= 80) {
            return 'bg-green-100 text-green-800';
        } else if (percentage >= 50) {
            return 'bg-yellow-100 text-yellow-800';
        } else {
            return 'bg-red-100 text-red-800';
        }
    }

    getPort() {
        return parseInt(this.elements.portInput.value) || 5555;
    }
}
