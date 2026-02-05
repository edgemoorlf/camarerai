// CamareraI - Always-Listening Voice Agent
// Minimal UI with auto-respond and barge-in support

class VoiceAgent {
    constructor() {
        this.sessionId = null;
        this.socket = null;
        this.isRecording = false;
        this.isSpeaking = false;
        this.mediaRecorder = null;
        this.audioContext = null;
        this.audioWorklet = null;
        this.currentOrder = [];
        this.audioPlayer = null;
        this.shouldResetAfterResponse = false;

        this.init();
    }

    async init() {
        // Connect to WebSocket server
        await this.connectWebSocket();

        // Set up event listeners
        this.setupEventListeners();

        // Don't auto-start - wait for user interaction
        console.log('Ready. Waiting for user to tap "Touch to Order" button...');
    }

    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            this.socket = io('http://localhost:5002', {
                transports: ['polling', 'websocket']
            });

            this.socket.on('connect', () => {
                console.log('✓ WebSocket connected');
                this.setupSocketListeners();
                this.createSession();
                resolve();
            });

            this.socket.on('connect_error', (error) => {
                console.error('WebSocket connection error:', error);
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
        });

        // Partial transcription (streaming)
        this.socket.on('transcription_partial', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Partial transcription:', data.text);
                document.getElementById('debug-transcript').textContent = data.text;
            }
        });

        // Transcription complete - auto-respond
        this.socket.on('transcription_complete', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Transcription complete:', data.text);
                const finalText = data.text;

                if (finalText && finalText.trim()) {
                    // Update debug
                    document.getElementById('debug-transcript').textContent = finalText;

                    // Check for closing remarks
                    if (this.isClosingRemark(finalText)) {
                        console.log('Closing remark detected - will reset after AI response');
                        this.shouldResetAfterResponse = true;
                    }

                    // Auto-send to LLM
                    this.updateStatus('thinking', '⋯', 'Thinking');
                    this.socket.emit('chat', {
                        session_id: this.sessionId,
                        message: finalText
                    });
                }
            }
        });

        // Transcription error
        this.socket.on('transcription_error', (data) => {
            console.error('Transcription error:', data.error);
            this.updateStatus('listening', '◉', 'Listening');
        });

        // Recognition stopped
        this.socket.on('recognition_stopped', (data) => {
            console.log('Recognition stopped');
        });

        // Chat response - auto-speak
        this.socket.on('chat_response', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Chat response:', data.response);
                document.getElementById('debug-response').textContent = data.response;

                // Auto-synthesize speech
                this.updateStatus('speaking', '🗣️', 'Speaking');
                this.isSpeaking = true;
                this.synthesizeSpeech(data.response);
            }
        });

        // Order updated
        this.socket.on('order_updated', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Order updated:', data);

                // Update current order
                this.currentOrder = data.order || [];

                // Update order display with totals
                this.updateOrderDisplay(data.subtotal, data.tax, data.total);

                // Log action
                console.log(`Order ${data.action}: ${this.currentOrder.length} items, Total: $${data.total}`);
            }
        });

        // Synthesis complete - auto-play
        this.socket.on('synthesis_complete', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Synthesis complete:', data.audio_url);
                this.playAudio(data.audio_url);
            }
        });

        // Error
        this.socket.on('error', (data) => {
            console.error('Server error:', data.message);
            this.updateStatus('listening', '◉', 'Listening');
        });
    }

    createSession() {
        this.socket.emit('create_session', {
            table_id: '1',
            role: 'customer'
        });
    }

    setupEventListeners() {
        // Start Order button
        const startOrderBtn = document.getElementById('start-order-btn');
        if (startOrderBtn) {
            startOrderBtn.addEventListener('click', () => this.handleStartOrder());
        }

        // Debug panel toggle
        const showDebugBtn = document.getElementById('show-debug');
        const debugPanel = document.getElementById('debug-panel');
        const closeDebugBtn = document.getElementById('close-debug');

        showDebugBtn.addEventListener('click', () => {
            debugPanel.classList.remove('hidden');
            showDebugBtn.classList.add('hidden');
        });

        closeDebugBtn.addEventListener('click', () => {
            debugPanel.classList.add('hidden');
            showDebugBtn.classList.remove('hidden');
        });

        // Send order button
        const sendOrderBtn = document.getElementById('send-order-btn');
        sendOrderBtn.addEventListener('click', () => this.sendOrder());

        // Monitor for barge-in during speech
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.isSpeaking) {
                this.handleBargeIn();
            }
        });
    }

    async handleStartOrder() {
        console.log('User tapped "Touch to Order" - starting microphone...');

        // Hide start button
        const startButtonArea = document.getElementById('start-button-area');
        startButtonArea.classList.add('hidden');

        // Show status area
        const statusArea = document.getElementById('status-area');
        statusArea.classList.remove('hidden');

        // Update status
        this.updateStatus('listening', '◉', 'Listening');

        // Start recording (now with user gesture)
        await this.startRecording();
    }

    async startRecording() {
        if (this.isRecording) return;

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

                // Check for barge-in during speaking
                if (this.isSpeaking) {
                    const volume = this.calculateVolume(inputData);
                    if (volume > 0.02) { // Voice detected threshold
                        this.handleBargeIn();
                    }
                }
            };

            source.connect(processor);
            processor.connect(this.audioContext.destination);

            this.audioWorklet = { source, processor, stream };
            this.isRecording = true;

            // Start recognition on server
            this.socket.emit('start_recognition', {
                session_id: this.sessionId
            });

            console.log('✓ Always-listening mode active');

        } catch (error) {
            console.error('Failed to start recording:', error);
            alert('Microphone access denied. Please allow microphone access and refresh the page.');
        }
    }

    calculateVolume(audioData) {
        let sum = 0;
        for (let i = 0; i < audioData.length; i++) {
            sum += audioData[i] * audioData[i];
        }
        return Math.sqrt(sum / audioData.length);
    }

    handleBargeIn() {
        if (!this.isSpeaking) return;

        console.log('Barge-in detected - stopping speech');

        // Stop audio playback immediately
        if (this.audioPlayer) {
            this.audioPlayer.pause();
            this.audioPlayer.currentTime = 0;
        }

        this.isSpeaking = false;
        this.updateStatus('listening', '◉', 'Listening');

        // Notify server to cancel any pending TTS
        this.socket.emit('interrupt', {
            session_id: this.sessionId
        });
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

    synthesizeSpeech(text) {
        this.socket.emit('synthesize', {
            session_id: this.sessionId,
            text: text
        });
    }

    playAudio(audioUrl) {
        this.audioPlayer = document.getElementById('audio-player');
        this.audioPlayer.src = audioUrl;

        this.audioPlayer.onended = () => {
            this.isSpeaking = false;

            // Check if we should reset to "Touch to Order"
            if (this.shouldResetAfterResponse) {
                console.log('Closing remark detected - resetting to "Touch to Order"');
                this.resetToStartScreen();
            } else {
                this.updateStatus('listening', '◉', 'Listening');
            }
        };

        this.audioPlayer.onerror = () => {
            console.warn('Audio playback failed');
            this.isSpeaking = false;

            if (this.shouldResetAfterResponse) {
                this.resetToStartScreen();
            } else {
                this.updateStatus('listening', '◉', 'Listening');
            }
        };

        this.audioPlayer.play().catch(err => {
            console.warn('Audio play error:', err);
            this.isSpeaking = false;

            if (this.shouldResetAfterResponse) {
                this.resetToStartScreen();
            } else {
                this.updateStatus('listening', '◉', 'Listening');
            }
        });
    }

    updateStatus(state, icon, text) {
        const statusIcon = document.getElementById('status-icon');
        const statusText = document.getElementById('status-text');

        statusIcon.textContent = icon;
        statusText.textContent = text;

        // Update icon class for animations
        statusIcon.className = 'status-icon ' + state;
    }

    updateOrderDisplay(subtotal, tax, total) {
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

        // Calculate totals if not provided
        if (subtotal === undefined) {
            subtotal = this.currentOrder.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            tax = subtotal * 0.09;
            total = subtotal + tax;
        }

        // Update item count
        const totalItems = this.currentOrder.reduce((sum, item) => sum + item.quantity, 0);
        itemCount.textContent = `${totalItems} item${totalItems > 1 ? 's' : ''}`;

        // Update totals
        subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
        taxEl.textContent = `$${tax.toFixed(2)}`;
        totalEl.textContent = `$${total.toFixed(2)}`;
        sendOrderBtn.disabled = false;

        // Build order items HTML
        orderItems.innerHTML = this.currentOrder.map(item => `
            <div class="order-item">
                <div class="item-details">
                    <span class="item-name">${this.escapeHtml(item.name)}</span>
                    ${item.quantity > 1 ? `<span class="item-quantity">x${item.quantity}</span>` : ''}
                    ${item.modifications && item.modifications.length > 0 ?
                        `<span class="item-mods">${item.modifications.map(m => this.escapeHtml(m)).join(', ')}</span>`
                        : ''}
                </div>
                <span class="item-price">$${(item.price * item.quantity).toFixed(2)}</span>
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

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    isClosingRemark(text) {
        // Normalize text for comparison
        const normalized = text.toLowerCase().trim();

        // English closing remarks
        const englishClosing = [
            'thank you',
            'thanks',
            'that\'s all',
            'that is all',
            'that\'ll be all',
            'that will be all',
            'please go ahead',
            'go ahead',
            'send the order',
            'place the order',
            'that\'s it',
            'that is it',
            'we\'re done',
            'we are done',
            'i\'m done',
            'i am done',
            'perfect',
            'sounds good',
            'looks good',
            'all set'
        ];

        // Chinese closing remarks (Mandarin)
        const chineseClosing = [
            '谢谢',
            '谢了',
            '好的',
            '可以了',
            '就这些',
            '就这样',
            '没了',
            '够了',
            '行了',
            '下单吧',
            '确认',
            '确定'
        ];

        // Cantonese closing remarks
        const cantoneseClosing = [
            '唔該',
            '多謝',
            '得啦',
            '可以啦',
            '就咁多',
            '冇啦',
            '夠啦',
            '落單啦'
        ];

        // Check if text contains any closing remark
        const allClosingRemarks = [...englishClosing, ...chineseClosing, ...cantoneseClosing];

        return allClosingRemarks.some(phrase => normalized.includes(phrase));
    }

    resetToStartScreen() {
        console.log('Resetting to start screen...');

        // Stop recording
        this.stopRecording();

        // Reset flag
        this.shouldResetAfterResponse = false;

        // Clear current order
        this.currentOrder = [];
        this.updateOrderDisplay();

        // Hide status area
        const statusArea = document.getElementById('status-area');
        statusArea.classList.add('hidden');

        // Show start button
        const startButtonArea = document.getElementById('start-button-area');
        startButtonArea.classList.remove('hidden');

        console.log('Ready for next customer. Tap "Touch to Order" to start.');
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

        console.log('Recording stopped');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.voiceAgent = new VoiceAgent();

    console.log('%c🎤 Always-Listening Voice Agent Active', 'color: #06c; font-size: 14px; font-weight: bold;');
    console.log('%c💡 Speak naturally - AI responds automatically', 'color: #06c; font-size: 12px;');
    console.log('%c🔇 Press SPACE or speak to interrupt AI', 'color: #06c; font-size: 12px;');
});
