/**
 * AudioStreamPlayer - Progressive audio playback for streaming TTS
 * Handles both audio URLs and raw audio data chunks
 */
class AudioStreamPlayer {
    constructor() {
        this.audioContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.currentSource = null;
        this.startTime = 0;
        this.nextStartTime = 0;
        this.onEndCallback = null;
    }

    async init() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        // Resume context if suspended (required by some browsers)
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }
    }

    reset() {
        console.log('[AudioStreamPlayer] Resetting player');
        this.stop();
        this.audioQueue = [];
        this.nextStartTime = 0;
    }

    stop() {
        console.log('[AudioStreamPlayer] Stopping playback');
        this.isPlaying = false;

        if (this.currentSource) {
            try {
                this.currentSource.stop();
            } catch (e) {
                // Already stopped
            }
            this.currentSource = null;
        }

        // Stop all queued audio
        this.audioQueue.forEach(item => {
            if (item.source) {
                try {
                    item.source.stop();
                } catch (e) {
                    // Already stopped
                }
            }
        });

        this.audioQueue = [];
    }

    async addAudioUrl(audioUrl) {
        console.log('[AudioStreamPlayer] Adding audio URL to queue');

        try {
            await this.init();

            // Fetch audio data
            const response = await fetch(audioUrl);
            const arrayBuffer = await response.arrayBuffer();

            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

            // Add to queue
            this.audioQueue.push({
                type: 'buffer',
                buffer: audioBuffer
            });

            console.log(`[AudioStreamPlayer] Audio URL added (${audioBuffer.duration.toFixed(2)}s), queue size: ${this.audioQueue.length}`);

            // Start playing if not already
            if (!this.isPlaying) {
                this.playNext();
            }

        } catch (error) {
            console.error('[AudioStreamPlayer] Error adding audio URL:', error);
            throw error;
        }
    }

    async addAudioData(base64Data) {
        console.log('[AudioStreamPlayer] Adding raw audio data to queue');

        try {
            await this.init();

            // Decode base64 to ArrayBuffer
            const binaryString = window.atob(base64Data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const arrayBuffer = bytes.buffer;

            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

            // Add to queue
            this.audioQueue.push({
                type: 'buffer',
                buffer: audioBuffer
            });

            console.log(`[AudioStreamPlayer] Audio data added (${audioBuffer.duration.toFixed(2)}s), queue size: ${this.audioQueue.length}`);

            // Start playing if not already
            if (!this.isPlaying) {
                this.playNext();
            }

        } catch (error) {
            console.error('[AudioStreamPlayer] Error adding audio data:', error);
            throw error;
        }
    }

    playNext() {
        if (this.audioQueue.length === 0) {
            console.log('[AudioStreamPlayer] Queue empty, playback complete');
            this.isPlaying = false;

            // Trigger end callback
            if (this.onEndCallback) {
                this.onEndCallback();
            }

            return;
        }

        this.isPlaying = true;

        const item = this.audioQueue.shift();
        const buffer = item.buffer;

        console.log(`[AudioStreamPlayer] Playing next chunk (${buffer.duration.toFixed(2)}s), ${this.audioQueue.length} remaining`);

        // Create buffer source
        const source = this.audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(this.audioContext.destination);

        // Schedule playback
        const currentTime = this.audioContext.currentTime;
        const startTime = Math.max(currentTime, this.nextStartTime);

        source.onended = () => {
            console.log('[AudioStreamPlayer] Chunk playback ended');
            this.playNext();
        };

        source.start(startTime);
        this.currentSource = source;

        // Update next start time for seamless playback
        this.nextStartTime = startTime + buffer.duration;

        console.log(`[AudioStreamPlayer] Scheduled playback at ${startTime.toFixed(2)}s, next at ${this.nextStartTime.toFixed(2)}s`);
    }

    setOnEndCallback(callback) {
        this.onEndCallback = callback;
    }
}

// Make available globally
window.AudioStreamPlayer = AudioStreamPlayer;
