/**
 * Main Application Entry Point
 */

// Initialize global instances
window.graphVisualizer = new GraphVisualizer('graph-container');
const wsClient = new WebSocketClient();
const uiManager = new UIManager();

// Application state
let isRunning = false;

// Initialize application
function init() {
    console.log('Initializing AltWalker2 Live Viewer...');

    // Initialize graph visualizer
    graphVisualizer.initialize();

    // Setup WebSocket message handlers
    setupWebSocketHandlers();

    // Setup connect button
    uiManager.elements.connectBtn.addEventListener('click', handleConnect);
}

// Setup WebSocket message handlers
function setupWebSocketHandlers() {
    wsClient.on('start', handleStartMessage);
    wsClient.on('step-start', handleStepStartMessage);
    wsClient.on('step-end', handleStepEndMessage);
    wsClient.on('end', handleEndMessage);
    wsClient.on('error', handleErrorMessage);
}

// Handle connection
async function handleConnect() {
    console.log('DEBUG [CONNECT]: handleConnect() called');
    const port = uiManager.getPort();
    console.log('DEBUG [CONNECT]: Port:', port);

    uiManager.showConnecting();
    uiManager.hideError();

    try {
        console.log('DEBUG [CONNECT]: Attempting WebSocket connection...');
        await wsClient.connect(port);
        console.log('DEBUG [CONNECT]: WebSocket connected successfully');

        // Connection successful - now start the test execution
        console.log('DEBUG [CONNECT]: About to call /api/start-test');
        const requestBody = {
            test_package: '../example/tests',
            // models: [['../example/models/default.json', 'a_star(edge_coverage(100))']],
            models: [['../example/models/default.json', 'random(edge_coverage(100))']],
            gw_port: 8888,
            host: 'localhost',
            port: port
        };
        console.log('DEBUG [CONNECT]: Request body:', JSON.stringify(requestBody));

        const response = await fetch('/api/start-test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        console.log('DEBUG [CONNECT]: Got response from /api/start-test, status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('DEBUG [CONNECT]: API error response:', errorText);
            throw new Error('Failed to start test execution: ' + errorText);
        }

        const result = await response.json();
        console.log('DEBUG [CONNECT]: Test execution started successfully:', result);

        // Keep overlay visible until test starts
        uiManager.hideConnecting();

    } catch (error) {
        console.error('DEBUG [CONNECT]: Error occurred:', error);
        console.error('DEBUG [CONNECT]: Error stack:', error.stack);
        uiManager.hideConnecting();
        uiManager.showError(error.message || 'Failed to connect to server');
    }
}

// Handle start message
function handleStartMessage(message) {
    console.log('DEBUG [MAIN]: Test run started', message);
    console.log('DEBUG [MAIN]: Models data:', message.models);
    console.log('DEBUG [MAIN]: Models count:', message.models ? message.models.length : 0);

    // Hide setup overlay
    console.log('DEBUG [MAIN]: Hiding setup overlay');
    uiManager.hideSetupOverlay();

    // Clear previous run data
    uiManager.clearOutput();
    uiManager.clearError();

    // Show current step section
    uiManager.showCurrentStepSection();
    uiManager.hideStatisticsSection();

    // Load models into graph
    if (message.models && message.models.length > 0) {
        console.log('DEBUG [MAIN]: Loading', message.models.length, 'models into graph');
        console.log('DEBUG [MAIN]: graphVisualizer object:', graphVisualizer);
        console.log('DEBUG [MAIN]: graphVisualizer.setModels exists:', typeof graphVisualizer.setModels);
        console.log('DEBUG [MAIN]: window.graphVisualizer:', window.graphVisualizer);
        console.log('DEBUG [MAIN]: window.graphVisualizer === graphVisualizer:', window.graphVisualizer === graphVisualizer);

        try {
            graphVisualizer.setModels(message.models);
            console.log('DEBUG [MAIN]: setModels() called successfully');
        } catch (error) {
            console.error('DEBUG [MAIN]: Error calling setModels():', error);
        }
    } else {
        console.warn('DEBUG [MAIN]: No models to load!');
    }

    isRunning = true;
    console.log('DEBUG [MAIN]: Start message handling complete');
}

// Handle step start message
function handleStepStartMessage(message) {
    console.log('DEBUG [STEP-START]: Step started', message.step);
    console.log('DEBUG [STEP-START]: Full message:', JSON.stringify(message));

    const step = message.step;
    console.log('DEBUG [STEP-START]: step.id =', step.id);
    console.log('DEBUG [STEP-START]: step.name =', step.name);
    console.log('DEBUG [STEP-START]: step.modelName =', step.modelName);

    // Update UI with step information
    uiManager.updateStepInfo(step);

    // Update graph visualization
    if (step.id) {
        console.log('DEBUG [STEP-START]: Calling graphVisualizer.updateStep with id:', step.id);
        graphVisualizer.updateStep(step.id);
    } else {
        console.warn('DEBUG [STEP-START]: step.id is null/undefined, cannot update graph');
        console.warn('DEBUG [STEP-START]: Trying with step.name instead:', step.name);
        // Try using name as fallback
        if (step.name) {
            console.log('DEBUG [STEP-START]: About to call graphVisualizer.updateStep with name:', step.name);
            console.log('DEBUG [STEP-START]: graphVisualizer object:', graphVisualizer);
            console.log('DEBUG [STEP-START]: graphVisualizer.updateStep:', graphVisualizer.updateStep);
            try {
                graphVisualizer.updateStep(step.name);
                console.log('DEBUG [STEP-START]: graphVisualizer.updateStep called successfully');
            } catch (error) {
                console.error('DEBUG [STEP-START]: Error calling updateStep:', error);
                console.error('DEBUG [STEP-START]: Error stack:', error.stack);
            }
        } else {
            console.error('DEBUG [STEP-START]: step.name is also null/undefined!');
        }
    }
}

// Handle step end message
function handleStepEndMessage(message) {
    console.log('Step ended', message.result);

    const result = message.result;

    // Append output
    if (result.output) {
        uiManager.appendOutput(result.output);
    }

    // Handle errors
    if (result.error) {
        const errorMsg = result.error.message || 'Unknown error';
        const errorTrace = result.error.trace || '';

        uiManager.updateError(errorMsg, errorTrace);

        // Mark element as failed in graph
        if (result.id) {
            graphVisualizer.markElementAsFailed(result.id);
        }
    }
}

// Handle end message
function handleEndMessage(message) {
    console.log('Test run ended', message);

    // Hide current step section
    uiManager.hideCurrentStepSection();

    // Show statistics section
    uiManager.showStatisticsSection();

    // Update statistics
    if (message.statistics) {
        const stats = {
            status: message.status,
            ...message.statistics
        };
        uiManager.updateStatistics(stats);
    } else {
        // If no statistics provided, just show status
        uiManager.updateStatistics({ status: message.status });
    }

    isRunning = false;

    // Append completion message
    uiManager.appendOutput('\n=== Test Execution Completed ===');
}

// Handle error message
function handleErrorMessage(message) {
    console.error('Error received', message);

    const errorMsg = message.message || 'Unknown error';
    const errorTrace = message.trace || '';

    uiManager.updateError(errorMsg, errorTrace);

    // Mark element as failed in graph
    if (message.step && message.step.id) {
        graphVisualizer.markElementAsFailed(message.step.id);
    }
}

// Start application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
