// CamareraI - Streaming Voice Recognition Client
// WebSocket-based real-time ASR with DashScope

class StreamingVoiceAgent {
    constructor() {
        this.sessionId = null;
        this.socket = null;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioContext = null;
        this.audioWorklet = null;
        this.currentOrder = [];
        this.transcriptionBuffer = "";

        this.init();
    }

    async init() {
        // Connect to WebSocket server
        await this.connectWebSocket();

        // Set up event listeners
        this.setupEventListeners();

        // Update UI
        this.updateStatus('sleeping', '💤', 'Ready');
    }

    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            // Connect to Socket.IO server
            this.socket = io('http://localhost:5002', {
                transports: ['websocket', 'polling']
            });

            this.socket.on('connect', () => {
                console.log('✓ WebSocket connected');
                this.setupSocketListeners();
                this.createSession();
                resolve();
            });

            this.socket.on('connect_error', (error) => {
                console.error('WebSocket connection error:', error);
                this.showError('Failed to connect to server. Please refresh the page.');
                reject(error);
            });

            this.socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                this.updateStatus('disconnected', '⚠️', 'Disconnected');
            });
        });
    }

    setupSocketListeners() {
        // Session created
        this.socket.on('session_created', (data) => {
            this.sessionId = data.session_id;
            document.getElementById('table-name').textContent = data.table_name;
            document.getElementById('debug-session').textContent = this.sessionId;
            console.log('Session created:', data);
        });

        // Recognition started
        this.socket.on('recognition_started', (data) => {
            console.log('Recognition started');
            this.transcriptionBuffer = "";
        });

        // Partial transcription (streaming)
        this.socket.on('transcription_partial', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Partial transcription:', data.text);
                this.transcriptionBuffer = data.text;

                // Update UI with partial result
                this.updateTranscriptionPreview(data.text);

                // Update debug info
                document.getElementById('debug-transcript').textContent = data.text;
            }
        });

        // Transcription complete
        this.socket.on('transcription_complete', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Transcription complete:', data.text);
                const finalText = data.text || this.transcriptionBuffer;

                if (finalText && finalText.trim()) {
                    this.handleTranscriptionComplete(finalText);
                }
            }
        });

        // Transcription error
        this.socket.on('transcription_error', (data) => {
            console.error('Transcription error:', data.error);
            this.showError('Transcription failed. Please try again.');
            this.updateStatus('sleeping', '💤', 'Ready');
        });

        // Recognition stopped
        this.socket.on('recognition_stopped', (data) => {
            console.log('Recognition stopped');
        });

        // Chat response
        this.socket.on('chat_response', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Chat response:', data.response);

                // Update debug info
                document.getElementById('debug-response').textContent = data.response;

                // Add assistant message
                this.addMessage('assistant', data.response);

                // Synthesize speech
                this.updateStatus('speaking', '🗣️', 'Speaking...');
                this.synthesizeSpeech(data.response);
            }
        });

        // Synthesis complete
        this.socket.on('synthesis_complete', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Synthesis complete:', data.audio_url);
                this.playAudio(data.audio_url);
            }
        });

        // Error
        this.socket.on('error', (data) => {
            console.error('Server error:', data.message);
            this.showError(data.message);
        });
    }

    createSession() {
        this.socket.emit('create_session', {
            table_id: '1',
            role: 'customer'
        });
    }

    setupEventListeners() {
        // Talk button
        const talkBtn = document.getElementById('talk-btn');
        talkBtn.addEventListener('click', () => this.toggleRecording());

        // Text input fallback
        const conversationHistory = document.getElementById('conversation-history');
        conversationHistory.addEventListener('dblclick', () => {
            this.showTextInput();
        });

        // Debug toggle
        const debugToggle = document.getElementById('toggle-debug');
        const debugContent = document.getElementById('debug-content');
        debugToggle.addEventListener('click', () => {
            debugContent.classList.toggle('hidden');
        });

        // Send order button
        const sendOrderBtn = document.getElementById('send-order-btn');
        sendOrderBtn.addEventListener('click', () => this.sendOrder());
    }

    showTextInput() {
        const text = prompt('Enter your message (text input fallback):');
        if (text && text.trim()) {
            this.processTextMessage(text.trim());
        }
    }

    async processTextMessage(text) {
        try {
            // Add user message
            this.addMessage('user', text);
            document.getElementById('debug-transcript').textContent = text;

            // Send to server
            this.updateStatus('thinking', '🤔', 'Thinking...');
            this.socket.emit('chat', {
                session_id: this.sessionId,
                message: text
            });

        } catch (error) {
            console.error('Error processing text:', error);
            this.showError('Failed to process message. Please try again.');
            this.updateStatus('sleeping', '💤', 'Ready');
        }
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            // Get microphone access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });

            const source = this.audioContext.createMediaStreamSource(stream);

            // Create script processor for audio data
            const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (e) => {
                if (!this.isRecording) return;

                const inputData = e.inputBuffer.getChannelData(0);

                // Convert Float32Array to Int16Array (PCM)
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                // Convert to base64 and send
                const base64Audio = this.arrayBufferToBase64(pcmData.buffer);
                this.socket.emit('audio_data', {
                    audio: base64Audio
                });
            };

            source.connect(processor);
            processor.connect(this.audioContext.destination);

            this.audioWorklet = { source, processor, stream };
            this.isRecording = true;

            // Start recognition on server
            this.socket.emit('start_recognition', {
                session_id: this.sessionId
            });

            // Update UI
            this.updateStatus('listening', '👂', 'Listening...');
            document.getElementById('talk-btn').classList.add('recording');
            document.querySelector('.btn-text').textContent = 'Tap to Stop';
            document.getElementById('recording-indicator').classList.remove('hidden');

        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showError('Microphone access denied. Double-click conversation area to use text input instead.');
        }
    }

    stopRecording() {
        if (!this.isRecording) return;

        this.isRecording = false;

        // Stop audio processing
        if (this.audioWorklet) {
            this.audioWorklet.processor.disconnect();
            this.audioWorklet.source.disconnect();
            this.audioWorklet.stream.getTracks().forEach(track => track.stop());
            this.audioWorklet = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        // Stop recognition on server
        this.socket.emit('stop_recognition', {
            session_id: this.sessionId
        });

        // Update UI
        this.updateStatus('processing', '⚙️', 'Processing...');
        document.getElementById('talk-btn').classList.remove('recording');
        document.querySelector('.btn-text').textContent = 'Tap to Talk';
        document.getElementById('recording-indicator').classList.add('hidden');
    }

    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    updateTranscriptionPreview(text) {
        // Show partial transcription in a preview area
        const preview = document.getElementById('transcription-preview');
        if (preview) {
            preview.textContent = text;
            preview.style.display = 'block';
        }
    }

    handleTranscriptionComplete(text) {
        // Hide preview
        const preview = document.getElementById('transcription-preview');
        if (preview) {
            preview.style.display = 'none';
        }

        // Add user message
        this.addMessage('user', text);

        // Send to chat
        this.updateStatus('thinking', '🤔', 'Thinking...');
        this.socket.emit('chat', {
            session_id: this.sessionId,
            message: text
        });
    }

    synthesizeSpeech(text) {
        this.socket.emit('synthesize', {
            session_id: this.sessionId,
            text: text
        });
    }

    playAudio(audioUrl) {
        const audioPlayer = document.getElementById('audio-player');
        audioPlayer.src = audioUrl;

        audioPlayer.onended = () => {
            this.updateStatus('sleeping', '💤', 'Ready');
        };

        audioPlayer.onerror = () => {
            console.warn('Audio playback failed');
            this.updateStatus('sleeping', '💤', 'Ready');
        };

        audioPlayer.play().catch(err => {
            console.warn('Audio play error:', err);
            this.updateStatus('sleeping', '💤', 'Ready');
        });
    }

    addMessage(role, content) {
        const conversationHistory = document.getElementById('conversation-history');

        // Remove welcome message
        const welcomeMessage = conversationHistory.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const roleLabel = role === 'user' ? 'You' : 'Lily';
        messageDiv.innerHTML = `
            <div class="message-role">${roleLabel}</div>
            <div class="message-content">${this.escapeHtml(content)}</div>
        `;

        conversationHistory.appendChild(messageDiv);
        conversationHistory.scrollTop = conversationHistory.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    updateStatus(state, icon, text) {
        document.getElementById('status-icon').textContent = icon;
        document.getElementById('status-text').textContent = text;
    }

    showError(message) {
        const conversationHistory = document.getElementById('conversation-history');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message assistant';
        errorDiv.innerHTML = `
            <div class="message-role">System</div>
            <div class="message-content" style="color: #e53e3e;">⚠️ ${this.escapeHtml(message)}</div>
        `;
        conversationHistory.appendChild(errorDiv);
        conversationHistory.scrollTop = conversationHistory.scrollHeight;
    }

    updateOrderDisplay() {
        const orderItems = document.getElementById('order-items');
        const itemCount = document.getElementById('item-count');
        const subtotalEl = document.getElementById('subtotal');
        const taxEl = document.getElementById('tax');
        const totalEl = document.getElementById('total');
        const sendOrderBtn = document.getElementById('send-order-btn');

        if (this.currentOrder.length === 0) {
            orderItems.innerHTML = '<p class="empty-state">No items yet</p>';
            itemCount.textContent = '0 items';
            subtotalEl.textContent = '$0.00';
            taxEl.textContent = '$0.00';
            totalEl.textContent = '$0.00';
            sendOrderBtn.disabled = true;
            return;
        }

        const subtotal = this.currentOrder.reduce((sum, item) => sum + item.price, 0);
        const tax = subtotal * 0.09;
        const total = subtotal + tax;

        itemCount.textContent = `${this.currentOrder.length} item${this.currentOrder.length > 1 ? 's' : ''}`;
        subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
        taxEl.textContent = `$${tax.toFixed(2)}`;
        totalEl.textContent = `$${total.toFixed(2)}`;
        sendOrderBtn.disabled = false;

        orderItems.innerHTML = this.currentOrder.map(item => `
            <div class="order-item">
                <span class="item-name">${this.escapeHtml(item.name)}</span>
                <span class="item-price">$${item.price.toFixed(2)}</span>
            </div>
        `).join('');
    }

    addOrderItem(name, price) {
        this.currentOrder.push({ name, price });
        this.updateOrderDisplay();
    }

    async sendOrder() {
        console.log('Sending order:', this.currentOrder);
        alert('Order sent to kitchen! (Demo only)');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.voiceAgent = new StreamingVoiceAgent();

    console.log('%c🎤 Streaming Voice Recognition Enabled', 'color: #667eea; font-size: 14px; font-weight: bold;');
    console.log('%c💡 Tip: Double-click conversation area for text input fallback', 'color: #667eea; font-size: 12px;');
});
