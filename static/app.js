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
        this.audioPlayer = null;

        // Session state management
        this.sessionState = 'idle';  // idle, enrolling, ordering, confirmed

        // Order management
        this.confirmedItems = [];    // Locked items after confirmation
        this.currentOrder = [];      // New items being added

        // Streaming audio playback
        this.audioStreamPlayer = null;
        this.streamingEnabled = true;  // Enable streaming by default

        // Client-side speaker verification
        this.speakerVerifier = new ClientSpeakerVerifier(0.75); // threshold
        this.enrollmentAudioBuffer = [];
        this.enrollmentDuration = 2.5; // seconds
        this.isEnrolling = false;

        this.init();
    }

    async init() {
        // Connect to WebSocket server
        await this.connectWebSocket();

        // Set up event listeners
        this.setupEventListeners();

        // Initialize performance monitor
        this.perfMonitor = new PerformanceMonitor();

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
            this.sessionState = data.state || 'idle';
            document.getElementById('table-name').textContent = data.table_name;
            document.getElementById('debug-session').textContent = this.sessionId;
            console.log('Session created:', data);
        });

        // State changed
        this.socket.on('state_changed', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('[Session] State changed:', data.state);
                this.sessionState = data.state;

                if (data.state === 'confirmed_passive') {
                    // Passive listening mode - capture but don't respond
                    console.log('[Session] Entered passive listening mode');

                    this.confirmedItems = data.confirmed_items || [];
                    this.currentOrder = [];
                    this.updateButton('confirmed');
                    this.updateOrderDisplay(data.subtotal, data.tax, data.total);

                    // Show status area (passive mode)
                    const statusArea = document.getElementById('status-area');
                    statusArea.classList.remove('hidden');
                    this.updateStatus('listening', '◉', 'Listening');

                    // Show start button
                    const startButtonArea = document.getElementById('start-button-area');
                    startButtonArea.classList.remove('hidden');

                    // Show stop listening button
                    const stopButton = document.getElementById('stop-listening-btn');
                    stopButton.classList.remove('hidden');

                    console.log('[Session] Passive mode: capturing speech without responding');

                } else if (data.state === 'confirmed_stopped') {
                    // Listening stopped
                    console.log('[Session] Passive listening stopped');

                    // Hide status area
                    const statusArea = document.getElementById('status-area');
                    statusArea.classList.add('hidden');

                    // Hide stop button
                    const stopButton = document.getElementById('stop-listening-btn');
                    stopButton.classList.add('hidden');

                    // Show start button
                    const startButtonArea = document.getElementById('start-button-area');
                    startButtonArea.classList.remove('hidden');

                } else if (data.state === 'confirmed') {
                    // Active conversation mode
                    console.log('[Session] Active conversation mode');

                    this.confirmedItems = data.confirmed_items || [];
                    this.currentOrder = [];
                    this.updateButton('confirmed');

                    if (data.subtotal !== undefined) {
                        this.updateOrderDisplay(data.subtotal, data.tax, data.total);
                    }

                    // Hide start button and stop button
                    const startButtonArea = document.getElementById('start-button-area');
                    startButtonArea.classList.add('hidden');

                    const stopButton = document.getElementById('stop-listening-btn');
                    stopButton.classList.add('hidden');

                    // Show status area
                    const statusArea = document.getElementById('status-area');
                    statusArea.classList.remove('hidden');
                    this.updateStatus('listening', '◉', 'Listening');

                } else if (data.state === 'ordering') {
                    this.updateButton('ordering');
                }
            }
        });

        // Session reset
        this.socket.on('session_reset', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('[Session] Reset:', data.message);
                this.resetToStartScreen();
            }
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

                    // Auto-send to LLM
                    this.updateStatus('thinking', '⋯', 'Thinking');
                    this.socket.emit('chat', {
                        session_id: this.sessionId,
                        message: finalText
                    });
                }
            }
        });

        // Passive transcription - captured but no response
        this.socket.on('transcription_passive', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('[Passive] Captured:', data.text);
                // Update debug to show captured text
                document.getElementById('debug-transcript').textContent = `[Passive] ${data.text}`;
                // No AI response - just capturing context
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

                // Update confirmed and current orders
                this.confirmedItems = data.confirmed_items || [];
                this.currentOrder = data.current_order || [];

                // Update order display with totals
                this.updateOrderDisplay(data.subtotal, data.tax, data.total);

                // Log action
                const totalItems = this.confirmedItems.length + this.currentOrder.length;
                console.log(`Order ${data.action}: ${totalItems} items (${this.confirmedItems.length} confirmed, ${this.currentOrder.length} new), Total: $${data.total}`);
            }
        });

        // TTS synthesis started (streaming mode)
        this.socket.on('synthesis_started', async (data) => {
            if (data.session_id === this.sessionId) {
                console.log('[TTS] Streaming synthesis started');
                this.isSpeaking = true;
                this.updateStatus('speaking', '🔊', 'Speaking');

                // Initialize streaming audio player if not already done
                if (!this.audioStreamPlayer) {
                    console.log('[Audio] Creating AudioStreamPlayer (fallback)');
                    this.audioStreamPlayer = new AudioStreamPlayer();
                    await this.audioStreamPlayer.init();
                    this.audioStreamPlayer.setOnEndCallback(() => {
                        console.log('[TTS] All audio chunks played');
                        this.isSpeaking = false;
                        this.updateStatus('listening', '◉', 'Listening');
                    });
                } else {
                    // Ensure AudioContext is initialized and resumed
                    await this.audioStreamPlayer.init();
                }
                this.audioStreamPlayer.reset();
            }
        });

        // TTS audio chunk received (streaming mode)
        this.socket.on('audio_chunk', async (data) => {
            if (data.session_id === this.sessionId) {
                if (data.is_final) {
                    console.log('[TTS] Streaming complete');
                    // Audio will continue playing until all chunks are done
                    // The audioStreamPlayer will handle the end event
                } else {
                    console.log(`[TTS] Received chunk ${data.chunk_number} (${data.chunk_type})`);

                    try {
                        if (data.chunk_type === 'url') {
                            // Audio URL chunk - fetch and add to queue
                            await this.audioStreamPlayer.addAudioUrl(data.audio_data);
                        } else if (data.chunk_type === 'data') {
                            // Raw audio data chunk - add to queue
                            await this.audioStreamPlayer.addAudioData(data.audio_data);
                        }
                    } catch (error) {
                        console.error('[TTS] Error processing audio chunk:', error);
                    }
                }
            }
        });

        // TTS synthesis complete (non-streaming mode - fallback)
        this.socket.on('synthesis_complete', (data) => {
            if (data.session_id === this.sessionId) {
                console.log('Synthesis complete (non-streaming), playing audio');
                this.isSpeaking = true;
                this.updateStatus('speaking', '🔊', 'Speaking');
                this.playAudio(data.audio_url);
            }
        });

        // Error
        this.socket.on('error', (data) => {
            console.error('Server error:', data.message);
            this.updateStatus('listening', '◉', 'Listening');
        });

        // Performance metrics
        this.socket.on('performance_metrics', (data) => {
            if (data.session_id === this.sessionId && this.perfMonitor) {
                console.log('[Perf] Metrics received:', data.metrics);
                this.perfMonitor.updateCurrent(data.metrics);
                this.perfMonitor.recordMetrics(data.metrics);
            }
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

        // Reset session button (for staff/testing)
        const resetSessionBtn = document.getElementById('reset-session-btn');
        if (resetSessionBtn) {
            resetSessionBtn.addEventListener('click', () => this.resetSession());
        }

        // Stop listening button
        const stopListeningBtn = document.getElementById('stop-listening-btn');
        if (stopListeningBtn) {
            stopListeningBtn.addEventListener('click', () => this.handleStopListening());
        }

        // Monitor for barge-in during speech
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.isSpeaking) {
                this.handleBargeIn();
            }
        });
    }

    async handleStartOrder() {
        console.log('User tapped button...');

        // Initialize AudioStreamPlayer during user interaction to satisfy browser autoplay policy
        if (!this.audioStreamPlayer) {
            console.log('[Audio] Initializing AudioStreamPlayer during user interaction');
            this.audioStreamPlayer = new AudioStreamPlayer();
            await this.audioStreamPlayer.init();
            this.audioStreamPlayer.setOnEndCallback(() => {
                console.log('[TTS] All audio chunks played');
                this.isSpeaking = false;
                this.updateStatus('listening', '◉', 'Listening');
            });
        }

        if (this.sessionState === 'confirmed_passive' || this.sessionState === 'confirmed_stopped') {
            // Resume active conversation from passive/stopped state
            console.log('[Session] Resuming active conversation from passive/stopped state');

            // Emit resume event
            this.socket.emit('resume_conversation', {
                session_id: this.sessionId
            });

            // Hide button and stop button
            const startButtonArea = document.getElementById('start-button-area');
            startButtonArea.classList.add('hidden');

            const stopButton = document.getElementById('stop-listening-btn');
            stopButton.classList.add('hidden');

            // Show status
            this.updateStatus('listening', '◉', 'Listening');

            return;
        }

        if (this.sessionState === 'confirmed') {
            // "Tap for Anything" - resume conversation
            console.log('[Session] Resuming conversation in CONFIRMED state');

            // Hide button
            const startButtonArea = document.getElementById('start-button-area');
            startButtonArea.classList.add('hidden');

            // Resume listening
            this.updateStatus('listening', '◉', 'Listening');

            // Notify backend (optional - state remains CONFIRMED)
            return;
        }

        // Normal flow: "Touch to Order" - start enrollment
        console.log('User tapped "Touch to Order" - starting enrollment...');
        this.sessionState = 'enrolling';

        // Hide start button
        const startButtonArea = document.getElementById('start-button-area');
        startButtonArea.classList.add('hidden');

        // Show enrollment prompt
        const enrollmentArea = document.getElementById('enrollment-area');
        if (enrollmentArea) {
            enrollmentArea.classList.remove('hidden');
            this.updateEnrollmentStatus('Please say: "Hello, I\'d like to order"');
        }

        // Start enrollment recording
        await this.startEnrollmentRecording();
    }

    async startEnrollmentRecording() {
        console.log('[Enrollment] Starting...');
        this.isEnrolling = true;
        this.enrollmentAudioBuffer = [];

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
            const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

            const startTime = Date.now();

            processor.onaudioprocess = (e) => {
                if (!this.isEnrolling) return;

                const inputData = e.inputBuffer.getChannelData(0);

                // Buffer audio for enrollment
                const buffer = new Float32Array(inputData.length);
                buffer.set(inputData);
                this.enrollmentAudioBuffer.push(buffer);

                // Check if we've collected enough audio
                const elapsed = (Date.now() - startTime) / 1000;
                if (elapsed >= this.enrollmentDuration) {
                    this.completeEnrollment(processor, source, stream);
                }
            };

            source.connect(processor);
            processor.connect(this.audioContext.destination);

            this.audioWorklet = { source, processor, stream };

            console.log('[Enrollment] Recording started');

        } catch (error) {
            console.error('[Enrollment] Failed:', error);
            alert('Microphone access denied. Please allow microphone access and refresh the page.');
            this.isEnrolling = false;
        }
    }

    completeEnrollment(processor, source, stream) {
        console.log('[Enrollment] Completing...');
        this.isEnrolling = false;

        // Stop audio processing
        processor.disconnect();
        source.disconnect();
        stream.getTracks().forEach(track => track.stop());

        // Concatenate all audio buffers
        const totalLength = this.enrollmentAudioBuffer.reduce((sum, buf) => sum + buf.length, 0);
        const enrollmentAudio = new Float32Array(totalLength);
        let offset = 0;
        for (const buf of this.enrollmentAudioBuffer) {
            enrollmentAudio.set(buf, offset);
            offset += buf.length;
        }

        console.log(`[Enrollment] Collected ${enrollmentAudio.length} samples (${(enrollmentAudio.length / 16000).toFixed(2)}s)`);

        // Enroll speaker (client-side)
        this.updateEnrollmentStatus('Processing...');
        const result = this.speakerVerifier.enroll(enrollmentAudio);

        console.log('[Enrollment] Result:', result);

        if (result.success) {
            console.log('[Enrollment] ✓ Success - speaker enrolled');
            console.log('[Enrollment] isEnrolled:', this.speakerVerifier.isEnrolled());
            this.onEnrollmentComplete();
        } else {
            console.error('[Enrollment] ✗ Failed:', result.message);
            console.error('[Enrollment] Barge-in will be DISABLED (no enrollment)');
            // Continue anyway, but barge-in will be disabled
            this.onEnrollmentComplete();
        }
    }

    onEnrollmentComplete() {
        console.log('[Enrollment] Complete, starting normal ordering...');
        console.log('[Enrollment] Final enrollment status:', this.speakerVerifier.isEnrolled());

        // Update session state
        this.sessionState = 'ordering';

        // Notify backend of state transition
        this.socket.emit('start_ordering', {
            session_id: this.sessionId
        });

        // Hide enrollment area
        const enrollmentArea = document.getElementById('enrollment-area');
        if (enrollmentArea) {
            enrollmentArea.classList.add('hidden');
        }

        // Show status area
        const statusArea = document.getElementById('status-area');
        statusArea.classList.remove('hidden');

        // Show order panel
        const orderPanel = document.getElementById('order-panel');
        orderPanel.classList.remove('hidden');

        // Hide main content area
        const mainContent = document.querySelector('.main-content');
        mainContent.classList.add('with-order');

        // Update status
        this.updateStatus('listening', '◉', 'Listening');

        // Start normal recording
        this.startRecording();
    }

    updateEnrollmentStatus(text) {
        const statusEl = document.getElementById('enrollment-status');
        if (statusEl) {
            statusEl.textContent = text;
        }
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

                // Check for barge-in during speaking (only if enrolled)
                if (this.isSpeaking && this.speakerVerifier.isEnrolled()) {
                    const volume = this.calculateVolume(inputData);
                    if (volume > 0.02) { // Voice detected threshold
                        // Verify speaker (client-side, no network latency!)
                        const result = this.speakerVerifier.verify(inputData);

                        if (result.isMatch) {
                            console.log(`[Barge-in] ✓ Verified (similarity: ${result.similarity.toFixed(3)})`);
                            this.handleBargeIn();
                        } else {
                            console.log(`[Barge-in] ✗ Rejected (similarity: ${result.similarity.toFixed(3)}) - not customer`);
                        }
                    }
                }
                // Note: If not enrolled, barge-in is disabled for safety
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

        // Stop streaming audio player
        if (this.audioStreamPlayer) {
            this.audioStreamPlayer.stop();
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
            text: text,
            stream: this.streamingEnabled  // Request streaming
        });
    }

    playAudio(audioUrl) {
        this.audioPlayer = document.getElementById('audio-player');
        this.audioPlayer.src = audioUrl;

        this.audioPlayer.onended = () => {
            this.isSpeaking = false;
            this.updateStatus('listening', '◉', 'Listening');
        };

        this.audioPlayer.onerror = () => {
            console.warn('Audio playback failed');
            this.isSpeaking = false;
            this.updateStatus('listening', '◉', 'Listening');
        };

        this.audioPlayer.play().catch(err => {
            console.warn('Audio play error:', err);
            this.isSpeaking = false;
            this.updateStatus('listening', '◉', 'Listening');
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
        const confirmedSection = document.getElementById('confirmed-section');
        const confirmedItemsEl = document.getElementById('confirmed-items');
        const newSection = document.getElementById('new-section');
        const newItemsEl = document.getElementById('new-items');
        const itemCount = document.getElementById('item-count');
        const subtotalEl = document.getElementById('subtotal');
        const taxEl = document.getElementById('tax');
        const totalEl = document.getElementById('total');
        const sendOrderBtn = document.getElementById('send-order-btn');

        // Calculate totals if not provided
        const allItems = [...this.confirmedItems, ...this.currentOrder];
        if (subtotal === undefined) {
            subtotal = allItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            tax = subtotal * 0.09;
            total = subtotal + tax;
        }

        // Update item count
        const totalItems = allItems.reduce((sum, item) => sum + item.quantity, 0);
        itemCount.textContent = `${totalItems} item${totalItems > 1 ? 's' : ''}`;

        // Update totals
        subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
        taxEl.textContent = `$${tax.toFixed(2)}`;
        totalEl.textContent = `$${total.toFixed(2)}`;

        // Show/hide confirmed section
        if (this.confirmedItems.length > 0 && confirmedSection) {
            confirmedSection.classList.remove('hidden');
            if (confirmedItemsEl) {
                confirmedItemsEl.innerHTML = this.confirmedItems.map(item => `
                    <div class="order-item locked">
                        <div class="item-details">
                            <span class="item-name">${this.escapeHtml(item.name)}</span>
                            ${item.quantity > 1 ? `<span class="item-quantity">x${item.quantity}</span>` : ''}
                        </div>
                        <span class="item-price">$${(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                `).join('');
            }
        } else if (confirmedSection) {
            confirmedSection.classList.add('hidden');
        }

        // Show/hide new items section
        if (this.currentOrder.length > 0 && newSection) {
            newSection.classList.remove('hidden');
            if (newItemsEl) {
                newItemsEl.innerHTML = this.currentOrder.map(item => `
                    <div class="order-item">
                        <div class="item-details">
                            <span class="item-name">${this.escapeHtml(item.name)}</span>
                            ${item.quantity > 1 ? `<span class="item-quantity">x${item.quantity}</span>` : ''}
                        </div>
                        <span class="item-price">$${(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                `).join('');
            }
        } else if (newSection) {
            newSection.classList.add('hidden');
        }

        // Show/hide empty state message
        const emptyState = orderItems.querySelector('.empty-state');
        if (allItems.length === 0) {
            if (emptyState) {
                emptyState.classList.remove('hidden');
            }
            sendOrderBtn.disabled = true;
        } else {
            if (emptyState) {
                emptyState.classList.add('hidden');
            }
            sendOrderBtn.disabled = false;
        }
    }

    addOrderItem(name, price) {
        this.currentOrder.push({ name, price });
        this.updateOrderDisplay();
    }

    async sendOrder() {
        console.log('Sending order:', this.currentOrder);
        alert('Order sent to kitchen! (Demo only)');
    }

    resetSession() {
        console.log('[Session] Manual reset requested');
        if (confirm('Reset session? This will clear the order and start over.')) {
            this.socket.emit('reset_session', {
                session_id: this.sessionId
            });
        }
    }

    handleStopListening() {
        console.log('[Session] User requested to stop passive listening');

        // Emit stop listening event
        this.socket.emit('stop_listening', {
            session_id: this.sessionId
        });

        // Stop recording
        this.stopRecording();

        // Hide status area
        const statusArea = document.getElementById('status-area');
        statusArea.classList.add('hidden');

        // Hide stop button
        const stopButton = document.getElementById('stop-listening-btn');
        stopButton.classList.add('hidden');

        // Show "Tap for Anything" button
        const startButtonArea = document.getElementById('start-button-area');
        startButtonArea.classList.remove('hidden');
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

        // Reset session state
        this.sessionState = 'idle';

        // Clear orders
        this.confirmedItems = [];
        this.currentOrder = [];
        this.updateOrderDisplay();

        // Reset speaker verification
        this.speakerVerifier.reset();

        // Hide status area
        const statusArea = document.getElementById('status-area');
        statusArea.classList.add('hidden');

        // Hide order panel
        const orderPanel = document.getElementById('order-panel');
        orderPanel.classList.add('hidden');

        // Show main content area
        const mainContent = document.querySelector('.main-content');
        mainContent.classList.remove('with-order');

        // Show start button
        const startButtonArea = document.getElementById('start-button-area');
        startButtonArea.classList.remove('hidden');

        // Reset button text
        this.updateButton('idle');

        console.log('Ready for next customer. Tap "Touch to Order" to start.');
    }

    updateButton(state) {
        const button = document.getElementById('start-order-btn');
        if (!button) return;

        switch(state) {
            case 'idle':
                button.textContent = 'Touch to Order';
                break;

            case 'enrolling':
            case 'ordering':
                // Button hidden during these states
                break;

            case 'confirmed':
                button.textContent = 'Tap for Anything';
                break;
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
