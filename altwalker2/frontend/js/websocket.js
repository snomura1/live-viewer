/**
 * WebSocket Client for AltWalker2
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.port = 5555;
        this.messageHandlers = {
            'start': null,
            'step-start': null,
            'step-end': null,
            'end': null,
            'error': null
        };
    }

    on(messageType, handler) {
        if (this.messageHandlers.hasOwnProperty(messageType)) {
            this.messageHandlers[messageType] = handler;
        }
    }

    async connect(port) {
        this.port = port;

        // Check if server is running
        try {
            const response = await fetch(`http://localhost:${port}/healthz`);
            if (!response.ok) {
                throw new Error('Server not responding');
            }
        } catch (error) {
            throw new Error('Unable to connect to server. Make sure the server is running.');
        }

        return new Promise((resolve, reject) => {
            try {
                const wsUrl = `ws://localhost:${port}/`;
                console.log('DEBUG: Attempting WebSocket connection to:', wsUrl);
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('DEBUG [CLIENT]: WebSocket connected successfully to:', wsUrl);
                    this.connected = true;

                    // Send initialization message
                    console.log('DEBUG [CLIENT]: Sending init message');
                    this.send({
                        type: 'init',
                        client: 'viewer'
                    });

                    // Send start acknowledgment
                    console.log('DEBUG [CLIENT]: Sending start message');
                    this.send({
                        type: 'start'
                    });

                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        console.log('DEBUG [CLIENT]: Received message:', message.type, message);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('Error parsing message:', error);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.connected = false;
                    reject(new Error('WebSocket connection error'));
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.connected = false;
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    handleMessage(message) {
        const type = message.type;
        const handler = this.messageHandlers[type];

        if (handler && typeof handler === 'function') {
            handler(message);
        } else {
            console.log('Unhandled message type:', type, message);
        }
    }

    send(message) {
        if (this.ws && this.connected) {
            console.log('DEBUG [CLIENT]: Sending message:', message.type, message);
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('DEBUG [CLIENT]: Cannot send message, not connected:', message);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.connected = false;
        }
    }

    isConnected() {
        return this.connected;
    }
}
