// CamareraI - Frontend JavaScript
// Handles voice recording, API communication, and UI updates

class VoiceAgent {
    constructor() {
        this.sessionId = null;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.currentOrder = [];

        this.init();
    }

    async init() {
        // Initialize session
        await this.createSession();

        // Set up event listeners
        this.setupEventListeners();

        // Update UI
        this.updateStatus('sleeping', '💤', 'Ready');
    }

    async createSession() {
        try {
            const response = await fetch('/api/session/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    table_id: '1',
                    role: 'customer'
                })
            });

            const data = await response.json();
            this.sessionId = data.session_id;

            // Update UI with table name
            document.getElementById('table-name').textContent = data.table_name;
            document.getElementById('debug-session').textContent = this.sessionId;

            console.log('Session created:', data);
        } catch (error) {
            console.error('Failed to create session:', error);
            this.showError('Failed to initialize. Please refresh the page.');
        }
    }

    setupEventListeners() {
        // Talk button
        const talkBtn = document.getElementById('talk-btn');
        talkBtn.addEventListener('click', () => this.toggleRecording());

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

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                await this.processAudio(audioBlob);

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start();
            this.isRecording = true;

            // Update UI
            this.updateStatus('listening', '👂', 'Listening...');
            document.getElementById('talk-btn').classList.add('recording');
            document.querySelector('.btn-text').textContent = 'Tap to Stop';
            document.getElementById('recording-indicator').classList.remove('hidden');

        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showError('Microphone access denied. Please allow microphone access.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;

            // Update UI
            this.updateStatus('processing', '⚙️', 'Processing...');
            document.getElementById('talk-btn').classList.remove('recording');
            document.querySelector('.btn-text').textContent = 'Tap to Talk';
            document.getElementById('recording-indicator').classList.add('hidden');
        }
    }

    async processAudio(audioBlob) {
        try {
            // Step 1: Transcribe audio
            const transcription = await this.transcribeAudio(audioBlob);

            if (!transcription) {
                this.updateStatus('sleeping', '💤', 'Ready');
                return;
            }

            // Update debug info
            document.getElementById('debug-transcript').textContent = transcription;

            // Add user message to conversation
            this.addMessage('user', transcription);

            // Step 2: Get AI response
            this.updateStatus('thinking', '🤔', 'Thinking...');
            const response = await this.getAIResponse(transcription);

            // Update debug info
            document.getElementById('debug-response').textContent = response;

            // Add assistant message to conversation
            this.addMessage('assistant', response);

            // Step 3: Synthesize and play audio response
            this.updateStatus('speaking', '🗣️', 'Speaking...');
            await this.playAudioResponse(response);

            // Back to ready state
            this.updateStatus('sleeping', '💤', 'Ready');

        } catch (error) {
            console.error('Error processing audio:', error);
            this.showError('Failed to process audio. Please try again.');
            this.updateStatus('sleeping', '💤', 'Ready');
        }
    }

    async transcribeAudio(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('session_id', this.sessionId);

        const response = await fetch('/api/voice/transcribe', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Transcription failed');
        }

        const data = await response.json();
        return data.text;
    }

    async getAIResponse(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error('Chat failed');
        }

        const data = await response.json();
        return data.response;
    }

    async playAudioResponse(text) {
        const response = await fetch('/api/voice/synthesize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                text: text
            })
        });

        if (!response.ok) {
            throw new Error('Speech synthesis failed');
        }

        const data = await response.json();

        // Play audio
        const audioPlayer = document.getElementById('audio-player');
        audioPlayer.src = data.audio_url;

        return new Promise((resolve) => {
            audioPlayer.onended = resolve;
            audioPlayer.play();
        });
    }

    addMessage(role, content) {
        const conversationHistory = document.getElementById('conversation-history');

        // Remove welcome message if it exists
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
            <div class="message-content">${content}</div>
        `;

        conversationHistory.appendChild(messageDiv);

        // Scroll to bottom
        conversationHistory.scrollTop = conversationHistory.scrollHeight;
    }

    updateStatus(state, icon, text) {
        document.getElementById('status-icon').textContent = icon;
        document.getElementById('status-text').textContent = text;
    }

    showError(message) {
        // Simple error display (can be enhanced)
        alert(message);
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

        // Calculate totals
        const subtotal = this.currentOrder.reduce((sum, item) => sum + item.price, 0);
        const tax = subtotal * 0.09;
        const total = subtotal + tax;

        // Update display
        itemCount.textContent = `${this.currentOrder.length} item${this.currentOrder.length > 1 ? 's' : ''}`;
        subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
        taxEl.textContent = `$${tax.toFixed(2)}`;
        totalEl.textContent = `$${total.toFixed(2)}`;
        sendOrderBtn.disabled = false;

        // Render items
        orderItems.innerHTML = this.currentOrder.map(item => `
            <div class="order-item">
                <span class="item-name">${item.name}</span>
                <span class="item-price">$${item.price.toFixed(2)}</span>
            </div>
        `).join('');
    }

    addOrderItem(name, price) {
        this.currentOrder.push({ name, price });
        this.updateOrderDisplay();
    }

    async sendOrder() {
        // Placeholder for sending order to kitchen
        console.log('Sending order:', this.currentOrder);
        alert('Order sent to kitchen! (Demo only)');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.voiceAgent = new VoiceAgent();
});
